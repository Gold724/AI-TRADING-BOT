#!/usr/bin/env python3

import traceback
from test_bulenox_demo import test_trading_configuration

if __name__ == "__main__":
    try:
        result = test_trading_configuration()
        print(f"Configuration test result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()