
#!/bin/bash

echo "========================================"
echo "    AuraTrade Bot v2.0"
echo "    Professional Trading System"
echo "========================================"
echo

# Check if we're in the right directory
if [ ! -f "AuraTrade/bot.py" ]; then
    echo "ERROR: AuraTrade directory not found!"
    echo "Please make sure you're running this from the project root directory"
    exit 1
fi

echo "Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.8+ and make sure it's in PATH"
    exit 1
fi

echo
echo "Checking dependencies..."
python3 -c "import MetaTrader5, pandas, numpy, PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing missing dependencies..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo
echo "Checking MetaTrader 5 installation..."
python3 -c "import MetaTrader5 as mt5; print('MT5 Python API:', 'OK' if mt5.initialize() else 'FAILED'); mt5.shutdown()" 2>/dev/null

echo
echo "Starting AuraTrade Bot..."
echo "Target: 75%+ Win Rate with Conservative Risk Management"
echo "========================================"
echo

cd AuraTrade
python3 bot.py

if [ $? -ne 0 ]; then
    echo
    echo "========================================"
    echo "Bot exited with error code $?"
    echo "Check the logs for more information"
    echo "========================================"
fi

echo
echo "Press any key to exit..."
read -n 1
