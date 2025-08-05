
"""
Swing Trading Strategy for AuraTrade Bot
Medium-term position trading based on trend analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from analysis.technical_analysis import TechnicalAnalysis
from utils.logger import Logger

class SwingStrategy:
    """Swing trading strategy with trend following"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.technical_analysis = TechnicalAnalysis()
        
        # Strategy parameters
        self.name = "Swing Strategy"
        self.timeframe = 'H4'
        self.min_trend_strength = 0.6
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.macd_signal_threshold = 0.001
        
        self.logger.info("SwingStrategy initialized")

    def generate_signal(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Generate swing trading signal"""
        try:
            # Use H4 data for swing analysis
            if 'H4' not in data or data['H4'].empty:
                return {'action': 'HOLD', 'confidence': 0, 'reason': 'No H4 data'}
            
            df = data['H4'].copy()
            
            if len(df) < 50:  # Need enough data for swing analysis
                return {'action': 'HOLD', 'confidence': 0, 'reason': 'Insufficient data'}
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Analyze trend
            trend_analysis = self._analyze_trend(df, indicators)
            
            # Generate signal
            signal = self._evaluate_signal(df, indicators, trend_analysis)
            
            if signal and signal['action'] != 'HOLD':
                self.logger.info(f"Swing signal: {symbol} {signal['action']} (confidence: {signal['confidence']:.2f})")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating swing signal for {symbol}: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reason': f'Error: {str(e)}'}

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators for swing analysis"""
        try:
            indicators = {}
            
            # Moving averages
            indicators['ema_20'] = self.technical_analysis.calculate_ema(df['close'], 20)
            indicators['ema_50'] = self.technical_analysis.calculate_ema(df['close'], 50)
            indicators['sma_200'] = self.technical_analysis.calculate_sma(df['close'], 200)
            
            # RSI
            indicators['rsi'] = self.technical_analysis.calculate_rsi(df['close'], 14)
            
            # MACD
            macd_data = self.technical_analysis.calculate_macd(df['close'])
            indicators['macd'] = macd_data['macd']
            indicators['macd_signal'] = macd_data['signal']
            indicators['macd_histogram'] = macd_data['histogram']
            
            # Bollinger Bands
            bb_data = self.technical_analysis.calculate_bollinger_bands(df['close'], 20, 2)
            indicators['bb_upper'] = bb_data['upper']
            indicators['bb_middle'] = bb_data['middle']
            indicators['bb_lower'] = bb_data['lower']
            
            # ATR for volatility
            indicators['atr'] = self.technical_analysis.calculate_atr(df['high'], df['low'], df['close'], 14)
            
            # Support and Resistance
            indicators['support'] = self._find_support_resistance(df, 'support')
            indicators['resistance'] = self._find_support_resistance(df, 'resistance')
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating swing indicators: {e}")
            return {}

    def _analyze_trend(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """Analyze market trend for swing trading"""
        try:
            current_price = df['close'].iloc[-1]
            
            # EMA trend analysis
            ema_20 = indicators['ema_20'].iloc[-1] if not indicators['ema_20'].empty else 0
            ema_50 = indicators['ema_50'].iloc[-1] if not indicators['ema_50'].empty else 0
            sma_200 = indicators['sma_200'].iloc[-1] if not indicators['sma_200'].empty else 0
            
            # Trend direction
            short_trend = 'up' if ema_20 > ema_50 else 'down'
            long_trend = 'up' if current_price > sma_200 else 'down'
            
            # Trend strength calculation
            if ema_20 > 0 and ema_50 > 0:
                trend_strength = abs(ema_20 - ema_50) / ema_50
            else:
                trend_strength = 0
            
            # Price position relative to EMAs
            price_above_ema20 = current_price > ema_20
            price_above_ema50 = current_price > ema_50
            price_above_sma200 = current_price > sma_200
            
            return {
                'short_trend': short_trend,
                'long_trend': long_trend,
                'trend_strength': trend_strength,
                'price_above_ema20': price_above_ema20,
                'price_above_ema50': price_above_ema50,
                'price_above_sma200': price_above_sma200,
                'trend_aligned': short_trend == long_trend
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend: {e}")
            return {}

    def _evaluate_signal(self, df: pd.DataFrame, indicators: Dict, trend_analysis: Dict) -> Dict[str, Any]:
        """Evaluate swing trading signal"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Get latest indicator values
            rsi = indicators['rsi'].iloc[-1] if not indicators['rsi'].empty else 50
            macd = indicators['macd'].iloc[-1] if not indicators['macd'].empty else 0
            macd_signal = indicators['macd_signal'].iloc[-1] if not indicators['macd_signal'].empty else 0
            macd_histogram = indicators['macd_histogram'].iloc[-1] if not indicators['macd_histogram'].empty else 0
            
            bb_upper = indicators['bb_upper'].iloc[-1] if not indicators['bb_upper'].empty else current_price
            bb_lower = indicators['bb_lower'].iloc[-1] if not indicators['bb_lower'].empty else current_price
            
            # Initialize signal
            signal = {'action': 'HOLD', 'confidence': 0, 'reason': 'No clear signal'}
            
            # Check trend strength
            trend_strength = trend_analysis.get('trend_strength', 0)
            if trend_strength < self.min_trend_strength:
                return signal
            
            # Long signal conditions
            long_conditions = [
                trend_analysis.get('short_trend') == 'up',  # Short trend up
                trend_analysis.get('long_trend') == 'up',   # Long trend up
                rsi < 70,  # Not overbought
                macd > macd_signal,  # MACD bullish
                macd_histogram > 0,  # MACD histogram positive
                current_price > bb_lower,  # Above BB lower
                trend_analysis.get('price_above_ema20', False)  # Above EMA20
            ]
            
            # Short signal conditions
            short_conditions = [
                trend_analysis.get('short_trend') == 'down',  # Short trend down
                trend_analysis.get('long_trend') == 'down',   # Long trend down
                rsi > 30,  # Not oversold
                macd < macd_signal,  # MACD bearish
                macd_histogram < 0,  # MACD histogram negative
                current_price < bb_upper,  # Below BB upper
                not trend_analysis.get('price_above_ema20', True)  # Below EMA20
            ]
            
            # Calculate confidence
            long_score = sum(long_conditions) / len(long_conditions)
            short_score = sum(short_conditions) / len(short_conditions)
            
            # Determine signal
            if long_score >= 0.7 and long_score > short_score:
                signal = {
                    'action': 'BUY',
                    'confidence': long_score,
                    'entry_price': current_price,
                    'reason': f'Swing long signal (score: {long_score:.2f})',
                    'timeframe': self.timeframe,
                    'strategy': self.name
                }
            elif short_score >= 0.7 and short_score > long_score:
                signal = {
                    'action': 'SELL',
                    'confidence': short_score,
                    'entry_price': current_price,
                    'reason': f'Swing short signal (score: {short_score:.2f})',
                    'timeframe': self.timeframe,
                    'strategy': self.name
                }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error evaluating swing signal: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reason': f'Evaluation error: {str(e)}'}

    def _find_support_resistance(self, df: pd.DataFrame, level_type: str) -> float:
        """Find support/resistance levels"""
        try:
            if len(df) < 20:
                return 0.0
            
            # Use recent 20 candles for swing points
            recent_df = df.tail(20)
            
            if level_type == 'support':
                # Find lowest low in recent data
                return recent_df['low'].min()
            else:  # resistance
                # Find highest high in recent data
                return recent_df['high'].max()
                
        except Exception as e:
            self.logger.error(f"Error finding {level_type}: {e}")
            return 0.0

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Swing Trading',
            'timeframe': self.timeframe,
            'risk_level': 'Medium',
            'hold_duration': '1-7 days',
            'description': 'Medium-term trend following strategy using H4 timeframe'
        }
