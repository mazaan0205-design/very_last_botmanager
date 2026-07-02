import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "bot_manager.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # --- CORE TABLES ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS bots (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, instructions TEXT NOT NULL, engine TEXT DEFAULT 'llama-3.3-70b-versatile', temperature REAL DEFAULT 0.3, guardrails INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bot_statistics (bot_id TEXT PRIMARY KEY, conversations INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_sessions (session_id TEXT PRIMARY KEY, bot_id TEXT NOT NULL, title TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bot_knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id TEXT NOT NULL, file_name TEXT NOT NULL, content TEXT NOT NULL, FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE)''')
    
    # --- AGENT EXTENSION TABLES ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS bot_extensions (bot_id TEXT PRIMARY KEY, enabled_tools TEXT, FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS captured_events (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id TEXT, type TEXT, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE)''')
    
    conn.commit()
    conn.close()

# --- BOT MANAGEMENT LOGIC ---
def save_bot(bot_id: str, name: str, description: str, instructions: str, engine: str, temperature: float, guardrails: int) -> bool:
    try:
        clean_bot_id = str(bot_id).strip()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO bots (id, name, description, instructions, engine, temperature, guardrails) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description, instructions=excluded.instructions, engine=excluded.engine, temperature=excluded.temperature, guardrails=excluded.guardrails""", (clean_bot_id, name, description, instructions, engine, temperature, guardrails))
        cursor.execute("INSERT OR IGNORE INTO bot_statistics (bot_id, conversations) VALUES (?, 0)", (clean_bot_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database write exception: {e}"); return False

def get_bot_config(bot_id: str) -> Optional[Dict[str, Any]]:
    clean_id = str(bot_id).strip()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, instructions, engine, temperature, guardrails FROM bots WHERE id = ?", (clean_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": str(row[0]), "name": row[1], "description": row[2] if row[2] else "", "instructions": row[3], "engine": row[4], "temperature": row[5], "guardrails": row[6]}
    return None

def delete_bot_from_db(bot_id: str) -> bool:
    try:
        clean_id = str(bot_id).strip()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bots WHERE id = ?", (clean_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Delete transaction dropped: {e}"); return False

def get_all_bots_with_stats() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT b.id, b.name, b.description, b.instructions, b.engine, b.temperature, b.guardrails, COALESCE(s.conversations, 0) FROM bots b LEFT JOIN bot_statistics s ON b.id = s.bot_id""")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": str(r[0]), "name": r[1], "description": r[2] if r[2] else "", "instructions": r[3], "engine": r[4], "temperature": r[5], "guardrails": r[6], "statistics": {"conversations": r[7]}} for r in rows]

def increment_conversation_count(bot_id: str):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE bot_statistics SET conversations = conversations + 1 WHERE bot_id = ?", (str(bot_id).strip(),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Stats error: {e}")

# --- KNOWLEDGE BASE ENGINE ---
def add_knowledge_content(bot_id: str, file_name: str, content: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bot_knowledge (bot_id, file_name, content) VALUES (?, ?, ?)", (str(bot_id).strip(), file_name, content))
    conn.commit()
    conn.close()

def query_bot_knowledge(bot_id: str, user_query: str) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM bot_knowledge WHERE bot_id = ?", (str(bot_id).strip(),))
    rows = cursor.fetchall()
    conn.close()
    matched_chunks = [r[0] for r in rows if any(w in r[0].lower() for w in user_query.lower().split() if len(w) > 3)][:3]
    return "\n".join(matched_chunks)

def get_bot_knowledge_sources(bot_id: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, COUNT(id) FROM bot_knowledge WHERE bot_id = ? GROUP BY file_name", (str(bot_id).strip(),))
    rows = cursor.fetchall()
    conn.close()
    return [{"source_name": r[0], "type": "URL" if r[0].startswith("http") else "TXT", "sync_status": "Ready", "size": f"{r[1]} chunks"} for r in rows]

def delete_knowledge_file(bot_id: str, file_name: str) -> bool:
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bot_knowledge WHERE bot_id = ? AND file_name = ?", (str(bot_id).strip(), file_name))
        conn.commit()
        conn.close()
        return True
    except: return False

# --- CONVERSATION SESSIONS ---
def create_or_get_session(session_id: str, bot_id: str, first_message: str) -> str:
    clean_sid, clean_bid = str(session_id).strip(), str(bot_id).strip()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id FROM chat_sessions WHERE session_id = ?", (clean_sid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO chat_sessions (session_id, bot_id, title) VALUES (?, ?, ?)", (clean_sid, clean_bid, (first_message[:20] + "...")))
        conn.commit()
    conn.close()
    return clean_sid

def save_chat_message(session_id: str, role: str, content: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (str(session_id).strip(), role, content))
    conn.commit()
    conn.close()

def get_session_history(session_id: str) -> List[Dict[str, str]]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC", (str(session_id).strip(),))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

# --- AGENT EXTENSIONS LOGIC ---
def get_enabled_tools(bot_id: str) -> List[str]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT enabled_tools FROM bot_extensions WHERE bot_id = ?", (str(bot_id).strip(),))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else []

def save_enabled_tools(bot_id: str, tools: List[str]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO bot_extensions (bot_id, enabled_tools) VALUES (?, ?)", (str(bot_id).strip(), json.dumps(tools)))
    conn.commit()
    conn.close()

def log_captured_event(bot_id: str, event_type: str, data: Dict[str, Any]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO captured_events (bot_id, type, data) VALUES (?, ?, ?)", (str(bot_id).strip(), event_type, json.dumps(data)))
    conn.commit()
    conn.close()

# --- BACKEND DEVELOPER COMPATIBILITY ALIAS ---
def get_extensions_for_bot(bot_id: str) -> list:
    """Resolves the AttributeError by mapping the developer's requested name to the table tool reader."""
    return get_enabled_tools(bot_id)