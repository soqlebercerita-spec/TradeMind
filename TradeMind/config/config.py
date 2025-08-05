"""
Global configuration parameters for AuraTrade Bot
"""

import os
from typing import Dict, List, Any

class Config:
    """Main configuration class with all global parameters"""
    
    def __init__(self):
        # Trading pairs configuration
        self.SYMBOLS = [
            "XAUUSD",  # Gold
            "BTCUSD",  # Bitcoin
            "EURUSD",  # Euro/USD
            "GBPUSD",  # Pound/USD
            "USDJPY",  # USD/Japanese Yen
            "AUDUSD",  # Australian Dollar/USD
            "USDCAD",  # USD/Canadian Dollar
            "EURJPY",  # Euro/Japanese Yen
            "GBPJPY",  # Pound/Japanese Yen
            "EURGBP"   # Euro/Pound
        ]
        
        # Timeframes for analysis
        self.TIMEFRAMES = {
            'M1': 1,     # 1 minute
            'M5': 5,     # 5 minutes
            'M15': 15,   # 15 minutes
            'M30': 30,   # 30 minutes
            'H1': 60,    # 1 hour
            'H4': 240,   # 4 hours
            'D1': 1440   # Daily
        }
        
        # Primary timeframes for different strategies
        self.STRATEGY_TIMEFRAMES = {
            'hft': ['M1'],
            'scalping': ['M1', 'M5'],
            'swing': ['M15', 'M30', 'H1'],
            'position': ['H4', 'D1']
        }
        
        # Risk management parameters
        self.RISK_SETTINGS = {
            'max_risk_per_trade': 1.0,      # Maximum 1% risk per trade
            'max_daily_risk': 5.0,          # Maximum 5% daily risk
            'max_total_exposure': 10.0,     # Maximum 10% total exposure
            'max_drawdown': 15.0,           # Maximum 15% drawdown
            'min_risk_reward_ratio': 1.5,   # Minimum 1:1.5 risk/reward
            'default_tp_percentage': 2.0,   # Default 2% TP from equity
            'default_sl_percentage': 1.0,   # Default 1% SL from equity
            'trailing_stop_enabled': True,
            'trailing_stop_distance': 0.5   # 0.5% trailing stop
        }
        
        # Position sizing settings
        self.POSITION_SETTINGS = {
            'lot_calculation_method': 'risk_based',  # 'fixed', 'risk_based', 'kelly'
            'min_lot_size': 0.01,
            'max_lot_size': 10.0,
            'lot_step': 0.01,
            'kelly_fraction': 0.25  # Conservative Kelly fraction
        }
        
        # Trading hours (UTC)
        self.TRADING_HOURS = {
            'forex': {
                'start': '00:00',
                'end': '23:59',
                'exclude_friday_close': True,
                'friday_close_hour': 21
            },
            'crypto': {
                'start': '00:00',
                'end': '23:59',
                'exclude_friday_close': False
            }
        }
        
        # Technical analysis parameters
        self.TA_SETTINGS = {
            'sma_periods': [20, 50, 200],
            'ema_periods': [12, 26, 50],
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'atr_period': 14,
            'bollinger_period': 20,
            'bollinger_deviation': 2,
            'stochastic_k': 14,
            'stochastic_d': 3,
            'williams_r_period': 14
        }
        
        # Strategy-specific settings
        self.STRATEGY_SETTINGS = {
            'hft': {
                'max_spread': 2.0,          # Maximum spread in pips
                'min_volume': 100,          # Minimum tick volume
                'execution_delay_ms': 50,   # Maximum execution delay
                'profit_target_pips': 2,    # Quick profit target
                'stop_loss_pips': 1         # Tight stop loss
            },
            'scalping': {
                'max_spread': 3.0,
                'profit_target_pips': 5,
                'stop_loss_pips': 3,
                'max_trades_per_hour': 20
            },
            'arbitrage': {
                'min_price_difference': 0.1,  # Minimum price difference %
                'execution_timeout': 5000,    # 5 seconds timeout
                'max_latency_ms': 100
            },
            'pattern': {
                'confirmation_candles': 3,
                'pattern_strength_threshold': 0.7,
                'volume_confirmation': True
            }
        }
        
        # Machine Learning settings
        self.ML_SETTINGS = {
            'enabled': True,
            'model_retrain_frequency': 24,  # Hours
            'feature_window': 100,          # Number of candles for features
            'prediction_threshold': 0.6,    # Minimum confidence for signals
            'models': ['random_forest', 'xgboost', 'svm'],
            'cross_validation_folds': 5
        }
        
        # Data management settings
        self.DATA_SETTINGS = {
            'max_candles_history': 10000,
            'data_update_frequency': 1,     # Seconds
            'websocket_reconnect_delay': 5, # Seconds
            'backup_frequency': 3600,       # 1 hour in seconds
            'data_storage_days': 30
        }
        
        # GUI settings
        self.GUI_SETTINGS = {
            'update_frequency': 1000,       # Milliseconds
            'chart_candles_display': 500,
            'max_log_lines': 1000,
            'theme': 'dark',
            'window_geometry': (1200, 800)
        }
        
        # Performance monitoring
        self.PERFORMANCE_SETTINGS = {
            'benchmark_symbol': 'EURUSD',
            'performance_window_days': 30,
            'sharpe_ratio_calculation': True,
            'max_correlation_threshold': 0.8
        }
        
        # Error handling and recovery
        self.ERROR_SETTINGS = {
            'max_connection_retries': 5,
            'retry_delay_seconds': 10,
            'emergency_stop_drawdown': 20.0,    # Emergency stop at 20% drawdown
            'connection_timeout': 30,            # Seconds
            'order_timeout': 10                  # Seconds
        }
        
        # Logging configuration
        self.LOGGING_SETTINGS = {
            'level': 'INFO',
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    
    def get_symbol_settings(self, symbol: str) -> Dict[str, Any]:
        """Get symbol-specific settings"""
        # Default settings for all symbols
        default_settings = {
            'pip_value': 0.0001,
            'digits': 5,
            'min_lot': 0.01,
            'max_lot': 100.0,
            'lot_step': 0.01,
            'contract_size': 100000
        }
        
        # Symbol-specific overrides
        symbol_specific = {
            'XAUUSD': {
                'pip_value': 0.01,
                'digits': 3,
                'contract_size': 100
            },
            'BTCUSD': {
                'pip_value': 1.0,
                'digits': 2,
                'contract_size': 1
            },
            'USDJPY': {
                'pip_value': 0.001,
                'digits': 3
            }
        }
        
        settings = default_settings.copy()
        if symbol in symbol_specific:
            settings.update(symbol_specific[symbol])
        
        return settings
    
    def is_trading_hours(self, symbol: str) -> bool:
        """Check if current time is within trading hours for symbol"""
        from datetime import datetime
        
        current_hour = datetime.utcnow().hour
        
        if symbol.startswith('BTC') or 'CRYPTO' in symbol:
            return True  # Crypto trades 24/7
        
        # Forex trading hours (Sunday 21:00 UTC to Friday 21:00 UTC)
        current_weekday = datetime.utcnow().weekday()
        
        if current_weekday == 6:  # Sunday
            return current_hour >= 21
        elif current_weekday < 5:  # Monday to Friday
            return True
        else:  # Friday
            return current_hour < 21
    
    def get_max_spread(self, symbol: str) -> float:
        """Get maximum allowed spread for symbol"""
        spread_limits = {
            'EURUSD': 2.0,
            'GBPUSD': 3.0,
            'USDJPY': 2.0,
            'XAUUSD': 5.0,
            'BTCUSD': 50.0
        }
        
        return spread_limits.get(symbol, 5.0)  # Default 5 pips
