# Use an official Python base image
FROM python:3.10-slim

# Allow statements like RUN apt-get
USER root

# 1. Install OS packages needed for Node.js, Git, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    nodejs \
    npm \
    build-essential \
    libffi-dev \
    libssl-dev \
    # If needed for OCR or audio tasks, you can uncomment:
    # tesseract-ocr \
    # ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 2. Create a working directory for your app code
WORKDIR /app

# 3. Copy your project files into /app
COPY . /app

# 4. Create a /data directory for storing generated files
#    (Your code references absolute paths like /data/...)
#    Also make it world-writable if you need to ensure runtime write access.
RUN mkdir -p /data && chmod 777 /data

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Expose port 8000 (FastAPI default)
EXPOSE 8000

# 7. Run your app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
