
"""
Pattern Recognition Strategy for AuraTrade Bot
Identifies candlestick patterns and chart patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from utils.logger import Logger

class PatternStrategy:
    """Pattern recognition strategy implementation"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Pattern_Strategy"
        self.enabled = True
        
        # Pattern parameters
        self.min_body_ratio = 0.6
        self.doji_threshold = 0.1
        self.hammer_ratio = 2.0
        
    def analyze_signal(self, symbol: str, data: pd.DataFrame, 
                      current_price: tuple, market_condition: Dict) -> Optional[Dict[str, Any]]:
        """Analyze pattern signals"""
        try:
            if not self.enabled or len(data) < 10:
                return None
            
            # Get recent candles
            recent_candles = data.tail(5)
            
            # Detect patterns
            patterns = self._detect_patterns(recent_candles)
            
            if not patterns:
                return None
            
            # Evaluate strongest pattern
            strongest_pattern = max(patterns, key=lambda x: x['strength'])
            
            if strongest_pattern['strength'] > 70:
                bid, ask = current_price
                
                return {
                    'strategy': self.name,
                    'signal': strongest_pattern['signal'],
                    'confidence': strongest_pattern['strength'],
                    'entry_price': ask if strongest_pattern['signal'] == 'buy' else bid,
                    'stop_loss_pips': 4.0,
                    'take_profit_pips': 6.0,
                    'risk_percent': 1.5,
                    'timeframe': 'M15',
                    'reason': f"Pattern: {strongest_pattern['name']}"
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in pattern strategy analysis: {e}")
            return None
    
    def _detect_patterns(self, candles: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect candlestick patterns"""
        patterns = []
        
        try:
            if len(candles) < 3:
                return patterns
            
            # Get last few candles
            c1, c2, c3 = candles.iloc[-3], candles.iloc[-2], candles.iloc[-1]
            
            # Hammer pattern
            hammer = self._detect_hammer(c3)
            if hammer:
                patterns.append(hammer)
            
            # Doji pattern
            doji = self._detect_doji(c3)
            if doji:
                patterns.append(doji)
            
            # Engulfing pattern
            engulfing = self._detect_engulfing(c2, c3)
            if engulfing:
                patterns.append(engulfing)
            
            # Morning/Evening star
            star = self._detect_star_pattern(c1, c2, c3)
            if star:
                patterns.append(star)
            
            # Pin bar
            pin_bar = self._detect_pin_bar(c3)
            if pin_bar:
                patterns.append(pin_bar)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
            return []
    
    def _detect_hammer(self, candle: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect hammer/hanging man pattern"""
        try:
            body = abs(candle['close'] - candle['open'])
            lower_shadow = candle['open'] - candle['low'] if candle['close'] > candle['open'] else candle['close'] - candle['low']
            upper_shadow = candle['high'] - candle['close'] if candle['close'] > candle['open'] else candle['high'] - candle['open']
            
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return None
            
            # Hammer criteria
            if (lower_shadow > body * 2 and 
                upper_shadow < body * 0.5 and 
                body / total_range > 0.1):
                
                signal = 'buy' if candle['close'] > candle['open'] else 'sell'
                strength = 75 if candle['close'] > candle['open'] else 65
                
                return {
                    'name': 'Hammer',
                    'signal': signal,
                    'strength': strength
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting hammer: {e}")
            return None
    
    def _detect_doji(self, candle: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect doji pattern"""
        try:
            body = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return None
            
            # Doji criteria
            if body / total_range < self.doji_threshold:
                return {
                    'name': 'Doji',
                    'signal': 'neutral',
                    'strength': 60
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting doji: {e}")
            return None
    
    def _detect_engulfing(self, prev_candle: pd.Series, current_candle: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect bullish/bearish engulfing pattern"""
        try:
            # Bullish engulfing
            if (prev_candle['close'] < prev_candle['open'] and  # Previous bearish
                current_candle['close'] > current_candle['open'] and  # Current bullish
                current_candle['open'] < prev_candle['close'] and  # Opens below prev close
                current_candle['close'] > prev_candle['open']):  # Closes above prev open
                
                return {
                    'name': 'Bullish Engulfing',
                    'signal': 'buy',
                    'strength': 80
                }
            
            # Bearish engulfing
            elif (prev_candle['close'] > prev_candle['open'] and  # Previous bullish
                  current_candle['close'] < current_candle['open'] and  # Current bearish
                  current_candle['open'] > prev_candle['close'] and  # Opens above prev close
                  current_candle['close'] < prev_candle['open']):  # Closes below prev open
                
                return {
                    'name': 'Bearish Engulfing',
                    'signal': 'sell',
                    'strength': 80
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting engulfing: {e}")
            return None
    
    def _detect_star_pattern(self, c1: pd.Series, c2: pd.Series, c3: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect morning/evening star pattern"""
        try:
            # Morning star
            if (c1['close'] < c1['open'] and  # First candle bearish
                abs(c2['close'] - c2['open']) < (c1['high'] - c1['low']) * 0.3 and  # Second candle small
                c3['close'] > c3['open'] and  # Third candle bullish
                c3['close'] > (c1['open'] + c1['close']) / 2):  # Third closes above midpoint of first
                
                return {
                    'name': 'Morning Star',
                    'signal': 'buy',
                    'strength': 85
                }
            
            # Evening star
            elif (c1['close'] > c1['open'] and  # First candle bullish
                  abs(c2['close'] - c2['open']) < (c1['high'] - c1['low']) * 0.3 and  # Second candle small
                  c3['close'] < c3['open'] and  # Third candle bearish
                  c3['close'] < (c1['open'] + c1['close']) / 2):  # Third closes below midpoint of first
                
                return {
                    'name': 'Evening Star',
                    'signal': 'sell',
                    'strength': 85
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting star pattern: {e}")
            return None
    
    def _detect_pin_bar(self, candle: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect pin bar pattern"""
        try:
            body = abs(candle['close'] - candle['open'])
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return None
            
            # Bullish pin bar (hammer-like)
            if lower_shadow > body * 3 and upper_shadow < body:
                return {
                    'name': 'Bullish Pin Bar',
                    'signal': 'buy',
                    'strength': 75
                }
            
            # Bearish pin bar (shooting star-like)
            elif upper_shadow > body * 3 and lower_shadow < body:
                return {
                    'name': 'Bearish Pin Bar',
                    'signal': 'sell',
                    'strength': 75
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting pin bar: {e}")
            return None
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'type': 'Pattern Recognition',
            'timeframe': 'M15',
            'parameters': {
                'min_body_ratio': self.min_body_ratio,
                'doji_threshold': self.doji_threshold,
                'hammer_ratio': self.hammer_ratio
            }
        }
