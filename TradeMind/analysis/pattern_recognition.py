"""
Pattern Recognition module for AuraTrade Bot
Detects candlestick patterns and chart formations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from utils.logger import Logger

class PatternRecognition:
    """Pattern recognition for candlestick and chart patterns"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        
        # Pattern detection thresholds
        self.thresholds = {
            "doji_body_ratio": 0.1,          # Body must be < 10% of total range
            "hammer_body_ratio": 0.3,        # Body must be < 30% of total range
            "hammer_wick_ratio": 2.0,        # Lower wick must be > 2x body
            "shooting_star_ratio": 2.0,      # Upper wick must be > 2x body
            "engulfing_min_ratio": 1.1,      # Engulfing body must be > 110% of previous
            "pinbar_wick_ratio": 2.5,        # Pin bar wick must be > 2.5x body
            "inside_bar_ratio": 0.95         # Inside bar must be < 95% of previous range
        }
    
    def detect_hammer(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect hammer candlestick patterns"""
        try:
            if len(data) < 2:
                return []
            
            patterns = []
            
            for i in range(1, len(data)):
                current = data.iloc[i]
                previous = data.iloc[i-1]
                
                open_price = current['open']
                close_price = current['close']
                high_price = current['high']
                low_price = current['low']
                
                # Calculate components
                body = abs(close_price - open_price)
                total_range = high_price - low_price
                upper_wick = high_price - max(open_price, close_price)
                lower_wick = min(open_price, close_price) - low_price
                
                if total_range == 0:
                    continue
                
                # Hammer conditions
                body_ratio = body / total_range
                wick_ratio = lower_wick / body if body > 0 else 0
                
                # Check if it's a hammer
                is_hammer = (
                    body_ratio < self.thresholds["hammer_body_ratio"] and
                    wick_ratio > self.thresholds["hammer_wick_ratio"] and
                    upper_wick < body and
                    lower_wick > body * 2
                )
                
                if is_hammer:
                    # Determine if bullish or bearish hammer
                    if close_price > open_price:
                        direction = "BUY"
                        pattern_type = "bullish_hammer"
                    else:
                        direction = "BUY"  # Even bearish hammers are bullish signals
                        pattern_type = "hammer"
                    
                    # Calculate pattern strength
                    strength = min(wick_ratio / 5.0, 1.0)  # Normalize strength
                    
                    patterns.append({
                        "pattern_type": pattern_type,
                        "direction": direction,
                        "strength": strength,
                        "quality": 1.0 - body_ratio,  # Higher quality for smaller body
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i,
                        "confirmation": self._check_hammer_confirmation(data, i)
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting hammer patterns: {e}")
            return []
    
    def detect_doji(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect doji candlestick patterns"""
        try:
            if len(data) < 1:
                return []
            
            patterns = []
            
            for i in range(len(data)):
                current = data.iloc[i]
                
                open_price = current['open']
                close_price = current['close']
                high_price = current['high']
                low_price = current['low']
                
                # Calculate components
                body = abs(close_price - open_price)
                total_range = high_price - low_price
                
                if total_range == 0:
                    continue
                
                body_ratio = body / total_range
                
                # Doji condition: very small body relative to range
                if body_ratio < self.thresholds["doji_body_ratio"]:
                    upper_wick = high_price - max(open_price, close_price)
                    lower_wick = min(open_price, close_price) - low_price
                    
                    # Classify doji type
                    if upper_wick > lower_wick * 2:
                        pattern_type = "gravestone_doji"
                        direction = "SELL"
                    elif lower_wick > upper_wick * 2:
                        pattern_type = "dragonfly_doji"
                        direction = "BUY"
                    else:
                        pattern_type = "standard_doji"
                        direction = "NEUTRAL"
                    
                    # Calculate strength based on wick balance and context
                    strength = 1.0 - body_ratio  # Smaller body = stronger signal
                    
                    patterns.append({
                        "pattern_type": pattern_type,
                        "direction": direction,
                        "strength": strength * 0.7,  # Doji are weaker signals
                        "quality": 1.0 - body_ratio,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i,
                        "confirmation": self._check_doji_confirmation(data, i)
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting doji patterns: {e}")
            return []
    
    def detect_engulfing(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect engulfing candlestick patterns"""
        try:
            if len(data) < 2:
                return []
            
            patterns = []
            
            for i in range(1, len(data)):
                current = data.iloc[i]
                previous = data.iloc[i-1]
                
                # Current candle
                curr_open = current['open']
                curr_close = current['close']
                curr_body = abs(curr_close - curr_open)
                
                # Previous candle
                prev_open = previous['open']
                prev_close = previous['close']
                prev_body = abs(prev_close - prev_open)
                
                if prev_body == 0:
                    continue
                
                # Check for bullish engulfing
                if (prev_close < prev_open and  # Previous was bearish
                    curr_close > curr_open and  # Current is bullish
                    curr_open < prev_close and  # Current opens below previous close
                    curr_close > prev_open and  # Current closes above previous open
                    curr_body > prev_body * self.thresholds["engulfing_min_ratio"]):
                    
                    strength = min(curr_body / prev_body / 2.0, 1.0)
                    
                    patterns.append({
                        "pattern_type": "bullish_engulfing",
                        "direction": "BUY",
                        "strength": strength,
                        "quality": curr_body / prev_body,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i,
                        "confirmation": self._check_engulfing_confirmation(data, i, "bullish")
                    })
                
                # Check for bearish engulfing
                elif (prev_close > prev_open and  # Previous was bullish
                      curr_close < curr_open and  # Current is bearish
                      curr_open > prev_close and  # Current opens above previous close
                      curr_close < prev_open and  # Current closes below previous open
                      curr_body > prev_body * self.thresholds["engulfing_min_ratio"]):
                    
                    strength = min(curr_body / prev_body / 2.0, 1.0)
                    
                    patterns.append({
                        "pattern_type": "bearish_engulfing",
                        "direction": "SELL",
                        "strength": strength,
                        "quality": curr_body / prev_body,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i,
                        "confirmation": self._check_engulfing_confirmation(data, i, "bearish")
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting engulfing patterns: {e}")
            return []
    
    def detect_pinbar(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect pin bar (pin bar) patterns"""
        try:
            if len(data) < 1:
                return []
            
            patterns = []
            
            for i in range(len(data)):
                current = data.iloc[i]
                
                open_price = current['open']
                close_price = current['close']
                high_price = current['high']
                low_price = current['low']
                
                # Calculate components
                body = abs(close_price - open_price)
                total_range = high_price - low_price
                upper_wick = high_price - max(open_price, close_price)
                lower_wick = min(open_price, close_price) - low_price
                
                if total_range == 0 or body == 0:
                    continue
                
                # Check for bullish pin bar (long lower wick)
                if (lower_wick > body * self.thresholds["pinbar_wick_ratio"] and
                    upper_wick < body and
                    body / total_range < 0.3):
                    
                    strength = min(lower_wick / body / 3.0, 1.0)
                    
                    patterns.append({
                        "pattern_type": "bullish_pinbar",
                        "direction": "BUY",
                        "strength": strength,
                        "quality": lower_wick / total_range,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i,
                        "confirmation": self._check_pinbar_confirmation(data, i, "bullish")
                    })
                
                # Check for bearish pin bar (long upper wick)
                elif (upper_wick > body * self.thresholds["pinbar_wick_ratio"] and
                      lower_wick < body and
                      body / total_range < 0.3):
                    
                    strength = min(upper_wick / body / 3.0, 1.0)
                    
                    patterns.append({
                        "pattern_type": "bearish_pinbar",
                        "direction": "SELL",
                        "strength": strength,
                        "quality": upper_wick / total_range,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i,
                        "confirmation": self._check_pinbar_confirmation(data, i, "bearish")
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting pin bar patterns: {e}")
            return []
    
    def detect_inside_bar(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect inside bar patterns"""
        try:
            if len(data) < 2:
                return []
            
            patterns = []
            
            for i in range(1, len(data)):
                current = data.iloc[i]
                previous = data.iloc[i-1]
                
                curr_high = current['high']
                curr_low = current['low']
                prev_high = previous['high']
                prev_low = previous['low']
                
                # Inside bar conditions
                if (curr_high < prev_high and curr_low > prev_low):
                    current_range = curr_high - curr_low
                    previous_range = prev_high - prev_low
                    
                    if previous_range == 0:
                        continue
                    
                    range_ratio = current_range / previous_range
                    
                    # Quality based on how much smaller the inside bar is
                    quality = 1.0 - range_ratio
                    strength = quality * 0.6  # Inside bars are continuation patterns
                    
                    patterns.append({
                        "pattern_type": "inside_bar",
                        "direction": "CONTINUATION",  # Direction depends on breakout
                        "strength": strength,
                        "quality": quality,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i,
                        "range_ratio": range_ratio,
                        "confirmation": self._check_inside_bar_confirmation(data, i)
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting inside bar patterns: {e}")
            return []
    
    def detect_support_resistance(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect support and resistance levels using swing points"""
        try:
            if len(data) < 10:
                return []
            
            patterns = []
            swing_window = 5
            
            highs = data['high'].values
            lows = data['low'].values
            
            # Find swing highs (resistance)
            for i in range(swing_window, len(data) - swing_window):
                is_swing_high = True
                current_high = highs[i]
                
                # Check if current high is higher than surrounding highs
                for j in range(i - swing_window, i + swing_window + 1):
                    if j != i and highs[j] >= current_high:
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    # Check for multiple touches (stronger resistance)
                    touches = self._count_level_touches(highs, current_high, 0.001)
                    
                    patterns.append({
                        "pattern_type": "resistance",
                        "level": current_high,
                        "strength": min(touches / 5.0, 1.0),
                        "touches": touches,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i
                    })
            
            # Find swing lows (support)
            for i in range(swing_window, len(data) - swing_window):
                is_swing_low = True
                current_low = lows[i]
                
                # Check if current low is lower than surrounding lows
                for j in range(i - swing_window, i + swing_window + 1):
                    if j != i and lows[j] <= current_low:
                        is_swing_low = False
                        break
                
                if is_swing_low:
                    # Check for multiple touches (stronger support)
                    touches = self._count_level_touches(lows, current_low, 0.001)
                    
                    patterns.append({
                        "pattern_type": "support",
                        "level": current_low,
                        "strength": min(touches / 5.0, 1.0),
                        "touches": touches,
                        "bar_index": i,
                        "bars_ago": len(data) - 1 - i
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting support/resistance: {e}")
            return []
    
    def detect_triangles(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect triangle chart patterns"""
        try:
            if len(data) < 20:
                return []
            
            patterns = []
            
            # Get recent data for triangle detection
            recent_data = data.tail(20)
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            
            # Find swing points
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(recent_data) - 2):
                # Swing high
                if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and
                    highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                    swing_highs.append((i, highs[i]))
                
                # Swing low
                if (lows[i] < lows[i-1] and lows[i] < lows[i+1] and
                    lows[i] < lows[i-2] and lows[i] < lows[i+2]):
                    swing_lows.append((i, lows[i]))
            
            # Need at least 2 swing highs and 2 swing lows
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                # Calculate trend lines
                high_slope = self._calculate_slope(swing_highs)
                low_slope = self._calculate_slope(swing_lows)
                
                # Determine triangle type
                if abs(high_slope) < 0.0001 and low_slope > 0:
                    triangle_type = "ascending_triangle"
                    direction = "BUY"
                elif high_slope < 0 and abs(low_slope) < 0.0001:
                    triangle_type = "descending_triangle"
                    direction = "SELL"
                elif high_slope < 0 and low_slope > 0:
                    triangle_type = "symmetrical_triangle"
                    direction = "BREAKOUT"
                else:
                    return patterns
                
                # Calculate pattern quality
                quality = self._calculate_triangle_quality(swing_highs, swing_lows, high_slope, low_slope)
                
                patterns.append({
                    "pattern_type": triangle_type,
                    "direction": direction,
                    "strength": quality,
                    "quality": quality,
                    "high_slope": high_slope,
                    "low_slope": low_slope,
                    "swing_highs": swing_highs,
                    "swing_lows": swing_lows
                })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting triangles: {e}")
            return []
    
    def detect_head_shoulders(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect head and shoulders patterns"""
        try:
            if len(data) < 15:
                return []
            
            patterns = []
            
            # Look for head and shoulders in recent data
            recent_data = data.tail(15)
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            
            # Find significant peaks
            peaks = []
            for i in range(2, len(highs) - 2):
                if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and
                    highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                    peaks.append((i, highs[i]))
            
            # Need at least 3 peaks for head and shoulders
            if len(peaks) >= 3:
                # Check if middle peak is highest (head)
                for i in range(1, len(peaks) - 1):
                    left_shoulder = peaks[i-1]
                    head = peaks[i]
                    right_shoulder = peaks[i+1]
                    
                    # Head should be higher than shoulders
                    if (head[1] > left_shoulder[1] and head[1] > right_shoulder[1]):
                        # Shoulders should be roughly equal
                        shoulder_diff = abs(left_shoulder[1] - right_shoulder[1]) / head[1]
                        
                        if shoulder_diff < 0.05:  # Shoulders within 5% of each other
                            # Find neckline (support level between shoulders)
                            neckline = self._find_neckline(recent_data, left_shoulder[0], right_shoulder[0])
                            
                            if neckline:
                                quality = 1.0 - shoulder_diff  # Better quality for more equal shoulders
                                
                                patterns.append({
                                    "pattern_type": "head_and_shoulders",
                                    "direction": "SELL",
                                    "strength": quality * 0.8,
                                    "quality": quality,
                                    "left_shoulder": left_shoulder,
                                    "head": head,
                                    "right_shoulder": right_shoulder,
                                    "neckline": neckline
                                })
            
            # Look for inverse head and shoulders
            troughs = []
            for i in range(2, len(lows) - 2):
                if (lows[i] < lows[i-1] and lows[i] < lows[i+1] and
                    lows[i] < lows[i-2] and lows[i] < lows[i+2]):
                    troughs.append((i, lows[i]))
            
            if len(troughs) >= 3:
                for i in range(1, len(troughs) - 1):
                    left_shoulder = troughs[i-1]
                    head = troughs[i]
                    right_shoulder = troughs[i+1]
                    
                    # Head should be lower than shoulders
                    if (head[1] < left_shoulder[1] and head[1] < right_shoulder[1]):
                        shoulder_diff = abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1]
                        
                        if shoulder_diff < 0.05:
                            neckline = self._find_neckline(recent_data, left_shoulder[0], right_shoulder[0])
                            
                            if neckline:
                                quality = 1.0 - shoulder_diff
                                
                                patterns.append({
                                    "pattern_type": "inverse_head_and_shoulders",
                                    "direction": "BUY",
                                    "strength": quality * 0.8,
                                    "quality": quality,
                                    "left_shoulder": left_shoulder,
                                    "head": head,
                                    "right_shoulder": right_shoulder,
                                    "neckline": neckline
                                })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting head and shoulders: {e}")
            return []
    
    def detect_double_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect double top and double bottom patterns"""
        try:
            if len(data) < 10:
                return []
            
            patterns = []
            
            recent_data = data.tail(10)
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            
            # Find peaks for double top
            peaks = []
            for i in range(1, len(highs) - 1):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    peaks.append((i, highs[i]))
            
            # Check for double top
            if len(peaks) >= 2:
                for i in range(len(peaks) - 1):
                    peak1 = peaks[i]
                    peak2 = peaks[i + 1]
                    
                    # Peaks should be similar height
                    height_diff = abs(peak1[1] - peak2[1]) / max(peak1[1], peak2[1])
                    
                    if height_diff < 0.03:  # Within 3%
                        # Find valley between peaks
                        valley_start = peak1[0]
                        valley_end = peak2[0]
                        valley_low = min(lows[valley_start:valley_end + 1])
                        
                        # Valley should be significantly lower
                        valley_depth = (min(peak1[1], peak2[1]) - valley_low) / min(peak1[1], peak2[1])
                        
                        if valley_depth > 0.02:  # At least 2% retracement
                            quality = (1.0 - height_diff) * valley_depth
                            
                            patterns.append({
                                "pattern_type": "double_top",
                                "direction": "SELL",
                                "strength": quality * 0.7,
                                "quality": quality,
                                "peak1": peak1,
                                "peak2": peak2,
                                "valley_low": valley_low
                            })
            
            # Find troughs for double bottom
            troughs = []
            for i in range(1, len(lows) - 1):
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    troughs.append((i, lows[i]))
            
            # Check for double bottom
            if len(troughs) >= 2:
                for i in range(len(troughs) - 1):
                    trough1 = troughs[i]
                    trough2 = troughs[i + 1]
                    
                    # Troughs should be similar depth
                    depth_diff = abs(trough1[1] - trough2[1]) / max(trough1[1], trough2[1])
                    
                    if depth_diff < 0.03:  # Within 3%
                        # Find peak between troughs
                        peak_start = trough1[0]
                        peak_end = trough2[0]
                        peak_high = max(highs[peak_start:peak_end + 1])
                        
                        # Peak should be significantly higher
                        peak_height = (peak_high - max(trough1[1], trough2[1])) / max(trough1[1], trough2[1])
                        
                        if peak_height > 0.02:  # At least 2% retracement
                            quality = (1.0 - depth_diff) * peak_height
                            
                            patterns.append({
                                "pattern_type": "double_bottom",
                                "direction": "BUY",
                                "strength": quality * 0.7,
                                "quality": quality,
                                "trough1": trough1,
                                "trough2": trough2,
                                "peak_high": peak_high
                            })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting double patterns: {e}")
            return []
    
    def detect_trend_channels(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect trend channel patterns"""
        try:
            if len(data) < 20:
                return []
            
            patterns = []
            
            # Use recent data for trend channel detection
            recent_data = data.tail(20)
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            closes = recent_data['close'].values
            
            # Find trend using linear regression
            x = np.arange(len(closes))
            
            # Calculate trend line for closes
            close_slope, close_intercept = np.polyfit(x, closes, 1)
            
            # Calculate parallel lines for highs and lows
            high_slope, high_intercept = np.polyfit(x, highs, 1)
            low_slope, low_intercept = np.polyfit(x, lows, 1)
            
            # Check if slopes are similar (parallel channel)
            slope_similarity = 1.0 - abs(high_slope - low_slope) / (abs(high_slope) + abs(low_slope) + 0.0001)
            
            if slope_similarity > 0.8:  # Slopes are similar
                # Calculate channel width
                channel_width = np.mean(highs - lows)
                
                # Determine trend direction
                if close_slope > 0:
                    trend_direction = "uptrend_channel"
                    direction = "BUY"
                elif close_slope < 0:
                    trend_direction = "downtrend_channel"
                    direction = "SELL"
                else:
                    trend_direction = "sideways_channel"
                    direction = "RANGE"
                
                # Calculate how well price respects the channel
                channel_quality = self._calculate_channel_quality(recent_data, high_slope, high_intercept, low_slope, low_intercept)
                
                patterns.append({
                    "pattern_type": trend_direction,
                    "direction": direction,
                    "strength": channel_quality * 0.6,
                    "quality": channel_quality,
                    "upper_slope": high_slope,
                    "upper_intercept": high_intercept,
                    "lower_slope": low_slope,
                    "lower_intercept": low_intercept,
                    "channel_width": channel_width
                })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting trend channels: {e}")
            return []
    
    # Helper methods for pattern confirmation
    
    def _check_hammer_confirmation(self, data: pd.DataFrame, index: int) -> bool:
        """Check for hammer pattern confirmation"""
        try:
            if index + 1 >= len(data):
                return False
            
            hammer_candle = data.iloc[index]
            next_candle = data.iloc[index + 1]
            
            # Confirmation: next candle should close higher than hammer's high
            return next_candle['close'] > hammer_candle['high']
            
        except:
            return False
    
    def _check_doji_confirmation(self, data: pd.DataFrame, index: int) -> bool:
        """Check for doji pattern confirmation"""
        try:
            if index + 1 >= len(data):
                return False
            
            doji_candle = data.iloc[index]
            next_candle = data.iloc[index + 1]
            
            # Confirmation: significant move in next candle
            doji_range = doji_candle['high'] - doji_candle['low']
            next_range = next_candle['high'] - next_candle['low']
            
            return next_range > doji_range * 1.5
            
        except:
            return False
    
    def _check_engulfing_confirmation(self, data: pd.DataFrame, index: int, pattern_type: str) -> bool:
        """Check for engulfing pattern confirmation"""
        try:
            if index + 1 >= len(data):
                return False
            
            engulfing_candle = data.iloc[index]
            next_candle = data.iloc[index + 1]
            
            if pattern_type == "bullish":
                # Next candle should continue upward
                return next_candle['close'] > engulfing_candle['close']
            else:
                # Next candle should continue downward
                return next_candle['close'] < engulfing_candle['close']
                
        except:
            return False
    
    def _check_pinbar_confirmation(self, data: pd.DataFrame, index: int, pattern_type: str) -> bool:
        """Check for pin bar pattern confirmation"""
        try:
            if index + 1 >= len(data):
                return False
            
            pinbar_candle = data.iloc[index]
            next_candle = data.iloc[index + 1]
            
            if pattern_type == "bullish":
                # Next candle should close above pinbar body
                pinbar_body_top = max(pinbar_candle['open'], pinbar_candle['close'])
                return next_candle['close'] > pinbar_body_top
            else:
                # Next candle should close below pinbar body
                pinbar_body_bottom = min(pinbar_candle['open'], pinbar_candle['close'])
                return next_candle['close'] < pinbar_body_bottom
                
        except:
            return False
    
    def _check_inside_bar_confirmation(self, data: pd.DataFrame, index: int) -> bool:
        """Check for inside bar pattern confirmation"""
        try:
            if index + 1 >= len(data):
                return False
            
            inside_bar = data.iloc[index]
            next_candle = data.iloc[index + 1]
            
            # Confirmation: breakout from inside bar range
            return (next_candle['close'] > inside_bar['high'] or 
                    next_candle['close'] < inside_bar['low'])
                    
        except:
            return False
    
    def _count_level_touches(self, prices: np.ndarray, level: float, tolerance: float) -> int:
        """Count how many times price touched a specific level"""
        try:
            touches = 0
            for price in prices:
                if abs(price - level) / level < tolerance:
                    touches += 1
            return touches
            
        except:
            return 0
    
    def _calculate_slope(self, points: List[Tuple[int, float]]) -> float:
        """Calculate slope of trend line through points"""
        try:
            if len(points) < 2:
                return 0
            
            x_values = [point[0] for point in points]
            y_values = [point[1] for point in points]
            
            slope, _ = np.polyfit(x_values, y_values, 1)
            return slope
            
        except:
            return 0
    
    def _calculate_triangle_quality(self, swing_highs: List[Tuple], swing_lows: List[Tuple], 
                                  high_slope: float, low_slope: float) -> float:
        """Calculate quality of triangle pattern"""
        try:
            # Quality based on how well points fit the trend lines
            quality = 0.5
            
            # More swing points = better quality
            total_points = len(swing_highs) + len(swing_lows)
            quality += min(total_points * 0.1, 0.3)
            
            # Converging lines = better quality
            if abs(high_slope - low_slope) > 0.001:
                convergence = 1.0 / abs(high_slope - low_slope)
                quality += min(convergence * 0.1, 0.2)
            
            return min(quality, 1.0)
            
        except:
            return 0.5
    
    def _find_neckline(self, data: pd.DataFrame, start_idx: int, end_idx: int) -> Optional[float]:
        """Find neckline level for head and shoulders pattern"""
        try:
            # Look for support level between shoulders
            segment = data.iloc[start_idx:end_idx + 1]
            lows = segment['low'].values
            
            # Find the highest low in the segment (strongest support)
            neckline = np.max(lows)
            return neckline
            
        except:
            return None
    
    def _calculate_channel_quality(self, data: pd.DataFrame, upper_slope: float, upper_intercept: float,
                                 lower_slope: float, lower_intercept: float) -> float:
        """Calculate how well price respects the channel boundaries"""
        try:
            highs = data['high'].values
            lows = data['low'].values
            x = np.arange(len(data))
            
            # Calculate expected channel boundaries
            upper_line = upper_slope * x + upper_intercept
            lower_line = lower_slope * x + lower_intercept
            
            # Count touches and respect of boundaries
            upper_touches = 0
            lower_touches = 0
            violations = 0
            
            for i in range(len(data)):
                # Check upper boundary
                if abs(highs[i] - upper_line[i]) / upper_line[i] < 0.005:  # Within 0.5%
                    upper_touches += 1
                elif highs[i] > upper_line[i] * 1.01:  # Significant break
                    violations += 1
                
                # Check lower boundary
                if abs(lows[i] - lower_line[i]) / lower_line[i] < 0.005:  # Within 0.5%
                    lower_touches += 1
                elif lows[i] < lower_line[i] * 0.99:  # Significant break
                    violations += 1
            
            total_touches = upper_touches + lower_touches
            quality = total_touches / (len(data) * 2)  # Normalize
            quality -= violations * 0.1  # Penalize violations
            
            return max(0, min(quality, 1.0))
            
        except:
            return 0.5
