# AI Trading Sentinel - Bulenox Edition

## Overview

The AI Trading Sentinel for Bulenox is a stealth trading execution system that connects to Bulenox (ProjectX) using undetected-chromedriver with profile switching capabilities. This system provides a reliable way to execute trades on Bulenox with anti-detection features.

## Features

- **Stealth Login**: Uses undetected-chromedriver with Chrome profile switching
- **Profile Rotation**: Supports profiles 13-15 with fallback mechanisms
- **Retry Logic**: Implements intelligent retry and fallback XPath selectors
- **Strategic Screenshots**: Captures key moments for debugging
- **Heartbeat Monitoring**: Logs successful login status to dashboard
- **API-Driven**: RESTful API for trade execution
- **Docker Support**: Ready for cloud deployment
- **Multiple Account Sessions**: Supports session relays

## Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
   cd ai-trading-sentinel
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your credentials:
   ```
   BULENOX_USERNAME=your_username
   BULENOX_PASSWORD=your_password
   API_KEY=your_secure_api_key
   BULENOX_PROFILE_PATH=C:\Users\Admin\AppData\Local\Google\Chrome\User Data
   BULENOX_PROFILE_NAME=Profile 13
   ```

4. Run the application:
   ```bash
   python bulenox_trade_sentinel.py
   ```

### Docker Setup

1. Build and run with Docker Compose:
   ```bash
   docker-compose up -d bulenox-trade-sentinel
   ```

### VPS Deployment

1. SSH into your VPS:
   ```bash
   ssh root@your_vps_ip
   ```

2. Install dependencies:
   ```bash
   sudo apt update && sudo apt install git python3-pip supervisor unzip -y
   ```

3. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
   cd ai-trading-sentinel
   ```

4. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

5. Create a `.env` file with your credentials:
   ```
   BULENOX_USERNAME=your_username
   BULENOX_PASSWORD=your_password
   API_KEY=your_secure_api_key
   BULENOX_PROFILE_PATH=/root/.config/google-chrome
   BULENOX_PROFILE_NAME=Default
   ```

6. Set up Supervisor:
   ```bash
   sudo cp trae-sentinel.conf /etc/supervisor/conf.d/
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start trae-sentinel
   ```

## API Usage

### Health Check

```bash
curl -X GET http://localhost:5000/api/health
```

### Login

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"debug": true}'
```

### Execute Trade

```bash
curl -X POST http://localhost:5000/api/trade \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "direction": "buy",
    "quantity": 0.01,
    "tp": 1.0800,
    "sl": 1.0700,
    "debug": true
  }'
```

### Logout

```bash
curl -X POST http://localhost:5000/api/logout \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Dreamer Mode (Simulation)

To enable simulation mode without executing real trades, set `DREAMER_MODE=True` in your `.env` file.

## Monitoring

Check the logs directory for detailed logs and screenshots:

```
logs/
├── heartbeat_status.txt  # Current system status
├── trade_history.json    # History of executed trades
└── screenshots/          # Screenshots of trade execution
```

## Security Notes

- Always use a secure API key
- Store credentials securely in the `.env` file
- Consider using environment variables for sensitive information
- Restrict API access to trusted IPs

## Troubleshooting

- **Chrome Profile Issues**: Ensure the Chrome profile path exists and is accessible
- **Login Failures**: Check credentials and try a different profile
- **Trade Execution Errors**: Check the logs and screenshots for details

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.