# AI Trading Sentinel - Bulenox Trade Execution System
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libgconf-2-4 \
    libxss1 \
    libnss3 \
    libnspr4 \
    libasound2 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs/screenshots data/accounts data/signals

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BULENOX_PROFILE_PATH="/app/chrome_profiles" \
    BULENOX_PROFILE_NAME="Profile 13" \
    PORT=5000 \
    FLASK_RUN_HOST=0.0.0.0 \
    USE_BULENOX=true \
    AUTO_LOGIN=true \
    DISPLAY=:99

# Create Chrome profiles directory
RUN mkdir -p /app/chrome_profiles

# Expose port
EXPOSE 5000

# Set entrypoint script
COPY trae.sh /app/trae.sh
RUN chmod +x /app/trae.sh

# Run the application
CMD ["/app/trae.sh"]