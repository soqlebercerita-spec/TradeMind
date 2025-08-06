
@echo off
title AuraTrade Bot - Professional Trading System
color 0A

echo ========================================
echo    AuraTrade Bot v2.0
echo    Professional Trading System
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "AuraTrade\bot.py" (
    echo ERROR: AuraTrade directory not found!
    echo Please make sure you're running this from the project root directory
    pause
    exit /b 1
)

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ and add it to PATH
    echo Download from: https://python.org
    pause
    exit /b 1
)

echo.
echo Checking dependencies...
python -c "import MetaTrader5, pandas, numpy, PyQt5" 2>nul
if %errorlevel% neq 0 (
    echo Installing missing dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Checking MetaTrader 5 installation...
python -c "import MetaTrader5 as mt5; print('MT5 Python API:', 'OK' if mt5.initialize() else 'FAILED'); mt5.shutdown()" 2>nul

echo.
echo Starting AuraTrade Bot...
echo Target: 75%+ Win Rate with Conservative Risk Management
echo ========================================
echo.

cd AuraTrade
python bot.py

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Bot exited with error code %errorlevel%
    echo Check the logs for more information
    echo ========================================
)

echo.
echo Press any key to exit...
pause >nul
