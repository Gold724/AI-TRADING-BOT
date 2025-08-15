# TRAE Phase 10: LiveOps Activation

## Overview

Phase 10 represents the transition of TRAE from development to full-time automated trading operations. This phase implements 24/7 deployment capabilities, multi-account support, governance enforcement, and passive learning mechanisms.

## Core Components

### 1. Automated Trading Loop

- **Signal Reception**: Receives trading signals from multiple sources (Trae.ai, Tremius, webhook, file drop)
- **Governance Validation**: Validates signals against internal rules, risk filters, and governance engine
- **Stealth Execution**: Uses StealthExecutor to login and execute trades on supported brokers
- **Position Management**: Sets or adjusts TP/SL visually post-entry
- **Logging**: Records trades and decisions in standardized format (JSON/CSV)

### 2. Persistent Deployment

- **24/7 Operation**: Runs continuously on Contabo VPS with restart resilience
- **Process Management**: Uses supervisor, PM2, or systemd for process monitoring
- **Version Control**: Syncs with GitHub repository for core logic and config updates
- **Security**: Secures credentials with .env or encrypted configurations

### 3. Multi-Account Support

- **Account Differentiation**: Supports multiple trading accounts using unique account_id logic
- **Per-Account Configuration**: Loads account-specific settings for lot size, broker, execution method, risk limits
- **Separate Logging**: Maintains separate logs for each account for auditing and replay

### 4. Governance Enforcement

- **Pre-Trade Checks**: Verifies compliance with daily max loss, time-of-day limits, and previous outcomes
- **Automatic Safeguards**: Locks account or halts trading if governance criteria are breached
- **Violation Reporting**: Reports violations via logs or webhook

### 5. Passive Learning (Phase 11 Preparation)

- **Signal Performance Tracking**: Records which signals result in stop-loss hits
- **Adaptive Filtering**: Scores signal types over time to create adaptive filters
- **Anomaly Detection**: Flags unusual patterns or repetitive failures for review

## Technical Context

- **Host**: Contabo VPS
- **Signal Sources**: Tremius / webhook / Trae.ai
- **Version Control**: GitHub (synced)
- **Brokers**: Exness, Bulenox (stealth mode enabled)
- **Local Path**: /home/trae/AI-Sentinel/
- **Runtime Command**: `python main.py` or via Flask + background poller

## Implementation Details

### Key Classes

1. **StealthExecutor**: Handles trade execution across different brokers
2. **AccountManager**: Manages multiple trading accounts and their configurations
3. **HeartbeatMonitor**: Ensures system is running continuously and can recover from failures
4. **WebhookHandler**: Receives trading signals via HTTP endpoints
5. **FileHandler**: Monitors directories for signal files
6. **SignalProcessor**: Processes and normalizes signals from different sources

### Deployment Options

1. **Supervisor**: Configuration in `deployment/supervisor_config.ini`
2. **Systemd**: Service file in `deployment/trae-sentinel.service`
3. **PM2**: Configuration in `deployment/ecosystem.config.js`

## Success Metrics

- **Uptime**: >99.9% system availability
- **Execution Speed**: <500ms from signal receipt to order placement
- **Governance Compliance**: 100% adherence to trading rules
- **Multi-Account Support**: Successful management of 5+ concurrent accounts
- **Error Recovery**: Automatic recovery from common failure modes

## Monitoring

- **Heartbeat System**: Regular status updates to verify system health
- **Log Rotation**: Prevents log files from growing too large
- **Performance Metrics**: Tracks execution times, memory usage, and CPU load
- **Alert System**: Notifies administrators of critical issues

## Completion Criteria

Phase 10 is considered complete when:

1. The system can run continuously for 7+ days without manual intervention
2. All governance rules are properly enforced across multiple accounts
3. Trade execution is reliable and consistent across supported brokers
4. Signal processing from all sources works correctly
5. Passive learning data collection is operational

## Activation Command

```
TRAE, begin LiveOps. Accept signal stream. Govern your actions. Execute with stealth. Track everything. Protect my equity.
```