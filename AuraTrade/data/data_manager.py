
"""
Data Manager for AuraTrade Bot
Handles real-time data feeds and market analysis
"""

import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from utils.logger import Logger

class DataManager:
    """Real-time data management and processing"""
    
    def __init__(self, mt5_connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.data_cache = {}
        self.subscribers = {}
        self.update_thread = None
        self.running = False
        self.update_interval = 1  # seconds
        
        self.logger.info("DataManager initialized")
    
    def start_data_updates(self, symbols: List[str]):
        """Start real-time data updates"""
        try:
            self.symbols = symbols
            self.running = True
            
            # Initialize data cache
            for symbol in symbols:
                self.data_cache[symbol] = {
                    'rates': pd.DataFrame(),
                    'last_update': None,
                    'subscribers': []
                }
                
                # Get initial data
                initial_data = self.mt5_connector.get_rates(symbol, 'M1', 1000)
                if not initial_data.empty:
                    self.data_cache[symbol]['rates'] = initial_data
                    self.data_cache[symbol]['last_update'] = datetime.now()
            
            # Start update thread
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            self.logger.info(f"Started data updates for {len(symbols)} symbols")
            
        except Exception as e:
            self.logger.error(f"Error starting data updates: {e}")
    
    def stop_data_updates(self):
        """Stop data updates"""
        try:
            self.running = False
            
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=5)
            
            self.logger.info("Data updates stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping data updates: {e}")
    
    def _update_loop(self):
        """Main data update loop"""
        while self.running:
            try:
                for symbol in self.symbols:
                    if symbol in self.data_cache:
                        self._update_symbol_data(symbol)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in data update loop: {e}")
                time.sleep(5)
    
    def _update_symbol_data(self, symbol: str):
        """Update data for specific symbol"""
        try:
            # Get current price
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return
            
            current_time = datetime.now()
            current_price = symbol_info['bid']
            
            # Create new data point
            new_data = pd.DataFrame({
                'time': [current_time],
                'open': [current_price],
                'high': [current_price * 1.0001],
                'low': [current_price * 0.9999],
                'close': [current_price],
                'tick_volume': [np.random.randint(50, 200)]
            })
            new_data.set_index('time', inplace=True)
            
            # Update cache
            if symbol in self.data_cache:
                # Append new data
                self.data_cache[symbol]['rates'] = pd.concat([
                    self.data_cache[symbol]['rates'][-999:],  # Keep last 999 bars
                    new_data
                ])
                self.data_cache[symbol]['last_update'] = current_time
                
                # Notify subscribers
                self._notify_subscribers(symbol, new_data)
                
        except Exception as e:
            self.logger.error(f"Error updating data for {symbol}: {e}")
    
    def _notify_subscribers(self, symbol: str, new_data: pd.DataFrame):
        """Notify subscribers of new data"""
        try:
            if symbol in self.subscribers:
                for callback in self.subscribers[symbol]:
                    try:
                        callback(symbol, new_data)
                    except Exception as e:
                        self.logger.error(f"Error notifying subscriber: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error notifying subscribers for {symbol}: {e}")
    
    def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to data updates"""
        try:
            if symbol not in self.subscribers:
                self.subscribers[symbol] = []
            
            self.subscribers[symbol].append(callback)
            self.logger.debug(f"New subscriber added for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to {symbol}: {e}")
    
    def get_latest_data(self, symbol: str, count: int = 100) -> pd.DataFrame:
        """Get latest data for symbol"""
        try:
            if symbol not in self.data_cache:
                # Try to get data from MT5
                data = self.mt5_connector.get_rates(symbol, 'M1', count)
                if not data.empty:
                    self.data_cache[symbol] = {
                        'rates': data,
                        'last_update': datetime.now(),
                        'subscribers': []
                    }
                return data
            
            return self.data_cache[symbol]['rates'].tail(count)
            
        except Exception as e:
            self.logger.error(f"Error getting latest data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol: str) -> Dict[str, float]:
        """Get current bid/ask prices"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info:
                return {
                    'bid': symbol_info['bid'],
                    'ask': symbol_info['ask'],
                    'spread': symbol_info['ask'] - symbol_info['bid']
                }
            
            return {'bid': 0.0, 'ask': 0.0, 'spread': 0.0}
            
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return {'bid': 0.0, 'ask': 0.0, 'spread': 0.0}
    
    def calculate_technical_indicators(self, symbol: str, data: pd.DataFrame = None) -> Dict[str, Any]:
        """Calculate technical indicators"""
        try:
            if data is None:
                data = self.get_latest_data(symbol, 200)
            
            if data.empty or len(data) < 20:
                return {}
            
            indicators = {}
            
            # Simple Moving Averages
            indicators['sma_20'] = data['close'].rolling(20).mean().iloc[-1] if len(data) >= 20 else 0
            indicators['sma_50'] = data['close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else 0
            
            # Exponential Moving Averages
            indicators['ema_12'] = data['close'].ewm(span=12).mean().iloc[-1] if len(data) >= 12 else 0
            indicators['ema_26'] = data['close'].ewm(span=26).mean().iloc[-1] if len(data) >= 26 else 0
            
            # RSI
            indicators['rsi'] = self._calculate_rsi(data['close'], 14)
            
            # Bollinger Bands
            bb_data = self._calculate_bollinger_bands(data['close'], 20, 2)
            indicators.update(bb_data)
            
            # MACD
            macd_data = self._calculate_macd(data['close'])
            indicators.update(macd_data)
            
            # ATR
            indicators['atr'] = self._calculate_atr(data, 14)
            
            # Volume analysis
            if 'tick_volume' in data.columns:
                indicators['volume_sma'] = data['tick_volume'].rolling(20).mean().iloc[-1]
                indicators['volume_ratio'] = data['tick_volume'].iloc[-1] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else 50.0
            
        except Exception:
            return 50.0
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(period).mean()
            std = prices.rolling(period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return {
                'bb_upper': upper_band.iloc[-1] if not upper_band.empty else 0,
                'bb_middle': sma.iloc[-1] if not sma.empty else 0,
                'bb_lower': lower_band.iloc[-1] if not lower_band.empty else 0
            }
            
        except Exception:
            return {'bb_upper': 0, 'bb_middle': 0, 'bb_lower': 0}
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line.iloc[-1] if not macd_line.empty else 0,
                'macd_signal': signal_line.iloc[-1] if not signal_line.empty else 0,
                'macd_histogram': histogram.iloc[-1] if not histogram.empty else 0
            }
            
        except Exception:
            return {'macd': 0, 'macd_signal': 0, 'macd_histogram': 0}
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(period).mean()
            
            return atr.iloc[-1] if not atr.empty else 0
            
        except Exception:
            return 0
    
    def get_market_condition(self, symbol: str) -> Dict[str, Any]:
        """Analyze market condition"""
        try:
            data = self.get_latest_data(symbol, 100)
            if data.empty:
                return {'condition': 'unknown', 'volatility': 'normal', 'trend': 'sideways'}
            
            # Calculate volatility
            volatility = data['close'].pct_change().std() * 100
            
            # Determine volatility level
            if volatility > 1.5:
                vol_level = 'high'
            elif volatility < 0.5:
                vol_level = 'low'
            else:
                vol_level = 'normal'
            
            # Determine trend
            sma_20 = data['close'].rolling(20).mean()
            sma_50 = data['close'].rolling(50).mean()
            
            if len(sma_20) >= 2 and len(sma_50) >= 2:
                if sma_20.iloc[-1] > sma_50.iloc[-1] and sma_20.iloc[-1] > sma_20.iloc[-2]:
                    trend = 'uptrend'
                elif sma_20.iloc[-1] < sma_50.iloc[-1] and sma_20.iloc[-1] < sma_20.iloc[-2]:
                    trend = 'downtrend'
                else:
                    trend = 'sideways'
            else:
                trend = 'sideways'
            
            # Determine overall condition
            if vol_level == 'high':
                condition = 'volatile'
            elif trend in ['uptrend', 'downtrend']:
                condition = 'trending'
            else:
                condition = 'ranging'
            
            return {
                'condition': condition,
                'volatility': vol_level,
                'trend': trend,
                'volatility_value': volatility
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market condition for {symbol}: {e}")
            return {'condition': 'unknown', 'volatility': 'normal', 'trend': 'sideways'}
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get data manager status"""
        try:
            status = {
                'running': self.running,
                'symbols_count': len(self.data_cache),
                'subscribers_count': sum(len(subs) for subs in self.subscribers.values()),
                'last_updates': {}
            }
            
            for symbol, cache_data in self.data_cache.items():
                status['last_updates'][symbol] = cache_data['last_update']
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting data status: {e}")
            return {'running': False, 'symbols_count': 0, 'subscribers_count': 0}
