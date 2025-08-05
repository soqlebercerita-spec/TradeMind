
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
