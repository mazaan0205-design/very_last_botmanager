import uuid
import uvicorn
import os
import io
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
import database
import ai_service
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

app = FastAPI(title="Bot Manager Backend")

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.endswith('.js'):
            response.headers['Cache-Control'] = 'no-store'
        return response

app.add_middleware(NoCacheMiddleware)


# Enable CORS for internal Laravel and external client website widgets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the SQLite database tables (Bypasses PostgreSQL connection drops)
database.init_db()

# Mount the static folders safely
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
try:
    app.mount("/embed", StaticFiles(directory="static/embed"), name="embed")
except Exception:
    pass

# --- REQUEST PAYLOAD SCHEMAS ---
class BotConfigPayload(BaseModel):
    name: str
    description: Optional[str] = "Active AI Automation Agent"
    instructions: str = Field(default="You are a helpful AI assistant.", validation_alias="system_instruction")
    engine: Optional[str] = "llama-3.3-70b-versatile"
    temperature: Optional[float] = 0.3
    guardrails: Optional[bool] = True

    model_config = ConfigDict(extra="allow", populate_by_name=True)

class ChatPayload(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: List[Dict[str, str]] = []

    model_config = ConfigDict(extra="allow")

class UrlImportRequest(BaseModel):
    bot_id: str
    url: str


# --- BOT CONFIGURATION ROUTES ---
@app.get("/")
async def welcome():
    return 'backend is running'

@app.get("/bots/list")
async def list_all_configured_bots():
    return database.get_all_bots_with_stats()

@app.get("/bots/{bot_id}")
async def get_single_bot_configuration(bot_id: str):
    config = database.get_bot_config(bot_id)
    if not config:
        raise HTTPException(status_code=404, detail="Bot configuration not found.")
    return config

@app.post("/bots/update/{bot_id}")
async def save_or_modify_bot_profile(bot_id: str, payload: BotConfigPayload):
    if bot_id == "new":
        target_id = str(uuid.uuid4())
    else:
        target_id = bot_id

    if not payload.description or payload.description.strip() == "":
        safe_description = "Active AI Automation Agent"
    else:
        safe_description = payload.description

    safe_instructions = payload.instructions
    guardrail_flag = 1 if payload.guardrails else 0

    saved_successfully = database.save_bot(
        bot_id=target_id,
        name=payload.name,
        description=safe_description,
        instructions=safe_instructions,
        engine=payload.engine if payload.engine else "llama-3.3-70b-versatile",
        temperature=payload.temperature if payload.temperature is not None else 0.3,
        guardrails=guardrail_flag
    )

    if not saved_successfully:
        raise HTTPException(status_code=500, detail="Database write failure.")

    return {
        "status": "success",
        "message": "Bot saved successfully.",
        "bot_id": target_id
    }

@app.delete("/bots/{bot_id}")
async def terminate_bot_configuration(bot_id: str):
    if not database.delete_bot_from_db(bot_id):
        raise HTTPException(status_code=500, detail="Failed to delete bot.")
    return {"status": "success", "message": "Bot profile deleted successfully."}


# --- KNOWLEDGE BASE MANAGEMENT ENDPOINTS ---

@app.post("/bots/{bot_id}/knowledge/upload")
async def upload_bot_knowledge_file(bot_id: str, file: UploadFile = File(...)):
    if bot_id in ["new", "playground"]:
        raise HTTPException(status_code=400, detail="Please save your bot before uploading document files.")

    try:
        filename = file.filename.lower()
        contents = await file.read()
        text_content = ""

        if filename.endswith(".pdf"):
            try:
                pdf_stream = io.BytesIO(contents)
                pdf_reader = PdfReader(pdf_stream)
                extracted_pages = []
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_pages.append(page_text)
                text_content = "\n\n".join(extracted_pages)
            except Exception as pdf_err:
                raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(pdf_err)}")
        else:
            try:
                text_content = contents.decode("utf-8")
            except UnicodeDecodeError:
                text_content = contents.decode("latin-1")

        if not text_content.strip():
            raise HTTPException(status_code=400, detail="The uploaded document contains no readable text content.")

        paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]

        for paragraph in paragraphs:
            database.add_knowledge_content(bot_id=bot_id, file_name=file.filename, content=paragraph)

        return {"status": "success", "message": f"Successfully loaded {len(paragraphs)} facts from {file.filename}."}
        
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File tracking server error: {str(e)}")

@app.post("/bots/knowledge/url")
async def import_knowledge_url(data: UrlImportRequest):
    if data.bot_id in ["new", "playground"]:
        raise HTTPException(status_code=400, detail="Please save your bot before tracking web assets.")
        
    try:
        placeholder_text = f"Content extracted from website resource: {data.url}."
        database.add_knowledge_content(bot_id=data.bot_id, file_name=data.url, content=placeholder_text)
            
        return {"status": "success", "bot_id": data.bot_id, "url": data.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bots/{bot_id}/knowledge")
async def list_bot_knowledge_sources(bot_id: str):
    if bot_id in ["new", "playground"]:
        return []
        
    raw_sources = database.get_bot_knowledge_sources(bot_id)
    processed_sources = []
    for source in raw_sources:
        processed_sources.append({
            "id": source["source_name"],  
            "source_name": source["source_name"],
            "type": source["type"],
            "sync_status": source["sync_status"],
            "size": source["size"]
        })
    return processed_sources

@app.delete("/bots/{bot_id}/knowledge/{file_name:path}")
async def delete_bot_knowledge_source(bot_id: str, file_name: str):
    if bot_id in ["new", "playground"]:
        raise HTTPException(status_code=400, detail="Invalid bot target profile context.")

    if database.delete_knowledge_file(bot_id, file_name):
        return {"status": "success", "message": f"Successfully dropped source document: {file_name}"}
        
    raise HTTPException(status_code=500, detail="Failed to drop document data reference track.")


# --- EXECUTION CHAT PIPELINE ---

@app.post("/bots/{bot_id}/chat")
async def execute_chatbot_inference(bot_id: str, payload: ChatPayload):
    if bot_id in ["new", "playground"]:
        response_string = ai_service.generate_bot_reply(bot_id="new", user_message=payload.message, history=payload.history, temperature=0.3)
        return {"status": "success", "reply": response_string, "session_id": "playground"}

    bot_config = database.get_bot_config(bot_id)
    if not bot_config:
        raise HTTPException(status_code=404, detail="Chatbot matrix profile not found.")

    active_session_id = payload.session_id if payload.session_id else str(uuid.uuid4())
    database.create_or_get_session(active_session_id, bot_id, payload.message)
    database.save_chat_message(active_session_id, "user", payload.message)

    response_string = ai_service.generate_bot_reply(
        bot_id=bot_id,
        user_message=payload.message,
        history=payload.history,
        temperature=float(bot_config.get("temperature", 0.3))
    )

    database.save_chat_message(active_session_id, "assistant", response_string)
    database.increment_conversation_count(bot_id)

    return {"status": "success", "reply": response_string, "session_id": active_session_id}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)