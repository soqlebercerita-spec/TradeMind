"""
Advanced pattern recognition for AuraTrade Bot
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from utils.logger import Logger

class PatternRecognition:
    """Advanced chart pattern recognition"""

    def __init__(self):
        self.logger = Logger().get_logger()

    def detect_all_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect all available patterns"""
        patterns = []

        try:
            # Candlestick patterns
            patterns.extend(self.detect_candlestick_patterns(data))

            # Chart patterns
            patterns.extend(self.detect_chart_patterns(data))

            return patterns

        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
            return []

    def detect_candlestick_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect candlestick patterns"""
        patterns = []

        if len(data) < 3:
            return patterns

        try:
            # Doji pattern
            doji = self.detect_doji(data)
            if doji:
                patterns.append(doji)

            # Hammer/Hanging man
            hammer = self.detect_hammer(data)
            if hammer:
                patterns.append(hammer)

            # Engulfing patterns
            engulfing = self.detect_engulfing(data)
            if engulfing:
                patterns.append(engulfing)

        except Exception as e:
            self.logger.error(f"Error detecting candlestick patterns: {e}")

        return patterns

    def detect_chart_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect chart patterns"""
        patterns = []

        if len(data) < 20:
            return patterns

        try:
            # Head and shoulders
            h_and_s = self.detect_head_and_shoulders(data)
            if h_and_s:
                patterns.append(h_and_s)

            # Triangle patterns
            triangle = self.detect_triangle(data)
            if triangle:
                patterns.append(triangle)

        except Exception as e:
            self.logger.error(f"Error detecting chart patterns: {e}")

        return patterns

    def detect_doji(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Doji pattern"""
        try:
            current = data.iloc[-1]

            body = abs(current['close'] - current['open'])
            total_range = current['high'] - current['low']

            if total_range == 0:
                return None

            # Doji if body is less than 10% of total range
            if body / total_range < 0.1:
                return {
                    'pattern': 'Doji',
                    'type': 'reversal',
                    'confidence': 60.0,
                    'description': 'Indecision pattern'
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting Doji: {e}")
            return None

    def detect_hammer(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Hammer/Hanging Man pattern"""
        try:
            current = data.iloc[-1]

            body = abs(current['close'] - current['open'])
            upper_shadow = current['high'] - max(current['open'], current['close'])
            lower_shadow = min(current['open'], current['close']) - current['low']

            # Hammer: long lower shadow, small body, small upper shadow
            if (lower_shadow >= 2 * body and 
                upper_shadow <= 0.1 * (current['high'] - current['low'])):

                return {
                    'pattern': 'Hammer',
                    'type': 'reversal',
                    'confidence': 70.0,
                    'signal': 'bullish',
                    'description': 'Potential bullish reversal'
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting Hammer: {e}")
            return None

    def detect_engulfing(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Engulfing patterns"""
        try:
            if len(data) < 2:
                return None

            prev = data.iloc[-2]
            current = data.iloc[-1]

            # Bullish engulfing
            if (prev['close'] < prev['open'] and  # Previous bearish
                current['close'] > current['open'] and  # Current bullish
                current['open'] < prev['close'] and  # Opens below prev close
                current['close'] > prev['open']):  # Closes above prev open

                return {
                    'pattern': 'Bullish Engulfing',
                    'type': 'reversal',
                    'confidence': 80.0,
                    'signal': 'bullish',
                    'description': 'Strong bullish reversal signal'
                }

            # Bearish engulfing
            elif (prev['close'] > prev['open'] and  # Previous bullish
                  current['close'] < current['open'] and  # Current bearish
                  current['open'] > prev['close'] and  # Opens above prev close
                  current['close'] < prev['open']):  # Closes below prev open

                return {
                    'pattern': 'Bearish Engulfing',
                    'type': 'reversal',
                    'confidence': 80.0,
                    'signal': 'bearish',
                    'description': 'Strong bearish reversal signal'
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting Engulfing: {e}")
            return None

    def detect_head_and_shoulders(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Head and Shoulders pattern"""
        try:
            if len(data) < 30:
                return None

            # Find peaks in the data
            highs = data['high'].rolling(5, center=True).max()
            peaks = data[data['high'] == highs]['high'].tolist()

            if len(peaks) < 3:
                return None

            # Check for head and shoulders formation
            recent_peaks = peaks[-3:]

            # Head should be higher than both shoulders
            if (recent_peaks[1] > recent_peaks[0] and 
                recent_peaks[1] > recent_peaks[2] and
                abs(recent_peaks[0] - recent_peaks[2]) / recent_peaks[1] < 0.05):

                return {
                    'pattern': 'Head and Shoulders',
                    'type': 'reversal',
                    'confidence': 75.0,
                    'signal': 'bearish',
                    'description': 'Major bearish reversal pattern'
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting Head and Shoulders: {e}")
            return None

    def detect_triangle(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Triangle patterns"""
        try:
            if len(data) < 20:
                return None

            recent_data = data.tail(20)

            # Calculate trend lines
            highs = recent_data['high']
            lows = recent_data['low']

            # Simple triangle detection (ascending/descending)
            high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
            low_trend = np.polyfit(range(len(lows)), lows, 1)[0]

            # Ascending triangle
            if abs(high_trend) < 0.0001 and low_trend > 0:
                return {
                    'pattern': 'Ascending Triangle',
                    'type': 'continuation',
                    'confidence': 65.0,
                    'signal': 'bullish',
                    'description': 'Bullish continuation pattern'
                }

            # Descending triangle
            elif abs(low_trend) < 0.0001 and high_trend < 0:
                return {
                    'pattern': 'Descending Triangle',
                    'type': 'continuation',
                    'confidence': 65.0,
                    'signal': 'bearish',
                    'description': 'Bearish continuation pattern'
                }

            return None

        except Exception as e:
            self.logger.error(f"Error detecting Triangle: {e}")
            return None