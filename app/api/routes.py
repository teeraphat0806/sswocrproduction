from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.schemas import ExtractionResponse, ErrorResponse
from app.models.po_schemas import (
    TextInput, StructureRequest, StructureResponse,
    PDFToStructuredResponse
)
from app.services.extractor import PDFExtractor
from app.services.openrouter_client import OpenRouterClient
from app.services.structurer import TextStructurer
from app.utils.files import validate_pdf_file, save_temp_file, cleanup_temp_file
from app.utils.auth import verify_token
from pydantic import ValidationError
import logging
import time
import httpx

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


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
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size (20 MB)"
            )
        
        # Validate file
        validate_pdf_file(file.filename, file.content_type)
        
        # Save to temp file
        temp_path = save_temp_file(content, suffix=".pdf")
        logger.info(f"Processing PDF: {file.filename} ({file_size / 1024:.2f} KB)")
        
        # Extract text
        extractor = PDFExtractor()
        result = extractor.extract(temp_path)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Extraction completed: {result['page_count']} pages, "
            f"method={result['method']}, time={processing_time_ms}ms"
        )
        
        return ExtractionResponse(
            text=result["text"],
            pages=result["pages"],
            meta={
                "page_count": result["page_count"],
                "extraction_method": result["method"],
                "processing_time_ms": processing_time_ms
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )
    finally:
        # Cleanup temp file
        if temp_path:
            cleanup_temp_file(temp_path)


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
async def structure_text(request: StructureRequest, token: str = Depends(verify_token)):
    """
    Structure raw text into JSON using OpenRouter.ai LLM.
    
    - **text**: Raw text to structure (typically from OCR)
    - **include_raw_text**: Whether to include raw text in response (default: true)
    
    Returns structured PO data following defined schema.
    """
    start_time = time.time()
    
    try:
        # Initialize services
        openrouter = OpenRouterClient()
        structurer = TextStructurer()
        
        # Build prompt
        messages = structurer.build_prompt(request.text)
        
        # Call OpenRouter
        logger.info("Calling OpenRouter API for text structuring")
        try:
            raw_response = openrouter.call_openrouter(
                messages=messages,
                temperature=0.0  # Deterministic output
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"LLM service error: {e.response.status_code}"
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
        
        # Parse and validate response
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
        # Step 1: Read and validate file
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size (20 MB)"
            )
        
        validate_pdf_file(file.filename, file.content_type)
        temp_path = save_temp_file(content, suffix=".pdf")
        
        logger.info(f"Processing PDF to structured JSON: {file.filename} ({file_size / 1024:.2f} KB)")
        
        # Step 2: Extract text from PDF
        extractor = PDFExtractor()
        ocr_result = extractor.extract(temp_path)
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
        
        # Step 3: Initialize LLM services
        openrouter = OpenRouterClient()
        structurer = TextStructurer()
        
        # Step 4: Build prompt and call LLM
        messages = structurer.build_prompt(extracted_text)
        
        logger.info("Calling OpenRouter API for structuring")
        try:
            raw_response = openrouter.call_openrouter(
                messages=messages,
                temperature=0.0
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"LLM service error: {e.response.status_code}"
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
        
        # Step 5: Parse and validate
        try:
            structured_data = structurer.parse_and_validate(
                raw_response,
                include_raw_text=include_raw_text
            )
            
            # If include_raw_text is True and it wasn't set by LLM, add it
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
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Complete pipeline finished in {processing_time_ms}ms")
        
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
