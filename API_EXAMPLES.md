# ตัวอย่าง cURL Commands สำหรับทุก API Endpoints

## � Authentication

**สำคัญ!** ทุก API endpoint (ยกเว้น `/` และ `/health`) ต้องใส่ token ใน header

```bash
X-API-Token: my-secret-token-12345
```

**Token ปัจจุบัน:** `my-secret-token-12345` (เปลี่ยนได้ที่ไฟล์ `.env`)

**ดูรายละเอียดเพิ่มเติม:** [AUTHENTICATION.md](AUTHENTICATION.md)

---

## �📋 รายการ API ทั้งหมด

1. [GET /](#1-get---health-check) - Health check
2. [GET /health](#2-get-health---detailed-health-check) - Detailed health check
3. [POST /extract/pdf](#3-post-extractpdf---แยกข้อความจาก-pdf) - แยกข้อความจาก PDF
4. [POST /llm/structure](#4-post-llmstructure---แปลงข้อความเป็น-json-ด้วย-llm) - แปลงข้อความเป็น JSON ด้วย LLM
5. [POST /pdf/to-structured-json](#5-post-pdfto-structured-json---pipeline-เต็มรูปแบบ-) - Pipeline เต็มรูปแบบ

---

## 1. GET / - Health Check

**คำอธิบาย:** ตรวจสอบสถานะเบื้องต้นของ API

### Basic Request

```bash
curl http://localhost:8000/
```

### With Headers

```bash
curl -X GET "http://localhost:8000/" \
  -H "accept: application/json"
```

### Response

```json
{
  "status": "healthy",
  "service": "Thai PDF OCR API",
  "version": "2.0.0"
}
```

---

## 2. GET /health - Detailed Health Check

**คำอธิบาย:** ตรวจสอบสถานะโดยละเอียด

### Request

```bash
curl http://localhost:8000/health
```

### With Pretty Print

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

### Response

```json
{
  "status": "healthy",
  "checks": {
    "api": "ok"
  }
}
```

---

## 3. POST /extract/pdf - แยกข้อความจาก PDF

**คำอธิบาย:** อัปโหลด PDF และแยกข้อความภาษาไทย (ไม่ใช้ LLM)

**🔑 ต้องใส่ token!**

### ตัวอย่าง 1: Basic Upload

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@sample.pdf"
```

### ตัวอย่าง 2: With Headers

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -H "accept: application/json" \
  -F "file=@document.pdf"
```

### ตัวอย่าง 3: Save Response to File

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@purchase_order.pdf" \
  -o output.json
```

### ตัวอย่าง 4: With Pretty Print

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@sample.pdf" \
  | python -m json.tool
```

### ตัวอย่าง 5: Show Progress

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@large_document.pdf" \
  --progress-bar
```

### Response Example

```json
{
  "text": "ใบสั่งซื้อ\nเลขที่: PO-001\nวันที่: 27/01/2026\nบริษัท ABC จำกัด...",
  "pages": ["ใบสั่งซื้อ\nเลขที่: PO-001...", "หน้าที่ 2..."],
  "meta": {
    "page_count": 2,
    "extraction_method": "pdf_text",
    "processing_time_ms": 156
  }
}
```

### Error Examples

```bash
# ไม่ใส่ token
curl -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@document.pdf"
# Response: 401 Unauthorized - Invalid or missing API token

# Token ผิด
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: wrong-token" \
  -F "file=@document.pdf"
# Response: 401 Unauthorized - Invalid or missing API token

# ไฟล์ใหญ่เกินไป (> 20MB)
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@large_file.pdf"
# Response: 413 File too large

# ไม่ใช่ไฟล์ PDF
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@document.docx"
# Response: 400 Invalid file extension
```

---

## 4. POST /llm/structure - แปลงข้อความเป็น JSON ด้วย LLM

**คำอธิบาย:** ส่งข้อความที่แยกได้แล้ว ให้ LLM แปลงเป็น JSON ตามโครงสร้างที่กำหนด

**🔑 ต้องใส่ token!**

### ตัวอย่าง 1: Basic Request

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{
    "text": "ใบสั่งซื้อ\nเลขที่: PO-001\nวันที่: 27/01/2026\nบริษัท ABC Steel จำกัด\nเหล็ก SS400: 12 x 100 x 2000 mm จำนวน 50 ชิ้น"
  }'
```

### ตัวอย่าง 2: Without Raw Text in Response

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{
    "text": "ใบสั่งซื้อ\nPO-001\nบริษัท XYZ",
    "include_raw_text": false
  }'
```

### ตัวอย่าง 3: With Raw Text (Default)

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{
    "text": "PO-2026-123\nวันที่ 27 ม.ค. 2569\nบริษัท ABC",
    "include_raw_text": true
  }'
```

### ตัวอย่าง 4: Complex PO with Multiple Items

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \  -H "X-API-Token: my-secret-token-12345" \  -d '{
    "text": "ใบสั่งซื้อเหล็ก\nPO-2026-001\nวันที่: 27/01/2026\nบริษัท: เอบีซี สตีล จำกัด\nเบอร์โทร: 02-123-4567\nที่อยู่: 123 ถนนสุขุมวิท กรุงเทพฯ\n\nรายการสินค้า:\n1. เหล็กแผ่น SS400\n   หนา 12 mm กว้าง 100 mm ยาว 2000 mm\n   จำนวน 50 ชิ้น\n2. เหล็กแท่ง RB12\n   หนา 12 mm ยาว 6000 mm\n   จำนวน 100 เส้น"
  }'
```

### ตัวอย่าง 5: From File

```bash
# สร้างไฟล์ JSON ก่อน
cat > request.json << 'EOF'
{
  "text": "ใบสั่งซื้อ\nPO-001\nบริษัท ABC จำกัด\nเหล็ก SS400: 12x100x2000 จำนวน 50",
  "include_raw_text": false
}
EOF

# ส่ง request
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d @request.json
```

### ตัวอย่าง 6: With Pretty Print and Save

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{"text": "PO-001\nบริษัท ABC"}' \
  | python -m json.tool > structured_output.json
```

### Response Example

```json
{
  "result": {
    "header": {
      "poNumber": "PO-001",
      "poDate": "2026-01-27",
      "deliveryDate": null,
      "yourRef": null,
      "customer": {
        "name": "บริษัท ABC Steel จำกัด",
        "taxNumber": null,
        "tel": "02-123-4567",
        "email": null,
        "faxNumber": null,
        "address": "123 ถนนสุขุมวิท กรุงเทพฯ",
        "code": null
      }
    },
    "items": [
      {
        "codeSteel": "SS400",
        "description": "เหล็กแผ่น SS400",
        "shape": "square",
        "width": 100,
        "length": 2000,
        "thickness": 12,
        "quantity": 50,
        "cuttingMethod": null,
        "job": null,
        "notes": null,
        "matchedSteelTypeId": null,
        "confidence": 0.95
      }
    ],
    "meta": {
      "confidence": 0.92,
      "warnings": [],
      "rawText": "ใบสั่งซื้อ...",
      "fields": {
        "customer.name": 0.98,
        "poNumber": 0.99
      }
    }
  },
  "processing_time_ms": 1823
}
```

### Error Examples

```bash
# ไม่มี text
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 422 Validation Error

# OpenRouter API key ไม่ได้ตั้งค่า
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
# Response: 502 LLM service error
```

---

## 5. POST /pdf/to-structured-json - Pipeline เต็มรูปแบบ ⭐

**คำอธิบาย:** อัปโหลด PDF → แยกข้อความ → ส่ง LLM → รับ JSON (ทำทั้งหมดในครั้งเดียว)

**🔑 ต้องใส่ token!**

### ตัวอย่าง 1: Basic Upload

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@purchase_order.pdf"
```

### ตัวอย่าง 2: Without Raw Text

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json?include_raw_text=false" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@document.pdf"
```

### ตัวอย่าง 3: With Raw Text (Default)

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json?include_raw_text=true" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@po_document.pdf"
```

### ตัวอย่าง 4: Save to File

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@purchase_order.pdf" \
  -o structured_result.json
```

### ตัวอย่าง 5: With Progress and Pretty Print

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@document.pdf" \
  --progress-bar \
  | python -m json.tool
```

### ตัวอย่าง 6: Multiple Files (Sequential)

```bash
# สร้าง script สำหรับประมวลผลหลายไฟล์
for file in *.pdf; do
  echo "Processing: $file"
  curl -X POST "http://localhost:8000/pdf/to-structured-json" \
    -H "X-API-Token: my-secret-token-12345" \
    -F "file=@$file" \
    -o "${file%.pdf}_output.json"
  echo "✓ Done: ${file%.pdf}_output.json"
done
```

### ตัวอย่าง 7: With Timeout

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@large_document.pdf" \
  --max-time 120
```

### Response Example

```json
{
  "ocr": {
    "page_count": 2,
    "extraction_method": "pdf_text",
    "text_length": 1234
  },
  "result": {
    "header": {
      "poNumber": "PO-2026-001",
      "poDate": "2026-01-27",
      "deliveryDate": "2026-02-10",
      "yourRef": "REF-ABC-123",
      "customer": {
        "name": "บริษัท เอบีซี สตีล จำกัด",
        "taxNumber": "0123456789012",
        "tel": "02-123-4567",
        "email": "contact@abc-steel.com",
        "faxNumber": "02-123-4568",
        "address": "123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพฯ 10110",
        "code": "CUST-001"
      }
    },
    "items": [
      {
        "codeSteel": "SS400",
        "description": "เหล็กแผ่นดำ SS400",
        "shape": "square",
        "width": 100,
        "length": 2000,
        "thickness": 12,
        "quantity": 50,
        "cuttingMethod": "normal",
        "job": 1,
        "notes": "ตัดตามขนาด",
        "matchedSteelTypeId": "ST-001",
        "confidence": 0.95
      },
      {
        "codeSteel": "RB12",
        "description": "เหล็กเส้นกลม RB12",
        "shape": "line",
        "width": null,
        "length": 6000,
        "thickness": 12,
        "quantity": 100,
        "cuttingMethod": null,
        "job": 2,
        "notes": null,
        "matchedSteelTypeId": "ST-005",
        "confidence": 0.92
      }
    ],
    "meta": {
      "confidence": 0.93,
      "warnings": ["Delivery date might be approximate"],
      "rawText": "ใบสั่งซื้อ\n...",
      "fields": {
        "customer.name": 0.99,
        "customer.tel": 0.95,
        "poNumber": 0.99,
        "poDate": 0.97
      }
    }
  },
  "processing_time_ms": 3245
}
```

---

## 🛠️ ตัวอย่างการใช้งานจริง (Real-world Examples)

### Scenario 1: ประมวลผล PO และบันทึกผล

```bash
#!/bin/bash
# process_po.sh - Script สำหรับประมวลผล PO

PDF_FILE="$1"
if [ -z "$PDF_FILE" ]; then
  echo "Usage: ./process_po.sh <pdf_file>"
  exit 1
fi

echo "📄 Processing: $PDF_FILE"

# ส่งไปประมวลผล
RESPONSE=$(curl -s -X POST "http://localhost:8000/pdf/to-structured-json" \
  -F "file=@$PDF_FILE")

# ตรวจสอบสถานะ
if echo "$RESPONSE" | grep -q '"poNumber"'; then
  # สำเร็จ - บันทึกไฟล์
  OUTPUT_FILE="${PDF_FILE%.pdf}_structured.json"
  echo "$RESPONSE" | python -m json.tool > "$OUTPUT_FILE"
  echo "✅ Success! Output saved to: $OUTPUT_FILE"

  # แสดงข้อมูลสำคัญ
  PO_NUM=$(echo "$RESPONSE" | python -c "import json, sys; print(json.load(sys.stdin)['result']['header']['poNumber'])")
  CUSTOMER=$(echo "$RESPONSE" | python -c "import json, sys; print(json.load(sys.stdin)['result']['header']['customer']['name'])")
  ITEMS=$(echo "$RESPONSE" | python -c "import json, sys; print(len(json.load(sys.stdin)['result']['items']))")

  echo "PO Number: $PO_NUM"
  echo "Customer: $CUSTOMER"
  echo "Items: $ITEMS"
else
  echo "❌ Error processing file"
  echo "$RESPONSE"
fi
```

### Scenario 2: เปรียบเทียบวิธีต่างๆ

```bash
#!/bin/bash
# compare_methods.sh - เปรียบเทียบเวลาประมวลผล

PDF_FILE="sample.pdf"

echo "=== Method 1: Text Extraction Only ==="
time curl -s -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@$PDF_FILE" > text_only.json

echo -e "\n=== Method 2: Complete Pipeline ==="
time curl -s -X POST "http://localhost:8000/pdf/to-structured-json" \
  -F "file=@$PDF_FILE" > structured.json

echo -e "\n=== Method 3: Two-step Process ==="
# Step 1: Extract
time TEXT=$(curl -s -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@$PDF_FILE" | python -c "import json, sys; print(json.load(sys.stdin)['text'])")

# Step 2: Structure
time curl -s -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TEXT\"}" > structured_2step.json
```

### Scenario 3: Batch Processing

```bash
#!/bin/bash
# batch_process.sh - ประมวลผล PDF หลายไฟล์

INPUT_DIR="./purchase_orders"
OUTPUT_DIR="./structured_results"

mkdir -p "$OUTPUT_DIR"

for pdf_file in "$INPUT_DIR"/*.pdf; do
  filename=$(basename "$pdf_file" .pdf)
  echo "Processing: $filename"

  curl -s -X POST "http://localhost:8000/pdf/to-structured-json?include_raw_text=false" \
    -F "file=@$pdf_file" \
    | python -m json.tool > "$OUTPUT_DIR/${filename}.json"

  if [ $? -eq 0 ]; then
    echo "  ✅ $filename - Success"
  else
    echo "  ❌ $filename - Failed"
  fi
done

echo "Done! Results in: $OUTPUT_DIR"
```

---

## 🧪 การทดสอบ API

### Test Health

```bash
# ทดสอบว่า API ทำงานหรือไม่
curl -f http://localhost:8000/health || echo "API is down!"
```

### Test with Sample Data

```bash
# สร้าง PDF ทดสอบ (ต้องมี Python)
cat > create_test_pdf.py << 'EOF'
from pypdf import PdfWriter

writer = PdfWriter()
writer.add_blank_page(width=200, height=200)

with open("test.pdf", "wb") as f:
    writer.write(f)
print("Created test.pdf")
EOF

python create_test_pdf.py

# ทดสอบ API
curl -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@test.pdf"
```

### Load Testing

```bash
# ทดสอบ performance (ต้องมี ab - Apache Bench)
ab -n 10 -c 2 http://localhost:8000/health
```

---

## 🔧 Tips & Tricks

### 1. สร้าง alias สำหรับ commands ที่ใช้บ่อย

```bash
# เพิ่มใน ~/.bashrc หรือ ~/.zshrc
alias ocr-extract='curl -X POST "http://localhost:8000/extract/pdf" -H "X-API-Token: my-secret-token-12345" -F "file=@"'
alias ocr-structure='curl -X POST "http://localhost:8000/pdf/to-structured-json" -H "X-API-Token: my-secret-token-12345" -F "file=@"'

# ใช้งาน
ocr-extract sample.pdf
ocr-structure purchase_order.pdf
```

### 2. ใช้ jq แทน python สำหรับ JSON

```bash
# ติดตั้ง jq
# Ubuntu/Debian: sudo apt-get install jq
# macOS: brew install jq
# Windows: choco install jq

# ใช้งาน
curl -s -X POST "http://localhost:8000/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@po.pdf" | jq '.result.header.poNumber'
```

### 3. Debug mode

```bash
# แสดง headers และ response
curl -v -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@sample.pdf"

# แสดงเฉพาะ status code
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "http://localhost:8000/health"
```

---

## 📊 Response Status Codes

| Code | Meaning               | Example                        |
| ---- | --------------------- | ------------------------------ |
| 200  | Success               | Request processed successfully |
| 401  | Unauthorized          | Invalid or missing API token   |
| 400  | Bad Request           | Invalid file extension         |
| 413  | Payload Too Large     | File > 20MB                    |
| 422  | Validation Error      | Schema validation failed       |
| 502  | Bad Gateway           | LLM service error              |
| 504  | Gateway Timeout       | LLM timeout                    |
| 500  | Internal Server Error | Unexpected error               |

---

## 🚀 Quick Reference

```bash (ไม่ต้องใช้ token)
curl http://localhost:8000/health

# Extract text only (ต้องใช้ token)
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@doc.pdf"

# Structure text (ต้องใช้ token)
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{"text": "PO-001..."}'

# Complete pipeline (แนะนำ! ต้องใช้ token)
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \

curl -X POST "http://localhost:8000/pdf/to-structured-json" -F "file=@po.pdf"
```

--**ต้องใส่ `X-API-Token` header ในทุก request** (ยกเว้น `/` และ `/health`)

- Token ปัจจุบัน: `my-secret-token-12345` (เปลี่ยนได้ที่ไฟล์ `.env`)
- ต้องตั้งค่า `OPENROUTER_API_KEY` ใน `.env` ก่อนใช้ LLM endpoints
- สำหรับไฟล์ใหญ่ ให้ใช้ `--max-time` เพื่อกำหนด timeout
- ดูรายละเอียดเพิ่มเติมเกี่ยว authentication: [AUTHENTICATION.md](AUTHENTICATION.md)
  **หมายเหตุ:**

- เปลี่ยน `localhost:8000` เป็น URL ของ server จริงถ้าใช้งาน production
- ต้องตั้งค่า `OPENROUTER_API_KEY` ใน `.env` ก่อนใช้ LLM endpoints
- สำหรับไฟล์ใหญ่ ให้ใช้ `--max-time` เพื่อกำหนด timeout
