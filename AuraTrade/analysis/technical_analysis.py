"""
Technical analysis indicators without TA-Lib dependency
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from utils.logger import Logger

class TechnicalAnalysis:
    """Technical analysis calculations"""

    def __init__(self):
        self.logger = Logger().get_logger()

    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        try:
            df = data.copy()

            # Moving averages
            df['sma_20'] = self.sma(df['close'], 20)
            df['sma_50'] = self.sma(df['close'], 50)
            df['ema_12'] = self.ema(df['close'], 12)
            df['ema_26'] = self.ema(df['close'], 26)

            # RSI
            df['rsi'] = self.rsi(df['close'], 14)

            # MACD
            macd_data = self.macd(df['close'])
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']

            # Bollinger Bands
            bb_data = self.bollinger_bands(df['close'], 20, 2)
            df['bb_upper'] = bb_data['upper']
            df['bb_middle'] = bb_data['middle']
            df['bb_lower'] = bb_data['lower']

            # ATR
            df['atr'] = self.atr(df, 14)

            # Stochastic
            stoch_data = self.stochastic(df)
            df['stoch_k'] = stoch_data['%K']
            df['stoch_d'] = stoch_data['%D']

            return df

        except Exception as e:
            self.logger.error(f"Failed to calculate indicators: {e}")
            return data

    def sma(self, series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return series.rolling(window=period).mean()

    def ema(self, series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()

    def rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        try:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

        except Exception as e:
            self.logger.error(f"Failed to calculate RSI: {e}")
            return pd.Series()

    def macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD Indicator"""
        try:
            exp1 = series.ewm(span=fast, adjust=False).mean()
            exp2 = series.ewm(span=slow, adjust=False).mean()

            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line

            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate MACD: {e}")
            return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}

    def bollinger_bands(self, series: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        try:
            middle = series.rolling(window=period).mean()
            std = series.rolling(window=period).std()

            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)

            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate Bollinger Bands: {e}")
            return {'upper': pd.Series(), 'middle': pd.Series(), 'lower': pd.Series()}

    def atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        try:
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()

            return atr

        except Exception as e:
            self.logger.error(f"Failed to calculate ATR: {e}")
            return pd.Series()

    def stochastic(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        try:
            lowest_low = data['low'].rolling(window=k_period).min()
            highest_high = data['high'].rolling(window=k_period).max()

            k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()

            return {
                '%K': k_percent,
                '%D': d_percent
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate Stochastic: {e}")
            return {'%K': pd.Series(), '%D': pd.Series()}

    def williams_r(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Williams %R"""
        try:
            highest_high = data['high'].rolling(window=period).max()
            lowest_low = data['low'].rolling(window=period).min()

            wr = -100 * ((highest_high - data['close']) / (highest_high - lowest_low))

            return wr

        except Exception as e:
            self.logger.error(f"Failed to calculate Williams %R: {e}")
            return pd.Series()

    def detect_trend(self, data: pd.DataFrame) -> str:
        """Detect trend direction"""
        try:
            if len(data) < 50:
                return 'unknown'

            sma_20 = self.sma(data['close'], 20)
            sma_50 = self.sma(data['close'], 50)

            if sma_20.iloc[-1] > sma_50.iloc[-1] and data['close'].iloc[-1] > sma_20.iloc[-1]:
                return 'uptrend'
            elif sma_20.iloc[-1] < sma_50.iloc[-1] and data['close'].iloc[-1] < sma_20.iloc[-1]:
                return 'downtrend'
            else:
                return 'sideways'

        except Exception as e:
            self.logger.error(f"Failed to detect trend: {e}")
            return 'unknown'

    def calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        try:
            if len(data) < 20:
                return {'support': 0, 'resistance': 0}

            # Use recent highs and lows
            recent_data = data.tail(50)

            # Find local maxima and minima
            highs = recent_data['high'].rolling(window=5, center=True).max()
            lows = recent_data['low'].rolling(window=5, center=True).min()

            resistance_levels = highs[highs == recent_data['high']].values
            support_levels = lows[lows == recent_data['low']].values

            current_price = data['close'].iloc[-1]

            # Find nearest levels
            resistance = np.min(resistance_levels[resistance_levels > current_price]) if len(resistance_levels[resistance_levels > current_price]) > 0 else current_price * 1.01
            support = np.max(support_levels[support_levels < current_price]) if len(support_levels[support_levels < current_price]) > 0 else current_price * 0.99

            return {
                'support': support,
                'resistance': resistance
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate support/resistance: {e}")
            return {'support': 0, 'resistance': 0}