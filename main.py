from fastapi import FastAPI, Request, HTTPException
import os
import requests
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, CallbackContext

# --- 1. CONFIGURATION ---
# บน Render เราจะดึงค่าจาก Environment Variables โดยตรงค่ะ
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL")
SESSION_KEY = os.getenv("OPENCLAW_SESSION_KEY")
# ตั้ง Timeout ไว้ที่ 10 วินาทีเพื่อให้เอเจ้นท์มีเวลาคุยกันค่ะ
OPENCLAW_TIMEOUT_MS = int(os.getenv("OPENCLAW_TIMEOUT_MS", "10000"))

if not TELEGRAM_TOKEN or not OPENCLAW_API_URL:
    print("❌ Error: Missing TELEGRAM_TOKEN or OPENCLAW_API_URL")

# --- 2. INITIALIZE BOT & APP ---
app = FastAPI()
bot_instance = Bot(token=TELEGRAM_TOKEN)
# สร้าง Application เพื่อจัดการ logic ของ telegram
application = Application.builder().bot(bot_instance).build()

# --- 3. MULTI-AGENT LOGIC (ส่วนที่จะให้บอทถกกัน) ---
async def call_openclaw_agent(user_message: str) -> str:
    """
    ฟังก์ชันเรียก OpenClaw 
    ในอนาคตเราจะขยายตรงนี้ให้เป็น 4 เอเจ้นท์มาถกกันค่ะ
    """
    payload = {
        "session_key": SESSION_KEY if SESSION_KEY else None,
        "command": user_message,
    }
    try:
        timeout_seconds = OPENCLAW_TIMEOUT_MS / 1000
        # ใช้ requests เรียก API (ต้องมี requests ใน requirements.txt นะค๊ะ)
        resp = requests.post(
            OPENCLAW_API_URL, 
            json=payload, 
            timeout=timeout_seconds
        )
        if resp.ok:
            data = resp.json()
            return data.get("response", "น้อง Golden ยังหาคำตอบให้ไม่ได้ในตอนนี้ค่ะ")
        else:
            return f"ขออภัยค่ะ ระบบขัดข้อง (Error {resp.status_code})"
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {str(e)}"

# --- 4. MESSAGE HANDLER ---
async def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text
    chat_id = update.effective_chat.id

    print(f"📩 ได้รับข้อความ: {user_message}")

    # เรียกตัวแทนเอเจ้นท์ไปประมวลผล (ถกกันในขั้นตอนนี้)
    agent_response = await call_openclaw_agent(user_message)

    # ส่งคำตอบกลับไปที่ Telegram
    await context.bot.send_message(chat_id=chat_id, text=agent_response)

# --- 5. WEBHOOK ENDPOINT ---
@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != TELEGRAM_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
        update = Update.de_json(body, bot_instance)
        
        # รัน handler ประมวลผลข้อความ
        await handle_message(update, CallbackContext(application.bot))
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/")
async def root():
    return {"status": "Golden Bot is Live!", "endpoint": "/webhook/YOUR_TOKEN"}
