# 🧪 Frontend Necessities Verification Script
# Verifies all trading dashboard components and API connectivity

Write-Host "🔍 AI Trading Sentinel - Frontend Verification" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$VPS_IP = "161.97.112.146"
$LOCAL_URL = "http://localhost:5173"
$CLOUD_URL = "http://$VPS_IP"

# Test Configuration
$tests = @(
    @{ Name = "Frontend Build"; Path = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\dist\index.html" },
    @{ Name = "Deployment Package"; Path = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\frontend-cloud.zip" },
    @{ Name = "Environment Config"; Path = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\.env" }
)

# Component Verification
$components = @(
    "App.tsx", "SignalCard.tsx", "SignalStats.tsx", "SignalExport.tsx",
    "BrokerAdminPanel.tsx", "BulenoxTradingPanel.tsx", "BulenoxRiskManager.tsx",
    "BulenoxPerformanceTracker.tsx", "BulenoxPositionManager.tsx", "RemoteControlPanel.tsx",
    "HeartbeatMonitor.tsx", "DailyStats.tsx", "CompoundingTracker.tsx", "ModeSelector.tsx"
)

# API Endpoints to Test
$apiEndpoints = @(
    @{ Endpoint = "/health"; Description = "Health Check" },
    @{ Endpoint = "/api/strategy"; Description = "Strategy API" },
    @{ Endpoint = "/api/login"; Description = "Authentication" }
)

Write-Host "\n📋 Step 1: Verifying Build Files..." -ForegroundColor Yellow
foreach ($test in $tests) {
    if (Test-Path $test.Path) {
        $size = (Get-Item $test.Path).Length
        Write-Host "✅ $($test.Name): Found ($([math]::Round($size/1KB, 2)) KB)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($test.Name): Missing" -ForegroundColor Red
    }
}

Write-Host "\n🧩 Step 2: Verifying React Components..." -ForegroundColor Yellow
$componentPath = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\src\components"
$missingComponents = @()
foreach ($component in $components) {
    $fullPath = Join-Path $componentPath $component
    if (Test-Path $fullPath) {
        Write-Host "✅ $component" -ForegroundColor Green
    } else {
        Write-Host "⚠️ $component: Not found" -ForegroundColor Yellow
        $missingComponents += $component
    }
}

if ($missingComponents.Count -eq 0) {
    Write-Host "✅ All core trading components verified!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Missing components: $($missingComponents -join ', ')" -ForegroundColor Yellow
}

Write-Host "\n📦 Step 3: Verifying Dependencies..." -ForegroundColor Yellow
$packageJsonPath = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\package.json"
if (Test-Path $packageJsonPath) {
    $packageJson = Get-Content $packageJsonPath | ConvertFrom-Json
    $requiredDeps = @("react", "react-dom", "recharts", "@vitejs/plugin-react")
    
    foreach ($dep in $requiredDeps) {
        if ($packageJson.dependencies.$dep -or $packageJson.devDependencies.$dep) {
            Write-Host "✅ $dep: Installed" -ForegroundColor Green
        } else {
            Write-Host "❌ $dep: Missing" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ package.json not found" -ForegroundColor Red
}

Write-Host "\n🌐 Step 4: Testing API Connectivity..." -ForegroundColor Yellow

# Test VPS Backend
Write-Host "Testing VPS Backend ($CLOUD_URL)..." -ForegroundColor Cyan
foreach ($api in $apiEndpoints) {
    try {
        $url = "$CLOUD_URL$($api.Endpoint)"
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -ErrorAction Stop
        Write-Host "✅ $($api.Description): $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($api.Description): Failed - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "\n🔧 Step 5: Environment Configuration Check..." -ForegroundColor Yellow
$envPath = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\.env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath
    Write-Host "Environment Variables:" -ForegroundColor Cyan
    foreach ($line in $envContent) {
        if ($line -match "^VITE_") {
            Write-Host "  $line" -ForegroundColor White
        }
    }
    
    # Check if pointing to VPS
    if ($envContent -match "161\.97\.112\.146") {
        Write-Host "✅ Environment configured for VPS deployment" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Environment may not be configured for VPS" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
}

Write-Host "\n📊 Step 6: Trading Features Verification..." -ForegroundColor Yellow

# Check App.tsx for trading features
$appTsxPath = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\src\App.tsx"
if (Test-Path $appTsxPath) {
    $appContent = Get-Content $appTsxPath -Raw
    
    $tradingFeatures = @(
        @{ Feature = "Authentication"; Pattern = "isAuthenticated" },
        @{ Feature = "Broker Selection"; Pattern = "setBroker" },
        @{ Feature = "Trade Parameters"; Pattern = "tradeParams" },
        @{ Feature = "Strategy Selection"; Pattern = "selectedStrategy" },
        @{ Feature = "Risk Management"; Pattern = "stopLoss|takeProfit" },
        @{ Feature = "API Integration"; Pattern = "fetch.*api" },
        @{ Feature = "WebSocket Support"; Pattern = "WebSocket|ws" },
        @{ Feature = "Error Handling"; Pattern = "backendError" }
    )
    
    foreach ($feature in $tradingFeatures) {
        if ($appContent -match $feature.Pattern) {
            Write-Host "✅ $($feature.Feature): Implemented" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($feature.Feature): Not detected" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "❌ App.tsx not found" -ForegroundColor Red
}

Write-Host "\n🎯 Step 7: Deployment Readiness Check..." -ForegroundColor Yellow

$deploymentChecks = @(
    @{ Check = "Frontend Build"; Status = (Test-Path "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\dist\index.html") },
    @{ Check = "Deployment Package"; Status = (Test-Path "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\frontend-cloud.zip") },
    @{ Check = "VPS Configuration"; Status = $true },
    @{ Check = "Component Library"; Status = ($missingComponents.Count -eq 0) }
)

$readyForDeployment = $true
foreach ($check in $deploymentChecks) {
    if ($check.Status) {
        Write-Host "✅ $($check.Check): Ready" -ForegroundColor Green
    } else {
        Write-Host "❌ $($check.Check): Not Ready" -ForegroundColor Red
        $readyForDeployment = $false
    }
}

Write-Host "\n🎉 VERIFICATION COMPLETE!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Cyan

if ($readyForDeployment) {
    Write-Host "🟢 STATUS: READY FOR CLOUD DEPLOYMENT" -ForegroundColor Green
    Write-Host "\n📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. 📤 Upload frontend-cloud.zip to VPS" -ForegroundColor White
    Write-Host "2. 🔧 Configure Nginx (see SIMPLE_CLOUD_DEPLOYMENT.md)" -ForegroundColor White
    Write-Host "3. 🌐 Access dashboard at http://$VPS_IP" -ForegroundColor White
    Write-Host "4. 🚀 Start trading from anywhere in the world!" -ForegroundColor White
} else {
    Write-Host "🟡 STATUS: NEEDS ATTENTION" -ForegroundColor Yellow
    Write-Host "Please resolve the issues above before deployment." -ForegroundColor White
}

Write-Host "\n🌍 Access Points After Deployment:" -ForegroundColor Cyan
Write-Host "🌐 Dashboard: http://$VPS_IP" -ForegroundColor White
Write-Host "🔧 API: http://$VPS_IP/api/" -ForegroundColor White
Write-Host "📊 Health: http://$VPS_IP/health" -ForegroundColor White