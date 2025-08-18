#!/bin/bash
# AI Trading Sentinel - VPS Setup Script

echo "🚀 Configuring AI Trading Sentinel on VPS..."

# Update system
echo "📦 Updating system packages..."
apt update -y
apt install -y nginx unzip curl

# Create deployment directory
echo "📁 Setting up deployment directory..."
mkdir -p /var/www/ai-trading-sentinel
cd /var/www/ai-trading-sentinel

# Extract frontend
echo "📦 Extracting frontend package..."
if [ -f "/tmp/frontend-cloud.zip" ]; then
    unzip -o /tmp/frontend-cloud.zip
    echo "✅ Frontend extracted successfully"
else
    echo "❌ Frontend package not found"
    exit 1
fi

# Set permissions
chown -R www-data:www-data /var/www/ai-trading-sentinel
chmod -R 755 /var/www/ai-trading-sentinel

# Create Nginx config
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-trading-sentinel << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    root /var/www/ai-trading-sentinel;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws {
        proxy_pass http://127.0.0.1:5000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
echo "🔧 Testing Nginx..."
nginx -t && systemctl restart nginx && systemctl enable nginx

# Configure firewall
echo "🔒 Configuring firewall..."
ufw allow 80/tcp
ufw allow 5000/tcp
ufw --force enable

echo "🎉 Deployment completed!"
echo "🌍 Access: http://161.97.112.146"

# Cleanup
rm -f /tmp/frontend-cloud.zip
echo "🧹 Cleanup completed"