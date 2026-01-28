# Thai PDF OCR API - LLM Integration Extension

## ✅ Implementation Complete

### What Was Added

#### 1. **New Services** (Clean Architecture)

- `app/services/openrouter_client.py` - OpenRouter API client (HTTP only)
- `app/services/structurer.py` - Prompt building & validation (logic only)
- `app/models/po_schemas.py` - Pydantic models for PO structure

#### 2. **New API Endpoints**

| Endpoint                       | Purpose                      | Input           | Output             |
| ------------------------------ | ---------------------------- | --------------- | ------------------ |
| `POST /extract/pdf`            | Extract text only (existing) | PDF file        | Text + metadata    |
| `POST /llm/structure`          | Structure text via LLM       | Raw text (JSON) | Structured PO JSON |
| `POST /pdf/to-structured-json` | **Complete pipeline**        | PDF file        | Structured PO JSON |

#### 3. **Configuration**

- `.env.example` - Updated with OpenRouter settings
- `requirements.txt` - Added httpx, python-dotenv
- `app/main.py` - Added dotenv loading

#### 4. **Documentation**

- `USAGE.md` - Complete guide for LLM integration
- Updated README.md with new features

### Key Features

✅ **Separation of Concerns**

- PDF extraction completely separate from LLM calls
- Each service has single responsibility
- Easy to test and maintain

✅ **Flexible Architecture**

- Can extract text only (`/extract/pdf`)
- Can structure pre-extracted text (`/llm/structure`)
- Can do everything in one call (`/pdf/to-structured-json`)

✅ **Error Handling**

- 400: Invalid input
- 413: File too large
- 422: Schema validation failed
- 502: LLM service error
- 504: LLM timeout

✅ **Configuration via Environment**

```env
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### Project Structure

```
OCRV2/
├── app/
│   ├── main.py                      # FastAPI app (updated)
│   ├── config.py                    # Environment loading (new)
│   ├── api/
│   │   └── routes.py                # +3 new endpoints
│   ├── services/
│   │   ├── extractor.py             # PDF extraction (existing)
│   │   ├── openrouter_client.py     # OpenRouter API (new)
│   │   └── structurer.py            # Prompt & validation (new)
│   ├── models/
│   │   ├── schemas.py               # OCR schemas (existing)
│   │   └── po_schemas.py            # PO structure schemas (new)
│   └── utils/
│       └── files.py                 # File handling (existing)
│
├── requirements.txt                 # Updated
├── .env.example                     # Updated
├── README.md                        # Updated
├── USAGE.md                         # New - LLM usage guide
└── ...
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy and edit .env
cp .env.example .env

# Add your OpenRouter API key
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Server

```bash
uvicorn app.main:app --reload
```

### 4. Test Endpoints

**A) Extract text only:**

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@sample.pdf"
```

**B) Structure text:**

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -d '{"text": "PO-001\nบริษัท ABC"}'
```

**C) Complete pipeline:**

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -F "file=@purchase_order.pdf"
```

## 📊 Schema

The LLM returns structured data following this schema:

```typescript
{
  header: {
    poNumber: string | null,
    poDate: string | null,      // ISO format
    customer: {
      name: string | null,
      tel: string | null,
      address: string | null,
      ...
    }
  },
  items: [{
    codeSteel: string | null,   // e.g., "SS400"
    thickness: number | null,   // mm
    width: number | null,       // mm
    length: number | null,      // mm
    quantity: number | null,    // pieces
    shape: "square" | "line" | null,
    confidence: number          // 0.0-1.0
  }],
  meta: {
    confidence: number,         // 0.0-1.0
    warnings: string[],
    rawText: string | null
  }
}
```

## 🎯 Design Principles

1. **Single Responsibility**
   - `extractor.py` - Only PDF text extraction
   - `openrouter_client.py` - Only HTTP calls to OpenRouter
   - `structurer.py` - Only prompt building & validation

2. **Dependency Injection**

   ```python
   openrouter = OpenRouterClient()  # Independent service
   structurer = TextStructurer()     # Independent service
   ```

3. **Type Safety**
   - All responses validated with Pydantic
   - Schema enforcement at runtime
   - Clear error messages

4. **Environment-Based Config**
   - No hardcoded API keys
   - Easy to switch models
   - Production-ready

## 🔧 Customization

### Change LLM Model

```bash
# Edit .env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### Modify Schema

```python
# Edit app/models/po_schemas.py
class POHeader(BaseModel):
    # Add your fields here
    myCustomField: Optional[str] = None
```

### Adjust Prompt

```python
# Edit app/services/structurer.py
def build_prompt(self, text: str):
    # Customize system/user prompts
```

## 📝 Testing

Interactive testing at: http://localhost:8000/docs

All endpoints have:

- Request examples
- Response schemas
- Try-it-out functionality

## 🆘 Support

- Documentation: `README.md` and `USAGE.md`
- API Docs: http://localhost:8000/docs
- OpenRouter Docs: https://openrouter.ai/docs

## ✨ Next Steps

Potential enhancements:

1. Add caching for similar documents
2. Implement batch processing endpoint
3. Add webhook for async processing
4. Implement retry logic for LLM failures
5. Add confidence-based validation rules
6. Support multiple languages
7. Add export to Excel/CSV

---

**Version:** 2.0.0  
**Status:** Production Ready ✅  
**Last Updated:** January 28, 2026
