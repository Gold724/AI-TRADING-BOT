# AI Trading Sentinel - Storage Configuration
import os
from pathlib import Path

# Set storage paths
TRAE_DATA_DIR = Path("D:/trae-data")
TRAE_LOGS_DIR = Path("E:/trae-logs")
TRAE_CACHE_DIR = Path("D:/trae-data/cache")
TRAE_DOWNLOADS_DIR = Path("D:/trae-downloads")

# Create directories if they don't exist
for directory in [TRAE_DATA_DIR, TRAE_LOGS_DIR, TRAE_CACHE_DIR, TRAE_DOWNLOADS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configure logging to use E: drive
import logging
logging.basicConfig(
    filename=TRAE_LOGS_DIR / "trading_sentinel.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Export paths for use in other modules
os.environ['TRAE_DATA_DIR'] = str(TRAE_DATA_DIR)
os.environ['TRAE_LOGS_DIR'] = str(TRAE_LOGS_DIR)
os.environ['TRAE_CACHE_DIR'] = str(TRAE_CACHE_DIR)
os.environ['TRAE_DOWNLOADS_DIR'] = str(TRAE_DOWNLOADS_DIR)