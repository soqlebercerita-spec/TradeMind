"""
High-Frequency Trading Strategy for AuraTrade Bot
Ultra-fast execution based on tick data and micro-movements
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time
from utils.logger import Logger

class HFTStrategy:
    """High-Frequency Trading Strategy with ultra-fast execution"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "HFT"

        # Strategy parameters
        self.min_price_movement = 0.00005  # 0.5 pips minimum movement
        self.max_hold_time = 300  # 5 minutes max hold time
        self.scalp_target = 0.0001  # 1 pip target
        self.stop_loss = 0.00005   # 0.5 pip stop loss

        # Tick analysis
        self.tick_buffer = []
        self.max_buffer_size = 100

        # Performance tracking
        self.trades_count = 0
        self.winning_trades = 0

        self.logger.info("HFT Strategy initialized")

    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Optional[Dict]:
        """Analyze market for HFT opportunities"""
        try:
            if rates is None or len(rates) < 20:
                return None

            # Add current tick to buffer
            self._update_tick_buffer(tick)

            # Quick momentum analysis
            momentum_signal = self._analyze_momentum(rates)

            # Tick velocity analysis
            velocity_signal = self._analyze_tick_velocity()

            # Spread analysis
            spread_ok = self._check_spread(tick, symbol)

            if not spread_ok:
                return None

            # Combine signals
            combined_signal = self._combine_signals(momentum_signal, velocity_signal)

            if combined_signal and combined_signal.get('confidence', 0) > 0.7:
                return self._generate_trade_signal(symbol, combined_signal, tick)

            return None

        except Exception as e:
            self.logger.error(f"Error in HFT analysis for {symbol}: {e}")
            return None

    def _update_tick_buffer(self, tick: Dict):
        """Update tick buffer for velocity analysis"""
        try:
            tick_data = {
                'timestamp': datetime.now(),
                'bid': tick.get('bid', 0),
                'ask': tick.get('ask', 0),
                'spread': tick.get('ask', 0) - tick.get('bid', 0)
            }

            self.tick_buffer.append(tick_data)

            # Keep buffer size manageable
            if len(self.tick_buffer) > self.max_buffer_size:
                self.tick_buffer.pop(0)

        except Exception as e:
            self.logger.error(f"Error updating tick buffer: {e}")

    def _analyze_momentum(self, rates: pd.DataFrame) -> Dict:
        """Analyze short-term momentum"""
        try:
            if len(rates) < 10:
                return {'action': 'hold', 'confidence': 0}

            # Calculate short-term EMAs
            closes = rates['close'].values
            ema_3 = self._calculate_ema(closes, 3)
            ema_5 = self._calculate_ema(closes, 5)
            ema_8 = self._calculate_ema(closes, 8)

            # Current values
            current_price = closes[-1]
            current_ema3 = ema_3[-1]
            current_ema5 = ema_5[-1]
            current_ema8 = ema_8[-1]

            # Momentum signals
            momentum_up = (current_ema3 > current_ema5 > current_ema8 and 
                          current_price > current_ema3)
            momentum_down = (current_ema3 < current_ema5 < current_ema8 and 
                            current_price < current_ema3)

            # Price velocity
            price_change = (current_price - closes[-5]) / closes[-5] * 100

            if momentum_up and price_change > 0.01:  # 0.01% minimum change
                return {
                    'action': 'buy',
                    'confidence': min(0.8, abs(price_change) * 10),
                    'strength': price_change
                }
            elif momentum_down and price_change < -0.01:
                return {
                    'action': 'sell',
                    'confidence': min(0.8, abs(price_change) * 10),
                    'strength': abs(price_change)
                }

            return {'action': 'hold', 'confidence': 0}

        except Exception as e:
            self.logger.error(f"Error in momentum analysis: {e}")
            return {'action': 'hold', 'confidence': 0}

    def _analyze_tick_velocity(self) -> Dict:
        """Analyze tick-by-tick velocity"""
        try:
            if len(self.tick_buffer) < 10:
                return {'action': 'hold', 'confidence': 0}

            # Calculate price changes
            recent_ticks = self.tick_buffer[-10:]
            price_changes = []

            for i in range(1, len(recent_ticks)):
                mid_price_prev = (recent_ticks[i-1]['bid'] + recent_ticks[i-1]['ask']) / 2
                mid_price_curr = (recent_ticks[i]['bid'] + recent_ticks[i]['ask']) / 2
                change = mid_price_curr - mid_price_prev
                price_changes.append(change)

            if not price_changes:
                return {'action': 'hold', 'confidence': 0}

            # Velocity metrics
            avg_change = np.mean(price_changes)
            velocity = np.std(price_changes)

            # Direction consistency
            positive_moves = sum(1 for x in price_changes if x > 0)
            negative_moves = sum(1 for x in price_changes if x < 0)

            direction_strength = abs(positive_moves - negative_moves) / len(price_changes)

            # Strong upward velocity
            if avg_change > self.min_price_movement and direction_strength > 0.6:
                return {
                    'action': 'buy',
                    'confidence': min(0.9, direction_strength + velocity * 1000),
                    'velocity': velocity
                }
            # Strong downward velocity
            elif avg_change < -self.min_price_movement and direction_strength > 0.6:
                return {
                    'action': 'sell',
                    'confidence': min(0.9, direction_strength + velocity * 1000),
                    'velocity': velocity
                }

            return {'action': 'hold', 'confidence': 0}

        except Exception as e:
            self.logger.error(f"Error in velocity analysis: {e}")
            return {'action': 'hold', 'confidence': 0}

    def _check_spread(self, tick: Dict, symbol: str) -> bool:
        """Check if spread is acceptable for HFT"""
        try:
            spread = tick.get('ask', 0) - tick.get('bid', 0)

            # Symbol-specific spread limits
            if 'JPY' in symbol:
                max_spread = 0.002  # 2 points for JPY pairs
            elif 'XAU' in symbol or 'GOLD' in symbol:
                max_spread = 0.5    # 50 cents for gold
            else:
                max_spread = 0.00003  # 3 pips for major pairs

            return spread <= max_spread

        except Exception as e:
            self.logger.error(f"Error checking spread: {e}")
            return False

    def _combine_signals(self, momentum_signal: Dict, velocity_signal: Dict) -> Optional[Dict]:
        """Combine momentum and velocity signals"""
        try:
            if (momentum_signal.get('action') == velocity_signal.get('action') and 
                momentum_signal.get('action') != 'hold'):

                # Both signals agree
                combined_confidence = (momentum_signal.get('confidence', 0) + 
                                     velocity_signal.get('confidence', 0)) / 2

                return {
                    'action': momentum_signal.get('action'),
                    'confidence': min(0.95, combined_confidence * 1.2),  # Boost confidence
                    'momentum_strength': momentum_signal.get('strength', 0),
                    'velocity': velocity_signal.get('velocity', 0)
                }

            return None

        except Exception as e:
            self.logger.error(f"Error combining signals: {e}")
            return None

    def _generate_trade_signal(self, symbol: str, signal: Dict, tick: Dict) -> Dict:
        """Generate final trade signal"""
        try:
            action = signal.get('action')
            confidence = signal.get('confidence', 0)

            # Calculate volume based on confidence
            base_volume = 0.01
            volume = base_volume * (1 + confidence)

            # Calculate TP/SL in pips
            if 'JPY' in symbol:
                tp_pips = 1    # 1 point for JPY
                sl_pips = 0.5  # 0.5 point for JPY
            elif 'XAU' in symbol:
                tp_pips = 10   # $1 for gold
                sl_pips = 5    # $0.5 for gold
            else:
                tp_pips = 1    # 1 pip
                sl_pips = 0.5  # 0.5 pip

            trade_signal = {
                'action': action,
                'symbol': symbol,
                'volume': round(volume, 2),
                'confidence': confidence,
                'take_profit_pips': tp_pips,
                'stop_loss_pips': sl_pips,
                'strategy': 'HFT',
                'timestamp': datetime.now(),
                'current_price': (tick.get('bid', 0) + tick.get('ask', 0)) / 2,
                'spread': tick.get('ask', 0) - tick.get('bid', 0)
            }

            self.trades_count += 1
            self.logger.info(f"HFT signal generated: {action.upper()} {symbol} (confidence: {confidence:.2f})")

            return trade_signal

        except Exception as e:
            self.logger.error(f"Error generating trade signal: {e}")
            return None

    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        try:
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data)
            ema[0] = data[0]

            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

            return ema

        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return np.zeros_like(data)

    def get_signals(self, rates: pd.DataFrame, indicators: Dict, tick: Dict) -> List[Dict]:
        """Get trading signals (interface compatibility)"""
        try:
            signal = self.analyze(tick.get('symbol', 'UNKNOWN'), rates, tick)
            return [signal] if signal else []

        except Exception as e:
            self.logger.error(f"Error getting signals: {e}")
            return []

    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        win_rate = (self.winning_trades / max(self.trades_count, 1)) * 100

        return {
            'name': self.name,
            'type': 'High-Frequency Trading',
            'trades_count': self.trades_count,
            'win_rate': win_rate,
            'target_pips': self.scalp_target,
            'stop_loss_pips': self.stop_loss,
            'max_hold_time': self.max_hold_time,
            'status': 'active'
        }

    def reset_stats(self):
        """Reset strategy statistics"""
        self.trades_count = 0
        self.winning_trades = 0
        self.tick_buffer.clear()
        self.logger.info("HFT strategy statistics reset")