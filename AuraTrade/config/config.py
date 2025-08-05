
"""
Global configuration parameters for AuraTrade Bot
"""

import os
from typing import Dict, List, Any

class Config:
    """Global configuration manager"""
    
    def __init__(self):
        # System settings
        self.APP_NAME = "AuraTrade Bot"
        self.VERSION = "1.0.0"
        self.DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Trading configuration
        self.DEFAULT_SYMBOLS = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD', 'USDJPY']
        self.DEFAULT_TIMEFRAMES = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']
        
        # Technical analysis settings
        self.TA_PERIODS = {
            'sma_fast': 10,
            'sma_slow': 20,
            'ema_fast': 12,
            'ema_slow': 26,
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bollinger_period': 20,
            'bollinger_std': 2,
            'atr_period': 14,
            'stoch_k': 14,
            'stoch_d': 3
        }
        
        # Risk management defaults
        self.DEFAULT_RISK_PER_TRADE = 1.0  # 1% of equity
        self.DEFAULT_MAX_DAILY_RISK = 5.0  # 5% of equity
        self.DEFAULT_MAX_EXPOSURE = 10.0   # 10% of equity
        self.DEFAULT_TP_RATIO = 2.0        # 2:1 TP:SL ratio
        
        # ML/AI settings
        self.ML_ENABLED = True
        self.ML_MODEL_UPDATE_HOURS = 24
        self.ML_PREDICTION_THRESHOLD = 0.6
        
        # HFT settings
        self.HFT_MAX_LATENCY_MS = 5
        self.HFT_TICK_ANALYSIS_DEPTH = 100
        self.HFT_MIN_SPREAD_POINTS = 2
        
        # GUI settings
        self.GUI_UPDATE_INTERVAL_MS = 1000
        self.CHART_CANDLES_VISIBLE = 200
        
        # Data settings
        self.DATA_HISTORY_DAYS = 30
        self.DATA_BACKUP_ENABLED = True
        self.DATA_COMPRESSION = True
        
        # Notification settings
        self.TELEGRAM_ENABLED = True
        self.EMAIL_ENABLED = False
        
        # File paths
        self.LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
        self.DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache')
        self.MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [self.LOG_DIR, self.DATA_DIR, self.MODEL_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_symbol_config(self, symbol: str) -> Dict[str, Any]:
        """Get symbol-specific configuration"""
        symbol_configs = {
            'EURUSD': {'pip_size': 0.0001, 'lot_size': 100000, 'min_lot': 0.01},
            'GBPUSD': {'pip_size': 0.0001, 'lot_size': 100000, 'min_lot': 0.01},
            'USDJPY': {'pip_size': 0.01, 'lot_size': 100000, 'min_lot': 0.01},
            'XAUUSD': {'pip_size': 0.01, 'lot_size': 100, 'min_lot': 0.01},
            'BTCUSD': {'pip_size': 1.0, 'lot_size': 1, 'min_lot': 0.01}
        }
        
        return symbol_configs.get(symbol, {
            'pip_size': 0.0001, 'lot_size': 100000, 'min_lot': 0.01
        })
    
    def get_timeframe_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        timeframe_map = {
            'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
            'H1': 60, 'H4': 240, 'D1': 1440, 'W1': 10080
        }
        return timeframe_map.get(timeframe, 15)
"""
Main configuration file for AuraTrade Bot
Centralized settings for all components
"""

import os
from datetime import time

class Config:
    """Centralized configuration for AuraTrade Bot"""
    
    def __init__(self):
        # Bot Information
        self.BOT_NAME = "AuraTrade"
        self.BOT_VERSION = "2.0.0"
        self.BOT_DESCRIPTION = "High-Performance AI Trading Bot"
        
        # Trading Configuration
        self.TRADING = {
            'enabled': True,
            'max_daily_trades': 10,
            'target_win_rate': 85.0,
            'default_risk_percent': 1.0,
            'default_reward_ratio': 2.0,
            'max_spread_pips': 2.0,
            'min_signal_confidence': 70.0,
            'trading_symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'],
            'trading_hours': {
                'start': time(8, 0),   # 08:00
                'end': time(17, 0)     # 17:00
            }
        }
        
        # Risk Management
        self.RISK = {
            'max_risk_per_trade': 1.0,      # 1% per trade
            'max_daily_risk': 5.0,          # 5% daily max
            'max_drawdown': 10.0,           # 10% max drawdown
            'max_consecutive_losses': 2,     # Stop after 2 losses
            'emergency_stop_loss': 100.0,   # $100 daily loss limit
            'daily_profit_target': 500.0,   # $500 daily target
            'margin_safety_level': 200.0    # 200% margin level minimum
        }
        
        # Strategy Configuration
        self.STRATEGIES = {
            'hft': {
                'enabled': True,
                'timeframe': 'M1',
                'risk_percent': 0.5,
                'max_trades_per_hour': 5
            },
            'scalping': {
                'enabled': True,
                'timeframe': 'M5',
                'risk_percent': 1.0,
                'max_trades_per_hour': 3
            },
            'pattern': {
                'enabled': True,
                'timeframe': 'M15',
                'risk_percent': 1.5,
                'max_trades_per_hour': 2
            }
        }
        
        # Technical Analysis
        self.INDICATORS = {
            'ema_periods': [20, 50, 200],
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'macd_periods': [12, 26, 9],
            'bb_period': 20,
            'bb_deviation': 2.0,
            'atr_period': 14
        }
        
        # Machine Learning
        self.ML = {
            'enabled': False,
            'model_update_frequency': 24,  # hours
            'features_count': 50,
            'prediction_threshold': 0.7
        }
        
        # GUI Configuration
        self.GUI = {
            'theme': 'dark',
            'update_interval': 2000,  # milliseconds
            'chart_symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'],
            'default_timeframe': 'M15'
        }
        
        # Logging Configuration
        self.LOGGING = {
            'level': 'INFO',
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'console_output': True
        }
        
        # Data Management
        self.DATA = {
            'history_days': 30,
            'backup_enabled': True,
            'backup_interval': 24,  # hours
            'data_sources': ['MT5'],
            'fallback_mode': True
        }
        
        # Notification Settings
        self.NOTIFICATIONS = {
            'telegram_enabled': True,
            'email_enabled': False,
            'trade_alerts': True,
            'system_alerts': True,
            'daily_summary': True
        }
        
        # Performance Optimization
        self.PERFORMANCE = {
            'max_threads': 4,
            'data_cache_size': 1000,
            'optimize_memory': True,
            'gc_frequency': 300  # seconds
        }
    
    def get_trading_config(self):
        """Get trading configuration"""
        return self.TRADING
    
    def get_risk_config(self):
        """Get risk management configuration"""
        return self.RISK
    
    def get_strategy_config(self, strategy_name: str):
        """Get specific strategy configuration"""
        return self.STRATEGIES.get(strategy_name, {})
    
    def is_trading_enabled(self):
        """Check if trading is enabled"""
        return self.TRADING['enabled']
    
    def is_ml_enabled(self):
        """Check if ML is enabled"""
        return self.ML['enabled']
    
    def validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate risk percentages
        if self.RISK['max_risk_per_trade'] > 5.0:
            errors.append("Max risk per trade should not exceed 5%")
        
        if self.RISK['max_daily_risk'] > 20.0:
            errors.append("Max daily risk should not exceed 20%")
        
        # Validate trading hours
        if self.TRADING['trading_hours']['start'] >= self.TRADING['trading_hours']['end']:
            errors.append("Trading start time must be before end time")
        
        # Validate symbols
        if not self.TRADING['trading_symbols']:
            errors.append("At least one trading symbol must be configured")
        
        return errors
