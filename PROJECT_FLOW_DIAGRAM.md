# Thai PDF OCR API - Current Flow Diagram (Mermaid Code)

## Endpoint: POST /pdf/to-structured-json (Main Pipeline)

````mermaid
flowchart TD
    Start([เริ่ม]) --> Upload["📤 Upload PDF File<br/>ผ่าน API Request"]

    Upload --> Validate["✅ Validate File<br/>- Size limit: 20MB<br/>- Extension: .pdf<br/>- Content-Type check"]

    Validate -->|Error| Error1["❌ HTTP 400/413<br/>Invalid file"]
    Error1 --> End1([สิ้นสุด])

    Validate -->|OK| SaveTemp["💾 Save Temp File<br/>ใน /tmp directory"]

    SaveTemp --> Extract["🔍 PDFExtractor.extract()"]

    Extract --> TryText["📄 Step 1: Text Extraction<br/>ลอง pypdf.PdfReader<br/>Extract page by page"]

    TryText --> CheckQuality["⚖️ Quality Check<br/>- ความยาว >= 10 chars<br/>- Thai ratio >= 10%"]

    CheckQuality -->|Valid Text| UsePDF["✅ ใช้ PDF Text Method<br/>method='pdf_text'"]

    CheckQuality -->|Invalid| FallbackOCR["🔄 Fallback to OCR<br/>Text ไม่พอให้ใช้ OCR"]

    FallbackOCR --> OCRProcess["🤖 OCR Processing<br/>- fitz render page to image<br/>- pytesseract + Thai lang<br/>- 2x zoom = 144 DPI"]

    OCRProcess --> UseTess["✅ ใช้ OCR Method<br/>method='ocr'"]

    UsePDF --> CombineText["📝 Combine Text<br/>text + pages list<br/>page_count"]

    UseTess --> CombineText

    CombineText --> BuildPrompt["🎨 Build LLM Prompt<br/>TextStructurer.build_prompt()"]

    BuildPrompt --> PromptDetail["📋 Prompt Format<br/>System: Schema definition<br/>+ Thai PO rules<br/>+ Company exclusion list<br/>User: Raw text"]

    PromptDetail --> CallLLM["🔗 Call OpenRouter API<br/>OpenRouterClient.call_openrouter()"]

    CallLLM --> LLMConfig["⚙️ LLM Configuration<br/>Model: gpt-4o-mini (default)<br/>Temp: 0.0<br/>Timeout: 60s"]

    LLMConfig --> LLMCall["📤 HTTP POST to OpenRouter<br/>Headers: Auth + Referer<br/>Body: messages + model"]

    LLMCall -->|No Response| Fallback["🔄 Try Fallback Models<br/>gpt-3.5-turbo<br/>claude-3-haiku<br/>gemini-pro"]

    Fallback -->|Success| LLMResp["📥 LLM Response<br/>Raw JSON string"]

    Fallback -->|Fail| Error2["❌ HTTP 502/504<br/>LLM Service Error"]

    Error2 --> Cleanup["🧹 Cleanup Temp"]
    Cleanup --> End2([สิ้นสุด])

    LLMCall -->|Success| LLMResp

    LLMResp --> ParseJSON["🔍 Parse JSON<br/>TextStructurer.parse_and_validate()"]

    ParseJSON --> CleanMarkdown["🧹 Clean Markdown Fence<br/>Remove ``` if present"]

    CleanMarkdown --> JSONParse["📦 JSON Parse<br/>json.loads()"]

    JSONParse -->|Parse Error| Error3["❌ HTTP 502<br/>Invalid JSON from LLM"]
    Error3 --> Cleanup

    JSONParse -->|Success| Validate2["✔️ Pydantic Validation<br/>OCRPOResult schema"]

    Validate2 -->|Validation Error| Error4["❌ HTTP 422<br/>Schema Mismatch"]
    Error4 --> Cleanup

    Validate2 -->|Success| Response["✅ Build Success Response<br/>PDFToStructuredResponse"]

    Response --> ResponseData["📊 Response Data<br/>- ocr: extraction metadata<br/>- result: structured PO<br/>- processing_time_ms"]

    ResponseData --> ReturnJSON["📤 Return JSON<br/>HTTP 200"]

    ReturnJSON --> Cleanup
    Cleanup --> End3([สิ้นสุด])

    style Start fill:#90EE90
    style End1 fill:#FFB6C6
    style End2 fill:#FFB6C6
    style End3 fill:#90EE90
    style Error1 fill:#FFB6C6
    style Error2 fill:#FFB6C6
    style Error3 fill:#FFB6C6
    style Error4 fill:#FFB6C6
    style UsePDF fill:#87CEEB
    style UseTess fill:#87CEEB
    style Response fill:#DDA0DD
    style ReturnJSON fill:#DDA0DD
````

---

## Detailed: Text Extraction Decision Logic

```mermaid
flowchart TD
    A["PDF File<br/>passed validation"] --> B["PDFExtractor._extract_text()"]
    B --> C["pypdf.PdfReader"]
    C --> D["Extract each page"]
    D --> E{"Combine text<br/>length?"}
    E -->|< 10 chars| F["Invalid text"]
    E -->|>= 10 chars| G["Count Thai characters<br/>U+0E00 to U+0E7F"]
    G --> H{"Thai ratio<br/>>= 10%?"}
    H -->|No| F
    H -->|Yes| I["✅ TEXT EXTRACTION<br/>Use pdf_text method"]
    F --> J["PDFExtractor._extract_with_ocr()"]
    J --> K["fitz.open PDF"]
    K --> L["Loop each page"]
    L --> M["Render to image<br/>2x zoom = 144 DPI"]
    M --> N["pytesseract.image_to_string<br/>lang: tha+eng"]
    N --> O["✅ OCR<br/>Use ocr method"]
    I --> P["Return extracted text"]
    O --> P

    style I fill:#87CEEB
    style O fill:#87CEEB
    style P fill:#90EE90
```

---

## API Response Structure

```mermaid
flowchart LR
    A["PDFToStructuredResponse<br/>{"]
    A --> B["ocr: {<br/>  page_count: int<br/>  extraction_method: str<br/>  text_length: int<br/>}"]
    A --> C["result: OCRPOResult {<br/>  header: POHeader<br/>  items: List[POItem]<br/>  meta: POMeta<br/>}"]
    A --> D["processing_time_ms: int<br/>}"]

    B --> E["📊 Extraction Info"]
    C --> F["🎯 Structured PO Data"]

    style A fill:#E6F3FF
    style B fill:#FFF9E6
    style C fill:#F0E6FF
    style D fill:#E6FFE6
    style E fill:#FFF9E6
    style F fill:#F0E6FF
```

---

## Service Layer Architecture

```mermaid
graph TB
    API["🔗 API Routes<br/>app/api/routes.py"]

    API -->|calls| EXT["🔍 PDFExtractor<br/>app/services/extractor.py<br/>- _extract_text<br/>- _extract_with_ocr<br/>- _is_valid_extraction"]

    API -->|calls| STR["📝 TextStructurer<br/>app/services/structurer.py<br/>- build_prompt<br/>- parse_and_validate<br/>- structure_text"]

    API -->|calls| OR["🤖 OpenRouterClient<br/>app/services/openrouter_client.py<br/>- call_openrouter<br/>- fallback model logic"]

    EXT -->|uses| PYPDF["📦 pypdf"]
    EXT -->|uses| FITZ["📦 PyMuPDF"]
    EXT -->|uses| TESS["📦 pytesseract"]

    STR -->|validates| PYDANTIC["📦 Pydantic<br/>app/models/po_schemas.py"]
    STR -->|uses| PROMPT["📋 Schema Definition"]

    OR -->|HTTP calls| OPENROUTER["🌐 OpenRouter API<br/>https://openrouter.ai/api/v1"]

    API -->|uses| AUTH["🔐 verify_token<br/>app/utils/auth.py"]
    API -->|uses| FILES["📂 File utilities<br/>app/utils/files.py"]

    style API fill:#E3F2FD
    style EXT fill:#FFF3E0
    style STR fill:#F3E5F5
    style OR fill:#E8F5E9
    style PYDANTIC fill:#FDEEF4
    style OPENROUTER fill:#E1F5FE
```

---

## Authentication & Validation Flow

```mermaid
flowchart TD
    REQ["📨 HTTP Request<br/>POST /pdf/to-structured-json"]

    REQ --> AUTH["🔐 Verify Token<br/>verify_token dependency"]

    AUTH --> HASTOKEN{"X-API-Token<br/>header?"}

    HASTOKEN -->|No| NOTOKEN["❌ HTTP 401<br/>Missing token"]
    NOTOKEN --> END1([Reject])

    HASTOKEN -->|Yes| CHECKTOKEN{"Token<br/>matches?"}

    CHECKTOKEN -->|No| BADTOKEN["❌ HTTP 401<br/>Invalid token"]
    BADTOKEN --> END1

    CHECKTOKEN -->|Yes| FILEUPLOAD["📁 File Upload<br/>validate_pdf_file()"]

    FILEUPLOAD --> CHECKEXT{".pdf<br/>extension?"}
    CHECKEXT -->|No| BADEXT["❌ HTTP 400<br/>Invalid extension"]
    BADEXT --> END1

    CHECKEXT -->|Yes| CHECKSIZE{"Size<br/><= 20MB?"}

    CHECKSIZE -->|No| BIGFILE["❌ HTTP 413<br/>File too large"]
    BIGFILE --> END1

    CHECKSIZE -->|Yes| PROCEED["✅ Proceed<br/>to extraction"]
    PROCEED --> END2([Process])

    style REQ fill:#E3F2FD
    style AUTH fill:#F3E5F5
    style NOTOKEN fill:#FFB6C6
    style BADTOKEN fill:#FFB6C6
    style BADEXT fill:#FFB6C6
    style BIGFILE fill:#FFB6C6
    style PROCEED fill:#90EE90
```

---

## Data Flow: From OCR Text to Structured PO

```mermaid
flowchart LR
    A["🔤 Raw OCR Text<br/>ใบสั่งซื้อ<br/>PO-001<br/>บริษัท ABC<br/>SS400: 12x100x2000"]

    B["📋 System Prompt<br/>- Schema definition<br/>- Thai rules<br/>- Shape logic<br/>- Company exclusion"]

    C["👤 User Prompt<br/>Text + schema"]

    D["🤖 LLM Processing<br/>OpenRouter"]

    E["📦 JSON Output<br/>{<br/>  header: {...}<br/>  items: [{...}]<br/>  meta: {...}<br/>}"]

    F["✔️ Validation<br/>OCRPOResult"]

    G["✅ Success<br/>or<br/>❌ Error"]

    A --> B
    B --> C
    A --> C
    C --> D
    D --> E
    E --> F
    F --> G

    style A fill:#FFFACD
    style B fill:#DDA0DD
    style C fill:#DDA0DD
    style D fill:#87CEEB
    style E fill:#FFE5B4
    style F fill:#F0E68C
    style G fill:#98FB98
```
