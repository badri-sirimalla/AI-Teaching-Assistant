FROM python:3.11-slim

# Install FFmpeg required for video/audio processing
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY . .

# Render provides the PORT environment variable
CMD gunicorn app:app --bind 0.0.0.0:$PORT