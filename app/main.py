from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import logging
import os

# โหลด environment variables จาก .env ไฟล์
from dotenv import load_dotenv
load_dotenv()

# ตั้งค่าระดับ logging จาก environment variable หรือใช้ค่าเริ่มต้นเป็น INFO
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# สร้าง logger สำหรับโมดูลนี้
logger = logging.getLogger(__name__)
# สร้าง FastAPI app และตั้งค่าชื่อ, คำอธิบาย, และเวอร์ชันของ API
app = FastAPI(
    title="Thai PDF OCR API",
    description="Extract Thai text from PDF files using text extraction and OCR fallback, "
                "then structure into JSON using LLM",
    version="2.0.0",
)

# ตั้งค่า CORS middleware โดยดึง allowed origins จาก environment variable และอนุญาตให้ใช้ credentials, methods, และ headers ที่จำเป็นสำหรับการทำงานของ API
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# รวม router จากโมดูล api.routes เพื่อให้สามารถเข้าถึง endpoints ที่กำหนดไว้ใน router ได้ผ่าน API นี้
app.include_router(router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Thai PDF OCR API",
        "version": "2.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    import os
    return {
        "status": "healthy",
        "version": "2.0.0",
        "checks": {
            "api": "ok",
            "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY"))
        }
    }

# จุดเริ่มต้นของแอปพลิเคชัน โดยจะมีการตั้งค่าระดับ logging จาก environment variable และสร้าง FastAPI app พร้อมกับตั้งค่าชื่อ, คำอธิบาย, และเวอร์ชันของ API นอกจากนี้ยังมีการตั้งค่า CORS middleware เพื่ออนุญาตให้เข้าถึง API จาก origins ที่กำหนดไว้ใน environment variable และรวม router จากโมดูล api.routes เพื่อให้สามารถเข้าถึง endpoints ที่กำหนดไว้ใน router ได้ผ่าน API นี้ โดยมี endpoints สำหรับ health check เพื่อให้สามารถตรวจสอบสถานะของ API ได้อย่างง่ายดาย
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
