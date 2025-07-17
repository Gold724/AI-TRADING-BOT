# Logic for executing trades

MAX_TRADES_PER_DAY = 12
executed_trades_today = 0

if executed_trades_today >= MAX_TRADES_PER_DAY:
    print("🔒 Trade limit reached. Skipping execution.")
else:
    print("✅ Ready to trade")