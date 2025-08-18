# 🚀 Local Development Setup - VPS Alternative

## 🎯 Quick Solution While VPS is Down

**Since VPS `161.97.112.146` is unreachable, let's run everything locally!**

## 📋 Prerequisites Check

```powershell
# Check Python version (need 3.8+)
python --version

# Check Node.js (need 16+)
node --version
npm --version

# Check Git
git --version
```

## 🔧 Step 1: Backend Setup

```powershell
# Navigate to project
cd c:\Users\Admin\Downloads\ai-trading-sentinel

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
$env:FLASK_APP = "backend_main.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

# Start Flask backend
python backend_main.py
```

**Expected output:**
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

## 🎨 Step 2: Frontend Setup

**Open new terminal:**

```powershell
# Navigate to frontend
cd c:\Users\Admin\Downloads\ai-trading-sentinel\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Expected output:**
```
  Local:   http://localhost:3000/
  Network: http://10.144.230.55:3000/
```

## 🐳 Step 3: Docker Alternative (Optional)

```powershell
# Build Docker image
docker build -t ai-trading-sentinel .

# Run container
docker run -p 80:80 -p 5000:5000 ai-trading-sentinel

# Access at: http://localhost
```

## 🔗 Access URLs

**Local Development:**
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **Health Check:** http://localhost:5000/api/health
- **Trading Dashboard:** http://localhost:3000/dashboard

## 🧪 Step 4: Test Local Setup

```powershell
# Test backend health
curl http://localhost:5000/api/health

# Test frontend
Start-Process "http://localhost:3000"
```

## 📊 Step 5: Run Trading Bot Locally

```powershell
# Start trading bot
python main.py

# Or with specific config
python main.py --config config/local.json
```

## 🔄 Step 6: Local File Server (Already Running)

**Your local file server is active:**
- **URL:** http://10.144.230.55:8000/
- **Files available:** `vps_activation_script.sh`, `frontend-cloud.zip`

## 🛠️ Troubleshooting

### Port Conflicts

```powershell
# Check what's using port 5000
netstat -ano | findstr :5000

# Kill process if needed
Stop-Process -Id <PID> -Force
```

### Missing Dependencies

```powershell
# Install missing packages
pip install flask flask-cors requests playwright

# Install Node dependencies
npm install --legacy-peer-deps
```

### Environment Variables

```powershell
# Create .env file
@"
FLASK_APP=backend_main.py
FLASK_ENV=development
DEBUG=True
API_URL=http://localhost:5000
FRONTEND_URL=http://localhost:3000
"@ | Out-File -FilePath .env -Encoding utf8
```

## 🎯 Development Workflow

1. **Backend changes:** Restart `python backend_main.py`
2. **Frontend changes:** Auto-reload with `npm run dev`
3. **Full restart:** Stop both servers, restart
4. **Testing:** Use `python -m pytest test/`

## 🔄 When VPS Comes Back Online

**Easy migration back to VPS:**

1. **Test locally first:** Ensure everything works
2. **Upload to VPS:** Use `vps_activation_script.sh`
3. **Deploy frontend:** Upload `frontend-cloud.zip`
4. **Switch URLs:** Update environment variables

## 📈 Performance Monitoring

```powershell
# Monitor local processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
Get-Process | Where-Object {$_.ProcessName -like "*node*"}

# Check memory usage
Get-Counter "\Memory\Available MBytes"
```

## 🚀 Ready to Code!

**Your local development environment is now ready!**

- ✅ Backend: Flask API server
- ✅ Frontend: React development server  
- ✅ Trading Bot: Python execution
- ✅ File Server: Local asset serving

**Continue development while VPS issue is resolved!**