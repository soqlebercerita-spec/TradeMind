
@echo off
echo ========================================
echo AuraTrade Bot - Windows Installation
echo ========================================
echo.

REM Check if Python is installed
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
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Creating environment file...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
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
    )
) else (
    echo .env file already exists
)

echo.
echo Creating necessary directories...
if not exist "AuraTrade\logs" mkdir "AuraTrade\logs"
if not exist "AuraTrade\data\cache" mkdir "AuraTrade\data\cache"
if not exist "AuraTrade\reports" mkdir "AuraTrade\reports"

echo.
echo Setting up file permissions...
attrib +R AuraTrade\config\*.py

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your MT5 credentials
echo 2. Make sure MetaTrader 5 is installed and running
echo 3. Enable Expert Advisors in MT5
echo 4. Run: start_auratrade.bat
echo.
echo Press any key to continue...
pause >nul
