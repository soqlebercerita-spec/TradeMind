
"""
Swing Trading Strategy for AuraTrade Bot
Medium-term trend following strategy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.logger import Logger

class SwingStrategy:
    """Swing trading strategy for medium-term trends"""
    
    def __init__(self, params: Dict = None):
        self.name = "Swing"
        self.logger = Logger().get_logger()
        
        # Default parameters
        self.params = {
            'timeframe': 'H4',
            'ma_fast': 20,
            'ma_slow': 50,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'atr_period': 14,
            'atr_multiplier': 2.0,
            'volume': 0.1,
            'stop_loss_atr': 2.0,
            'take_profit_ratio': 2.0,  # Risk:Reward 1:2
            'min_trend_strength': 0.6,
            'max_positions': 3
        }
        
        if params:
            self.params.update(params)
            
        self.trend_direction = 'NEUTRAL'
        self.last_signals = []
        
        self.logger.info(f"Swing strategy initialized with params: {self.params}")
    
    def analyze_market(self, rates: pd.DataFrame, tick: Dict = None) -> Dict[str, any]:
        """Analyze market for swing trading opportunities"""
        try:
            if len(rates) < max(self.params['ma_slow'], self.params['rsi_period'], self.params['atr_period']) + 10:
                return {'signals': [], 'analysis': {}}
            
            # Calculate indicators
            analysis = self._calculate_indicators(rates)
            
            # Determine trend
            trend = self._identify_trend(analysis, rates)
            
            # Generate signals
            signals = self._generate_signals(analysis, trend, rates)
            
            # Risk assessment
            risk_assessment = self._assess_risk(analysis, rates)
            
            return {
                'signals': signals,
                'analysis': analysis,
                'trend': trend,
                'risk_assessment': risk_assessment,
                'strategy': self.name,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in swing market analysis: {e}")
            return {'signals': [], 'analysis': {}}
    
    def _calculate_indicators(self, rates: pd.DataFrame) -> Dict[str, any]:
        """Calculate technical indicators for swing trading"""
        try:
            analysis = {}
            
            # Moving Averages
            analysis['ma_fast'] = rates['close'].rolling(window=self.params['ma_fast']).mean()
            analysis['ma_slow'] = rates['close'].rolling(window=self.params['ma_slow']).mean()
            
            # RSI
            analysis['rsi'] = self._calculate_rsi(rates, self.params['rsi_period'])
            
            # ATR for volatility
            analysis['atr'] = self._calculate_atr(rates, self.params['atr_period'])
            
            # MACD
            macd_data = self._calculate_macd(rates)
            analysis.update(macd_data)
            
            # Bollinger Bands
            bb_data = self._calculate_bollinger_bands(rates)
            analysis.update(bb_data)
            
            # Support and Resistance
            sr_data = self._calculate_support_resistance(rates)
            analysis.update(sr_data)
            
            # Trend strength
            analysis['trend_strength'] = self._calculate_trend_strength(rates)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_rsi(self, rates: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = rates['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(rates), index=rates.index)
    
    def _calculate_atr(self, rates: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high_low = rates['high'] - rates['low']
            high_close = np.abs(rates['high'] - rates['close'].shift())
            low_close = np.abs(rates['low'] - rates['close'].shift())
            
            tr = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = tr.rolling(window=period).mean()
            return atr
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return pd.Series([0.001] * len(rates), index=rates.index)
    
    def _calculate_macd(self, rates: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD"""
        try:
            exp1 = rates['close'].ewm(span=fast).mean()
            exp2 = rates['close'].ewm(span=slow).mean()
            
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd_line': macd_line,
                'macd_signal': signal_line,
                'macd_histogram': histogram
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return {'macd_line': pd.Series([0] * len(rates)), 'macd_signal': pd.Series([0] * len(rates)), 'macd_histogram': pd.Series([0] * len(rates))}
    
    def _calculate_bollinger_bands(self, rates: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict:
        """Calculate Bollinger Bands"""
        try:
            sma = rates['close'].rolling(window=period).mean()
            std = rates['close'].rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return {
                'bb_upper': upper_band,
                'bb_middle': sma,
                'bb_lower': lower_band,
                'bb_width': (upper_band - lower_band) / sma
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return {'bb_upper': pd.Series([0] * len(rates)), 'bb_middle': pd.Series([0] * len(rates)), 'bb_lower': pd.Series([0] * len(rates))}
    
    def _calculate_support_resistance(self, rates: pd.DataFrame, lookback: int = 50) -> Dict:
        """Calculate support and resistance levels"""
        try:
            if len(rates) < lookback:
                lookback = len(rates)
            
            recent_rates = rates.tail(lookback)
            
            # Find local highs and lows
            highs = recent_rates['high'].values
            lows = recent_rates['low'].values
            
            resistance_levels = []
            support_levels = []
            
            # Simple peak detection
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    resistance_levels.append(highs[i])
                
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    support_levels.append(lows[i])
            
            # Get strongest levels
            current_price = rates['close'].iloc[-1]
            
            resistance_above = [r for r in resistance_levels if r > current_price]
            support_below = [s for s in support_levels if s < current_price]
            
            nearest_resistance = min(resistance_above) if resistance_above else None
            nearest_support = max(support_below) if support_below else None
            
            return {
                'nearest_resistance': nearest_resistance,
                'nearest_support': nearest_support,
                'all_resistance': sorted(resistance_levels),
                'all_support': sorted(support_levels)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance: {e}")
            return {'nearest_resistance': None, 'nearest_support': None}
    
    def _calculate_trend_strength(self, rates: pd.DataFrame, period: int = 20) -> float:
        """Calculate trend strength"""
        try:
            if len(rates) < period:
                return 0.5
            
            recent_rates = rates.tail(period)
            
            # Calculate price direction changes
            price_changes = recent_rates['close'].diff()
            positive_changes = (price_changes > 0).sum()
            negative_changes = (price_changes < 0).sum()
            
            # Trend strength based on directional consistency
            total_changes = positive_changes + negative_changes
            if total_changes == 0:
                return 0.5
            
            if positive_changes > negative_changes:
                strength = positive_changes / total_changes
            else:
                strength = negative_changes / total_changes
            
            return strength
            
        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return 0.5
    
    def _identify_trend(self, analysis: Dict, rates: pd.DataFrame) -> Dict[str, any]:
        """Identify market trend"""
        try:
            if 'ma_fast' not in analysis or 'ma_slow' not in analysis:
                return {'direction': 'NEUTRAL', 'strength': 0.5, 'confidence': 0.0}
            
            current_ma_fast = analysis['ma_fast'].iloc[-1]
            current_ma_slow = analysis['ma_slow'].iloc[-1]
            current_price = rates['close'].iloc[-1]
            
            # Trend direction
            if current_ma_fast > current_ma_slow and current_price > current_ma_fast:
                direction = 'BULLISH'
            elif current_ma_fast < current_ma_slow and current_price < current_ma_fast:
                direction = 'BEARISH'
            else:
                direction = 'NEUTRAL'
            
            # Trend strength
            strength = analysis.get('trend_strength', 0.5)
            
            # Confidence based on multiple factors
            confidence = 0.0
            
            # MA alignment
            if direction != 'NEUTRAL':
                confidence += 0.3
            
            # MACD confirmation
            if 'macd_line' in analysis and 'macd_signal' in analysis:
                macd_line = analysis['macd_line'].iloc[-1]
                macd_signal = analysis['macd_signal'].iloc[-1]
                
                if direction == 'BULLISH' and macd_line > macd_signal:
                    confidence += 0.3
                elif direction == 'BEARISH' and macd_line < macd_signal:
                    confidence += 0.3
            
            # RSI confirmation
            if 'rsi' in analysis:
                rsi = analysis['rsi'].iloc[-1]
                if direction == 'BULLISH' and 30 < rsi < 70:
                    confidence += 0.2
                elif direction == 'BEARISH' and 30 < rsi < 70:
                    confidence += 0.2
            
            # Trend strength confirmation
            if strength > self.params['min_trend_strength']:
                confidence += 0.2
            
            self.trend_direction = direction
            
            return {
                'direction': direction,
                'strength': strength,
                'confidence': min(1.0, confidence),
                'ma_fast': current_ma_fast,
                'ma_slow': current_ma_slow,
                'current_price': current_price
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying trend: {e}")
            return {'direction': 'NEUTRAL', 'strength': 0.5, 'confidence': 0.0}
    
    def _generate_signals(self, analysis: Dict, trend: Dict, rates: pd.DataFrame) -> List[Dict]:
        """Generate swing trading signals"""
        try:
            signals = []
            
            if trend['confidence'] < 0.6:
                return signals
            
            current_price = rates['close'].iloc[-1]
            atr = analysis.get('atr', pd.Series([0.001] * len(rates))).iloc[-1]
            
            # Entry conditions
            entry_signal = None
            
            # Bullish setup
            if (trend['direction'] == 'BULLISH' and 
                analysis.get('rsi', pd.Series([50] * len(rates))).iloc[-1] < 70):
                
                # Check for pullback to MA
                ma_fast = analysis['ma_fast'].iloc[-1]
                if abs(current_price - ma_fast) / ma_fast < 0.005:  # Within 0.5% of MA
                    entry_signal = {
                        'action': 'buy',
                        'reason': 'Bullish trend pullback to MA',
                        'confidence': trend['confidence']
                    }
            
            # Bearish setup
            elif (trend['direction'] == 'BEARISH' and 
                  analysis.get('rsi', pd.Series([50] * len(rates))).iloc[-1] > 30):
                
                # Check for pullback to MA
                ma_fast = analysis['ma_fast'].iloc[-1]
                if abs(current_price - ma_fast) / ma_fast < 0.005:  # Within 0.5% of MA
                    entry_signal = {
                        'action': 'sell',
                        'reason': 'Bearish trend pullback to MA',
                        'confidence': trend['confidence']
                    }
            
            # Create complete signal
            if entry_signal:
                stop_loss_distance = atr * self.params['stop_loss_atr']
                
                if entry_signal['action'] == 'buy':
                    stop_loss = current_price - stop_loss_distance
                    take_profit = current_price + (stop_loss_distance * self.params['take_profit_ratio'])
                else:
                    stop_loss = current_price + stop_loss_distance
                    take_profit = current_price - (stop_loss_distance * self.params['take_profit_ratio'])
                
                signal = {
                    'action': entry_signal['action'],
                    'confidence': entry_signal['confidence'],
                    'reason': entry_signal['reason'],
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'volume': self.params['volume'],
                    'timeframe': self.params['timeframe'],
                    'expected_duration': '4-24 hours',
                    'risk_reward': f"1:{self.params['take_profit_ratio']}"
                }
                
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return []
    
    def _assess_risk(self, analysis: Dict, rates: pd.DataFrame) -> Dict[str, any]:
        """Assess risk for swing trading"""
        try:
            risk_factors = []
            risk_level = 'LOW'
            
            # Volatility risk
            if 'atr' in analysis:
                current_atr = analysis['atr'].iloc[-1]
                avg_atr = analysis['atr'].tail(20).mean()
                
                if current_atr > avg_atr * 1.5:
                    risk_factors.append('High volatility')
                    risk_level = 'HIGH'
                elif current_atr > avg_atr * 1.2:
                    risk_factors.append('Elevated volatility')
                    risk_level = 'MEDIUM'
            
            # RSI extremes
            if 'rsi' in analysis:
                rsi = analysis['rsi'].iloc[-1]
                if rsi > 80 or rsi < 20:
                    risk_factors.append('Extreme RSI levels')
                    if risk_level == 'LOW':
                        risk_level = 'MEDIUM'
            
            # Support/Resistance proximity
            if 'nearest_resistance' in analysis or 'nearest_support' in analysis:
                current_price = rates['close'].iloc[-1]
                
                if analysis.get('nearest_resistance'):
                    resistance_distance = abs(current_price - analysis['nearest_resistance']) / current_price
                    if resistance_distance < 0.002:  # Within 0.2%
                        risk_factors.append('Near resistance level')
                        if risk_level == 'LOW':
                            risk_level = 'MEDIUM'
                
                if analysis.get('nearest_support'):
                    support_distance = abs(current_price - analysis['nearest_support']) / current_price
                    if support_distance < 0.002:  # Within 0.2%
                        risk_factors.append('Near support level')
                        if risk_level == 'LOW':
                            risk_level = 'MEDIUM'
            
            return {
                'level': risk_level,
                'factors': risk_factors,
                'recommended_position_size': self._calculate_position_size(risk_level),
                'max_risk_per_trade': '1-2%',
                'assessment_time': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing risk: {e}")
            return {'level': 'HIGH', 'factors': ['Assessment error']}
    
    def _calculate_position_size(self, risk_level: str) -> float:
        """Calculate appropriate position size"""
        base_volume = self.params['volume']
        
        if risk_level == 'LOW':
            return base_volume
        elif risk_level == 'MEDIUM':
            return base_volume * 0.7
        else:  # HIGH
            return base_volume * 0.5
    
    def get_strategy_info(self) -> Dict[str, any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Swing Trading',
            'timeframe': self.params['timeframe'],
            'description': 'Medium-term trend following with pullback entries',
            'risk_level': 'Medium',
            'avg_trade_duration': '4-24 hours',
            'profit_target': f"Risk:Reward 1:{self.params['take_profit_ratio']}",
            'stop_loss': f"{self.params['stop_loss_atr']} * ATR",
            'max_positions': self.params['max_positions'],
            'current_trend': self.trend_direction
        }
"""
Swing Trading Strategy for AuraTrade Bot
Medium-term trading strategy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from utils.logger import Logger

class SwingStrategy:
    """Swing trading strategy"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Swing"
        self.timeframe = "H1"
        
        # Strategy parameters
        self.max_spread = 5.0
        self.tp_pips = 80
        self.sl_pips = 40
        
        self.logger.info("Swing Strategy initialized")
    
    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Optional[Dict]:
        """Analyze swing opportunities"""
        try:
            if len(rates) < 50:
                return None
            
            # Basic swing logic placeholder
            return {
                'action': 'buy',
                'confidence': 0.6,
                'tp_pips': self.tp_pips,
                'sl_pips': self.sl_pips,
                'volume': 0.01,
                'reason': 'Swing analysis'
            }
            
        except Exception as e:
            self.logger.error(f"Error in swing analysis: {e}")
            return None
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'timeframe': self.timeframe,
            'tp_pips': self.tp_pips,
            'sl_pips': self.sl_pips,
            'max_spread': self.max_spread,
            'risk_level': 'Medium',
            'description': 'Swing trading strategy'
        }
