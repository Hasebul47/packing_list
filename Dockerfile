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

EXPOSE 8002

# Streamlit healthcheck (optional but handy)
HEALTHCHECK CMD curl --fail http://localhost:8002/_stcore/health || exit 1

# Streamlit needs these flags to run correctly inside a container
ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8002", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
