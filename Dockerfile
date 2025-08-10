FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies termasuk tools untuk download
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    build-essential \
    libpq-dev \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY waitress_server.py .
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/static/uploads \
    /app/chroma_db \
    /app/model \
    /app/audios \
    /app/temp && \
    chmod +x /app/bin/linux/rhubarb && \
    echo "Rhubarb status:" && ls -la /app/bin/linux/ && \
    echo "Testing Rhubarb:" && (/app/bin/linux/rhubarb --version 2>/dev/null || echo "Rhubarb binary ready")

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

# Expose port
EXPOSE 5001

# Health check dengan delay yang lebih lama
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:5001/health || exit 1

# Start dengan single worker untuk stability
CMD ["python", "waitress_server.py"]
