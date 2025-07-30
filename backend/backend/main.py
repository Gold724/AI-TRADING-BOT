from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import json

# Executors
from executor_bulenox import BulenoxExecutor
# from executor_exness import ExnessExecutor  # If needed
# from executor_binance import BinanceExecutor  # If needed

app = Flask(__name__)
CORS(app)

# Health check
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.datetime.now().isoformat()}), 200

# Strategy listing (stubbed)
@app.route("/api/strategies", methods=["GET"])
def get_strategies():
    return jsonify({
        "strategies": [
            {"id": 1, "name": "Liquidity Sweep"},
            {"id": 2, "name": "FVG + OTE Combo"},
            {"id": 3, "name": "Volume Weighted Fibonacci"}
        ]
    })

# Trade execution route
@app.route("/api/trade", methods=["POST"])
def execute_trade():
    try:
        data = request.get_json()
        symbol = data.get("symbol")
        side = data.get("side")
        quantity = data.get("quantity")
        broker = data.get("broker", "bulenox")  # default broker
        stopLoss = data.get("stopLoss")
        takeProfit = data.get("takeProfit")

        if not all([symbol, side, quantity]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        signal = {"symbol": symbol, "side": side, "quantity": quantity}

        if broker == "bulenox":
            executor = BulenoxExecutor(signal=signal, stopLoss=stopLoss, takeProfit=takeProfit)
        # elif broker == "exness":
        #     executor = ExnessExecutor(signal=signal, stopLoss=stopLoss, takeProfit=takeProfit)
        # elif broker == "binance":
        #     executor = BinanceExecutor(signal=signal, stopLoss=stopLoss, takeProfit=takeProfit)
        else:
            return jsonify({"status": "error", "message": f"Unsupported broker: {broker}"}), 400

        success = executor.execute_trade()
        return jsonify({"status": "success" if success else "fail"}), 200 if success else 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Futures trade execution route
@app.route("/api/trade/futures", methods=["POST"])
def execute_futures_trade():
    try:
        data = request.get_json()
        symbol = data.get("symbol")  # Should be in futures format like 6EU25
        side = data.get("side")
        quantity = data.get("quantity")
        broker = data.get("broker", "bulenox")  # default broker for futures
        stopLoss = data.get("stopLoss")
        takeProfit = data.get("takeProfit")

        if not all([symbol, side, quantity]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Log the futures trade request
        print(f"Futures trade request: {symbol} {side} {quantity} via {broker}")

        signal = {"symbol": symbol, "side": side, "quantity": quantity}

        if broker == "bulenox":
            executor = BulenoxExecutor(signal=signal, stopLoss=stopLoss, takeProfit=takeProfit)
        else:
            return jsonify({"status": "error", "message": f"Unsupported broker for futures: {broker}"}), 400

        success = executor.execute_trade()
        return jsonify({"status": "success" if success else "fail"}), 200 if success else 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Trade history (if available)
@app.route("/api/trade/history", methods=["GET"])
def trade_history():
    try:
        with open("logs/bulenox_trades.json", "r") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    return jsonify({"trades": history}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
