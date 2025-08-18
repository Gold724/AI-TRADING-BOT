
# 🚀 AI Trading Sentinel - Cloud Deployment Commands

## 1. VPS Setup (Run on your Contabo VPS)
```bash
# Download and run production deployment
wget https://raw.githubusercontent.com/YOUR_REPO/main/deploy_production.py
python3 deploy_production.py --domain trading-sentinel.com --email your@email.com
```

## 2. Docker Deployment (Alternative)
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
cd ai-trading-sentinel

# Configure environment
cp .env.cloud.template .env.production
# Edit .env.production with your credentials

# Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d
```

## 3. Manual VPS Setup
```bash
# System setup
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 nodejs npm nginx git

# Clone and setup
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Install dependencies
pip3 install -r requirements.txt
cd frontend && npm install && npm run build && cd ..

# Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/trading-sentinel.com
sudo ln -s /etc/nginx/sites-available/trading-sentinel.com /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Setup SSL
sudo certbot --nginx -d trading-sentinel.com

# Start services
pm2 start ecosystem.config.json
```

## 4. Access Your Cloud Deployment

### 🌐 Production URLs:
- **Main Dashboard:** https://trading-sentinel.com
- **Trading API:** https://trading-sentinel.com/api
- **Sentinel Control:** https://trading-sentinel.com/sentinel
- **Monitoring:** https://trading-sentinel.com/monitoring
- **Health Check:** https://trading-sentinel.com/api/health

### 📱 Mobile Access:
All interfaces are responsive and work perfectly on mobile devices!

### 🔧 Management:
```bash
# Check status
pm2 status

# View logs
pm2 logs

# Restart services
pm2 restart all

# Deploy updates
git pull && ./deploy.sh
```

## 5. Monitoring & Alerts

### Health Checks:
```bash
# Manual health check
curl https://trading-sentinel.com/api/health

# Automated monitoring (runs every 5 minutes)
crontab -e
# Add: */5 * * * * /opt/ai-trading-sentinel/health_check.py
```

### Slack Alerts:
1. Create Slack webhook URL
2. Add to .env.production: SLACK_WEBHOOK_URL=your_webhook
3. Alerts sent for: crashes, failed trades, login issues

## 6. Security Checklist

- [ ] SSH key-only access
- [ ] Firewall configured (UFW)
- [ ] SSL certificates installed
- [ ] Environment variables secured
- [ ] Regular security updates
- [ ] Database credentials encrypted

## 7. Cost Estimate

- **Contabo VPS (8GB):** €20/month
- **Domain name:** €10/year
- **SSL certificate:** Free (Let's Encrypt)
- **Total:** ~€25/month for 24/7 professional trading bot

🎯 **Result:** Your AI Trading Sentinel accessible anywhere, anytime!
