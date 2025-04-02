FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for better caching
COPY requirements.txt .

# Create pip cache directory
ENV PIP_CACHE_DIR=/pip-cache

# Install Python dependencies with caching
RUN --mount=type=cache,target=/pip-cache \
    pip install --cache-dir=/pip-cache --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create healthcheck endpoint
RUN echo 'from fastapi import FastAPI, APIRouter\nrouter = APIRouter()\n@router.get("/health")\ndef health_check():\n    return {"status": "ok"}' > src/api/health.py
RUN echo 'from .main import app\nfrom .health import router\napp.include_router(router)' >> src/api/__init__.py

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]