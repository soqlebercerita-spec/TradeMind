
"""
Technical Analysis Module for AuraTrade Bot
Implements all required technical indicators without TA-Lib
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from utils.logger import Logger

class TechnicalAnalysis:
    """Complete technical analysis system without TA-Lib dependency"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.logger.info("Technical Analysis module initialized")
    
    def analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Complete trend analysis with all indicators"""
        try:
            if df is None or len(df) < 50:
                return self._get_default_analysis()
            
            # Calculate all indicators
            analysis = {
                'ma10': self._calculate_ma(df, 10),
                'ema50': self._calculate_ema(df, 50),
                'bollinger': self._calculate_bollinger_bands(df),
                'rsi': self._calculate_rsi(df),
                'macd': self._calculate_macd(df),
                'wma': self._calculate_wma(df, 20),
                'stochastic': self._calculate_stochastic(df),
                'atr': self._calculate_atr(df),
                'fibonacci': self._calculate_fibonacci_levels(df),
                'pivot_points': self._calculate_pivot_points(df),
                'support_resistance': self._calculate_support_resistance(df)
            }
            
            # Determine overall trend
            analysis['trend'] = self._determine_trend(df, analysis)
            analysis['momentum'] = self._calculate_momentum(df, analysis)
            analysis['signal_strength'] = self._calculate_signal_strength(analysis)
            analysis['bollinger_position'] = self._get_bollinger_position(df, analysis['bollinger'])
            analysis['volume_trend'] = self._analyze_volume_trend(df)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return self._get_default_analysis()
    
    def _calculate_ma(self, df: pd.DataFrame, period: int) -> float:
        """Simple Moving Average"""
        try:
            return df['close'].rolling(window=period).mean().iloc[-1]
        except:
            return 0.0
    
    def _calculate_ema(self, df: pd.DataFrame, period: int) -> float:
        """Exponential Moving Average"""
        try:
            return df['close'].ewm(span=period).mean().iloc[-1]
        except:
            return 0.0
    
    def _calculate_wma(self, df: pd.DataFrame, period: int) -> float:
        """Weighted Moving Average"""
        try:
            weights = np.arange(1, period + 1)
            wma = df['close'].rolling(window=period).apply(
                lambda prices: np.dot(prices, weights) / weights.sum(), raw=True
            )
            return wma.iloc[-1]
        except:
            return 0.0
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: int = 2) -> Dict[str, float]:
        """Bollinger Bands"""
        try:
            sma = df['close'].rolling(window=period).mean()
            std_dev = df['close'].rolling(window=period).std()
            
            upper = sma + (std_dev * std)
            lower = sma - (std_dev * std)
            
            return {
                'upper': upper.iloc[-1],
                'middle': sma.iloc[-1],
                'lower': lower.iloc[-1],
                'bandwidth': ((upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1]) * 100
            }
        except:
            return {'upper': 0, 'middle': 0, 'lower': 0, 'bandwidth': 0}
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """RSI Calculation"""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0
    
    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """MACD Calculation"""
        try:
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line.iloc[-1],
                'signal': signal_line.iloc[-1],
                'histogram': histogram.iloc[-1]
            }
        except:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
    
    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """Stochastic Oscillator"""
        try:
            lowest_low = df['low'].rolling(window=k_period).min()
            highest_high = df['high'].rolling(window=k_period).max()
            
            k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'k': k_percent.iloc[-1],
                'd': d_percent.iloc[-1]
            }
        except:
            return {'k': 50, 'd': 50}
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Average True Range"""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            
            return true_range.rolling(window=period).mean().iloc[-1]
        except:
            return 0.0
    
    def _calculate_fibonacci_levels(self, df: pd.DataFrame, period: int = 50) -> Dict[str, float]:
        """Fibonacci Retracement Levels"""
        try:
            recent_data = df.tail(period)
            high_price = recent_data['high'].max()
            low_price = recent_data['low'].min()
            
            diff = high_price - low_price
            
            return {
                'level_0': high_price,
                'level_236': high_price - 0.236 * diff,
                'level_382': high_price - 0.382 * diff,
                'level_50': high_price - 0.5 * diff,
                'level_618': high_price - 0.618 * diff,
                'level_786': high_price - 0.786 * diff,
                'level_100': low_price
            }
        except:
            return {f'level_{i}': 0 for i in ['0', '236', '382', '50', '618', '786', '100']}
    
    def _calculate_pivot_points(self, df: pd.DataFrame) -> Dict[str, float]:
        """Daily Pivot Points"""
        try:
            yesterday = df.tail(1)
            high = yesterday['high'].iloc[0]
            low = yesterday['low'].iloc[0]
            close = yesterday['close'].iloc[0]
            
            pivot = (high + low + close) / 3
            
            return {
                'pivot': pivot,
                'r1': 2 * pivot - low,
                'r2': pivot + (high - low),
                'r3': high + 2 * (pivot - low),
                's1': 2 * pivot - high,
                's2': pivot - (high - low),
                's3': low - 2 * (high - pivot)
            }
        except:
            return {f'{level}': 0 for level in ['pivot', 'r1', 'r2', 'r3', 's1', 's2', 's3']}
    
    def _calculate_support_resistance(self, df: pd.DataFrame, period: int = 20) -> Dict[str, List[float]]:
        """Dynamic Support and Resistance Levels"""
        try:
            recent_data = df.tail(period * 2)
            
            # Find local highs and lows
            highs = recent_data[recent_data['high'] == recent_data['high'].rolling(window=5, center=True).max()]['high'].tolist()
            lows = recent_data[recent_data['low'] == recent_data['low'].rolling(window=5, center=True).min()]['low'].tolist()
            
            # Remove duplicates and sort
            resistance_levels = sorted(list(set(highs)), reverse=True)[:3]
            support_levels = sorted(list(set(lows)))[:3]
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
        except:
            return {'resistance': [], 'support': []}
    
    def _determine_trend(self, df: pd.DataFrame, analysis: Dict) -> str:
        """Determine overall trend direction"""
        try:
            current_price = df['close'].iloc[-1]
            ma10 = analysis['ma10']
            ema50 = analysis['ema50']
            
            bullish_signals = 0
            bearish_signals = 0
            
            # Price vs Moving Averages
            if current_price > ma10:
                bullish_signals += 1
            else:
                bearish_signals += 1
                
            if current_price > ema50:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # MACD
            if analysis['macd']['macd'] > analysis['macd']['signal']:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # RSI
            rsi = analysis['rsi']
            if 40 < rsi < 60:
                pass  # Neutral
            elif rsi > 60:
                bullish_signals += 1
            elif rsi < 40:
                bearish_signals += 1
            
            if bullish_signals > bearish_signals:
                return "BULLISH"
            elif bearish_signals > bullish_signals:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except:
            return "NEUTRAL"
    
    def _calculate_momentum(self, df: pd.DataFrame, analysis: Dict) -> str:
        """Calculate price momentum"""
        try:
            macd_histogram = analysis['macd']['histogram']
            rsi = analysis['rsi']
            stoch_k = analysis['stochastic']['k']
            
            if macd_histogram > 0 and rsi > 55 and stoch_k > 50:
                return "STRONG_BULLISH"
            elif macd_histogram < 0 and rsi < 45 and stoch_k < 50:
                return "STRONG_BEARISH"
            elif macd_histogram > 0 or rsi > 50:
                return "WEAK_BULLISH"
            elif macd_histogram < 0 or rsi < 50:
                return "WEAK_BEARISH"
            else:
                return "NEUTRAL"
        except:
            return "NEUTRAL"
    
    def _calculate_signal_strength(self, analysis: Dict) -> float:
        """Calculate signal strength (0-100)"""
        try:
            strength = 50  # Base strength
            
            # RSI contribution
            rsi = analysis['rsi']
            if rsi > 70:
                strength += 15  # Overbought
            elif rsi < 30:
                strength += 15  # Oversold
            elif 45 < rsi < 55:
                strength -= 10  # Neutral zone
            
            # MACD contribution
            macd = analysis['macd']
            if abs(macd['histogram']) > abs(macd['macd']) * 0.1:
                strength += 10
            
            # Stochastic contribution
            stoch = analysis['stochastic']
            if stoch['k'] > 80 or stoch['k'] < 20:
                strength += 10
            
            return min(max(strength, 0), 100)
        except:
            return 50
    
    def _get_bollinger_position(self, df: pd.DataFrame, bollinger: Dict) -> str:
        """Determine position relative to Bollinger Bands"""
        try:
            current_price = df['close'].iloc[-1]
            upper = bollinger['upper']
            lower = bollinger['lower']
            middle = bollinger['middle']
            
            if current_price > upper:
                return "ABOVE_UPPER"
            elif current_price < lower:
                return "BELOW_LOWER"
            elif current_price > middle:
                return "UPPER_HALF"
            else:
                return "LOWER_HALF"
        except:
            return "MIDDLE"
    
    def _analyze_volume_trend(self, df: pd.DataFrame) -> str:
        """Analyze volume trend"""
        try:
            if 'tick_volume' not in df.columns:
                return "NORMAL"
            
            recent_volume = df['tick_volume'].tail(5).mean()
            previous_volume = df['tick_volume'].tail(20).head(15).mean()
            
            if recent_volume > previous_volume * 1.5:
                return "HIGH"
            elif recent_volume < previous_volume * 0.7:
                return "LOW"
            else:
                return "NORMAL"
        except:
            return "NORMAL"
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when calculation fails"""
        return {
            'trend': 'NEUTRAL',
            'momentum': 'NEUTRAL',
            'signal_strength': 50,
            'rsi': 50,
            'macd': {'macd': 0, 'signal': 0, 'histogram': 0},
            'bollinger_position': 'MIDDLE',
            'volume_trend': 'NORMAL',
            'ma10': 0,
            'ema50': 0,
            'bollinger': {'upper': 0, 'middle': 0, 'lower': 0},
            'stochastic': {'k': 50, 'd': 50},
            'atr': 0,
            'fibonacci': {},
            'pivot_points': {},
            'support_resistance': {'resistance': [], 'support': []}
        }
    
    def get_trading_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on technical analysis"""
        try:
            analysis = self.analyze_trends(df)
            
            signals = {
                'action': 'HOLD',
                'confidence': 0.0,
                'stop_loss_pips': 20,
                'take_profit_pips': 40,
                'reasoning': []
            }
            
            confidence = 0
            reasoning = []
            
            # Fast signals (Price Action, MA10)
            current_price = df['close'].iloc[-1]
            ma10 = analysis['ma10']
            
            if current_price > ma10:
                confidence += 20
                reasoning.append("Price above MA10")
            elif current_price < ma10:
                confidence += 20
                reasoning.append("Price below MA10")
            
            # Slow signals (EMA50, RSI)
            ema50 = analysis['ema50']
            rsi = analysis['rsi']
            
            if current_price > ema50 and rsi < 70:
                confidence += 15
                reasoning.append("Bullish trend confirmed")
                signals['action'] = 'BUY'
            elif current_price < ema50 and rsi > 30:
                confidence += 15
                reasoning.append("Bearish trend confirmed")
                signals['action'] = 'SELL'
            
            # MACD confirmation
            if analysis['macd']['histogram'] > 0:
                confidence += 10
                reasoning.append("MACD bullish")
            elif analysis['macd']['histogram'] < 0:
                confidence += 10
                reasoning.append("MACD bearish")
            
            # Bollinger Bands
            bb_pos = analysis['bollinger_position']
            if bb_pos == 'BELOW_LOWER':
                confidence += 15
                reasoning.append("Oversold on Bollinger")
                if signals['action'] == 'HOLD':
                    signals['action'] = 'BUY'
            elif bb_pos == 'ABOVE_UPPER':
                confidence += 15
                reasoning.append("Overbought on Bollinger")
                if signals['action'] == 'HOLD':
                    signals['action'] = 'SELL'
            
            signals['confidence'] = min(confidence / 100.0, 1.0)
            signals['reasoning'] = reasoning
            
            # Dynamic SL/TP based on ATR
            atr = analysis['atr']
            if atr > 0:
                signals['stop_loss_pips'] = max(15, int(atr * 1.5))
                signals['take_profit_pips'] = max(30, int(atr * 3))
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating trading signals: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'stop_loss_pips': 20,
                'take_profit_pips': 40,
                'reasoning': ['Analysis error']
            }
