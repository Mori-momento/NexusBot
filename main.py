import os
import requests
import json
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime


# --- IMPORTANT: Add your Telegram Bot Token here ---
# In production, you would use an environment variable for this.
TELEGRAM_TOKEN = "7714180083:AAG2NoBRWnj2FL6BxTzykm_fDUaR-RKrA3A" # <--- PASTE YOUR TOKEN HERE

# --- 1. Initialize the AI Model and Chain ---

# Force env for auth (covers local/Render; no param needed)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "AIzaSyDqRByCe-7kJBU8LebAun56ZleKEt7GG54")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)  # Auto-uses env

prompt = ChatPromptTemplate.from_template("""
You are an intelligent triaging agent for a productivity app.
Classify the user's text into one of: 'Idea', 'Flexible Task', or 'Time-Blocked Task'.
Respond ONLY with valid JSON: {{"category": "Idea", "confidence": 0.85}}  # confidence 0-1, high if obvious (1=dead sure, 0=clueless).

User Text: "{user_input}"
""")
chain = prompt | llm | StrOutputParser()

# --- 2. Initialize the FastAPI Application ---
app = FastAPI()

# --- 3. Update Pydantic models to capture the 'chat_id' ---
class TelegramChat(BaseModel):
    id: int

class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: str

class TelegramWebhookPayload(BaseModel):
    message: TelegramMessage

# --- 4. Define the function to send a reply ---
def send_telegram_reply(chat_id: int, text: str):
    """Sends a message back to the user on Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=payload)
        print("Reply sent! Response:", response.json())
    except Exception as e:
        print(f"Error sending reply: {e}")

# --- 5. Update the webhook to handle the reply ---
@app.post("/webhook")
def handle_webhook(payload: TelegramWebhookPayload):
    user_message = payload.message.text
    chat_id = payload.message.chat.id
    
    try:
        classification = chain.invoke({"user_input": user_message})
    except Exception as e:
        print(f"Chain invoke fail: {e}")
        classification = '{"category": "Idea", "confidence": 1.0}'
    
    # Parse JSON output
    try:
        parsed = json.loads(classification)
        category = parsed['category'].strip()
        confidence = float(parsed['confidence'])
    except (json.JSONDecodeError, KeyError, ValueError):
        category, confidence = "Idea", 0.5
        print("JSON parse fail—defaulted to Idea.")

    # Simple in-mem store (chat_id -> list of dicts); upgrade to SQLite next sprint
    user_entries = {}  # Global dict for MVP (not thread-safe; fine for solo bot)

    if confidence < 0.7:
        clarify_map = {
            "Idea": "Sounds like a creative spark—is this an Idea to park, or a task to schedule? Reply: Idea / Task / Time.",
            "Flexible Task": "Quick to-do? Confirm: Flexible Task (no deadline) or Time-Blocked (calendar slot)? Reply: Flexible / Time.",
            "Time-Blocked Task": "Needs a slot? When—Flexible anytime or Time-Blocked specific? Reply: Flexible / Time."
        }
        reply_text = f"Unclear on '{user_message[:50]}...' {clarify_map.get(category, 'What fits: Idea/Task/Time?')}"
        # TODO: Add user state dict for multi-turn (e.g., pending[chat_id] = {'guessed': category})
    else:
        entry = {
            "text": user_message,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "chat_id": chat_id
        }
        if chat_id not in user_entries:
            user_entries[chat_id] = []
        user_entries[chat_id].append(entry)
        print(f"Saved entry for {chat_id}: {category} - {user_message[:30]}...")
        reply_text = f"Got it! Filed '{user_message[:30]}...' as {category} in your Nexus Inbox."

    send_telegram_reply(chat_id, reply_text)
    return {"status": "success"}