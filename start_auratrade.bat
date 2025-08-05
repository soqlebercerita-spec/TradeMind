
@echo off
echo Starting AuraTrade Bot...
echo ========================

cd AuraTrade

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r ../requirements.txt

echo Starting AuraTrade Bot...
python bot.py

pause
