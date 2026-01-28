from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractionMeta(BaseModel):
    """Metadata about the extraction process."""
    page_count: int = Field(..., description="Total number of pages in the PDF")
    extraction_method: str = Field(..., description="Method used: 'pdf_text' or 'ocr'")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class ExtractionResponse(BaseModel):
    """Response model for PDF text extraction."""
    text: str = Field(..., description="Combined text from all pages")
    pages: Optional[List[str]] = Field(None, description="Text from each page separately")
    meta: ExtractionMeta = Field(..., description="Extraction metadata")


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")
