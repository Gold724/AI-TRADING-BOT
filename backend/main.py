import os

try:
    from executor_binance import BinanceExecutor
except ImportError:
    BinanceExecutor = None

try:
    from executor_exness import ExecutorExness
except ImportError:
    ExecutorExness = None

from flask import Flask, jsonify, request, session
from flask_cors import CORS

try:
    from executor_bulenox import ExecutorBulenox
except ImportError:
    ExecutorBulenox = None

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = "your-secret-key"  # Replace with a secure random key
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

from .auth import login, login_required, logout

# Initialize executors
binance_executor = BinanceExecutor() if BinanceExecutor else None
exness_executor = ExecutorExness() if ExecutorExness else None
bulenox_executor = ExecutorBulenox() if ExecutorBulenox else None

import datetime

STRATEGIES_DIR = os.path.join(os.path.dirname(__file__), "strategies")

from strategies.quantconnect_strategy import BasicTemplateAlgorithm

# Add a dictionary to map strategy names to classes
strategy_classes = {"quantconnect_strategy.py": BasicTemplateAlgorithm}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# Load strategy files from /strategies/
def list_strategies():
    strategies = []
    if os.path.exists(STRATEGIES_DIR):
        for filename in os.listdir(STRATEGIES_DIR):
            if (
                filename.endswith(".json")
                or filename.endswith(".yaml")
                or filename.endswith(".py")
            ):
                strategies.append(filename)
    return strategies


# Dummy data for signals
signals = [
    {
        "timestamp": "2023-01-01T00:00:00",
        "confidence": 75,
        "direction": "BUY",
        "asset": "BTCUSD",
    }
]


@app.route("/")
def index():
    return jsonify({"status": "success", "message": "AI Trading Sentinel API is running"})


@app.route("/api/login", methods=["POST"])
def handle_login():
    return login()


@app.route("/api/logout", methods=["POST"])
def handle_logout():
    return logout()


@app.route("/api/strategies", methods=["GET"])
@login_required
def get_strategies():
    strategies = list_strategies()
    return jsonify({"strategies": strategies})


@app.route("/api/simulate", methods=["POST"])
@login_required
def simulate_strategy():
    data = request.json
    strategy_name = data.get("strategy_name")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if not strategy_name or not start_date_str or not end_date_str:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        import datetime

        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format, expected YYYY-MM-DD"}), 400

    if strategy_name not in list_strategies():
        return jsonify({"error": "Strategy not found"}), 404

    if strategy_name in strategy_classes:
        StrategyClass = strategy_classes[strategy_name]
        # Instantiate and run the strategy simulation here
        # For now, return a mock response
        simulation_result = {
            "strategy": strategy_name,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "signals": [
                {
                    "timestamp": "2023-01-01T10:00:00",
                    "symbol": "BTCUSD",
                    "side": "buy",
                    "price": 20000,
                    "quantity": 0.1,
                },
                {
                    "timestamp": "2023-01-02T15:30:00",
                    "symbol": "BTCUSD",
                    "side": "sell",
                    "price": 21000,
                    "quantity": 0.1,
                },
            ],
            "pnl_summary": {
                "total_trades": 2,
                "winning_trades": 1,
                "losing_trades": 1,
                "net_profit": 1000,
            },
        }
        return jsonify(simulation_result)

    # For other strategies, return mock data
    simulation_result = {
        "strategy": strategy_name,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "signals": [
            {
                "timestamp": "2023-01-01T10:00:00",
                "symbol": "BTCUSD",
                "side": "buy",
                "price": 20000,
                "quantity": 0.1,
            },
            {
                "timestamp": "2023-01-02T15:30:00",
                "symbol": "BTCUSD",
                "side": "sell",
                "price": 21000,
                "quantity": 0.1,
            },
        ],
        "pnl_summary": {
            "total_trades": 2,
            "winning_trades": 1,
            "losing_trades": 1,
            "net_profit": 1000,
        },
    }

    return jsonify(simulation_result)


@app.route("/api/signal")
def get_signal():
    return jsonify(signals[-1])


@app.route("/api/signal/stats")
def get_signal_stats():
    total_signals = len(signals)
    # Safely calculate average confidence, handling missing confidence fields
    signals_with_confidence = [s.get("confidence", 0) for s in signals if "confidence" in s]
    avg_confidence = (
        sum(signals_with_confidence) / len(signals_with_confidence)
        if signals_with_confidence
        else 0
    )
    return jsonify(
        {
            "totalSignals": total_signals,
            "averageConfidence": avg_confidence,
            "history": signals,
        }
    )


@app.route("/api/signal/export", methods=["POST"])
def export_signal():
    # Implement export and webhook test logic here
    return jsonify(
        {"status": "success", "message": "Signal exported and webhook tested."}
    )


@app.route("/api/trade/binance", methods=["POST"])
def trigger_binance_trade():
    signal = request.json
    if not signal:
        return jsonify({"status": "error", "message": "No signal data provided."}), 400
    try:
        trade_result = binance_executor.execute_trade_from_signal(signal)
        if trade_result:
            # Log trade to signals history
            signals.append(
                {
                    "timestamp": trade_result.get("timestamp", ""),
                    "confidence": signal.get("confidence", 0),
                    "direction": signal.get("side", ""),
                    "asset": signal.get("symbol", ""),
                }
            )
            return jsonify(
                {
                    "status": "success",
                    "message": "Trade executed successfully.",
                    "trade": trade_result,
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Trade not executed due to low confidence or other reasons.",
                    }
                ),
                400,
            )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


import datetime
import importlib
import json
import os

import requests


@app.route("/api/trade", methods=["POST"])
def trigger_trade():
    data = request.json
    broker = data.get("broker")
    signal = data.get("signal")
    if not broker or not signal:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Broker and signal data must be provided.",
                }
            ),
            400,
        )
    try:
        module_name = f"executor_{broker}"
        if broker == "exness":
            class_name = "ExecutorExness"
        else:
            class_name = (
                "".join([part.capitalize() for part in broker.split("_")]) + "Executor"
            )
        executor_module = importlib.import_module(module_name)
        ExecutorClass = getattr(executor_module, class_name)

        stop_loss = signal.get("stopLoss")
        take_profit = signal.get("takeProfit")

        executor_instance = ExecutorClass(
            signal=signal, stopLoss=stop_loss, takeProfit=take_profit
        )

        trade_result = executor_instance.execute_trade()

        trade_log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "broker": broker,
            "symbol": signal.get("symbol"),
            "side": signal.get("side"),
            "quantity": signal.get("quantity"),
            "stopLoss": stop_loss,
            "takeProfit": take_profit,
            "status": "success" if trade_result else "failed",
        }

        signals.append(trade_log_entry)

        log_file = f"logs/{broker}_trades.json"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                history = json.load(f)
        else:
            history = []
        history.append(trade_log_entry)
        with open(log_file, "w") as f:
            json.dump(history, f, indent=2)

        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_token and telegram_chat_id:
            message = f"Trade executed on {broker}: {signal.get('side')} {signal.get('quantity')} {signal.get('symbol')}"
            if stop_loss:
                message += f", Stop Loss: {stop_loss}"
            if take_profit:
                message += f", Take Profit: {take_profit}"
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {"chat_id": telegram_chat_id, "text": message}
            try:
                requests.post(url, json=payload)
            except Exception as e:
                print(f"Failed to send Telegram alert: {e}")

        if trade_result:
            return jsonify(
                {"status": "success", "message": "Trade executed successfully."}
            )
        else:
            return (
                jsonify({"status": "failed", "message": "Trade execution failed."}),
                500,
            )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/trade/history", methods=["GET"])
def get_trade_history():
    broker = request.args.get("broker")
    if not broker:
        return (
            jsonify({"status": "error", "message": "Broker parameter is required."}),
            400,
        )
    log_file = f"logs/{broker}_trades.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    return jsonify({"status": "success", "history": history})


@app.route("/api/health/broker/<broker>", methods=["GET"])
def broker_health_check(broker):
    try:
        module_name = f"executor_{broker}"
        class_name = (
            "".join([part.capitalize() for part in broker.split("_")]) + "Executor"
        )
        executor_module = importlib.import_module(module_name)
        ExecutorClass = getattr(executor_module, class_name)
        executor_instance = ExecutorClass()
        health_status = executor_instance.health()
        return jsonify(health_status)
    except Exception as e:
        return jsonify({"status": "error", "details": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
