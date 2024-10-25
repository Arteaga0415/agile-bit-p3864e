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

"""
VER INSCRUTCIONS.md PARA INSTRUCCIONES SIMPLES O EL README.md PARA LAS INSTRUCCIONES DE LIVEKIT
"""
load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")

#Funcion para acitvar el VAD (Voice Automatic Detection)
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

# Funcion para generar filler responses
def generate_filler_response():
    fillers = [
        "I hear you.",
        "Got it.",
        "Okay.",
        "I see.",
        "Alright.",
        "Awesome.",
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
    #Iniciar instancia de la clase DataExtractor la cual exrae los datos importantes de la transcripcion al finalizar la conversacion. 
    extractor = DataExtractor()

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
            "Ask about the house's conditions, how many bedrooms/baths it has. "
            "Ask about year built and square footage."
            "Ask about kitchen and flooring."
            "Ask about electrical/plumbing status."
            "Ask about roof age, and foundation status."
            "Inquire about the property's status (rented, vacant, or lived in) and how long it has been in that condition. "
            "If rented, ask for the rental amount, and lease expiration date. "
            "If vacant, ask how long it has been vacant. "
            "Inquire about additional features like HVAC, pool, or other valuable property attributes. "
            "If the customer refuses to answer, mention your company helps families rent properties, fixes and improves homes, and assists tenants with relocation. "
            "If the customers ask what do you mean by house conditions say (good, outdated, average, or needs work)."
            "When setting up the appointment make sure to specify the time zone "
            "Be upbeat, friendly, and genuine. "
        ),
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    logger.info('------------------------------------------------------------')
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Esperar a que el participante se conecte
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")
    logger.info('------------------------------------------------------------')

    """
    EN CASO DE NO QUERER UTILIZAR LAS FILLER PHRASES BORRAR "preemptive_synthesis=True," Y "before_llm_cb=before_llm_cb," DEL "VoicePipelineAgent"
    """
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
    
    #Metodo para iniciar el room
    assistant.start(ctx.room, participant)
    #Metodo para iniciar la conversacion
    await assistant.say(f"Hello, am I speaking with David, the owner of 42-43 California Street?", allow_interruptions=True)

    """
    EN CASO DE NO QUERER UTILIZAR LA CLASE "extract_data.py" BORRAR EL CODIGO DE ABAJO
    """
    #funcion para extraer solo el texto del objeto assistant.chat_ctx.messages
    def extract_conversation_text(messages):
        # Extract content from each message in the list
        text_content = " ".join([msg.content for msg in messages if msg.content])
        
        return text_content

    # Callback para cuando se desconecte el room
    async def on_room_shutdown():
        full_transcription = extract_conversation_text(assistant.chat_ctx.messages)
        logger.info(f"Room has been disconnected. Performing data extraction: {full_transcription}")
        logger.info('------------------------------------------------------------')
        extracted_data = extractor.extract_information(full_transcription)
        logger.info(f"Extracted data: {extracted_data}")
        logger.info('------------------------------------------------------------')
    # Metodo del ctx para llamar un callback una vez se desconecte el room
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
