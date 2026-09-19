FROM python:3.11-slim

# libgomp1 for XGBoost; tesseract-ocr for scanned-report OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
ENV PORT=8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
