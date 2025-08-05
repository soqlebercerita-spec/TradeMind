"""
Scalping Strategy
Short-term trading strategy focused on capturing small price movements
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config.config import Config
from config.settings import Settings
from utils.logger import Logger

class ScalpingStrategy:
    """Scalping strategy implementation"""
    
    def __init__(self, config: Config, settings: Settings):
        self.logger = Logger().get_logger()
        self.config = config
        self.settings = settings
        
        # Strategy parameters
        self.strategy_name = 'scalping'
        self.min_signal_strength = settings.strategies[self.strategy_name].min_signal_strength
        self.max_positions = settings.strategies[self.strategy_name].max_positions
        
        # Scalping-specific parameters
        self.max_spread_pips = config.STRATEGY_SETTINGS['scalping']['max_spread']
        self.profit_target_pips = config.STRATEGY_SETTINGS['scalping']['profit_target_pips']
        self.stop_loss_pips = config.STRATEGY_SETTINGS['scalping']['stop_loss_pips']
        self.max_trades_per_hour = config.STRATEGY_SETTINGS['scalping']['max_trades_per_hour']
        
        # Technical indicators parameters
        self.ema_fast = 8
        self.ema_slow = 21
        self.rsi_period = 14
        self.rsi_overbought = 75
        self.rsi_oversold = 25
        self.stoch_k = 5
        self.stoch_d = 3
        
        # Scalping state tracking
        self.recent_trades = {}
        self.support_resistance_levels = {}
        self.trend_direction = {}
        
        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.win_rate = 0.0
        
    def generate_signal(self, symbol: str, market_data: Dict[str, pd.DataFrame], 
                       aggregated_signal: Dict) -> Optional[Dict[str, Any]]:
        """Generate scalping trading signal"""
        try:
            # Use M1 and M5 timeframes for scalping
            if 'M1' not in market_data or 'M5' not in market_data:
                return None
            
            df_m1 = market_data['M1']
            df_m5 = market_data['M5']
            
            if df_m1.empty or df_m5.empty or len(df_m1) < 50 or len(df_m5) < 50:
                return None
            
            # Check if we can trade (spread, trading hours, etc.)
            if not self._can_scalp(symbol):
                return None
            
            # Update support/resistance levels
            self._update_support_resistance(symbol, df_m5)
            
            # Analyze trend direction on M5
            trend_signal = self._analyze_trend(symbol, df_m5)
            
            # Look for entry signals on M1
            entry_signal = self._find_entry_signal(symbol, df_m1, trend_signal)
            
            if not entry_signal:
                return None
            
            # Confirm with momentum indicators
            momentum_signal = self._analyze_momentum(df_m1)
            
            # Check for support/resistance confluence
            sr_signal = self._check_support_resistance(symbol, df_m1['close'].iloc[-1])
            
            # Combine all signals
            combined_strength = self._combine_scalping_signals(
                entry_signal, momentum_signal, sr_signal, trend_signal
            )
            
            if abs(combined_strength) < self.min_signal_strength:
                return None
            
            # Determine final direction
            direction = 1 if combined_strength > 0 else -1
            
            # Calculate entry, SL, and TP levels
            current_price = df_m1['close'].iloc[-1]
            pip_size = self._get_pip_size(symbol)
            
            if direction > 0:  # Buy signal
                entry_price = current_price
                stop_loss = entry_price - (self.stop_loss_pips * pip_size)
                take_profit = entry_price + (self.profit_target_pips * pip_size)
            else:  # Sell signal
                entry_price = current_price
                stop_loss = entry_price + (self.stop_loss_pips * pip_size)
                take_profit = entry_price - (self.profit_target_pips * pip_size)
            
            # Check if trade frequency is within limits
            if not self._check_trade_frequency(symbol):
                return None
            
            self.signals_generated += 1
            
            return {
                'direction': direction,
                'strength': abs(combined_strength),
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': f'Scalping Signal: {entry_signal.get("reason", "Multi-timeframe confirmation")}',
                'timeframe': 'M1',
                'strategy_type': 'scalping'
            }
            
        except Exception as e:
            self.logger.error(f"Error generating scalping signal for {symbol}: {e}")
            return None
    
    def _can_scalp(self, symbol: str) -> bool:
        """Check if scalping conditions are met"""
        try:
            # Check spread (would normally get from MT5)
            # For now, assume spread check passes
            
            # Check trading session (scalping works best during active sessions)
            current_hour = datetime.now().hour
            
            # European and US sessions are best for scalping major pairs
            if symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
                if 8 <= current_hour <= 17 or 13 <= current_hour <= 22:  # EU or US session
                    return True
            
            # For other symbols, allow trading during most hours
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking scalping conditions for {symbol}: {e}")
            return False
    
    def _analyze_trend(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend direction using M5 timeframe"""
        try:
            if len(df) < 50:
                return {'direction': 0, 'strength': 0}
            
            # Calculate EMAs
            ema_fast = df['close'].ewm(span=self.ema_fast).mean()
            ema_slow = df['close'].ewm(span=self.ema_slow).mean()
            
            # Current trend direction
            current_trend = 1 if ema_fast.iloc[-1] > ema_slow.iloc[-1] else -1
            
            # Trend strength based on EMA separation
            ema_separation = abs(ema_fast.iloc[-1] - ema_slow.iloc[-1]) / df['close'].iloc[-1]
            trend_strength = min(ema_separation * 1000, 1.0)  # Normalize
            
            # Check for trend continuation
            ema_fast_slope = (ema_fast.iloc[-1] - ema_fast.iloc[-5]) / df['close'].iloc[-1]
            ema_slow_slope = (ema_slow.iloc[-1] - ema_slow.iloc[-5]) / df['close'].iloc[-1]
            
            # Confirm trend if both EMAs are moving in same direction
            if (ema_fast_slope > 0 and ema_slow_slope > 0 and current_trend > 0) or \
               (ema_fast_slope < 0 and ema_slow_slope < 0 and current_trend < 0):
                trend_confirmation = 1.2  # Boost strength
            else:
                trend_confirmation = 0.8  # Reduce strength
            
            final_strength = trend_strength * trend_confirmation
            
            # Store trend information
            self.trend_direction[symbol] = {
                'direction': current_trend,
                'strength': final_strength,
                'ema_fast': ema_fast.iloc[-1],
                'ema_slow': ema_slow.iloc[-1],
                'timestamp': datetime.now()
            }
            
            return {
                'direction': current_trend,
                'strength': final_strength,
                'reason': f'EMA Trend ({self.ema_fast}/{self.ema_slow})'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend for {symbol}: {e}")
            return {'direction': 0, 'strength': 0}
    
    def _find_entry_signal(self, symbol: str, df: pd.DataFrame, trend_signal: Dict) -> Optional[Dict[str, Any]]:
        """Find entry signals on M1 timeframe"""
        try:
            if len(df) < 20:
                return None
            
            # Calculate short-term EMAs for entry
            ema_entry_fast = df['close'].ewm(span=3).mean()
            ema_entry_slow = df['close'].ewm(span=8).mean()
            
            # Look for EMA crossover
            crossover_signal = self._detect_ema_crossover(ema_entry_fast, ema_entry_slow)
            
            # Look for pullback to EMA
            pullback_signal = self._detect_ema_pullback(df, ema_entry_slow)
            
            # Look for breakout from consolidation
            breakout_signal = self._detect_breakout(df)
            
            # Combine entry signals
            entry_signals = [crossover_signal, pullback_signal, breakout_signal]
            valid_signals = [s for s in entry_signals if s is not None]
            
            if not valid_signals:
                return None
            
            # Use the strongest signal
            best_signal = max(valid_signals, key=lambda x: x['strength'])
            
            # Confirm signal aligns with trend
            if trend_signal['direction'] != 0:
                if best_signal['direction'] == trend_signal['direction']:
                    best_signal['strength'] *= 1.5  # Boost strength for trend alignment
                else:
                    best_signal['strength'] *= 0.5  # Reduce strength for counter-trend
            
            return best_signal
            
        except Exception as e:
            self.logger.error(f"Error finding entry signal for {symbol}: {e}")
            return None
    
    def _detect_ema_crossover(self, ema_fast: pd.Series, ema_slow: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect EMA crossover signals"""
        try:
            if len(ema_fast) < 3:
                return None
            
            # Check for crossover in last 2 bars
            current_above = ema_fast.iloc[-1] > ema_slow.iloc[-1]
            previous_above = ema_fast.iloc[-2] > ema_slow.iloc[-2]
            
            if current_above and not previous_above:
                # Bullish crossover
                return {
                    'direction': 1,
                    'strength': 0.8,
                    'reason': 'EMA Bullish Crossover'
                }
            elif not current_above and previous_above:
                # Bearish crossover
                return {
                    'direction': -1,
                    'strength': 0.8,
                    'reason': 'EMA Bearish Crossover'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting EMA crossover: {e}")
            return None
    
    def _detect_ema_pullback(self, df: pd.DataFrame, ema: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect pullback to EMA for entry"""
        try:
            if len(df) < 10:
                return None
            
            current_price = df['close'].iloc[-1]
            current_ema = ema.iloc[-1]
            
            # Check if price is near EMA (within 0.1% for forex)
            price_ema_distance = abs(current_price - current_ema) / current_price
            
            if price_ema_distance < 0.001:  # Within 0.1%
                # Determine direction based on recent price action
                recent_high = df['high'].tail(5).max()
                recent_low = df['low'].tail(5).min()
                
                if current_price > current_ema and current_price > (recent_low + recent_high) / 2:
                    return {
                        'direction': 1,
                        'strength': 0.6,
                        'reason': 'Bullish EMA Pullback'
                    }
                elif current_price < current_ema and current_price < (recent_low + recent_high) / 2:
                    return {
                        'direction': -1,
                        'strength': 0.6,
                        'reason': 'Bearish EMA Pullback'
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting EMA pullback: {e}")
            return None
    
    def _detect_breakout(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect breakout from consolidation"""
        try:
            if len(df) < 20:
                return None
            
            # Calculate recent range
            lookback = 15
            recent_df = df.tail(lookback)
            
            range_high = recent_df['high'].max()
            range_low = recent_df['low'].min()
            range_size = range_high - range_low
            
            # Current price
            current_price = df['close'].iloc[-1]
            current_high = df['high'].iloc[-1]
            current_low = df['low'].iloc[-1]
            
            # Check for breakout
            if current_high > range_high:
                # Bullish breakout
                breakout_strength = min((current_price - range_high) / range_size, 1.0)
                if breakout_strength > 0.1:  # Significant breakout
                    return {
                        'direction': 1,
                        'strength': 0.7 + breakout_strength * 0.3,
                        'reason': 'Bullish Breakout'
                    }
            elif current_low < range_low:
                # Bearish breakout
                breakout_strength = min((range_low - current_price) / range_size, 1.0)
                if breakout_strength > 0.1:  # Significant breakout
                    return {
                        'direction': -1,
                        'strength': 0.7 + breakout_strength * 0.3,
                        'reason': 'Bearish Breakout'
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting breakout: {e}")
            return None
    
    def _analyze_momentum(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum using RSI and Stochastic"""
        try:
            if len(df) < 20:
                return {'direction': 0, 'strength': 0}
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Calculate Stochastic
            lowest_low = df['low'].rolling(window=self.stoch_k).min()
            highest_high = df['high'].rolling(window=self.stoch_k).max()
            k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=self.stoch_d).mean()
            
            current_k = k_percent.iloc[-1]
            current_d = d_percent.iloc[-1]
            
            # Momentum signals
            momentum_direction = 0
            momentum_strength = 0
            
            # RSI signals
            if current_rsi < self.rsi_oversold:
                momentum_direction += 1
                momentum_strength += 0.5
            elif current_rsi > self.rsi_overbought:
                momentum_direction -= 1
                momentum_strength += 0.5
            
            # Stochastic signals
            if current_k < 20 and current_d < 20:
                momentum_direction += 1
                momentum_strength += 0.3
            elif current_k > 80 and current_d > 80:
                momentum_direction -= 1
                momentum_strength += 0.3
            
            # Stochastic crossover
            if current_k > current_d and k_percent.iloc[-2] <= d_percent.iloc[-2]:
                momentum_direction += 1
                momentum_strength += 0.4
            elif current_k < current_d and k_percent.iloc[-2] >= d_percent.iloc[-2]:
                momentum_direction -= 1
                momentum_strength += 0.4
            
            # Normalize direction
            if momentum_direction > 0:
                final_direction = 1
            elif momentum_direction < 0:
                final_direction = -1
            else:
                final_direction = 0
            
            return {
                'direction': final_direction,
                'strength': min(momentum_strength, 1.0),
                'rsi': current_rsi,
                'stoch_k': current_k,
                'stoch_d': current_d
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing momentum: {e}")
            return {'direction': 0, 'strength': 0}
    
    def _update_support_resistance(self, symbol: str, df: pd.DataFrame):
        """Update support and resistance levels"""
        try:
            if len(df) < 50:
                return
            
            # Use pivot points and swing highs/lows
            recent_df = df.tail(50)
            
            # Find swing highs and lows
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(recent_df) - 2):
                # Swing high: higher than 2 bars on each side
                if (recent_df['high'].iloc[i] > recent_df['high'].iloc[i-2:i].max() and
                    recent_df['high'].iloc[i] > recent_df['high'].iloc[i+1:i+3].max()):
                    swing_highs.append(recent_df['high'].iloc[i])
                
                # Swing low: lower than 2 bars on each side
                if (recent_df['low'].iloc[i] < recent_df['low'].iloc[i-2:i].min() and
                    recent_df['low'].iloc[i] < recent_df['low'].iloc[i+1:i+3].min()):
                    swing_lows.append(recent_df['low'].iloc[i])
            
            # Store levels
            self.support_resistance_levels[symbol] = {
                'resistance_levels': sorted(swing_highs, reverse=True)[:5],  # Top 5 resistance
                'support_levels': sorted(swing_lows)[-5:],  # Top 5 support
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error updating support/resistance for {symbol}: {e}")
    
    def _check_support_resistance(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Check proximity to support/resistance levels"""
        try:
            if symbol not in self.support_resistance_levels:
                return {'direction': 0, 'strength': 0}
            
            levels = self.support_resistance_levels[symbol]
            resistance_levels = levels['resistance_levels']
            support_levels = levels['support_levels']
            
            # Check distance to nearest levels
            min_resistance_distance = float('inf')
            min_support_distance = float('inf')
            
            for level in resistance_levels:
                distance = abs(current_price - level) / current_price
                if distance < min_resistance_distance:
                    min_resistance_distance = distance
            
            for level in support_levels:
                distance = abs(current_price - level) / current_price
                if distance < min_support_distance:
                    min_support_distance = distance
            
            # Generate signals based on proximity to levels
            if min_support_distance < 0.002:  # Within 0.2% of support
                return {
                    'direction': 1,  # Expect bounce up from support
                    'strength': 0.6,
                    'reason': 'Near Support Level'
                }
            elif min_resistance_distance < 0.002:  # Within 0.2% of resistance
                return {
                    'direction': -1,  # Expect rejection at resistance
                    'strength': 0.6,
                    'reason': 'Near Resistance Level'
                }
            
            return {'direction': 0, 'strength': 0}
            
        except Exception as e:
            self.logger.error(f"Error checking support/resistance for {symbol}: {e}")
            return {'direction': 0, 'strength': 0}
    
    def _combine_scalping_signals(self, entry_signal: Dict, momentum_signal: Dict, 
                                sr_signal: Dict, trend_signal: Dict) -> float:
        """Combine all scalping signals"""
        try:
            # Signal weights
            weights = {
                'entry': 0.4,
                'momentum': 0.3,
                'support_resistance': 0.2,
                'trend': 0.1
            }
            
            total_strength = 0.0
            
            # Entry signal
            if entry_signal:
                total_strength += entry_signal['direction'] * entry_signal['strength'] * weights['entry']
            
            # Momentum signal
            if momentum_signal['strength'] > 0:
                total_strength += momentum_signal['direction'] * momentum_signal['strength'] * weights['momentum']
            
            # Support/resistance signal
            if sr_signal['strength'] > 0:
                total_strength += sr_signal['direction'] * sr_signal['strength'] * weights['support_resistance']
            
            # Trend signal
            if trend_signal['strength'] > 0:
                total_strength += trend_signal['direction'] * trend_signal['strength'] * weights['trend']
            
            return total_strength
            
        except Exception as e:
            self.logger.error(f"Error combining scalping signals: {e}")
            return 0.0
    
    def _check_trade_frequency(self, symbol: str) -> bool:
        """Check if trade frequency is within limits"""
        try:
            current_time = datetime.now()
            
            if symbol not in self.recent_trades:
                self.recent_trades[symbol] = []
            
            # Remove trades older than 1 hour
            one_hour_ago = current_time - timedelta(hours=1)
            self.recent_trades[symbol] = [
                trade_time for trade_time in self.recent_trades[symbol] 
                if trade_time > one_hour_ago
            ]
            
            # Check if we're under the limit
            if len(self.recent_trades[symbol]) < self.max_trades_per_hour:
                self.recent_trades[symbol].append(current_time)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking trade frequency for {symbol}: {e}")
            return False
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        try:
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
            
            return pip_sizes.get(symbol, 0.0001)
            
        except Exception as e:
            self.logger.error(f"Error getting pip size for {symbol}: {e}")
            return 0.0001
    
    def manage_position(self, position: Dict, mt5_connector, order_manager):
        """Manage scalping positions"""
        try:
            symbol = position['symbol']
            ticket = position['ticket']
            open_time = datetime.fromtimestamp(position['time'])
            current_time = datetime.now()
            
            # Scalping positions should be closed within 1 hour
            position_age = (current_time - open_time).total_seconds() / 3600
            
            if position_age > 1.0:  # 1 hour
                order_manager.close_position(ticket, "Scalping time limit")
                return
            
            # Quick profit taking for scalping
            if position['profit'] > 10:  # $10 profit
                order_manager.close_position(ticket, "Scalping quick profit")
                return
            
            # Implement breakeven stop after some profit
            if position['profit'] > 5 and position['sl'] != position['price_open']:
                # Move stop to breakeven
                mt5_connector.modify_position(ticket, sl=position['price_open'])
            
        except Exception as e:
            self.logger.error(f"Error managing scalping position {position.get('ticket', 0)}: {e}")
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """Get scalping strategy status"""
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
                    'profit_target_pips': self.profit_target_pips,
                    'stop_loss_pips': self.stop_loss_pips,
                    'max_trades_per_hour': self.max_trades_per_hour
                },
                'tracked_symbols': {
                    'trend_direction': len(self.trend_direction),
                    'support_resistance': len(self.support_resistance_levels),
                    'recent_trades': len(self.recent_trades)
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting scalping strategy status: {e}")
            return {}
