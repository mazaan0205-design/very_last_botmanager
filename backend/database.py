import os
import time
import uuid
import json
from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, Column, String, Text, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from jose import jwt

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./botmanager.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- DATABASE MODELS ---

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String, default="")


class BotConfigModel(Base):
    __tablename__ = "bot_configs"
    bot_id = Column(String, primary_key=True, index=True)
    name = Column(String, default="Assistant")
    description = Column(String, default="")
    system_prompt = Column(Text, default="")
    goal = Column(String, default="Help users efficiently.")
    instructions = Column(Text, default="You are a helpful AI assistant.")
    engine = Column(String, default="llama-3.3-70b-versatile")
    model_name = Column(String, default="gpt-4o")
    temperature = Column(Float, default=0.3)
    autonomy = Column(String, default="approve")
    conversation_count = Column(Integer, default=0)
    owner_id = Column(String, default="default_owner", index=True)


class BotToolModel(Base):
    __tablename__ = "bot_tools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(String, index=True)
    tool_name = Column(String, index=True)


class BotKnowledgeModel(Base):
    __tablename__ = "bot_knowledge"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(String, index=True)
    filename = Column(String, default="document.txt")
    content = Column(Text)


class BotExtensionModel(Base):
    __tablename__ = "bot_extensions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(String, index=True)
    extension_type = Column(String, index=True)
    is_enabled = Column(Integer, default=0)
    config_json = Column(Text, default="{}")


class BotLeadModel(Base):
    __tablename__ = "bot_leads"
    id = Column(String, primary_key=True, index=True)
    bot_id = Column(String, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String, default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class EmbedTokenModel(Base):
    __tablename__ = "embed_tokens"
    bot_id = Column(String, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"
    session_id = Column(String, primary_key=True, index=True)
    bot_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class UserOAuthTokenModel(Base):
    __tablename__ = "user_oauth_tokens"
    target_id = Column(String, primary_key=True, index=True)  # owner_id or user email/id
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(Float)


# Initialize tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- AUTH & USER FUNCTIONS ---

def create_user(email: str, password: str, full_name: str = "") -> Optional[str]:
    db = SessionLocal()
    try:
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            return None
        user_id = str(uuid.uuid4())
        user = UserModel(id=user_id, email=email, password=password, full_name=full_name)
        db.add(user)
        db.commit()
        return user_id
    finally:
        db.close()


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == email, UserModel.password == password).first()
        if not user:
            return None
        return {"id": user.id, "email": user.email, "full_name": user.full_name}
    finally:
        db.close()


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return {"id": user_id, "email": "user@example.com", "full_name": "Developer"}
        return {"id": user.id, "email": user.email, "full_name": user.full_name}
    finally:
        db.close()


def create_access_token(data: dict, secret_key: str, algorithm: str = "HS256", expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=1440))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_jwt_token(token: str, secret_key: str, algorithm: str = "HS256") -> Optional[dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except Exception:
        return None


# --- BOT MANAGEMENT CRUD FUNCTIONS ---

def create_bot(name: str, description: str, system_prompt: str, model_name: str, owner_id: str) -> str:
    db = SessionLocal()
    try:
        bot_id = str(uuid.uuid4())
        bot = BotConfigModel(
            bot_id=bot_id,
            name=name,
            description=description or "",
            system_prompt=system_prompt or "",
            instructions=system_prompt or "You are a professional AI assistant.",
            model_name=model_name or "gpt-4o",
            engine=model_name or "llama-3.3-70b-versatile",
            owner_id=owner_id or "default_owner"
        )
        db.add(bot)
        db.commit()
        return bot_id
    finally:
        db.close()


def get_all_bots(owner_id: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        bots = db.query(BotConfigModel).filter(
            (BotConfigModel.owner_id == owner_id) | (owner_id == "default_owner")
        ).all()
        result = []
        for b in bots:
            result.append({
                "id": b.bot_id,
                "bot_id": b.bot_id,
                "name": b.name,
                "description": b.description,
                "system_prompt": b.system_prompt,
                "instructions": b.instructions,
                "model_name": b.model_name,
                "engine": b.engine,
                "temperature": b.temperature,
                "autonomy": b.autonomy,
                "conversation_count": b.conversation_count,
                "owner_id": b.owner_id
            })
        return result
    finally:
        db.close()


def get_bot_by_id(bot_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        b = db.query(BotConfigModel).filter(BotConfigModel.bot_id == bot_id).first()
        if not b:
            return None
        return {
            "id": b.bot_id,
            "bot_id": b.bot_id,
            "name": b.name,
            "description": b.description,
            "system_prompt": b.system_prompt,
            "instructions": b.instructions,
            "model_name": b.model_name,
            "engine": b.engine,
            "temperature": b.temperature,
            "autonomy": b.autonomy,
            "conversation_count": b.conversation_count,
            "owner_id": b.owner_id
        }
    finally:
        db.close()


def update_bot(bot_id: str, update_data: Dict[str, Any]) -> bool:
    db = SessionLocal()
    try:
        b = db.query(BotConfigModel).filter(BotConfigModel.bot_id == bot_id).first()
        if not b:
            return False
        for key, val in update_data.items():
            if hasattr(b, key) and val is not None:
                setattr(b, key, val)
        db.commit()
        return True
    finally:
        db.close()


def delete_bot(bot_id: str) -> bool:
    db = SessionLocal()
    try:
        b = db.query(BotConfigModel).filter(BotConfigModel.bot_id == bot_id).first()
        if not b:
            return False
        db.delete(b)
        db.commit()
        return True
    finally:
        db.close()


def get_bot_config(bot_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        bot = db.query(BotConfigModel).filter(BotConfigModel.bot_id == bot_id).first()
        if not bot:
            return {
                "bot_id": bot_id,
                "name": "BotManager Assistant",
                "goal": "Answer questions and automate tasks.",
                "instructions": "You are a professional AI assistant.",
                "engine": "llama-3.3-70b-versatile",
                "temperature": 0.3,
                "autonomy": "approve"
            }
        return {
            "bot_id": bot.bot_id,
            "name": bot.name,
            "goal": bot.goal,
            "instructions": bot.instructions,
            "engine": bot.engine,
            "temperature": bot.temperature,
            "autonomy": bot.autonomy,
            "conversation_count": bot.conversation_count
        }
    finally:
        db.close()


def get_enabled_tools(bot_id: str) -> List[str]:
    db = SessionLocal()
    try:
        tools = db.query(BotToolModel).filter(BotToolModel.bot_id == bot_id).all()
        return [t.tool_name for t in tools]
    finally:
        db.close()


# --- KNOWLEDGE BASE FUNCTIONS ---

def ingest_document(bot_id: str, filename: str, file_bytes: bytes) -> str:
    db = SessionLocal()
    try:
        doc_id = str(uuid.uuid4())
        try:
            content_str = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            content_str = str(file_bytes)
        
        doc = BotKnowledgeModel(bot_id=bot_id, filename=filename, content=content_str)
        db.add(doc)
        db.commit()
        return doc_id
    finally:
        db.close()


def get_bot_documents(bot_id: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        docs = db.query(BotKnowledgeModel).filter(BotKnowledgeModel.bot_id == bot_id).all()
        return [{"doc_id": str(d.id), "filename": getattr(d, 'filename', 'document.txt'), "snippet": d.content[:100]} for d in docs]
    finally:
        db.close()


def delete_bot_document(bot_id: str, doc_id: str) -> bool:
    db = SessionLocal()
    try:
        query_filter = BotKnowledgeModel.bot_id == bot_id
        if doc_id.isdigit():
            query_filter = (BotKnowledgeModel.bot_id == bot_id) & (BotKnowledgeModel.id == int(doc_id))
        doc = db.query(BotKnowledgeModel).filter(query_filter).first()
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        return True
    except Exception:
        return False
    finally:
        db.close()


def query_bot_knowledge(bot_id: str, query: str) -> str:
    db = SessionLocal()
    try:
        k_items = db.query(BotKnowledgeModel).filter(BotKnowledgeModel.bot_id == bot_id).all()
        if not k_items:
            return ""
        matched = [item.content for item in k_items if any(word.lower() in item.content.lower() for word in query.split() if len(word) > 3)]
        if not matched:
            return "\n".join([item.content for item in k_items[:3]])
        return "\n".join(matched)
    finally:
        db.close()


# --- CHAT & SESSIONS ---

def create_or_get_session(session_id: str, bot_id: str, initial_message: str = "") -> str:
    db = SessionLocal()
    try:
        session = db.query(ChatSessionModel).filter(ChatSessionModel.session_id == session_id).first()
        if not session:
            session = ChatSessionModel(session_id=session_id, bot_id=bot_id)
            db.add(session)
            db.commit()
        return session_id
    finally:
        db.close()


def save_chat_message(session_id: str, role: str, content: str):
    db = SessionLocal()
    try:
        msg = ChatMessageModel(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()


def get_session_history(session_id: str, limit: int = 12) -> List[Dict[str, str]]:
    db = SessionLocal()
    try:
        messages = db.query(ChatMessageModel).filter(ChatMessageModel.session_id == session_id)\
                     .order_by(ChatMessageModel.timestamp.asc()).all()
        history = [{"role": m.role, "content": m.content} for m in messages]
        return history[-limit:] if len(history) > limit else history
    finally:
        db.close()


def increment_conversation_count(bot_id: str):
    db = SessionLocal()
    try:
        bot = db.query(BotConfigModel).filter(BotConfigModel.bot_id == bot_id).first()
        if bot:
            bot.conversation_count = (bot.conversation_count or 0) + 1
            db.commit()
    finally:
        db.close()


# --- EXTENSIONS, LEADS & ANALYTICS ---

def get_bot_extensions(bot_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        exts = db.query(BotExtensionModel).filter(BotExtensionModel.bot_id == bot_id).all()
        res = {}
        for e in exts:
            try:
                cfg = json.loads(e.config_json)
            except Exception:
                cfg = {}
            res[e.extension_type] = {"is_enabled": bool(e.is_enabled), "config": cfg}
        return res
    finally:
        db.close()


def save_bot_extension(bot_id: str, extension_type: str, is_enabled: bool, config: Dict[str, Any]) -> bool:
    db = SessionLocal()
    try:
        ext = db.query(BotExtensionModel).filter(
            BotExtensionModel.bot_id == bot_id,
            BotExtensionModel.extension_type == extension_type
        ).first()
        
        cfg_str = json.dumps(config or {})
        if not ext:
            ext = BotExtensionModel(
                bot_id=bot_id,
                extension_type=extension_type,
                is_enabled=1 if is_enabled else 0,
                config_json=cfg_str
            )
            db.add(ext)
        else:
            ext.is_enabled = 1 if is_enabled else 0
            ext.config_json = cfg_str
        db.commit()
        return True
    finally:
        db.close()


def get_bot_leads(bot_id: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        leads = db.query(BotLeadModel).filter(BotLeadModel.bot_id == bot_id).all()
        return [{
            "lead_id": l.id,
            "name": l.name,
            "email": l.email,
            "phone": l.phone,
            "notes": l.notes,
            "created_at": l.created_at.isoformat() if l.created_at else ""
        } for l in leads]
    finally:
        db.close()


def save_bot_lead(bot_id: str, name: str, email: str, phone: Optional[str], notes: Optional[str]) -> str:
    db = SessionLocal()
    try:
        lead_id = str(uuid.uuid4())
        lead = BotLeadModel(
            id=lead_id,
            bot_id=bot_id,
            name=name,
            email=email,
            phone=phone or "",
            notes=notes or ""
        )
        db.add(lead)
        db.commit()
        return lead_id
    finally:
        db.close()


def get_bot_analytics(bot_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        bot = db.query(BotConfigModel).filter(BotConfigModel.bot_id == bot_id).first()
        conv_count = bot.conversation_count if bot else 0
        leads_count = db.query(BotLeadModel).filter(BotLeadModel.bot_id == bot_id).count()
        return {
            "total_chats": conv_count,
            "total_leads": leads_count,
            "active_visitors": conv_count * 2
        }
    finally:
        db.close()


def get_or_create_embed_token(bot_id: str) -> str:
    db = SessionLocal()
    try:
        record = db.query(EmbedTokenModel).filter(EmbedTokenModel.bot_id == bot_id).first()
        if record:
            return record.token
        token = f"embed_{uuid.uuid4().hex}"
        new_rec = EmbedTokenModel(bot_id=bot_id, token=token)
        db.add(new_rec)
        db.commit()
        return token
    finally:
        db.close()


# --- OAUTH TOKENS ---

def get_user_oauth_token(target_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        token_record = db.query(UserOAuthTokenModel).filter(UserOAuthTokenModel.target_id == target_id).first()
        if not token_record:
            return None
        return {
            "access_token": token_record.access_token,
            "refresh_token": token_record.refresh_token,
            "expires_at": token_record.expires_at
        }
    finally:
        db.close()


def update_user_oauth_token(target_id: str, access_token: str, expires_at: float, refresh_token: Optional[str] = None):
    db = SessionLocal()
    try:
        token_record = db.query(UserOAuthTokenModel).filter(UserOAuthTokenModel.target_id == target_id).first()
        if not token_record:
            token_record = UserOAuthTokenModel(
                target_id=target_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            db.add(token_record)
        else:
            token_record.access_token = access_token
            if refresh_token:
                token_record.refresh_token = refresh_token
            token_record.expires_at = expires_at
        db.commit()
    finally:
        db.close()


def clear_user_oauth_token(target_id: str) -> bool:
    """Removes a stored Google OAuth token, effectively disconnecting the account."""
    db = SessionLocal()
    try:
        token_record = db.query(UserOAuthTokenModel).filter(UserOAuthTokenModel.target_id == target_id).first()
        if not token_record:
            return False
        db.delete(token_record)
        db.commit()
        return True
    finally:
        db.close()
