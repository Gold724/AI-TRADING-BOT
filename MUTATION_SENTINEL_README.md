# O.R.I.G.I.N. Cloud Prime - Mutation Sentinel

## Overview

The Mutation Sentinel is a cloud-native architecture that evolves static trading logic into an intelligent, self-mutating, multi-broker AI infrastructure. This document provides an overview of the key components and how they work together.

## Core Components

### 1. Strategy Mutation & Version Control

The strategy mutation system allows for dynamic loading, modification, and tracking of trading strategies.

**Key Files:**
- `api_strategy_mutation.py`: API endpoints for strategy management
- `strategies/`: Directory containing strategy modules
- `strategy_history.json`: History of strategy mutations

**API Endpoints:**
- `/api/strategy/available`: List available strategies
- `/api/strategy/history`: View strategy mutation history
- `/api/strategy/mutate`: Update strategy parameters via JSON
- `/api/strategy/prompt`: Update strategy via natural language

### 2. Broker Scaling

The system supports trading across multiple brokers concurrently.

**Supported Brokers:**
- Bulenox
- Binance
- Exness

**Implementation:**
- Each broker has a dedicated executor class
- Trades are routed by `BROKER_ID` or `ACCOUNT_ID`
- Each broker instance maintains a unique `session_id`

### 3. Auto-Recovery Engine

The auto-recovery system monitors daemon health and automatically restarts failed sessions.

**Key Features:**
- Heartbeat monitoring
- Automatic session recovery
- Failure tracking and notifications
- Crash diagnostics with screenshots

**Implementation:**
- `auto_recovery.py`: Core recovery engine
- Configurable recovery parameters
- Thread-safe operation

### 4. Signal Broadcasting Layer

The broadcasting system distributes trading signals to multiple bots and accounts.

**Key Features:**
- Signal distribution to multiple endpoints
- Filtering capabilities
- Signal history tracking
- Comprehensive logging

**Implementation:**
- `broadcast.py`: Core broadcasting engine
- Thread-safe operation
- JSON persistence for signal history

### 5. Dashboard API

The dashboard API provides real-time monitoring of the trading system.

**Key Features:**
- System metrics (CPU, memory, disk usage)
- Trading metrics (active sessions, trade counts)
- Broker status monitoring
- Strategy information
- Signal processing metrics
- Health monitoring

**API Endpoints:**
- `/api/dashboard/status`: Overall system status
- `/api/dashboard/trading`: Trading metrics
- `/api/dashboard/brokers`: Broker status
- `/api/dashboard/strategies`: Strategy information
- `/api/dashboard/signals`: Signal metrics
- `/api/dashboard/health`: Health status
- `/api/dashboard/update`: Update dashboard data

### 6. JavaScript-Enhanced Selenium Integration

The JavaScript helper enhances Selenium capabilities for robust web automation.

**Key Features:**
- Stealth mode to avoid bot detection
- Advanced page ready detection
- State monitoring system
- Enhanced element interaction
- Network monitoring
- Console log capture

**Implementation:**
- `js_helper.py`: Core JavaScript helper

## Integration

All components are integrated through the main Flask application in `main.py`. The integration test script `test_integration.py` verifies that all components are working together correctly.

## Getting Started

1. Ensure all dependencies are installed:
   ```
   pip install -r requirements.txt
   ```

2. Start the backend server:
   ```
   cd backend
   python main.py
   ```

3. Start the frontend server:
   ```
   cd frontend
   npm run dev
   ```

4. Access the dashboard at http://localhost:5173/

## Testing

Run the integration test to verify all components are working correctly:

```
python test_integration.py
```

## Configuration

Configuration parameters can be adjusted in the following files:

- `auto_recovery.py`: Recovery parameters
- `broadcast.py`: Broadcasting parameters
- `api_dashboard.py`: Dashboard parameters
- `js_helper.py`: JavaScript helper parameters

## Security

The system implements several security measures:

- API key management for broker access
- Secure storage of credentials
- Session isolation for multi-broker operation
- Error handling to prevent sensitive information leakage

## Future Enhancements

1. Add support for additional brokers
2. Implement machine learning for strategy optimization
3. Enhance dashboard with real-time visualization
4. Add webhook support for external integrations
5. Implement advanced risk management features