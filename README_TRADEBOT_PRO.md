# TradeBot Sentinel Pro - Enhanced Trading Automation

## Overview

TradeBot Sentinel Pro is an enhanced version of the original TradeBot Sentinel, designed for automated interaction with Bulenox ProjectX's trading platform. This upgraded version includes advanced POST request capture, targeted trade detection, and improved retry logic.

## Key Features

### 🔐 Secure Authentication
- Environment variable-based credential management
- Robust login with fallback selectors
- Time sync warning modal handling
- Persistent Chrome context for reliable sessions

### 🕸️ Enhanced Network Interception
- **All POST Request Capture**: Every POST request is captured and saved to timestamped files in `/logs/curls/`
- **Targeted Trade Detection**: Dual-criteria system for identifying trade-specific requests:
  - URL pattern matching: `/trade`, `/orders`, `/execute`
  - JSON body keyword detection: `symbol`, `price`, `order`, `amount`
- **Automatic Conversion**: Trade requests are automatically converted to both cURL and Python formats

### 🔄 Retry Logic
- `waitForSelectorWithRetries()` helper function with configurable attempts and delays
- Robust element detection with multiple selector patterns
- Graceful failure handling with detailed logging

### 📊 Comprehensive Logging
- Structured logging with UTF-8 compatibility
- Trade detection log with timestamps and metadata
- Screenshot documentation at critical points
- Enhanced summary reports in JSON format

## Directory Structure

```
ai-trading-sentinel/
├── tradebot_sentinel_pro.py          # Main enhanced script
├── test_tradebot_pro_features.py     # Feature validation tests
├── logs/
│   ├── curls/                         # All POST requests (timestamped)
│   └── trade_detections.log           # Trade detection log
├── trade.sh                           # Latest trade request (cURL)
├── trade_request_full.py              # Latest trade request (Python)
└── trade_requests_summary_pro.json   # Enhanced summary report
```

## Prerequisites

### Required Environment Variables
```bash
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
BROKER_URL=https://bulenox.projectx.com/login  # Optional, defaults to this URL
```

### Python Dependencies
```bash
pip install playwright python-dotenv
python -m playwright install chromium

# Optional for enhanced cURL conversion
pip install curlconverter
```

## Usage

### Basic Execution
```bash
python tradebot_sentinel_pro.py
```

### Feature Testing
```bash
python test_tradebot_pro_features.py
```

## Enhanced Features in Detail

### 1. All POST Request Capture
- Every POST request is automatically saved to `/logs/curls/post_request_YYYYMMDD_HHMMSS_mmm.sh`
- Files contain complete cURL commands with headers and data
- Enables comprehensive request analysis and debugging

### 2. Targeted Trade Detection

#### URL Pattern Matching
- Detects URLs containing: `/trade`, `/orders`, `/execute`
- Case-insensitive matching
- Logs detected patterns for analysis

#### JSON Body Analysis
- Scans POST data for trading keywords: `symbol`, `price`, `order`, `amount`
- Works with both JSON objects and form data
- Records all detected keywords

#### Trade Request Processing
When a trade request is detected:
1. Saves cURL command to `trade.sh` (overwrites previous)
2. Converts to Python requests code in `trade_request_full.py`
3. Logs detection details to `/logs/trade_detections.log`
4. Increments detection counter

### 3. Retry Helper Function

```python
await waitForSelectorWithRetries(
    page, 
    selectors=['#btn1', '.btn2', 'button'], 
    retries=3, 
    delay=2000
)
```

- Attempts each selector in sequence
- Retries on failure with configurable delay
- Throws descriptive error if all attempts fail
- Used throughout the script for robust element detection

### 4. Enhanced Logging System

#### Trade Detection Log Format
```json
{
  "timestamp": "2025-08-13T12:18:15.998533",
  "url": "https://api.bulenox.projectx.com/trade/execute",
  "detected_keywords": ["symbol", "price"],
  "detected_url_patterns": ["/trade"],
  "curl_filename": "post_request_20250813_121815_998.sh",
  "trade_sh_updated": true,
  "detection_count": 1
}
```

#### Summary Report
- Total requests captured
- Trade detection count
- Complete request details
- File generation status

## Security Features

- No hardcoded credentials
- UTF-8 encoding without BOM
- Secure header handling
- Screenshot capture for debugging (no sensitive data)
- Proper resource cleanup

## Error Handling

- Graceful failure with detailed error messages
- Screenshot capture on critical failures
- Comprehensive exception logging
- Automatic browser cleanup

## Compatibility

- **OS**: Windows, macOS, Linux
- **Python**: 3.7+
- **Browser**: Chromium-based (via Playwright)
- **Encoding**: UTF-8 throughout

## Troubleshooting

### Common Issues

1. **Login Failures**
   - Check environment variables
   - Verify broker URL accessibility
   - Review login screenshots in project directory

2. **Element Detection Issues**
   - Increase retry count in `waitForSelectorWithRetries`
   - Add custom selectors to selector arrays
   - Check browser screenshots for UI changes

3. **Network Interception Problems**
   - Ensure proper browser context setup
   - Check `/logs/curls/` for captured requests
   - Verify POST request format in logs

### Debug Mode
- Script runs in visible browser mode by default
- Screenshots saved at critical points
- Comprehensive console logging
- 60-second manual inspection period

## Upgrade from Original Version

The Pro version maintains full compatibility with the original `tradebot_sentinel_fixed.py` while adding:

- ✅ Enhanced POST capture (all requests)
- ✅ Targeted trade detection with dual criteria
- ✅ Retry helper function implementation
- ✅ Structured logging system
- ✅ Directory organization
- ✅ Comprehensive testing suite

## Contributing

When contributing to TradeBot Sentinel Pro:

1. Maintain UTF-8 compatibility
2. Follow existing logging patterns
3. Add tests for new features
4. Update documentation
5. Ensure security best practices

## License

This project is for educational and automation purposes. Ensure compliance with your trading platform's terms of service.

---

**TradeBot Sentinel Pro** - Enhanced automation for professional trading workflows.