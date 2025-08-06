
"""
Advanced Pattern Recognition for AuraTrade Bot
Candlestick patterns, chart patterns, and technical formations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from utils.logger import Logger

class CandlestickPatternRecognition:
    """Candlestick pattern recognition engine"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
    
    def detect_all_patterns(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect all candlestick patterns"""
        patterns = []
        
        if len(rates) < 5:
            return patterns
        
        try:
            # Single candlestick patterns
            patterns.extend(self.detect_doji(rates))
            patterns.extend(self.detect_hammer(rates))
            patterns.extend(self.detect_shooting_star(rates))
            patterns.extend(self.detect_marubozu(rates))
            
            # Two-candlestick patterns
            patterns.extend(self.detect_engulfing(rates))
            patterns.extend(self.detect_harami(rates))
            patterns.extend(self.detect_piercing_line(rates))
            patterns.extend(self.detect_dark_cloud_cover(rates))
            
            # Three-candlestick patterns
            patterns.extend(self.detect_morning_evening_star(rates))
            patterns.extend(self.detect_three_white_soldiers(rates))
            patterns.extend(self.detect_three_black_crows(rates))
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
            return patterns
    
    def detect_doji(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Doji patterns"""
        patterns = []
        
        try:
            for i in range(len(rates)):
                candle = rates.iloc[i]
                body = abs(candle['close'] - candle['open'])
                range_size = candle['high'] - candle['low']
                
                if range_size > 0 and body / range_size < 0.1:  # Body is less than 10% of range
                    patterns.append({
                        'type': 'Doji',
                        'signal': 'REVERSAL',
                        'confidence': 0.6,
                        'index': i,
                        'description': 'Doji candle - indecision, potential reversal',
                        'bullish': None  # Context-dependent
                    })
        except Exception as e:
            self.logger.error(f"Error detecting Doji: {e}")
        
        return patterns
    
    def detect_hammer(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Hammer and Hanging Man patterns"""
        patterns = []
        
        try:
            for i in range(len(rates)):
                candle = rates.iloc[i]
                body = abs(candle['close'] - candle['open'])
                upper_shadow = candle['high'] - max(candle['open'], candle['close'])
                lower_shadow = min(candle['open'], candle['close']) - candle['low']
                range_size = candle['high'] - candle['low']
                
                if (range_size > 0 and lower_shadow > 2 * body and 
                    upper_shadow < body and body > 0):
                    
                    # Determine if hammer or hanging man based on trend context
                    if i >= 5:
                        prev_trend = self._determine_trend(rates.iloc[i-5:i])
                        if prev_trend == 'downtrend':
                            patterns.append({
                                'type': 'Hammer',
                                'signal': 'BULLISH',
                                'confidence': 0.7,
                                'index': i,
                                'description': 'Hammer pattern - potential bullish reversal',
                                'bullish': True
                            })
                        elif prev_trend == 'uptrend':
                            patterns.append({
                                'type': 'Hanging Man',
                                'signal': 'BEARISH',
                                'confidence': 0.65,
                                'index': i,
                                'description': 'Hanging Man pattern - potential bearish reversal',
                                'bullish': False
                            })
        except Exception as e:
            self.logger.error(f"Error detecting Hammer: {e}")
        
        return patterns
    
    def detect_shooting_star(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Shooting Star and Inverted Hammer patterns"""
        patterns = []
        
        try:
            for i in range(len(rates)):
                candle = rates.iloc[i]
                body = abs(candle['close'] - candle['open'])
                upper_shadow = candle['high'] - max(candle['open'], candle['close'])
                lower_shadow = min(candle['open'], candle['close']) - candle['low']
                range_size = candle['high'] - candle['low']
                
                if (range_size > 0 and upper_shadow > 2 * body and 
                    lower_shadow < body and body > 0):
                    
                    if i >= 5:
                        prev_trend = self._determine_trend(rates.iloc[i-5:i])
                        if prev_trend == 'uptrend':
                            patterns.append({
                                'type': 'Shooting Star',
                                'signal': 'BEARISH',
                                'confidence': 0.7,
                                'index': i,
                                'description': 'Shooting Star pattern - potential bearish reversal',
                                'bullish': False
                            })
                        elif prev_trend == 'downtrend':
                            patterns.append({
                                'type': 'Inverted Hammer',
                                'signal': 'BULLISH',
                                'confidence': 0.65,
                                'index': i,
                                'description': 'Inverted Hammer pattern - potential bullish reversal',
                                'bullish': True
                            })
        except Exception as e:
            self.logger.error(f"Error detecting Shooting Star: {e}")
        
        return patterns
    
    def detect_marubozu(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Marubozu patterns"""
        patterns = []
        
        try:
            for i in range(len(rates)):
                candle = rates.iloc[i]
                body = abs(candle['close'] - candle['open'])
                upper_shadow = candle['high'] - max(candle['open'], candle['close'])
                lower_shadow = min(candle['open'], candle['close']) - candle['low']
                range_size = candle['high'] - candle['low']
                
                if (range_size > 0 and body / range_size > 0.95 and 
                    upper_shadow < body * 0.05 and lower_shadow < body * 0.05):
                    
                    if candle['close'] > candle['open']:
                        patterns.append({
                            'type': 'White Marubozu',
                            'signal': 'BULLISH',
                            'confidence': 0.8,
                            'index': i,
                            'description': 'White Marubozu - strong bullish sentiment',
                            'bullish': True
                        })
                    else:
                        patterns.append({
                            'type': 'Black Marubozu',
                            'signal': 'BEARISH',
                            'confidence': 0.8,
                            'index': i,
                            'description': 'Black Marubozu - strong bearish sentiment',
                            'bullish': False
                        })
        except Exception as e:
            self.logger.error(f"Error detecting Marubozu: {e}")
        
        return patterns
    
    def detect_engulfing(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Bullish and Bearish Engulfing patterns"""
        patterns = []
        
        try:
            for i in range(1, len(rates)):
                current = rates.iloc[i]
                previous = rates.iloc[i-1]
                
                curr_body = abs(current['close'] - current['open'])
                prev_body = abs(previous['close'] - previous['open'])
                
                # Bullish Engulfing
                if (previous['close'] < previous['open'] and  # Previous red candle
                    current['close'] > current['open'] and   # Current green candle
                    current['open'] < previous['close'] and  # Current opens below prev close
                    current['close'] > previous['open'] and  # Current closes above prev open
                    curr_body > prev_body):                  # Current body larger
                    
                    patterns.append({
                        'type': 'Bullish Engulfing',
                        'signal': 'BULLISH',
                        'confidence': 0.75,
                        'index': i,
                        'description': 'Bullish Engulfing pattern - strong bullish reversal signal',
                        'bullish': True
                    })
                
                # Bearish Engulfing
                elif (previous['close'] > previous['open'] and  # Previous green candle
                      current['close'] < current['open'] and   # Current red candle
                      current['open'] > previous['close'] and  # Current opens above prev close
                      current['close'] < previous['open'] and  # Current closes below prev open
                      curr_body > prev_body):                  # Current body larger
                    
                    patterns.append({
                        'type': 'Bearish Engulfing',
                        'signal': 'BEARISH',
                        'confidence': 0.75,
                        'index': i,
                        'description': 'Bearish Engulfing pattern - strong bearish reversal signal',
                        'bullish': False
                    })
        except Exception as e:
            self.logger.error(f"Error detecting Engulfing: {e}")
        
        return patterns
    
    def detect_harami(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Harami patterns"""
        patterns = []
        
        try:
            for i in range(1, len(rates)):
                current = rates.iloc[i]
                previous = rates.iloc[i-1]
                
                curr_high = max(current['open'], current['close'])
                curr_low = min(current['open'], current['close'])
                prev_high = max(previous['open'], previous['close'])
                prev_low = min(previous['open'], previous['close'])
                
                # Current candle is inside previous candle's body
                if (curr_high < prev_high and curr_low > prev_low):
                    
                    if previous['close'] < previous['open']:  # Previous red, current any
                        patterns.append({
                            'type': 'Bullish Harami',
                            'signal': 'BULLISH',
                            'confidence': 0.65,
                            'index': i,
                            'description': 'Bullish Harami pattern - potential bullish reversal',
                            'bullish': True
                        })
                    elif previous['close'] > previous['open']:  # Previous green, current any
                        patterns.append({
                            'type': 'Bearish Harami',
                            'signal': 'BEARISH',
                            'confidence': 0.65,
                            'index': i,
                            'description': 'Bearish Harami pattern - potential bearish reversal',
                            'bullish': False
                        })
        except Exception as e:
            self.logger.error(f"Error detecting Harami: {e}")
        
        return patterns
    
    def detect_piercing_line(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Piercing Line pattern"""
        patterns = []
        
        try:
            for i in range(1, len(rates)):
                current = rates.iloc[i]
                previous = rates.iloc[i-1]
                
                prev_body = abs(previous['close'] - previous['open'])
                
                if (previous['close'] < previous['open'] and    # Previous red candle
                    current['close'] > current['open'] and     # Current green candle
                    current['open'] < previous['low'] and      # Gap down
                    current['close'] > (previous['open'] + previous['close']) / 2 and  # Closes above midpoint
                    current['close'] < previous['open']):      # But below previous open
                    
                    patterns.append({
                        'type': 'Piercing Line',
                        'signal': 'BULLISH',
                        'confidence': 0.7,
                        'index': i,
                        'description': 'Piercing Line pattern - bullish reversal signal',
                        'bullish': True
                    })
        except Exception as e:
            self.logger.error(f"Error detecting Piercing Line: {e}")
        
        return patterns
    
    def detect_dark_cloud_cover(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Dark Cloud Cover pattern"""
        patterns = []
        
        try:
            for i in range(1, len(rates)):
                current = rates.iloc[i]
                previous = rates.iloc[i-1]
                
                if (previous['close'] > previous['open'] and    # Previous green candle
                    current['close'] < current['open'] and     # Current red candle
                    current['open'] > previous['high'] and     # Gap up
                    current['close'] < (previous['open'] + previous['close']) / 2 and  # Closes below midpoint
                    current['close'] > previous['open']):      # But above previous open
                    
                    patterns.append({
                        'type': 'Dark Cloud Cover',
                        'signal': 'BEARISH',
                        'confidence': 0.7,
                        'index': i,
                        'description': 'Dark Cloud Cover pattern - bearish reversal signal',
                        'bullish': False
                    })
        except Exception as e:
            self.logger.error(f"Error detecting Dark Cloud Cover: {e}")
        
        return patterns
    
    def detect_morning_evening_star(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Morning Star and Evening Star patterns"""
        patterns = []
        
        try:
            for i in range(2, len(rates)):
                first = rates.iloc[i-2]
                second = rates.iloc[i-1]
                third = rates.iloc[i]
                
                first_body = abs(first['close'] - first['open'])
                second_body = abs(second['close'] - second['open'])
                third_body = abs(third['close'] - third['open'])
                
                # Morning Star
                if (first['close'] < first['open'] and        # First candle red
                    second_body < first_body * 0.5 and       # Second candle small
                    third['close'] > third['open'] and       # Third candle green
                    third['close'] > (first['open'] + first['close']) / 2):  # Third closes above first midpoint
                    
                    patterns.append({
                        'type': 'Morning Star',
                        'signal': 'BULLISH',
                        'confidence': 0.8,
                        'index': i,
                        'description': 'Morning Star pattern - strong bullish reversal signal',
                        'bullish': True
                    })
                
                # Evening Star
                elif (first['close'] > first['open'] and      # First candle green
                      second_body < first_body * 0.5 and     # Second candle small
                      third['close'] < third['open'] and     # Third candle red
                      third['close'] < (first['open'] + first['close']) / 2):  # Third closes below first midpoint
                    
                    patterns.append({
                        'type': 'Evening Star',
                        'signal': 'BEARISH',
                        'confidence': 0.8,
                        'index': i,
                        'description': 'Evening Star pattern - strong bearish reversal signal',
                        'bullish': False
                    })
        except Exception as e:
            self.logger.error(f"Error detecting Morning/Evening Star: {e}")
        
        return patterns
    
    def detect_three_white_soldiers(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Three White Soldiers pattern"""
        patterns = []
        
        try:
            for i in range(2, len(rates)):
                first = rates.iloc[i-2]
                second = rates.iloc[i-1]
                third = rates.iloc[i]
                
                if (first['close'] > first['open'] and        # All green candles
                    second['close'] > second['open'] and
                    third['close'] > third['open'] and
                    second['close'] > first['close'] and     # Ascending closes
                    third['close'] > second['close'] and
                    second['open'] > first['open'] and       # Each opens higher
                    third['open'] > second['open']):
                    
                    patterns.append({
                        'type': 'Three White Soldiers',
                        'signal': 'BULLISH',
                        'confidence': 0.8,
                        'index': i,
                        'description': 'Three White Soldiers pattern - strong bullish continuation',
                        'bullish': True
                    })
        except Exception as e:
            self.logger.error(f"Error detecting Three White Soldiers: {e}")
        
        return patterns
    
    def detect_three_black_crows(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Three Black Crows pattern"""
        patterns = []
        
        try:
            for i in range(2, len(rates)):
                first = rates.iloc[i-2]
                second = rates.iloc[i-1]
                third = rates.iloc[i]
                
                if (first['close'] < first['open'] and        # All red candles
                    second['close'] < second['open'] and
                    third['close'] < third['open'] and
                    second['close'] < first['close'] and     # Descending closes
                    third['close'] < second['close'] and
                    second['open'] < first['open'] and       # Each opens lower
                    third['open'] < second['open']):
                    
                    patterns.append({
                        'type': 'Three Black Crows',
                        'signal': 'BEARISH',
                        'confidence': 0.8,
                        'index': i,
                        'description': 'Three Black Crows pattern - strong bearish continuation',
                        'bullish': False
                    })
        except Exception as e:
            self.logger.error(f"Error detecting Three Black Crows: {e}")
        
        return patterns
    
    def _determine_trend(self, rates: pd.DataFrame) -> str:
        """Determine trend direction from price data"""
        try:
            if len(rates) < 3:
                return 'neutral'
            
            closes = rates['close'].values
            
            # Simple trend determination using linear regression slope
            x = np.arange(len(closes))
            slope = np.polyfit(x, closes, 1)[0]
            
            if slope > closes[-1] * 0.001:  # Slope > 0.1% of current price
                return 'uptrend'
            elif slope < -closes[-1] * 0.001:  # Slope < -0.1% of current price
                return 'downtrend'
            else:
                return 'neutral'
                
        except Exception as e:
            self.logger.error(f"Error determining trend: {e}")
            return 'neutral'
    
    def get_pattern_significance(self, pattern: Dict, rates: pd.DataFrame) -> float:
        """Calculate pattern significance based on context"""
        try:
            base_confidence = pattern.get('confidence', 0.5)
            
            # Factors that increase significance
            multiplier = 1.0
            
            # Volume confirmation (if available)
            if 'tick_volume' in rates.columns:
                pattern_index = pattern.get('index', len(rates) - 1)
                if pattern_index > 0:
                    current_volume = rates.iloc[pattern_index]['tick_volume']
                    avg_volume = rates['tick_volume'].tail(20).mean()
                    if current_volume > avg_volume * 1.5:
                        multiplier += 0.2  # Higher volume increases significance
            
            # Position in trend
            if pattern.get('signal') == 'REVERSAL':
                multiplier += 0.1  # Reversal patterns at trend extremes are more significant
            
            # Pattern type reliability
            high_reliability_patterns = ['Morning Star', 'Evening Star', 'Bullish Engulfing', 'Bearish Engulfing']
            if pattern.get('type') in high_reliability_patterns:
                multiplier += 0.15
            
            return min(1.0, base_confidence * multiplier)
            
        except Exception as e:
            self.logger.error(f"Error calculating pattern significance: {e}")
            return pattern.get('confidence', 0.5)

class ChartPatternRecognition:
    """Chart pattern recognition for trend analysis"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
    
    def detect_trend_patterns(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect trend-based chart patterns"""
        patterns = []
        
        if len(rates) < 20:
            return patterns
        
        try:
            patterns.extend(self.detect_triangles(rates))
            patterns.extend(self.detect_channels(rates))
            patterns.extend(self.detect_head_shoulders(rates))
            patterns.extend(self.detect_double_tops_bottoms(rates))
            
        except Exception as e:
            self.logger.error(f"Error detecting trend patterns: {e}")
        
        return patterns
    
    def detect_triangles(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect triangle patterns"""
        patterns = []
        
        try:
            # Analyze recent 20 bars for triangle formation
            recent = rates.tail(20)
            highs = recent['high'].values
            lows = recent['low'].values
            
            # Fit trend lines to highs and lows
            x = np.arange(len(highs))
            high_slope = np.polyfit(x, highs, 1)[0]
            low_slope = np.polyfit(x, lows, 1)[0]
            
            # Symmetric Triangle
            if abs(high_slope) > 0 and abs(low_slope) > 0:
                if high_slope < 0 and low_slope > 0:  # Converging lines
                    patterns.append({
                        'type': 'Symmetric Triangle',
                        'signal': 'BREAKOUT_PENDING',
                        'confidence': 0.6,
                        'description': 'Symmetric Triangle - awaiting breakout direction'
                    })
                elif high_slope > 0 and low_slope > high_slope:  # Ascending triangle
                    patterns.append({
                        'type': 'Ascending Triangle',
                        'signal': 'BULLISH',
                        'confidence': 0.65,
                        'description': 'Ascending Triangle - bullish breakout expected'
                    })
                elif high_slope < 0 and low_slope < high_slope:  # Descending triangle
                    patterns.append({
                        'type': 'Descending Triangle',
                        'signal': 'BEARISH',
                        'confidence': 0.65,
                        'description': 'Descending Triangle - bearish breakout expected'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error detecting triangles: {e}")
        
        return patterns
    
    def detect_channels(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect channel patterns"""
        patterns = []
        
        try:
            recent = rates.tail(30)
            highs = recent['high'].values
            lows = recent['low'].values
            
            x = np.arange(len(highs))
            high_slope = np.polyfit(x, highs, 1)[0]
            low_slope = np.polyfit(x, lows, 1)[0]
            
            # Parallel channel detection
            if abs(high_slope - low_slope) < abs(high_slope) * 0.1:  # Slopes are similar
                if high_slope > 0 and low_slope > 0:
                    patterns.append({
                        'type': 'Ascending Channel',
                        'signal': 'BULLISH',
                        'confidence': 0.7,
                        'description': 'Ascending Channel - upward trend continuation'
                    })
                elif high_slope < 0 and low_slope < 0:
                    patterns.append({
                        'type': 'Descending Channel',
                        'signal': 'BEARISH',
                        'confidence': 0.7,
                        'description': 'Descending Channel - downward trend continuation'
                    })
                else:
                    patterns.append({
                        'type': 'Horizontal Channel',
                        'signal': 'RANGE_BOUND',
                        'confidence': 0.6,
                        'description': 'Horizontal Channel - range-bound movement'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error detecting channels: {e}")
        
        return patterns
    
    def detect_head_shoulders(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Head and Shoulders patterns"""
        patterns = []
        
        try:
            if len(rates) < 30:
                return patterns
            
            recent = rates.tail(30)
            highs = recent['high'].values
            lows = recent['low'].values
            
            # Find local extremes
            peaks = []
            troughs = []
            
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    peaks.append((i, highs[i]))
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    troughs.append((i, lows[i]))
            
            # Head and Shoulders Top
            if len(peaks) >= 3:
                last_three_peaks = peaks[-3:]
                left_shoulder = last_three_peaks[0][1]
                head = last_three_peaks[1][1]
                right_shoulder = last_three_peaks[2][1]
                
                if (head > left_shoulder and head > right_shoulder and
                    abs(left_shoulder - right_shoulder) / left_shoulder < 0.02):  # Shoulders similar height
                    
                    patterns.append({
                        'type': 'Head and Shoulders Top',
                        'signal': 'BEARISH',
                        'confidence': 0.75,
                        'description': 'Head and Shoulders Top - bearish reversal pattern'
                    })
            
            # Inverse Head and Shoulders
            if len(troughs) >= 3:
                last_three_troughs = troughs[-3:]
                left_shoulder = last_three_troughs[0][1]
                head = last_three_troughs[1][1]
                right_shoulder = last_three_troughs[2][1]
                
                if (head < left_shoulder and head < right_shoulder and
                    abs(left_shoulder - right_shoulder) / left_shoulder < 0.02):
                    
                    patterns.append({
                        'type': 'Inverse Head and Shoulders',
                        'signal': 'BULLISH',
                        'confidence': 0.75,
                        'description': 'Inverse Head and Shoulders - bullish reversal pattern'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error detecting Head and Shoulders: {e}")
        
        return patterns
    
    def detect_double_tops_bottoms(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect Double Top and Double Bottom patterns"""
        patterns = []
        
        try:
            if len(rates) < 20:
                return patterns
            
            recent = rates.tail(20)
            highs = recent['high'].values
            lows = recent['low'].values
            
            # Find significant peaks and troughs
            peaks = []
            troughs = []
            
            for i in range(3, len(highs) - 3):
                if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and
                    highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                    peaks.append(highs[i])
                
                if (lows[i] < lows[i-1] and lows[i] < lows[i+1] and
                    lows[i] < lows[i-2] and lows[i] < lows[i+2]):
                    troughs.append(lows[i])
            
            # Double Top
            if len(peaks) >= 2:
                if abs(peaks[-1] - peaks[-2]) / peaks[-1] < 0.01:  # Peaks within 1%
                    patterns.append({
                        'type': 'Double Top',
                        'signal': 'BEARISH',
                        'confidence': 0.7,
                        'description': 'Double Top pattern - bearish reversal signal'
                    })
            
            # Double Bottom
            if len(troughs) >= 2:
                if abs(troughs[-1] - troughs[-2]) / troughs[-1] < 0.01:  # Troughs within 1%
                    patterns.append({
                        'type': 'Double Bottom',
                        'signal': 'BULLISH',
                        'confidence': 0.7,
                        'description': 'Double Bottom pattern - bullish reversal signal'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error detecting Double Tops/Bottoms: {e}")
        
        return patterns

# Main pattern recognition coordinator
class PatternRecognition:
    """Main pattern recognition coordinator"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.candlestick_patterns = CandlestickPatternRecognition()
        self.chart_patterns = ChartPatternRecognition()
    
    def analyze_patterns(self, rates: pd.DataFrame) -> Dict:
        """Comprehensive pattern analysis"""
        try:
            # Get all patterns
            candlestick_patterns = self.candlestick_patterns.detect_all_patterns(rates)
            chart_patterns = self.chart_patterns.detect_trend_patterns(rates)
            
            # Combine and prioritize
            all_patterns = candlestick_patterns + chart_patterns
            
            # Sort by confidence
            all_patterns.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Analysis summary
            bullish_signals = len([p for p in all_patterns if p.get('bullish') == True or p.get('signal') == 'BULLISH'])
            bearish_signals = len([p for p in all_patterns if p.get('bullish') == False or p.get('signal') == 'BEARISH'])
            
            overall_sentiment = 'NEUTRAL'
            if bullish_signals > bearish_signals:
                overall_sentiment = 'BULLISH'
            elif bearish_signals > bullish_signals:
                overall_sentiment = 'BEARISH'
            
            return {
                'patterns': all_patterns[:10],  # Top 10 patterns
                'total_patterns': len(all_patterns),
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'overall_sentiment': overall_sentiment,
                'confidence': max([p.get('confidence', 0) for p in all_patterns]) if all_patterns else 0,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")
            return {
                'patterns': [],
                'total_patterns': 0,
                'bullish_signals': 0,
                'bearish_signals': 0,
                'overall_sentiment': 'NEUTRAL',
                'confidence': 0,
                'timestamp': datetime.now()
            }

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
