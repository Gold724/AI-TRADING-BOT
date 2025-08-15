# TRAE Phase 10: LiveOps Activation

## Goals

- Transition TRAE from development to full-time automated trading operations
- Implement 24/7 resilient deployment on Contabo VPS with GitHub sync
- Support multiple trading accounts with differentiated configurations
- Enforce governance rules with automatic safeguards
- Begin passive learning for signal quality assessment

## System Instructions

### Sentinel LiveOps Activation

```
trigger: sentinel_decider.py
mode: liveops
parameters:
  automated_trade_loop: true
  persistent_deployment: true
  multi_account_support: true
  governance_enforcement: true
  passive_learning: true
```

### Automated Trade Loop

- Poll or receive signals from multiple sources (Trae.ai, Tremius, webhook, file drop)
- Validate signals against internal rules, risk filters, and governance engine
- Use StealthExecutor to login and execute trades on all supported brokers
- Set or adjust TP/SL visually post-entry using drag logic
- Log all trades and decisions in standardized format (JSON/CSV/local DB)

### Persistent Deployment

- Run TRAE 24/7 on Contabo VPS with restart resilience
- Use supervisor, pm2, or systemd for process management
- Sync core logic and config updates via GitHub repository
- Secure credentials and execution logic with .env or encrypted configs
- Implement heartbeat monitoring with auto-recovery

### Account Differentiation

- Support multiple accounts (funded or cash-based) using unique account_id logic
- Load per-account configurations:
  - Lot size and position sizing
  - Broker selection and credentials
  - Execution method preferences
  - Risk limits and drawdown thresholds
- Log each account separately for auditing and performance tracking

### Governance Enforcement

- Check all trades against:
  - Daily maximum loss limits
  - Time-of-day trading restrictions
  - Previous outcome patterns
  - Risk exposure thresholds
- Automatically lock account or halt trading if governance criteria are breached
- Report violations via log files or webhook notifications
- Require governance vote for resuming locked accounts

### Intelligence Extension

- Begin passive learning of which signals result in stop losses
- Score each signal type over time to create adaptive filters
- Flag anomalies or repetitive failure patterns for review
- Prepare data structures for Phase 11 advanced learning

## Technical Context

- **Host**: Contabo VPS
- **Signal Source**: Tremius / webhook / Trae.ai
- **Version Control**: GitHub (synced)
- **Brokers**: Exness, Bulenox (stealth mode enabled)
- **Local Path**: /home/trae/AI-Sentinel/
- **Runtime Command**: python main.py or via Flask + background poller

## Success Metrics

- System uptime exceeds 99.5% over 30-day period
- All trades are properly logged with complete execution details
- Account-specific configurations correctly applied to each trade
- Governance rules successfully prevent trading violations
- Signal quality metrics begin to show meaningful patterns

## Monitoring

- `/logs/liveops/uptime.log`
- `/logs/liveops/trades_{account_id}.json`
- `/logs/liveops/signals_quality.json`
- `/logs/governance/violations.json`
- Slack/Telegram notifications for critical events

## Completion Criteria

- Successful execution of trades across multiple accounts
- Proper handling of broker login and trade execution
- Governance rules correctly enforced with violation handling
- System recovery from simulated failures
- Initial signal quality metrics collected and analyzed