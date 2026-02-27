from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Bot is running!"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print(f"Received message: {data}")
    # ตรงนี้ไว้เขียน Logic ประมวลผลข้อความนะคะ
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
