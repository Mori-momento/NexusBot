import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- IMPORTANT: Add your Telegram Bot Token here ---
# In production, you would use an environment variable for this.
TELEGRAM_TOKEN = "7714180083:AAG2NoBRWnj2FL6BxTzykm_fDUaR-RKrA3A" # <--- PASTE YOUR TOKEN HERE

# --- 1. Initialize the AI Model and Chain ---
llm = OllamaLLM(model="gemma3:1b", base_url="http://localhost:11435")
prompt = ChatPromptTemplate.from_template("""
You are an intelligent triaging agent for a productivity app. Your task is to analyze the user's text and classify it into one of three categories: 'Idea', 'Flexible Task', or 'Time-Blocked Task'. Analyze the following user text and respond with ONLY the category name.
User Text: "{user_input}"
Category:
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
    
    classification = chain.invoke({"user_input": user_message})
    clean_classification = classification.strip()
    
    print(f"Received from Chat ID {chat_id}: '{user_message}' -> Classified as: '{clean_classification}'")
    
    # Create the reply message
    reply_text = f"Got it! I've classified that as an '{clean_classification}'."
    
    # Send the reply
    send_telegram_reply(chat_id, reply_text)
    
    return {"status": "success"}