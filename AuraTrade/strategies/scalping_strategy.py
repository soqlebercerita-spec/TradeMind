
"""
Scalping Strategy for AuraTrade Bot
Fast profit scalping with quick entry/exit
"""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from utils.logger import Logger

class ScalpingStrategy:
    """Advanced scalping strategy with fast and slow signal combination"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Scalping"
        
        # Strategy parameters
        self.params = {
            'timeframe': 'M1',  # 1-minute scalping
            'min_confidence': 0.65,  # Higher confidence for scalping
            'max_positions': 3,
            'profit_target_pips': 8,  # Quick profit target
            'stop_loss_pips': 12,     # Tight stop loss
            'max_holding_time': 5,    # Max 5 minutes
            'spread_limit': 2.0,      # Max spread in pips
        }
        
        # Signal tracking
        self.last_signals = {}
        self.active_positions = {}
        
        self.logger.info("Scalping strategy initialized for fast profits")
    
    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Optional[Dict[str, Any]]:
        """Main analysis method combining fast and slow signals"""
        try:
            if len(rates) < 50:
                return None
            
            # Check spread
            if self._check_spread(tick):
                return None
            
            # Get fast signals (immediate indicators)
            fast_signals = self._get_fast_signals(rates, tick)
            
            # Get slow signals (trend confirmation)
            slow_signals = self._get_slow_signals(rates)
            
            # Combine signals for decision
            signal = self._combine_signals(fast_signals, slow_signals, symbol)
            
            if signal and signal.get('confidence', 0) >= self.params['min_confidence']:
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in scalping analysis for {symbol}: {e}")
            return None
    
    def _get_fast_signals(self, rates: pd.DataFrame, tick: Dict) -> Dict[str, Any]:
        """Fast signals: Price Action, MA10, candle momentum"""
        try:
            current_price = tick['bid']
            
            # Moving Average 10
            ma10 = rates['close'].rolling(window=10).mean().iloc[-1]
            
            # Price momentum (last 3 candles)
            momentum = self._calculate_momentum(rates)
            
            # Candle pattern analysis
            candle_signal = self._analyze_candle_pattern(rates)
            
            # Price action relative to MA10
            price_action = "BULLISH" if current_price > ma10 else "BEARISH"
            
            # Combine fast signals
            fast_score = 0
            
            if price_action == "BULLISH":
                fast_score += 30
            elif price_action == "BEARISH":
                fast_score += 30
            
            if momentum == "STRONG":
                fast_score += 25
            elif momentum == "MODERATE":
                fast_score += 15
            
            if candle_signal != "NEUTRAL":
                fast_score += 20
            
            return {
                'direction': price_action,
                'strength': fast_score,
                'momentum': momentum,
                'candle_signal': candle_signal,
                'ma10': ma10
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating fast signals: {e}")
            return {'direction': 'NEUTRAL', 'strength': 0}
    
    def _get_slow_signals(self, rates: pd.DataFrame) -> Dict[str, Any]:
        """Slow signals: EMA50, RSI for trend validation"""
        try:
            # EMA50 for trend direction
            ema50 = rates['close'].ewm(span=50).mean().iloc[-1]
            current_price = rates['close'].iloc[-1]
            
            # RSI for overbought/oversold
            rsi = self._calculate_rsi(rates)
            
            # Trend validation
            trend = "BULLISH" if current_price > ema50 else "BEARISH"
            
            # RSI conditions
            rsi_signal = "NEUTRAL"
            if rsi > 70:
                rsi_signal = "OVERBOUGHT"
            elif rsi < 30:
                rsi_signal = "OVERSOLD"
            elif 45 < rsi < 55:
                rsi_signal = "NEUTRAL_ZONE"
            
            # Calculate slow signal strength
            slow_score = 0
            
            # Trend strength
            trend_strength = abs(current_price - ema50) / ema50 * 100
            if trend_strength > 0.1:  # Strong trend
                slow_score += 25
            elif trend_strength > 0.05:  # Moderate trend
                slow_score += 15
            
            # RSI confirmation
            if rsi_signal in ["OVERSOLD", "OVERBOUGHT"]:
                slow_score += 20
            elif rsi_signal == "NEUTRAL_ZONE":
                slow_score -= 10  # Reduce confidence in neutral zone
            
            return {
                'trend': trend,
                'strength': slow_score,
                'rsi': rsi,
                'rsi_signal': rsi_signal,
                'ema50': ema50,
                'trend_strength': trend_strength
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating slow signals: {e}")
            return {'trend': 'NEUTRAL', 'strength': 0}
    
    def _combine_signals(self, fast_signals: Dict, slow_signals: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """Combine fast and slow signals for final decision"""
        try:
            # Don't wait for all indicators to agree - use sufficient combination
            fast_direction = fast_signals.get('direction', 'NEUTRAL')
            slow_trend = slow_signals.get('trend', 'NEUTRAL')
            
            fast_strength = fast_signals.get('strength', 0)
            slow_strength = slow_signals.get('strength', 0)
            
            # Decision logic: Fast signals + trend confirmation
            signal = None
            confidence = 0
            
            # Case 1: Fast and slow signals agree
            if fast_direction == slow_trend and fast_direction != 'NEUTRAL':
                confidence = (fast_strength + slow_strength) / 100
                action = 'BUY' if fast_direction == 'BULLISH' else 'SELL'
                
                signal = {
                    'action': action,
                    'confidence': confidence,
                    'stop_loss_pips': self.params['stop_loss_pips'],
                    'take_profit_pips': self.params['profit_target_pips'],
                    'reasoning': f"Fast and slow signals agree: {fast_direction}",
                    'strategy': self.name
                }
            
            # Case 2: Fast signals strong enough even without full slow confirmation
            elif fast_strength >= 60:  # Strong fast signal
                # Check if slow signals don't strongly oppose
                rsi = slow_signals.get('rsi', 50)
                
                if fast_direction == 'BULLISH' and rsi < 75:  # Not too overbought
                    confidence = fast_strength / 120  # Slightly reduced confidence
                    signal = {
                        'action': 'BUY',
                        'confidence': confidence,
                        'stop_loss_pips': self.params['stop_loss_pips'] + 3,  # Wider SL
                        'take_profit_pips': self.params['profit_target_pips'] - 2,  # Tighter TP
                        'reasoning': "Strong fast signals with acceptable trend",
                        'strategy': self.name
                    }
                
                elif fast_direction == 'BEARISH' and rsi > 25:  # Not too oversold
                    confidence = fast_strength / 120
                    signal = {
                        'action': 'SELL',
                        'confidence': confidence,
                        'stop_loss_pips': self.params['stop_loss_pips'] + 3,
                        'take_profit_pips': self.params['profit_target_pips'] - 2,
                        'reasoning': "Strong fast signals with acceptable trend",
                        'strategy': self.name
                    }
            
            # Apply additional filters
            if signal:
                signal = self._apply_additional_filters(signal, fast_signals, slow_signals)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error combining signals: {e}")
            return None
    
    def _apply_additional_filters(self, signal: Dict, fast_signals: Dict, slow_signals: Dict) -> Optional[Dict]:
        """Apply additional filters to reduce false signals"""
        try:
            # Filter 1: Avoid trading in extreme RSI conditions opposite to signal
            rsi = slow_signals.get('rsi', 50)
            action = signal['action']
            
            if action == 'BUY' and rsi > 80:  # Very overbought
                return None
            elif action == 'SELL' and rsi < 20:  # Very oversold
                return None
            
            # Filter 2: Check momentum strength
            momentum = fast_signals.get('momentum', 'WEAK')
            if momentum == 'WEAK':
                signal['confidence'] *= 0.8  # Reduce confidence
            
            # Filter 3: Time-based filter (avoid trading at certain times)
            current_time = datetime.now()
            hour = current_time.hour
            
            # Avoid low volatility hours (example)
            if hour in [0, 1, 2, 22, 23]:
                signal['confidence'] *= 0.7
            
            # Filter 4: Minimum confidence check after filters
            if signal['confidence'] < self.params['min_confidence']:
                return None
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            return signal
    
    def _calculate_momentum(self, rates: pd.DataFrame, period: int = 3) -> str:
        """Calculate price momentum strength"""
        try:
            recent_closes = rates['close'].tail(period + 1)
            
            if len(recent_closes) < period + 1:
                return "WEAK"
            
            changes = recent_closes.diff().dropna()
            
            # Check for consistent direction
            positive_moves = (changes > 0).sum()
            negative_moves = (changes < 0).sum()
            
            avg_change = abs(changes.mean())
            price_range = rates['high'].tail(period).max() - rates['low'].tail(period).min()
            
            if price_range > 0:
                momentum_strength = avg_change / price_range
                
                if (positive_moves >= period * 0.7 or negative_moves >= period * 0.7) and momentum_strength > 0.3:
                    return "STRONG"
                elif momentum_strength > 0.1:
                    return "MODERATE"
            
            return "WEAK"
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum: {e}")
            return "WEAK"
    
    def _analyze_candle_pattern(self, rates: pd.DataFrame) -> str:
        """Analyze last candle pattern"""
        try:
            if len(rates) < 2:
                return "NEUTRAL"
            
            last_candle = rates.iloc[-1]
            prev_candle = rates.iloc[-2]
            
            # Basic candle analysis
            body_size = abs(last_candle['close'] - last_candle['open'])
            candle_range = last_candle['high'] - last_candle['low']
            
            if candle_range == 0:
                return "NEUTRAL"
            
            body_ratio = body_size / candle_range
            
            # Strong directional candle
            if body_ratio > 0.7:
                if last_candle['close'] > last_candle['open']:
                    return "BULLISH"
                else:
                    return "BEARISH"
            
            # Doji or indecision
            elif body_ratio < 0.1:
                return "INDECISION"
            
            return "NEUTRAL"
            
        except Exception as e:
            self.logger.error(f"Error analyzing candle pattern: {e}")
            return "NEUTRAL"
    
    def _calculate_rsi(self, rates: pd.DataFrame, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            delta = rates['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0
    
    def _check_spread(self, tick: Dict) -> bool:
        """Check if spread is too wide for scalping"""
        try:
            spread = tick.get('ask', 0) - tick.get('bid', 0)
            symbol = tick.get('symbol', '')
            
            # Convert spread to pips
            if 'JPY' in symbol:
                spread_pips = spread * 100
            else:
                spread_pips = spread * 10000
            
            return spread_pips > self.params['spread_limit']
            
        except:
            return False
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Scalping',
            'timeframe': self.params['timeframe'],
            'description': 'Fast profit scalping with MA10 + EMA50 + RSI combination',
            'risk_level': 'Medium-High',
            'avg_trade_duration': '1-5 minutes',
            'profit_target': f"{self.params['profit_target_pips']} pips",
            'stop_loss': f"{self.params['stop_loss_pips']} pips"
        }
"""
Scalping Strategy for AuraTrade Bot
High-frequency short-term trading strategy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import Logger

class ScalpingStrategy:
    """High-frequency scalping strategy"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Scalping"
        self.timeframe = "M1"
        self.min_spread = 0.5  # Max spread in pips
        self.max_spread = 3.0
        
        # Strategy parameters
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.ma_fast = 5
        self.ma_slow = 20
        
        # Risk parameters
        self.tp_pips = 8
        self.sl_pips = 12
        self.max_positions = 3
        
        self.logger.info("Scalping Strategy initialized")
    
    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Optional[Dict]:
        """Analyze market and generate signals"""
        try:
            if len(rates) < 50:
                return None
            
            # Calculate indicators
            indicators = self._calculate_indicators(rates)
            
            # Check spread
            spread = self._calculate_spread(tick, symbol)
            if spread > self.max_spread:
                return None
            
            # Generate signals
            signals = self._generate_signals(rates, indicators, tick)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error in scalping analysis: {e}")
            return None
    
    def _calculate_indicators(self, rates: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        try:
            close = rates['close']
            high = rates['high']
            low = rates['low']
            
            # RSI
            rsi = self._calculate_rsi(close, self.rsi_period)
            
            # Moving averages
            ma_fast = close.rolling(window=self.ma_fast).mean()
            ma_slow = close.rolling(window=self.ma_slow).mean()
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            bb_middle = close.rolling(window=bb_period).mean()
            bb_std_val = close.rolling(window=bb_period).std()
            bb_upper = bb_middle + (bb_std_val * bb_std)
            bb_lower = bb_middle - (bb_std_val * bb_std)
            
            # MACD
            ema_12 = close.ewm(span=12).mean()
            ema_26 = close.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            macd_histogram = macd_line - signal_line
            
            return {
                'rsi': rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50,
                'ma_fast': ma_fast.iloc[-1],
                'ma_slow': ma_slow.iloc[-1],
                'bb_upper': bb_upper.iloc[-1],
                'bb_lower': bb_lower.iloc[-1],
                'bb_middle': bb_middle.iloc[-1],
                'macd_line': macd_line.iloc[-1],
                'signal_line': signal_line.iloc[-1],
                'macd_histogram': macd_histogram.iloc[-1]
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_spread(self, tick: Dict, symbol: str) -> float:
        """Calculate spread in pips"""
        try:
            spread = tick['ask'] - tick['bid']
            # Convert to pips (assuming 5-digit quotes for most pairs)
            if 'JPY' in symbol:
                return spread * 100  # 3-digit quotes
            else:
                return spread * 10000  # 5-digit quotes
        except:
            return 999  # High value to block trading
    
    def _generate_signals(self, rates: pd.DataFrame, indicators: Dict, tick: Dict) -> Optional[Dict]:
        """Generate trading signals"""
        try:
            current_price = rates['close'].iloc[-1]
            rsi = indicators.get('rsi', 50)
            ma_fast = indicators.get('ma_fast', current_price)
            ma_slow = indicators.get('ma_slow', current_price)
            bb_upper = indicators.get('bb_upper', current_price)
            bb_lower = indicators.get('bb_lower', current_price)
            macd_histogram = indicators.get('macd_histogram', 0)
            
            # Signal conditions
            signals = []
            
            # RSI + MA Crossover (BUY)
            if (rsi < self.rsi_oversold and 
                ma_fast > ma_slow and 
                current_price <= bb_lower and
                macd_histogram > 0):
                
                signals.append({
                    'action': 'buy',
                    'confidence': 0.75,
                    'tp_pips': self.tp_pips,
                    'sl_pips': self.sl_pips,
                    'volume': 0.01,
                    'reason': 'RSI Oversold + MA Bullish + BB Lower + MACD Positive'
                })
            
            # RSI + MA Crossover (SELL)
            elif (rsi > self.rsi_overbought and 
                  ma_fast < ma_slow and 
                  current_price >= bb_upper and
                  macd_histogram < 0):
                
                signals.append({
                    'action': 'sell',
                    'confidence': 0.75,
                    'tp_pips': self.tp_pips,
                    'sl_pips': self.sl_pips,
                    'volume': 0.01,
                    'reason': 'RSI Overbought + MA Bearish + BB Upper + MACD Negative'
                })
            
            # Quick scalp on strong momentum
            if len(rates) >= 5:
                recent_closes = rates['close'].tail(5)
                if recent_closes.is_monotonic_increasing and macd_histogram > 0.0001:
                    signals.append({
                        'action': 'buy',
                        'confidence': 0.65,
                        'tp_pips': 5,  # Quick profit
                        'sl_pips': 8,
                        'volume': 0.01,
                        'reason': 'Strong Upward Momentum'
                    })
                elif recent_closes.is_monotonic_decreasing and macd_histogram < -0.0001:
                    signals.append({
                        'action': 'sell',
                        'confidence': 0.65,
                        'tp_pips': 5,  # Quick profit
                        'sl_pips': 8,
                        'volume': 0.01,
                        'reason': 'Strong Downward Momentum'
                    })
            
            # Return best signal
            if signals:
                return max(signals, key=lambda x: x['confidence'])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return None
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'timeframe': self.timeframe,
            'tp_pips': self.tp_pips,
            'sl_pips': self.sl_pips,
            'max_spread': self.max_spread,
            'risk_level': 'High',
            'description': 'High-frequency scalping with RSI, MA, and Bollinger Bands'
        }
