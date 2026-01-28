# 🔐 API Authentication Guide

## Overview

ทุก API endpoint ต้องการ authentication token ใน header ของ request

## ⚙️ การตั้งค่า Token

### 1. สร้าง Token

```bash
# วิธีสร้าง token ที่ปลอดภัย
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. เพิ่มใน `.env`

```bash
API_TOKEN=your-secret-token-here
```

**ตอนนี้คือ:** `API_TOKEN=my-secret-token-12345`

**สำหรับ Production:** สร้าง token ใหม่ที่ปลอดภัยกว่า!

---

## 📤 การส่ง Request

### Header ที่ต้องใส่

```
X-API-Token: your-secret-token-here
```

---

## 💻 ตัวอย่าง cURL

### 1. Health Check (ไม่ต้องใช้ token)

```bash
curl http://localhost:8000/health
```

### 2. Extract PDF (ต้องใช้ token)

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@document.pdf"
```

### 3. Structure Text (ต้องใช้ token)

```bash
curl -X POST "http://localhost:8000/llm/structure" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: my-secret-token-12345" \
  -d '{
    "text": "ใบสั่งซื้อ PO-001 บริษัท ABC"
  }'
```

### 4. Complete Pipeline (ต้องใช้ token)

```bash
curl -X POST "http://localhost:8000/pdf/to-structured-json" \
  -H "X-API-Token: my-secret-token-12345" \
  -F "file=@purchase_order.pdf"
```

---

## 🔑 Response Codes

| Code | Message               | Meaning                   |
| ---- | --------------------- | ------------------------- |
| 200  | Success               | Request successful        |
| 401  | Unauthorized          | Token ไม่ถูกต้องหรือไม่มี |
| 400  | Bad Request           | Request format ผิด        |
| 413  | File too large        | ไฟล์ใหญ่เกิน 20MB         |
| 500  | Internal Server Error | Server error              |

---

## ⚠️ Error Examples

### ไม่ส่ง Token

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -F "file=@document.pdf"
```

**Response:**

```json
{
  "detail": "Invalid or missing API token"
}
```

**Status:** 401 Unauthorized

### Token ผิด

```bash
curl -X POST "http://localhost:8000/extract/pdf" \
  -H "X-API-Token: wrong-token" \
  -F "file=@document.pdf"
```

**Response:**

```json
{
  "detail": "Invalid or missing API token"
}
```

**Status:** 401 Unauthorized

---

## 🌐 Integration Examples

### JavaScript/TypeScript

```javascript
const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/pdf/to-structured-json", {
    method: "POST",
    headers: {
      "X-API-Token": "my-secret-token-12345",
    },
    body: formData,
  });

  if (response.status === 401) {
    throw new Error("Invalid API token");
  }

  return await response.json();
};
```

### Python

```python
import requests

url = "http://localhost:8000/pdf/to-structured-json"
headers = {
    "X-API-Token": "my-secret-token-12345"
}
files = {
    "file": open("invoice.pdf", "rb")
}

response = requests.post(url, headers=headers, files=files)

if response.status_code == 401:
    print("Invalid API token!")
else:
    result = response.json()
    print(result)
```

### Postman

1. Method: `POST`
2. URL: `http://localhost:8000/extract/pdf`
3. Headers:
   - Key: `X-API-Token`
   - Value: `my-secret-token-12345`
4. Body:
   - Type: `form-data`
   - Key: `file`
   - Type: `File`
   - Value: (เลือกไฟล์ PDF)

---

## 🚀 Production Deployment

### Railway Environment Variables

เพิ่ม environment variable ใน Railway Dashboard:

```bash
API_TOKEN=your-production-token-here
```

**⚠️ สำคัญ:** ใช้ token ที่ปลอดภัยและเก็บเป็นความลับ!

### Generate Secure Token

```bash
# สร้าง token แบบ secure
python -c "import secrets; print(secrets.token_urlsafe(32))"

# หรือใช้ OpenSSL
openssl rand -base64 32
```

---

## 🔒 Security Best Practices

1. **อย่า hardcode token** ในโค้ด
2. **ใช้ environment variables** เสมอ
3. **สร้าง token ใหม่** สำหรับแต่ละ environment (dev, staging, production)
4. **เก็บ token เป็นความลับ** อย่าแชร์ใน chat หรือ commit ลง Git
5. **ใช้ HTTPS** ใน production (Railway จัดการให้อัตโนมัติ)
6. **Rotate tokens** เป็นระยะๆ

---

## ❓ FAQ

### Q: ถ้าไม่ตั้งค่า API_TOKEN จะเกิดอะไร?

**A:** API จะทำงานแบบไม่มี authentication (development mode) - ไม่แนะนำสำหรับ production

### Q: ส่ง token ใน query string ได้ไหม?

**A:** ไม่ควร! ใช้ header เท่านั้นเพื่อความปลอดภัย

### Q: Token หมดอายุไหม?

**A:** ตอนนี้ไม่หมดอายุ แต่ควร rotate เป็นระยะๆ

### Q: ใช้ token เดียวกันสำหรับทุก client ได้ไหม?

**A:** ได้ แต่ถ้าต้องการแยก client แนะนำให้สร้างระบบ API key management

---

## 📚 เพิ่มเติม

- [API Examples](API_EXAMPLES.md) - ตัวอย่าง curl ทั้งหมด
- [Production Checklist](PRODUCTION_CHECKLIST.md) - Checklist ก่อน deploy
- [Railway Deployment](RAILWAY_DEPLOYMENT.md) - วิธี deploy บน Railway
