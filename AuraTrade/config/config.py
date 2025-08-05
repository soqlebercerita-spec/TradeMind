
"""
Main configuration for AuraTrade Bot
Global settings and parameters
"""

class Config:
    """Main configuration class"""
    
    def __init__(self):
        # Trading Parameters
        self.SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
        self.TIMEFRAMES = ['M1', 'M5', 'M15', 'H1']
        self.DEFAULT_TIMEFRAME = 'M5'
        
        # Risk Management
        self.MAX_RISK_PER_TRADE = 1.0  # 1% per trade
        self.MAX_DAILY_RISK = 5.0      # 5% per day
        self.MAX_DRAWDOWN = 15.0       # 15% maximum drawdown
        self.MAX_OPEN_POSITIONS = 5
        
        # Strategy Configuration
        self.STRATEGY_ENABLED = {
            'hft': True,
            'scalping': True,
            'swing': True,
            'arbitrage': True,
            'pattern': True
        }
        
        # Technical Analysis
        self.SMA_PERIODS = [20, 50, 100, 200]
        self.EMA_PERIODS = [12, 26, 50]
        self.RSI_PERIOD = 14
        self.RSI_OVERBOUGHT = 70
        self.RSI_OVERSOLD = 30
        self.MACD_FAST = 12
        self.MACD_SLOW = 26
        self.MACD_SIGNAL = 9
        self.BOLLINGER_PERIOD = 20
        self.BOLLINGER_STD = 2.0
        
        # Trading Hours (UTC)
        self.TRADING_START_HOUR = 1   # 01:00 UTC
        self.TRADING_END_HOUR = 23    # 23:00 UTC
        self.NEWS_BLACKOUT_MINUTES = 15  # Minutes before/after news
        
        # Position Management
        self.USE_TRAILING_STOP = True
        self.TRAILING_STOP_PIPS = 20
        self.PARTIAL_CLOSE_ENABLED = True
        self.PARTIAL_CLOSE_PERCENT = 50
        
        # Performance Targets
        self.TARGET_WIN_RATE = 85.0    # 85% win rate target
        self.TARGET_MONTHLY_RETURN = 15.0  # 15% monthly return
        self.TARGET_SHARPE_RATIO = 2.0
        
        # GUI Settings
        self.GUI_UPDATE_INTERVAL = 1000  # milliseconds
        self.CHART_CANDLES_COUNT = 200
        self.LOG_DISPLAY_LINES = 1000
        
        # Logging
        self.LOG_LEVEL = 'INFO'
        self.LOG_FILE_ROTATION = True
        self.LOG_MAX_SIZE_MB = 10
        self.LOG_BACKUP_COUNT = 5
        
        # Data Management
        self.DATA_UPDATE_INTERVAL = 1  # seconds
        self.DATA_CACHE_SIZE = 1000    # number of bars
        self.PRICE_PRECISION = 5
        
        # Notification Settings
        self.NOTIFY_ON_TRADE_OPEN = True
        self.NOTIFY_ON_TRADE_CLOSE = True
        self.NOTIFY_ON_PROFIT_TARGET = True
        self.NOTIFY_ON_LOSS_LIMIT = True
        self.NOTIFY_ON_SYSTEM_ERROR = True
        
    def get_symbol_config(self, symbol: str) -> dict:
        """Get symbol-specific configuration"""
        symbol_configs = {
            'EURUSD': {
                'pip_value': 0.00001,
                'min_stop_loss': 10,
                'max_spread': 3,
                'typical_range': 80,
                'lot_step': 0.01
            },
            'GBPUSD': {
                'pip_value': 0.00001,
                'min_stop_loss': 15,
                'max_spread': 4,
                'typical_range': 120,
                'lot_step': 0.01
            },
            'USDJPY': {
                'pip_value': 0.001,
                'min_stop_loss': 10,
                'max_spread': 3,
                'typical_range': 70,
                'lot_step': 0.01
            },
            'XAUUSD': {
                'pip_value': 0.01,
                'min_stop_loss': 50,
                'max_spread': 50,
                'typical_range': 800,
                'lot_step': 0.01
            },
            'BTCUSD': {
                'pip_value': 1.0,
                'min_stop_loss': 100,
                'max_spread': 100,
                'typical_range': 2000,
                'lot_step': 0.01
            }
        }
        
        return symbol_configs.get(symbol, {
            'pip_value': 0.00001,
            'min_stop_loss': 10,
            'max_spread': 5,
            'typical_range': 100,
            'lot_step': 0.01
        })
    
    def get_strategy_config(self, strategy_name: str) -> dict:
        """Get strategy-specific configuration"""
        strategy_configs = {
            'hft': {
                'timeframe': 'M1',
                'max_positions': 2,
                'min_profit_pips': 2,
                'max_loss_pips': 5,
                'confidence_threshold': 80
            },
            'scalping': {
                'timeframe': 'M5',
                'max_positions': 3,
                'min_profit_pips': 5,
                'max_loss_pips': 10,
                'confidence_threshold': 75
            },
            'swing': {
                'timeframe': 'H1',
                'max_positions': 2,
                'min_profit_pips': 50,
                'max_loss_pips': 25,
                'confidence_threshold': 70
            },
            'arbitrage': {
                'timeframe': 'M15',
                'max_positions': 4,
                'correlation_threshold': 0.8,
                'spread_threshold': 0.0005,
                'confidence_threshold': 85
            }
        }
        
        return strategy_configs.get(strategy_name, {
            'timeframe': 'M5',
            'max_positions': 1,
            'min_profit_pips': 10,
            'max_loss_pips': 10,
            'confidence_threshold': 70
        })
    
    def is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        from datetime import datetime
        
        current_hour = datetime.utcnow().hour
        return self.TRADING_START_HOUR <= current_hour <= self.TRADING_END_HOUR
    
    def get_performance_metrics(self) -> dict:
        """Get performance target metrics"""
        return {
            'target_win_rate': self.TARGET_WIN_RATE,
            'target_monthly_return': self.TARGET_MONTHLY_RETURN,
            'target_sharpe_ratio': self.TARGET_SHARPE_RATIO,
            'max_drawdown': self.MAX_DRAWDOWN
        }
