#!/usr/bin/env python3
"""
🌐 AI Trading Sentinel - Cloud Configuration Script

This script configures your local development environment to work with cloud deployment.
It shows the difference between local and cloud access patterns.
"""

import os
import json
from pathlib import Path

class CloudConfigurator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.frontend_dir = self.project_root / "frontend"
        self.backend_dir = self.project_root / "backend"
        
    def show_current_architecture(self):
        """Display current local vs cloud architecture"""
        print("\n" + "="*60)
        print("🏗️ AI TRADING SENTINEL ARCHITECTURE")
        print("="*60)
        
        print("\n📍 CURRENT LOCAL SETUP:")
        print("┌─────────────────────────────────────────────┐")
        print("│ 1. React Frontend    → http://localhost:3000 │")
        print("│ 2. Flask Backend API → http://localhost:5000 │")
        print("│ 3. Bulenox Sentinel  → http://localhost:8090 │")
        print("└─────────────────────────────────────────────┘")
        
        print("\n🌐 CLOUD DEPLOYMENT ARCHITECTURE:")
        print("┌─────────────────────────────────────────────┐")
        print("│ 1. React Frontend    → https://yourdomain.com│")
        print("│ 2. Flask Backend API → https://yourdomain.com/api│")
        print("│ 3. Bulenox Sentinel  → https://yourdomain.com/sentinel│")
        print("└─────────────────────────────────────────────┘")
        
        print("\n🔄 KEY DIFFERENCES:")
        print("• Local: Multiple ports, HTTP only")
        print("• Cloud: Single domain, HTTPS, reverse proxy")
        print("• Cloud: 24/7 availability, mobile access")
        print("• Cloud: Professional SSL certificates")
        print("• Cloud: Automatic backups & monitoring")
    
    def create_cloud_env_template(self, domain="your-domain.com"):
        """Create environment template for cloud deployment"""
        
        cloud_env = f"""
# 🌐 AI Trading Sentinel - Cloud Environment Configuration
# Copy this to .env.production on your VPS

# ===== TRADING CREDENTIALS =====
BULENOX_USERNAME=BX64883
BULENOX_PASSWORD=your_secure_password_here
BROKER_URL=https://bulenox.projectx.com

# ===== API CONFIGURATION =====
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_super_secret_key_change_this_in_production
PORT=5000

# ===== FRONTEND URLS =====
VITE_API_URL=https://{domain}/api
VITE_WEBSOCKET_URL=wss://{domain}/ws
VITE_ENVIRONMENT=production

# ===== SECURITY =====
ALLOWED_HOSTS={domain},www.{domain}
CORS_ORIGINS=https://{domain},https://www.{domain}

# ===== MONITORING & ALERTS =====
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EMAIL_ALERTS=your-email@domain.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# ===== DATABASE (Optional) =====
DATABASE_URL=postgresql://user:password@localhost:5432/trading_db
REDIS_URL=redis://localhost:6379/0

# ===== BROWSER AUTOMATION =====
HEADLESS=true
DISPLAY=:99
CHROME_BINARY_PATH=/usr/bin/chromium-browser

# ===== LOGGING =====
LOG_LEVEL=INFO
LOG_FILE=/var/log/ai-trading/app.log
"""
        
        env_file = self.project_root / ".env.cloud.template"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(cloud_env)
        
        print(f"\n✅ Created cloud environment template: {env_file}")
        return env_file
    
    def create_docker_compose(self, domain="your-domain.com"):
        """Create Docker Compose for easy cloud deployment"""
        
        docker_compose = f"""
version: '3.8'

services:
  # React Frontend (built and served by Nginx)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: ai-trading-frontend
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend
      - sentinel
    networks:
      - trading-network

  # Flask Backend API
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-trading-backend
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - PYTHONPATH=/app
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - trading-network

  # Bulenox Sentinel Control Panel
  sentinel:
    build:
      context: .
      dockerfile: Dockerfile.sentinel
    container_name: ai-trading-sentinel
    restart: unless-stopped
    ports:
      - "8090:8090"
    environment:
      - DISPLAY=:99
      - PYTHONPATH=/app
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
    networks:
      - trading-network
    depends_on:
      - xvfb

  # Virtual display for headless browser
  xvfb:
    image: selenium/standalone-chrome:latest
    container_name: ai-trading-xvfb
    restart: unless-stopped
    ports:
      - "4444:4444"
    environment:
      - DISPLAY=:99
    networks:
      - trading-network

  # Redis for caching and session management
  redis:
    image: redis:7-alpine
    container_name: ai-trading-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - trading-network

  # PostgreSQL for trade data storage
  postgres:
    image: postgres:15-alpine
    container_name: ai-trading-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=trading_db
      - POSTGRES_USER=trading_user
      - POSTGRES_PASSWORD=secure_password_change_this
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - trading-network

  # Monitoring with Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: ai-trading-grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - trading-network

volumes:
  postgres_data:
  redis_data:
  grafana_data:

networks:
  trading-network:
    driver: bridge
"""
        
        compose_file = self.project_root / "docker-compose.prod.yml"
        with open(compose_file, "w", encoding="utf-8") as f:
            f.write(docker_compose)
        
        print(f"✅ Created Docker Compose file: {compose_file}")
        return compose_file
    
    def create_nginx_config(self, domain="your-domain.com"):
        """Create Nginx configuration for reverse proxy"""
        
        nginx_config = f"""
events {{
    worker_connections 1024;
}}

http {{
    upstream backend {{
        server backend:5000;
    }}
    
    upstream sentinel {{
        server sentinel:8090;
    }}
    
    # Redirect HTTP to HTTPS
    server {{
        listen 80;
        server_name {domain} www.{domain};
        return 301 https://$server_name$request_uri;
    }}
    
    # Main HTTPS server
    server {{
        listen 443 ssl http2;
        server_name {domain} www.{domain};
        
        # SSL Configuration
        ssl_certificate /etc/ssl/certs/{domain}.crt;
        ssl_certificate_key /etc/ssl/certs/{domain}.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        
        # Frontend (React build)
        location / {{
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {{
                expires 1y;
                add_header Cache-Control "public, immutable";
            }}
        }}
        
        # Backend API
        location /api/ {{
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
        
        # Bulenox Sentinel Control Panel
        location /sentinel/ {{
            proxy_pass http://sentinel/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            rewrite ^/sentinel/(.*) /$1 break;
        }}
        
        # WebSocket support
        location /ws/ {{
            proxy_pass http://backend/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }}
        
        # Grafana monitoring
        location /monitoring/ {{
            proxy_pass http://grafana:3000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            rewrite ^/monitoring/(.*) /$1 break;
        }}
    }}
}}
"""
        
        nginx_file = self.project_root / "nginx.conf"
        with open(nginx_file, "w", encoding="utf-8") as f:
            f.write(nginx_config)
        
        print(f"✅ Created Nginx configuration: {nginx_file}")
        return nginx_file
    
    def create_deployment_commands(self, domain="your-domain.com"):
        """Create quick deployment commands"""
        
        commands = f"""
# 🚀 AI Trading Sentinel - Cloud Deployment Commands

## 1. VPS Setup (Run on your Contabo VPS)
```bash
# Download and run production deployment
wget https://raw.githubusercontent.com/YOUR_REPO/main/deploy_production.py
python3 deploy_production.py --domain {domain} --email your@email.com
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
sudo cp nginx.conf /etc/nginx/sites-available/{domain}
sudo ln -s /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Setup SSL
sudo certbot --nginx -d {domain}

# Start services
pm2 start ecosystem.config.json
```

## 4. Access Your Cloud Deployment

### 🌐 Production URLs:
- **Main Dashboard:** https://{domain}
- **Trading API:** https://{domain}/api
- **Sentinel Control:** https://{domain}/sentinel
- **Monitoring:** https://{domain}/monitoring
- **Health Check:** https://{domain}/api/health

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
curl https://{domain}/api/health

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
"""
        
        commands_file = self.project_root / "CLOUD_DEPLOYMENT_COMMANDS.md"
        with open(commands_file, "w", encoding="utf-8") as f:
            f.write(commands)
        
        print(f"✅ Created deployment commands: {commands_file}")
        return commands_file
    
    def configure_for_cloud(self, domain="your-domain.com"):
        """Main configuration function"""
        print("🌐 Configuring AI Trading Sentinel for cloud deployment...")
        
        self.show_current_architecture()
        
        print("\n📝 Creating cloud configuration files...")
        self.create_cloud_env_template(domain)
        self.create_docker_compose(domain)
        self.create_nginx_config(domain)
        self.create_deployment_commands(domain)
        
        print("\n" + "="*60)
        print("🎉 CLOUD CONFIGURATION COMPLETE!")
        print("="*60)
        
        print(f"\n📋 Next Steps:")
        print(f"1. Get a VPS (Contabo recommended)")
        print(f"2. Point your domain to VPS IP")
        print(f"3. Run: python3 deploy_production.py --domain {domain} --email your@email.com")
        print(f"4. Access your bot at: https://{domain}")
        
        print(f"\n🔧 Alternative: Use Docker Compose")
        print(f"   docker-compose -f docker-compose.prod.yml up -d")
        
        print(f"\n📱 Mobile Access: All interfaces work on phones/tablets!")
        print(f"\n💰 Cost: ~€25/month for 24/7 professional trading bot")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Configure AI Trading Sentinel for cloud deployment')
    parser.add_argument('--domain', default='your-domain.com', help='Your domain name')
    
    args = parser.parse_args()
    
    configurator = CloudConfigurator()
    configurator.configure_for_cloud(args.domain)

if __name__ == "__main__":
    main()