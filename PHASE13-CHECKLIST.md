# Phase 13: Bulenox AI Bot Testing & Cloud Deployment Checklist

## Local Testing

- [ ] Verify `bulenox_trade_sentinel.py` Flask app is working
  - [ ] Confirm `/api/trade/stealth` route exists and functions properly
  - [ ] Verify `StealthExecutor` class is properly integrated

- [ ] Confirm Chrome profile configuration
  - [ ] Local path: `C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Profile 13`
  - [ ] Verify profile contains saved Bulenox credentials

- [ ] Test local execution
  - [ ] Start Flask app: `python bulenox_trade_sentinel.py`
  - [ ] Send test signal: `curl -X POST http://127.0.0.1:5000/api/trade/stealth`
  - [ ] Verify Chrome launches and logs in successfully
  - [ ] Confirm trade execution or simulation
  - [ ] Check logs and screenshots for proper recording

## VPS Deployment

- [ ] SSH into VPS using Termius
  - [ ] Connect to: `ssh root@your_vps_ip`

- [ ] Install dependencies
  - [ ] Run: `sudo apt update && sudo apt install git python3-pip supervisor unzip -y`
  - [ ] Install Python packages: `pip3 install flask undetected-chromedriver`

- [ ] Clone repository
  - [ ] Run: `git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git`
  - [ ] Navigate to directory: `cd ai-trading-sentinel`

- [ ] Update Chrome profile paths for VPS
  - [ ] Set path to: `/root/.config/google-chrome`
  - [ ] Set profile to: `Default`

- [ ] Test VPS execution
  - [ ] Run: `python3 bulenox_trade_sentinel.py`
  - [ ] Test API: `curl -X POST http://YOUR_VPS_IP:5000/api/trade/stealth`

## Supervisor Configuration

- [ ] Create supervisor config
  - [ ] Copy `trae-sentinel.conf` to `/etc/supervisor/conf.d/`
  - [ ] Verify config contains correct paths and environment variables

- [ ] Enable and start service
  - [ ] Run: `supervisorctl reread`
  - [ ] Run: `supervisorctl update`
  - [ ] Run: `supervisorctl start trae-sentinel`

- [ ] Verify service is running
  - [ ] Check status: `supervisorctl status trae-sentinel`
  - [ ] Test API endpoint again

## API Security

- [ ] Implement API key authentication
  - [ ] Verify `check_api_key()` function is working
  - [ ] Test with: `curl -X POST http://YOUR_VPS_IP:5000/api/trade/stealth -H "Authorization: Bearer YOUR_API_KEY"`

## Optional: Dreamer Mode

- [ ] Test simulation mode
  - [ ] Set `DREAMER_MODE=True` in `.env`
  - [ ] Verify trade simulation works without executing real trades

## Persistence Verification

- [ ] Test system after terminal disconnect
  - [ ] Close Termius connection
  - [ ] Test API endpoint again
  - [ ] Verify system still responds and functions

## Docker Deployment (Optional)

- [ ] Test Docker deployment
  - [ ] Build and run with Docker Compose: `docker-compose up -d bulenox-trade-sentinel`
  - [ ] Verify container is running: `docker ps`
  - [ ] Test API endpoint

## Final Verification

- [ ] Create comprehensive test report
  - [ ] Document all test results
  - [ ] Note any issues or improvements
  - [ ] Capture screenshots of successful operations

- [ ] Update documentation
  - [ ] Ensure README is up to date
  - [ ] Document API endpoints and usage
  - [ ] Document deployment process

## Notes

- Chrome Profile: `C:\Users\Admin\...\Profile 13` (Local) / `/root/.config/google-chrome` (VPS)
- Flask Route: `/api/trade/stealth`
- Main Scripts: `bulenox_trade_sentinel.py`, `stealth_executor.py`
- VPS Autostart: via supervisor
- Remote API Access: via curl or webhook with API key