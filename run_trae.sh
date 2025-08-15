#!/bin/bash
# run_trae.sh
# Bash script to run the TRAE AI Trading System

# Default values
ENVIRONMENT="development"
BROKER="mock"
SKIP_TEST=false
CONFIG_PATH="config/deploy_config.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --broker)
      BROKER="$2"
      shift 2
      ;;
    --skip-test)
      SKIP_TEST=true
      shift
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Display banner
echo ""
echo "==============================================="
echo "         TRAE AI TRADING SYSTEM"
echo "==============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Python detected: $PYTHON_VERSION"

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import pandas, numpy, matplotlib, streamlit" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies."
        exit 1
    fi
    echo "Dependencies installed successfully."
else
    echo "Dependencies already installed."
fi

# Build command arguments
COMMAND="python3 deploy.py --environment $ENVIRONMENT --broker $BROKER --config $CONFIG_PATH"
if [ "$SKIP_TEST" = true ]; then
    COMMAND="$COMMAND --skip-test"
fi

# Display configuration
echo ""
echo "Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Broker: $BROKER"
echo "  Config Path: $CONFIG_PATH"
echo "  Skip Test: $SKIP_TEST"
echo ""

# Run the deployment script
echo "Starting TRAE AI Trading System..."
echo ""

# Execute the command
eval $COMMAND