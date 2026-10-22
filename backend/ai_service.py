import os
import json
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from groq import Groq
import database
import integrations

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your-fallback-groq-key")
client = Groq(api_key=GROQ_API_KEY)

# Groq model configuration. GROQ_MODEL is the fallback used whenever a bot's
# saved engine is missing or is no longer a valid Groq model (e.g. legacy names
# like "gpt-4o" or "llama-3.3-70b-versatile", which Groq rejects or retired, or
# models the account has no access to, like "qwen/qwen3.6-27b").
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
ALLOWED_GROQ_MODELS = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
)


def resolve_groq_model(engine: Optional[str]) -> str:
    """Return a valid Groq model for the bot, falling back to GROQ_MODEL."""
    if engine in ALLOWED_GROQ_MODELS:
        return engine
    if engine:
        logging.warning(
            "Unknown or deprecated Groq model '%s' in bot config; "
            "falling back to GROQ_MODEL ('%s').",
            engine, GROQ_MODEL
        )
    return GROQ_MODEL


# --- GOOGLE WORKSPACE FUNCTION CALLING SCHEMAS ---
GWORKSPACE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_recent_emails",
            "description": "Fetch recent inbox emails from Gmail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "description": "Number of emails to fetch (default 5)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an outbound email to a recipient via Gmail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Subject line of the email"},
                    "body": {"type": "string", "description": "Body message text"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Get upcoming Google Calendar events and schedule context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "description": "Number of events to retrieve (default 5)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Schedule/mark a new meeting or event on Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Title or summary of the meeting/event"},
                    "start_time": {"type": "string", "description": "Start time in ISO format e.g. 2026-08-10T14:00:00Z"},
                    "end_time": {"type": "string", "description": "End time in ISO format e.g. 2026-08-10T15:00:00Z"},
                    "description": {"type": "string", "description": "Notes or agenda for the event"},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses"
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_drive_files",
            "description": "Search for documents or files in Google Drive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or file name"},
                    "max_results": {"type": "integer", "description": "Maximum number of files to return"}
                },
                "required": []
            }
        }
    }
]


def execute_gworkspace_tool(tool_name: str, tool_args: dict, target_id: str) -> str:
    """Dispatches tool call execution to integrations.py."""
    token = integrations.get_valid_token(target_id)
    if not token:
        return "Error: No active Google Workspace token found."

    try:
        if tool_name == "get_recent_emails":
            return integrations.get_recent_emails(target_id=token, max_results=tool_args.get("max_results", 5))
        elif tool_name == "send_email":
            return integrations.send_email(
                target_id_or_token=token,
                to=tool_args.get("to"),
                subject=tool_args.get("subject"),
                body=tool_args.get("body")
            )
        elif tool_name == "get_calendar_events":
            return integrations.get_calendar_events(target_id=token, max_results=tool_args.get("max_results", 5))
        elif tool_name == "create_calendar_event":
            return integrations.create_calendar_event(
                target_id_or_token=token,
                summary=tool_args.get("summary"),
                start_time=tool_args.get("start_time"),
                end_time=tool_args.get("end_time"),
                description=tool_args.get("description", ""),
                attendees=tool_args.get("attendees", [])
            )
        elif tool_name == "search_drive_files":
            return integrations.search_drive_files(
                target_id=token, 
                query=tool_args.get("query", ""), 
                max_results=tool_args.get("max_results", 5)
            )
        else:
            return f"Error: Unknown tool '{tool_name}'."
    except Exception as e:
        # Full traceback lands in the uvicorn terminal; the string sent back
        # to the model stays generic. owner_id is safe to log — tokens are not.
        logging.exception("Google tool '%s' execution failed for owner %s", tool_name, target_id)
        return f"Error executing tool {tool_name}: {e}"


def _complete(model: str, messages: list, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    """Core helper for executing standard completions on Groq."""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            stream=False,
        )
        return completion.choices[0].message.content or ""
    except Exception as err:
        print(f"[GROQ COMPLETION ERROR]: {err}")
        raise err


def build_work_plan(bot_id: str, task_input: str) -> list:
    """Turn a request into reviewable steps before an autonomous agent works."""
    bot = database.get_bot_config(bot_id) or {}
    prompt = f"""You are planning work for the AI agent '{bot.get('name', 'Agent')}'.
Agent goal: {bot.get('goal') or "Complete the user's work accurately."}
Agent instructions: {bot.get('instructions', '')}
Task: {task_input}

Return ONLY a JSON array of 3-6 concise objects. Every object must have `step` and `outcome`.
Do not claim you used external tools or changed external systems without review."""

    engine_model = resolve_groq_model(bot.get("engine"))

    try:
        raw = _complete(
            model=engine_model, 
            messages=[
                {"role": "system", "content": "You create safe, practical work plans."}, 
                {"role": "user", "content": prompt}
            ], 
            temperature=0.2, 
            max_tokens=600
        )
        match = re.search(r"\[[\s\S]*\]", raw)
        plan = json.loads(match.group(0) if match else raw)
        if isinstance(plan, list) and plan:
            return [
                {
                    "step": str(item.get("step", "Review task")), 
                    "outcome": str(item.get("outcome", "Progress recorded"))
                } 
                for item in plan[:6] if isinstance(item, dict)
            ]
    except Exception as error:
        print(f"Groq planning error: {error}")

    return [
        {"step": "Understand the request and available context", "outcome": "Clear task brief"},
        {"step": "Prepare the requested deliverable", "outcome": "Draft result ready for review"},
        {"step": "Check the result against the agent goal", "outcome": "Final work report"},
    ]


def execute_agent_task(bot_id: str, task_input: str, plan: list) -> str:
    """Produce the agent work result."""
    bot = database.get_bot_config(bot_id) or {}
    enabled_tools = database.get_enabled_tools(bot_id)
    
    guardrail = (
        "Do not claim that you sent, booked, published, purchased, deleted, or changed anything externally. "
        "Instead, prepare the exact draft or request approval." 
        if bot.get("autonomy", "approve") != "auto" 
        else "You may prepare work autonomously, but never claim an external side effect unless the application actually performed it."
    )
    
    messages = [
        {
            "role": "system", 
            "content": f"""You are {bot.get('name', 'an AI work agent')}.
Goal: {bot.get('goal') or 'Complete useful work for the user.'}
Instructions: {bot.get('instructions', '')}
Enabled capabilities: {', '.join(enabled_tools) or 'knowledge lookup and drafting'}.
{guardrail}
Return a well-structured work report with: Summary, Deliverable, and Recommended next action."""
        },
        {
            "role": "user", 
            "content": f"Task: {task_input}\n\nApproved plan:\n{json.dumps(plan, indent=2)}"
        },
    ]
    
    engine_model = resolve_groq_model(bot.get("engine"))

    try:
        return _complete(engine_model, messages, float(bot.get("temperature", 0.3)), 1400)
    except Exception as error:
        print(f"Task Execution Error: {error}")
        return "Failed to complete task execution due to API model communication failure."


def generate_bot_reply(
    bot_id: str,
    user_message: str,
    session_id: Optional[str] = None,
    owner_id: str = "default_owner",
    history: Optional[List[Dict[str, str]]] = None,
    **kwargs
) -> str:
    """
    Generates dynamic bot reply while preserving full session chat memory from database,
    evaluating enabled extensions, and triggering function calling when applicable.
    """
    try:
        # 1. Ensure isolated session per workspace/owner if session_id isn't explicitly provided
        resolved_session_id = session_id or f"session_{owner_id}_{bot_id}"
        resolved_session_id = database.create_or_get_session(resolved_session_id, bot_id, user_message)

        # 2. Retrieve bot configuration
        bot_config = database.get_bot_config(bot_id) or {}
        base_instructions = bot_config.get("instructions", "You are a helpful AI assistant.")
        engine_model = resolve_groq_model(bot_config.get("engine"))
        temperature = float(bot_config.get("temperature", 0.3))

        # 3. Retrieve system extensions
        enabled_tools = database.get_enabled_tools(bot_id)
        bot_extensions = database.get_bot_extensions(bot_id)

        # 4. Build dynamic system instruction
        system_instruction = base_instructions
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")
        system_instruction += f"\n\n[SYSTEM CONTEXT]: Current date and time is {current_time_str}."

        if "smart_lead_capture" in enabled_tools:
            system_instruction += (
                "\n\n[EXTENSION ENABLED: Smart Lead Capture]\n"
                "CRITICAL: If the user provides personal identification data such as names, "
                "emails, or phone numbers, explicitly acknowledge that you have captured this detail."
            )

        if "live_scheduler" in enabled_tools:
            system_instruction += (
                "\n\n[EXTENSION ENABLED: Live Scheduler]\n"
                "CRITICAL: If the user requests a consultation, callback, demo, or meeting, "
                "actively guide them to book a calendar time block."
            )

        retrieved_knowledge = database.query_bot_knowledge(bot_id, user_message)
        if "instant_faq" in enabled_tools and retrieved_knowledge:
            system_instruction += f"""

[EXTENSION ENABLED: Instant FAQ Resolver]
CRITICAL KNOWLEDGE BASE CONTEXT:
You must use the following facts verified by the business owner to resolve the user's question:
{retrieved_knowledge}
"""
        elif retrieved_knowledge:
            system_instruction += f"\n\nContextual Reference Content:\n{retrieved_knowledge}"

        # 5. Persist the new incoming user message to the database first
        database.save_chat_message(resolved_session_id, "user", user_message)

        # 6. Retrieve recent conversation history memory window (e.g., last 12 messages)
        chat_history = database.get_session_history(resolved_session_id, limit=12)
        if not chat_history and history:
            chat_history = history

        # 7. Construct messages payload array with system prompt + past turns
        messages = [{"role": "system", "content": system_instruction}]
        for turn in chat_history:
            messages.append({"role": turn["role"], "content": turn["content"]})

        # 8. Check Google Workspace Tool availability
        has_google_tool = any("google" in str(t).lower() or "gmail" in str(t).lower() or "calendar" in str(t).lower() for t in enabled_tools)
        token = integrations.get_valid_token(owner_id or bot_id)

        # Tools fire whenever the logged-in owner has a connected (and
        # auto-refreshable) Google account. The extension gate alone would skip
        # tools for bots that never enabled a Google-flavoured extension.
        use_tools = bool(token)
        if has_google_tool and not token:
            logging.warning(
                "Bot %s has a Google extension enabled but owner %s has no connected Google account; tools disabled.",
                bot_id, owner_id,
            )

        # The per-bot Google Workspace toggle on the bot config page can
        # explicitly switch tools off. Bots created before the toggle existed
        # have no row and keep the default-on behaviour.
        google_extension = bot_extensions.get("google_workspace")
        if google_extension is not None and not google_extension.get("is_enabled", True):
            if use_tools:
                logging.info(
                    "Bot %s: Google Workspace extension is toggled off; tools disabled.", bot_id
                )
            use_tools = False

        # Connection state (never the token itself) is logged so tool-less
        # replies are immediately explainable in the uvicorn terminal.
        logging.info(
            "Bot %s (owner %s): Google tool use=%s (connected=%s)",
            bot_id, owner_id, use_tools, bool(token),
        )

        bot_reply = ""

        # 9. Execute with function calling when the owner's Google account is
        # connected. Both allowed Groq models (openai/gpt-oss-120b / 20b) support
        # native tool calling.
        if use_tools:
            try:
                response = client.chat.completions.create(
                    model=engine_model,
                    messages=messages,
                    tools=GWORKSPACE_TOOLS,
                    tool_choice="auto",
                    temperature=temperature
                )
                response_message = response.choices[0].message

                if response_message.tool_calls:
                    messages.append(response_message)

                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                        # Tool activity is logged to uvicorn; tokens and full
                        # email contents are never logged (only the result
                        # length, or the head of an error message).
                        print(f"[TOOL CALL DETECTED]: {tool_name} with args: {tool_args}")
                        logging.info(
                            "Bot %s owner %s executing tool %s args=%s",
                            bot_id, owner_id, tool_name, tool_args,
                        )
                        tool_result = execute_gworkspace_tool(tool_name, tool_args, target_id=owner_id)

                        if str(tool_result).startswith("Error"):
                            logging.error(
                                "Tool %s returned an error for owner %s: %s",
                                tool_name, owner_id, str(tool_result)[:300],
                            )
                        else:
                            logging.info(
                                "Tool %s completed for owner %s (%d chars returned)",
                                tool_name, owner_id, len(str(tool_result)),
                            )

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": str(tool_result)
                        })

                    second_response = client.chat.completions.create(
                        model=engine_model,
                        messages=messages,
                        temperature=temperature
                    )
                    bot_reply = second_response.choices[0].message.content or ""
                else:
                    bot_reply = response_message.content or ""
            except Exception:
                # Tool-calling failed (transient Groq error or a model without
                # tool-use support) — degrade gracefully to a plain completion
                # instead of failing the whole chat.
                logging.exception("Groq tool-calling failed; falling back to plain completion")
                plain_messages = [
                    m for m in messages
                    if isinstance(m, dict) and m.get("role") not in ("tool",)
                ]
                bot_reply = _complete(engine_model, plain_messages, temperature, 1024)
        else:
            # Fallback standard response execution
            bot_reply = _complete(engine_model, messages, temperature, 1024)

        # 10. Persist assistant reply to database for future turn memory
        database.save_chat_message(resolved_session_id, "assistant", bot_reply)
        
        # 11. Update bot conversation statistics
        database.increment_conversation_count(bot_id)

        return bot_reply

    except Exception:
        # logging.exception logs at ERROR level WITH the full traceback,
        # so the real cause (e.g. 401 Invalid API Key) prints in the uvicorn terminal.
        logging.exception("Groq API Inference Engine Error")
        return "I apologize, but I encountered an issue processing your request."