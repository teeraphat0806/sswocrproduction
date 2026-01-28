import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}
ALLOWED_CONTENT_TYPES = {"application/pdf"}


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
