import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

import database
import ai_service

app = FastAPI(
    title="Bot Manager API Engine",
    description="Backend pipeline for managing autonomous AI automation agents, database configurations, and extensions.",
    version="2.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()

# --- Request Schemas ---
class BotProfile(BaseModel):
    name: str
    description: Optional[str] = ""
    instructions: str
    engine: Optional[str] = "llama-3.3-70b-versatile"
    temperature: Optional[float] = 0.3
    guardrails: Optional[int] = 1

class ChatPayload(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    temperature: Optional[float] = 0.3

# --- 1. Base Connection Root ---
@app.get("/")
def read_root():
    """Provides a clear status payload to resolve frontend handshake drop alerts."""
    return {
        "status": "online", 
        "message": "FastAPI Bot Manager Backend Engine is running successfully on port 8001"
    }

# --- 2. Bot Profiles ---
@app.get("/bots/list")
def list_configured_bots():
    return database.get_all_bots_with_stats()

@app.get("/bots/{bot_id}")
def get_single_bot_configuration(bot_id: str):
    config = database.get_bot_config(bot_id)
    if not config:
        raise HTTPException(status_code=404, detail="Bot profile not found.")
    return config

@app.post("/bots/update/{bot_id}")
def save_or_modify_bot_profile(bot_id: str, profile: BotProfile):
    success = database.save_bot(
        bot_id=bot_id,
        name=profile.name,
        description=profile.description,
        instructions=profile.instructions,
        engine=profile.engine,
        temperature=profile.temperature,
        guardrails=profile.guardrails
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to sync bot metrics to database.")
    return {"status": "success", "message": f"Bot profile '{bot_id}' successfully synchronized."}

@app.delete("/bots/{bot_id}")
def purge_bot_profile(bot_id: str):
    success = database.delete_bot_from_db(bot_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to execute profile deletion.")
    return {"status": "success", "message": f"Bot '{bot_id}' successfully removed."}

# --- 3. Knowledge Base Core (RAG) ---
@app.post("/bots/{bot_id}/knowledge/upload")
async def upload_bot_knowledge_file(bot_id: str, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text_content = contents.decode("utf-8", errors="ignore")
        database.add_knowledge_content(bot_id=bot_id, file_name=file.filename, content=text_content)
        return {"status": "success", "file_name": file.filename, "message": "Knowledge asset logged."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest knowledge stream: {str(e)}")

@app.get("/bots/{bot_id}/knowledge")
def list_bot_knowledge_sources(bot_id: str):
    return database.get_bot_knowledge_sources(bot_id)

@app.delete("/bots/{bot_id}/knowledge/{file_name}")
def delete_bot_knowledge_source(bot_id: str, file_name: str):
    success = database.delete_knowledge_file(bot_id=bot_id, file_name=file_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove knowledge reference.")
    return {"status": "success", "message": f"Knowledge tracking for '{file_name}' removed."}

# --- 4. Extensions Engine ---
@app.get("/bots/{bot_id}/extensions")
def get_bot_extensions(bot_id: str):
    return database.get_enabled_tools(bot_id)

@app.post("/bots/{bot_id}/extensions/{extension_id}/toggle")
def toggle_bot_extension(bot_id: str, extension_id: str, payload: Optional[Dict[str, Any]] = None):
    """Toggles tool metrics. Safely parses optional dict bodies to block 422 schema errors."""
    current_tools = database.get_enabled_tools(bot_id)
    clean_ext = extension_id.strip().lower()
    
    if clean_ext in current_tools:
        current_tools.remove(clean_ext)
        action = "disabled"
    else:
        current_tools.append(clean_ext)
        action = "enabled"
        
    database.save_enabled_tools(bot_id, current_tools)
    return {
        "status": "success", 
        "bot_id": bot_id, 
        "extension_id": clean_ext, 
        "action": action, 
        "enabled_tools": current_tools
    }

# --- 5. Interface Core Runtime ---
@app.post("/bots/{bot_id}/chat")
def execute_chatbot_inference(bot_id: str, payload: ChatPayload):
    database.increment_conversation_count(bot_id)
    reply = ai_service.generate_bot_reply(
        bot_id=bot_id,
        user_message=payload.message,
        history=payload.history,
        temperature=payload.temperature
    )
    return {"reply": reply}

# =====================================================================
# 🏁 6. AUTOMATIC SERVER RUNTIME (PORT 8001 FORCE)
# =====================================================================
if __name__ == "__main__":
    import uvicorn
    # Forces the engine to launch on port 8001 with hot-reloading enabled
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)