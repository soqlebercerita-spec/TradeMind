"""
Data management system for AuraTrade Bot
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import threading
import time
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class DataManager:
    """Real-time data management system"""

    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.running = False
        self.data_cache = {}
        self.update_thread = None
        self.lock = threading.Lock()

        # Data update intervals (seconds)
        self.update_intervals = {
            'M1': 60,
            'M5': 300,
            'M15': 900,
            'M30': 1800,
            'H1': 3600,
            'H4': 14400,
            'D1': 86400
        }

    def start_data_updates(self, symbols: List[str]):
        """Start real-time data updates"""
        try:
            self.symbols = symbols
            self.running = True

            # Initialize cache
            for symbol in symbols:
                self.data_cache[symbol] = {}
                for timeframe in ['M1', 'M5', 'M15', 'H1', 'H4']:
                    self.data_cache[symbol][timeframe] = None

            # Start update thread
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

            self.logger.info(f"Data updates started for {symbols}")

        except Exception as e:
            self.logger.error(f"Failed to start data updates: {e}")

    def stop_data_updates(self):
        """Stop data updates"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        self.logger.info("Data updates stopped")

    def _update_loop(self):
        """Main data update loop"""
        while self.running:
            try:
                for symbol in self.symbols:
                    for timeframe in ['M1', 'M5', 'M15', 'H1', 'H4']:
                        self._update_symbol_data(symbol, timeframe)

                time.sleep(1)  # Update every second

            except Exception as e:
                self.logger.error(f"Error in data update loop: {e}")
                time.sleep(5)

    def _update_symbol_data(self, symbol: str, timeframe: str):
        """Update data for specific symbol and timeframe"""
        try:
            data = self.mt5_connector.get_rates(symbol, timeframe, 1000)
            if data is not None:
                with self.lock:
                    self.data_cache[symbol][timeframe] = data

        except Exception as e:
            self.logger.error(f"Failed to update {symbol} {timeframe}: {e}")

    def get_rates(self, symbol: str, timeframe: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """Get historical rates"""
        try:
            # Try cache first
            with self.lock:
                if (symbol in self.data_cache and 
                    timeframe in self.data_cache[symbol] and 
                    self.data_cache[symbol][timeframe] is not None):
                    cached_data = self.data_cache[symbol][timeframe].copy()
                    if len(cached_data) >= count:
                        return cached_data.tail(count)

            # Get from MT5 if not in cache
            return self.mt5_connector.get_rates(symbol, timeframe, count)

        except Exception as e:
            self.logger.error(f"Failed to get rates for {symbol} {timeframe}: {e}")
            return None

    def get_current_price(self, symbol: str) -> Optional[Tuple[float, float]]:
        """Get current bid/ask prices"""
        return self.mt5_connector.get_current_price(symbol)

    def analyze_market_condition(self, symbol: str) -> Dict[str, Any]:
        """Analyze current market condition"""
        try:
            # Get multiple timeframe data
            h1_data = self.get_rates(symbol, 'H1', 100)
            h4_data = self.get_rates(symbol, 'H4', 100)

            if h1_data is None or h4_data is None:
                return {'condition': 'unknown', 'trend': 'unknown', 'volatility': 'unknown'}

            # Calculate trend
            h1_sma20 = h1_data['close'].rolling(20).mean()
            h4_sma20 = h4_data['close'].rolling(20).mean()

            h1_trend = 'up' if h1_data['close'].iloc[-1] > h1_sma20.iloc[-1] else 'down'
            h4_trend = 'up' if h4_data['close'].iloc[-1] > h4_sma20.iloc[-1] else 'down'

            # Overall trend
            if h1_trend == h4_trend:
                trend = h1_trend
                condition = 'trending'
            else:
                trend = 'mixed'
                condition = 'ranging'

            # Calculate volatility
            h1_atr = self._calculate_atr(h1_data, 14)
            avg_atr = h1_atr.mean()
            current_atr = h1_atr.iloc[-1]

            if current_atr > avg_atr * 1.5:
                volatility = 'high'
            elif current_atr < avg_atr * 0.5:
                volatility = 'low'
            else:
                volatility = 'normal'

            return {
                'condition': condition,
                'trend': trend,
                'volatility': volatility,
                'h1_trend': h1_trend,
                'h4_trend': h4_trend
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze market condition for {symbol}: {e}")
            return {'condition': 'unknown', 'trend': 'unknown', 'volatility': 'unknown'}

    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(period).mean()

            return atr

        except Exception as e:
            self.logger.error(f"Failed to calculate ATR: {e}")
            return pd.Series()

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        return self.mt5_connector.get_symbol_info(symbol)

    def is_market_open(self, symbol: str) -> bool:
        """Check if market is open"""
        return self.mt5_connector.is_market_open(symbol)

    def get_spread(self, symbol: str) -> Optional[float]:
        """Get current spread"""
        return self.mt5_connector.get_spread(symbol)