
"""
Pattern Recognition Strategy for AuraTrade Bot
Detects chart patterns and candlestick formations
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import Logger

class PatternStrategy:
    """Advanced pattern recognition strategy"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Pattern"
        
        # Strategy parameters
        self.params = {
            'timeframe': 'M5',
            'min_confidence': 0.70,
            'max_positions': 2,
            'profit_target_pips': 25,
            'stop_loss_pips': 15,
            'pattern_lookback': 30,
            'min_pattern_strength': 60
        }
        
        # Pattern tracking
        self.detected_patterns = {}
        self.pattern_history = {}
        
        self.logger.info("Pattern recognition strategy initialized")
    
    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Optional[Dict[str, Any]]:
        """Main pattern analysis method"""
        try:
            if len(rates) < self.params['pattern_lookback']:
                return None
            
            # Detect candlestick patterns
            candle_patterns = self._detect_candlestick_patterns(rates)
            
            # Detect chart patterns
            chart_patterns = self._detect_chart_patterns(rates)
            
            # Combine pattern signals
            signal = self._combine_pattern_signals(candle_patterns, chart_patterns, symbol)
            
            if signal and signal.get('confidence', 0) >= self.params['min_confidence']:
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in pattern analysis for {symbol}: {e}")
            return None
    
    def _detect_candlestick_patterns(self, rates: pd.DataFrame) -> Dict[str, Any]:
        """Detect various candlestick patterns"""
        try:
            patterns = {
                'doji': self._detect_doji(rates),
                'hammer': self._detect_hammer(rates),
                'shooting_star': self._detect_shooting_star(rates),
                'engulfing': self._detect_engulfing(rates),
                'harami': self._detect_harami(rates),
                'morning_star': self._detect_morning_star(rates),
                'evening_star': self._detect_evening_star(rates),
                'spinning_top': self._detect_spinning_top(rates)
            }
            
            # Find strongest pattern
            strongest_pattern = None
            max_strength = 0
            
            for pattern_name, pattern_data in patterns.items():
                if pattern_data and pattern_data.get('strength', 0) > max_strength:
                    max_strength = pattern_data['strength']
                    strongest_pattern = pattern_data
                    strongest_pattern['name'] = pattern_name
            
            return strongest_pattern or {'strength': 0, 'signal': 'NEUTRAL'}
            
        except Exception as e:
            self.logger.error(f"Error detecting candlestick patterns: {e}")
            return {'strength': 0, 'signal': 'NEUTRAL'}
    
    def _detect_chart_patterns(self, rates: pd.DataFrame) -> Dict[str, Any]:
        """Detect chart patterns like triangles, head and shoulders, etc."""
        try:
            patterns = {
                'triangle': self._detect_triangle(rates),
                'head_shoulders': self._detect_head_shoulders(rates),
                'double_top': self._detect_double_top(rates),
                'double_bottom': self._detect_double_bottom(rates),
                'flag': self._detect_flag(rates),
                'wedge': self._detect_wedge(rates)
            }
            
            # Find strongest chart pattern
            strongest_pattern = None
            max_strength = 0
            
            for pattern_name, pattern_data in patterns.items():
                if pattern_data and pattern_data.get('strength', 0) > max_strength:
                    max_strength = pattern_data['strength']
                    strongest_pattern = pattern_data
                    strongest_pattern['name'] = pattern_name
            
            return strongest_pattern or {'strength': 0, 'signal': 'NEUTRAL'}
            
        except Exception as e:
            self.logger.error(f"Error detecting chart patterns: {e}")
            return {'strength': 0, 'signal': 'NEUTRAL'}
    
    def _detect_doji(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Doji candlestick pattern"""
        try:
            last_candle = rates.iloc[-1]
            
            open_price = last_candle['open']
            close_price = last_candle['close']
            high_price = last_candle['high']
            low_price = last_candle['low']
            
            body_size = abs(close_price - open_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            body_ratio = body_size / total_range
            
            # Doji: very small body relative to total range
            if body_ratio < 0.1:
                upper_shadow = high_price - max(open_price, close_price)
                lower_shadow = min(open_price, close_price) - low_price
                
                strength = 60 + (40 * (1 - body_ratio * 10))  # Higher strength for smaller body
                
                return {
                    'strength': min(strength, 100),
                    'signal': 'REVERSAL',
                    'type': 'doji',
                    'upper_shadow': upper_shadow,
                    'lower_shadow': lower_shadow
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Doji: {e}")
            return None
    
    def _detect_hammer(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Hammer candlestick pattern"""
        try:
            last_candle = rates.iloc[-1]
            
            open_price = last_candle['open']
            close_price = last_candle['close']
            high_price = last_candle['high']
            low_price = last_candle['low']
            
            body_size = abs(close_price - open_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            
            # Hammer: long lower shadow, small body, small upper shadow
            if (lower_shadow > body_size * 2 and 
                upper_shadow < body_size * 0.5 and
                body_size / total_range < 0.3):
                
                # Check if in downtrend (hammer is bullish reversal)
                prev_trend = self._check_previous_trend(rates, 'DOWN')
                
                if prev_trend:
                    strength = 70 + (20 * (lower_shadow / total_range))
                    
                    return {
                        'strength': min(strength, 95),
                        'signal': 'BUY',
                        'type': 'hammer',
                        'reversal': True
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Hammer: {e}")
            return None
    
    def _detect_shooting_star(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Shooting Star candlestick pattern"""
        try:
            last_candle = rates.iloc[-1]
            
            open_price = last_candle['open']
            close_price = last_candle['close']
            high_price = last_candle['high']
            low_price = last_candle['low']
            
            body_size = abs(close_price - open_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            upper_shadow = high_price - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low_price
            
            # Shooting Star: long upper shadow, small body, small lower shadow
            if (upper_shadow > body_size * 2 and 
                lower_shadow < body_size * 0.5 and
                body_size / total_range < 0.3):
                
                # Check if in uptrend (shooting star is bearish reversal)
                prev_trend = self._check_previous_trend(rates, 'UP')
                
                if prev_trend:
                    strength = 70 + (20 * (upper_shadow / total_range))
                    
                    return {
                        'strength': min(strength, 95),
                        'signal': 'SELL',
                        'type': 'shooting_star',
                        'reversal': True
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Shooting Star: {e}")
            return None
    
    def _detect_engulfing(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Bullish/Bearish Engulfing pattern"""
        try:
            if len(rates) < 2:
                return None
            
            prev_candle = rates.iloc[-2]
            curr_candle = rates.iloc[-1]
            
            prev_open = prev_candle['open']
            prev_close = prev_candle['close']
            curr_open = curr_candle['open']
            curr_close = curr_candle['close']
            
            prev_body = abs(prev_close - prev_open)
            curr_body = abs(curr_close - curr_open)
            
            # Bullish Engulfing
            if (prev_close < prev_open and  # Previous candle is bearish
                curr_close > curr_open and  # Current candle is bullish
                curr_open < prev_close and  # Current opens below prev close
                curr_close > prev_open and  # Current closes above prev open
                curr_body > prev_body):     # Current body is larger
                
                strength = 75 + (15 * (curr_body / prev_body - 1))
                
                return {
                    'strength': min(strength, 95),
                    'signal': 'BUY',
                    'type': 'bullish_engulfing',
                    'reversal': True
                }
            
            # Bearish Engulfing
            elif (prev_close > prev_open and  # Previous candle is bullish
                  curr_close < curr_open and  # Current candle is bearish
                  curr_open > prev_close and  # Current opens above prev close
                  curr_close < prev_open and  # Current closes below prev open
                  curr_body > prev_body):     # Current body is larger
                
                strength = 75 + (15 * (curr_body / prev_body - 1))
                
                return {
                    'strength': min(strength, 95),
                    'signal': 'SELL',
                    'type': 'bearish_engulfing',
                    'reversal': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Engulfing: {e}")
            return None
    
    def _detect_harami(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Harami pattern"""
        try:
            if len(rates) < 2:
                return None
            
            prev_candle = rates.iloc[-2]
            curr_candle = rates.iloc[-1]
            
            prev_open = prev_candle['open']
            prev_close = prev_candle['close']
            curr_open = curr_candle['open']
            curr_close = curr_candle['close']
            
            # Current candle body is inside previous candle body
            if (min(curr_open, curr_close) > min(prev_open, prev_close) and
                max(curr_open, curr_close) < max(prev_open, prev_close)):
                
                prev_body = abs(prev_close - prev_open)
                curr_body = abs(curr_close - curr_open)
                
                if curr_body < prev_body * 0.7:  # Significantly smaller body
                    
                    # Bullish Harami
                    if prev_close < prev_open and curr_close > curr_open:
                        return {
                            'strength': 65,
                            'signal': 'BUY',
                            'type': 'bullish_harami',
                            'reversal': True
                        }
                    
                    # Bearish Harami
                    elif prev_close > prev_open and curr_close < curr_open:
                        return {
                            'strength': 65,
                            'signal': 'SELL',
                            'type': 'bearish_harami',
                            'reversal': True
                        }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Harami: {e}")
            return None
    
    def _detect_morning_star(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Morning Star pattern (3-candle bullish reversal)"""
        try:
            if len(rates) < 3:
                return None
            
            candle1 = rates.iloc[-3]  # First candle
            candle2 = rates.iloc[-2]  # Star candle
            candle3 = rates.iloc[-1]  # Third candle
            
            # First candle: bearish
            if candle1['close'] >= candle1['open']:
                return None
            
            # Star candle: small body
            star_body = abs(candle2['close'] - candle2['open'])
            star_range = candle2['high'] - candle2['low']
            if star_range > 0 and star_body / star_range > 0.3:
                return None
            
            # Third candle: bullish and closes above midpoint of first candle
            if (candle3['close'] <= candle3['open'] or
                candle3['close'] <= (candle1['open'] + candle1['close']) / 2):
                return None
            
            return {
                'strength': 80,
                'signal': 'BUY',
                'type': 'morning_star',
                'reversal': True
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting Morning Star: {e}")
            return None
    
    def _detect_evening_star(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Evening Star pattern (3-candle bearish reversal)"""
        try:
            if len(rates) < 3:
                return None
            
            candle1 = rates.iloc[-3]  # First candle
            candle2 = rates.iloc[-2]  # Star candle
            candle3 = rates.iloc[-1]  # Third candle
            
            # First candle: bullish
            if candle1['close'] <= candle1['open']:
                return None
            
            # Star candle: small body
            star_body = abs(candle2['close'] - candle2['open'])
            star_range = candle2['high'] - candle2['low']
            if star_range > 0 and star_body / star_range > 0.3:
                return None
            
            # Third candle: bearish and closes below midpoint of first candle
            if (candle3['close'] >= candle3['open'] or
                candle3['close'] >= (candle1['open'] + candle1['close']) / 2):
                return None
            
            return {
                'strength': 80,
                'signal': 'SELL',
                'type': 'evening_star',
                'reversal': True
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting Evening Star: {e}")
            return None
    
    def _detect_spinning_top(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Spinning Top pattern"""
        try:
            last_candle = rates.iloc[-1]
            
            open_price = last_candle['open']
            close_price = last_candle['close']
            high_price = last_candle['high']
            low_price = last_candle['low']
            
            body_size = abs(close_price - open_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            upper_shadow = high_price - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low_price
            
            # Spinning top: small body with upper and lower shadows
            if (body_size / total_range < 0.2 and
                upper_shadow > body_size and
                lower_shadow > body_size):
                
                return {
                    'strength': 50,
                    'signal': 'NEUTRAL',
                    'type': 'spinning_top',
                    'indecision': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Spinning Top: {e}")
            return None
    
    def _detect_triangle(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Triangle pattern"""
        try:
            if len(rates) < 20:
                return None
            
            highs = rates['high'].tail(20)
            lows = rates['low'].tail(20)
            
            # Simple triangle detection based on converging trend lines
            high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
            low_trend = np.polyfit(range(len(lows)), lows, 1)[0]
            
            # Ascending triangle: horizontal resistance, rising support
            if abs(high_trend) < 0.0001 and low_trend > 0:
                return {
                    'strength': 70,
                    'signal': 'BUY',
                    'type': 'ascending_triangle',
                    'continuation': True
                }
            
            # Descending triangle: declining resistance, horizontal support
            elif high_trend < 0 and abs(low_trend) < 0.0001:
                return {
                    'strength': 70,
                    'signal': 'SELL',
                    'type': 'descending_triangle',
                    'continuation': True
                }
            
            # Symmetrical triangle: converging trend lines
            elif high_trend < 0 and low_trend > 0 and abs(high_trend - low_trend) > 0.0001:
                return {
                    'strength': 60,
                    'signal': 'BREAKOUT',
                    'type': 'symmetrical_triangle',
                    'neutral': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Triangle: {e}")
            return None
    
    def _detect_head_shoulders(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Head and Shoulders pattern"""
        try:
            if len(rates) < 30:
                return None
            
            highs = rates['high'].tail(30)
            
            # Find local maxima
            peaks = []
            for i in range(2, len(highs) - 2):
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and
                    highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
                    peaks.append((i, highs.iloc[i]))
            
            if len(peaks) >= 3:
                # Check if middle peak is highest (head)
                peaks.sort(key=lambda x: x[1], reverse=True)
                head = peaks[0]
                shoulders = peaks[1:3]
                
                # Shoulders should be roughly equal height and lower than head
                if (abs(shoulders[0][1] - shoulders[1][1]) / head[1] < 0.05 and
                    shoulders[0][1] < head[1] * 0.95):
                    
                    return {
                        'strength': 85,
                        'signal': 'SELL',
                        'type': 'head_shoulders',
                        'reversal': True
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Head and Shoulders: {e}")
            return None
    
    def _detect_double_top(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Double Top pattern"""
        try:
            if len(rates) < 20:
                return None
            
            highs = rates['high'].tail(20)
            
            # Find two roughly equal peaks
            max_high = highs.max()
            peak_threshold = max_high * 0.98
            
            peaks = []
            for i in range(2, len(highs) - 2):
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1] and
                    highs.iloc[i] >= peak_threshold):
                    peaks.append((i, highs.iloc[i]))
            
            if len(peaks) == 2:
                peak1, peak2 = peaks
                # Check if peaks are roughly equal
                if abs(peak1[1] - peak2[1]) / max(peak1[1], peak2[1]) < 0.02:
                    return {
                        'strength': 75,
                        'signal': 'SELL',
                        'type': 'double_top',
                        'reversal': True
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Double Top: {e}")
            return None
    
    def _detect_double_bottom(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Double Bottom pattern"""
        try:
            if len(rates) < 20:
                return None
            
            lows = rates['low'].tail(20)
            
            # Find two roughly equal lows
            min_low = lows.min()
            trough_threshold = min_low * 1.02
            
            troughs = []
            for i in range(2, len(lows) - 2):
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1] and
                    lows.iloc[i] <= trough_threshold):
                    troughs.append((i, lows.iloc[i]))
            
            if len(troughs) == 2:
                trough1, trough2 = troughs
                # Check if troughs are roughly equal
                if abs(trough1[1] - trough2[1]) / max(trough1[1], trough2[1]) < 0.02:
                    return {
                        'strength': 75,
                        'signal': 'BUY',
                        'type': 'double_bottom',
                        'reversal': True
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Double Bottom: {e}")
            return None
    
    def _detect_flag(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Flag pattern"""
        try:
            if len(rates) < 15:
                return None
            
            # Check for strong move followed by consolidation
            recent_closes = rates['close'].tail(15)
            
            # Strong initial move
            initial_move = (recent_closes.iloc[5] - recent_closes.iloc[0]) / recent_closes.iloc[0]
            
            # Consolidation phase
            consolidation = recent_closes.iloc[5:]
            volatility = consolidation.std() / consolidation.mean()
            
            if abs(initial_move) > 0.02 and volatility < 0.01:  # Strong move + low volatility
                if initial_move > 0:
                    return {
                        'strength': 65,
                        'signal': 'BUY',
                        'type': 'bull_flag',
                        'continuation': True
                    }
                else:
                    return {
                        'strength': 65,
                        'signal': 'SELL',
                        'type': 'bear_flag',
                        'continuation': True
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Flag: {e}")
            return None
    
    def _detect_wedge(self, rates: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect Wedge pattern"""
        try:
            if len(rates) < 20:
                return None
            
            highs = rates['high'].tail(20)
            lows = rates['low'].tail(20)
            
            # Calculate trend lines
            high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
            low_trend = np.polyfit(range(len(lows)), lows, 1)[0]
            
            # Rising wedge: both trend lines rising, but resistance rising slower
            if high_trend > 0 and low_trend > 0 and low_trend > high_trend:
                return {
                    'strength': 70,
                    'signal': 'SELL',
                    'type': 'rising_wedge',
                    'reversal': True
                }
            
            # Falling wedge: both trend lines falling, but support falling slower
            elif high_trend < 0 and low_trend < 0 and high_trend < low_trend:
                return {
                    'strength': 70,
                    'signal': 'BUY',
                    'type': 'falling_wedge',
                    'reversal': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Wedge: {e}")
            return None
    
    def _check_previous_trend(self, rates: pd.DataFrame, direction: str, periods: int = 10) -> bool:
        """Check if there was a previous trend in the specified direction"""
        try:
            if len(rates) < periods + 1:
                return False
            
            start_price = rates['close'].iloc[-(periods + 1)]
            end_price = rates['close'].iloc[-2]
            
            price_change = (end_price - start_price) / start_price
            
            if direction == 'UP':
                return price_change > 0.01  # 1% upward move
            elif direction == 'DOWN':
                return price_change < -0.01  # 1% downward move
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking previous trend: {e}")
            return False
    
    def _combine_pattern_signals(self, candle_pattern: Dict, chart_pattern: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """Combine candlestick and chart pattern signals"""
        try:
            combined_strength = 0
            signals = []
            final_signal = 'NEUTRAL'
            
            # Process candlestick pattern
            if candle_pattern and candle_pattern.get('strength', 0) > 40:
                combined_strength += candle_pattern['strength'] * 0.6
                if candle_pattern.get('signal') != 'NEUTRAL':
                    signals.append(candle_pattern['signal'])
            
            # Process chart pattern
            if chart_pattern and chart_pattern.get('strength', 0) > 40:
                combined_strength += chart_pattern['strength'] * 0.4
                if chart_pattern.get('signal') not in ['NEUTRAL', 'BREAKOUT']:
                    signals.append(chart_pattern['signal'])
            
            # Determine final signal
            if signals:
                buy_signals = signals.count('BUY')
                sell_signals = signals.count('SELL')
                
                if buy_signals > sell_signals:
                    final_signal = 'BUY'
                elif sell_signals > buy_signals:
                    final_signal = 'SELL'
                elif buy_signals == sell_signals == 1:
                    # Conflicting signals - use stronger pattern
                    candle_str = candle_pattern.get('strength', 0) if candle_pattern else 0
                    chart_str = chart_pattern.get('strength', 0) if chart_pattern else 0
                    
                    if candle_str > chart_str:
                        final_signal = candle_pattern.get('signal', 'NEUTRAL')
                    else:
                        final_signal = chart_pattern.get('signal', 'NEUTRAL')
            
            if final_signal != 'NEUTRAL' and combined_strength >= self.params['min_pattern_strength']:
                confidence = min(combined_strength / 100.0, 0.95)
                
                pattern_info = []
                if candle_pattern and candle_pattern.get('strength', 0) > 40:
                    pattern_info.append(candle_pattern.get('type', 'unknown'))
                if chart_pattern and chart_pattern.get('strength', 0) > 40:
                    pattern_info.append(chart_pattern.get('type', 'unknown'))
                
                return {
                    'action': final_signal,
                    'confidence': confidence,
                    'stop_loss_pips': self.params['stop_loss_pips'],
                    'take_profit_pips': self.params['profit_target_pips'],
                    'reasoning': f"Pattern recognition: {', '.join(pattern_info)}",
                    'strategy': self.name,
                    'patterns_detected': pattern_info,
                    'combined_strength': combined_strength
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error combining pattern signals: {e}")
            return None
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get pattern strategy information"""
        return {
            'name': self.name,
            'type': 'Pattern Recognition',
            'timeframe': self.params['timeframe'],
            'description': 'Advanced candlestick and chart pattern detection',
            'risk_level': 'Medium',
            'avg_trade_duration': '15-60 minutes',
            'profit_target': f"{self.params['profit_target_pips']} pips",
            'stop_loss': f"{self.params['stop_loss_pips']} pips",
            'patterns_supported': [
                'Doji', 'Hammer', 'Shooting Star', 'Engulfing', 'Harami',
                'Morning Star', 'Evening Star', 'Triangle', 'Head & Shoulders',
                'Double Top/Bottom', 'Flag', 'Wedge'
            ]
        }
