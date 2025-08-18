# TradeBot Sentinel - Trade Endpoint Discovery System

🎯 **Objective**: Automatically capture all missing trade execution endpoints (70% of required cURLs) for complete VPS automation deployment.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies and setup browsers
python setup_discovery.py

# Configure credentials
cp .env.template .env
# Edit .env with your Bulenox credentials
```

### 2. Run Discovery
```bash
# Visible mode (recommended for first run)
python trade_endpoint_discovery.py --visible

# Headless mode (for automated runs)
python trade_endpoint_discovery.py --headless
```

### 3. Check Results
```bash
# View captured cURLs
ls logs/curls/

# View endpoint summary
cat logs/endpoints/discovery_summary.json

# View generated Python code
cat trade_request_full.py
```

## 📊 Current Status

### ✅ Already Captured (30%)
- **Authentication**: `login_auth.curl` - Login endpoint
- **Account Data**: `account_info.curl` - Layout/account information
- **Chart Data**: `trade.sh` - Chart data requests

### 🎯 Missing Endpoints (70% - TO BE CAPTURED)
- **ORDER Mode BUY**: Trade execution via ORDER interface
- **ORDER Mode SELL**: Trade execution via ORDER interface  
- **DOM Mode BUY**: Trade execution via DOM interface
- **DOM Mode SELL**: Trade execution via DOM interface
- **Order Cancellation**: Cancel existing trades/orders
- **Order Modification**: Modify existing orders
- **Position Management**: Real-time position data
- **Account Balance**: Live balance updates
- **P/L Data**: Realized/Unrealized P/L endpoints
- **Risk Management**: Risk calculation endpoints

## 🔧 How It Works

### Discovery Process
1. **Login**: Automatically logs into Bulenox platform
2. **Navigation**: Navigates to trading interface
3. **ORDER Mode**: Clicks BUY/SELL buttons in ORDER tab
4. **DOM Mode**: Clicks BUY/SELL buttons in DOM tab
5. **Management**: Attempts order cancellation and modification
6. **Capture**: Intercepts all POST/PUT/DELETE requests
7. **Save**: Saves each request as timestamped cURL file
8. **Convert**: Generates Python requests code

### Network Interception
- Monitors all requests to `userapi.bulenox.projectx.com`
- Captures POST, PUT, DELETE methods only
- Automatically categorizes by action type
- Saves complete cURL commands with headers
- Preserves JSON request bodies

### File Organization
```
logs/
├── curls/           # Captured cURL files
│   ├── 20240101_120000_order_buy_execution.curl
│   ├── 20240101_120030_order_sell_execution.curl
│   ├── 20240101_120100_dom_buy_execution.curl
│   └── ...
├── json/            # JSON request bodies
├── screenshots/     # Action screenshots
└── endpoints/       # Discovery summaries

trade_request_full.py  # Generated Python code
```

## 🎮 UI Selectors Used

### Login Interface
- **Username**: `#\:r34\:`
- **Password**: `#\:r35\:`
- **Login Button**: Complex CSS selector for login form

### Trading Interface
- **ORDER Tab**: `#orderCardTab`
- **DOM Tab**: `#domTab`
- **Symbol Inputs**: Different selectors for ORDER vs DOM
- **Amount Inputs**: Mode-specific amount fields

### Trade Execution Buttons
- **ORDER BUY**: Green button in ORDER tab
- **ORDER SELL**: Red button in ORDER tab
- **DOM BUY**: Green button in DOM tab
- **DOM SELL**: Red button in DOM tab

### Management Actions
- **Cancel Trade**: SVG button in positions table
- **Positions Tab**: Position management interface
- **Editable Fields**: Any modifiable order parameters

## 🛡️ Safety Features

### Robust Selector Handling
- **Retry Logic**: 3 attempts with 2-second delays
- **Fallback Selectors**: Multiple selector strategies
- **Error Screenshots**: Captures on failures
- **Graceful Degradation**: Continues on individual failures

### Network Safety
- **Request Filtering**: Only captures Bulenox API calls
- **Method Filtering**: Only POST/PUT/DELETE operations
- **Content Validation**: Validates trade-related content
- **Rate Limiting**: Built-in delays between actions

### Session Management
- **Persistent Context**: Maintains login session
- **Modal Handling**: Automatically handles popups
- **Time Sync**: Handles time synchronization warnings
- **Cleanup**: Proper browser cleanup on exit

## 📈 Expected Outcomes

After successful discovery, you should have:

### 🎯 Complete cURL Collection
- **10-15 new cURL files** covering all trade actions
- **Organized by timestamp and action type**
- **Ready for VPS deployment**

### 🐍 Python Integration Code
- **Auto-generated `trade_request_full.py`**
- **Methods for each captured action**
- **Ready-to-use trade execution functions**

### 📊 Deployment Readiness
- **100% endpoint coverage** (vs current 30%)
- **VPS-ready automation scripts**
- **Complete trade execution pipeline**

## 🔍 Troubleshooting

### Common Issues

#### Login Failures
```bash
# Check credentials
echo $BULENOX_USERNAME
echo $BULENOX_PASSWORD

# Run in visible mode to debug
python trade_endpoint_discovery.py --visible
```

#### Selector Not Found
- UI may have changed - check screenshots in `logs/screenshots/`
- Try running in visible mode to see current interface
- Update selectors in script if needed

#### No Requests Captured
- Ensure you're on correct trading page
- Check network connectivity
- Verify API endpoints haven't changed

#### Browser Issues
```bash
# Reinstall Playwright browsers
python -m playwright install chromium
python -m playwright install-deps
```

### Debug Mode
```bash
# Enable verbose logging
export VERBOSE_LOGGING=true
python trade_endpoint_discovery.py --visible

# Check logs
tail -f logs/trade_endpoint_discovery.log
```

## 🚀 VPS Deployment Pipeline

Once discovery is complete:

1. **Verify Captures**: Check `logs/endpoints/discovery_summary.json`
2. **Test Python Code**: Run `trade_request_full.py` locally
3. **Deploy to VPS**: Upload captured cURLs and Python code
4. **Configure Automation**: Set up scheduled trading
5. **Monitor Execution**: Track trade success rates

## 📋 Checklist

### Pre-Discovery
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Playwright browsers ready
- [ ] Network connectivity verified

### Post-Discovery
- [ ] All trade modes captured (ORDER + DOM)
- [ ] Both BUY and SELL endpoints captured
- [ ] Management actions captured
- [ ] Python code generated
- [ ] Summary report reviewed

### VPS Ready
- [ ] 70%+ endpoint coverage achieved
- [ ] cURL files validated
- [ ] Python integration tested
- [ ] Automation scripts prepared

## 🎉 Success Metrics

**Target**: Capture missing 70% of trade execution endpoints

**Success Criteria**:
- ✅ ORDER BUY/SELL endpoints captured
- ✅ DOM BUY/SELL endpoints captured  
- ✅ Order management endpoints captured
- ✅ Position data endpoints captured
- ✅ Python automation code generated
- ✅ VPS deployment ready

---

**Ready to capture the missing 70% of endpoints and complete your VPS trading automation!** 🚀