
"""
Pattern Recognition Module for AuraTrade Bot
Advanced chart pattern and candlestick pattern detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from utils.logger import Logger

class PatternRecognition:
    """Advanced pattern recognition system"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
    
    def detect_all_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """Detect all patterns in the given data"""
        patterns = []
        
        try:
            if len(data) < 20:
                return patterns
            
            # Chart patterns
            patterns.extend(self._detect_chart_patterns(data))
            
            # Candlestick patterns
            patterns.extend(self._detect_candlestick_patterns(data))
            
            # Support/Resistance patterns
            patterns.extend(self._detect_sr_patterns(data))
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
            return []
    
    def _detect_chart_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """Detect chart patterns like triangles, channels, etc."""
        patterns = []
        
        try:
            # Triangle patterns
            triangle = self._detect_triangle_pattern(data)
            if triangle:
                patterns.append(triangle)
            
            # Channel patterns
            channel = self._detect_channel_pattern(data)
            if channel:
                patterns.append(channel)
            
            # Head and shoulders
            head_shoulders = self._detect_head_shoulders(data)
            if head_shoulders:
                patterns.append(head_shoulders)
            
            # Double top/bottom
            double_pattern = self._detect_double_top_bottom(data)
            if double_pattern:
                patterns.append(double_pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting chart patterns: {e}")
            return []
    
    def _detect_triangle_pattern(self, data: pd.DataFrame, min_touches: int = 4) -> Optional[Dict]:
        """Detect triangle patterns (ascending, descending, symmetrical)"""
        try:
            if len(data) < 20:
                return None
            
            highs = data['high'].values
            lows = data['low'].values
            
            # Find significant highs and lows
            high_peaks = self._find_peaks(highs, min_prominence=0.0005)
            low_valleys = self._find_peaks(-lows, min_prominence=0.0005)
            
            if len(high_peaks) < 2 or len(low_valleys) < 2:
                return None
            
            # Get recent peaks and valleys
            recent_highs = high_peaks[-4:] if len(high_peaks) >= 4 else high_peaks
            recent_lows = low_valleys[-4:] if len(low_valleys) >= 4 else low_valleys
            
            # Calculate trend lines
            high_slope = self._calculate_trendline_slope(recent_highs, highs)
            low_slope = self._calculate_trendline_slope(recent_lows, lows)
            
            # Determine triangle type
            if abs(high_slope) < 0.0001 and low_slope > 0.0001:
                pattern_type = "Ascending Triangle"
                signal = "bullish"
                confidence = 75
            elif high_slope < -0.0001 and abs(low_slope) < 0.0001:
                pattern_type = "Descending Triangle"
                signal = "bearish"
                confidence = 75
            elif high_slope < -0.0001 and low_slope > 0.0001:
                pattern_type = "Symmetrical Triangle"
                signal = "breakout_pending"
                confidence = 65
            else:
                return None
            
            return {
                'type': 'chart_pattern',
                'name': pattern_type,
                'signal': signal,
                'confidence': confidence,
                'high_slope': high_slope,
                'low_slope': low_slope
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting triangle pattern: {e}")
            return None
    
    def _detect_channel_pattern(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect channel patterns (parallel trend lines)"""
        try:
            if len(data) < 30:
                return None
            
            highs = data['high'].values
            lows = data['low'].values
            
            # Find peaks and valleys
            high_peaks = self._find_peaks(highs, min_prominence=0.001)
            low_valleys = self._find_peaks(-lows, min_prominence=0.001)
            
            if len(high_peaks) < 3 or len(low_valleys) < 3:
                return None
            
            # Calculate trend lines
            high_slope = self._calculate_trendline_slope(high_peaks, highs)
            low_slope = self._calculate_trendline_slope(low_valleys, lows)
            
            # Check if slopes are parallel (similar)
            slope_diff = abs(high_slope - low_slope)
            
            if slope_diff < 0.0002:  # Parallel lines
                if high_slope > 0.0001:
                    pattern_type = "Ascending Channel"
                    signal = "bullish"
                elif high_slope < -0.0001:
                    pattern_type = "Descending Channel"
                    signal = "bearish"
                else:
                    pattern_type = "Horizontal Channel"
                    signal = "range_bound"
                
                return {
                    'type': 'chart_pattern',
                    'name': pattern_type,
                    'signal': signal,
                    'confidence': 70,
                    'high_slope': high_slope,
                    'low_slope': low_slope
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting channel pattern: {e}")
            return None
    
    def _detect_head_shoulders(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect head and shoulders pattern"""
        try:
            if len(data) < 30:
                return None
            
            highs = data['high'].values
            high_peaks = self._find_peaks(highs, min_prominence=0.001)
            
            if len(high_peaks) < 3:
                return None
            
            # Check last 3 peaks for head and shoulders
            if len(high_peaks) >= 3:
                left_shoulder = high_peaks[-3]
                head = high_peaks[-2]
                right_shoulder = high_peaks[-1]
                
                left_height = highs[left_shoulder]
                head_height = highs[head]
                right_height = highs[right_shoulder]
                
                # Head should be higher than both shoulders
                # Shoulders should be roughly equal height
                if (head_height > left_height and 
                    head_height > right_height and
                    abs(left_height - right_height) < (head_height - min(left_height, right_height)) * 0.3):
                    
                    return {
                        'type': 'chart_pattern',
                        'name': 'Head and Shoulders',
                        'signal': 'bearish',
                        'confidence': 80,
                        'left_shoulder': left_height,
                        'head': head_height,
                        'right_shoulder': right_height
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting head and shoulders: {e}")
            return None
    
    def _detect_double_top_bottom(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect double top/bottom patterns"""
        try:
            if len(data) < 20:
                return None
            
            highs = data['high'].values
            lows = data['low'].values
            
            high_peaks = self._find_peaks(highs, min_prominence=0.001)
            low_valleys = self._find_peaks(-lows, min_prominence=0.001)
            
            # Check for double top
            if len(high_peaks) >= 2:
                peak1 = high_peaks[-2]
                peak2 = high_peaks[-1]
                
                height1 = highs[peak1]
                height2 = highs[peak2]
                
                # Heights should be similar (within 0.5%)
                if abs(height1 - height2) / max(height1, height2) < 0.005:
                    return {
                        'type': 'chart_pattern',
                        'name': 'Double Top',
                        'signal': 'bearish',
                        'confidence': 75,
                        'peak1': height1,
                        'peak2': height2
                    }
            
            # Check for double bottom
            if len(low_valleys) >= 2:
                valley1 = low_valleys[-2]
                valley2 = low_valleys[-1]
                
                depth1 = lows[valley1]
                depth2 = lows[valley2]
                
                # Depths should be similar (within 0.5%)
                if abs(depth1 - depth2) / max(depth1, depth2) < 0.005:
                    return {
                        'type': 'chart_pattern',
                        'name': 'Double Bottom',
                        'signal': 'bullish',
                        'confidence': 75,
                        'valley1': depth1,
                        'valley2': depth2
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting double top/bottom: {e}")
            return None
    
    def _detect_sr_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """Detect support and resistance patterns"""
        patterns = []
        
        try:
            current_price = data['close'].iloc[-1]
            
            # Calculate dynamic support/resistance levels
            highs = data['high'].tail(50)
            lows = data['low'].tail(50)
            
            # Find significant levels
            resistance_levels = self._find_resistance_levels(highs)
            support_levels = self._find_support_levels(lows)
            
            # Check if current price is near key levels
            for level in resistance_levels:
                distance = abs(current_price - level) / current_price
                if distance < 0.002:  # Within 0.2%
                    patterns.append({
                        'type': 'support_resistance',
                        'name': 'Near Resistance',
                        'signal': 'bearish',
                        'confidence': 60,
                        'level': level,
                        'distance': distance
                    })
            
            for level in support_levels:
                distance = abs(current_price - level) / current_price
                if distance < 0.002:  # Within 0.2%
                    patterns.append({
                        'type': 'support_resistance',
                        'name': 'Near Support',
                        'signal': 'bullish',
                        'confidence': 60,
                        'level': level,
                        'distance': distance
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting S/R patterns: {e}")
            return []
    
    def _find_peaks(self, data: np.array, min_prominence: float = 0.001) -> List[int]:
        """Find peaks in data array"""
        try:
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(data, prominence=min_prominence * np.mean(data))
            return peaks.tolist()
        except ImportError:
            # Fallback implementation without scipy
            peaks = []
            for i in range(1, len(data) - 1):
                if data[i] > data[i-1] and data[i] > data[i+1]:
                    peaks.append(i)
            return peaks
    
    def _calculate_trendline_slope(self, indices: List[int], values: np.array) -> float:
        """Calculate slope of trendline through given points"""
        try:
            if len(indices) < 2:
                return 0.0
            
            x = np.array(indices)
            y = values[indices]
            
            slope, _, _, _, _ = stats.linregress(x, y)
            return slope
        except:
            return 0.0
    
    def _find_resistance_levels(self, highs: pd.Series) -> List[float]:
        """Find resistance levels from highs"""
        try:
            # Group similar highs into levels
            levels = []
            sorted_highs = highs.sort_values(ascending=False)
            
            for high in sorted_highs[:10]:  # Top 10 highs
                # Check if this high is similar to existing level
                is_new_level = True
                for level in levels:
                    if abs(high - level) / level < 0.002:  # Within 0.2%
                        is_new_level = False
                        break
                
                if is_new_level:
                    levels.append(high)
                
                if len(levels) >= 5:  # Max 5 levels
                    break
            
            return levels
        except:
            return []
    
    def _find_support_levels(self, lows: pd.Series) -> List[float]:
        """Find support levels from lows"""
        try:
            # Group similar lows into levels
            levels = []
            sorted_lows = lows.sort_values()
            
            for low in sorted_lows[:10]:  # Bottom 10 lows
                # Check if this low is similar to existing level
                is_new_level = True
                for level in levels:
                    if abs(low - level) / level < 0.002:  # Within 0.2%
                        is_new_level = False
                        break
                
                if is_new_level:
                    levels.append(low)
                
                if len(levels) >= 5:  # Max 5 levels
                    break
            
            return levels
        except:
            return []
