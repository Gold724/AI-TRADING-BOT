# AI Trading Sentinel - Production Docker Container
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV HEADLESS=true
ENV ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    xvfb \
    supervisor \
    cron \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -s /bin/bash tradebot

# Set up supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Switch to app user
USER tradebot
WORKDIR /home/tradebot/app

# Create virtual environment
RUN python3 -m venv venv
ENV PATH="/home/tradebot/app/venv/bin:$PATH"

# Copy requirements first for better caching
COPY --chown=tradebot:tradebot requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY --chown=tradebot:tradebot . .

# Create necessary directories
RUN mkdir -p logs screenshots data backups

# Set up entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starting AI Trading Sentinel..."\n\
\n\
# Start Xvfb\n\
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &\n\
XVFB_PID=$!\n\
\n\
# Wait for Xvfb to start\n\
sleep 2\n\
\n\
# Function to cleanup on exit\n\
cleanup() {\n\
    echo "🛑 Shutting down..."\n\
    kill $XVFB_PID 2>/dev/null || true\n\
    exit 0\n\
}\n\
\n\
# Set up signal handlers\n\
trap cleanup SIGTERM SIGINT\n\
\n\
# Start the application\n\
exec "$@"' > /home/tradebot/app/entrypoint.sh
RUN chmod +x /home/tradebot/app/entrypoint.sh

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=30s --retries=3 \
    CMD python3 -c "import os; exit(0 if os.path.exists('logs/health.log') else 1)"

# Expose port for monitoring dashboard
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/home/tradebot/app/entrypoint.sh"]
CMD ["python3", "tradebot_sentinel_advanced_pro.py"]