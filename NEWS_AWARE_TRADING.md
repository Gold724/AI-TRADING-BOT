# News-Aware Trading System for Trae Sentinel

## Overview

The News-Aware Trading System is an enhancement to the Trae AI Trading Sentinel that intelligently handles high-impact economic news events. It helps minimize risk and maximize opportunity by implementing several key features:

1. **News-Aware Filter (Risk Avoidance Logic)** - Avoids risky trades around high-impact economic news
2. **Dynamic Risk Allocation** - Auto-adjusts lot sizes based on news impact
3. **Automated Deployment** - Scheduled updates of economic calendar data

## Components

### Core Files

- `news_filter.py` - Main filter logic for news-aware trading
- `fetch_news.py` - API integration with Forex Factory to retrieve economic calendar data
- `data/banned_periods.json` - Storage for high-impact news event periods
- `data/forex_news.json` - Cached economic calendar data
- `sentinel_config.yml` - Configuration for news-aware features

### Automation Scripts

- `auto_news_cron.sh` - Daily cron job for Linux/macOS to fetch and update news data
- `auto_news_cron.ps1` - PowerShell script for Windows to fetch and update news data
- `setup_auto_scheduling.sh` - Setup script for Linux/macOS cron jobs
- `setup_auto_scheduling.ps1` - Setup script for Windows Task Scheduler
- `.github/workflows/news_aware_push.yml` - GitHub Actions workflow for daily updates

## Features

### 1. News-Aware Filter

The system blocks trade entries when:
- High-impact news is within ±30 minutes of the current time
- The news event relates to the currency pair being traded

```python
class NewsAwareFilter:
    def is_safe_to_trade(self, pair):
        # Checks if it's safe to trade based on upcoming news events
        # Returns False if high-impact news is within ±30 minutes
```

### 2. Dynamic Risk Allocation

Automatically adjusts position sizes based on news impact:

```python
def get_dynamic_lot_size(pair, base_lot):
    # Reduces position size based on news impact level
    # High impact: 25% of base lot
    # Medium impact: 50% of base lot
    # Low/No impact: 100% of base lot
```

### 3. Automated Deployment

The system includes scripts for:
- Daily fetching of economic calendar data
- Updating banned trading periods
- Sending notifications about upcoming high-impact events

## Setup Instructions

### Prerequisites

- Python 3.7+
- Required packages: `requests`, `beautifulsoup4`, `pytz`

### Installation

1. Ensure the required Python packages are installed:

```bash
pip install requests beautifulsoup4 pytz
```

2. Create necessary directories:

```bash
mkdir -p data logs
```

3. Set up automated scheduling:

**For Linux/macOS:**
```bash
chmod +x setup_auto_scheduling.sh
./setup_auto_scheduling.sh
```

**For Windows:**
```powershell
.\setup_auto_scheduling.ps1
```

### Configuration

Edit `sentinel_config.yml` to customize the news-aware trading behavior:

```yaml
news_aware_trading:
  enabled: true  # Master switch for news-aware features
  filtering:
    block_high_impact: true  # Block trades around high-impact news
    block_window_minutes: 30  # Time window to block trades
  risk_allocation:
    enabled: true  # Enable dynamic risk adjustment
```

## Usage

Once set up, the system will:

1. Automatically fetch economic calendar data daily
2. Block trades during high-impact news events
3. Adjust position sizes based on news impact
4. Send notifications about blocked trades and upcoming events

## Notifications

The system can send notifications via Slack or Telegram when:
- A trade is blocked due to news
- High-impact news events are upcoming
- Economic calendar data is updated

## Troubleshooting

- Check the log files in the `logs` directory for detailed information
- Ensure the `data` directory contains the latest `forex_news.json` and `banned_periods.json` files
- Verify that the scheduled tasks are running correctly

## License

This project is part of the Trae AI Trading Sentinel system.