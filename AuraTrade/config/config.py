"""
Main configuration for AuraTrade Bot
"""

class Config:
    """Main configuration settings"""

    def __init__(self):
        # Trading Configuration
        self.TRADING = {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD'],
            'timeframes': ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'],
            'max_spread': 3.0,  # Maximum spread in pips
            'min_liquidity_hours': (8, 17),  # Trading hours (24h format)
            'max_slippage': 2.0  # Maximum slippage in pips
        }

        # Strategy Configuration
        self.STRATEGIES = {
            'hft_enabled': True,
            'scalping_enabled': True,
            'pattern_enabled': True,
            'sentiment_enabled': False,
            'ml_enabled': False
        }

        # Technical Analysis
        self.TECHNICAL = {
            'rsi_period': 14,
            'ema_fast': 12,
            'ema_slow': 26,
            'sma_period': 20,
            'bb_period': 20,
            'bb_std': 2,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'atr_period': 14
        }

        # Performance Targets
        self.PERFORMANCE = {
            'target_win_rate': 75.0,
            'max_daily_trades': 15,
            'max_concurrent_trades': 5,
            'min_confidence': 70.0
        }