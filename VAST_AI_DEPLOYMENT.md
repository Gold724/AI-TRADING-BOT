# 🌐 AI Trading Sentinel - Vast.ai Deployment Guide

This guide provides detailed instructions for deploying the AI Trading Sentinel on Vast.ai, a platform that offers cost-effective GPU and CPU instances for running containerized applications.

## 🔍 Recommended Vast.ai Instance

For optimal performance and cost-effectiveness, the following Vast.ai instance configuration is recommended:

### Minimum Requirements
- **Instance Type**: On-demand
- **Machine Type**: CPU-only (no GPU needed)
- **RAM**: 2GB minimum (4GB recommended)
- **vCPUs**: 1 minimum (2 recommended)
- **Disk Space**: 10GB minimum
- **OS Image**: Ubuntu 20.04 or newer with Docker

### Cost-Effective Options
- Look for instances with pricing around $0.03-$0.05 per hour
- Filter for instances with at least 2GB RAM and 1 vCPU
- Sort by price to find the most economical options

## 🚀 Deployment Steps

### 1. Create a Vast.ai Instance

1. Sign up for a Vast.ai account if you don't have one
2. Navigate to the "Create" tab
3. Apply the following filters:
   - **Instance Type**: On-demand
   - **Disk Space**: 10+ GB
   - **RAM**: 2+ GB
   - **vCPUs**: 1+
   - **Image**: Select an Ubuntu image with Docker pre-installed
4. Sort by price (ascending) and select an appropriate instance
5. Click "Rent" to create the instance

### 2. Connect to Your Instance

Once your instance is running, you'll need to connect to it via SSH:

```bash
ssh -p <port> root@<ip_address>
```

Replace `<port>` and `<ip_address>` with the values provided by Vast.ai in the instance details.

### 3. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-trading-sentinel.git
cd ai-trading-sentinel
```

### 4. Configure Environment Variables

```bash
# Create .env file from example
cp .env.example .env

# Edit the .env file with your credentials
nano .env
```

Make sure to update the following variables in the `.env` file:

```
BULENOX_USERNAME=your_bulenox_username
BULENOX_PASSWORD=your_bulenox_password
BULENOX_ACCOUNT_ID=your_bulenox_account_id
HEADLESS=true
USE_TEMP_PROFILE=true
SCREENSHOT_ON_FAILURE=true
```

### 5. Build and Run the Docker Container

```bash
# Make the helper script executable
chmod +x run_sentinel_docker.sh

# Build and run the container
./run_sentinel_docker.sh all
```

Alternatively, you can use Docker commands directly:

```bash
# Build the Docker image
docker build -t sentinel-bot -f Dockerfile.sentinel .

# Run the container
docker run -d --name sentinel-runner \
  -p 5000:5000 \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/.env:/app/.env" \
  -v "$(pwd)/temp_chrome_profile:/app/temp_chrome_profile" \
  --restart unless-stopped \
  sentinel-bot
```

### 6. Verify Deployment

```bash
# Check if the container is running
docker ps

# View logs to ensure everything is working
docker logs -f sentinel-runner
```

## 📊 Monitoring and Management

### Setting Up Persistent Monitoring

To keep the bot running even after you disconnect from SSH, you can use tools like `tmux` or `screen`:

```bash
# Install tmux
apt-get update && apt-get install -y tmux

# Start a new tmux session
tmux new -s sentinel

# Run your commands here
./run_sentinel_docker.sh all

# Detach from the session by pressing Ctrl+B, then D
# To reattach later:
tmux attach -t sentinel
```

### Checking Logs

The container is configured to write logs to the `logs` directory, which is mounted as a volume:

```bash
# View the main application log
cat logs/cloud_main.log

# Follow the log in real-time
tail -f logs/cloud_main.log

# View the trade executor log
cat logs/cloud_trade_executor.log
```

### Checking Container Health

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' sentinel-runner

# View container resource usage
docker stats sentinel-runner
```

## 🔄 Updating the Bot

To update the bot with the latest code:

```bash
# Stop the container
./run_sentinel_docker.sh stop

# Pull the latest code
git pull

# Rebuild and restart
./run_sentinel_docker.sh all
```

## 💰 Cost Optimization

### Estimating Costs

With a typical Vast.ai instance costing around $0.03-$0.05 per hour, the monthly cost would be approximately:

- $0.04/hour × 24 hours × 30 days = $28.80/month

This makes Vast.ai significantly more cost-effective than traditional cloud providers for this type of application.

### Tips for Reducing Costs

1. **Use Interruptible Instances**: If your trading strategy can tolerate occasional interruptions, consider using interruptible instances which are cheaper.

2. **Optimize Container Resources**: Adjust the container's resource limits in the docker-compose file to use only what's necessary.

3. **Schedule Uptime**: If you only need the bot during certain trading hours, consider automating the start/stop of the instance.

## 🛠️ Troubleshooting

### Common Issues on Vast.ai

1. **Container fails to start**:
   - Check if there's enough disk space: `df -h`
   - Ensure Docker is running: `systemctl status docker`
   - Check for Docker errors: `docker logs sentinel-runner`

2. **Chrome/Selenium issues**:
   - Ensure all Chrome dependencies are installed
   - Verify the container has enough memory allocated
   - Check if Chrome is running in headless mode correctly

3. **Network connectivity issues**:
   - Test network connectivity: `curl -I https://bulenox.com`
   - Check if the instance has outbound internet access

### Restarting After Instance Reboot

If your Vast.ai instance reboots, you'll need to restart the container:

```bash
# Check if the container exists but is stopped
docker ps -a | grep sentinel-runner

# Start the container if it exists
docker start sentinel-runner

# If the container doesn't exist, run it again
./run_sentinel_docker.sh run
```

## 📝 Additional Resources

- [Vast.ai Documentation](https://vast.ai/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)

---

By following this guide, you should be able to deploy the AI Trading Sentinel on a cost-effective Vast.ai instance, allowing for automated trading with minimal infrastructure costs.