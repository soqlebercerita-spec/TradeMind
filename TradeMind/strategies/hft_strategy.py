"""
High Frequency Trading (HFT) Strategy
Ultra-fast execution strategy focusing on tick-level movements and market microstructure
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config.config import Config
from config.settings import Settings
from utils.logger import Logger

class HFTStrategy:
    """High Frequency Trading strategy implementation"""
    
    def __init__(self, config: Config, settings: Settings):
        self.logger = Logger().get_logger()
        self.config = config
        self.settings = settings
        
        # Strategy parameters
        self.strategy_name = 'hft'
        self.min_signal_strength = settings.strategies[self.strategy_name].min_signal_strength
        self.max_positions = settings.strategies[self.strategy_name].max_positions
        
        # HFT-specific parameters
        self.max_spread_pips = config.STRATEGY_SETTINGS['hft']['max_spread']
        self.min_volume = config.STRATEGY_SETTINGS['hft']['min_volume']
        self.execution_delay_ms = config.STRATEGY_SETTINGS['hft']['execution_delay_ms']
        self.profit_target_pips = config.STRATEGY_SETTINGS['hft']['profit_target_pips']
        self.stop_loss_pips = config.STRATEGY_SETTINGS['hft']['stop_loss_pips']
        
        # Market microstructure tracking
        self.order_book_imbalance = {}
        self.tick_momentum = {}
        self.last_tick_time = {}
        self.volume_profile = {}
        
        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.win_rate = 0.0
        
    def generate_signal(self, symbol: str, market_data: Dict[str, pd.DataFrame], 
                       aggregated_signal: Dict) -> Optional[Dict[str, Any]]:
        """Generate HFT trading signal"""
        try:
            # Get M1 data for HFT analysis
            if 'M1' not in market_data or market_data['M1'].empty:
                return None
            
            df = market_data['M1']
            
            # Check if we have sufficient recent data
            if len(df) < 10:
                return None
            
            # Check spread condition
            if not self._check_spread_condition(symbol):
                return None
            
            # Analyze tick momentum
            tick_signal = self._analyze_tick_momentum(symbol, df)
            if not tick_signal:
                return None
            
            # Check order book imbalance
            imbalance_signal = self._analyze_order_book_imbalance(symbol, df)
            
            # Check volume conditions
            volume_signal = self._analyze_volume_conditions(symbol, df)
            
            # Price action analysis
            price_action_signal = self._analyze_price_action(df)
            
            # Combine signals
            signal_strength = self._combine_hft_signals(
                tick_signal, imbalance_signal, volume_signal, price_action_signal
            )
            
            if abs(signal_strength) < self.min_signal_strength:
                return None
            
            # Determine direction
            direction = 1 if signal_strength > 0 else -1
            
            # Calculate entry, SL, and TP
            current_price = df['close'].iloc[-1]
            
            if direction > 0:  # Buy signal
                entry_price = current_price + (0.5 * self._get_pip_size(symbol))  # Slightly above market
                stop_loss = entry_price - (self.stop_loss_pips * self._get_pip_size(symbol))
                take_profit = entry_price + (self.profit_target_pips * self._get_pip_size(symbol))
            else:  # Sell signal
                entry_price = current_price - (0.5 * self._get_pip_size(symbol))  # Slightly below market
                stop_loss = entry_price + (self.stop_loss_pips * self._get_pip_size(symbol))
                take_profit = entry_price - (self.profit_target_pips * self._get_pip_size(symbol))
            
            self.signals_generated += 1
            
            return {
                'direction': direction,
                'strength': abs(signal_strength),
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': f'HFT Signal: Tick momentum, Strength: {abs(signal_strength):.3f}',
                'urgency': 'high',  # HFT signals need immediate execution
                'max_execution_delay': self.execution_delay_ms
            }
            
        except Exception as e:
            self.logger.error(f"Error generating HFT signal for {symbol}: {e}")
            return None
    
    def _check_spread_condition(self, symbol: str) -> bool:
        """Check if spread is within acceptable limits for HFT"""
        try:
            # This would normally get real-time spread data
            # For now, assume spread check is passed if within configured limits
            return True
        except Exception as e:
            self.logger.error(f"Error checking spread condition for {symbol}: {e}")
            return False
    
    def _analyze_tick_momentum(self, symbol: str, df: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Analyze tick-level momentum"""
        try:
            if len(df) < 5:
                return None
            
            # Calculate tick-by-tick price changes
            price_changes = df['close'].diff().tail(5)
            
            # Calculate momentum score
            positive_ticks = (price_changes > 0).sum()
            negative_ticks = (price_changes < 0).sum()
            
            if positive_ticks + negative_ticks == 0:
                return None
            
            momentum_ratio = (positive_ticks - negative_ticks) / (positive_ticks + negative_ticks)
            
            # Calculate velocity (rate of change)
            time_diff = (df.index[-1] - df.index[-5]).total_seconds()
            if time_diff > 0:
                velocity = abs(df['close'].iloc[-1] - df['close'].iloc[-5]) / time_diff
            else:
                velocity = 0
            
            # Volume-weighted momentum
            volume_weights = df['tick_volume'].tail(5)
            if volume_weights.sum() > 0:
                weighted_momentum = (price_changes * volume_weights).sum() / volume_weights.sum()
            else:
                weighted_momentum = 0
            
            # Store in tracking dictionary
            self.tick_momentum[symbol] = {
                'momentum_ratio': momentum_ratio,
                'velocity': velocity,
                'weighted_momentum': weighted_momentum,
                'timestamp': datetime.now()
            }
            
            # Generate signal based on momentum
            if abs(momentum_ratio) > 0.6 and velocity > 0:
                return {
                    'direction': 1 if momentum_ratio > 0 else -1,
                    'strength': min(abs(momentum_ratio) + velocity * 0.1, 1.0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing tick momentum for {symbol}: {e}")
            return None
    
    def _analyze_order_book_imbalance(self, symbol: str, df: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Analyze order book imbalance (simulated)"""
        try:
            # In real HFT, this would analyze actual order book data
            # For simulation, we'll use price and volume patterns
            
            if len(df) < 3:
                return None
            
            # Simulate bid/ask imbalance using recent price movements and volume
            recent_df = df.tail(3)
            
            # Calculate price pressure based on volume-weighted moves
            up_moves = recent_df[recent_df['close'] > recent_df['open']]
            down_moves = recent_df[recent_df['close'] < recent_df['open']]
            
            up_volume = up_moves['tick_volume'].sum() if not up_moves.empty else 0
            down_volume = down_moves['tick_volume'].sum() if not down_moves.empty else 0
            
            total_volume = up_volume + down_volume
            
            if total_volume == 0:
                return None
            
            imbalance_ratio = (up_volume - down_volume) / total_volume
            
            # Store imbalance data
            self.order_book_imbalance[symbol] = {
                'imbalance_ratio': imbalance_ratio,
                'total_volume': total_volume,
                'timestamp': datetime.now()
            }
            
            # Generate signal if imbalance is significant
            if abs(imbalance_ratio) > 0.3:
                return {
                    'direction': 1 if imbalance_ratio > 0 else -1,
                    'strength': min(abs(imbalance_ratio), 1.0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing order book imbalance for {symbol}: {e}")
            return None
    
    def _analyze_volume_conditions(self, symbol: str, df: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Analyze volume conditions for HFT"""
        try:
            if len(df) < 10:
                return None
            
            # Current volume vs recent average
            current_volume = df['tick_volume'].iloc[-1]
            avg_volume = df['tick_volume'].tail(10).mean()
            
            if avg_volume == 0:
                return None
            
            volume_ratio = current_volume / avg_volume
            
            # Volume spike detection
            volume_spike = volume_ratio > 2.0
            
            # Volume trend
            volume_trend = df['tick_volume'].tail(5).diff().mean()
            
            # Store volume profile
            self.volume_profile[symbol] = {
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'volume_spike': volume_spike,
                'volume_trend': volume_trend,
                'timestamp': datetime.now()
            }
            
            # Generate signal based on volume
            if current_volume >= self.min_volume and volume_ratio > 1.5:
                strength = min(volume_ratio / 3.0, 1.0)  # Normalize strength
                direction = 1 if volume_trend > 0 else -1
                
                return {
                    'direction': direction,
                    'strength': strength
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing volume conditions for {symbol}: {e}")
            return None
    
    def _analyze_price_action(self, df: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Analyze price action patterns for HFT"""
        try:
            if len(df) < 5:
                return None
            
            recent_df = df.tail(5)
            
            # Breakout detection
            high_breakout = recent_df['high'].iloc[-1] > recent_df['high'].iloc[:-1].max()
            low_breakout = recent_df['low'].iloc[-1] < recent_df['low'].iloc[:-1].min()
            
            # Momentum confirmation
            price_momentum = (recent_df['close'].iloc[-1] - recent_df['close'].iloc[0]) / recent_df['close'].iloc[0]
            
            # Candle patterns
            current_candle = recent_df.iloc[-1]
            body_size = abs(current_candle['close'] - current_candle['open'])
            total_range = current_candle['high'] - current_candle['low']
            
            body_ratio = body_size / total_range if total_range > 0 else 0
            
            # Signal generation
            if high_breakout and price_momentum > 0.0005:  # 0.05% momentum
                return {
                    'direction': 1,
                    'strength': min(abs(price_momentum) * 100 + body_ratio * 0.5, 1.0)
                }
            elif low_breakout and price_momentum < -0.0005:
                return {
                    'direction': -1,
                    'strength': min(abs(price_momentum) * 100 + body_ratio * 0.5, 1.0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing price action: {e}")
            return None
    
    def _combine_hft_signals(self, tick_signal: Dict, imbalance_signal: Dict, 
                           volume_signal: Dict, price_action_signal: Dict) -> float:
        """Combine all HFT signals into final strength"""
        try:
            total_strength = 0.0
            signal_count = 0
            
            # Weight each signal type
            weights = {
                'tick': 0.4,
                'imbalance': 0.3,
                'volume': 0.2,
                'price_action': 0.1
            }
            
            signals = {
                'tick': tick_signal,
                'imbalance': imbalance_signal,
                'volume': volume_signal,
                'price_action': price_action_signal
            }
            
            for signal_type, signal in signals.items():
                if signal:
                    direction = signal['direction']
                    strength = signal['strength']
                    weight = weights[signal_type]
                    
                    total_strength += direction * strength * weight
                    signal_count += 1
            
            # Require at least 2 confirming signals
            if signal_count < 2:
                return 0.0
            
            # Normalize by number of signals
            final_strength = total_strength / sum(weights.values())
            
            return final_strength
            
        except Exception as e:
            self.logger.error(f"Error combining HFT signals: {e}")
            return 0.0
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        try:
            # Standard pip sizes
            pip_sizes = {
                'EURUSD': 0.0001,
                'GBPUSD': 0.0001,
                'USDJPY': 0.01,
                'USDCHF': 0.0001,
                'AUDUSD': 0.0001,
                'USDCAD': 0.0001,
                'NZDUSD': 0.0001,
                'XAUUSD': 0.1,
                'BTCUSD': 1.0
            }
            
            return pip_sizes.get(symbol, 0.0001)  # Default to 0.0001
            
        except Exception as e:
            self.logger.error(f"Error getting pip size for {symbol}: {e}")
            return 0.0001
    
    def manage_position(self, position: Dict, mt5_connector, order_manager):
        """Manage HFT positions with fast exit conditions"""
        try:
            symbol = position['symbol']
            ticket = position['ticket']
            open_time = datetime.fromtimestamp(position['time'])
            current_time = datetime.now()
            
            # HFT positions should be closed quickly
            position_age_seconds = (current_time - open_time).total_seconds()
            
            # Close position if held for more than 5 minutes (300 seconds)
            if position_age_seconds > 300:
                order_manager.close_position(ticket, "HFT time limit exceeded")
                return
            
            # Fast profit taking
            current_profit = position['profit']
            if current_profit > 0:
                # Take profit quickly if we have any profit after 30 seconds
                if position_age_seconds > 30:
                    order_manager.close_position(ticket, "HFT quick profit take")
                    return
            
            # Tight trailing stop for HFT
            if position['profit'] > 5:  # $5 profit
                # Implement very tight trailing stop
                current_price = mt5_connector.get_current_price(symbol)
                if current_price:
                    bid, ask = current_price
                    
                    if position['type'] == 0:  # Buy position
                        new_sl = bid - (2 * self._get_pip_size(symbol))  # 2 pip trailing
                    else:  # Sell position
                        new_sl = ask + (2 * self._get_pip_size(symbol))  # 2 pip trailing
                    
                    if new_sl != position['sl']:
                        mt5_connector.modify_position(ticket, sl=new_sl)
            
        except Exception as e:
            self.logger.error(f"Error managing HFT position {position.get('ticket', 0)}: {e}")
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """Get HFT strategy status"""
        try:
            return {
                'strategy_name': self.strategy_name,
                'signals_generated': self.signals_generated,
                'trades_executed': self.trades_executed,
                'win_rate': self.win_rate,
                'min_signal_strength': self.min_signal_strength,
                'max_positions': self.max_positions,
                'settings': {
                    'max_spread_pips': self.max_spread_pips,
                    'min_volume': self.min_volume,
                    'execution_delay_ms': self.execution_delay_ms,
                    'profit_target_pips': self.profit_target_pips,
                    'stop_loss_pips': self.stop_loss_pips
                },
                'market_data': {
                    'tick_momentum_count': len(self.tick_momentum),
                    'order_book_imbalance_count': len(self.order_book_imbalance),
                    'volume_profile_count': len(self.volume_profile)
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting HFT strategy status: {e}")
            return {}
    
    def update_performance(self, trade_result: Dict):
        """Update strategy performance metrics"""
        try:
            self.trades_executed += 1
            
            if trade_result.get('profit', 0) > 0:
                wins = getattr(self, 'wins', 0) + 1
                self.wins = wins
            else:
                losses = getattr(self, 'losses', 0) + 1
                self.losses = losses
            
            total_trades = getattr(self, 'wins', 0) + getattr(self, 'losses', 0)
            if total_trades > 0:
                self.win_rate = getattr(self, 'wins', 0) / total_trades
            
        except Exception as e:
            self.logger.error(f"Error updating HFT performance: {e}")
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        try:
            self.signals_generated = 0
            self.trades_executed = 0
            self.tick_momentum.clear()
            self.order_book_imbalance.clear()
            self.volume_profile.clear()
            
            self.logger.info("HFT strategy daily stats reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting HFT daily stats: {e}")
