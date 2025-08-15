#!/bin/bash
# Script to activate the TRAE Adaptive Intelligence System

# Default values
MODE="full"
FORCE_REPORT=false
CONFIG_DIR="config"
DATA_DIR="data"

# Display help message
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -m, --mode MODE       Operation mode: initialize, evaluate, report, full (default: full)"
    echo "  -f, --force-report    Force report generation regardless of schedule"
    echo "  -c, --config-dir DIR  Directory containing configuration files (default: config)"
    echo "  -d, --data-dir DIR    Directory containing data files (default: data)"
    echo "  -h, --help            Display this help message"
    echo ""
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -f|--force-report)
            FORCE_REPORT=true
            shift
            ;;
        -c|--config-dir)
            CONFIG_DIR="$2"
            shift 2
            ;;
        -d|--data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
 done

# Validate mode
if [[ "$MODE" != "initialize" && "$MODE" != "evaluate" && "$MODE" != "report" && "$MODE" != "full" ]]; then
    echo "Error: Invalid mode '$MODE'. Must be one of: initialize, evaluate, report, full"
    exit 1
fi

# Ensure Python virtual environment is activated if it exists
if [ -d "venv" ]; then
    echo "Activating Python virtual environment..."
    source venv/bin/activate
fi

# Build command arguments
CMD_ARGS="--mode $MODE --config-dir $CONFIG_DIR --data-dir $DATA_DIR"

if [ "$FORCE_REPORT" = true ]; then
    CMD_ARGS="$CMD_ARGS --force-report"
fi

# Run the Python script
echo "=== TRAE Adaptive Intelligence System ==="
echo "Mode: $MODE"
echo "Force report: $FORCE_REPORT"
echo "Config directory: $CONFIG_DIR"
echo "Data directory: $DATA_DIR"
echo ""

echo "Executing: python activate_adaptive_intelligence.py $CMD_ARGS"
python activate_adaptive_intelligence.py $CMD_ARGS

# Check exit status
if [ $? -eq 0 ]; then
    echo "Adaptive Intelligence System execution completed successfully"
else
    echo "Error: Adaptive Intelligence System execution failed"
    exit 1
fi