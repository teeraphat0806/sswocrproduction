from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field

# pydantic models สำหรับข้อมูลที่ได้จากการสกัดและโครงสร้างของ PO โดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class CustomerInfo(BaseModel):
    """Customer information from PO header."""
    name: Optional[str] = None
    taxNumber: Optional[str] = Field(None, alias="taxNumber")
    tel: Optional[str] = None
    email: Optional[str] = None
    faxNumber: Optional[str] = Field(None, alias="faxNumber")
    address: Optional[str] = None
    code: Optional[str] = None
    
    class Config:
        populate_by_name = True

# ฟังก์ชันหลักที่ใช้ในการสร้าง schema สำหรับข้อมูลที่ได้จากการสกัดและโครงสร้างของ PO โดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class POHeader(BaseModel):
    """Purchase Order header information."""
    poNumber: Optional[str] = Field(None, alias="poNumber")
    poDate: Optional[str] = Field(None, alias="poDate")
    deliveryDate: Optional[str] = Field(None, alias="deliveryDate")
    yourRef: Optional[str] = Field(None, alias="yourRef")
    customer: CustomerInfo
    
    class Config:
        populate_by_name = True

# ฟังก์ชันหลักที่ใช้ในการสร้าง schema สำหรับข้อมูลที่ได้จากการสกัดและโครงสร้างของ PO โดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class POItem(BaseModel):
    """Individual line item in purchase order."""
    codeSteel: Optional[str] = Field(None, alias="codeSteel")
    description: Optional[str] = None
    shape: Optional[Literal["square", "line"]] = None
    width: Optional[float] = None
    length: Optional[float] = None
    thickness: Optional[float] = None
    quantity: Optional[int] = None
    cuttingMethod: Optional[Literal["normal", "laser", "plasma", "gas"]] = Field(None, alias="cuttingMethod")
    job: Optional[int] = None
    notes: Optional[str] = None
    matchedSteelTypeId: Optional[str] = Field(None, alias="matchedSteelTypeId")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    class Config:
        populate_by_name = True

# PoMeta จะเก็บข้อมูลเกี่ยวกับกระบวนการสกัดและโครงสร้างของ PO โดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class POMeta(BaseModel):
    """Metadata about the extraction process."""
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    warnings: Optional[List[str]] = Field(default_factory=list)
    rawText: Optional[str] = Field(None, alias="rawText")
    fields: Optional[Dict[str, float]] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True

# OcrPOResult จะเก็บผลลัพธ์ของการสกัดและโครงสร้างของ PO โดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class OCRPOResult(BaseModel):
    """Complete Purchase Order extraction result."""
    header: POHeader
    items: List[POItem] = Field(default_factory=list)
    meta: POMeta
    
    class Config:
        populate_by_name = True


# Request/Response models for API endpoints

class TextInput(BaseModel):
    """Input for text-based endpoints."""
    text: str = Field(..., min_length=1, description="Text to process")

# PDFInput จะเก็บข้อมูลเกี่ยวกับคำขอในการสกัดข้อความจาก PDF โดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการสกัดข้อความจาก PDF และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class StructureRequest(BaseModel):
    """Request for LLM structuring endpoint."""
    text: str = Field(..., min_length=1, description="Raw text to structure")
    include_raw_text: bool = Field(True, description="Include raw text in meta.rawText")

# StructureResponse จะเก็บผลลัพธ์ของการแปลงข้อมูลจาก LLM เป็น JSON และตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class StructureResponse(BaseModel):
    """Response from LLM structuring."""
    result: OCRPOResult
    processing_time_ms: int

# PDFToStructuredRequest จะเก็บข้อมูลเกี่ยวกับคำขอในการแปลง PDF เป็นข้อมูลที่มีโครงสร้างโดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class PDFToStructuredRequest(BaseModel):
    """Metadata for PDF to structured JSON endpoint (file is in multipart)."""
    include_raw_text: bool = Field(True, description="Include raw text in meta.rawText")

# pdf_to_structured_response จะเก็บผลลัพธ์ของการแปลง PDF เป็นข้อมูลที่มีโครงสร้างโดยจะมีการกำหนด schema ที่ชัดเจนเพื่อให้แน่ใจว่าข้อมูลที่ได้รับมีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
class PDFToStructuredResponse(BaseModel):
    """Response from full pipeline (PDF -> text -> structured JSON)."""
    ocr: dict = Field(..., description="OCR extraction metadata")
    result: OCRPOResult = Field(..., description="Structured PO data")
    processing_time_ms: int
