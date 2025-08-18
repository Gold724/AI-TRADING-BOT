# 🌐 Frontend Cloud Deployment Guide

## Quick Manual Deployment to VPS

Since you want the frontend accessible from the cloud, here's how to deploy it to your Contabo VPS:

### Option 1: Manual Upload (Recommended)

1. **Prepare the build** (already done):
   ```bash
   cd frontend
   npm run build
   ```

2. **Upload to VPS using SCP/SFTP**:
   ```bash
   # Create a zip of the dist folder
   cd frontend
   tar -czf frontend-build.tar.gz dist/
   
   # Upload to VPS (you'll need to enter password)
   scp frontend-build.tar.gz root@161.97.112.146:/tmp/
   ```

3. **SSH into VPS and setup**:
   ```bash
   ssh root@161.97.112.146
   
   # Install Nginx if not installed
   apt update && apt install -y nginx
   
   # Extract and deploy frontend
   cd /tmp
   tar -xzf frontend-build.tar.gz
   mkdir -p /var/www/trae-frontend
   cp -r dist/* /var/www/trae-frontend/
   chown -R www-data:www-data /var/www/trae-frontend
   chmod -R 755 /var/www/trae-frontend
   ```

4. **Configure Nginx**:
   ```bash
   # Create Nginx config
   cat > /etc/nginx/sites-available/trae-frontend << 'EOF'
   server {
       listen 80;
       server_name 161.97.112.146;
       root /var/www/trae-frontend;
       index index.html;
       
       # Handle React Router
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       # Proxy API calls to Flask backend
       location /api/ {
           proxy_pass http://127.0.0.1:5000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
       
       # WebSocket proxy
       location /ws {
           proxy_pass http://127.0.0.1:5000/ws;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   EOF
   
   # Enable the site
   ln -sf /etc/nginx/sites-available/trae-frontend /etc/nginx/sites-enabled/
   rm -f /etc/nginx/sites-enabled/default
   
   # Test and restart Nginx
   nginx -t
   systemctl restart nginx
   systemctl enable nginx
   
   # Configure firewall
   ufw allow 80/tcp
   ufw allow 'Nginx Full'
   ```

### Option 2: Using FileZilla/WinSCP (Windows Users)

1. **Download FileZilla or WinSCP**
2. **Connect to VPS**:
   - Host: `161.97.112.146`
   - Username: `root`
   - Password: [your VPS password]
   - Port: `22`

3. **Upload the `frontend/dist` folder** to `/var/www/trae-frontend/`

4. **SSH and configure Nginx** (same as Option 1, step 4)

### Option 3: Automated Script (Requires SSH Key Setup)

If you want to use the automated script, first set up SSH keys:

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy public key to VPS
ssh-copy-id root@161.97.112.146

# Then run the deployment script
powershell -ExecutionPolicy Bypass -File deploy_frontend_vps.ps1
```

## 🎯 Access Points After Deployment

- **Frontend Dashboard**: `http://161.97.112.146`
- **API Endpoint**: `http://161.97.112.146/api/`
- **Health Check**: `http://161.97.112.146/api/health`
- **WebSocket**: `ws://161.97.112.146/ws`

## 🔧 Verification Commands

```bash
# Check if services are running
sudo systemctl status nginx
sudo systemctl status trae-backend

# Check logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Test endpoints
curl http://161.97.112.146/
curl http://161.97.112.146/api/health
```

## 🚀 Benefits of Cloud Frontend

✅ **Universal Access**: Access your trading dashboard from anywhere  
✅ **No Local Dependencies**: No need to run `npm run dev` locally  
✅ **Production Performance**: Optimized build with Nginx serving static files  
✅ **Integrated Backend**: Direct API calls without CORS issues  
✅ **Real-time Updates**: WebSocket connection for live trading data  

## 📱 Mobile Access

Once deployed, you can access the trading dashboard from:
- Desktop browsers
- Mobile browsers
- Tablets
- Any device with internet connection

## 🔒 Security Notes

- Consider setting up SSL/HTTPS for production use
- Configure proper firewall rules
- Use strong passwords and SSH keys
- Regular security updates

---

**Next Step**: Choose your preferred deployment method and get your trading dashboard live in the cloud! 🌐