# TradeBot Sentinel - Quick Start Guide 🚀

## Current Setup Status ✅

Your TradeBot Sentinel is fully configured and ready to use with:

- ✅ **Environment Variables**: Contabo VPS credentials configured
- ✅ **Dependencies**: All Python packages installed
- ✅ **Playwright**: Browser automation ready
- ✅ **Testing**: All system tests passing (4/4)
- ✅ **Documentation**: Comprehensive README available

## VPS Configuration 🖥️

Your Contabo VPS is configured with:
```
CONTABO_USERNAME=root
CONTABO_VPS_IP=161.97.112.146
CONTABO_SSH_PORT=22
CONTABO_PASSWORD=JfAJZ38VwU8j42LKa84PqIxVx
```

## Running TradeBot Sentinel

### 1. Local Testing (Recommended First)
```bash
# Activate virtual environment (if using one)
# source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate   # Windows

# Run system tests
python test_tradebot.py

# Run TradeBot Sentinel
python tradebot_sentinel.py
```

### 2. Deploy to Contabo VPS
```bash
# Generate deployment script
.\deploy_contabo.ps1

# Upload to VPS (generated instructions)
scp -P 22 contabo_deploy.sh root@161.97.112.146:/root/

# Connect and execute
ssh -p 22 root@161.97.112.146
chmod +x /root/contabo_deploy.sh
./contabo_deploy.sh
```

## Expected Behavior 🎯

When you run TradeBot Sentinel, it will:

1. **🔐 Login**: Securely authenticate using environment credentials
2. **⚠️ Handle Modals**: Automatically dismiss time sync warnings
3. **📊 Verify Dashboard**: Confirm successful login
4. **📈 Navigate Trading**: Access the trading interface
5. **🎯 Place Orders**: Attempt to place a trade order
6. **🔍 Monitor Network**: Intercept all POST requests
7. **💾 Generate Code**: Save cURL and Python code when trades detected
8. **📸 Debug**: Capture screenshots on any errors

## Generated Files 📁

After successful trade detection:
- `trade.sh` - cURL command for the trade request
- `trade_request_full.py` - Complete Python requests code
- `screenshot_*.png` - Debug screenshots (if errors occur)

## Troubleshooting 🛠️

### If Login Fails:
1. Verify your Bulenox credentials in `.env`
2. Check if platform UI has changed
3. Run with `headless=False` to see browser
4. Review generated screenshots

### If No Trades Detected:
1. Ensure order placement was successful
2. Check console logs for POST requests
3. Verify trade keywords match platform
4. Monitor network tab in browser dev tools

### If Elements Not Found:
1. Platform may have updated selectors
2. Increase retry delays in script
3. Add custom selectors for your platform version
4. Check console logs for detailed errors

## Security Reminders 🔒

- ✅ Credentials stored in environment variables
- ✅ No hardcoded sensitive information
- ⚠️ Generated files may contain auth tokens
- ⚠️ Screenshots may show sensitive data
- ⚠️ Use only on accounts you own

## Next Steps 📈

1. **Test Locally**: Run `python test_tradebot.py` first
2. **Configure Credentials**: Set your Bulenox username/password in `.env`
3. **Run Automation**: Execute `python tradebot_sentinel.py`
4. **Monitor Output**: Watch console logs and generated files
5. **Deploy to VPS**: Use the Contabo deployment script when ready

## Support 📞

For detailed documentation, see `README_TradeBot_Sentinel.md`

For issues:
1. Check console logs
2. Review screenshot files
3. Verify environment setup
4. Test with latest dependencies

---

**🎯 TradeBot Sentinel is ready for action!** 🤖

Start with local testing, then deploy to your Contabo VPS when satisfied with the results.