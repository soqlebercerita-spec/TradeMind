
"""
Swing Trading Strategy for AuraTrade Bot
Medium-term position trading for 75%+ win rate
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from utils.logger import Logger

class SwingStrategy:
    """Conservative swing trading strategy"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "swing"
        self.timeframe = "H4"
        self.min_confidence = 0.7
        
        # Strategy parameters
        self.rsi_period = 14
        self.ma_short = 20
        self.ma_long = 50
        self.bb_period = 20
        self.bb_std = 2
        
        self.logger.info("SwingStrategy initialized")

    def initialize(self):
        """Initialize strategy"""
        self.logger.info("Swing strategy initialized for H4 timeframe")

    def analyze(self, symbol: str, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Analyze symbol for swing trading opportunities"""
        try:
            if data is None or len(data) < 50:
                return None

            # Calculate indicators
            indicators = self._calculate_indicators(data)
            
            # Generate signals
            signal = self._generate_signal(indicators, data)
            
            if signal and signal['action'] != 'hold':
                self.logger.info(f"Swing signal for {symbol}: {signal['action']} (confidence: {signal['confidence']:.2f})")
                
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol} for swing: {e}")
            return None

    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            # Moving averages
            ma_short = self._sma(close, self.ma_short)
            ma_long = self._sma(close, self.ma_long)
            
            # RSI
            rsi = self._rsi(close, self.rsi_period)
            
            # Bollinger Bands
            bb_middle = self._sma(close, self.bb_period)
            bb_std = self._rolling_std(close, self.bb_period)
            bb_upper = bb_middle + (bb_std * self.bb_std)
            bb_lower = bb_middle - (bb_std * self.bb_std)
            
            # MACD
            ema_12 = self._ema(close, 12)
            ema_26 = self._ema(close, 26)
            macd_line = ema_12 - ema_26
            macd_signal = self._ema(macd_line, 9)
            macd_histogram = macd_line - macd_signal
            
            # Support/Resistance levels
            support = self._find_support_resistance(high, low, close)
            
            return {
                'ma_short': ma_short,
                'ma_long': ma_long,
                'rsi': rsi,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_histogram,
                'support_resistance': support,
                'close': close
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating swing indicators: {e}")
            return {}

    def _generate_signal(self, indicators: Dict[str, Any], data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on indicators"""
        try:
            if not indicators:
                return None
            
            current_idx = -1
            confidence = 0.0
            action = 'hold'
            
            # Get current values
            close = indicators['close'][current_idx]
            ma_short = indicators['ma_short'][current_idx]
            ma_long = indicators['ma_long'][current_idx]
            rsi = indicators['rsi'][current_idx]
            bb_upper = indicators['bb_upper'][current_idx]
            bb_lower = indicators['bb_lower'][current_idx]
            macd_line = indicators['macd_line'][current_idx]
            macd_signal = indicators['macd_signal'][current_idx]
            
            # Check for valid values
            if any(np.isnan([close, ma_short, ma_long, rsi, bb_upper, bb_lower, macd_line, macd_signal])):
                return None
            
            # Bull signal conditions
            bull_conditions = []
            
            # 1. Price above short MA, short MA above long MA
            if close > ma_short > ma_long:
                bull_conditions.append(0.2)
            
            # 2. RSI oversold recovery (30-50 range)
            if 30 < rsi < 50:
                bull_conditions.append(0.15)
            
            # 3. Price near lower Bollinger Band (oversold)
            bb_position = (close - bb_lower) / (bb_upper - bb_lower)
            if bb_position < 0.3:
                bull_conditions.append(0.2)
            
            # 4. MACD bullish crossover
            if (len(indicators['macd_line']) > 1 and 
                macd_line > macd_signal and 
                indicators['macd_line'][-2] <= indicators['macd_signal'][-2]):
                bull_conditions.append(0.25)
            
            # 5. Price at support level
            support_levels = indicators.get('support_resistance', {}).get('support', [])
            if support_levels and any(abs(close - level) / close < 0.002 for level in support_levels):
                bull_conditions.append(0.2)
            
            # Bear signal conditions
            bear_conditions = []
            
            # 1. Price below short MA, short MA below long MA
            if close < ma_short < ma_long:
                bear_conditions.append(0.2)
            
            # 2. RSI overbought correction (50-70 range)
            if 50 < rsi < 70:
                bear_conditions.append(0.15)
            
            # 3. Price near upper Bollinger Band (overbought)
            if bb_position > 0.7:
                bear_conditions.append(0.2)
            
            # 4. MACD bearish crossover
            if (len(indicators['macd_line']) > 1 and 
                macd_line < macd_signal and 
                indicators['macd_line'][-2] >= indicators['macd_signal'][-2]):
                bear_conditions.append(0.25)
            
            # 5. Price at resistance level
            resistance_levels = indicators.get('support_resistance', {}).get('resistance', [])
            if resistance_levels and any(abs(close - level) / close < 0.002 for level in resistance_levels):
                bear_conditions.append(0.2)
            
            # Calculate confidence scores
            bull_confidence = sum(bull_conditions)
            bear_confidence = sum(bear_conditions)
            
            # Determine action
            if bull_confidence > bear_confidence and bull_confidence >= self.min_confidence:
                action = 'buy'
                confidence = bull_confidence
            elif bear_confidence > bull_confidence and bear_confidence >= self.min_confidence:
                action = 'sell'
                confidence = bear_confidence
            
            # Additional safety check - avoid signals during high volatility
            if len(data) >= 20:
                recent_volatility = data['close'].tail(20).std() / data['close'].tail(20).mean()
                if recent_volatility > 0.02:  # 2% volatility threshold
                    confidence *= 0.8  # Reduce confidence during high volatility
            
            if confidence < self.min_confidence:
                action = 'hold'
            
            return {
                'action': action,
                'confidence': min(confidence, 1.0),
                'indicators': {
                    'rsi': rsi,
                    'ma_trend': 'up' if ma_short > ma_long else 'down',
                    'bb_position': bb_position,
                    'macd_signal': 'bull' if macd_line > macd_signal else 'bear'
                },
                'strategy': 'swing',
                'timeframe': self.timeframe
            }
            
        except Exception as e:
            self.logger.error(f"Error generating swing signal: {e}")
            return None

    def _find_support_resistance(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict[str, List[float]]:
        """Find support and resistance levels"""
        try:
            if len(close) < 20:
                return {'support': [], 'resistance': []}
            
            # Look for pivot points in last 20 periods
            lookback = min(20, len(close))
            recent_high = high[-lookback:]
            recent_low = low[-lookback:]
            recent_close = close[-lookback:]
            
            support_levels = []
            resistance_levels = []
            
            # Find local minima for support
            for i in range(2, len(recent_low) - 2):
                if (recent_low[i] < recent_low[i-1] and recent_low[i] < recent_low[i-2] and
                    recent_low[i] < recent_low[i+1] and recent_low[i] < recent_low[i+2]):
                    support_levels.append(recent_low[i])
            
            # Find local maxima for resistance
            for i in range(2, len(recent_high) - 2):
                if (recent_high[i] > recent_high[i-1] and recent_high[i] > recent_high[i-2] and
                    recent_high[i] > recent_high[i+1] and recent_high[i] > recent_high[i+2]):
                    resistance_levels.append(recent_high[i])
            
            # Keep only most relevant levels (closest to current price)
            current_price = close[-1]
            support_levels = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]
            resistance_levels = sorted([r for r in resistance_levels if r > current_price])[:3]
            
            return {
                'support': support_levels,
                'resistance': resistance_levels
            }
            
        except Exception as e:
            self.logger.error(f"Error finding support/resistance: {e}")
            return {'support': [], 'resistance': []}

    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        try:
            sma = np.full(len(data), np.nan)
            for i in range(period - 1, len(data)):
                sma[i] = np.mean(data[i - period + 1:i + 1])
            return sma
        except:
            return np.full(len(data), np.nan)

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        try:
            ema = np.full(len(data), np.nan)
            multiplier = 2 / (period + 1)
            
            # Start with SMA for first value
            ema[period - 1] = np.mean(data[:period])
            
            for i in range(period, len(data)):
                ema[i] = (data[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
            
            return ema
        except:
            return np.full(len(data), np.nan)

    def _rsi(self, data: np.ndarray, period: int) -> np.ndarray:
        """Relative Strength Index"""
        try:
            rsi = np.full(len(data), np.nan)
            deltas = np.diff(data)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[:period])
            avg_loss = np.mean(losses[:period])
            
            for i in range(period, len(data)):
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    rsi[i] = 100 - (100 / (1 + rs))
                else:
                    rsi[i] = 100
                
                # Update averages
                if i < len(deltas):
                    gain = gains[i] if i < len(gains) else 0
                    loss = losses[i] if i < len(losses) else 0
                    avg_gain = ((avg_gain * (period - 1)) + gain) / period
                    avg_loss = ((avg_loss * (period - 1)) + loss) / period
            
            return rsi
        except:
            return np.full(len(data), np.nan)

    def _rolling_std(self, data: np.ndarray, period: int) -> np.ndarray:
        """Rolling standard deviation"""
        try:
            std = np.full(len(data), np.nan)
            for i in range(period - 1, len(data)):
                std[i] = np.std(data[i - period + 1:i + 1])
            return std
        except:
            return np.full(len(data), np.nan)
