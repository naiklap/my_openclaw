from fastapi import FastAPI, Request
import httpx
import os
import json

app = FastAPI()

# --- [CONFIG] ดึงค่าจาก Environment Variables ที่ตั้งไว้ใน Render ---
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL")
OPENCLAW_SESSION_KEY = os.getenv("OPENCLAW_SESSION_KEY")

@app.get("/")
def root():
    return {
        "message": "Golden Bot is ready!",
        "status": "Waiting for Gold Logic and Webhook connection"
    }

# --- [NEW] ส่วนของ API Tool เพื่อให้หน้า /docs มีรายการ Tools ---
@app.get("/api/tools")
async def get_openclaw_tools():
    """
    ฟังก์ชันสำหรับดึงรายการเครื่องมือ (Tools) จากระบบ OpenClaw 
    เพื่อให้หน้า /docs แสดงผล API ได้ครบถ้วนค่ะ
    """
    # ตรวจสอบว่ามี Session Key ไหม ถ้ามีให้แนบไปใน Header ค่ะ
    headers = {"Authorization": f"Bearer {OPENCLAW_SESSION_KEY}"} if OPENCLAW_SESSION_KEY else {}
    
    async with httpx.AsyncClient() as client:
        try:
            # ยิงไปที่ URL ของ OpenClaw ที่คุณพี่ตั้งค่าไว้
            response = await client.get(OPENCLAW_API_URL, headers=headers)
            # คืนค่าผลลัพธ์กลับไปแสดงที่หน้า /docs
            return response.json()
        except Exception as e:
            return {"error": f"ไม่สามารถเชื่อมต่อ OpenClaw ได้: {str(e)}"}

# --- [WEBHOOK] โครงสร้างพื้นฐานสำหรับรับ Webhook จาก Telegram ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    จุดรับข้อความจาก Telegram (Webhook)
    ในอนาคตเราจะเอา Logic ราคาทองและ Flex Message มาใส่ที่นี่ค่ะ
    """
    try:
        data = await request.json()
        # พิมพ์ log ออกมาดูใน Render เพื่อตรวจสอบข้อความที่ส่งมาค่ะ
        print(f"Received Telegram Data: {data}")
        return {"status": "success", "message": "Webhook received"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
