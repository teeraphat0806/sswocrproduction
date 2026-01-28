# 📘 API Usage Guide - ocrapi.sswsteelcenter.com

## 🔑 Authentication

**Required Header** (ยกเว้น `/` และ `/health`):

```
X-API-Token: my-secret-token-12345
```

---

## 📋 API Endpoints

1. [GET /](#1-get---root-endpoint)
2. [GET /health](#2-get-health---health-check)
3. [POST /extract/pdf](#3-post-extractpdf---extract-text-from-pdf)
4. [POST /llm/structure](#4-post-llmstructure---structure-text-with-llm)
5. [POST /pdf/to-structured-json](#5-post-pdfto-structured-json---complete-pipeline)

---

## 1. GET / - Root Endpoint

**คำอธิบาย:** เช็คสถานะ API เบื้องต้น

### cURL

```bash
curl https://ocrapi.sswsteelcenter.com/
```

### Next.js Fetch

```typescript
// app/api/check-status/route.ts
export async function GET() {
  try {
    const response = await fetch("https://ocrapi.sswsteelcenter.com/", {
      method: "GET",
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Error:", error);
    return Response.json({ error: "Failed to fetch" }, { status: 500 });
  }
}
```

### Client Component (Next.js)

```typescript
'use client';

import { useState, useEffect } from 'react';

export default function StatusCheck() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://ocrapi.sswsteelcenter.com/')
      .then(res => res.json())
      .then(data => {
        setStatus(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error:', error);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>API Status</h2>
      <pre>{JSON.stringify(status, null, 2)}</pre>
    </div>
  );
}
```

---

## 2. GET /health - Health Check

**คำอธิบาย:** เช็คสถานะ API แบบละเอียด

### cURL

```bash
curl https://ocrapi.sswsteelcenter.com/health
```

### Next.js Server Action

```typescript
// app/actions/health.ts
"use server";

export async function checkHealth() {
  try {
    const response = await fetch("https://ocrapi.sswsteelcenter.com/health", {
      method: "GET",
      cache: "no-store",
    });

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: "Health check failed" };
  }
}
```

### Usage in Component

```typescript
'use client';

import { checkHealth } from '@/app/actions/health';
import { useState } from 'react';

export default function HealthCheck() {
  const [result, setResult] = useState<any>(null);

  const handleCheck = async () => {
    const health = await checkHealth();
    setResult(health);
  };

  return (
    <div>
      <button onClick={handleCheck}>Check Health</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

---

## 3. POST /extract/pdf - Extract Text from PDF

**คำอธิบาย:** อัปโหลด PDF และแยกข้อความภาษาไทย

**Authentication:** Required ✅

### cURL

```bash
# Basic
curl -X POST "https://ocrapi.sswsteelcenter.com/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@document.pdf"

# Save to file
curl -X POST "https://ocrapi.sswsteelcenter.com/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@invoice.pdf" \
  -o result.json

# With pretty print
curl -s -X POST "https://ocrapi.sswsteelcenter.com/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@doc.pdf" | python -m json.tool
```

### Next.js API Route

```typescript
// app/api/extract-pdf/route.ts
export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return Response.json({ error: "No file provided" }, { status: 400 });
    }

    // Forward to OCR API
    const ocrFormData = new FormData();
    ocrFormData.append("file", file);

    const response = await fetch(
      "https://ocrapi.sswsteelcenter.com/extract/pdf",
      {
        method: "POST",
        headers: {
          "X-API-Token": "my-secret-token-12345",
        },
        body: ocrFormData,
      },
    );

    if (!response.ok) {
      const error = await response.json();
      return Response.json(error, { status: response.status });
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Error:", error);
    return Response.json({ error: "Extraction failed" }, { status: 500 });
  }
}
```

### Client Component with File Upload

```typescript
'use client';

import { useState } from 'react';

export default function PDFExtractor() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('https://ocrapi.sswsteelcenter.com/extract/pdf', {
        method: 'POST',
        headers: {
          'X-API-Token': 'my-secret-token-12345'
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to extract PDF');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">PDF Text Extraction</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm"
        />

        <button
          type="submit"
          disabled={!file || loading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Extract Text'}
        </button>
      </form>

      {result && (
        <div className="mt-6 p-4 bg-gray-100 rounded">
          <h2 className="font-bold mb-2">Extracted Text:</h2>
          <pre className="whitespace-pre-wrap text-sm">{result.text}</pre>

          <div className="mt-4 text-sm text-gray-600">
            <p>Pages: {result.meta.page_count}</p>
            <p>Method: {result.meta.extraction_method}</p>
            <p>Time: {result.meta.processing_time_ms}ms</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 4. POST /llm/structure - Structure Text with LLM

**คำอธิบาย:** ส่งข้อความให้ LLM แปลงเป็น JSON

**Authentication:** Required ✅

### cURL

```bash
# Basic
curl -X POST "https://ocrapi.sswsteelcenter.com/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{
    "text": "ใบสั่งซื้อ\nเลขที่: PO-001\nวันที่: 27/01/2026\nบริษัท ABC Steel จำกัด"
  }'

# Without raw text
curl -X POST "https://ocrapi.sswsteelcenter.com/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{
    "text": "PO-001 บริษัท ABC",
    "include_raw_text": false
  }'
```

### Next.js Server Action

```typescript
// app/actions/structure.ts
"use server";

interface StructureRequest {
  text: string;
  include_raw_text?: boolean;
}

export async function structureText(request: StructureRequest) {
  try {
    const response = await fetch(
      "https://ocrapi.sswsteelcenter.com/llm/structure",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Token": "my-secret-token-12345",
        },
        body: JSON.stringify(request),
      },
    );

    if (!response.ok) {
      const error = await response.json();
      return { success: false, error };
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: "Failed to structure text" };
  }
}
```

### Client Component

```typescript
'use client';

import { structureText } from '@/app/actions/structure';
import { useState } from 'react';

export default function TextStructurer() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const response = await structureText({ text });

    if (response.success) {
      setResult(response.data);
    } else {
      alert('Failed to structure text');
    }

    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Text to Structured JSON</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="วางข้อความที่ต้องการแปลง..."
          rows={10}
          className="w-full p-3 border rounded"
        />

        <button
          type="submit"
          disabled={!text || loading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Structure Text'}
        </button>
      </form>

      {result && (
        <div className="mt-6 p-4 bg-gray-100 rounded">
          <h2 className="font-bold mb-2">Structured Data:</h2>
          <pre className="text-xs overflow-auto">
            {JSON.stringify(result.result, null, 2)}
          </pre>
          <p className="mt-2 text-sm text-gray-600">
            Processing time: {result.processing_time_ms}ms
          </p>
        </div>
      )}
    </div>
  );
}
```

---

## 5. POST /pdf/to-structured-json - Complete Pipeline ⭐

**คำอธิบาย:** อัปโหลด PDF → แยกข้อความ → แปลงเป็น JSON (ทำทั้งหมดในครั้งเดียว)

**Authentication:** Required ✅

### cURL

```bash
# Basic
curl -X POST "https://ocrapi.sswsteelcenter.com/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@purchase_order.pdf"

# Without raw text
curl -X POST "https://ocrapi.sswsteelcenter.com/pdf/to-structured-json?include_raw_text=false" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@document.pdf"

# Save to file
curl -X POST "https://ocrapi.sswsteelcenter.com/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@invoice.pdf" \
  -o structured_result.json

# Process multiple files
for file in *.pdf; do
  curl -X POST "https://ocrapi.sswsteelcenter.com/pdf/to-structured-json" \
    -H "X-API-Token: my-secret-token-12345" \
    -F "file=@$file" \
    -o "${file%.pdf}_result.json"
done
```

### Next.js API Route (Recommended)

```typescript
// app/api/process-pdf/route.ts
export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File;
    const includeRawText = formData.get("include_raw_text") === "true";

    if (!file) {
      return Response.json({ error: "No file provided" }, { status: 400 });
    }

    // Validate file type
    if (!file.name.endsWith(".pdf")) {
      return Response.json(
        { error: "Only PDF files are allowed" },
        { status: 400 },
      );
    }

    // Validate file size (max 20MB)
    if (file.size > 20 * 1024 * 1024) {
      return Response.json(
        { error: "File too large (max 20MB)" },
        { status: 413 },
      );
    }

    // Forward to OCR API
    const ocrFormData = new FormData();
    ocrFormData.append("file", file);

    const url = `https://ocrapi.sswsteelcenter.com/pdf/to-structured-json?include_raw_text=${includeRawText}`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "X-API-Token": process.env.OCR_API_TOKEN || "my-secret-token-12345",
      },
      body: ocrFormData,
    });

    if (!response.ok) {
      const error = await response.json();
      return Response.json(error, { status: response.status });
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Error:", error);
    return Response.json({ error: "Processing failed" }, { status: 500 });
  }
}
```

### Complete Client Component

```typescript
'use client';

import { useState } from 'react';

interface POResult {
  ocr: {
    page_count: number;
    extraction_method: string;
    text_length: number;
  };
  result: {
    header: {
      poNumber: string;
      poDate: string;
      customer: {
        name: string;
        tel: string;
        address: string;
      };
    };
    items: Array<{
      codeSteel: string;
      description: string;
      thickness: number;
      width: number;
      length: number;
      quantity: number;
    }>;
    meta: {
      confidence: number;
      warnings: string[];
    };
  };
  processing_time_ms: number;
}

export default function CompletePDFProcessor() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<POResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('https://ocrapi.sswsteelcenter.com/pdf/to-structured-json', {
        method: 'POST',
        headers: {
          'X-API-Token': 'my-secret-token-12345'
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Processing failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Thai PDF OCR - Complete Pipeline</h1>

      <form onSubmit={handleSubmit} className="mb-8 space-y-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {file && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={!file || loading}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700 transition"
        >
          {loading ? 'Processing PDF...' : 'Process PDF to JSON'}
        </button>
      </form>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">Error:</p>
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">Processing your PDF...</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6">
          {/* OCR Info */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h2 className="font-bold text-lg mb-2">OCR Information</h2>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Pages</p>
                <p className="font-medium">{result.ocr.page_count}</p>
              </div>
              <div>
                <p className="text-gray-600">Method</p>
                <p className="font-medium">{result.ocr.extraction_method}</p>
              </div>
              <div>
                <p className="text-gray-600">Processing Time</p>
                <p className="font-medium">{result.processing_time_ms}ms</p>
              </div>
            </div>
          </div>

          {/* Header Info */}
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="font-bold text-xl mb-4">Purchase Order Details</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-600 text-sm">PO Number</p>
                <p className="font-medium">{result.result.header.poNumber}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Date</p>
                <p className="font-medium">{result.result.header.poDate}</p>
              </div>
            </div>

            <div className="mt-4 p-4 bg-white rounded">
              <p className="font-medium mb-2">{result.result.header.customer.name}</p>
              <p className="text-sm text-gray-600">{result.result.header.customer.address}</p>
              <p className="text-sm text-gray-600 mt-1">Tel: {result.result.header.customer.tel}</p>
            </div>
          </div>

          {/* Items */}
          <div className="bg-white border rounded-lg overflow-hidden">
            <h2 className="font-bold text-xl p-4 bg-gray-50 border-b">Items ({result.result.items.length})</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left">Code</th>
                    <th className="px-4 py-3 text-left">Description</th>
                    <th className="px-4 py-3 text-right">Thickness</th>
                    <th className="px-4 py-3 text-right">Width</th>
                    <th className="px-4 py-3 text-right">Length</th>
                    <th className="px-4 py-3 text-right">Qty</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {result.result.items.map((item, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{item.codeSteel}</td>
                      <td className="px-4 py-3">{item.description}</td>
                      <td className="px-4 py-3 text-right">{item.thickness}</td>
                      <td className="px-4 py-3 text-right">{item.width}</td>
                      <td className="px-4 py-3 text-right">{item.length}</td>
                      <td className="px-4 py-3 text-right font-medium">{item.quantity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Meta Info */}
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="font-bold mb-2">Confidence & Warnings</h3>
            <p className="text-sm">Overall Confidence: {(result.result.meta.confidence * 100).toFixed(1)}%</p>
            {result.result.meta.warnings.length > 0 && (
              <div className="mt-2">
                <p className="text-sm font-medium">Warnings:</p>
                <ul className="list-disc list-inside text-sm text-gray-700">
                  {result.result.meta.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Raw JSON */}
          <details className="bg-gray-100 p-4 rounded-lg">
            <summary className="cursor-pointer font-medium">View Raw JSON</summary>
            <pre className="mt-4 text-xs overflow-auto bg-white p-4 rounded">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
```

---

## 🔒 Environment Variables (Next.js)

สร้างไฟล์ `.env.local`:

```bash
# OCR API Configuration
OCR_API_URL=https://ocrapi.sswsteelcenter.com
OCR_API_TOKEN=my-secret-token-12345
```

### ใช้ใน code:

```typescript
const API_URL = process.env.OCR_API_URL || "https://ocrapi.sswsteelcenter.com";
const API_TOKEN = process.env.OCR_API_TOKEN || "my-secret-token-12345";

fetch(`${API_URL}/extract/pdf`, {
  headers: {
    "X-API-Token": API_TOKEN,
  },
  // ...
});
```

---

## 🎯 Quick Start Template

### Next.js App Router Structure

```
app/
├── api/
│   ├── extract-pdf/
│   │   └── route.ts
│   ├── structure/
│   │   └── route.ts
│   └── process-pdf/
│       └── route.ts
├── actions/
│   ├── health.ts
│   └── structure.ts
├── components/
│   ├── PDFExtractor.tsx
│   ├── TextStructurer.tsx
│   └── CompletePipeline.tsx
└── page.tsx
```

---

## 📚 Response Schemas

### ExtractionResponse

```typescript
interface ExtractionResponse {
  text: string;
  pages: string[];
  meta: {
    page_count: number;
    extraction_method: "pdf_text" | "ocr";
    processing_time_ms: number;
  };
}
```

### StructureResponse

```typescript
interface StructureResponse {
  result: {
    header: POHeader;
    items: POItem[];
    meta: POMeta;
  };
  processing_time_ms: number;
}
```

### PDFToStructuredResponse

```typescript
interface PDFToStructuredResponse {
  ocr: {
    page_count: number;
    extraction_method: string;
    text_length: number;
  };
  result: {
    header: POHeader;
    items: POItem[];
    meta: POMeta;
  };
  processing_time_ms: number;
}
```

---

## ⚠️ Error Handling

### Common Errors

| Status | Error            | Solution                    |
| ------ | ---------------- | --------------------------- |
| 401    | Unauthorized     | เช็ค X-API-Token header     |
| 400    | Bad Request      | เช็ค file format (PDF only) |
| 413    | File Too Large   | ไฟล์ต้อง < 20MB             |
| 422    | Validation Error | เช็ค request body schema    |
| 502    | LLM Error        | LLM service ไม่ available   |
| 500    | Internal Error   | ติดต่อ admin                |

### Error Response Example

```json
{
  "detail": "Invalid or missing API token"
}
```

---

## 🚀 Production Tips

1. **Use environment variables** สำหรับ API token
2. **Implement retry logic** สำหรับ network errors
3. **Add loading states** ให้ user experience ดี
4. **Validate files** ก่อนส่งไป API
5. **Cache results** ถ้าเหมาะสม
6. **Monitor API usage** ด้วย logging

---

**Base URL:** https://ocrapi.sswsteelcenter.com  
**API Token:** `my-secret-token-12345`  
**Max File Size:** 20MB  
**Supported Format:** PDF only
