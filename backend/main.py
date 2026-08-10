import os
import time
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Depends, Query, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

import ai_service
import database
from integrations import router as integrations_router

app = FastAPI(title="BotManager AI Backend API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Google Workspace integration routes (Gmail, Calendar, Drive)
app.include_router(integrations_router)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# JWT Security Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your_super_secret_jwt_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# --- REQUEST SCHEMAS ---

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = ""


class UserLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    owner_id: Optional[str] = "default_owner"


class PlanRequest(BaseModel):
    task_input: str


class ExecuteTaskRequest(BaseModel):
    task_input: str
    plan: List[Dict[str, str]]


class BotCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    system_prompt: Optional[str] = ""
    instructions: Optional[str] = ""
    first_message: Optional[str] = "Hello!"
    mode: Optional[str] = "chatbot"
    goal: Optional[str] = ""
    autonomy: Optional[str] = "approve"
    model_name: Optional[str] = "gpt-4o"
    owner_id: Optional[str] = "default_owner"


class BotUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    instructions: Optional[str] = None
    first_message: Optional[str] = None
    mode: Optional[str] = None
    goal: Optional[str] = None
    autonomy: Optional[str] = None
    model_name: Optional[str] = None


class ExtensionToggleRequest(BaseModel):
    extension_type: str  # e.g., lead_generation, faq_resolver, scheduler
    is_enabled: bool
    config: Optional[Dict[str, Any]] = {}


class LeadCaptureRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    notes: Optional[str] = ""


# --- AUTHENTICATION DEPENDENCY ---

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates JWT token and returns current authenticated user session data if present."""
    if not token:
        return {"sub": "default_owner"}
    try:
        payload = database.decode_jwt_token(token, SECRET_KEY, ALGORITHM)
        if not payload or "sub" not in payload:
            return {"sub": "default_owner"}
        return payload
    except Exception:
        return {"sub": "default_owner"}


# --- 1. SYSTEM & HEALTH CHECK ENDPOINTS ---

@app.get("/", tags=["System"])
def health_check():
    """1. Health Check Endpoint"""
    return {"status": "online", "service": "BotManager AI Engine Core"}


@app.get("/api/system/status", tags=["System"])
def system_status():
    """2. Detailed System Status & Database Diagnostics"""
    return {"status": "healthy", "database": "connected", "active_modules": 3}


# --- 2. AUTHENTICATION & LOGIN SYSTEM ---

@app.post("/api/auth/register", tags=["Authentication"])
def register_user(req: UserRegisterRequest):
    """Register a New Platform User Account"""
    try:
        user_id = database.create_user(email=req.email, password=req.password, full_name=req.full_name)
        if not user_id:
            raise HTTPException(status_code=400, detail="Email already registered or invalid input.")
        return {"message": "User registered successfully", "user_id": user_id, "email": req.email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login_user(req: UserLoginRequest):
    """Authenticate User and Generate JWT Access Token"""
    user = database.authenticate_user(email=req.email, password=req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = database.create_access_token(
        data={"sub": user["id"], "email": user["email"]},
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email": user["email"]
    }


@app.get("/api/auth/me", tags=["Authentication"])
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Retrieve Currently Authenticated User Profile"""
    user_profile = database.get_user_by_id(current_user["sub"])
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user_profile}


# --- 3. BOT MANAGEMENT CRUD ENDPOINTS (Supporting both /api/bots and /api/v1/bots) ---

@app.get("/api/bots", tags=["Bots Management"])
@app.get("/api/v1/bots", tags=["Bots Management"])
def list_bots(owner_id: Optional[str] = "default_owner", current_user: dict = Depends(get_current_user)):
    """List All Deployed Bots"""
    return {"bots": database.get_all_bots(owner_id or current_user["sub"])}


@app.post("/api/bots", tags=["Bots Management"])
@app.post("/api/v1/bots", tags=["Bots Management"])
def create_bot(req: BotCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create a New Bot Instance"""
    owner = req.owner_id if req.owner_id != "default_owner" else current_user["sub"]
    # Fallback system prompt if instructions are provided
    sys_prompt = req.system_prompt or req.instructions
    bot_id = database.create_bot(req.name, req.description, sys_prompt, req.model_name, owner)
    return {"message": "Bot created successfully", "bot_id": bot_id, "status": "success"}


@app.get("/api/bots/{bot_id}", tags=["Bots Management"])
@app.get("/api/v1/bots/{bot_id}", tags=["Bots Management"])
def get_bot(bot_id: str):
    """Get Bot Details by ID"""
    bot = database.get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"bot": bot}


@app.put("/api/bots/{bot_id}", tags=["Bots Management"])
@app.put("/api/v1/bots/{bot_id}", tags=["Bots Management"])
def update_bot(bot_id: str, req: BotUpdateRequest):
    """Update Bot Configuration"""
    update_data = req.dict(exclude_unset=True)
    if "instructions" in update_data and not update_data.get("system_prompt"):
        update_data["system_prompt"] = update_data["instructions"]
        
    success = database.update_bot(bot_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found or update failed")
    return {"message": "Bot updated successfully", "status": "success"}


@app.delete("/api/bots/{bot_id}", tags=["Bots Management"])
@app.delete("/api/v1/bots/{bot_id}", tags=["Bots Management"])
def delete_bot(bot_id: str):
    """Delete Bot Instance"""
    success = database.delete_bot(bot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"message": "Bot deleted successfully", "status": "success"}


# --- 4. AI CORE & AGENT EXECUTION ENDPOINTS ---

@app.post("/api/bots/{bot_id}/chat", tags=["AI Engine"])
@app.post("/api/v1/bots/{bot_id}/chat", tags=["AI Engine"])
def chat_with_bot(bot_id: str, req: ChatRequest):
    """Primary Chat Endpoint for Visitors Interacting with Deployed Bots"""
    try:
        reply = ai_service.generate_bot_reply(
            bot_id=bot_id,
            user_message=req.message,
            session_id=req.session_id,
            owner_id=req.owner_id or "default_owner"
        )
        return {"bot_id": bot_id, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bots/{bot_id}/plan", tags=["AI Engine"])
@app.post("/api/v1/bots/{bot_id}/plan", tags=["AI Engine"])
def create_bot_work_plan(bot_id: str, req: PlanRequest):
    """Generates Structured Reviewable Steps Before an Autonomous Agent Runs a Task"""
    try:
        plan = ai_service.build_work_plan(bot_id, req.task_input)
        return {"bot_id": bot_id, "plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bots/{bot_id}/execute", tags=["AI Engine"])
@app.post("/api/v1/bots/{bot_id}/execute", tags=["AI Engine"])
def execute_bot_task(bot_id: str, req: ExecuteTaskRequest):
    """Executes the Approved Task Plan Using the Bot's Configured Engine"""
    try:
        result = ai_service.execute_agent_task(bot_id, req.task_input, req.plan)
        return {"bot_id": bot_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 5. KNOWLEDGE BASE & VECTOR INGESTION ENDPOINTS ---

@app.post("/api/bots/{bot_id}/knowledge", tags=["Knowledge Base"])
@app.post("/api/v1/bots/{bot_id}/knowledge", tags=["Knowledge Base"])
def upload_knowledge_document(bot_id: str, file: UploadFile = File(...)):
    """Upload and Ingest Document / PDF into Bot Vector Knowledge Base"""
    try:
        doc_id = database.ingest_document(bot_id, file.filename, file.file.read())
        return {"message": "Document ingested successfully", "doc_id": doc_id, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bots/{bot_id}/knowledge", tags=["Knowledge Base"])
@app.get("/api/v1/bots/{bot_id}/knowledge", tags=["Knowledge Base"])
def list_knowledge_documents(bot_id: str):
    """List All Ingested Knowledge Base Documents for a Bot"""
    docs = database.get_bot_documents(bot_id)
    return {"bot_id": bot_id, "documents": docs}


@app.delete("/api/bots/{bot_id}/knowledge/{doc_id}", tags=["Knowledge Base"])
@app.delete("/api/v1/bots/{bot_id}/knowledge/{doc_id}", tags=["Knowledge Base"])
def delete_knowledge_document(bot_id: str, doc_id: str):
    """Delete a Specific Knowledge Document"""
    success = database.delete_bot_document(bot_id, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}


# --- 6. MODULAR EXTENSIONS & LEADS ENDPOINTS ---

@app.get("/api/bots/{bot_id}/extensions", tags=["Extensions & Leads"])
@app.get("/api/v1/bots/{bot_id}/extensions", tags=["Extensions & Leads"])
def get_bot_extensions(bot_id: str):
    """Get Configured Modular Extensions"""
    extensions = database.get_bot_extensions(bot_id)
    return {"bot_id": bot_id, "extensions": extensions}


@app.post("/api/bots/{bot_id}/extensions", tags=["Extensions & Leads"])
@app.post("/api/v1/bots/{bot_id}/extensions", tags=["Extensions & Leads"])
def toggle_bot_extension(bot_id: str, req: ExtensionToggleRequest):
    """Toggle or Configure Modular Extensions for Bot"""
    success = database.save_bot_extension(bot_id, req.extension_type, req.is_enabled, req.config)
    return {"message": f"Extension {req.extension_type} updated successfully", "status": req.is_enabled}


@app.get("/api/bots/{bot_id}/leads", tags=["Extensions & Leads"])
@app.get("/api/v1/bots/{bot_id}/leads", tags=["Extensions & Leads"])
def get_bot_leads(bot_id: str):
    """Retrieve Captured Leads from Lead Generation Extension"""
    leads = database.get_bot_leads(bot_id)
    return {"bot_id": bot_id, "leads": leads}


@app.post("/api/bots/{bot_id}/leads", tags=["Extensions & Leads"])
@app.post("/api/v1/bots/{bot_id}/leads", tags=["Extensions & Leads"])
def capture_bot_lead(bot_id: str, req: LeadCaptureRequest):
    """Manually Submit or Capture a Lead for the Bot"""
    lead_id = database.save_bot_lead(bot_id, req.name, req.email, req.phone, req.notes)
    return {"message": "Lead captured successfully", "lead_id": lead_id}


# --- 7. ANALYTICS & WIDGET TOKENS ENDPOINTS ---

@app.get("/api/bots/{bot_id}/analytics", tags=["Analytics & Embeds"])
@app.get("/api/v1/bots/{bot_id}/analytics", tags=["Analytics & Embeds"])
def get_bot_analytics(bot_id: str):
    """Get Bot Chat Metrics, Visitor Counts, and Activity Logs"""
    analytics = database.get_bot_analytics(bot_id)
    return {"bot_id": bot_id, "analytics": analytics}


@app.get("/api/bots/{bot_id}/widget-token", tags=["Analytics & Embeds"])
@app.get("/api/v1/bots/{bot_id}/widget-token", tags=["Analytics & Embeds"])
def get_bot_widget_token(bot_id: str):
    """Generate Secure Embed Token for Website Widget Integration"""
    token = database.get_or_create_embed_token(bot_id)
    return {"bot_id": bot_id, "embed_token": token}


# --- 8. GOOGLE OAUTH AUTHENTICATION ENDPOINTS ---

@app.get("/auth/google", tags=["Google Auth"])
def google_auth_redirect(owner_id: str = "default_owner"):
    """Initiates Google OAuth Flow for Google Workspace Integrations"""
    scope = (
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/gmail.send "
        "https://www.googleapis.com/auth/calendar "
        "https://www.googleapis.com/auth/drive.readonly"
    )
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&scope={scope}&access_type=offline&prompt=consent&state={owner_id}"
    )
    return RedirectResponse(auth_url)


@app.get("/auth/google/callback", tags=["Google Auth"])
def google_auth_callback(code: str, state: str = "default_owner"):
    """Handles OAuth Callback from Google"""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    try:
        res = requests.post(token_url, data=payload, timeout=10)
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to obtain token from Google: {res.text}")

        token_data = res.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        expires_at = time.time() + expires_in

        database.update_user_oauth_token(
            target_id=state,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

        return {"message": "Google Workspace successfully connected and authenticated!", "owner_id": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))