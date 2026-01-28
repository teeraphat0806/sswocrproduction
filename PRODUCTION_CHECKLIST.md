# 🚀 Production Deployment Checklist

## ✅ Pre-Deployment Checklist

### Security

- [x] No API keys in code
- [x] `.env` in `.gitignore`
- [x] CORS configured (needs customization for production)
- [x] Error handling without exposing internals
- [x] File size limits enforced
- [x] Input validation with Pydantic

### Configuration

- [x] Environment variables ready
- [x] Dockerfile optimized
- [x] Health checks configured
- [x] Logging configured
- [x] PORT environment variable support

### Testing

- [ ] Test all endpoints locally
- [ ] Test with sample PDF files
- [ ] Test error scenarios
- [ ] Verify LLM integration works

### Documentation

- [x] README.md complete
- [x] API examples ready
- [x] Railway deployment guide
- [x] Environment variables documented

---

## 🔧 Before Pushing to Railway

### 1. Update CORS (Important!)

Edit [app/main.py](app/main.py#L29):

```python
# For production, set ALLOWED_ORIGINS environment variable:
# ALLOWED_ORIGINS=https://yourfrontend.com,https://app.yourfrontend.com
```

### 2. Verify .gitignore

Make sure these are ignored:

```
.env
venv/
*.pdf
*.log
__pycache__/
```

### 3. Test Locally

```bash
# Build Docker image
docker build -t thai-ocr-api .

# Run container
docker run -p 8000:8000 --env-file .env thai-ocr-api

# Test endpoints
curl http://localhost:8000/health
```

---

## 📦 Railway Deployment Steps

### Step 1: Prepare Git Repository

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Production-ready Thai PDF OCR API"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/thai-ocr-api.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway auto-detects Dockerfile

### Step 3: Configure Environment Variables

In Railway Dashboard → Variables, add:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-actual-key

# Recommended
ALLOWED_ORIGINS=https://your-frontend-domain.com
LOG_LEVEL=INFO
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Optional
MAX_FILE_SIZE_MB=20
```

### Step 4: Get Your URL

Railway provides: `https://your-app-name.up.railway.app`

### Step 5: Test Production

```bash
# Health check
curl https://your-app-name.up.railway.app/health

# Upload test
curl -X POST "https://your-app-name.up.railway.app/pdf/to-structured-json" \
  -F "file=@test.pdf"
```

---

## 🔍 Post-Deployment Verification

### Critical Tests

```bash
# 1. Health check
curl https://your-app.railway.app/health
# Expected: {"status":"healthy","version":"2.0.0","checks":{"api":"ok","openrouter_configured":true}}

# 2. Root endpoint
curl https://your-app.railway.app/
# Expected: {"status":"healthy","service":"Thai PDF OCR API","version":"2.0.0"}

# 3. API documentation
# Visit: https://your-app.railway.app/docs

# 4. PDF extraction (without LLM)
curl -X POST "https://your-app.railway.app/extract/pdf" \
  -F "file=@sample.pdf"

# 5. Full pipeline (with LLM)
curl -X POST "https://your-app.railway.app/pdf/to-structured-json" \
  -F "file=@purchase_order.pdf"
```

---

## 🐛 Troubleshooting

### Deployment Fails

**Check Railway logs:**

```bash
railway logs
```

**Common issues:**

- Missing Dockerfile → ✅ Already created
- Build timeout → Optimize Dockerfile layers
- Port binding → ✅ Using $PORT variable

### API Returns 500

**Check environment variables:**

- `OPENROUTER_API_KEY` set correctly?
- No spaces or quotes in values

**View logs:**

```bash
railway logs --tail
```

### LLM Not Working

**Verify:**

- API key is valid
- Model name is correct
- OpenRouter has credits/quota

### CORS Errors

**Update:**

```bash
# In Railway dashboard
ALLOWED_ORIGINS=https://your-actual-domain.com
```

---

## 📊 Monitoring

### Railway Metrics

- View in Railway Dashboard
- CPU, Memory, Network usage
- Request logs

### Health Endpoint

```bash
curl https://your-app.railway.app/health
```

Should return:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "checks": {
    "api": "ok",
    "openrouter_configured": true
  }
}
```

---

## 💰 Cost Considerations

### Railway

- Free tier: $5/month credit
- Scales automatically
- Pay for usage beyond free tier

### OpenRouter

- Free models available (llama-3.3-70b)
- Paid models for better quality
- Monitor usage in OpenRouter dashboard

---

## 🔐 Security Best Practices

### ✅ Implemented

- Environment-based configuration
- No hardcoded secrets
- CORS with configurable origins
- File size limits
- Input validation
- Error handling

### 🎯 Recommended

- [ ] Add rate limiting (slowapi)
- [ ] Set up monitoring (Sentry)
- [ ] Configure specific CORS origins
- [ ] Enable HTTPS only (Railway default)
- [ ] Add authentication if needed

---

## 📱 Integration Examples

### Frontend Integration

```javascript
// React/Next.js example
const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    "https://your-app.railway.app/pdf/to-structured-json",
    {
      method: "POST",
      body: formData,
    },
  );

  const data = await response.json();
  return data;
};
```

### Python Client

```python
import requests

url = "https://your-app.railway.app/pdf/to-structured-json"
files = {"file": open("invoice.pdf", "rb")}
response = requests.post(url, files=files)
result = response.json()
```

---

## 🎓 Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure environment variables
3. ✅ Test all endpoints
4. 🔧 Customize CORS for your frontend
5. 📊 Monitor logs and usage
6. 🚀 Integrate with your application
7. 📈 Scale as needed

---

**Need help?**

- Railway Docs: https://docs.railway.app
- OpenRouter Docs: https://openrouter.ai/docs
- Project README: [README.md](README.md)
- Deployment Guide: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
