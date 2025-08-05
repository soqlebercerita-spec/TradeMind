"""
Pattern recognition strategy for AuraTrade Bot
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import Logger

class PatternStrategy:
    """Pattern recognition strategy"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.enabled = True
        self.name = "Pattern"

        # Strategy parameters
        self.min_confidence = 65.0
        self.pattern_target = 15.0  # pips
        self.stop_loss = 10.0  # pips

    def analyze_signal(self, symbol: str, data: pd.DataFrame, current_price: tuple, 
                      market_condition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze pattern signals"""
        try:
            if len(data) < 50:
                return None

            # Check for various patterns
            patterns = self._detect_patterns(data)

            if not patterns:
                return None

            # Select strongest pattern
            best_pattern = max(patterns, key=lambda x: x['confidence'])

            if best_pattern['confidence'] >= self.min_confidence:
                bid, ask = current_price
                current = (bid + ask) / 2

                return {
                    'signal': best_pattern['signal'],
                    'confidence': best_pattern['confidence'],
                    'entry_price': current,
                    'stop_loss_pips': self.stop_loss,
                    'take_profit_pips': self.pattern_target,
                    'risk_percent': 1.0,
                    'strategy': f"{self.name}-{best_pattern['pattern']}",
                    'timeframe': 'M15'
                }

            return None

        except Exception as e:
            self.logger.error(f"Error in pattern strategy analysis: {e}")
            return None

    def _detect_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect various chart patterns"""
        patterns = []

        try:
            # Engulfing patterns
            engulfing = self._detect_engulfing(data)
            if engulfing:
                patterns.append(engulfing)

            # Hammer/Doji patterns
            hammer = self._detect_hammer(data)
            if hammer:
                patterns.append(hammer)

            # Double top/bottom
            double_pattern = self._detect_double_topbottom(data)
            if double_pattern:
                patterns.append(double_pattern)

            # Support/Resistance break
            break_pattern = self._detect_breakout(data)
            if break_pattern:
                patterns.append(break_pattern)

        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")

        return patterns

    def _detect_engulfing(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect bullish/bearish engulfing patterns"""
        try:
            if len(data) < 3:
                return None

            # Get last two candles
            prev = data.iloc[-2]
            current = data.iloc[-1]

            # Bullish engulfing
            if (prev['close'] < prev['open'] and  # Previous red candle
                current['close'] > current['open'] and  # Current green candle
                current['open'] < prev['close'] and  # Opens below previous close
                current['close'] > prev['open']):  # Closes above previous open

                return {
                    'pattern': 'Bullish Engulfing',
                    'signal': 'buy',
                    'confidence': 75.0
                }

            # Bearish engulfing
            elif (prev['close'] > prev['open'] and  # Previous green candle
                  current['close'] < current['open'] and  # Current red candle
                  current['open'] > prev['close'] and  # Opens above previous close
                  current['close'] < prev['open']):  # Closes below previous open

                return {
                    'pattern': 'Bearish Engulfing',
                    'signal': 'sell',
                    'confidence': 75.0
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting engulfing pattern: {e}")
            return None

    def _detect_hammer(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect hammer/doji patterns"""
        try:
            if len(data) < 2:
                return None

            current = data.iloc[-1]

            # Calculate candle properties
            body = abs(current['close'] - current['open'])
            upper_shadow = current['high'] - max(current['open'], current['close'])
            lower_shadow = min(current['open'], current['close']) - current['low']
            total_range = current['high'] - current['low']

            if total_range == 0:
                return None

            # Hammer pattern (bullish)
            if (lower_shadow >= 2 * body and
                upper_shadow <= 0.1 * total_range and
                body <= 0.3 * total_range):

                return {
                    'pattern': 'Hammer',
                    'signal': 'buy',
                    'confidence': 70.0
                }

            # Shooting star (bearish)
            elif (upper_shadow >= 2 * body and
                  lower_shadow <= 0.1 * total_range and
                  body <= 0.3 * total_range):

                return {
                    'pattern': 'Shooting Star',
                    'signal': 'sell',
                    'confidence': 70.0
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting hammer pattern: {e}")
            return None

    def _detect_double_topbottom(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect double top/bottom patterns"""
        try:
            if len(data) < 20:
                return None

            recent_data = data.tail(20)
            highs = recent_data['high']
            lows = recent_data['low']

            # Find peaks and troughs
            peaks = []
            troughs = []

            for i in range(2, len(recent_data) - 2):
                # Peak detection
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and
                    highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
                    peaks.append(highs.iloc[i])

                # Trough detection
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2] and
                    lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]):
                    troughs.append(lows.iloc[i])

            # Double top
            if len(peaks) >= 2:
                last_two_peaks = peaks[-2:]
                if abs(last_two_peaks[0] - last_two_peaks[1]) / last_two_peaks[0] < 0.002:  # Within 0.2%
                    return {
                        'pattern': 'Double Top',
                        'signal': 'sell',
                        'confidence': 68.0
                    }

            # Double bottom
            if len(troughs) >= 2:
                last_two_troughs = troughs[-2:]
                if abs(last_two_troughs[0] - last_two_troughs[1]) / last_two_troughs[0] < 0.002:  # Within 0.2%
                    return {
                        'pattern': 'Double Bottom',
                        'signal': 'buy',
                        'confidence': 68.0
                    }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting double top/bottom: {e}")
            return None

    def _detect_breakout(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect support/resistance breakouts"""
        try:
            if len(data) < 30:
                return None

            recent_data = data.tail(20)
            current_price = data['close'].iloc[-1]

            # Calculate support and resistance
            resistance = recent_data['high'].rolling(10).max().iloc[-1]
            support = recent_data['low'].rolling(10).min().iloc[-1]

            # Breakout above resistance
            if current_price > resistance * 1.001:  # 0.1% above resistance
                return {
                    'pattern': 'Resistance Breakout',
                    'signal': 'buy',
                    'confidence': 72.0
                }

            # Breakdown below support
            elif current_price < support * 0.999:  # 0.1% below support
                return {
                    'pattern': 'Support Breakdown',
                    'signal': 'sell',
                    'confidence': 72.0
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting breakout: {e}")
            return None