from typing import List, Optional
from pydantic import BaseModel, Field
# ใช้กำหนดรูปแบบ response ตอน “ดึงข้อความจาก PDF” (ก่อนเข้า LLM)
# ExtractionMeta → ข้อมูลเบื้องหลังการดึง
class ExtractionMeta(BaseModel):
    """Metadata about the extraction process."""
    page_count: int = Field(..., description="Total number of pages in the PDF")
    extraction_method: str = Field(..., description="Method used: 'pdf_text' or 'ocr'")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")

# ExtractionResponse → ผลลัพธ์ OCR 
class ExtractionResponse(BaseModel):
    """Response model for PDF text extraction."""
    text: str = Field(..., description="Combined text from all pages")
    pages: Optional[List[str]] = Field(None, description="Text from each page separately")
    meta: ExtractionMeta = Field(..., description="Extraction metadata")

# ErrorResponse → error response model
class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")
