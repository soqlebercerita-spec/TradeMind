
"""
Scalping Strategy for AuraTrade Bot
High-frequency scalping with tight spreads and quick profits
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from utils.logger import Logger, log_info, log_error

class ScalpingStrategy:
    """High-frequency scalping strategy"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Scalping Strategy"
        
        # Strategy parameters
        self.params = {
            'timeframe': 'M1',           # 1-minute charts
            'scalp_target': 5,           # 5 pip target
            'stop_loss': 8,              # 8 pip stop loss
            'min_confidence': 0.7,       # Minimum signal confidence
            'max_spread_pips': 2,        # Maximum spread allowed
            'rsi_period': 14,
            'ema_fast': 5,
            'ema_slow': 15,
            'bb_period': 20,
            'bb_std': 2.0,
            'volume_threshold': 1.2,     # Volume spike threshold
            'momentum_threshold': 0.6    # Momentum threshold
        }
        
        # Performance tracking
        self.trades_today = 0
        self.wins_today = 0
        self.last_trade_time = None
        self.cooldown_minutes = 2
        
        log_info("ScalpingStrategy", "Scalping strategy initialized")
    
    def analyze(self, symbol: str, data: pd.DataFrame, current_spread: float) -> Optional[Dict[str, Any]]:
        """Analyze market for scalping opportunities"""
        try:
            if data.empty or len(data) < 50:
                return None
            
            # Check spread condition
            spread_pips = current_spread * 10000  # Convert to pips
            if spread_pips > self.params['max_spread_pips']:
                return None
            
            # Check cooldown period
            if self._is_in_cooldown():
                return None
            
            # Calculate indicators
            indicators = self._calculate_indicators(data)
            if not indicators:
                return None
            
            # Generate signals
            signals = self._generate_signals(indicators, spread_pips)
            
            return signals
            
        except Exception as e:
            log_error("ScalpingStrategy", f"Error analyzing {symbol}", e)
            return None
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Calculate technical indicators for scalping"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data.get('volume', pd.Series([1000] * len(data))).values
            
            # EMAs for trend
            ema_fast = pd.Series(close).ewm(span=self.params['ema_fast']).mean().values
            ema_slow = pd.Series(close).ewm(span=self.params['ema_slow']).mean().values
            
            # RSI for momentum
            delta = pd.Series(close).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).values
            
            # Bollinger Bands
            bb_middle = pd.Series(close).rolling(window=self.params['bb_period']).mean().values
            bb_std = pd.Series(close).rolling(window=self.params['bb_period']).std().values
            bb_upper = bb_middle + (bb_std * self.params['bb_std'])
            bb_lower = bb_middle - (bb_std * self.params['bb_std'])
            
            # Price momentum
            price_change = close[-1] - close[-5]  # 5-period change
            momentum = price_change / close[-5] if close[-5] != 0 else 0
            
            # Volume analysis
            avg_volume = np.mean(volume[-20:])  # 20-period average
            current_volume = volume[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volatility (ATR approximation)
            tr = np.maximum(high - low, 
                           np.maximum(np.abs(high - np.roll(close, 1)),
                                    np.abs(low - np.roll(close, 1))))
            atr = np.mean(tr[-14:])  # 14-period ATR
            
            return {
                'close': close[-1],
                'ema_fast': ema_fast[-1] if not np.isnan(ema_fast[-1]) else close[-1],
                'ema_slow': ema_slow[-1] if not np.isnan(ema_slow[-1]) else close[-1],
                'rsi': rsi[-1] if not np.isnan(rsi[-1]) else 50,
                'bb_upper': bb_upper[-1] if not np.isnan(bb_upper[-1]) else close[-1] * 1.001,
                'bb_middle': bb_middle[-1] if not np.isnan(bb_middle[-1]) else close[-1],
                'bb_lower': bb_lower[-1] if not np.isnan(bb_lower[-1]) else close[-1] * 0.999,
                'momentum': momentum,
                'volume_ratio': volume_ratio,
                'atr': atr,
                'volatility': atr / close[-1] if close[-1] != 0 else 0.001
            }
            
        except Exception as e:
            log_error("ScalpingStrategy", "Error calculating indicators", e)
            return None
    
    def _generate_signals(self, indicators: Dict[str, Any], spread_pips: float) -> Optional[Dict[str, Any]]:
        """Generate trading signals based on indicators"""
        try:
            buy_score = 0
            sell_score = 0
            
            # Current values
            price = indicators['close']
            ema_fast = indicators['ema_fast']
            ema_slow = indicators['ema_slow']
            rsi = indicators['rsi']
            bb_upper = indicators['bb_upper']
            bb_middle = indicators['bb_middle']
            bb_lower = indicators['bb_lower']
            momentum = indicators['momentum']
            volume_ratio = indicators['volume_ratio']
            volatility = indicators['volatility']
            
            # EMA crossover signals
            if ema_fast > ema_slow:
                buy_score += 2
            else:
                sell_score += 2
            
            # RSI signals (contrarian for scalping)
            if rsi < 30:  # Oversold - potential bounce
                buy_score += 2
            elif rsi > 70:  # Overbought - potential drop
                sell_score += 2
            elif 45 < rsi < 55:  # Neutral RSI
                buy_score += 0.5
                sell_score += 0.5
            
            # Bollinger Band signals
            bb_position = (price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            
            if bb_position < 0.2:  # Near lower band
                buy_score += 1.5
            elif bb_position > 0.8:  # Near upper band
                sell_score += 1.5
            elif 0.4 < bb_position < 0.6:  # Near middle
                buy_score += 0.5
                sell_score += 0.5
            
            # Momentum signals
            if momentum > self.params['momentum_threshold'] / 1000:
                buy_score += 1
            elif momentum < -self.params['momentum_threshold'] / 1000:
                sell_score += 1
            
            # Volume confirmation
            if volume_ratio > self.params['volume_threshold']:
                buy_score += 0.5
                sell_score += 0.5
            
            # Volatility filter (prefer moderate volatility for scalping)
            if 0.0005 < volatility < 0.002:  # Optimal volatility range for scalping
                buy_score += 1
                sell_score += 1
            
            # Spread penalty (tighter spreads get higher scores)
            spread_bonus = max(0, (self.params['max_spread_pips'] - spread_pips) / self.params['max_spread_pips'])
            buy_score += spread_bonus
            sell_score += spread_bonus
            
            # Determine signal
            total_possible_score = 8.5
            
            if buy_score > sell_score and buy_score >= 5:
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
                        'timestamp': datetime.now(),
                        'entry_reason': f"EMA:{ema_fast>ema_slow}, RSI:{rsi:.1f}, BB:{bb_position:.2f}"
                    }
            
            elif sell_score > buy_score and sell_score >= 5:
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
                        'timestamp': datetime.now(),
                        'entry_reason': f"EMA:{ema_fast<ema_slow}, RSI:{rsi:.1f}, BB:{bb_position:.2f}"
                    }
            
            return None
            
        except Exception as e:
            log_error("ScalpingStrategy", "Error generating signals", e)
            return None
    
    def _is_in_cooldown(self) -> bool:
        """Check if strategy is in cooldown period"""
        if self.last_trade_time is None:
            return False
        
        time_since_last = datetime.now() - self.last_trade_time
        return time_since_last.total_seconds() < (self.cooldown_minutes * 60)
    
    def on_trade_opened(self, trade_info: Dict[str, Any]):
        """Handle trade opened event"""
        try:
            self.trades_today += 1
            self.last_trade_time = datetime.now()
            
            log_info("ScalpingStrategy", 
                    f"Trade opened: {trade_info.get('symbol')} {trade_info.get('action')} "
                    f"@ {trade_info.get('price', 0):.5f}")
            
        except Exception as e:
            log_error("ScalpingStrategy", "Error handling trade opened", e)
    
    def on_trade_closed(self, trade_info: Dict[str, Any]):
        """Handle trade closed event"""
        try:
            profit = trade_info.get('profit', 0)
            if profit > 0:
                self.wins_today += 1
            
            win_rate = (self.wins_today / self.trades_today * 100) if self.trades_today > 0 else 0
            
            log_info("ScalpingStrategy", 
                    f"Trade closed: {trade_info.get('symbol')} "
                    f"P&L: ${profit:.2f}, Win Rate: {win_rate:.1f}%")
            
        except Exception as e:
            log_error("ScalpingStrategy", "Error handling trade closed", e)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information and statistics"""
        try:
            win_rate = (self.wins_today / self.trades_today * 100) if self.trades_today > 0 else 0
            
            return {
                'name': self.name,
                'type': 'Scalping',
                'timeframe': self.params['timeframe'],
                'target_pips': self.params['scalp_target'],
                'stop_loss_pips': self.params['stop_loss'],
                'trades_today': self.trades_today,
                'wins_today': self.wins_today,
                'win_rate': win_rate,
                'max_spread': self.params['max_spread_pips'],
                'cooldown_minutes': self.cooldown_minutes,
                'status': 'Active' if not self._is_in_cooldown() else 'Cooldown'
            }
            
        except Exception as e:
            log_error("ScalpingStrategy", "Error getting strategy info", e)
            return {'name': self.name, 'status': 'Error'}
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.trades_today = 0
        self.wins_today = 0
        log_info("ScalpingStrategy", "Daily statistics reset")
