import logging
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero

from database import DatabaseManager
from session import SessionManager
from rag import KnowledgeBase

load_dotenv()

logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("auralis-prod")
logger.setLevel(logging.INFO)

logger.info("Preloading VAD model...")
vad_model = silero.VAD.load()

async def warmup_pipeline(llm_instance, tts_instance):
    logger.info("🔥 Warming up LLM & TTS connection...")
    try:
        await asyncio.gather(
            llm_instance.chat(chat_ctx=llm.ChatContext().append(text="ping", role="user")),
            tts_instance.synthesize(" ") 
        )
    except Exception:
        pass 

async def entrypoint(ctx: JobContext):
    db_manager = DatabaseManager()
    knowledge_base = KnowledgeBase()
    session = SessionManager()
    
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    fnc_ctx = llm.FunctionContext()

    @fnc_ctx.ai_callable()
    async def lookup_customer(identifier: str):
        """
        Search for a customer profile by Name or Phone. 
        RETURNS: JSON with 'name', 'vehicle', 'phone'.
        """ 
        logger.info(f"🔎 LOOKUP REQUEST: {identifier}")
        clean_id = session.normalize_phone(identifier)
        query = clean_id if clean_id else identifier 
        user_data = await db_manager.get_customer_by_lookup(query)
        
        if user_data:
            session.set_customer(user_data)
            return json.dumps({
                "status": "success", 
                "data": {
                    "name": user_data['name'], 
                    "vehicle": user_data['vehicle'],
                    "phone": user_data.get('phone', 'Unknown')
                }
            })
        return json.dumps({"status": "not_found", "message": "User not found. Ask for spelling or phone number."})

    @fnc_ctx.ai_callable()
    async def check_availability(date: str):
        """
        Check if a date is POTENTIALLY available. 
        Note: Availability is not guaranteed until validated by the manager.
        """
        is_open = await db_manager.check_availability(date)
        return json.dumps({"available": is_open, "date": date})
    
    @fnc_ctx.ai_callable()
    async def consult_policy(topic: str):
        """Search Knowledge Base for policies (e.g., 'oil change included?')."""
        logger.info(f"📚 RAG LOOKUP: {topic}")
        return knowledge_base.search(topic)

    @fnc_ctx.ai_callable()
    async def submit_booking_request(date: str, service_type: str):
        """
        Submit a service request to the validation queue.
        DO NOT say 'Confirmed'. Say 'Submitted for approval'.
        """
        if not session.is_authenticated:
            return json.dumps({"status": "error", "message": "Authentication required. Identify customer first."})
        
        request_payload = {
            "name": session.customer.name,
            "phone": session.customer.phone,
            "vehicle": session.customer.vehicle,
            "requested_date": date,
            "requested_service": service_type
        }
        
        result = await db_manager.queue_booking_request(request_payload)
        return json.dumps(result)

    now = datetime.now().strftime("%A, %B %d, %Y")

    system_instruction = f"""
    You are Auralis, the Front Desk for Rolls-Royce.
    
    --- TEMPORAL CONTEXT ---
    **Today is: {now}**
    
    --- CONTEXT & MEMORY ---
    1. **Session Awareness:** Once `lookup_customer` succeeds, you KNOW the Name, Vehicle, and Phone. NEVER ask again.
    2. **Vehicle Confirmation:** Always confirm the vehicle model found (e.g., "I see you have the Phantom...").
    
    --- PROTOCOL: REQUEST QUEUE ---
    **CRITICAL:** You CANNOT "confirm" bookings. You can only "submit requests".
    - **Bad:** "I have booked your appointment."
    - **Good:** "I have submitted your request for Tuesday. You will receive a confirmation once approved."
    
    --- VOICE RULES ---
    1. **Conciseness:** Keep responses under 10 words (unless explaining policy).
    2. **Verbal Bridges:** Speak BEFORE tool usage.
       - "Checking availability..." -> `check_availability`
       - "Submitting your request..." -> `submit_booking_request`
    
    --- WORKFLOW ---
    1. **Identify:** Ask Name/Phone -> `lookup_customer` -> Confirm Vehicle.
    2. **Service Check:** If user asks "Is X included?", run `consult_policy`.
    3. **Schedule:** - Ask Date -> `check_availability`.
       - If open -> `submit_booking_request`.
       - **Closing:** "Request submitted. We will notify you shortly."
    """

    initial_ctx = llm.ChatContext().append(
        role="system",
        text=system_instruction
    )

    llm_instance = openai.LLM(model="gpt-4o-mini")
    tts_instance = deepgram.TTS()

    asyncio.create_task(warmup_pipeline(llm_instance, tts_instance))

    agent = VoicePipelineAgent(
        vad=vad_model,
        stt=deepgram.STT(),
        llm=llm_instance,
        tts=tts_instance,
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
        allow_interruptions=True,
        min_endpointing_delay=0.3 
    )

    @agent.on("user_speech_committed")
    def on_user_speech(msg):
        if isinstance(msg, list): msg = msg[-1]
        asyncio.create_task(ctx.room.local_participant.publish_data(
            json.dumps({"type": "user_transcript", "data": {"text": msg.content}})
        ))

    @agent.on("agent_speech_committed")
    def on_agent_speech(msg):
        if isinstance(msg, list): msg = msg[-1]
        
        if len(agent.chat_ctx.messages) > 10:
            logger.info("✂️ Pruning chat history")
            agent.chat_ctx.messages = [agent.chat_ctx.messages[0]] + agent.chat_ctx.messages[-9:]

        asyncio.create_task(ctx.room.local_participant.publish_data(
            json.dumps({"type": "agent_transcript", "data": {"text": msg.content}})
        ))
        
    @agent.on("agent_state_changed")
    def on_state_changed(state):
        asyncio.create_task(ctx.room.local_participant.publish_data(
             json.dumps({"type": "state", "data": {"status": state}})
        ))

    agent.start(ctx.room)
    
    greeting_text = "Rolls-Royce Service. How may I assist you?"
    await ctx.room.local_participant.publish_data(
        json.dumps({"type": "agent_transcript", "data": {"text": greeting_text}})
    )
    
    await agent.say(greeting_text)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))