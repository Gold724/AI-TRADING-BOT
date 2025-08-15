#!/bin/bash

echo "🔍 Starting Full System Check (Linux) 🐧"

# Load environment variables
source .env

# Create logs directory
mkdir -p logs
mkdir -p screenshots

# 1. SSH into VPS and start the backend server
echo "🚀 Connecting to $VAST_INSTANCE_IP via SSH..."
ssh -i $SSH_KEY_PATH $SSH_USER@$VAST_INSTANCE_IP << EOF
  echo "🌐 Starting Flask API..."
  pkill -f cloud_main.py || true
  nohup python3 cloud_main.py > flask.log 2>&1 &
  sleep 5
  curl http://localhost:$FLASK_PORT/api/health || echo "❌ API failed to respond"
EOF

# 2. Trigger Stealth Trade
echo "📡 Triggering trade on /api/trade/stealth..."
curl -X POST http://$VAST_INSTANCE_IP:$FLASK_PORT/api/trade/stealth \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "GCZ25",
    "action": "buy",
    "lots": 1,
    "mode": "demo",
    "broker": "bulenox"
  }'

# 3. Fetch screenshot
echo "🖼️ Checking if screenshot saved..."
ssh -i $SSH_KEY_PATH $SSH_USER@$VAST_INSTANCE_IP "ls screenshots | tail -n 1"

echo "✅ All done."

exit 0