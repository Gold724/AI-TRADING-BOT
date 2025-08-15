# TRAE AI Trading Bot - Adaptive Intelligence System

## Overview

The Adaptive Intelligence System is a sophisticated component of the TRAE AI Trading Bot that enables continuous learning, strategy feedback, and LLM-enhanced decision logic. This system allows the bot to evolve its trading strategies over time, adapt to changing market conditions, and improve its performance through reinforcement learning.

## Core Components

### 1. Sentinel Decider (LLM-powered strategy validation)

The Sentinel Decider is an LLM-powered component that validates trading strategies based on multiple factors:

- Technical analysis confidence
- Psychological market factors
- News impact analysis
- Historical performance evaluation

Location: `ai_components/sentinel_decider_llm.py`

Key features:
- Multi-factor confidence scoring
- LLM prompt generation for trade analysis
- Strategy validation with configurable thresholds
- Performance tracking and statistics

### 2. Dynamic Risk Engine (evolves from trade history)

The Dynamic Risk Engine adjusts risk parameters based on historical trade performance and current market conditions:

- Adapts position sizing based on win/loss streaks
- Adjusts stop-loss and take-profit levels based on volatility
- Implements time-based risk adjustments (day of week, time of day)
- Tracks drawdown and adjusts risk accordingly

Location: `ai_components/dynamic_risk_engine.py`

Key features:
- Dynamic risk calculation based on multiple factors
- Risk configuration persistence
- Historical risk adjustment tracking
- Risk management reporting

### 3. Strategy Evolution (A/B testing, retiring poor strategies)

The Strategy Evolution system implements a genetic algorithm approach to evolve trading strategies:

- Creates variants of successful strategies
- Implements A/B testing to compare performance
- Retires poorly performing strategies
- Optimizes strategy parameters

Location: `ai_components/strategy_evolution.py`

Key features:
- Parameter mutation and optimization
- Performance-based strategy selection
- A/B testing framework
- Strategy retirement and promotion

### 4. Weekly AI Feedback Reports

The Weekly Report Generator creates comprehensive performance reports and distributes them via Slack and email:

- Performance summaries (win rates, profit factors, drawdowns)
- Strategy evolution updates
- Risk adjustment tracking
- News impact analysis
- AI-generated recommendations

Location: `ai_components/weekly_report_generator.py`

Key features:
- Configurable report frequency (daily, weekly, monthly)
- Multi-channel distribution (Slack, email)
- Comprehensive performance metrics
- AI-generated recommendations

## Continuous Learning Loop

The Adaptive Intelligence System implements a continuous learning loop:

1. **Evaluate**: Analyze trade performance, market conditions, and news impact
2. **Improve**: Adjust strategies, risk parameters, and decision thresholds
3. **Execute**: Apply improved strategies to new trading decisions
4. **Re-learn**: Collect new performance data and repeat the cycle

## Triggers

The system can be triggered in several ways:

### Time-based Triggers
- Daily evaluation (end of trading day)
- Weekly comprehensive review
- Monthly strategy optimization

### Signal-based Triggers
- After a specific number of trades
- After consecutive wins or losses
- When drawdown exceeds thresholds

### Manual Triggers
- Via GitHub repository updates
- Through CLI commands

## Setup and Configuration

### Systemd Auto-Start

The TRAE AI bot is configured to run as a systemd service for automatic startup:

```
[Unit]
Description=TRAE AI Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/AI-TRADING-BOT
ExecStart=/root/AI-TRADING-BOT/venv/bin/python main.py --auto
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
StandardOutput=append:/root/AI-TRADING-BOT/trae_output.log
StandardError=append:/root/AI-TRADING-BOT/trae_output.log
StartLimitIntervalSec=300
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
```

Installation commands:
```bash
sudo cp trae-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trae-bot
sudo systemctl start trae-bot
```

### Activating the Adaptive Intelligence System

The Adaptive Intelligence System can be activated using the provided scripts:

#### Linux/macOS

```bash
# Run with default settings (full mode)
./activate_adaptive_intelligence.sh

# Run in specific mode
./activate_adaptive_intelligence.sh --mode evaluate

# Force report generation
./activate_adaptive_intelligence.sh --mode report --force-report
```

#### Windows

```powershell
# Using PowerShell
.\activate_adaptive_intelligence.ps1 -mode evaluate

# Using batch file
activate_adaptive_intelligence.bat -mode report -forceReport
```

Available modes:
- `initialize`: Only set up the components without running evaluation
- `evaluate`: Run strategy evaluation and risk adjustment
- `report`: Generate and send reports
- `full`: Run all steps (default)

### Scheduling Automated Execution

To ensure continuous learning and adaptation, the Adaptive Intelligence System should be scheduled to run automatically at regular intervals.

#### Linux/macOS (Cron Jobs)

Use the provided script to set up cron jobs:

```bash
./setup_adaptive_intelligence_cron.sh
```

This will create the following cron jobs:
- **Daily Evaluation**: Runs at 00:15 every day
- **Weekly Report**: Runs at 01:00 every Sunday
- **Monthly Full Run**: Runs at 02:00 on the 1st of each month

#### Windows (Task Scheduler)

Use the provided PowerShell script to set up scheduled tasks:

```powershell
.\setup_adaptive_intelligence_tasks.ps1
```

## Deployment

The TRAE AI Trading Bot with Adaptive Intelligence can be deployed using the provided deployment scripts.

### Linux Deployment

For Linux servers, use the deployment script to automate the setup process:

```bash
# Run as root
sudo ./deploy_adaptive_intelligence.sh
```

This script will:
1. Copy the trae-bot.service file to /etc/systemd/system/
2. Reload the systemd daemon
3. Enable the trae-bot service
4. Start the trae-bot service
5. Set up the cron jobs for Adaptive Intelligence

### Windows Deployment

For Windows systems, use the provided batch file (run as administrator):

```
deploy_adaptive_intelligence.bat
```

Alternatively, you can run the PowerShell script directly:

```powershell
# Run as administrator
.\deploy_adaptive_intelligence.ps1
```

The Windows deployment script will:
1. Check for Python installation
2. Activate the virtual environment if present
3. Set up scheduled tasks for Adaptive Intelligence
4. Test the Adaptive Intelligence activation
5. Verify the deployment

This will create the following scheduled tasks:
- **TRAE_AdaptiveIntelligence_Daily**: Runs at 00:15 every day
- **TRAE_AdaptiveIntelligence_Weekly**: Runs at 01:00 every Sunday
- **TRAE_AdaptiveIntelligence_Monthly**: Runs at 02:00 on the 1st of each month

### Monitoring

To monitor the TRAE AI bot:

1. Check service status:
   ```bash
   systemctl status trae-bot
   ```

2. View real-time logs:
   ```bash
   tail -f /root/AI-TRADING-BOT/trae_output.log
   ```

3. Validate auto-recovery by rebooting the VPS and confirming the bot restarts automatically.

4. Confirm that auto trade decisions reflect the strategy and risk engine logic by reviewing the logs and weekly reports.

## Configuration Files

The Adaptive Intelligence System uses several configuration files:

- `config/sentinel_config.json`: Configuration for the Sentinel Decider
- `config/risk_config.json`: Configuration for the Dynamic Risk Engine
- `config/strategy_config.json`: Configuration for the Strategy Evolution system
- `config/report_config.json`: Configuration for the Weekly Report Generator

## Integration

The Adaptive Intelligence System integrates with the core TRAE AI Trading Bot through the following interfaces:

1. The Sentinel Decider provides confidence scores for trading decisions
2. The Dynamic Risk Engine adjusts risk parameters for trade execution
3. The Strategy Evolution system updates strategy parameters
4. The Weekly Report Generator provides feedback to traders and developers

## Future Enhancements

Planned enhancements for the Adaptive Intelligence System include:

1. Integration with external market data sources
2. Enhanced natural language processing for news analysis
3. Advanced machine learning models for pattern recognition
4. Real-time strategy adaptation based on market conditions
5. Multi-market correlation analysis