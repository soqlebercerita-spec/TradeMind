
@echo off
title AuraTrade - High Performance Trading Bot
echo.
echo =====================================================
echo    AuraTrade Bot v2.0 - High Performance Edition
echo    Target Win Rate: 85%+ with Conservative Trading
echo =====================================================
echo.

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo [2/3] Installing/Updating dependencies...
pip install -r requirements.txt --quiet

echo [3/3] Starting AuraTrade Bot...
echo.
echo Bot is starting...
echo Check the GUI window for real-time monitoring
echo.

cd AuraTrade
python bot.py

echo.
echo Bot has stopped. Press any key to exit...
pause >nul
