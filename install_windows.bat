
@echo off
echo ========================================
echo AuraTrade Bot - Windows Installation
echo ========================================
echo.

echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Creating environment file...
if not exist .env (
    copy .env.example .env
    echo Please edit .env file with your MT5 and Telegram credentials
) else (
    echo .env file already exists
)

echo.
echo Creating logs directory...
if not exist AuraTrade\logs mkdir AuraTrade\logs

echo.
echo ========================================
echo Installation completed!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo 2. Make sure MetaTrader 5 is installed
echo 3. Run: python AuraTrade\bot.py
echo.
pause
