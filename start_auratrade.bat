
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
    echo Current directory: %CD%
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
echo Checking environment configuration...
if not exist .env (
    echo WARNING: .env file not found!
    echo Please run install_windows.bat first to set up the environment
    pause
    exit /b 1
)

echo.
echo Checking core dependencies...
python -c "import MetaTrader5, pandas, numpy, PyQt5" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies are missing!
    echo Installing missing dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        echo Please run install_windows.bat first
        pause
        exit /b 1
    )
)

echo.
echo Testing MetaTrader 5 connection...
python -c "import MetaTrader5 as mt5; result = mt5.initialize(); print('MT5 Connection:', 'SUCCESS' if result else 'FAILED'); mt5.shutdown()" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: MT5 connection test failed
    echo Please ensure:
    echo - MetaTrader 5 is installed and running
    echo - Expert Advisors are enabled
    echo - Automated trading is allowed
    echo.
    echo Continue anyway? (Y/N)
    choice /c YN /n
    if %errorlevel% equ 2 (
        echo Startup cancelled by user
        pause
        exit /b 1
    )
)

echo.
echo Checking required directories...
if not exist "AuraTrade\logs" mkdir "AuraTrade\logs"
if not exist "AuraTrade\data\cache" mkdir "AuraTrade\data\cache"
if not exist "AuraTrade\reports" mkdir "AuraTrade\reports"

echo.
echo Starting AuraTrade Bot...
echo Target: 75%+ Win Rate with Conservative Risk Management
echo ========================================
echo.
echo Bot Status: INITIALIZING...
echo Time: %date% %time%
echo.

cd AuraTrade
python bot.py

echo.
echo ========================================
if %errorlevel% equ 0 (
    echo Bot exited normally
) else (
    echo Bot exited with error code %errorlevel%
    echo Check the logs in AuraTrade\logs\ for more information
    echo.
    echo Common issues:
    echo - MT5 not running or not connected
    echo - Invalid credentials in .env file
    echo - Network connectivity issues
    echo - Missing permissions for automated trading
)
echo ========================================
echo.
echo Press any key to exit...
pause >nul
