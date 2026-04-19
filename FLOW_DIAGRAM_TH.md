# Thai PDF OCR API - Flow Diagram (ภาษาไทย + Token Validation)

## Mermaid Code - Complete Flow with Token

````mermaid
flowchart TD
    Start([เริ่มต้น]) --> ReqInfo["📨 Client Request<br/>POST /pdf/to-structured-json<br/>+ PDF File<br/>+ X-API-Token Header"]

    ReqInfo --> CheckToken{"ส่ง Token<br/>มาหรือไม่?"}

    CheckToken -->|ไม่มี Token| Error0["❌ HTTP 401<br/>ไม่พบ Token<br/>ต้องใส่ X-API-Token<br/>ใน Header"]
    Error0 --> End0([สิ้นสุด])

    CheckToken -->|มี Token| VerifyToken["🔐 Verify Token<br/>ตรวจสอบ Token<br/>ว่าตรงกับ env<br/>API_TOKEN"]

    VerifyToken --> TokenMatch{"Token<br/>ถูกต้องหรือไม่?"}

    TokenMatch -->|Token ผิด| Error01["❌ HTTP 401<br/>Token ไม่ถูกต้อง<br/>Invalid API Token"]
    Error01 --> End01([สิ้นสุด])

    TokenMatch -->|Token ถูก| LogAuth["📝 Log Detail<br/>✓ Token verified<br/>Client IP: xxx<br/>Request ID: xxx<br/>Timestamp: xxx"]

    LogAuth --> ValidateFile{"ตรวจสอบไฟล์<br/>ขนาด <= 20MB<br/>นามสกุล .pdf"}

    ValidateFile -->|FAIL| Error1["❌ HTTP 400/413<br/>ไฟล์ไม่ถูกต้อง"]
    Error1 --> LogError1["📝 Log Error<br/>File validation failed"]
    LogError1 --> End1([สิ้นสุด])

    ValidateFile -->|PASS| SaveTemp["💾 บันทึกไฟล์ชั่วคราว<br/>ในโฟลเดอร์ /tmp"]

    SaveTemp --> LogSave["📝 Log Detail<br/>File saved: /tmp/uuid.pdf<br/>File size: xxx KB"]

    LogSave --> ExtractModule["🔍 PDFExtractor.extract<br/>เริ่มแยกข้อความ"]

    ExtractModule --> TryText["📄 พยายาม pypdf<br/>Text Extraction<br/>อ่านทีละหน้า"]

    TryText --> CheckThai{"ตรวจสอบคุณภาพ<br/>ความยาว >= 10 ตัวอักษร<br/>และ ตัวอักษรไทย >= 10%"}

    CheckThai -->|ผ่าน| UseText["✓ ใช้วิธี PDF Text<br/>method = pdf_text<br/>เนื่องจาก PDF มี<br/>text layer ชัดเจน"]

    CheckThai -->|ไม่ผ่าน| FallbackOCR["🔄 Fallback to OCR<br/>ข้อความที่แยกได้<br/>ไม่เพียงพอ"]

    LogTryText["📝 Log Detail<br/>pypdf result:<br/>Text length: xxx<br/>Thai ratio: x.xx%"]
    TryText --> LogTryText
    LogTryText --> CheckThai

    FallbackOCR --> OCREngine["🤖 Tesseract OCR<br/>+ Thai Language Pack<br/>- fitz render page to image<br/>- 2x zoom = 144 DPI<br/>- pytesseract tha+eng<br/>- psm3 oem3 config"]

    OCREngine --> UseOCR["✓ ใช้วิธี OCR<br/>method = ocr<br/>เนื่องจาก PDF<br/>เป็นภาพสแกน"]

    LogOCR["📝 Log Detail<br/>OCR completed:<br/>Pages: x<br/>Total text length: xxx"]
    OCREngine --> LogOCR
    LogOCR --> UseOCR

    UseText --> CombinedText["📚 รวมข้อความทั้งหมด<br/>- text: ข้อความรวม<br/>- pages: array ของแต่ละหน้า<br/>- page_count: จำนวนหน้า<br/>- extraction_method: pdf_text|ocr"]
    UseOCR --> CombinedText

    CombinedText --> BuildPrompt["📝 TextStructurer<br/>build_prompt"]

    BuildPrompt --> SysPrompt["📋 System Prompt<br/>- JSON Schema เต็ม<br/>- กฎการแยกข้อมูล PO ไทย<br/>- กฎการจำแนก shape<br/>- รายการชื่อบริษัทที่ไม่ใช่<br/>  เป็นลูกค้า SSW"]

    SysPrompt --> UserPrompt["👤 User Prompt<br/>--- TEXT FROM OCR ---<br/>[ข้อความที่แยก]<br/>--- END TEXT ---<br/>Return ONLY JSON"]

    UserPrompt --> CallLLM["🤖 OpenRouterClient<br/>call_openrouter"]

    CallLLM --> LLMConfig["⚙️ Config:<br/>Model: gpt-4o-mini<br/>Temperature: 0.0<br/>Timeout: 60 seconds<br/>Custom headers: auth+referer"]

    LLMConfig --> HTTPCall["📤 HTTP POST<br/>to openrouter.ai/api/v1<br/>/chat/completions"]

    LogReq["📝 Log Detail<br/>LLM Request:<br/>Model: gpt-4o-mini<br/>Input tokens: xxx<br/>Temperature: 0.0"]
    HTTPCall --> LogReq
    LogReq --> LLMResponse{"LLM Response<br/>สำเร็จหรือไม่?"}

    LLMResponse -->|Error/Timeout| TryFallback["🔄 Fallback Models<br/>พยายามใช้ alternative<br/>1. gpt-3.5-turbo<br/>2. claude-3-haiku<br/>3. gemini-pro"]

    TryFallback --> FBResult{"Fallback<br/>สำเร็จหรือไม่?"}

    FBResult -->|ล้มเหลว| Error2["❌ HTTP 502/504<br/>LLM Service Error<br/>ไม่สามารถเรียก<br/>OpenRouter API ได้"]
    Error2 --> LogError2["📝 Log Error<br/>LLM call failed<br/>All models failed<br/>Last error: xxx"]
    LogError2 --> Cleanup1["🧹 ลบไฟล์ชั่วคราว"]
    Cleanup1 --> End2([สิ้นสุด])

    LLMResponse -->|Success| RawJSON["📥 ได้ Raw JSON<br/>จาก OpenRouter"]
    FBResult -->|สำเร็จ| RawJSON

    LogResp["📝 Log Detail<br/>LLM Response:<br/>Status: 200<br/>Model used: xxx<br/>Output tokens: xxx"]
    RawJSON --> LogResp
    LogResp --> ParseVal["🔍 TextStructurer<br/>parse_and_validate"]

    ParseVal --> CleanMD["🧹 ทำความสะอาด<br/>- ลบ ``` fences<br/>- Trim whitespace<br/>- Normalize format"]

    CleanMD --> JSONParse["📦 json.loads<br/>แปลง string เป็น<br/>Python dict"]

    JSONParse -->|JSON Invalid| Error3["❌ HTTP 502<br/>Invalid JSON<br/>from LLM<br/>ไม่สามารถ parse<br/>เป็น JSON ได้"]
    Error3 --> LogError3["📝 Log Error<br/>JSON parse failed<br/>Snippet: xxx..."]
    LogError3 --> Cleanup1

    JSONParse -->|JSON Valid| PydanticVal["✔️ Pydantic<br/>Validation<br/>ตรวจสอบ schema<br/>OCRPOResult"]

    PydanticVal -->|Validation Error| Error4["❌ HTTP 422<br/>Schema Validation<br/>Failed<br/>ข้อมูลไม่ตรง schema"]
    Error4 --> LogError4["📝 Log Error<br/>Validation failed<br/>Errors: xxx"]
    LogError4 --> Cleanup1

    PydanticVal -->|Validation Success| BuildResp["✅ สร้าง Success<br/>Response<br/>PDFToStructuredResponse"]

    LogValidate["📝 Log Detail<br/>Validation:<br/>Status: PASSED<br/>PO Number: xxx<br/>Items count: x<br/>Confidence: x.xx"]

    PydanticVal -->|Validation Success| LogValidate

    BuildResp --> RespData["📊 Response Data:<br/>- ocr:<br/>  page_count: x<br/>  extraction_method: xxx<br/>  text_length: xxx<br/>- result: OCRPOResult<br/>- processing_time_ms: xxx"]

    RespData --> Return200["✓ HTTP 200 OK<br/>Return JSON Response"]

    LogSuccess["📝 Log Detail<br/>✓ Processing Complete<br/>Status: SUCCESS<br/>Total time: xxx ms<br/>LLM model: xxx<br/>Extraction: pdf_text|ocr"]

    Return200 --> LogSuccess

    LogSuccess --> Cleanup2["🧹 ลบไฟล์ชั่วคราว"]

    Cleanup2 --> LogCleanup["📝 Log Detail<br/>Temp file deleted"]

    LogCleanup --> End3["✓ สิ้นสุด<br/>Success"]

    style Start fill:#90EE90
    style End3 fill:#90EE90
    style End0 fill:#FFB6C6
    style End01 fill:#FFB6C6
    style Error0 fill:#FFB6C6
    style Error01 fill:#FFB6C6
    style Error1 fill:#FFB6C6
    style Error2 fill:#FFB6C6
    style Error3 fill:#FFB6C6
    style Error4 fill:#FFB6C6
    style CheckToken fill:#F3E5F5
    style VerifyToken fill:#F3E5F5
    style TokenMatch fill:#F3E5F5
    style LogAuth fill:#E1BEE7
    style ValidateFile fill:#87CEEB
    style CheckThai fill:#87CEEB
    style PydanticVal fill:#87CEEB
    style LLMResponse fill:#87CEEB
    style FBResult fill:#87CEEB
    style UseText fill:#FFFFE0
    style UseOCR fill:#FFFFE0
    style BuildResp fill:#DDA0DD
    style Return200 fill:#DDA0DD
    style RawJSON fill:#FFE5B4
    style JSONParse fill:#FFE5B4
````

---

## หมายเหตุ: Token Validation Layer

### 1️⃣ ไม่มี Token Header

```
Request: POST /pdf/to-structured-json
Header: (ไม่มี X-API-Token)

Response:
HTTP 401 Unauthorized
{
  "detail": "Invalid or missing API token"
}

Log:
[ERROR] Authentication failed: Missing token
       Client IP: 192.168.1.1
       Timestamp: 2026-04-06T14:35:22Z
```

### 2️⃣ Token ผิด

```
Request: POST /pdf/to-structured-json
Header: X-API-Token: wrong-token-123

Response:
HTTP 401 Unauthorized
{
  "detail": "Invalid or missing API token"
}

Log:
[ERROR] Authentication failed: Invalid token
       Provided: wrong-token-123****
       Expected: my-secret-token-****
       Client IP: 192.168.1.1
       Timestamp: 2026-04-06T14:35:22Z
```

### 3️⃣ Token ถูก (ผ่าน)

```
Request: POST /pdf/to-structured-json
Header: X-API-Token: my-secret-token-12345
File: purchase_order.pdf

Response:
HTTP 200 OK
{
  "ocr": {...},
  "result": {...},
  "processing_time_ms": 2345
}

Log:
[INFO] Authentication successful
       Verified token: my-secret-token-****
       Client IP: 192.168.1.1
       Request ID: req_a1b2c3d4e5f6
       Timestamp: 2026-04-06T14:35:22Z

[INFO] Processing started
       Filename: purchase_order.pdf
       File size: 256 KB
       Request ID: req_a1b2c3d4e5f6

[INFO] Extraction completed
       Method: pdf_text
       Pages: 2
       Text length: 1234
       Request ID: req_a1b2c3d4e5f6

[INFO] LLM call initiated
       Model: gpt-4o-mini
       Request ID: req_a1b2c3d4e5f6

[INFO] Processing completed successfully
       Status: SUCCESS
       Total time: 2345 ms
       Extraction: pdf_text
       Confidence: 0.92
       PO Number: PO-2026-001
       Items: 5
       Request ID: req_a1b2c3d4e5f6
```

---

## Log Format Template

```properties
[TIMESTAMP] [LEVEL] [REQUEST_ID] [MESSAGE]
           [ADDITIONAL_CONTEXT]

# Example:
[2026-04-06T14:35:22.123Z] [INFO] [req_a1b2c3d4e5f6] Authentication successful
                                   Client IP: 192.168.1.100
                                   User Agent: curl/7.81.0
                                   Token: my-secret-token-****

[2026-04-06T14:35:23.456Z] [INFO] [req_a1b2c3d4e5f6] File validation passed
                                   Filename: po_2026.pdf
                                   Size: 256 KB
                                   Content-Type: application/pdf

[2026-04-06T14:35:45.789Z] [INFO] [req_a1b2c3d4e5f6] Extraction method: pdf_text
                                   Pages: 2
                                   Text length: 1234 chars
                                   Thai ratio: 45.23%

[2026-04-06T14:35:46.012Z] [INFO] [req_a1b2c3d4e5f6] LLM request sent
                                   Model: gpt-4o-mini
                                   Input tokens: ~2000
                                   Temperature: 0.0

[2026-04-06T14:35:47.345Z] [INFO] [req_a1b2c3d4e5f6] LLM response received
                                   Output tokens: ~500
                                   Status: 200
                                   Response time: 1333ms

[2026-04-06T14:35:47.567Z] [INFO] [req_a1b2c3d4e5f6] Validation passed
                                   Schema: OCRPOResult
                                   Overall confidence: 0.92
                                   PO Number: PO-2026-001
                                   Items count: 5
                                   Warnings: 0

[2026-04-06T14:35:47.890Z] [INFO] [req_a1b2c3d4e5f6] Response sent successfully
                                   Status: HTTP 200
                                   Response time: 2345ms
                                   Total file size cleaned
```
