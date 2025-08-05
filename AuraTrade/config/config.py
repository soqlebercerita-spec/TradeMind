
"""
AuraTrade Configuration Management
Centralized configuration for the trading system
"""

import os
from typing import Dict, Any, List
from datetime import datetime


class Config:
    """Main configuration class for AuraTrade"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration settings"""
        # Trading Settings
        self.TRADING_ENABLED = True
        self.MAX_POSITIONS = 10
        self.MAX_DAILY_TRADES = 50
        self.MIN_BALANCE = 1000.0
        
        # Risk Management
        self.MAX_RISK_PER_TRADE = 0.02  # 2% per trade
        self.MAX_DAILY_RISK = 0.10      # 10% per day
        self.STOP_LOSS_PERCENT = 0.015  # 1.5%
        self.TAKE_PROFIT_PERCENT = 0.03 # 3%
        
        # Timeframes
        self.TIMEFRAMES = {
            'M1': 1,
            'M5': 5,
            'M15': 15,
            'M30': 30,
            'H1': 60,
            'H4': 240,
            'D1': 1440
        }
        
        # Trading Symbols
        self.SYMBOLS = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
            'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD'
        ]
        
        # Strategy Settings
        self.STRATEGIES = {
            'hft': {
                'enabled': True,
                'timeframe': 'M1',
                'max_positions': 3,
                'profit_target': 0.001
            },
            'scalping': {
                'enabled': True,
                'timeframe': 'M5',
                'max_positions': 5,
                'profit_target': 0.002
            },
            'pattern': {
                'enabled': True,
                'timeframe': 'M15',
                'max_positions': 2,
                'profit_target': 0.005
            }
        }
        
        # Technical Analysis
        self.INDICATORS = {
            'sma_periods': [10, 20, 50],
            'ema_periods': [12, 26],
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bollinger_period': 20,
            'bollinger_std': 2
        }
        
        # Logging
        self.LOG_LEVEL = 'INFO'
        self.LOG_FILE = 'logs/auratrade.log'
        self.MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
        self.LOG_BACKUP_COUNT = 5
        
    def get_symbol_config(self, symbol: str) -> Dict[str, Any]:
        """Get configuration for specific symbol"""
        return {
            'symbol': symbol,
            'min_lot': 0.01,
            'max_lot': 10.0,
            'lot_step': 0.01,
            'spread_limit': 3.0,
            'slippage': 3
        }
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for specific strategy"""
        return self.STRATEGIES.get(strategy_name, {})
    
    def is_trading_time(self) -> bool:
        """Check if current time is within trading hours"""
        now = datetime.now()
        hour = now.hour
        
        # Avoid major news times (simplified)
        if hour in [0, 1, 22, 23]:  # Avoid low liquidity hours
            return False
        
        return True
    
    def get_risk_config(self) -> Dict[str, float]:
        """Get risk management configuration"""
        return {
            'max_risk_per_trade': self.MAX_RISK_PER_TRADE,
            'max_daily_risk': self.MAX_DAILY_RISK,
            'stop_loss_percent': self.STOP_LOSS_PERCENT,
            'take_profit_percent': self.TAKE_PROFIT_PERCENT,
            'max_positions': self.MAX_POSITIONS,
            'max_daily_trades': self.MAX_DAILY_TRADES
        }
    
    def update_config(self, key: str, value: Any):
        """Update configuration value"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise ValueError(f"Configuration key '{key}' not found")
    
    def save_config(self):
        """Save current configuration (placeholder)"""
        # In a real implementation, this would save to file
        pass
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        try:
            # Check risk parameters
            if self.MAX_RISK_PER_TRADE > 0.05:  # Max 5% per trade
                return False
            
            if self.MAX_DAILY_RISK > 0.20:  # Max 20% per day
                return False
            
            # Check position limits
            if self.MAX_POSITIONS > 50:
                return False
            
            # Check symbols
            if not self.SYMBOLS:
                return False
            
            return True
            
        except Exception:
            return False
