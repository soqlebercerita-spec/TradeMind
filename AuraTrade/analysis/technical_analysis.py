
"""
Technical Analysis Module for AuraTrade Bot
Comprehensive technical indicators and trend analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from utils.logger import Logger

class TechnicalAnalysis:
    """Technical analysis with multiple indicators"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.logger.info("Technical Analysis initialized")
    
    def analyze_trends(self, rates: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market trends using multiple indicators"""
        try:
            if len(rates) < 50:
                return {}
            
            indicators = self.calculate_all_indicators(rates)
            
            # Determine overall trend
            trend = self._determine_trend(rates, indicators)
            
            return {
                'trend': trend,
                'rsi': indicators.get('rsi', 50),
                'macd': indicators.get('macd_line', 0),
                'bollinger_position': self._get_bollinger_position(rates, indicators),
                'volume_trend': self._analyze_volume_trend(rates),
                'support_resistance': self._find_support_resistance(rates)
            }
            
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return {}
    
    def calculate_all_indicators(self, rates: pd.DataFrame) -> Dict[str, float]:
        """Calculate all technical indicators"""
        try:
            close = rates['close']
            high = rates['high']
            low = rates['low']
            volume = rates.get('tick_volume', pd.Series([1] * len(rates)))
            
            indicators = {}
            
            # Moving Averages
            indicators['sma_20'] = close.rolling(20).mean().iloc[-1]
            indicators['sma_50'] = close.rolling(50).mean().iloc[-1]
            indicators['ema_12'] = close.ewm(span=12).mean().iloc[-1]
            indicators['ema_26'] = close.ewm(span=26).mean().iloc[-1]
            
            # RSI
            indicators['rsi'] = self._calculate_rsi(close).iloc[-1]
            
            # MACD
            macd_line, signal_line, histogram = self._calculate_macd(close)
            indicators['macd_line'] = macd_line.iloc[-1]
            indicators['macd_signal'] = signal_line.iloc[-1]
            indicators['macd_histogram'] = histogram.iloc[-1]
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close)
            indicators['bb_upper'] = bb_upper.iloc[-1]
            indicators['bb_middle'] = bb_middle.iloc[-1]
            indicators['bb_lower'] = bb_lower.iloc[-1]
            
            # Stochastic
            stoch_k, stoch_d = self._calculate_stochastic(high, low, close)
            indicators['stoch_k'] = stoch_k.iloc[-1]
            indicators['stoch_d'] = stoch_d.iloc[-1]
            
            # Williams %R
            indicators['williams_r'] = self._calculate_williams_r(high, low, close).iloc[-1]
            
            # Average True Range (ATR)
            indicators['atr'] = self._calculate_atr(high, low, close).iloc[-1]
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=3).mean()
        return k_percent, d_percent
    
    def _calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        return williams_r
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        hl = high - low
        hc = np.abs(high - close.shift())
        lc = np.abs(low - close.shift())
        tr = pd.DataFrame({'hl': hl, 'hc': hc, 'lc': lc}).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def _determine_trend(self, rates: pd.DataFrame, indicators: Dict) -> str:
        """Determine overall market trend"""
        try:
            close = rates['close'].iloc[-1]
            sma_20 = indicators.get('sma_20', close)
            sma_50 = indicators.get('sma_50', close)
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd_histogram', 0)
            
            bullish_signals = 0
            bearish_signals = 0
            
            # Price vs Moving Averages
            if close > sma_20:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            if sma_20 > sma_50:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # RSI
            if rsi > 50:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # MACD
            if macd > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            if bullish_signals > bearish_signals:
                return 'BULLISH'
            elif bearish_signals > bullish_signals:
                return 'BEARISH'
            else:
                return 'NEUTRAL'
                
        except Exception:
            return 'NEUTRAL'
    
    def _get_bollinger_position(self, rates: pd.DataFrame, indicators: Dict) -> str:
        """Get Bollinger Bands position"""
        try:
            close = rates['close'].iloc[-1]
            bb_upper = indicators.get('bb_upper', close)
            bb_lower = indicators.get('bb_lower', close)
            bb_middle = indicators.get('bb_middle', close)
            
            if close >= bb_upper:
                return 'UPPER'
            elif close <= bb_lower:
                return 'LOWER'
            elif close > bb_middle:
                return 'MIDDLE_HIGH'
            else:
                return 'MIDDLE_LOW'
                
        except Exception:
            return 'MIDDLE'
    
    def _analyze_volume_trend(self, rates: pd.DataFrame) -> str:
        """Analyze volume trend"""
        try:
            if 'tick_volume' not in rates.columns:
                return 'NORMAL'
            
            volume = rates['tick_volume']
            recent_avg = volume.tail(10).mean()
            overall_avg = volume.tail(50).mean()
            
            if recent_avg > overall_avg * 1.2:
                return 'HIGH'
            elif recent_avg < overall_avg * 0.8:
                return 'LOW'
            else:
                return 'NORMAL'
                
        except Exception:
            return 'NORMAL'
    
    def _find_support_resistance(self, rates: pd.DataFrame, period: int = 20) -> Dict:
        """Find support and resistance levels"""
        try:
            high = rates['high']
            low = rates['low']
            
            # Recent highs and lows
            recent_high = high.tail(period).max()
            recent_low = low.tail(period).min()
            
            return {
                'resistance': recent_high,
                'support': recent_low,
                'range': recent_high - recent_low
            }
            
        except Exception:
            return {'resistance': 0, 'support': 0, 'range': 0}

class TechnicalAnalysis:
    """Advanced technical analysis with multiple indicators"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.logger.info("Technical Analysis module initialized")
    
    def analyze_trends(self, rates: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive trend analysis using multiple indicators"""
        try:
            if rates is None or len(rates) < 50:
                return self._get_default_analysis()
            
            # Calculate all indicators
            analysis = {
                'trend': self._determine_trend(rates),
                'rsi': self._calculate_rsi(rates),
                'macd': self._calculate_macd(rates),
                'bollinger_position': self._calculate_bollinger_bands(rates),
                'volume_trend': self._analyze_volume_trend(rates),
                'moving_averages': self._calculate_moving_averages(rates),
                'support_resistance': self._calculate_support_resistance(rates),
                'momentum': self._calculate_momentum(rates),
                'volatility': self._calculate_volatility(rates),
                'fibonacci': self._calculate_fibonacci_levels(rates),
                'pivot_points': self._calculate_pivot_points(rates),
                'stochastic': self._calculate_stochastic(rates),
                'atr': self._calculate_atr(rates),
                'wma': self._calculate_wma(rates),
                'timestamp': datetime.now()
            }
            
            # Overall signal strength
            analysis['signal_strength'] = self._calculate_signal_strength(analysis)
            analysis['market_condition'] = self._determine_market_condition(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Default analysis when calculation fails"""
        return {
            'trend': 'NEUTRAL',
            'rsi': 50.0,
            'macd': 0.0,
            'bollinger_position': 'MIDDLE',
            'volume_trend': 'NORMAL',
            'signal_strength': 0.0,
            'market_condition': 'SIDEWAYS',
            'timestamp': datetime.now()
        }
    
    def _determine_trend(self, rates: pd.DataFrame) -> str:
        """Determine overall trend using multiple timeframes"""
        try:
            closes = rates['close']
            
            # Short-term trend (20 periods)
            sma20 = closes.rolling(window=20).mean()
            short_trend = "BULLISH" if closes.iloc[-1] > sma20.iloc[-1] else "BEARISH"
            
            # Medium-term trend (50 periods)
            sma50 = closes.rolling(window=50).mean()
            medium_trend = "BULLISH" if closes.iloc[-1] > sma50.iloc[-1] else "BEARISH"
            
            # Long-term trend direction
            price_change = (closes.iloc[-1] - closes.iloc[-20]) / closes.iloc[-20] * 100
            
            if short_trend == medium_trend:
                if abs(price_change) > 1.0:  # Strong trend
                    return short_trend
                else:
                    return "WEAK_" + short_trend
            
            return "NEUTRAL"
            
        except Exception as e:
            self.logger.error(f"Error determining trend: {e}")
            return "NEUTRAL"
    
    def _calculate_rsi(self, rates: pd.DataFrame, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        try:
            delta = rates['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return 50.0
    
    def _calculate_macd(self, rates: pd.DataFrame) -> Dict[str, float]:
        """Calculate MACD indicator"""
        try:
            closes = rates['close']
            
            # Calculate EMAs
            ema12 = closes.ewm(span=12).mean()
            ema26 = closes.ewm(span=26).mean()
            
            # MACD line
            macd_line = ema12 - ema26
            
            # Signal line
            signal_line = macd_line.ewm(span=9).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]),
                'signal': float(signal_line.iloc[-1]),
                'histogram': float(histogram.iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
    
    def _calculate_bollinger_bands(self, rates: pd.DataFrame, period: int = 20) -> str:
        """Calculate Bollinger Bands position"""
        try:
            closes = rates['close']
            sma = closes.rolling(window=period).mean()
            std = closes.rolling(window=period).std()
            
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            current_price = closes.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_middle = sma.iloc[-1]
            
            if current_price >= current_upper:
                return "UPPER"
            elif current_price <= current_lower:
                return "LOWER"
            elif current_price > current_middle:
                return "UPPER_MIDDLE"
            else:
                return "LOWER_MIDDLE"
                
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return "MIDDLE"
    
    def _analyze_volume_trend(self, rates: pd.DataFrame) -> str:
        """Analyze volume trend"""
        try:
            if 'tick_volume' not in rates.columns:
                return "NORMAL"
            
            volumes = rates['tick_volume']
            avg_volume = volumes.rolling(window=20).mean()
            
            recent_volume = volumes.tail(5).mean()
            baseline_volume = avg_volume.iloc[-1]
            
            if recent_volume > baseline_volume * 1.5:
                return "HIGH"
            elif recent_volume < baseline_volume * 0.7:
                return "LOW"
            else:
                return "NORMAL"
                
        except Exception as e:
            self.logger.error(f"Error analyzing volume: {e}")
            return "NORMAL"
    
    def _calculate_moving_averages(self, rates: pd.DataFrame) -> Dict[str, float]:
        """Calculate various moving averages"""
        try:
            closes = rates['close']
            
            return {
                'sma10': float(closes.rolling(window=10).mean().iloc[-1]),
                'sma20': float(closes.rolling(window=20).mean().iloc[-1]),
                'sma50': float(closes.rolling(window=50).mean().iloc[-1]),
                'ema10': float(closes.ewm(span=10).mean().iloc[-1]),
                'ema20': float(closes.ewm(span=20).mean().iloc[-1]),
                'ema50': float(closes.ewm(span=50).mean().iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating moving averages: {e}")
            return {}
    
    def _calculate_support_resistance(self, rates: pd.DataFrame) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        try:
            highs = rates['high'].tail(50)
            lows = rates['low'].tail(50)
            
            # Find local maxima and minima
            resistance_levels = []
            support_levels = []
            
            for i in range(2, len(highs) - 2):
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and
                    highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
                    resistance_levels.append(highs.iloc[i])
                
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2] and
                    lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]):
                    support_levels.append(lows.iloc[i])
            
            return {
                'resistance': float(np.mean(resistance_levels)) if resistance_levels else float(highs.max()),
                'support': float(np.mean(support_levels)) if support_levels else float(lows.min())
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance: {e}")
            return {'resistance': 0.0, 'support': 0.0}
    
    def _calculate_momentum(self, rates: pd.DataFrame, period: int = 14) -> float:
        """Calculate price momentum"""
        try:
            closes = rates['close']
            momentum = (closes.iloc[-1] - closes.iloc[-period]) / closes.iloc[-period] * 100
            return float(momentum)
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum: {e}")
            return 0.0
    
    def _calculate_volatility(self, rates: pd.DataFrame, period: int = 20) -> float:
        """Calculate price volatility"""
        try:
            returns = rates['close'].pct_change()
            volatility = returns.rolling(window=period).std() * np.sqrt(period) * 100
            return float(volatility.iloc[-1])
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def _calculate_fibonacci_levels(self, rates: pd.DataFrame) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        try:
            highs = rates['high'].tail(50)
            lows = rates['low'].tail(50)
            
            high_price = highs.max()
            low_price = lows.min()
            diff = high_price - low_price
            
            return {
                'level_0': float(high_price),
                'level_236': float(high_price - 0.236 * diff),
                'level_382': float(high_price - 0.382 * diff),
                'level_500': float(high_price - 0.500 * diff),
                'level_618': float(high_price - 0.618 * diff),
                'level_100': float(low_price)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Fibonacci levels: {e}")
            return {}
    
    def _calculate_pivot_points(self, rates: pd.DataFrame) -> Dict[str, float]:
        """Calculate pivot points for daily/weekly levels"""
        try:
            # Use last complete day's data
            yesterday = rates.tail(24) if len(rates) >= 24 else rates
            
            high = yesterday['high'].max()
            low = yesterday['low'].min()
            close = yesterday['close'].iloc[-1]
            
            pivot = (high + low + close) / 3
            
            return {
                'pivot': float(pivot),
                'resistance1': float(2 * pivot - low),
                'resistance2': float(pivot + (high - low)),
                'support1': float(2 * pivot - high),
                'support2': float(pivot - (high - low))
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating pivot points: {e}")
            return {}
    
    def _calculate_stochastic(self, rates: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """Calculate Stochastic Oscillator"""
        try:
            highs = rates['high'].rolling(window=k_period).max()
            lows = rates['low'].rolling(window=k_period).min()
            closes = rates['close']
            
            k_percent = 100 * ((closes - lows) / (highs - lows))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'k_percent': float(k_percent.iloc[-1]),
                'd_percent': float(d_percent.iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic: {e}")
            return {'k_percent': 50.0, 'd_percent': 50.0}
    
    def _calculate_atr(self, rates: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            highs = rates['high']
            lows = rates['low']
            closes = rates['close']
            
            tr1 = highs - lows
            tr2 = np.abs(highs - closes.shift())
            tr3 = np.abs(lows - closes.shift())
            
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            atr = true_range.rolling(window=period).mean()
            
            return float(atr.iloc[-1])
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return 0.0
    
    def _calculate_wma(self, rates: pd.DataFrame, period: int = 20) -> float:
        """Calculate Weighted Moving Average"""
        try:
            closes = rates['close'].tail(period)
            weights = np.arange(1, period + 1)
            wma = np.average(closes, weights=weights)
            return float(wma)
            
        except Exception as e:
            self.logger.error(f"Error calculating WMA: {e}")
            return 0.0
    
    def _calculate_signal_strength(self, analysis: Dict) -> float:
        """Calculate overall signal strength from all indicators"""
        try:
            strength = 0.0
            
            # RSI contribution
            rsi = analysis.get('rsi', 50)
            if rsi > 70:
                strength += 15  # Overbought
            elif rsi < 30:
                strength += 15  # Oversold
            elif 40 < rsi < 60:
                strength += 5   # Neutral zone
            
            # MACD contribution
            macd_data = analysis.get('macd', {})
            if isinstance(macd_data, dict):
                macd = macd_data.get('macd', 0)
                signal = macd_data.get('signal', 0)
                if macd > signal:
                    strength += 10  # Bullish crossover
                elif macd < signal:
                    strength += 10  # Bearish crossover
            
            # Trend contribution
            trend = analysis.get('trend', 'NEUTRAL')
            if trend in ['BULLISH', 'BEARISH']:
                strength += 20
            elif trend in ['WEAK_BULLISH', 'WEAK_BEARISH']:
                strength += 10
            
            # Bollinger Bands contribution
            bb_position = analysis.get('bollinger_position', 'MIDDLE')
            if bb_position in ['UPPER', 'LOWER']:
                strength += 15
            
            # Volume contribution
            volume_trend = analysis.get('volume_trend', 'NORMAL')
            if volume_trend == 'HIGH':
                strength += 10
            
            return min(strength, 100.0)  # Cap at 100%
            
        except Exception as e:
            self.logger.error(f"Error calculating signal strength: {e}")
            return 0.0
    
    def _determine_market_condition(self, analysis: Dict) -> str:
        """Determine current market condition"""
        try:
            trend = analysis.get('trend', 'NEUTRAL')
            volatility = analysis.get('volatility', 0)
            signal_strength = analysis.get('signal_strength', 0)
            
            if signal_strength > 70:
                if 'BULLISH' in trend:
                    return 'STRONG_UPTREND'
                elif 'BEARISH' in trend:
                    return 'STRONG_DOWNTREND'
                else:
                    return 'VOLATILE'
            elif signal_strength > 40:
                if 'BULLISH' in trend:
                    return 'UPTREND'
                elif 'BEARISH' in trend:
                    return 'DOWNTREND'
                else:
                    return 'SIDEWAYS'
            else:
                return 'CONSOLIDATION'
                
        except Exception as e:
            self.logger.error(f"Error determining market condition: {e}")
            return 'UNKNOWN'
    
    def get_trading_signals(self, rates: pd.DataFrame) -> Dict[str, Any]:
        """Get specific trading signals based on technical analysis"""
        try:
            analysis = self.analyze_trends(rates)
            
            signals = {
                'buy_signals': [],
                'sell_signals': [],
                'neutral_signals': [],
                'overall_signal': 'NEUTRAL',
                'confidence': 0.0
            }
            
            # RSI signals
            rsi = analysis.get('rsi', 50)
            if rsi < 30:
                signals['buy_signals'].append('RSI_Oversold')
            elif rsi > 70:
                signals['sell_signals'].append('RSI_Overbought')
            
            # MACD signals
            macd_data = analysis.get('macd', {})
            if isinstance(macd_data, dict):
                macd = macd_data.get('macd', 0)
                signal_line = macd_data.get('signal', 0)
                if macd > signal_line and macd > 0:
                    signals['buy_signals'].append('MACD_Bullish')
                elif macd < signal_line and macd < 0:
                    signals['sell_signals'].append('MACD_Bearish')
            
            # Trend signals
            trend = analysis.get('trend', 'NEUTRAL')
            if 'BULLISH' in trend:
                signals['buy_signals'].append('Trend_Bullish')
            elif 'BEARISH' in trend:
                signals['sell_signals'].append('Trend_Bearish')
            
            # Determine overall signal
            buy_count = len(signals['buy_signals'])
            sell_count = len(signals['sell_signals'])
            
            if buy_count > sell_count and buy_count >= 2:
                signals['overall_signal'] = 'BUY'
                signals['confidence'] = min((buy_count / 5.0) * 100, 95)
            elif sell_count > buy_count and sell_count >= 2:
                signals['overall_signal'] = 'SELL'
                signals['confidence'] = min((sell_count / 5.0) * 100, 95)
            else:
                signals['overall_signal'] = 'NEUTRAL'
                signals['confidence'] = analysis.get('signal_strength', 0) / 2
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error getting trading signals: {e}")
            return {
                'buy_signals': [],
                'sell_signals': [],
                'neutral_signals': [],
                'overall_signal': 'NEUTRAL',
                'confidence': 0.0
            }
