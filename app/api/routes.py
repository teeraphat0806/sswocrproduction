from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.schemas import ExtractionResponse, ErrorResponse
from app.models.po_schemas import (
    TextInput, StructureRequest, StructureResponse,
    PDFToStructuredResponse
)
from app.services.extractor import PDFExtractor
from app.services.openrouter_client import OpenRouterClient
from app.services.structurer import TextStructurer
from app.utils.files import (
    validate_pdf_file,
    save_upload_file_streaming,
    cleanup_temp_file,
)
from app.utils.auth import verify_token
from pydantic import ValidationError
import asyncio
import logging
import time
import httpx

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

# Shared singleton extractor and concurrency limiter to avoid reloading EasyOCR or spiking peak RAM
pdf_extractor = PDFExtractor()
ocr_semaphore = asyncio.Semaphore(1)
# ไฟล์นี้คือ “API Layer (FastAPI Router)” ของระบบทั้งหมดคือ “ประตูเข้า” ของระบบ OCR + LLM ทั้งก้อน
# ดึง text จาก PDF
@router.post(
    "/extract/pdf",
    response_model=ExtractionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid API token"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Extraction failed"},
    },
    summary="Extract Thai text from PDF",
    description="Upload a PDF file and extract all readable Thai text. "
                "Uses text extraction first, falls back to OCR for scanned PDFs. "
                "Requires X-API-Token header for authentication."
)
# ใช้ “แค่ OCR / text extraction”
async def extract_pdf(
    file: UploadFile = File(..., description="PDF file to extract text from"),
    token: str = Depends(verify_token)
):
    """
    Extract Thai text from uploaded PDF file.
    
    - **file**: PDF file (max 20MB)
    
    Returns extracted text, per-page text, and metadata.
    """
    start_time = time.time()
    temp_path = None
    
    try:
        # ขั้นที่ 1 ตรวจสอบว่าเป็น PDF และสตรีมไฟล์ลงดิสก์ทีละ chunk พร้อมจำกัดขนาดไฟล์เพื่อไม่ให้กิน RAM
        validate_pdf_file(file.filename, file.content_type)
        temp_path, file_size = await save_upload_file_streaming(
            file, MAX_FILE_SIZE, suffix=".pdf"
        )
        logger.info(f"Processing PDF: {file.filename} ({file_size / 1024:.2f} KB)")
        
        # ขั้นที่ 2 สกัดข้อความจาก PDF โดยใช้ shared PDFExtractor และจำกัด concurrency ผ่าน semaphore
        async with ocr_semaphore:
            result = await asyncio.to_thread(pdf_extractor.extract, temp_path)
        
        # ขั้นที่ 4 คำนวณเวลาที่ใช้ในการประมวลผลและสร้าง response โดยจะคำนวณเวลาที่ใช้ในการประมวลผลโดยการนำเวลาปัจจุบันมาลบกับเวลาที่เริ่มต้น และแปลงเป็นหน่วยมิลลิวินาที จากนั้นจะสร้าง response โดยใช้โมเดล ExtractionResponse ซึ่งจะประกอบด้วยข้อความที่สกัดได้ ข้อความจากแต่ละหน้า และข้อมูลเมตาเกี่ยวกับกระบวนการสกัด เช่น จำนวนหน้า วิธีการสกัดที่ใช้ และเวลาที่ใช้ในการประมวลผล เพื่อให้สามารถส่งข้อมูลเหล่านี้กลับไปยังผู้เรียกใช้งาน API ได้อย่างครบถ้วนและมีประสิทธิภาพ
        processing_time_ms = int((time.time() - start_time) * 1000)
        # บันทึกข้อมูลการประมวลผลลงใน log เพื่อให้สามารถติดตามและวิเคราะห์การทำงานของ API
        logger.info(
            f"Extraction completed: {result['page_count']} pages, "
            f"method={result['method']}, time={processing_time_ms}ms"
        )
        # คืนผลลัพธ์การสกัดข้อความพร้อมกับข้อมูลเมตาเกี่ยวกับกระบวนการสกัดในรูปแบบของโมเดล ExtractionResponse
        return ExtractionResponse(
            text=result["text"],
            pages=result["pages"],
            meta={
                "page_count": result["page_count"],
                "extraction_method": result["method"],
                "processing_time_ms": processing_time_ms
            }
        )
        # จัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการประมวลผล เช่น การตรวจสอบขนาดของไฟล์ การตรวจสอบประเภทของไฟล์
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )
    finally:
        # ขั้นที่ 5 ลบไฟล์ชั่วคราวหลังจากใช้งานเสร็จแล้ว 
        if temp_path:
            cleanup_temp_file(temp_path)

# ใช้ “เฉพาะ LLM” (รับ text input มาแล้วส่งไป structuring Json)
@router.post(
    "/llm/structure",
    response_model=StructureResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid API token"},
        502: {"model": ErrorResponse, "description": "LLM returned invalid response"},
        422: {"model": ErrorResponse, "description": "Response validation failed"},
        500: {"model": ErrorResponse, "description": "Processing failed"},
    },
    summary="Structure text using LLM",
    description="Send raw text to OpenRouter LLM to extract structured JSON data. "
                "Returns validated JSON following the PO schema. "
                "Requires X-API-Token header for authentication."
)
# ใช้ “เฉพาะ LLM” (รับ text input มาแล้วส่งไป structuring Json) โดยจะมีการรับข้อความดิบที่ต้องการนำไปสกัดข้อมูลในรูปแบบ JSON ผ่านทาง request body และจะมีการตรวจสอบ API token เพื่อความปลอดภัย จากนั้นจะมีการเรียกใช้บริการ OpenRouter.ai LLM เพื่อทำการสกัดข้อมูลจากข้อความดิบและแปลงเป็น JSON ตาม schema ที่กำหนดไว้ โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการเรียกใช้ LLM เช่น การจัดการกับข้อผิดพลาดในการเชื่อมต่อหรือข้อผิดพลาดที่เกิดจาก LLM เอง และจะมีการตรวจสอบความถูกต้องของ JSON ที่ได้รับจาก LLM ว่าตรงตาม schema ที่กำหนดไว้หรือไม่ เพื่อให้แน่ใจว่าข้อมูลที่ส่งกลับไปยังผู้เรียกใช้งาน API มีความถูกต้องและสามารถนำไปใช้งานต่อได้อย่างมีประสิทธิภาพ
async def structure_text(request: StructureRequest, token: str = Depends(verify_token)):
    """
    Structure raw text into JSON using OpenRouter.ai LLM.
    
    - **text**: Raw text to structure (typically from OCR)
    - **include_raw_text**: Whether to include raw text in response (default: true)
    
    Returns structured PO data following defined schema.
    """
    # บันทึกเวลาที่เริ่มต้นการประมวลผลเพื่อใช้ในการคำนวณเวลาที่ใช้ในการประมวลผลทั้งหมดของฟังก์ชันนี้
    start_time = time.time()
    # จัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการประมวลผล เช่น การตรวจสอบความถูกต้องของ JSON ที่ได้รับจาก LLM ว่าตรงตาม schema ที่กำหนดไว้หรือไม่ และการจัดการกับข้อผิดพลาดในการเรียกใช้ LLM เพื่อให้แน่ใจว่าข้อมูลที่ส่งกลับไปยังผู้เรียกใช้งาน API มีความถูกต้องและสามารถนำไปใช้งานต่อได้อย่างมีประสิทธิภาพ
    try:
        # สร้าง instance ของ OpenRouterClient และ TextStructurer เพื่อใช้ในการเรียกใช้บริการ OpenRouter.ai LLM
        openrouter = OpenRouterClient()
        structurer = TextStructurer()
        
        # สร้าง prompt สำหรับ LLM โดยใช้ฟังก์ชัน build_prompt ของ TextStructurer
        messages = structurer.build_prompt(request.text)
        
        # เรียกใช้บริการ OpenRouter.ai LLM เพื่อทำการสกัดข้อมูลจากข้อความดิบและแปลงเป็น JSON ตาม schema
        logger.info("Calling OpenRouter API for text structuring")
        try:
            raw_response = openrouter.call_openrouter(
                messages=messages,
                temperature=0.0  # พารามิเตอร์ที่ควบคุม “ความสุ่ม/ความสร้างสรรค์” ของคำตอบจากโมเดลภาษา (LLM)ต่ำ = ตอบนิ่งสูง = ตอบหลากหลาย สุ่มมากขึ้น เดาได้ ใช้ temperature 0.0 เพื่อให้ได้ผลลัพธ์ที่คาดเดาได้และสอดคล้องกับ schema
            )
        except httpx.HTTPStatusError as e:
            error_detail = str(e)
            if hasattr(e, 'message'):
                error_detail = e.message
            logger.error(f"OpenRouter API error: {error_detail}")
            raise HTTPException(
                status_code=502,
                detail=f"LLM service error: {error_detail}"
            )
        except httpx.TimeoutException:
            logger.error("OpenRouter API timeout")
            raise HTTPException(
                status_code=504,
                detail="LLM service timeout"
            )
        except Exception as e:
            logger.error(f"OpenRouter call failed: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to call LLM service: {str(e)}"
            )
        
        # ตรวจสอบความถูกต้องของ JSON ที่ได้รับจาก LLM ว่าตรงตาม schema ที่กำหนดไว้หรือไม่ โดยใช้ฟังก์ชัน parse_and_validate
        try:
            structured_data = structurer.parse_and_validate(
                raw_response,
                include_raw_text=request.include_raw_text
            )
        except ValueError as e:
            # JSON parsing failed
            logger.error(f"Invalid JSON from LLM: {e}")
            raise HTTPException(
                status_code=502,
                detail=str(e)
            )
        except ValidationError as e:
            # Schema validation failed
            logger.error(f"Schema validation failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"LLM response doesn't match schema: {e.errors()}"
            )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Text structuring completed in {processing_time_ms}ms")
        
        return StructureResponse(
            result=structured_data,
            processing_time_ms=processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Structuring failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Text structuring failed: {str(e)}"
        )

# ใช้ “ครบจบในที่เดียว” (รับ PDF มาแล้วส่งกลับ structured Json)
@router.post(
    "/pdf/to-structured-json",
    response_model=PDFToStructuredResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid API token"},
        413: {"model": ErrorResponse, "description": "File too large"},
        502: {"model": ErrorResponse, "description": "LLM returned invalid response"},
        422: {"model": ErrorResponse, "description": "Response validation failed"},
        500: {"model": ErrorResponse, "description": "Processing failed"},
    },
    summary="Extract and structure PDF in one request",
    description="Upload PDF, extract Thai text, and structure into JSON using LLM in single request. "
                "This is the complete pipeline: PDF -> OCR -> LLM -> Structured JSON. "
                "Requires X-API-Token header for authentication."
)
# ใช้ “ครบจบในที่เดียว” (รับ PDF มาแล้วส่งกลับ structured Json) 
async def pdf_to_structured_json(
    file: UploadFile = File(..., description="PDF file to process"),
    include_raw_text: bool = True,
    token: str = Depends(verify_token)
):
    """
    Complete pipeline: PDF -> Text Extraction -> LLM Structuring -> JSON.
    
    - **file**: PDF file (max 20MB)
    - **include_raw_text**: Include raw OCR text in meta.rawText (query param)
    
    Returns both OCR metadata and structured PO data.
    """
    start_time = time.time()
    temp_path = None
    
    try:
        # Step 1: ตรวจสอบว่าเป็น PDF และสตรีมไฟล์ลงดิสก์ทีละ chunk พร้อมจำกัดขนาดไฟล์
        validate_pdf_file(file.filename, file.content_type)
        temp_path, file_size = await save_upload_file_streaming(
            file, MAX_FILE_SIZE, suffix=".pdf"
        )
        
        logger.info(f"Processing PDF to structured JSON: {file.filename} ({file_size / 1024:.2f} KB)")
        
        # Step 2: สกัดข้อความจาก PDF โดยใช้ shared PDFExtractor และจำกัด concurrency ผ่าน semaphore
        async with ocr_semaphore:
            ocr_result = await asyncio.to_thread(pdf_extractor.extract, temp_path)
        extracted_text = ocr_result["text"]
        
        logger.info(
            f"OCR completed: {ocr_result['page_count']} pages, "
            f"method={ocr_result['method']}, text_length={len(extracted_text)}"
        )
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Extracted text is too short or empty. Please provide a valid document."
            )
        
        # Step 3: เรียกใช้บริการ OpenRouter.ai LLM เพื่อทำการสกัดข้อมูลจากข้อความดิบและแปลงเป็น JSON ตาม schema
        openrouter = OpenRouterClient()
        structurer = TextStructurer()
        
        # Step 4: สร้าง prompt สำหรับ LLM โดยใช้ฟังก์ชัน build_prompt ของ TextStructurer
        messages = structurer.build_prompt(extracted_text)
        
        logger.info("Calling OpenRouter API for structuring")
        # จัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการเรียกใช้ LLM เช่น การจัดการกับข้อผิดพลาดในการเชื่อมต่อหรือข้อผิดพลาดที่เกิดจาก LLM เอง
        try:
            raw_response = openrouter.call_openrouter(
                messages=messages,
                temperature=0.0
            )
        except httpx.HTTPStatusError as e:
            error_detail = str(e)
            if hasattr(e, 'message'):
                error_detail = e.message
            logger.error(f"OpenRouter API error: {error_detail}")
            raise HTTPException(
                status_code=502,
                detail=f"LLM service error: {error_detail}"
            )
        except httpx.TimeoutException:
            logger.error("OpenRouter API timeout")
            raise HTTPException(
                status_code=504,
                detail="LLM service timeout"
            )
        except Exception as e:
            logger.error(f"OpenRouter call failed: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to call LLM service: {str(e)}"
            )
        
        # Step 5: ตรวจสอบความถูกต้องของ JSON ที่ได้รับจาก LLM ว่าตรงตาม schema ที่กำหนดไว้หรือไม่ โดยใช้ฟังก์ชัน parse_and_validate และจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการตรวจสอบความถูกต้องของ JSON ที่ได้รับจาก LLM ว่าตรงตาม schema ที่กำหนดไว้หรือไม่ และการจัดการกับข้อผิดพลาดในการเรียกใช้ LLM เพื่อให้แน่ใจว่าข้อมูลที่ส่งกลับไปยังผู้เรียกใช้งาน API มีความถูกต้องและสามารถนำไปใช้งานต่อได้อย่างมีประสิทธิภาพ
        try:
            structured_data = structurer.parse_and_validate(
                raw_response,
                include_raw_text=include_raw_text
            )
            
            # ถ้า include_raw_text เป็น True แต่ไม่มี rawText ใน meta ของ structured_data ให้เพิ่ม rawText เข้าไปใน meta ด้วยข้อความที่สกัดได้จาก OCR เพื่อให้แน่ใจว่าข้อมูลที่ส่งกลับไปยังผู้เรียกใช้งาน API มีความครบถ้วนและสามารถนำไปใช้งานต่อได้อย่างมีประสิทธิภาพ
            if include_raw_text and not structured_data.get("meta", {}).get("rawText"):
                if "meta" not in structured_data:
                    structured_data["meta"] = {}
                structured_data["meta"]["rawText"] = extracted_text
                
        except ValueError as e:
            logger.error(f"Invalid JSON from LLM: {e}")
            raise HTTPException(
                status_code=502,
                detail=str(e)
            )
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"LLM response doesn't match schema: {e.errors()}"
            )
        # คำนวณเวลาที่ใช้ในการประมวลผลทั้งหมดของฟังก์ชันนี้โดยการนำเวลาปัจจุบันมาลบกับเวลาที่เริ่มต้น และแปลงเป็นหน่วยมิลลิวินาที จากนั้นจะสร้าง response โดยใช้โมเดล PDFToStructuredResponse ซึ่งจะประกอบด้วยข้อมูลเมตาเกี่ยวกับกระบวนการสกัดข้อความจาก PDF เช่น จำนวนหน้า วิธีการสกัดที่ใช้ และความยาวของข้อความที่สกัดได้ พร้อมกับข้อมูลที่ถูกสกัดและจัดโครงสร้างในรูปแบบ JSON ตาม schema 
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Complete pipeline finished in {processing_time_ms}ms")
        # คืนผลลัพธ์การสกัดข้อความพร้อมกับข้อมูลเมตาเกี่ยวกับกระบวนการสกัดในรูปแบบของโมเดล PDFToStructuredResponse
        return PDFToStructuredResponse(
            ocr={
                "page_count": ocr_result["page_count"],
                "extraction_method": ocr_result["method"],
                "text_length": len(extracted_text)
            },
            result=structured_data,
            processing_time_ms=processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF to structured JSON failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        if temp_path:
            cleanup_temp_file(temp_path)
