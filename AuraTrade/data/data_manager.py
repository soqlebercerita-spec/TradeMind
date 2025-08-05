
"""
Data management system for AuraTrade Bot
Handles real-time data feeds, historical data, and market analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import time
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class DataManager:
    """Data management and real-time feed handler"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.mt5_connector = mt5_connector
        self.logger = Logger().get_logger()
        
        # Data storage
        self.live_data = {}
        self.historical_data = {}
        
        # Update control
        self.update_thread = None
        self.updating = False
        self.update_interval = 1  # seconds
        
        # Symbols to monitor
        self.monitored_symbols = []
        
    def start_data_updates(self, symbols: List[str]):
        """Start real-time data updates for specified symbols"""
        try:
            self.monitored_symbols = symbols
            self.updating = True
            
            # Initialize data for all symbols
            for symbol in symbols:
                self._initialize_symbol_data(symbol)
            
            # Start update thread
            self.update_thread = threading.Thread(target=self._data_update_loop, daemon=True)
            self.update_thread.start()
            
            self.logger.info(f"Started data updates for {len(symbols)} symbols")
            
        except Exception as e:
            self.logger.error(f"Error starting data updates: {e}")
    
    def stop_data_updates(self):
        """Stop real-time data updates"""
        try:
            self.updating = False
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=5)
            
            self.logger.info("Data updates stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping data updates: {e}")
    
    def _initialize_symbol_data(self, symbol: str):
        """Initialize historical data for symbol"""
        try:
            # Get initial historical data for multiple timeframes
            timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
            
            self.historical_data[symbol] = {}
            
            for tf in timeframes:
                data = self.mt5_connector.get_rates(symbol, tf, 1000)
                if data is not None:
                    # Add technical indicators
                    data = self._add_technical_indicators(data)
                    self.historical_data[symbol][tf] = data
                    
            self.logger.info(f"Initialized data for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error initializing data for {symbol}: {e}")
    
    def _data_update_loop(self):
        """Main data update loop"""
        while self.updating:
            try:
                for symbol in self.monitored_symbols:
                    self._update_symbol_data(symbol)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in data update loop: {e}")
                time.sleep(1)
    
    def _update_symbol_data(self, symbol: str):
        """Update data for single symbol"""
        try:
            # Update current prices
            current_price = self.mt5_connector.get_current_price(symbol)
            if current_price:
                bid, ask = current_price
                self.live_data[symbol] = {
                    'bid': bid,
                    'ask': ask,
                    'spread': ask - bid,
                    'timestamp': datetime.now()
                }
            
            # Update M1 data (most frequent)
            if symbol in self.historical_data:
                m1_data = self.mt5_connector.get_rates(symbol, 'M1', 100)
                if m1_data is not None:
                    m1_data = self._add_technical_indicators(m1_data)
                    self.historical_data[symbol]['M1'] = m1_data
                    
        except Exception as e:
            self.logger.error(f"Error updating data for {symbol}: {e}")
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to price data"""
        try:
            if len(data) < 50:
                return data
            
            # Moving Averages
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            data['ema_12'] = data['close'].ewm(span=12).mean()
            data['ema_26'] = data['close'].ewm(span=26).mean()
            
            # RSI
            data['rsi'] = self._calculate_rsi(data['close'], 14)
            
            # MACD
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=9).mean()
            data['macd_histogram'] = data['macd'] - data['macd_signal']
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            data['bb_middle'] = data['close'].rolling(window=bb_period).mean()
            bb_std_dev = data['close'].rolling(window=bb_period).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std_dev * bb_std)
            data['bb_lower'] = data['bb_middle'] - (bb_std_dev * bb_std)
            
            # ATR
            data['atr'] = self._calculate_atr(data, 14)
            
            # Stochastic
            stoch_k, stoch_d = self._calculate_stochastic(data, 14, 3)
            data['stoch_k'] = stoch_k
            data['stoch_d'] = stoch_d
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error adding technical indicators: {e}")
            return data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series(index=prices.index, dtype=float)
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            tr1 = data['high'] - data['low']
            tr2 = abs(data['high'] - data['close'].shift())
            tr3 = abs(data['low'] - data['close'].shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return atr
        except:
            return pd.Series(index=data.index, dtype=float)
    
    def _calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, 
                            d_period: int = 3) -> tuple:
        """Calculate Stochastic Oscillator"""
        try:
            lowest_low = data['low'].rolling(window=k_period).min()
            highest_high = data['high'].rolling(window=k_period).max()
            k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            return k_percent, d_percent
        except:
            return pd.Series(index=data.index, dtype=float), pd.Series(index=data.index, dtype=float)
    
    def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical rates with indicators"""
        try:
            if symbol in self.historical_data and timeframe in self.historical_data[symbol]:
                data = self.historical_data[symbol][timeframe]
                return data.tail(count) if len(data) > count else data
            
            # Fallback to MT5 direct call
            data = self.mt5_connector.get_rates(symbol, timeframe, count)
            if data is not None:
                data = self._add_technical_indicators(data)
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[tuple]:
        """Get current bid/ask price"""
        try:
            if symbol in self.live_data:
                data = self.live_data[symbol]
                return (data['bid'], data['ask'])
            
            # Fallback to MT5 direct call
            return self.mt5_connector.get_current_price(symbol)
            
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def analyze_market_condition(self, symbol: str, timeframe: str = 'H1') -> Dict[str, Any]:
        """Analyze current market conditions"""
        try:
            data = self.get_rates(symbol, timeframe, 100)
            if data is None or len(data) < 50:
                return {}
            
            latest = data.iloc[-1]
            
            # Trend analysis
            sma_20 = latest['sma_20']
            sma_50 = latest['sma_50']
            current_price = latest['close']
            
            trend = 'bullish' if sma_20 > sma_50 and current_price > sma_20 else \
                   'bearish' if sma_20 < sma_50 and current_price < sma_20 else 'sideways'
            
            # Volatility analysis
            atr = latest['atr']
            atr_avg = data['atr'].tail(20).mean()
            volatility = 'high' if atr > atr_avg * 1.5 else \
                        'low' if atr < atr_avg * 0.7 else 'normal'
            
            # Momentum analysis
            rsi = latest['rsi']
            momentum = 'overbought' if rsi > 70 else \
                      'oversold' if rsi < 30 else 'neutral'
            
            return {
                'trend': trend,
                'volatility': volatility,
                'momentum': momentum,
                'rsi': rsi,
                'atr': atr,
                'price_above_sma20': current_price > sma_20,
                'price_above_sma50': current_price > sma_50
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market condition: {e}")
            return {}
    
    def get_support_resistance_levels(self, symbol: str, timeframe: str = 'H4') -> Dict[str, List[float]]:
        """Calculate dynamic support and resistance levels"""
        try:
            data = self.get_rates(symbol, timeframe, 200)
            if data is None or len(data) < 100:
                return {'support': [], 'resistance': []}
            
            # Find local highs and lows
            highs = []
            lows = []
            
            for i in range(5, len(data) - 5):
                # Local high
                if all(data['high'].iloc[i] >= data['high'].iloc[i-j] for j in range(1, 6)) and \
                   all(data['high'].iloc[i] >= data['high'].iloc[i+j] for j in range(1, 6)):
                    highs.append(data['high'].iloc[i])
                
                # Local low
                if all(data['low'].iloc[i] <= data['low'].iloc[i-j] for j in range(1, 6)) and \
                   all(data['low'].iloc[i] <= data['low'].iloc[i+j] for j in range(1, 6)):
                    lows.append(data['low'].iloc[i])
            
            # Filter and sort levels
            resistance_levels = sorted(list(set(highs)), reverse=True)[:5]
            support_levels = sorted(list(set(lows)))[:5]
            
            return {
                'support': support_levels,
                'resistance': resistance_levels
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating S/R levels: {e}")
            return {'support': [], 'resistance': []}
