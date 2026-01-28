from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field


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


class POHeader(BaseModel):
    """Purchase Order header information."""
    poNumber: Optional[str] = Field(None, alias="poNumber")
    poDate: Optional[str] = Field(None, alias="poDate")
    deliveryDate: Optional[str] = Field(None, alias="deliveryDate")
    yourRef: Optional[str] = Field(None, alias="yourRef")
    customer: CustomerInfo
    
    class Config:
        populate_by_name = True


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


class POMeta(BaseModel):
    """Metadata about the extraction process."""
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    warnings: Optional[List[str]] = Field(default_factory=list)
    rawText: Optional[str] = Field(None, alias="rawText")
    fields: Optional[Dict[str, float]] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True


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


class StructureRequest(BaseModel):
    """Request for LLM structuring endpoint."""
    text: str = Field(..., min_length=1, description="Raw text to structure")
    include_raw_text: bool = Field(True, description="Include raw text in meta.rawText")


class StructureResponse(BaseModel):
    """Response from LLM structuring."""
    result: OCRPOResult
    processing_time_ms: int


class PDFToStructuredRequest(BaseModel):
    """Metadata for PDF to structured JSON endpoint (file is in multipart)."""
    include_raw_text: bool = Field(True, description="Include raw text in meta.rawText")


class PDFToStructuredResponse(BaseModel):
    """Response from full pipeline (PDF -> text -> structured JSON)."""
    ocr: dict = Field(..., description="OCR extraction metadata")
    result: OCRPOResult = Field(..., description="Structured PO data")
    processing_time_ms: int
