
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
    """High-Frequency Trading strategy for sub-second opportunities"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "HFT"
        
        # HFT Parameters (very aggressive)
        self.params = {
            'timeframe': 'TICK',  # Tick-based trading
            'min_confidence': 0.7,  # High confidence required
            'max_positions': 2,     # Limited concurrent positions
            'profit_target_pips': 3,   # Very small profit target
            'stop_loss_pips': 5,       # Tight stop loss
            'max_holding_time': 1,     # Max 1 minute holding
            'min_tick_movement': 0.5,  # Minimum pip movement to trigger
            'spread_limit': 1.0,       # Very tight spread requirement
            'volume_threshold': 1.5,   # Volume spike threshold
        }
        
        # Tick data storage
        self.tick_history = {}
        self.price_momentum = {}
        self.last_execution = {}
        
        self.logger.info("HFT strategy initialized for ultra-fast execution")
    
    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Optional[Dict[str, Any]]:
        """High-frequency analysis based on tick movements"""
        try:
            # Check if suitable for HFT
            if not self._is_hft_suitable(symbol, tick):
                return None
            
            # Store tick data
            self._store_tick_data(symbol, tick)
            
            # Quick spread check
            if self._check_spread(symbol, tick):
                return None
            
            # Analyze micro-movements
            signal = self._analyze_micro_movements(symbol, tick)
            
            if signal and signal.get('confidence', 0) >= self.params['min_confidence']:
                # Add HFT-specific parameters
                signal.update({
                    'strategy': self.name,
                    'execution_priority': 'IMMEDIATE',
                    'stop_loss_pips': self.params['stop_loss_pips'],
                    'take_profit_pips': self.params['profit_target_pips']
                })
                
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in HFT analysis for {symbol}: {e}")
            return None
    
    def _is_hft_suitable(self, symbol: str, tick: Dict) -> bool:
        """Check if current conditions are suitable for HFT"""
        try:
            # Check last execution time (avoid over-trading)
            current_time = time.time()
            if symbol in self.last_execution:
                if current_time - self.last_execution[symbol] < 5:  # 5 seconds cooldown
                    return False
            
            # Check market hours (avoid low liquidity periods)
            now = datetime.now()
            hour = now.hour
            
            # Only trade during high liquidity hours
            if hour < 6 or hour > 21:  # Avoid Asian/late US sessions
                return False
            
            # Check if it's a major currency pair (better for HFT)
            major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
            if symbol not in major_pairs and 'XAU' not in symbol:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking HFT suitability: {e}")
            return False
    
    def _store_tick_data(self, symbol: str, tick: Dict):
        """Store recent tick data for analysis"""
        try:
            current_time = time.time()
            
            if symbol not in self.tick_history:
                self.tick_history[symbol] = []
            
            # Store tick with timestamp
            tick_data = {
                'timestamp': current_time,
                'bid': tick.get('bid', 0),
                'ask': tick.get('ask', 0),
                'spread': tick.get('ask', 0) - tick.get('bid', 0)
            }
            
            self.tick_history[symbol].append(tick_data)
            
            # Keep only last 50 ticks (about 5 seconds worth)
            if len(self.tick_history[symbol]) > 50:
                self.tick_history[symbol] = self.tick_history[symbol][-50:]
            
        except Exception as e:
            self.logger.error(f"Error storing tick data: {e}")
    
    def _analyze_micro_movements(self, symbol: str, tick: Dict) -> Optional[Dict[str, Any]]:
        """Analyze micro price movements for HFT opportunities"""
        try:
            if symbol not in self.tick_history or len(self.tick_history[symbol]) < 10:
                return None
            
            tick_data = self.tick_history[symbol]
            
            # Calculate momentum indicators
            momentum_signal = self._calculate_tick_momentum(tick_data)
            
            # Calculate price acceleration
            acceleration = self._calculate_price_acceleration(tick_data)
            
            # Volume/spread analysis
            spread_signal = self._analyze_spread_pattern(tick_data)
            
            # Combine micro-signals
            signal = self._combine_hft_signals(momentum_signal, acceleration, spread_signal)
            
            if signal:
                # Add timing constraint
                signal['max_execution_delay'] = 0.1  # 100ms max delay
                signal['time_sensitive'] = True
                
                self.last_execution[symbol] = time.time()
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing micro movements: {e}")
            return None
    
    def _calculate_tick_momentum(self, tick_data: List[Dict]) -> Dict[str, Any]:
        """Calculate momentum from recent ticks"""
        try:
            if len(tick_data) < 5:
                return {'direction': 'NEUTRAL', 'strength': 0}
            
            # Get recent bid prices
            recent_bids = [t['bid'] for t in tick_data[-10:]]
            
            # Calculate directional momentum
            price_changes = np.diff(recent_bids)
            
            # Count directional moves
            up_moves = np.sum(price_changes > 0)
            down_moves = np.sum(price_changes < 0)
            
            # Calculate momentum strength
            avg_change = np.mean(np.abs(price_changes))
            total_range = max(recent_bids) - min(recent_bids)
            
            if total_range > 0:
                momentum_strength = (avg_change / total_range) * 100
            else:
                momentum_strength = 0
            
            # Determine direction
            if up_moves > down_moves * 1.5:
                direction = 'BULLISH'
                strength = momentum_strength * (up_moves / len(price_changes))
            elif down_moves > up_moves * 1.5:
                direction = 'BEARISH'  
                strength = momentum_strength * (down_moves / len(price_changes))
            else:
                direction = 'NEUTRAL'
                strength = 0
            
            return {
                'direction': direction,
                'strength': min(strength, 100),
                'consistency': max(up_moves, down_moves) / len(price_changes)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating tick momentum: {e}")
            return {'direction': 'NEUTRAL', 'strength': 0}
    
    def _calculate_price_acceleration(self, tick_data: List[Dict]) -> float:
        """Calculate price acceleration (change in momentum)"""
        try:
            if len(tick_data) < 6:
                return 0
            
            prices = [t['bid'] for t in tick_data[-6:]]
            
            # Calculate first and second derivatives
            first_diff = np.diff(prices)
            second_diff = np.diff(first_diff)
            
            # Acceleration is the average of second derivatives
            acceleration = np.mean(second_diff) if len(second_diff) > 0 else 0
            
            # Normalize acceleration
            price_range = max(prices) - min(prices)
            if price_range > 0:
                normalized_acceleration = (acceleration / price_range) * 10000
            else:
                normalized_acceleration = 0
            
            return normalized_acceleration
            
        except Exception as e:
            self.logger.error(f"Error calculating acceleration: {e}")
            return 0
    
    def _analyze_spread_pattern(self, tick_data: List[Dict]) -> Dict[str, Any]:
        """Analyze spread patterns for HFT opportunities"""
        try:
            if len(tick_data) < 5:
                return {'signal': 'NEUTRAL', 'strength': 0}
            
            spreads = [t['spread'] for t in tick_data[-10:]]
            
            current_spread = spreads[-1]
            avg_spread = np.mean(spreads[:-1])
            
            # Look for spread compression (better execution opportunity)
            if current_spread < avg_spread * 0.8:
                return {'signal': 'TIGHT_SPREAD', 'strength': 20}
            
            # Look for spread widening (market uncertainty)
            elif current_spread > avg_spread * 1.5:
                return {'signal': 'WIDE_SPREAD', 'strength': -30}
            
            return {'signal': 'NEUTRAL', 'strength': 0}
            
        except Exception as e:
            self.logger.error(f"Error analyzing spread pattern: {e}")
            return {'signal': 'NEUTRAL', 'strength': 0}
    
    def _combine_hft_signals(self, momentum: Dict, acceleration: float, spread: Dict) -> Optional[Dict[str, Any]]:
        """Combine all HFT signals for final decision"""
        try:
            confidence = 0
            action = None
            reasoning = []
            
            # Momentum contribution
            momentum_dir = momentum.get('direction', 'NEUTRAL')
            momentum_strength = momentum.get('strength', 0)
            consistency = momentum.get('consistency', 0)
            
            if momentum_dir != 'NEUTRAL' and momentum_strength > 30:
                confidence += momentum_strength * 0.4
                action = 'BUY' if momentum_dir == 'BULLISH' else 'SELL'
                reasoning.append(f"Strong {momentum_dir.lower()} momentum")
                
                # Bonus for consistency
                if consistency > 0.7:
                    confidence += 15
                    reasoning.append("Consistent directional movement")
            
            # Acceleration contribution
            if abs(acceleration) > 2:  # Significant acceleration
                if action == 'BUY' and acceleration > 0:
                    confidence += 20
                    reasoning.append("Positive acceleration")
                elif action == 'SELL' and acceleration < 0:
                    confidence += 20
                    reasoning.append("Negative acceleration")
                elif action is None:
                    # Acceleration-only signal
                    action = 'BUY' if acceleration > 0 else 'SELL'
                    confidence += 15
                    reasoning.append("Price acceleration detected")
            
            # Spread contribution
            spread_signal = spread.get('signal', 'NEUTRAL')
            spread_strength = spread.get('strength', 0)
            
            if spread_signal == 'TIGHT_SPREAD' and action:
                confidence += spread_strength
                reasoning.append("Favorable spread conditions")
            elif spread_signal == 'WIDE_SPREAD':
                confidence -= abs(spread_strength)
                reasoning.append("Wide spread reduces confidence")
            
            # Minimum confidence and action required
            if action and confidence >= 60:
                final_confidence = min(confidence / 100.0, 0.95)  # Cap at 95%
                
                return {
                    'action': action,
                    'confidence': final_confidence,
                    'reasoning': '; '.join(reasoning),
                    'execution_type': 'MARKET_IMMEDIATE',
                    'momentum_strength': momentum_strength,
                    'acceleration': acceleration
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error combining HFT signals: {e}")
            return None
    
    def _check_spread(self, symbol: str, tick: Dict) -> bool:
        """Check if spread is too wide for HFT"""
        try:
            spread = tick.get('ask', 0) - tick.get('bid', 0)
            
            # Convert to pips
            if 'JPY' in symbol:
                spread_pips = spread * 100
            else:
                spread_pips = spread * 10000
            
            return spread_pips > self.params['spread_limit']
            
        except:
            return True  # If can't calculate, assume too wide
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get HFT strategy information"""
        return {
            'name': self.name,
            'type': 'High-Frequency Trading',
            'timeframe': 'Tick/Sub-second',
            'description': 'Ultra-fast execution based on micro price movements',
            'risk_level': 'High',
            'avg_trade_duration': '10-60 seconds',
            'profit_target': f"{self.params['profit_target_pips']} pips",
            'stop_loss': f"{self.params['stop_loss_pips']} pips",
            'execution_speed': 'Sub-second'
        }
    
    def reset_tick_history(self, symbol: str):
        """Reset tick history for symbol (useful for testing)"""
        if symbol in self.tick_history:
            del self.tick_history[symbol]
    
    def get_tick_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get tick statistics for monitoring"""
        try:
            if symbol not in self.tick_history or not self.tick_history[symbol]:
                return {}
            
            tick_data = self.tick_history[symbol]
            spreads = [t['spread'] for t in tick_data]
            
            return {
                'tick_count': len(tick_data),
                'avg_spread': np.mean(spreads),
                'min_spread': min(spreads),
                'max_spread': max(spreads),
                'last_update': tick_data[-1]['timestamp'] if tick_data else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tick statistics: {e}")
            return {}
