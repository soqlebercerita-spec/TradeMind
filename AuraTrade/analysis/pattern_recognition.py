
"""
Advanced Pattern Recognition for AuraTrade Bot
Candlestick patterns, chart patterns, and technical formations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from utils.logger import Logger

class PatternRecognition:
    """Advanced pattern recognition for trading signals"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.patterns_found = []
        
    def analyze_candlestick_patterns(self, rates: pd.DataFrame) -> Dict[str, any]:
        """Analyze candlestick patterns"""
        try:
            if len(rates) < 5:
                return {'patterns': [], 'signals': []}
                
            patterns = []
            signals = []
            
            # Get last few candles
            last_candles = rates.tail(5)
            
            # Doji Pattern
            if self._is_doji(last_candles.iloc[-1]):
                patterns.append({
                    'name': 'Doji',
                    'type': 'reversal',
                    'strength': 'medium',
                    'position': len(rates) - 1
                })
                signals.append('INDECISION')
            
            # Hammer Pattern
            if self._is_hammer(last_candles.iloc[-1]):
                patterns.append({
                    'name': 'Hammer',
                    'type': 'reversal',
                    'strength': 'strong',
                    'position': len(rates) - 1
                })
                signals.append('BULLISH_REVERSAL')
            
            # Shooting Star
            if self._is_shooting_star(last_candles.iloc[-1]):
                patterns.append({
                    'name': 'Shooting Star',
                    'type': 'reversal',
                    'strength': 'strong',
                    'position': len(rates) - 1
                })
                signals.append('BEARISH_REVERSAL')
            
            # Engulfing Patterns
            if len(last_candles) >= 2:
                engulfing = self._check_engulfing(last_candles.iloc[-2], last_candles.iloc[-1])
                if engulfing:
                    patterns.append(engulfing)
                    signals.append(engulfing['signal'])
            
            # Three Candle Patterns
            if len(last_candles) >= 3:
                three_pattern = self._check_three_candle_patterns(last_candles.tail(3))
                if three_pattern:
                    patterns.append(three_pattern)
                    signals.append(three_pattern['signal'])
                    
            return {
                'patterns': patterns,
                'signals': signals,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in candlestick pattern analysis: {e}")
            return {'patterns': [], 'signals': []}
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """Check if candle is a Doji"""
        try:
            body = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return False
                
            body_ratio = body / total_range
            return body_ratio < 0.1  # Body is less than 10% of total range
            
        except:
            return False
    
    def _is_hammer(self, candle: pd.Series) -> bool:
        """Check if candle is a Hammer"""
        try:
            body = abs(candle['close'] - candle['open'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return False
            
            # Hammer conditions
            return (
                lower_shadow > body * 2 and  # Long lower shadow
                upper_shadow < body * 0.5 and  # Short upper shadow
                body / total_range > 0.1  # Reasonable body size
            )
            
        except:
            return False
    
    def _is_shooting_star(self, candle: pd.Series) -> bool:
        """Check if candle is a Shooting Star"""
        try:
            body = abs(candle['close'] - candle['open'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return False
            
            # Shooting Star conditions
            return (
                upper_shadow > body * 2 and  # Long upper shadow
                lower_shadow < body * 0.5 and  # Short lower shadow
                body / total_range > 0.1  # Reasonable body size
            )
            
        except:
            return False
    
    def _check_engulfing(self, prev_candle: pd.Series, curr_candle: pd.Series) -> Optional[Dict]:
        """Check for engulfing patterns"""
        try:
            prev_body = prev_candle['close'] - prev_candle['open']
            curr_body = curr_candle['close'] - curr_candle['open']
            
            # Bullish Engulfing
            if (prev_body < 0 and curr_body > 0 and  # Prev red, curr green
                curr_candle['open'] < prev_candle['close'] and  # Curr opens below prev close
                curr_candle['close'] > prev_candle['open']):  # Curr closes above prev open
                
                return {
                    'name': 'Bullish Engulfing',
                    'type': 'reversal',
                    'strength': 'strong',
                    'signal': 'BULLISH_REVERSAL'
                }
            
            # Bearish Engulfing
            if (prev_body > 0 and curr_body < 0 and  # Prev green, curr red
                curr_candle['open'] > prev_candle['close'] and  # Curr opens above prev close
                curr_candle['close'] < prev_candle['open']):  # Curr closes below prev open
                
                return {
                    'name': 'Bearish Engulfing',
                    'type': 'reversal',
                    'strength': 'strong',
                    'signal': 'BEARISH_REVERSAL'
                }
                
            return None
            
        except:
            return None
    
    def _check_three_candle_patterns(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Check for three-candle patterns"""
        try:
            if len(candles) < 3:
                return None
                
            c1, c2, c3 = candles.iloc[0], candles.iloc[1], candles.iloc[2]
            
            # Morning Star
            if (c1['close'] < c1['open'] and  # First candle is bearish
                abs(c2['close'] - c2['open']) < abs(c1['close'] - c1['open']) * 0.3 and  # Second is small
                c3['close'] > c3['open'] and  # Third is bullish
                c3['close'] > (c1['open'] + c1['close']) / 2):  # Third closes above first's midpoint
                
                return {
                    'name': 'Morning Star',
                    'type': 'reversal',
                    'strength': 'very_strong',
                    'signal': 'BULLISH_REVERSAL'
                }
            
            # Evening Star
            if (c1['close'] > c1['open'] and  # First candle is bullish
                abs(c2['close'] - c2['open']) < abs(c1['close'] - c1['open']) * 0.3 and  # Second is small
                c3['close'] < c3['open'] and  # Third is bearish
                c3['close'] < (c1['open'] + c1['close']) / 2):  # Third closes below first's midpoint
                
                return {
                    'name': 'Evening Star',
                    'type': 'reversal',
                    'strength': 'very_strong',
                    'signal': 'BEARISH_REVERSAL'
                }
                
            return None
            
        except:
            return None
    
    def detect_chart_patterns(self, rates: pd.DataFrame, lookback: int = 50) -> Dict[str, any]:
        """Detect chart patterns like triangles, head & shoulders, etc."""
        try:
            if len(rates) < lookback:
                return {'patterns': [], 'signals': []}
                
            patterns = []
            recent_data = rates.tail(lookback)
            
            # Support and Resistance levels
            support_resistance = self._find_support_resistance(recent_data)
            
            # Triangle patterns
            triangle = self._detect_triangle(recent_data)
            if triangle:
                patterns.append(triangle)
            
            # Double Top/Bottom
            double_pattern = self._detect_double_top_bottom(recent_data)
            if double_pattern:
                patterns.append(double_pattern)
                
            return {
                'patterns': patterns,
                'support_resistance': support_resistance,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in chart pattern detection: {e}")
            return {'patterns': [], 'signals': []}
    
    def _find_support_resistance(self, rates: pd.DataFrame) -> Dict[str, List[float]]:
        """Find support and resistance levels"""
        try:
            highs = rates['high'].values
            lows = rates['low'].values
            
            # Find local peaks and troughs
            resistance_levels = []
            support_levels = []
            
            # Simple peak/trough detection
            for i in range(2, len(highs) - 2):
                # Resistance (local high)
                if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                    highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                    resistance_levels.append(highs[i])
                
                # Support (local low)
                if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                    lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                    support_levels.append(lows[i])
            
            # Remove duplicates and sort
            resistance_levels = sorted(list(set(resistance_levels)))[-5:]  # Keep last 5
            support_levels = sorted(list(set(support_levels)))[-5:]  # Keep last 5
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
            
        except Exception as e:
            self.logger.error(f"Error finding support/resistance: {e}")
            return {'resistance': [], 'support': []}
    
    def _detect_triangle(self, rates: pd.DataFrame) -> Optional[Dict]:
        """Detect triangle patterns"""
        try:
            if len(rates) < 20:
                return None
                
            highs = rates['high'].values
            lows = rates['low'].values
            
            # Simple triangle detection logic
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            # Ascending triangle: horizontal resistance, rising support
            max_high = max(recent_highs)
            if (abs(max(recent_highs[-3:]) - max_high) / max_high < 0.001 and  # Flat resistance
                min(recent_lows[-3:]) > min(recent_lows[:3])):  # Rising support
                
                return {
                    'name': 'Ascending Triangle',
                    'type': 'continuation',
                    'strength': 'medium',
                    'signal': 'BULLISH_BREAKOUT_EXPECTED'
                }
            
            # Descending triangle: horizontal support, falling resistance
            min_low = min(recent_lows)
            if (abs(min(recent_lows[-3:]) - min_low) / min_low < 0.001 and  # Flat support
                max(recent_highs[-3:]) < max(recent_highs[:3])):  # Falling resistance
                
                return {
                    'name': 'Descending Triangle',
                    'type': 'continuation',
                    'strength': 'medium',
                    'signal': 'BEARISH_BREAKOUT_EXPECTED'
                }
                
            return None
            
        except:
            return None
    
    def _detect_double_top_bottom(self, rates: pd.DataFrame) -> Optional[Dict]:
        """Detect double top/bottom patterns"""
        try:
            if len(rates) < 30:
                return None
                
            highs = rates['high'].values
            lows = rates['low'].values
            
            # Find the two highest highs in recent data
            high_indices = np.argsort(highs[-20:])[-2:]
            high_values = [highs[-20:][i] for i in high_indices]
            
            # Check if they're similar (within 0.1%)
            if len(high_values) == 2 and abs(high_values[0] - high_values[1]) / max(high_values) < 0.001:
                return {
                    'name': 'Double Top',
                    'type': 'reversal',
                    'strength': 'strong',
                    'signal': 'BEARISH_REVERSAL'
                }
            
            # Find the two lowest lows
            low_indices = np.argsort(lows[-20:])[:2]
            low_values = [lows[-20:][i] for i in low_indices]
            
            # Check if they're similar (within 0.1%)
            if len(low_values) == 2 and abs(low_values[0] - low_values[1]) / min(low_values) < 0.001:
                return {
                    'name': 'Double Bottom',
                    'type': 'reversal',
                    'strength': 'strong',
                    'signal': 'BULLISH_REVERSAL'
                }
                
            return None
            
        except:
            return None
    
    def get_pattern_summary(self) -> Dict[str, any]:
        """Get summary of all detected patterns"""
        return {
            'total_patterns': len(self.patterns_found),
            'recent_patterns': self.patterns_found[-10:] if self.patterns_found else [],
            'pattern_types': list(set([p.get('type') for p in self.patterns_found])),
            'last_update': datetime.now()
        }
