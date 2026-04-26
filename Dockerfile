# Use official Python 3.12 slim image to minimize vulnerability footprint and storage costs
FROM python:3.12-slim

# Prevent memory page faults in Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install essential system dependencies required for C-bindings (PyTorch/Pandas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Upgrade pip securely
RUN pip install --no-cache-dir --upgrade pip

# Install requirements before copying core logic (allows Docker to cache this heavy layer)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend logic
COPY . /app/

# Port exposure
EXPOSE 5000

# Gunicorn ensures FastAPI handles multiple concurrent threads robustly in production
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000", "backend_api:app"]
