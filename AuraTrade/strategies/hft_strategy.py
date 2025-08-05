
"""
High-Frequency Trading Strategy for AuraTrade Bot
Scalping-based strategy targeting quick profits with high win rate
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from utils.logger import Logger

class HFTStrategy:
    """High-Frequency Trading strategy for quick scalping profits"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "HFT_Scalper"
        
        # Strategy parameters optimized for high win rate
        self.params = {
            'min_spread': 2,           # Minimum spread in pips
            'max_spread': 10,          # Maximum spread in pips  
            'scalp_target': 5,         # Target profit in pips
            'stop_loss': 3,            # Stop loss in pips
            'rsi_oversold': 25,        # RSI oversold level
            'rsi_overbought': 75,      # RSI overbought level
            'volume_threshold': 1.5,   # Volume spike threshold
            'momentum_period': 5,      # Momentum calculation period
            'min_confidence': 0.75,    # Minimum confidence for trade
        }
        
        # Internal state
        self.last_signals = {}
        self.signal_count = 0
        
        self.logger.info(f"HFT Strategy initialized - Target: Quick scalps with 85%+ win rate")
    
    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze market conditions for HFT opportunities"""
        try:
            if len(rates) < 20:
                return None
            
            # Current market conditions
            current_bid = tick['bid']
            current_ask = tick['ask']
            spread = (current_ask - current_bid) * 100000  # Convert to pips
            
            # Check spread conditions
            if not self._check_spread_conditions(spread):
                return None
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(rates)
            if not indicators:
                return None
            
            # Generate trading signal
            signal = self._generate_signal(symbol, indicators, tick, spread)
            
            if signal:
                self.signal_count += 1
                self.last_signals[symbol] = {
                    'signal': signal,
                    'timestamp': datetime.now()
                }
                
                self.logger.info(f"HFT signal generated for {symbol}: {signal['action']} (Confidence: {signal['confidence']:.2f})")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in HFT analysis for {symbol}: {e}")
            return None
    
    def _check_spread_conditions(self, spread_pips: float) -> bool:
        """Check if spread conditions are favorable for scalping"""
        return self.params['min_spread'] <= spread_pips <= self.params['max_spread']
    
    def _calculate_indicators(self, rates: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Calculate technical indicators for HFT"""
        try:
            # Ensure we have enough data
            if len(rates) < 20:
                return None
            
            close_prices = rates['close'].values
            high_prices = rates['high'].values
            low_prices = rates['low'].values
            volumes = rates['tick_volume'].values
            
            # RSI calculation
            rsi = self._calculate_rsi(close_prices, 14)
            
            # Price momentum (rate of change)
            momentum = self._calculate_momentum(close_prices, self.params['momentum_period'])
            
            # Volume analysis
            volume_avg = np.mean(volumes[-10:])
            current_volume = volumes[-1]
            volume_ratio = current_volume / volume_avg if volume_avg > 0 else 1.0
            
            # Volatility (ATR-like)
            volatility = self._calculate_volatility(high_prices, low_prices, close_prices)
            
            # Price action patterns
            price_pattern = self._analyze_price_action(close_prices[-5:])
            
            # Micro-trend analysis
            micro_trend = self._calculate_micro_trend(close_prices[-10:])
            
            return {
                'rsi': rsi,
                'momentum': momentum,
                'volume_ratio': volume_ratio,
                'volatility': volatility,
                'price_pattern': price_pattern,
                'micro_trend': micro_trend,
                'current_price': close_prices[-1]
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating HFT indicators: {e}")
            return None
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral RSI
            
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception:
            return 50.0
    
    def _calculate_momentum(self, prices: np.ndarray, period: int) -> float:
        """Calculate price momentum"""
        try:
            if len(prices) < period + 1:
                return 0.0
            
            current_price = prices[-1]
            past_price = prices[-period-1]
            
            momentum = (current_price - past_price) / past_price * 100
            return momentum
            
        except Exception:
            return 0.0
    
    def _calculate_volatility(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
        """Calculate volatility (ATR-like)"""
        try:
            if len(highs) < 10:
                return 0.0
            
            true_ranges = []
            for i in range(1, len(highs)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            
            volatility = np.mean(true_ranges[-10:]) if true_ranges else 0.0
            return volatility
            
        except Exception:
            return 0.0
    
    def _analyze_price_action(self, recent_prices: np.ndarray) -> str:
        """Analyze recent price action patterns"""
        try:
            if len(recent_prices) < 3:
                return "NEUTRAL"
            
            # Simple trend analysis
            trend_up = all(recent_prices[i] >= recent_prices[i-1] for i in range(1, len(recent_prices)))
            trend_down = all(recent_prices[i] <= recent_prices[i-1] for i in range(1, len(recent_prices)))
            
            if trend_up:
                return "BULLISH"
            elif trend_down:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except Exception:
            return "NEUTRAL"
    
    def _calculate_micro_trend(self, prices: np.ndarray) -> float:
        """Calculate micro-trend strength"""
        try:
            if len(prices) < 5:
                return 0.0
            
            # Linear regression slope
            x = np.arange(len(prices))
            slope = np.polyfit(x, prices, 1)[0]
            
            # Normalize slope
            price_range = max(prices) - min(prices)
            normalized_slope = slope / price_range if price_range > 0 else 0.0
            
            return normalized_slope * 1000  # Scale for easier interpretation
            
        except Exception:
            return 0.0
    
    def _generate_signal(self, symbol: str, indicators: Dict[str, float], 
                        tick: Dict[str, Any], spread_pips: float) -> Optional[Dict[str, Any]]:
        """Generate HFT trading signal"""
        try:
            rsi = indicators['rsi']
            momentum = indicators['momentum']
            volume_ratio = indicators['volume_ratio']
            volatility = indicators['volatility']
            price_pattern = indicators['price_pattern']
            micro_trend = indicators['micro_trend']
            
            # Signal scoring system
            buy_score = 0
            sell_score = 0
            
            # RSI signals
            if rsi < self.params['rsi_oversold']:
                buy_score += 2
            elif rsi > self.params['rsi_overbought']:
                sell_score += 2
            
            # Momentum signals
            if momentum > 0.1:
                buy_score += 1
            elif momentum < -0.1:
                sell_score += 1
            
            # Volume confirmation
            if volume_ratio > self.params['volume_threshold']:
                if micro_trend > 0:
                    buy_score += 1
                elif micro_trend < 0:
                    sell_score += 1
            
            # Price pattern confirmation
            if price_pattern == "BULLISH":
                buy_score += 1
            elif price_pattern == "BEARISH":
                sell_score += 1
            
            # Micro-trend signals
            if micro_trend > 0.5:
                buy_score += 1
            elif micro_trend < -0.5:
                sell_score += 1
            
            # Volatility filter (prefer moderate volatility)
            if 0.0001 < volatility < 0.001:  # Optimal volatility range
                buy_score += 0.5
                sell_score += 0.5
            
            # Determine signal
            total_possible_score = 6.5
            
            if buy_score > sell_score and buy_score >= 4:
                confidence = min(buy_score / total_possible_score, 0.95)
                if confidence >= self.params['min_confidence']:
                    return {
                        'action': 'BUY',
                        'confidence': confidence,
                        'stop_loss_pips': self.params['stop_loss'],
                        'take_profit_pips': self.params['scalp_target'],
                        'signal_strength': buy_score,
                        'indicators': indicators,
                        'spread_pips': spread_pips,
                        'strategy': self.name,
                        'timestamp': datetime.now()
                    }
            
            elif sell_score > buy_score and sell_score >= 4:
                confidence = min(sell_score / total_possible_score, 0.95)
                if confidence >= self.params['min_confidence']:
                    return {
                        'action': 'SELL',
                        'confidence': confidence,
                        'stop_loss_pips': self.params['stop_loss'],
                        'take_profit_pips': self.params['scalp_target'],
                        'signal_strength': sell_score,
                        'indicators': indicators,
                        'spread_pips': spread_pips,
                        'strategy': self.name,
                        'timestamp': datetime.now()
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating HFT signal: {e}")
            return None
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'High-Frequency Scalping',
            'parameters': self.params,
            'signals_generated': self.signal_count,
            'last_signals': self.last_signals,
            'target_win_rate': '85%+',
            'avg_trade_duration': '1-5 minutes',
            'risk_reward_ratio': f"1:{self.params['scalp_target']/self.params['stop_loss']:.1f}"
        }
    
    def update_parameters(self, new_params: Dict[str, Any]):
        """Update strategy parameters"""
        self.params.update(new_params)
        self.logger.info(f"HFT strategy parameters updated: {new_params}")
    
    def reset_statistics(self):
        """Reset strategy statistics"""
        self.signal_count = 0
        self.last_signals = {}
        self.logger.info("HFT strategy statistics reset")
