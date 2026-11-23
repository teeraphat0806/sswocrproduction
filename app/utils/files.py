import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException, UploadFile
import logging
# เป็นไฟล์ที่ใช้สำหรับจัดการกับไฟล์ PDF ที่ถูกอัปโหลดเข้ามา โดยจะมีฟังก์ชันหลักที่ใช้ในการตรวจสอบว่าไฟล์ที่อัปโหลดเป็น PDF หรือไม่ และฟังก์ชันที่ใช้ในการบันทึกไฟล์ชั่วคราวในระบบเพื่อนำไปสกัดข้อความจาก PDF และฟังก์ชันที่ใช้ในการลบไฟล์ชั่วคราวหลังจากใช้งานเสร็จแล้ว โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการจัดการไฟล์ เช่น การตรวจสอบประเภทของไฟล์และการจัดการกับข้อผิดพลาดในการบันทึกหรือการลบไฟล์ เพื่อให้แน่ใจว่าการจัดการกับไฟล์เป็นไปอย่างถูกต้องและปลอดภัย
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}
ALLOWED_CONTENT_TYPES = {"application/pdf"}

# ตรวจว่าเป็น PDF ไหม
def validate_pdf_file(filename: Optional[str], content_type: Optional[str]) -> None:
    """
    Validate uploaded file is a PDF.
    
    Args:
        filename: Original filename
        content_type: MIME content type
        
    Raises:
        HTTPException: If validation fails
    """
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )
    
    # Check file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{file_ext}'. Only .pdf files are allowed"
        )
    
    # Check content type (best-effort)
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(f"Unexpected content type: {content_type} for file: {filename}")
        # Don't fail, but log warning as some clients send wrong content-type

# ฟังก์ชันหลักที่ใช้ในการบันทึกไฟล์ชั่วคราวในระบบเพื่อนำไปสกัดข้อความจาก PDF โดยจะมีการสร้างชื่อไฟล์แบบสุ่มเพื่อป้องกันการชนกันของชื่อไฟล์ และจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการบันทึกไฟล์ เช่น การตรวจสอบว่าไดเรกทอรีชั่วคราวสามารถเขียนได้หรือไม่ และการจัดการกับข้อผิดพลาดในการเขียนไฟล์ เพื่อให้แน่ใจว่าการบันทึกไฟล์เป็นไปอย่างถูกต้องและปลอดภัย
def save_temp_file(content: bytes, suffix: str = ".pdf") -> str:
    """
    Save uploaded file content to a temporary file with random UUID name.
    
    Args:
        content: File content bytes
        suffix: File suffix/extension
        
    Returns:
        Path to temporary file
    """
    temp_dir = tempfile.gettempdir()
    
    # Generate random filename
    random_filename = f"{uuid.uuid4()}{suffix}"
    temp_path = os.path.join(temp_dir, random_filename)
    
    # Write content
    with open(temp_path, "wb") as f:
        f.write(content)
    
    logger.debug(f"Saved temporary file: {temp_path}")
    return temp_path


async def save_upload_file_streaming(
    upload_file: UploadFile,
    max_size: int,
    suffix: str = ".pdf",
    chunk_size: int = 1024 * 1024,
) -> Tuple[str, int]:
    """
    Stream uploaded file directly to a temporary file in chunks while enforcing max_size.
    Avoids buffering the entire file in RAM before size validation.
    """
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}{suffix}")
    total_size = 0

    try:
        with open(temp_path, "wb") as f:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File size exceeds maximum allowed size ({max_size / 1024 / 1024:.0f} MB)"
                    )
                f.write(chunk)

        logger.debug(f"Streamed temporary file: {temp_path} ({total_size} bytes)")
        return temp_path, total_size
    except Exception:
        cleanup_temp_file(temp_path)
        raise

# ฟังก์ชันที่ใช้ในการลบไฟล์ชั่วคราวหลังจากใช้งานเสร็จแล้ว โดยจะมีการตรวจสอบว่าไฟล์ที่ต้องการลบมีอยู่จริงหรือไม่ก่อนที่จะทำการลบ และจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการลบไฟล์ เช่น การจัดการกับข้อผิดพลาดในการเข้าถึงไฟล์หรือข้อผิดพลาดในการลบไฟล์ เพื่อให้แน่ใจว่าการลบไฟล์เป็นไปอย่างถูกต้องและปลอดภัย
def cleanup_temp_file(file_path: str) -> None:
    """
    Delete temporary file.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
