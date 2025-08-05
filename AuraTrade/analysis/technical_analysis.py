
"""
Technical Analysis Module for AuraTrade Bot
Comprehensive technical indicators and analysis functions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from utils.logger import Logger

class TechnicalAnalysis:
    """Technical analysis calculator"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for given data"""
        try:
            if len(data) < 50:
                return data
            
            # Moving Averages
            data = self.add_moving_averages(data)
            
            # Oscillators
            data = self.add_oscillators(data)
            
            # Volatility indicators
            data = self.add_volatility_indicators(data)
            
            # Volume indicators (if available)
            data = self.add_volume_indicators(data)
            
            # Trend indicators
            data = self.add_trend_indicators(data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return data
    
    def add_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add moving average indicators"""
        try:
            # Simple Moving Averages
            data['sma_10'] = data['close'].rolling(window=10).mean()
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            data['sma_100'] = data['close'].rolling(window=100).mean()
            data['sma_200'] = data['close'].rolling(window=200).mean()
            
            # Exponential Moving Averages
            data['ema_12'] = data['close'].ewm(span=12).mean()
            data['ema_26'] = data['close'].ewm(span=26).mean()
            data['ema_50'] = data['close'].ewm(span=50).mean()
            data['ema_100'] = data['close'].ewm(span=100).mean()
            
            # Weighted Moving Average
            data['wma_20'] = self._calculate_wma(data['close'], 20)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error adding moving averages: {e}")
            return data
    
    def add_oscillators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add oscillator indicators"""
        try:
            # RSI
            data['rsi_14'] = self.calculate_rsi(data['close'], 14)
            data['rsi_21'] = self.calculate_rsi(data['close'], 21)
            
            # Stochastic Oscillator
            data['stoch_k'], data['stoch_d'] = self.calculate_stochastic(data, 14, 3)
            
            # Williams %R
            data['williams_r'] = self.calculate_williams_r(data, 14)
            
            # MACD
            data['macd'], data['macd_signal'], data['macd_histogram'] = self.calculate_macd(data['close'])
            
            # CCI (Commodity Channel Index)
            data['cci'] = self.calculate_cci(data, 20)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error adding oscillators: {e}")
            return data
    
    def add_volatility_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        try:
            # Average True Range
            data['atr_14'] = self.calculate_atr(data, 14)
            data['atr_21'] = self.calculate_atr(data, 21)
            
            # Bollinger Bands
            data['bb_upper_20'], data['bb_middle_20'], data['bb_lower_20'] = self.calculate_bollinger_bands(data['close'], 20, 2)
            
            # Keltner Channels
            data['kc_upper'], data['kc_middle'], data['kc_lower'] = self.calculate_keltner_channels(data, 20, 2)
            
            # Donchian Channels
            data['dc_upper'], data['dc_lower'] = self.calculate_donchian_channels(data, 20)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error adding volatility indicators: {e}")
            return data
    
    def add_volume_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators"""
        try:
            # For Forex, we don't have real volume, so we'll use tick volume approximation
            if 'tick_volume' not in data.columns:
                # Approximate tick volume using price range
                data['tick_volume'] = (data['high'] - data['low']) * 1000000
            
            # Volume Moving Average
            data['volume_sma'] = data['tick_volume'].rolling(window=20).mean()
            
            # On Balance Volume (OBV)
            data['obv'] = self.calculate_obv(data)
            
            # Volume Rate of Change
            data['volume_roc'] = data['tick_volume'].pct_change(periods=10) * 100
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error adding volume indicators: {e}")
            return data
    
    def add_trend_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators"""
        try:
            # ADX (Average Directional Index)
            data['adx'], data['di_plus'], data['di_minus'] = self.calculate_adx(data, 14)
            
            # Parabolic SAR
            data['psar'] = self.calculate_parabolic_sar(data)
            
            # Aroon Oscillator
            data['aroon_up'], data['aroon_down'] = self.calculate_aroon(data, 25)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error adding trend indicators: {e}")
            return data
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal).mean()
            macd_histogram = macd - macd_signal
            return macd, macd_signal, macd_histogram
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float)
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            return upper_band, sma, lower_band
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float)
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            tr1 = data['high'] - data['low']
            tr2 = abs(data['high'] - data['close'].shift())
            tr3 = abs(data['low'] - data['close'].shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return atr
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        try:
            lowest_low = data['low'].rolling(window=k_period).min()
            highest_high = data['high'].rolling(window=k_period).max()
            k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            return k_percent, d_percent
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic: {e}")
            return pd.Series(index=data.index, dtype=float), pd.Series(index=data.index, dtype=float)
    
    def calculate_williams_r(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        try:
            highest_high = data['high'].rolling(window=period).max()
            lowest_low = data['low'].rolling(window=period).min()
            williams_r = -100 * ((highest_high - data['close']) / (highest_high - lowest_low))
            return williams_r
        except Exception as e:
            self.logger.error(f"Error calculating Williams %R: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate ADX and Directional Indicators"""
        try:
            # Calculate True Range
            tr = self.calculate_atr(data, 1)
            
            # Calculate Directional Movement
            dm_plus = np.where((data['high'] - data['high'].shift()) > (data['low'].shift() - data['low']),
                              np.maximum(data['high'] - data['high'].shift(), 0), 0)
            dm_minus = np.where((data['low'].shift() - data['low']) > (data['high'] - data['high'].shift()),
                               np.maximum(data['low'].shift() - data['low'], 0), 0)
            
            dm_plus = pd.Series(dm_plus, index=data.index)
            dm_minus = pd.Series(dm_minus, index=data.index)
            
            # Smooth the values
            tr_smooth = tr.rolling(window=period).mean()
            dm_plus_smooth = dm_plus.rolling(window=period).mean()
            dm_minus_smooth = dm_minus.rolling(window=period).mean()
            
            # Calculate DI
            di_plus = 100 * (dm_plus_smooth / tr_smooth)
            di_minus = 100 * (dm_minus_smooth / tr_smooth)
            
            # Calculate DX and ADX
            dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
            adx = dx.rolling(window=period).mean()
            
            return adx, di_plus, di_minus
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return pd.Series(index=data.index, dtype=float), pd.Series(index=data.index, dtype=float), pd.Series(index=data.index, dtype=float)
    
    def calculate_cci(self, data: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        try:
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            sma_tp = typical_price.rolling(window=period).mean()
            mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
            cci = (typical_price - sma_tp) / (0.015 * mad)
            return cci
        except Exception as e:
            self.logger.error(f"Error calculating CCI: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def calculate_obv(self, data: pd.DataFrame) -> pd.Series:
        """Calculate On Balance Volume"""
        try:
            volume = data.get('tick_volume', pd.Series(1, index=data.index))
            price_change = data['close'].diff()
            obv = (np.sign(price_change) * volume).cumsum()
            return obv
        except Exception as e:
            self.logger.error(f"Error calculating OBV: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def calculate_parabolic_sar(self, data: pd.DataFrame, af_start: float = 0.02, af_max: float = 0.2) -> pd.Series:
        """Calculate Parabolic SAR"""
        try:
            psar = data['close'].copy()
            af = af_start
            ep = data['high'].iloc[0]
            trend = 1  # 1 for uptrend, -1 for downtrend
            
            for i in range(1, len(data)):
                prev_psar = psar.iloc[i-1]
                
                if trend == 1:  # Uptrend
                    psar.iloc[i] = prev_psar + af * (ep - prev_psar)
                    
                    if data['high'].iloc[i] > ep:
                        ep = data['high'].iloc[i]
                        af = min(af + af_start, af_max)
                    
                    if data['low'].iloc[i] < psar.iloc[i]:
                        trend = -1
                        psar.iloc[i] = ep
                        ep = data['low'].iloc[i]
                        af = af_start
                        
                else:  # Downtrend
                    psar.iloc[i] = prev_psar - af * (prev_psar - ep)
                    
                    if data['low'].iloc[i] < ep:
                        ep = data['low'].iloc[i]
                        af = min(af + af_start, af_max)
                    
                    if data['high'].iloc[i] > psar.iloc[i]:
                        trend = 1
                        psar.iloc[i] = ep
                        ep = data['high'].iloc[i]
                        af = af_start
            
            return psar
        except Exception as e:
            self.logger.error(f"Error calculating Parabolic SAR: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def _calculate_wma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Weighted Moving Average"""
        try:
            weights = np.arange(1, period + 1)
            wma = prices.rolling(window=period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
            return wma
        except Exception as e:
            self.logger.error(f"Error calculating WMA: {e}")
            return pd.Series(index=prices.index, dtype=float)
"""
Technical Analysis Module for AuraTrade
Comprehensive technical indicators and analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class TechnicalAnalysis:
    """Technical analysis indicators and calculations"""
    
    def __init__(self):
        pass
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for the dataset"""
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
