# Bulenox Sentinel

A Linux-based headless Selenium automation agent for automated login and actions on the Bulenox trading platform.

## Features

- **Selenium Automation**: Uses undetected-chromedriver with adaptive stealth technology
- **Credential Management**: Rotates multiple pre-defined account credentials from JSON/CSV files
- **Login Automation**: Logs in to the target site and performs adaptive actions
- **Bot Detection Bypass**: Handles Cloudflare and other bot detection mechanisms
- **Auto-retry**: Automatically retries failed actions with different strategies
- **Remote Trigger**: Provides a Flask API endpoint for remote triggering

## Installation

### Prerequisites

- Python 3.10+
- Chrome browser
- Linux environment (for production deployment)

### Setup

1. Clone the repository to `/opt/bulenox`:

```bash
sudo mkdir -p /opt/bulenox
sudo chown $USER:$USER /opt/bulenox
git clone https://github.com/yourusername/bulenox-sentinel.git /opt/bulenox
cd /opt/bulenox
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:

```bash
cp .env.example .env
nano .env  # Edit with your credentials and settings
```

5. Create a credentials file (JSON or CSV):

```bash
cp credentials.json.example credentials.json
nano credentials.json  # Edit with your credentials
```

## Configuration

Edit the `.env` file to configure the following settings:

- `BROKER_URL`: The URL of the login page
- `BULENOX_USERNAME` / `BROKER_USERNAME`: Default username
- `BULENOX_PASSWORD` / `BROKER_PASSWORD`: Default password
- `CREDENTIALS_FILE`: Path to the credentials file (JSON or CSV)
- `MAX_RETRIES`: Maximum number of retry attempts
- `HEADLESS`: Whether to run in headless mode (true/false)
- `API_PORT`: Port for the Flask API endpoint

## Running as a Service

1. Copy the systemd service file:

```bash
sudo cp bulenox.service /etc/systemd/system/
```

2. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bulenox.service
sudo systemctl start bulenox.service
```

3. Check the service status:

```bash
sudo systemctl status bulenox.service
```

## API Usage

The Bulenox Sentinel provides a simple API endpoint for remote triggering:

```bash
curl -X POST http://localhost:8090/run -H "Content-Type: application/json" -d '{"headless": true}'
```

Response format:

```json
{
  "success": true,
  "message": "Automation completed successfully",
  "timestamp": "2025-08-10T14:02:09.570373"
}
```

## Logs

Logs are written to `/var/log/bulenox.log`. You can view them with:

```bash
tail -f /var/log/bulenox.log
```

## Troubleshooting

- **Login Failures**: Check the credentials in your `.env` file and credentials.json
- **Chrome Driver Issues**: Make sure Chrome is installed and up to date
- **Permission Issues**: Ensure the service is running as root or has appropriate permissions
- **API Connection Issues**: Check that the API port is not blocked by a firewall

## License

This project is licensed under the MIT License - see the LICENSE file for details.