# C:\Users\naikl\.openclaw\workspace\telegram\main.py
from fastapi import FastAPI, Request, HTTPException
import os
import requests
from dotenv import load_dotenv

from telegram import Update, Bot
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
)
from telegram.utils.request import Request as TelegramRequest

# -------------------------------------------------
# โหลด environment variables
# -------------------------------------------------
load_dotenv(dotenv_path="./.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL")
SESSION_KEY = os.getenv("OPENCLAW_SESSION_KEY")
OPENCLAW_TIMEOUT_MS = int(os.getenv("OPENCLAW_TIMEOUT_MS", "5000"))

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set in .env")
if not OPENCLAW_API_URL:
    raise RuntimeError("OPENCLAW_API_URL is not set in .env")

# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI()

# -------------------------------------------------
# สร้าง Bot + Application (สำหรับ webhook)
# -------------------------------------------------
telegram_request = TelegramRequest(con_pool_connections=10)
bot_instance = Bot(token=TELEGRAM_TOKEN, request=telegram_request)

# Application ใช้สำหรับจัดการ handlers (แม้จะใช้ webhook)
application = Application.builder().bot(bot_instance).build()

# -------------------------------------------------
# ฟังก์ชันเรียก OpenClaw API
# -------------------------------------------------
async def call_openclaw_agent(user_message: str) -> str:
    payload = {
        "session_key": SESSION_KEY if SESSION_KEY else None,
        "command": user_message,
    }
    try:
        timeout_seconds = OPENCLAW_TIMEOUT_MS / 1000
        resp = requests.post(
            OPENCLAW_API_URL, json=payload, timeout=timeout_seconds
        )
        if resp.ok:
            data = resp.json()
            return data.get("response", "น้องกุ้งไม่สามารถตอบได้ในตอนนี้")
        else:
            return f"OpenClaw API error: {resp.status_code} - {resp.text}"
    except requests.exceptions.RequestException as e:
        return f"Error calling OpenClaw API: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# -------------------------------------------------
# Handler ที่จะทำงานเมื่อมีข้อความจาก Telegram
# -------------------------------------------------
async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text if update.message else ""
    chat_id = update.effective_chat.id

    if not user_message:
        return

    print(f"[Telegram] Received from {chat_id}: {user_message}")

    # เรียก OpenClaw
    agent_response = await call_openclaw_agent(user_message)

    # ส่งกลับไป Telegram
    await context.bot.send_message(chat_id=chat_id, text=agent_response)
    print(f"[Telegram] Sent to {chat_id}: {agent_response}")


# -------------------------------------------------
# ลงทะเบียน handler สำหรับข้อความธรรมดา
# -------------------------------------------------
message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
application.add_handler(message_handler)


# -------------------------------------------------
# Webhook endpoint (FastAPI)
# -------------------------------------------------
@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != TELEGRAM_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
        update = Update.de_json(body, bot_instance)

        # สร้าง Context ที่มาจาก Application (ใช้ bot ของเรา)
        ctx = CallbackContext(application.bot)

        # เรียก handler ของเราโดยตรง
        await handle_message(update, ctx)

        print(f"[Webhook] Processed: {body.get('message', {}).get('text', '')}")
        return {"status": "ok"}
    except Exception as e:
        print(f"[Webhook] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing update: {e}")


# -------------------------------------------------
# Health check
# -------------------------------------------------
@app.get("/")
async def root():
    return {"status": "Bot is running and listening for Telegram webhooks."}
