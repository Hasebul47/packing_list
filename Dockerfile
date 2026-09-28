FROM python:3.11-slim

# System deps some PDF/imaging wheels need at runtime  
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8002

# Streamlit healthcheck
HEALTHCHECK CMD curl --fail -k https://localhost:8002/packing-list/_stcore/health || curl --fail http://localhost:8002/packing-list/_stcore/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
