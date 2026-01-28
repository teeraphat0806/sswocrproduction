import pytest
from fastapi.testclient import TestClient
from app.main import app
from io import BytesIO
from pypdf import PdfWriter

client = TestClient(app)


def create_dummy_pdf() -> BytesIO:
    """Create a simple dummy PDF for testing."""
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=200, height=200)
    
    pdf_bytes = BytesIO()
    pdf_writer.write(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_extract_pdf_no_file():
    """Test extraction without file."""
    response = client.post("/extract/pdf")
    assert response.status_code == 422  # Validation error


def test_extract_pdf_invalid_extension():
    """Test extraction with invalid file extension."""
    files = {"file": ("test.txt", b"fake content", "text/plain")}
    response = client.post("/extract/pdf", files=files)
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]


def test_extract_pdf_file_too_large():
    """Test extraction with file exceeding size limit."""
    # Create a large fake PDF (21 MB)
    large_content = b"x" * (21 * 1024 * 1024)
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    response = client.post("/extract/pdf", files=files)
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["detail"]


def test_extract_pdf_valid_dummy():
    """Test extraction with valid dummy PDF."""
    pdf_content = create_dummy_pdf()
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}
    
    response = client.post("/extract/pdf", files=files)
    
    # Should succeed (even if empty text)
    assert response.status_code == 200
    
    data = response.json()
    assert "text" in data
    assert "pages" in data
    assert "meta" in data
    assert data["meta"]["page_count"] >= 0
    assert data["meta"]["extraction_method"] in ["pdf_text", "ocr"]
    assert data["meta"]["processing_time_ms"] > 0


def test_extract_pdf_response_structure():
    """Test that response has correct structure."""
    pdf_content = create_dummy_pdf()
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}
    
    response = client.post("/extract/pdf", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert isinstance(data["text"], str)
    assert isinstance(data["pages"], list)
    assert isinstance(data["meta"], dict)
    
    # Check meta structure
    assert "page_count" in data["meta"]
    assert "extraction_method" in data["meta"]
    assert "processing_time_ms" in data["meta"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
