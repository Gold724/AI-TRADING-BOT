@echo off
echo AI Trading Sentinel - Test Suite
echo ==============================
echo.

echo Starting Flask backend server...
start cmd /k "cd backend && python main.py"

echo Waiting for server to start...
timeout /t 5 /nobreak

echo.
echo Running Selenium login test...
python test_bulenox_selenium.py

echo.
echo Running futures trading UI test...
python test_bulenox_futures.py

echo.
echo Running API futures trade test...
python test_futures_trade.py

echo.
echo All tests completed!
echo Check the screenshots directory and logs for results.
echo.

pause