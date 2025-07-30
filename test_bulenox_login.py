import os
import sys
import logging
from backend.executor_bulenox import BulenoxExecutor

# Configure logging to console for immediate feedback
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("BULENOX_TEST")

def main():
    """Test the BulenoxExecutor login functionality"""
    logger.info("Starting Bulenox login test")
    
    try:
        # Create executor instance
        executor = BulenoxExecutor()
        logger.info("BulenoxExecutor instance created successfully")
        
        # Run health check (which tests login)
        result = executor.health()
        
        if result:
            logger.info("[SUCCESS] CYPHER LOGIN TEST PASSED - Successfully logged in to Bulenox")
            return 0
        else:
            logger.error("[FAILED] CYPHER LOGIN TEST FAILED - Could not log in to Bulenox")
            return 1
            
    except Exception as e:
        logger.error(f"[ERROR] CYPHER LOGIN TEST ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())