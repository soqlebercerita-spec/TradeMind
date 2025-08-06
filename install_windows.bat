
@echo off
title AuraTrade Bot - Windows Installation
color 0A

echo ========================================
echo    AuraTrade Bot v2.0 Installation
echo    Professional Trading System
echo ========================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to add Python to PATH during installation
    pause
    exit /b 1
)

echo Python found! Proceeding with installation...
echo.

echo Installing Python dependencies...
echo Upgrading pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo WARNING: Failed to upgrade pip/setuptools/wheel
)

echo Installing core dependencies...
python -m pip install colorlog>=6.7.0 MetaTrader5>=5.0.45
python -m pip install pandas>=1.5.0 numpy>=1.21.0
python -m pip install PyQt5>=5.15.0 matplotlib>=3.5.0
python -m pip install scikit-learn>=1.1.0
python -m pip install requests>=2.28.0 python-telegram-bot>=20.0 schedule>=1.2.0
python -m pip install python-dotenv>=0.19.0 configparser>=5.3.0
python -m pip install numba>=0.56.0 cython>=0.29.0

if %errorlevel% neq 0 (
    echo ERROR: Failed to install some dependencies
    echo Trying fallback installation...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Installation failed completely
        pause
        exit /b 1
    )
)

echo.
echo Creating necessary directories...
if not exist "AuraTrade\logs" mkdir "AuraTrade\logs"
if not exist "AuraTrade\data" mkdir "AuraTrade\data"
if not exist "AuraTrade\data\cache" mkdir "AuraTrade\data\cache"
if not exist "AuraTrade\reports" mkdir "AuraTrade\reports"
if not exist "AuraTrade\config" mkdir "AuraTrade\config"
if not exist "AuraTrade\exports" mkdir "AuraTrade\exports"
if not exist "AuraTrade\backups" mkdir "AuraTrade\backups"

echo.
echo Setting up environment file...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo .env file created from template
        echo Please edit .env file with your MT5 and Telegram credentials
    ) else (
        echo Creating default .env file...
        echo # AuraTrade Configuration > .env
        echo MT5_LOGIN=your_login_here >> .env
        echo MT5_PASSWORD=your_password_here >> .env
        echo MT5_SERVER=your_server_here >> .env
        echo TELEGRAM_BOT_TOKEN=your_bot_token_here >> .env
        echo TELEGRAM_CHAT_ID=your_chat_id_here >> .env
        echo Created default .env file
    )
) else (
    echo .env file already exists
)

echo.
echo Checking MetaTrader 5 installation...
python -c "import MetaTrader5 as mt5; print('MT5 Python API:', 'OK' if mt5.initialize() else 'FAILED'); mt5.shutdown()" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: MT5 Python API test failed
    echo Make sure MetaTrader 5 is installed and properly configured
)

echo.
echo Setting up file permissions...
attrib +R AuraTrade\config\*.py >nul 2>&1

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your MT5 credentials
echo 2. Make sure MetaTrader 5 is installed and running
echo 3. Enable Expert Advisors in MT5 (Tools ^> Options ^> Expert Advisors)
echo 4. Allow automated trading in MT5
echo 5. Run: start_auratrade.bat
echo.
echo Important Notes:
echo - Ensure MT5 is running before starting the bot
echo - Check that your MT5 account allows automated trading
echo - The bot requires a stable internet connection
echo.
echo Press any key to continue...
pause >nul
