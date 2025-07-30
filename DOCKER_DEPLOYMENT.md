# 🐳 AI Trading Sentinel - Docker Deployment Guide

This guide provides instructions for deploying the AI Trading Sentinel using Docker containers, making it portable and easy to deploy across different environments.

## 📋 Prerequisites

- Docker installed on your system ([Get Docker](https://docs.docker.com/get-docker/))
- Git to clone the repository (if not already done)
- Basic understanding of Docker commands

## 🚀 Quick Start

### Building and Running with Docker

```bash
# Build the Docker image
docker build -t sentinel-bot -f Dockerfile.sentinel .

# Run the bot container
docker run -d --name sentinel-runner -p 5000:5000 sentinel-bot
```

### Using Docker Compose (Recommended)

```bash
# Start the container with Docker Compose
docker-compose -f docker-compose.sentinel.yml up -d

# View logs
docker logs -f sentinel-runner

# Stop the container
docker-compose -f docker-compose.sentinel.yml down
```

## ⚙️ Configuration

### Environment Variables

Before running the container, create a `.env` file based on the provided `.env.example`:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your credentials
nano .env  # or use any text editor
```

Key environment variables to configure:

- `BULENOX_USERNAME` - Your Bulenox username
- `BULENOX_PASSWORD` - Your Bulenox password
- `BULENOX_ACCOUNT_ID` - Your Bulenox account ID
- `HEADLESS` - Set to "true" for headless browser mode (recommended for servers)
- `SCREENSHOT_ON_FAILURE` - Set to "true" to capture screenshots on errors

### Passing Environment Variables at Runtime

You can also pass environment variables directly when running the container:

```bash
docker run -d --name sentinel-runner \
  -p 5000:5000 \
  -e BULENOX_USERNAME=your_username \
  -e BULENOX_PASSWORD=your_password \
  -e BULENOX_ACCOUNT_ID=your_account_id \
  sentinel-bot
```

## 📁 Volume Mounts

The Docker setup includes volume mounts for:

1. **Logs**: Persists log files to your host system
2. **Environment Variables**: Mounts your `.env` file into the container
3. **Chrome Profile**: Persists Chrome profile data between container restarts

```bash
docker run -d --name sentinel-runner \
  -p 5000:5000 \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/.env:/app/.env" \
  -v "$(pwd)/temp_chrome_profile:/app/temp_chrome_profile" \
  sentinel-bot
```

## 🔍 Monitoring

### Checking Container Status

```bash
# View running containers
docker ps

# Check container logs
docker logs -f sentinel-runner

# View container resource usage
docker stats sentinel-runner
```

### Health Check

The container includes a health check that pings the `/api/health` endpoint. You can check the health status with:

```bash
docker inspect --format='{{.State.Health.Status}}' sentinel-runner
```

## 🛠️ Troubleshooting

### Common Issues

1. **Container exits immediately**:
   - Check logs with `docker logs sentinel-runner`
   - Ensure environment variables are correctly set

2. **Chrome/Selenium issues**:
   - The container may need more memory. Adjust resource limits in docker-compose.yml
   - Check if Chrome is running in headless mode correctly

3. **API not accessible**:
   - Verify port mapping with `docker port sentinel-runner`
   - Check if the Flask app is running inside the container

## 🌐 Vast.ai Deployment

### Recommended Vast.ai Instance

For running the AI Trading Sentinel on Vast.ai, the following configuration is recommended:

- **Instance Type**: On-demand
- **Machine Type**: Any with at least 2GB RAM and 1 vCPU
- **Disk Space**: 10GB minimum
- **OS Image**: Ubuntu 20.04 or newer

### Deployment Steps for Vast.ai

1. Create a new instance on Vast.ai with Docker support
2. SSH into your instance
3. Clone your repository and navigate to it
4. Build and run the Docker container:

```bash
# Clone repository (if not already done)
git clone https://github.com/yourusername/ai-trading-sentinel.git
cd ai-trading-sentinel

# Create .env file with your credentials
cp .env.example .env
nano .env  # Edit with your credentials

# Build and run with Docker
docker build -t sentinel-bot -f Dockerfile.sentinel .
docker run -d --name sentinel-runner -p 5000:5000 \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/.env:/app/.env" \
  -v "$(pwd)/temp_chrome_profile:/app/temp_chrome_profile" \
  sentinel-bot
```

## 🔄 Alternative: Non-Docker Deployment

If you prefer to deploy without Docker on a Ubuntu server, you can use these commands:

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install Chrome dependencies
sudo apt-get install -y wget gnupg unzip xvfb libxi6 libgconf-2-4 default-jdk

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install Chrome Driver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
CHROME_DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Clone repository
git clone https://github.com/yourusername/ai-trading-sentinel.git
cd ai-trading-sentinel

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install flask flask-cors python-dotenv selenium undetected-chromedriver

# Create directories
mkdir -p logs/screenshots temp_chrome_profile

# Configure environment
cp .env.example .env
nano .env  # Edit with your credentials

# Run the application
python cloud_main.py
```

## 📝 Additional Notes

- The Docker container runs in headless mode by default, which is suitable for server environments
- For development, you may want to modify the Dockerfile to run in non-headless mode
- The container automatically restarts unless explicitly stopped
- All logs are available in the `logs` directory, which is mounted as a volume

## 🔒 Security Considerations

- Never commit your `.env` file with real credentials to version control
- Consider using Docker secrets for sensitive information in production
- Regularly update the Docker image to get security patches
- Limit access to the Docker container and its volumes