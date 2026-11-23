# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for PDF processing and OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-tha \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install CPU-only PyTorch first (reduces image size and avoids unused CUDA libs), then project dependencies
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR models (Thai and English) to cache them in the Docker image
RUN python -c "import easyocr; easyocr.Reader(['th', 'en'], gpu=False)"

# Copy application code
COPY . .

# Create temp directory for file processing
RUN mkdir -p /tmp/uploads && chmod 777 /tmp/uploads

# Expose port
EXPOSE 8000

# Run the application directly with Python
CMD ["python", "-m", "app.main"]
