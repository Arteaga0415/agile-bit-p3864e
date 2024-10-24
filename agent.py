import logging
import random
import asyncio

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, deepgram, silero
from extract_data import DataExtractor

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


# Function to generate filler responses
def generate_filler_response():
    fillers = [
        "I hear you.",
        "Got it.",
        "Okay.",
        "I see.",
        "Alright.",
    ]
    return random.choice(fillers)


# Callback function para activar las filler phrases mientras la respuesta se genera
async def before_llm_cb(agent, chat_ctx):
    filler_response = generate_filler_response()
    # Para que el modelo hable las filler phrases
    await agent.say(filler_response, allow_interruptions=True, add_to_chat_ctx=False)
    #Se devuelve NONE para que el flow continue en el pipeline
    return None


async def entrypoint(ctx: JobContext):
    extractor = DataExtractor()
    full_transcription = ''

    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoid unpronounceable punctuation. "
            "Use a helpful and conversational tone throughout the interaction. "
            "You are named Andres and are responsible for having voice conversations with customers who are looking to sell their properties."
            "Your goal is to set up meetings with our acquisitions partners by gathering information about the customer's property. "
            "Confirm the property address and who owns it. "
            "Start by saying that your company has been buying properties for over 20 years, closing in all-cash deals within 10 weeks or less. "
            "Ask about the house's conditions (good, outdated, average, or needs work), how many bedrooms/baths it has. "
            "Ask about year built and square footage."
            "Ask about kitchen, flooring and electrical/plumbing status."
            "Ask about roof age, and foundation status."
            "Inquire about the property's status (rented, vacant, or lived in) and how long it has been in that condition. "
            "If rented, ask for the rental amount, payment frequency (month-to-month or lease), and lease expiration date. "
            "If vacant, ask how long it has been vacant. "
            "Inquire about additional features like HVAC, pool, or other valuable property attributes. "
            "If the customer refuses to answer, mention your company helps families rent properties, fixes and improves homes, and assists tenants with relocation. "
            "Be upbeat, friendly, and genuine. "
        ),
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Esperar a que le primer participante se conecte
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    assistant = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        # Abilitar preemptive synthesis para que el modelo hable las filler phrases
        preemptive_synthesis=True,
        # Usar el callback para generar las filler phrases 
        before_llm_cb=before_llm_cb,
    )

    def on_transcription_update(transcription: str):
        nonlocal full_transcription
        full_transcription += transcription + " "

    assistant.on('user_final_transcript', on_transcription_update)

    assistant.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await assistant.say("Hello, am I speaking with David, the owner of 42-43 California Street?", allow_interruptions=True)

    # # Now that the conversation has finished, extract the data
    # extracted_data = extractor.extract_information(full_transcription)
    # logger.info(f"Extracted data: {extracted_data}")

    # Register a shutdown callback to handle the room disconnect event
    async def on_room_shutdown():
        logger.info("Room has been disconnected. Performing data extraction.")
        extracted_data = extractor.extract_information(full_transcription)
        logger.info(f"Extracted data: {extracted_data}")

    # Add shutdown callback to trigger when the room shuts down
    ctx.add_shutdown_callback(on_room_shutdown)

    # Keep the task running until shutdown
    await asyncio.Event().wait()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
