# VPS Connectivity Test Script for AI Trading Sentinel
# Run this in PowerShell to diagnose connection issues

Write-Host "AI Trading Sentinel - VPS Connectivity Diagnostics" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

$vpsIP = "161.97.112.146"
$ports = @(22, 80, 443, 5000, 8080)

# Test 1: Basic Ping
Write-Host "`nTesting Basic Connectivity..." -ForegroundColor Yellow
try {
    $pingResult = Test-Connection -ComputerName $vpsIP -Count 4 -ErrorAction Stop
    Write-Host "SUCCESS: VPS is reachable" -ForegroundColor Green
    $pingResult | ForEach-Object { 
        Write-Host "   Response from $($_.Address): time=$($_.ResponseTime)ms" -ForegroundColor White
    }
} catch {
    Write-Host "PING FAILED: VPS unreachable (Network isolation)" -ForegroundColor Red
    Write-Host "   This confirms the critical network issue" -ForegroundColor Red
}

# Test 2: Port Connectivity
Write-Host "`nTesting Port Connectivity..." -ForegroundColor Yellow
foreach ($port in $ports) {
    $service = switch ($port) {
        22 { "SSH (Termius)" }
        80 { "HTTP (Web Dashboard)" }
        443 { "HTTPS (Secure Web)" }
        5000 { "Flask Direct" }
        8080 { "Alternative HTTP" }
    }
    
    try {
        $tcpTest = Test-NetConnection -ComputerName $vpsIP -Port $port -WarningAction SilentlyContinue
        if ($tcpTest.TcpTestSucceeded) {
            Write-Host "   Port $port ($service): OPEN" -ForegroundColor Green
        } else {
            Write-Host "   Port $port ($service): CLOSED" -ForegroundColor Red
        }
    } catch {
        Write-Host "   Port $port ($service): ERROR" -ForegroundColor Red
    }
}

# Test 3: DNS Resolution
Write-Host "`nTesting DNS Resolution..." -ForegroundColor Yellow
try {
    $dnsResult = Resolve-DnsName -Name $vpsIP -ErrorAction Stop
    Write-Host "DNS Resolution: Working" -ForegroundColor Green
} catch {
    Write-Host "DNS Resolution: Failed" -ForegroundColor Red
}

# Test 4: Traceroute (Network Path)
Write-Host "`nTesting Network Path..." -ForegroundColor Yellow
try {
    Write-Host "   Running traceroute to $vpsIP..." -ForegroundColor White
    $traceResult = Test-NetConnection -ComputerName $vpsIP -TraceRoute -WarningAction SilentlyContinue
    if ($traceResult.TraceRoute) {
        Write-Host "Traceroute completed:" -ForegroundColor Green
        $traceResult.TraceRoute | ForEach-Object { Write-Host "   -> $_" -ForegroundColor White }
    } else {
        Write-Host "Traceroute failed: Network path blocked" -ForegroundColor Red
    }
} catch {
    Write-Host "Traceroute error: Cannot trace path" -ForegroundColor Red
}

# Results Summary
Write-Host "`nDIAGNOSIS SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Gray

$pingSuccess = $false
try {
    Test-Connection -ComputerName $vpsIP -Count 1 -ErrorAction Stop | Out-Null
    $pingSuccess = $true
} catch {}

if ($pingSuccess) {
    Write-Host "VPS Status: REACHABLE" -ForegroundColor Green
    Write-Host "   -> Termius should work normally" -ForegroundColor White
    Write-Host "   -> Check Termius settings or SSH keys" -ForegroundColor White
} else {
    Write-Host "VPS Status: UNREACHABLE (CRITICAL)" -ForegroundColor Red
    Write-Host "   -> Complete network isolation confirmed" -ForegroundColor White
    Write-Host "   -> Termius cannot connect (not a Termius issue)" -ForegroundColor White
    Write-Host "   -> Requires VPS console access or Contabo support" -ForegroundColor White
}

# Next Steps
Write-Host "`nIMMEDIATE ACTIONS REQUIRED:" -ForegroundColor Cyan
if ($pingSuccess) {
    Write-Host "1. Network is working - check Termius configuration" -ForegroundColor Green
    Write-Host "2. Verify SSH keys and authentication" -ForegroundColor Green
    Write-Host "3. Try alternative SSH clients (PuTTY, Windows Terminal)" -ForegroundColor Green
} else {
    Write-Host "1. Login to Contabo control panel immediately" -ForegroundColor Red
    Write-Host "2. Use VPS Console (VNC) to access server directly" -ForegroundColor Red
    Write-Host "3. Run network reset commands via console" -ForegroundColor Red
    Write-Host "4. Contact Contabo support if console access fails" -ForegroundColor Red
}

Write-Host "`nFull recovery guide: TERMIUS_VPS_RECOVERY.md" -ForegroundColor Yellow
Write-Host "Contabo Panel: https://my.contabo.com/" -ForegroundColor Blue

Write-Host "`n" -ForegroundColor White
Read-Host "Press Enter to exit"