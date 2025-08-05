
# 🤖 AuraTrade - High Performance Trading Bot

Professional AI-powered trading bot optimized for **85%+ win rate** with conservative risk management.

## ✨ Key Features

### 🎯 **High Win Rate System**
- Conservative trading approach targeting 85%+ win rate
- Advanced signal filtering with multiple confirmations
- Risk-first position sizing based on account percentage
- Smart daily limits to preserve performance

### ⚙️ **Complete MT5 Integration**
- **Auto-detect and auto-login** to MetaTrader 5
- Multi-symbol support (EURUSD, GBPUSD, USDJPY, XAUUSD)
- Real-time data feeds and order execution
- Automatic reconnection and fallback modes

### 🧠 **Multi-Strategy Trading**
- **HFT Engine**: Ultra-fast tick-based execution
- **Scalping Strategy**: Quick entries with small targets
- **Pattern Strategy**: Chart pattern recognition
- Modular system - enable/disable strategies per config

### 📊 **Advanced Technical Analysis**
- All indicators built with NumPy/Pandas (no TA-Lib dependency)
- EMA, SMA, WMA, RSI, MACD, Bollinger Bands
- ATR, Stochastic, Support/Resistance detection
- Multi-timeframe analysis (M1, M5, M15, H1, H4)

### 💼 **Professional Risk Management**
- **TP/SL based on account percentage** (not pips)
- Auto lot calculation based on risk %
- Maximum exposure limits per session/day
- Drawdown control with emergency stops
- Trailing stops and position management

### 💻 **Professional GUI Dashboard**
- Real-time monitoring with PyQt5
- Live charts with technical indicators
- **Emergency stop button** for instant control
- Account info, positions, and trade history
- Dark theme with professional styling

### 📱 **Smart Notifications**
- Telegram integration for trade alerts
- Real-time notifications for entries/exits
- Daily summary reports
- Risk alerts and system status updates

## 🚀 Quick Start

### 1. **Auto-Launch (Recommended)**
```bash
# Windows
start_auratrade.bat

# Or directly
python bot.py
```

### 2. **Configuration**
Edit `AuraTrade/config/credentials.py`:
```python
self.MT5 = {
    'login': YOUR_MT5_LOGIN,        # Your MT5 account
    'password': 'YOUR_PASSWORD',    # Your MT5 password  
    'server': 'YOUR_BROKER_SERVER'  # Your broker server
}
```

### 3. **Optional: Telegram Notifications**
```python
self.TELEGRAM = {
    'bot_token': 'YOUR_BOT_TOKEN',     # From @BotFather
    'chat_id': 'YOUR_CHAT_ID',         # Your Telegram ID
    'notifications_enabled': True
}
```

## 🎯 Trading Performance

### **Conservative Settings (Default)**
- **Max Risk**: 1% per trade
- **Daily Limit**: 10 trades maximum
- **Target Win Rate**: 85%+
- **Risk/Reward**: 1:2 minimum
- **Max Spread**: 2 pips
- **Trading Hours**: 08:00-17:00 (high liquidity)

### **Performance Metrics**
- Automatic win rate calculation
- Real-time P&L tracking
- Drawdown monitoring
- Performance-based risk adjustment

## 🛠️ Advanced Features

### **AI & Machine Learning**
- Optional ML module for trend prediction
- XGBoost integration for signal enhancement
- Performance evaluation vs. real results

### **Market Analysis**
- Multi-timeframe trend analysis
- Market condition detection (trending/ranging)
- Volatility and momentum indicators
- Currency strength analysis

### **Risk Controls**
- Emergency stop (GUI + code)
- Auto-reconnect MT5 on disconnect
- Session filtering (time-based trading)
- Maximum consecutive loss protection

## 📁 Project Structure

```
AuraTrade/
├── bot.py                 # Main entry point
├── config/
│   ├── credentials.py     # MT5 & API credentials
│   ├── config.py          # Main configuration
│   └── settings.py        # Runtime settings
├── core/
│   ├── mt5_connector.py   # MT5 integration
│   ├── trading_engine.py  # Main trading logic
│   ├── order_manager.py   # Order management
│   ├── risk_manager.py    # Risk controls
│   └── position_sizing.py # Position calculations
├── strategies/
│   ├── hft_strategy.py    # High-frequency trading
│   ├── scalping_strategy.py # Scalping logic
│   └── pattern_strategy.py  # Pattern recognition
├── gui/
│   ├── main_window.py     # Main GUI window
│   ├── dashboard.py       # Trading dashboard
│   └── charts.py          # Real-time charts
├── analysis/
│   ├── technical_analysis.py # Technical indicators
│   └── pattern_recognition.py # Chart patterns
└── utils/
    ├── logger.py          # Professional logging
    └── notifier.py        # Telegram notifications
```

## 🔧 Requirements

- **Python 3.8+**
- **MetaTrader 5** terminal
- Windows OS (recommended)
- Internet connection for notifications

## 📈 Trading Strategy

### **Signal Generation**
1. **Multi-timeframe Analysis**: H4 → H1 → M15 → M5
2. **Confirmation Required**: Minimum 3 confirmations
3. **Quality over Quantity**: Max 10 trades/day
4. **Optimal Timing**: European/US session overlap

### **Risk Management**
1. **Position Sizing**: Based on account % risk
2. **Stop Loss**: Percentage-based, not pip-based
3. **Take Profit**: Minimum 1:2 risk/reward
4. **Emergency Controls**: Multiple safety layers

### **Performance Optimization**
- Conservative approach for consistent profits
- Adaptive risk adjustment based on performance  
- Quality signal filtering to maintain high win rate
- Automatic performance monitoring and alerts

## 🚨 Important Notes

- **This is a professional trading tool** - understand the risks
- **Test on demo account first** before live trading
- **Monitor the bot regularly** - it's not set-and-forget
- **Keep MT5 terminal running** for proper operation
- **Maintain stable internet connection** for reliability

## 📞 Support

The bot includes comprehensive logging and error handling. Check:
- `logs/auratrade.log` for general operations
- `logs/errors.log` for error details
- `logs/trades.log` for trading activity

---

**🎯 Target: 85%+ Win Rate | 💰 Professional Trading | 🛡️ Conservative Risk Management**

*AuraTrade v2.0 - Built for Professional Traders*
