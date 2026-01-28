# 🚂 Railway Deployment Guide

## Quick Setup

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Thai PDF OCR API"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will auto-detect Dockerfile and deploy

### 3. Configure Environment Variables

Add these in Railway Dashboard → Variables:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# Optional (defaults are fine)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
OPENROUTER_HTTP_REFERER=https://your-app.railway.app
OPENROUTER_APP_TITLE=Thai PDF OCR API

# File Upload
MAX_FILE_SIZE_MB=20

# OCR
TESSERACT_CMD=/usr/bin/tesseract
OCR_DPI=144

# Logging
LOG_LEVEL=INFO
```

### 4. Get Your API URL

Railway will provide a URL like: `https://your-app.railway.app`

### 5. Test Your Deployment

```bash
# Health check
curl https://your-app.railway.app/health

# Upload PDF
curl -X POST "https://your-app.railway.app/pdf/to-structured-json" \
  -F "file=@sample.pdf"
```

---

## Configuration Files

### ✅ Procfile

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### ✅ railway.json

```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### ✅ Dockerfile

- Base image: `python:3.11-slim`
- Includes Tesseract OCR with Thai language
- Health check configured
- Port 8000 exposed

---

## Environment Variables Checklist

| Variable              | Required | Default                      | Description                         |
| --------------------- | -------- | ---------------------------- | ----------------------------------- |
| `OPENROUTER_API_KEY`  | ✅ Yes   | -                            | Get from https://openrouter.ai/keys |
| `OPENROUTER_MODEL`    | ❌ No    | llama-3.3-70b-instruct:free  | LLM model to use                    |
| `OPENROUTER_BASE_URL` | ❌ No    | https://openrouter.ai/api/v1 | API base URL                        |
| `MAX_FILE_SIZE_MB`    | ❌ No    | 20                           | Max upload size                     |
| `LOG_LEVEL`           | ❌ No    | INFO                         | Logging level                       |

---

## Security Best Practices

### ✅ Already Implemented

- [x] No hardcoded API keys
- [x] Environment variables for secrets
- [x] .gitignore includes .env
- [x] CORS configured (needs customization)
- [x] File size limits
- [x] Error handling without exposing internals
- [x] Health checks

### 🔧 Production Recommendations

1. **Update CORS origins** in [app/main.py](app/main.py):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

2. **Add rate limiting** (optional):

```bash
pip install slowapi
```

3. **Monitor with Railway logs**:

```bash
railway logs
```

---

## Troubleshooting

### Deployment fails

- Check Railway build logs
- Verify Dockerfile builds locally: `docker build -t ocr-api .`
- Ensure requirements.txt is complete

### API returns 500 error

- Check `OPENROUTER_API_KEY` is set correctly
- View Railway logs for detailed errors
- Test health endpoint: `/health`

### Tesseract not working

- Ensure `tesseract-ocr-tha` package in Dockerfile
- Check logs for Tesseract initialization

### Large files fail

- Adjust `MAX_FILE_SIZE_MB` environment variable
- Check Railway plan limits

---

## API Documentation

Once deployed, access interactive docs at:

- Swagger UI: `https://your-app.railway.app/docs`
- ReDoc: `https://your-app.railway.app/redoc`

---

## Cost Optimization

### Free Tier Options

- OpenRouter: Free models available (llama-3.3-70b-instruct:free)
- Railway: $5/month credit (sufficient for moderate usage)

### Paid Options

- OpenRouter: Better models (GPT-4, Claude)
- Railway: Scale as needed

---

## Monitoring

### Health Checks

Railway will automatically ping `/health` endpoint

### Custom Monitoring

Add to Railway environment:

```bash
# Optional monitoring service
SENTRY_DSN=your-sentry-dsn
```

---

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure environment variables
3. ✅ Test all endpoints
4. 🔧 Update CORS origins
5. 🔧 Set up custom domain (optional)
6. 📊 Monitor logs and usage

---

**Need Help?**

- Railway Docs: https://docs.railway.app
- OpenRouter Docs: https://openrouter.ai/docs
- Project README: [README.md](README.md)
