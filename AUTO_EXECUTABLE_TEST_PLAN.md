# TRAE AI Trading Sentinel - Auto-Executable Test Plan
## Bulenox Playwright Login Integration

**TRADEBOT SENTINEL** comprehensive testing protocol for robust login automation with stealth capabilities, retries, and debugging.

---

## Prerequisites Checklist

### 1. Environment Setup
```powershell
# Check Python version (requires 3.8+)
python --version

# Verify dependencies
pip show playwright
pip show playwright-stealth
pip show curlconverter

# Install missing dependencies
pip install playwright>=1.40.0 playwright-stealth>=1.0.6 curlconverter>=2.1.0

# Install Playwright browsers
python -m playwright install chromium
```

### 2. Environment Variables
```powershell
# Create .env file with your credentials
echo BULENOX_USERNAME=your_username > .env
echo BULENOX_PASSWORD=your_password >> .env
echo BULENOX_HEADLESS=false >> .env
```

### 3. Directory Structure Verification
```powershell
# Verify required files exist
ls login_bulenox_playwright.py
ls trae_trade_capture.py
ls requirements.txt
```

---

## Test Case 1: Fresh Login Success (Basic Authentication)

### Command
```powershell
python login_bulenox_playwright.py
```

### Expected Logs
```
[2024-XX-XX XX:XX:XX] [INFO] Starting Bulenox Playwright login...
[2024-XX-XX XX:XX:XX] [INFO] Browser launched successfully
[2024-XX-XX XX:XX:XX] [INFO] Stealth mode applied
[2024-XX-XX XX:XX:XX] [INFO] Navigating to https://projectx.bulenox.com/
[2024-XX-XX XX:XX:XX] [INFO] Login page loaded successfully
[2024-XX-XX XX:XX:XX] [INFO] Human-like typing for username...
[2024-XX-XX XX:XX:XX] [INFO] Human-like typing for password...
[2024-XX-XX XX:XX:XX] [INFO] Login attempt 1/3
[2024-XX-XX XX:XX:XX] [INFO] Login successful - dashboard detected
[2024-XX-XX XX:XX:XX] [SUCCESS] Session saved to session_YYYYMMDD_HHMMSS.json
```

### Expected Artifacts
- **Session file**: `session_YYYYMMDD_HHMMSS.json`
- **Screenshot**: `login_success_YYYYMMDD_HHMMSS.png` (if BULENOX_HEADLESS=false)

### Success Criteria
- ✅ No timeout errors
- ✅ Dashboard elements detected
- ✅ Session file created
- ✅ Exit code 0

---

## Test Case 2: Session Reuse Validation

### Command (Run immediately after Test Case 1)
```powershell
python login_bulenox_playwright.py
```

### Expected Logs
```
[2024-XX-XX XX:XX:XX] [INFO] Starting Bulenox Playwright login...
[2024-XX-XX XX:XX:XX] [INFO] Found existing session: session_YYYYMMDD_HHMMSS.json
[2024-XX-XX XX:XX:XX] [INFO] Attempting to reuse session...
[2024-XX-XX XX:XX:XX] [SUCCESS] Session reused successfully - dashboard detected
```

### Success Criteria
- ✅ Session reuse detected
- ✅ No fresh login attempt
- ✅ Dashboard validation passed
- ✅ Execution time < 10 seconds

---

## Test Case 3: Visual Debugging Mode

### Command
```powershell
# Force headless=false for visual debugging
set BULENOX_HEADLESS=false
python login_bulenox_playwright.py
```

### Expected Behavior
- 🖥️ Browser window opens visibly
- 🖱️ Human-like mouse movements observed
- ⌨️ Realistic typing delays visible
- 📸 Screenshots captured on key steps

### Expected Artifacts
- **Screenshots**: Multiple timestamped PNG files
- **HTML snapshots**: On any errors/failures

### Success Criteria
- ✅ Visual browser interaction
- ✅ Screenshots captured
- ✅ Human-like behavior observed

---

## Test Case 4: Stealth Fallback Mode

### Setup
```powershell
# Temporarily uninstall playwright-stealth
pip uninstall playwright-stealth -y
```

### Command
```powershell
python login_bulenox_playwright.py
```

### Expected Logs
```
[2024-XX-XX XX:XX:XX] [WARN] playwright_stealth not installed - proceeding without stealth (install with: pip install playwright-stealth)
[2024-XX-XX XX:XX:XX] [INFO] Browser launched successfully
[2024-XX-XX XX:XX:XX] [INFO] Navigating to https://projectx.bulenox.com/
```

### Cleanup
```powershell
# Reinstall playwright-stealth
pip install playwright-stealth>=1.0.6
```

### Success Criteria
- ✅ Warning logged
- ✅ Login continues without stealth
- ✅ No crashes or exceptions

---

## Test Case 5: Retry Logic and Error Handling

### Setup
```powershell
# Use invalid credentials temporarily
set BULENOX_USERNAME=invalid_user
set BULENOX_PASSWORD=invalid_pass
```

### Command
```powershell
python login_bulenox_playwright.py
```

### Expected Logs
```
[2024-XX-XX XX:XX:XX] [INFO] Login attempt 1/3
[2024-XX-XX XX:XX:XX] [WARN] Login attempt 1 failed, retrying...
[2024-XX-XX XX:XX:XX] [INFO] Login attempt 2/3
[2024-XX-XX XX:XX:XX] [WARN] Login attempt 2 failed, retrying...
[2024-XX-XX XX:XX:XX] [INFO] Login attempt 3/3
[2024-XX-XX XX:XX:XX] [ERROR] All 3 login attempts failed
```

### Expected Artifacts
- **Error screenshots**: `login_failed_attempt_X_YYYYMMDD_HHMMSS.png`
- **HTML snapshots**: Page state on failures

### Cleanup
```powershell
# Restore valid credentials
set BULENOX_USERNAME=your_valid_username
set BULENOX_PASSWORD=your_valid_password
```

### Success Criteria
- ✅ 3 retry attempts executed
- ✅ Error screenshots captured
- ✅ Graceful failure handling
- ✅ Browser cleanup on failure

---

## Test Case 6: Full Trade Capture Integration

### Command
```powershell
python trae_trade_capture.py
```

### Expected Logs
```
[2024-XX-XX XX:XX:XX] [INFO] TradeBot Sentinel - Bulenox automation starting...
[2024-XX-XX XX:XX:XX] [INFO] Network interceptor attached
[2024-XX-XX XX:XX:XX] [INFO] Login successful - dashboard detected
[2024-XX-XX XX:XX:XX] [INFO] Trading interface detected
[2024-XX-XX XX:XX:XX] [INFO] Attempting to place test order...
[2024-XX-XX XX:XX:XX] [SUCCESS] Trade request detected and saved to trade.sh
[2024-XX-XX XX:XX:XX] [SUCCESS] Python code saved to trade_request_full.py
```

### Expected Artifacts
- **cURL file**: `trade.sh` (executable)
- **Python file**: `trade_request_full.py` (runnable)
- **Backup files**: `trade_YYYYMMDD_HHMMSS.sh`, `trade_request_full_YYYYMMDD_HHMMSS.py`

### Success Criteria
- ✅ Login integration successful
- ✅ Trading interface navigation
- ✅ Network request interception
- ✅ cURL command extraction
- ✅ Python code generation

---

## Test Case 7: Modal Handling Validation

### Command
```powershell
# Run during peak hours when modals are likely
python login_bulenox_playwright.py
```

### Expected Modal Scenarios
1. **Cookie Banner**: Automatically dismissed
2. **Time Sync Warning**: Detected and handled
3. **Terms Update**: Logged and attempted bypass

### Expected Logs (if modals appear)
```
[2024-XX-XX XX:XX:XX] [INFO] Cookie banner detected - dismissing...
[2024-XX-XX XX:XX:XX] [INFO] Time sync modal detected - handling...
[2024-XX-XX XX:XX:XX] [SUCCESS] Modal handled successfully
```

### Success Criteria
- ✅ Modal detection working
- ✅ Automatic dismissal
- ✅ Login continues after modal handling

---

## Test Case 8: Multi-Domain Fallback

### Command
```powershell
# Script will automatically attempt fallback domains
python login_bulenox_playwright.py
```

### Expected Domain Attempts (if primary fails)
1. `https://projectx.bulenox.com/` (primary)
2. `https://trade.bulenox.com/` (fallback 1)
3. `https://platform.bulenox.com/` (fallback 2)

### Expected Logs (if fallback needed)
```
[2024-XX-XX XX:XX:XX] [WARN] Primary domain failed, trying fallback...
[2024-XX-XX XX:XX:XX] [INFO] Attempting login on https://trade.bulenox.com/
[2024-XX-XX XX:XX:XX] [SUCCESS] Fallback domain successful
```

### Success Criteria
- ✅ Fallback domains attempted
- ✅ Clear logging of domain switches
- ✅ Screenshots of each domain attempt

---

## Performance Benchmarks

### Timing Expectations
- **Fresh Login**: 15-30 seconds
- **Session Reuse**: 3-8 seconds
- **Failed Login**: 45-60 seconds (with retries)
- **Trade Capture**: 60-120 seconds

### Resource Usage
- **Memory**: < 500MB peak
- **CPU**: < 50% during automation
- **Disk**: < 50MB for artifacts

---

## Troubleshooting Commands

### Debug Mode
```powershell
# Enable verbose logging
set PLAYWRIGHT_DEBUG=1
python login_bulenox_playwright.py
```

### Clear Session Cache
```powershell
# Remove old session files
del session_*.json
```

### Reset Browser State
```powershell
# Clear Playwright browser cache
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch().close(); p.stop()"
```

### Network Diagnostics
```powershell
# Test domain connectivity
ping projectx.bulenox.com
curl -I https://projectx.bulenox.com/
```

---

## Success Validation Checklist

### ✅ Core Functionality
- [ ] Fresh login completes successfully
- [ ] Session reuse works properly  
- [ ] Retries execute on failures
- [ ] Browser cleanup happens always

### ✅ Stealth & Security
- [ ] Stealth mode applies when available
- [ ] Graceful fallback without stealth
- [ ] Human-like interaction patterns
- [ ] No bot detection triggers

### ✅ Debugging & Monitoring
- [ ] Screenshots captured on failures
- [ ] HTML snapshots saved for analysis
- [ ] Clear logging throughout process
- [ ] Timestamped artifacts created

### ✅ Integration Features
- [ ] Trade interface navigation
- [ ] Network request interception
- [ ] cURL command generation
- [ ] Python code conversion

### ✅ Error Handling
- [ ] Invalid credentials handled gracefully
- [ ] Network failures retry properly
- [ ] Modal dismissal working
- [ ] Multi-domain fallback functional

---

## Next Phase Enhancement Roadmap

### Phase 1: Modal Handling Expansion
- Cookie consent automation
- Terms of service updates
- Account verification prompts
- Security warnings dismissal

### Phase 2: Multi-Domain Intelligence
- Dynamic domain discovery
- Health check integration
- Load balancing logic
- Failover notifications

### Phase 3: Advanced Trade Capture
- Multiple order types support
- Real-time position monitoring
- Risk management integration
- Portfolio synchronization

**STATUS**: ✅ **READY FOR AUTO-EXECUTABLE DEPLOYMENT**

---

*Generated by TRAE AI Trading Sentinel - TradeBot Sentinel Integration*  
*Last Updated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")*