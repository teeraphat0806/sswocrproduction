# Thai PDF OCR API

A robust REST API for extracting Thai text from PDF files and structuring it into JSON using AI, with intelligent fallback from text extraction to OCR.

## Features

- **Smart Extraction Pipeline**: Attempts text extraction first, automatically falls back to OCR for scanned PDFs
- **Thai Language Support**: Optimized for Thai text using Tesseract OCR with Thai language pack
- **LLM-Powered Structuring**: Uses OpenRouter.ai to convert extracted text into structured JSON
- **Flexible Endpoints**: Separate endpoints for text extraction only, LLM structuring only, or complete pipeline
- **FastAPI Framework**: Modern, fast, with automatic API documentation
- **Docker Support**: Easy deployment with Docker and docker-compose
- **Validation**: File type, size, and content validation
- **Per-Page Results**: Returns both combined text and per-page breakdown
- **Metadata**: Includes page count, extraction method, and processing time

## API Endpoints

### 1. `POST /extract/pdf` - Extract Text Only

Extract Thai text from PDF without LLM processing.

**Request:**

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@document.pdf"
```

**Response:**

```json
{
  "text": "สวัสดีครับ\nข้อความจากเอกสาร...",
  "pages": ["หน้า 1...", "หน้า 2..."],
  "meta": {
    "page_count": 2,
    "extraction_method": "pdf_text",
    "processing_time_ms": 123
  }
}
```

### 2. `POST /llm/structure` - Structure Text with LLM

Convert raw text to structured JSON using OpenRouter.ai.

**Request:**

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ใบสั่งซื้อ\nเลขที่: PO-001\nบริษัท ABC จำกัด...",
    "include_raw_text": true
  }'
```

**Response:**

```json
{
  "result": {
    "header": {
      "poNumber": "PO-001",
      "poDate": "2026-01-27",
      "customer": {
        "name": "บริษัท ABC จำกัด",
        "tel": "02-xxx-xxxx"
      }
    },
    "items": [
      {
        "codeSteel": "SS400",
        "thickness": 12,
        "width": 100,
        "length": 2000,
        "quantity": 50,
        "shape": "square",
        "confidence": 0.95
      }
    ],
    "meta": {
      "confidence": 0.92,
      "warnings": [],
      "rawText": "..."
    }
  },
  "processing_time_ms": 1523
}
```

### 3. `POST /pdf/to-structured-json` - Complete Pipeline ⭐

**One-shot endpoint**: PDF → Extract Text → LLM Structure → JSON

**Request:**

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json?include_raw_text=true" \
  -F "file=@purchase_order.pdf"
```

**Response:**

```json
{
  "ocr": {
    "page_count": 2,
    "extraction_method": "pdf_text",
    "text_length": 1234
  },
  "result": {
    "header": {
      /* structured header */
    },
    "items": [
      /* structured items */
    ],
    "meta": {
      /* metadata */
    }
  },
  "processing_time_ms": 2145
}
```

## Requirements

### Local Development

- Python 3.11+ (3.12 recommended for best package support)
- Tesseract OCR with Thai language data
- OpenRouter.ai API key
- System dependencies:
  - `tesseract-ocr`
  - `tesseract-ocr-tha` (Thai language pack)

### Docker

- Docker
- Docker Compose

## Installation

### Option 1: Local Setup

#### 1. Install System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-tha
```

**macOS:**

```bash
brew install tesseract tesseract-lang
```

**Windows:**

- Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download Thai language data from: https://github.com/tesseract-ocr/tessdata
- Place `tha.traineddata` in Tesseract's `tessdata` directory

#### 2. Get OpenRouter API Key

1. Sign up at https://openrouter.ai
2. Go to https://openrouter.ai/keys
3. Create a new API key
4. Copy the key (starts with `sk-or-v1-...`)

#### 3. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

#### 4. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 6. Run the Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

### Option 2: Docker Setup

#### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

#### 2. Build and Run

```bash
docker-compose up --build
```

The API will be available at: http://localhost:8000

#### 3. Run in Detached Mode

```bash
docker-compose up -d
```

#### 4. View Logs

```bash
docker-compose logs -f
```

#### 5. Stop Services

```bash
docker-compose down
```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage

### Extract Text from PDF

**Endpoint:** `POST /extract/pdf`

**cURL Example:**

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@sample.pdf" \
  -H "accept: application/json"
```

**Python Example:**

```python
import requests

url = "http://localhost:8000/extract/pdf"
files = {"file": open("sample.pdf", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

**Response Example:**

```json
{
  "text": "สวัสดีครับ\nนี่คือเอกสารตัวอย่าง\n\nหน้า 2 เนื้อหา...",
  "pages": ["สวัสดีครับ\nนี่คือเอกสารตัวอย่าง", "หน้า 2 เนื้อหา..."],
  "meta": {
    "page_count": 2,
    "extraction_method": "pdf_text",
    "processing_time_ms": 123
  }
}
```

### Health Check

**Endpoint:** `GET /health`

```bash
curl http://localhost:8000/health
```

## Extraction Methods

The API uses a two-step extraction pipeline:

### 1. Text Extraction (pdf_text)

- Uses `pypdf` to extract embedded text from searchable PDFs
- Fast and accurate for native digital PDFs
- Validates Thai character ratio to ensure quality

### 2. OCR Fallback (ocr)

- Triggered when text extraction yields insufficient Thai content
- Converts PDF pages to images at 2x zoom (144 DPI)
- Uses Tesseract OCR with Thai language pack (`tha`)
- Configured for optimal Thai text recognition

## Configuration

### File Limits

Default maximum file size: **20 MB**

To change, modify `MAX_FILE_SIZE` in [app/api/routes.py](app/api/routes.py):

```python
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
```

### OCR Settings

Thai character detection threshold in [app/services/extractor.py](app/services/extractor.py):

```python
self.min_text_length = 10  # Minimum text length
self.thai_ratio_threshold = 0.1  # Minimum Thai character ratio
```

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

## Testing

### Run Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_extract_pdf.py::test_extract_pdf_valid_dummy -v
```

## Project Structure

```
OCRV2/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── extractor.py        # PDF extraction logic
│   ├── utils/
│   │   ├── __init__.py
│   │   └── files.py            # File validation and temp handling
│   └── models/
│       ├── __init__.py
│       └── schemas.py          # Pydantic models
├── tests/
│   ├── __init__.py
│   └── test_extract_pdf.py     # API tests
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Docker compose configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore
└── README.md
```

## Error Codes

| Status Code | Description                                    |
| ----------- | ---------------------------------------------- |
| 200         | Success                                        |
| 400         | Invalid file (wrong extension or content type) |
| 413         | File too large (exceeds 20 MB)                 |
| 422         | Validation error (missing file)                |
| 500         | Extraction failed (internal error)             |

## Troubleshooting

### Tesseract Not Found

**Error:** `TesseractNotFoundError`

**Solution:**

- Ensure Tesseract is installed
- On Windows, add Tesseract to PATH or set `pytesseract.pytesseract.tesseract_cmd` in code

### Thai Language Data Missing

**Error:** `Error opening data file...`

**Solution:**

- Install Thai language pack: `sudo apt-get install tesseract-ocr-tha`
- Or download `tha.traineddata` from: https://github.com/tesseract-ocr/tessdata

### Docker Build Fails

**Solution:**

- Ensure Docker daemon is running
- Check disk space
- Try: `docker-compose build --no-cache`

### OCR Quality Issues

**Tips for better OCR results:**

- Use high-quality scans (300+ DPI)
- Ensure good contrast
- Remove noise/artifacts before scanning
- Use clear, standard Thai fonts in original documents

## Performance Considerations

- **Text extraction** (pdf_text): ~50-200ms per page
- **OCR extraction**: ~1-3 seconds per page (depending on resolution and content)
- **Memory usage**: ~100-500 MB depending on PDF size
- **Recommended**: Use load balancer and multiple instances for high-traffic scenarios

## Security Notes

- Files are stored temporarily with random UUID names
- Temporary files are deleted after processing
- No persistent storage of uploaded documents
- Content-type validation (best-effort)
- File size limits enforced
- Configure CORS appropriately for production

## Production Deployment

### Recommendations

1. **Reverse Proxy**: Use nginx or similar
2. **HTTPS**: Enable TLS/SSL
3. **Authentication**: Add API key or OAuth
4. **Rate Limiting**: Implement request throttling
5. **Monitoring**: Add logging aggregation and metrics
6. **Scaling**: Use multiple worker processes or containers

### Example nginx configuration

```nginx
upstream api {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 20M;
    }
}
```

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

- FastAPI framework
- Tesseract OCR project
- PyMuPDF (fitz) for PDF rendering
- pypdf for text extraction
