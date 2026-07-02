import os
from groq import Groq
import database

# Initialize the Groq core interface client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your-fallback-groq-key")
client = Groq(api_key=GROQ_API_KEY)

def generate_bot_reply(bot_id: str, user_message: str, history: list, temperature: float = 0.3) -> str:
    try:
        # 1. Fetch system instructions and engine configuration metrics
        bot_config = database.get_bot_config(bot_id)
        if bot_config:
            base_instructions = bot_config.get("instructions", "You are a helpful AI assistant.")
            engine_model = bot_config.get("engine", "llama-3.3-70b-versatile")
        else:
            base_instructions = "You are a helpful AI assistant."
            engine_model = "llama-3.3-70b-versatile"

        # 2. Fetch active tools list string array from extensions database
        enabled_tools = database.get_enabled_tools(bot_id)
        
        # 3. Dynamic setup of instructions blueprint template strings
        system_instruction = base_instructions

        # --- EXTENSION 1: SMART LEAD CAPTURE ---
        if "smart_lead_capture" in enabled_tools:
            system_instruction += (
                "\n\n[EXTENSION ENABLED: Smart Lead Capture]\n"
                "CRITICAL: If the user provides personal identification data such as names, "
                "emails, or phone numbers, explicitly acknowledge that you have captured this detail."
            )

        # --- EXTENSION 2: LIVE SCHEDULER ---
        if "live_scheduler" in enabled_tools:
            system_instruction += (
                "\n\n[EXTENSION ENABLED: Live Scheduler]\n"
                "CRITICAL: If the user requests a consultation, callback, demo, or meeting, "
                "actively guide them to book a calendar time block."
            )

        # --- EXTENSION 3: INSTANT FAQ RESOLVER & ORIGINAL CHUNKING LOGIC ---
        # If instant_faq toggle is active, we enforce strict boundary control over knowledge matches
        if "instant_faq" in enabled_tools:
            retrieved_knowledge = database.query_bot_knowledge(bot_id, user_message)
            if retrieved_knowledge:
                system_instruction += f"""

[EXTENSION ENABLED: Instant FAQ Resolver]
CRITICAL KNOWLEDGE BASE CONTEXT:
You must use the following facts verified by the business owner to resolve the user's question. 
If the answer cannot be explicitly generated from this documentation context, inform them clearly that you lack that data.

Verified Business Facts:
{retrieved_knowledge}
"""
        else:
            # Traditional Fallback: Query knowledge matching anyway but without strict boundary penalty
            retrieved_knowledge = database.query_bot_knowledge(bot_id, user_message)
            if retrieved_knowledge:
                system_instruction += f"\n\nContextual Reference Content:\n{retrieved_knowledge}"

        # 4. Compile messages structural payload arrays
        messages = [{"role": "system", "content": system_instruction}]
        
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": user_message})

        # 5. Route structured transaction payloads directly to Groq Cloud API
        completion = client.chat.completions.create(
            model=engine_model,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
            top_p=1,
            stream=False,
        )
        
        return completion.choices[0].message.content

    except Exception as e:
        print(f"Groq API Inference Engine Error: {e}")
        return "I apologize, but I am having trouble connecting to my processing networks right now."