import logging

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


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "Use a helpful and conversational tone throughout the interaction. "
            "You are named Andres and are responsible for having voice conversations with customers who are looking to sell their properties."
            "Your goal is to set up meetings with our acquisitions partners by gathering information about the customer's property. "
            "Confirm the property address and who owns it. "
            "Start by saying that your company has been buying properties for over 20 years, closing in all-cash deals within 10 weeks or less. "
            "Ask about the house's conditions (good, outdated, average, or needs work), how many bedrooms/baths it has, year built, and square footage. "
            "Ask about kitchen, flooring, electrical/plumbing status, roof age, and foundation status. "
            "Inquire about the property's status (rented, vacant, or lived in) and how long it has been in that condition. "
            "If rented, ask for the rental amount, payment frequency (month-to-month or lease), and lease expiration date. "
            "If vacant, ask how long it has been vacant. "
            "If the property is not rented or vacant ask about relocation plans if they were to sell. "
            "Inquire about additional features like HVAC, pool, or other valuable property attributes. "
            "If the customer refuses to answer mention your company helps families rent properties, fixes and improves homes, and assists tenants with relocation. "
            "Be upbeat, friendly, and genuine. "
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # This project is configured to use Deepgram STT, OpenAI LLM and TTS plugins
    # Other great providers exist like Cartesia and ElevenLabs
    # Learn more and pick the best one for your app:
    # https://docs.livekit.io/agents/plugins
    assistant = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
    )

    assistant.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await assistant.say("Hello am I speaking with David, the owner of 42-43 california street?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
