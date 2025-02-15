# Use an official Python base image
FROM python:3.10-slim

# Allow statements like RUN apt-get
USER root

# 1. Install OS packages needed for Node.js, Git, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    # Node.js (for `npx prettier` in Task A2) 
    # We'll install it via apt or directly from NodeSource (here we use apt):
    nodejs \
    npm \
    # For building python packages (if needed, e.g. if you have cryptography or pillow)
    build-essential \
    libffi-dev \
    libssl-dev \
    # If you need tesseract-ocr or ffmpeg for optional tasks B8, etc., you can add them here
    # tesseract-ocr \
    # ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 2. Create a working directory inside the container
WORKDIR /app

# 3. Copy your code into the container
# (assuming your Dockerfile is at the project root alongside your 'app/' folder, etc.)
COPY . /app

# 4. Install Python dependencies (from your requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Expose port 8000 for FastAPI
EXPOSE 8000

# 6. By default, run uvicorn on port 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
