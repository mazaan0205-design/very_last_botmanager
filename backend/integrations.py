import os
import json
import base64
import time
import datetime
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any
import requests
import database
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


def get_valid_token(target_id: str) -> Optional[str]:
    """
    Retrieves a valid Google OAuth access token for the given user/owner.
    If the access token is expired, it attempts to refresh it using the stored refresh token.
    """
    token_data = database.get_user_oauth_token(target_id)
    if not token_data:
        # Fallback check if target_id itself is already a raw token string passed in testing
        if len(target_id) > 40 and not target_id.startswith("owner_") and not target_id.startswith("session_"):
            return target_id
        return None

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_at = token_data.get("expires_at", 0)

    # Check if token is expired or expiring within 60 seconds
    if time.time() >= (expires_at - 60) and refresh_token:
        try:
            payload = {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            response = requests.post(GOOGLE_TOKEN_URL, data=payload, timeout=10)
            if response.status_code == 200:
                new_data = response.json()
                access_token = new_data.get("access_token")
                expires_in = new_data.get("expires_in", 3600)
                
                # Update stored token in database
                database.update_user_oauth_token(
                    target_id, 
                    access_token=access_token, 
                    expires_at=time.time() + expires_in
                )
            else:
                print(f"[OAuth Refresh Error]: {response.text}")
                return None
        except Exception as e:
            print(f"[OAuth Exception]: {e}")
            return None

    return access_token


# --- GMAIL INTEGRATIONS ---

def get_recent_emails(target_id: str, max_results: int = 5) -> str:
    """Fetch recent inbox emails from Gmail API."""
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}&q=label:INBOX"
    headers = {"Authorization": f"Bearer {target_id}"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Error fetching emails: {res.text}"
        
        data = res.json()
        messages = data.get("messages", [])
        if not messages:
            return "No recent messages found in inbox."

        summaries = []
        for msg in messages:
            msg_id = msg["id"]
            detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date"
            detail_res = requests.get(detail_url, headers=headers, timeout=5)
            if detail_res.status_code == 200:
                m_data = detail_res.json()
                headers_list = m_data.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "No Subject")
                sender = next((h["value"] for h in headers_list if h["name"] == "From"), "Unknown Sender")
                snippet = m_data.get("snippet", "")
                summaries.append(f"- From: {sender} | Subject: {subject} | Snippet: {snippet}")

        return "Recent Emails:\n" + "\n".join(summaries)
    except Exception as e:
        return f"Exception while fetching emails: {e}"


def send_email(target_id_or_token: str, to: str, subject: str, body: str) -> str:
    """Send an outbound email via Gmail API."""
    message = MIMEText(body)
    message["To"] = to
    message["Subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    headers = {
        "Authorization": f"Bearer {target_id_or_token}",
        "Content-Type": "application/json"
    }
    payload = {"raw": raw_message}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code in [200, 201]:
            return f"Successfully sent email to {to} with subject '{subject}'."
        return f"Failed to send email: {res.text}"
    except Exception as e:
        return f"Exception while sending email: {e}"


# --- GOOGLE CALENDAR INTEGRATIONS ---

def get_calendar_events(target_id: str, max_results: int = 5) -> str:
    """Retrieve upcoming Google Calendar events."""
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={now_iso}&maxResults={max_results}&singleEvents=true&orderBy=startTime"
    headers = {"Authorization": f"Bearer {target_id}"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Error fetching calendar events: {res.text}"

        items = res.json().get("items", [])
        if not items:
            return "No upcoming calendar events found."

        event_list = []
        for event in items:
            summary = event.get("summary", "Untitled Event")
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
            end = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", ""))
            event_list.append(f"- {summary} (From: {start} To: {end})")

        return "Upcoming Calendar Events:\n" + "\n".join(event_list)
    except Exception as e:
        return f"Exception while fetching calendar events: {e}"


def create_calendar_event(
    target_id_or_token: str, 
    summary: str, 
    start_time: str, 
    end_time: str, 
    description: str = "", 
    attendees: List[str] = []
) -> str:
    """Schedule a new meeting or event on Google Calendar."""
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {
        "Authorization": f"Bearer {target_id_or_token}",
        "Content-Type": "application/json"
    }
    
    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
        "attendees": [{"email": email} for email in attendees]
    }

    try:
        res = requests.post(url, headers=headers, json=event_body, timeout=10)
        if res.status_code in [200, 201]:
            event_data = res.json()
            return f"Successfully scheduled event '{summary}' (ID: {event_data.get('id')})."
        return f"Failed to create calendar event: {res.text}"
    except Exception as e:
        return f"Exception while creating calendar event: {e}"


# --- GOOGLE DRIVE INTEGRATIONS ---

def search_drive_files(target_id: str, query: str = "", max_results: int = 5) -> str:
    """Search for files or documents in Google Drive."""
    q_param = f"fullText contains '{query}'" if query else ""
    url = f"https://www.googleapis.com/drive/v3/files?pageSize={max_results}"
    if q_param:
        url += f"&q={requests.utils.quote(q_param)}"

    headers = {"Authorization": f"Bearer {target_id}"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Error searching drive files: {res.text}"

        files = res.json().get("files", [])
        if not files:
            return "No matching Google Drive files found."

        file_list = [f"- {f.get('name')} (ID: {f.get('id')}, Type: {f.get('mimeType')})" for f in files]
        return "Google Drive Search Results:\n" + "\n".join(file_list)
    except Exception as e:
        return f"Exception while searching Google Drive: {e}"


# --- FASTAPI ENDPOINTS ---

class SendEmailRequest(BaseModel):
    target_id: str
    to: str
    subject: str
    body: str

class CreateEventRequest(BaseModel):
    target_id: str
    summary: str
    start_time: str
    end_time: str
    description: Optional[str] = ""
    attendees: Optional[List[str]] = []


@router.get("/gmail/recent")
def api_get_recent_emails(target_id: str = Query(..., description="User ID or OAuth Token"), max_results: int = 5):
    token = get_valid_token(target_id)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or missing OAuth token.")
    return {"result": get_recent_emails(token, max_results)}


@router.post("/gmail/send")
def api_send_email(payload: SendEmailRequest):
    token = get_valid_token(payload.target_id)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or missing OAuth token.")
    result = send_email(token, payload.to, payload.subject, payload.body)
    return {"result": result}


@router.get("/calendar/events")
def api_get_calendar_events(target_id: str = Query(..., description="User ID or OAuth Token"), max_results: int = 5):
    token = get_valid_token(target_id)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or missing OAuth token.")
    return {"result": get_calendar_events(token, max_results)}


@router.post("/calendar/events")
def api_create_calendar_event(payload: CreateEventRequest):
    token = get_valid_token(payload.target_id)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or missing OAuth token.")
    result = create_calendar_event(
        token, 
        payload.summary, 
        payload.start_time, 
        payload.end_time, 
        payload.description, 
        payload.attendees
    )
    return {"result": result}


@router.get("/drive/search")
def api_search_drive_files(target_id: str = Query(..., description="User ID or OAuth Token"), query: str = "", max_results: int = 5):
    token = get_valid_token(target_id)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or missing OAuth token.")
    return {"result": search_drive_files(token, query, max_results)}