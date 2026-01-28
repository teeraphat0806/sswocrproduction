# API Usage Guide - LLM Integration

## New Endpoints (v2.0)

### 1. POST /llm/structure

Structure extracted text into JSON using OpenRouter.ai

**Request:**

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ใบสั่งซื้อ\nเลขที่: PO-001\nวันที่: 27/01/2026\nบริษัท: ABC Steel จำกัด\nเหล็ก SS400: 12 x 100 x 2000 mm จำนวน 50 ชิ้น",
    "include_raw_text": false
  }'
```

**Response:**

```json
{
  "result": {
    "header": {
      "poNumber": "PO-001",
      "poDate": "2026-01-27",
      "customer": { "name": "บริษัท ABC Steel จำกัด" }
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
    "meta": { "confidence": 0.92 }
  },
  "processing_time_ms": 1523
}
```

### 2. POST /pdf/to-structured-json ⭐ RECOMMENDED

Complete pipeline: PDF → Text → Structure → JSON

**Request:**

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -F "file=@purchase_order.pdf"
```

**Python Example:**

```python
import requests

url = "http://localhost:8000/pdf/to-structured-json"
with open("purchase_order.pdf", "rb") as f:
    response = requests.post(url, files={"file": f})

data = response.json()
print(f"PO#: {data['result']['header']['poNumber']}")
print(f"Customer: {data['result']['header']['customer']['name']}")
print(f"Items: {len(data['result']['items'])}")

for item in data['result']['items']:
    print(f"  - {item['codeSteel']}: {item['thickness']}x{item['width']}x{item['length']} @ {item['quantity']} pcs")
```

## Setup OpenRouter.ai

### 1. Get API Key

1. Visit https://openrouter.ai
2. Sign up / Log in
3. Go to https://openrouter.ai/keys
4. Create new key
5. Copy key (starts with `sk-or-v1-...`)

### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env and add:
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=openai/gpt-4o-mini  # or other model
```

### 3. Test Connection

```bash
# Start server
uvicorn app.main:app --reload

# Test with sample text
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test PO\nPO-001\nCompany ABC"}'
```

## Model Selection

Edit `OPENROUTER_MODEL` in `.env`:

| Model                         | Best For       | Speed  | Cost/1M tokens |
| ----------------------------- | -------------- | ------ | -------------- |
| `openai/gpt-4o-mini`          | Default choice | Fast   | ~$0.15         |
| `openai/gpt-4o`               | High accuracy  | Medium | ~$2.50         |
| `anthropic/claude-3.5-sonnet` | Thai language  | Medium | ~$3.00         |
| `google/gemini-pro-1.5`       | Long docs      | Fast   | ~$1.25         |
| `meta-llama/llama-3.1-70b`    | Budget         | Fast   | ~$0.50         |

See all models: https://openrouter.ai/models

## Cost Estimation

Typical PO document (~1-2 pages, ~2000 tokens):

- Input: ~2000 tokens
- Output: ~500 tokens
- **Cost per PO: ~$0.001-0.01** (depending on model)

Monthly cost for 100 POs/day with gpt-4o-mini: ~$30-50

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /pdf/to-structured-json
       ▼
┌─────────────────────────────────────┐
│         FastAPI Router              │
│     (app/api/routes.py)             │
└──────┬──────────────────────────────┘
       │
       ├──► PDFExtractor.extract()
       │    └─► Text Extraction / OCR
       │         (app/services/extractor.py)
       │
       ├──► TextStructurer.build_prompt()
       │    └─► Create LLM prompt
       │         (app/services/structurer.py)
       │
       ├──► OpenRouterClient.call_openrouter()
       │    └─► HTTP call to OpenRouter API
       │         (app/services/openrouter_client.py)
       │
       └──► TextStructurer.parse_and_validate()
            └─► Pydantic validation
                 (app/models/po_schemas.py)
```

## Error Handling

| Status | Cause                    | Solution                                 |
| ------ | ------------------------ | ---------------------------------------- |
| 400    | Invalid file/input       | Check file format and size               |
| 413    | File too large           | Reduce file size or increase limit       |
| 422    | Schema validation failed | LLM output doesn't match schema          |
| 502    | LLM service error        | Check OpenRouter status                  |
| 504    | LLM timeout              | Reduce document size or increase timeout |

## Troubleshooting

### "OpenRouter API key is required"

```bash
# Check .env file exists
cat .env | grep OPENROUTER_API_KEY

# If missing, add it:
echo "OPENROUTER_API_KEY=sk-or-v1-your-key" >> .env
```

### "LLM returned invalid JSON"

- LLM occasionally returns markdown or text
- Check model selection (some models better than others)
- Try increasing temperature=0 for more deterministic output

### High costs

- Use cheaper model like `gpt-4o-mini` instead of `gpt-4o`
- Enable caching if processing similar documents
- Implement rate limiting

## Security Best Practices

1. **Never commit .env file**

   ```bash
   # .gitignore already includes:
   .env
   ```

2. **Rotate API keys regularly**
   - Generate new key monthly
   - Revoke old keys

3. **Monitor usage**
   - Check OpenRouter dashboard: https://openrouter.ai/activity
   - Set spending limits

4. **Production deployment**
   - Use secrets manager (AWS Secrets Manager, Azure Key Vault)
   - Don't store keys in code or containers
   - Use environment variables injection
