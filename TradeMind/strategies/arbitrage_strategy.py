"""
Arbitrage Strategy
Strategy focused on exploiting price differences between correlated instruments
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import threading
from collections import defaultdict

from config.config import Config
from config.settings import Settings
from utils.logger import Logger

class ArbitrageStrategy:
    """Arbitrage strategy implementation"""
    
    def __init__(self, config: Config, settings: Settings):
        self.logger = Logger().get_logger()
        self.config = config
        self.settings = settings
        
        # Strategy parameters
        self.strategy_name = 'arbitrage'
        self.min_signal_strength = settings.strategies[self.strategy_name].min_signal_strength
        self.max_positions = settings.strategies[self.strategy_name].max_positions
        
        # Arbitrage-specific parameters
        self.min_price_difference = config.STRATEGY_SETTINGS['arbitrage']['min_price_difference']
        self.execution_timeout = config.STRATEGY_SETTINGS['arbitrage']['execution_timeout']
        self.max_latency_ms = config.STRATEGY_SETTINGS['arbitrage']['max_latency_ms']
        
        # Correlation pairs and their expected relationships
        self.correlation_pairs = {
            'EURUSD_GBPUSD': {
                'symbol1': 'EURUSD',
                'symbol2': 'GBPUSD',
                'correlation': 0.8,
                'ratio_mean': 0.85,  # Historical EUR/GBP ratio
                'ratio_std': 0.05
            },
            'EURJPY_USDJPY': {
                'symbol1': 'EURJPY',
                'symbol2': 'USDJPY',
                'correlation': 0.7,
                'ratio_mean': 1.15,  # EURJPY / USDJPY ratio
                'ratio_std': 0.1
            },
            'XAUUSD_XAGUSD': {
                'symbol1': 'XAUUSD',
                'symbol2': 'XAGUSD',
                'correlation': 0.8,
                'ratio_mean': 80.0,  # Gold/Silver ratio
                'ratio_std': 10.0
            }
        }
        
        # Real-time price tracking
        self.price_data = {}
        self.price_lock = threading.Lock()
        
        # Arbitrage opportunities tracking
        self.opportunities = {}
        self.executed_arbitrages = []
        
        # Statistical arbitrage parameters
        self.lookback_period = 100
        self.z_score_threshold = 2.0
        self.mean_reversion_period = 20
        
        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.arbitrage_profits = []
        
    def generate_signal(self, symbol: str, market_data: Dict[str, pd.DataFrame], 
                       aggregated_signal: Dict) -> Optional[Dict[str, Any]]:
        """Generate arbitrage trading signal"""
        try:
            # Update price data
            self._update_price_data(symbol, market_data)
            
            # Look for direct arbitrage opportunities
            direct_arbitrage = self._find_direct_arbitrage(symbol)
            if direct_arbitrage:
                return direct_arbitrage
            
            # Look for statistical arbitrage opportunities
            stat_arbitrage = self._find_statistical_arbitrage(symbol, market_data)
            if stat_arbitrage:
                return stat_arbitrage
            
            # Look for triangular arbitrage (for currency pairs)
            triangular_arbitrage = self._find_triangular_arbitrage(symbol)
            if triangular_arbitrage:
                return triangular_arbitrage
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating arbitrage signal for {symbol}: {e}")
            return None
    
    def _update_price_data(self, symbol: str, market_data: Dict[str, pd.DataFrame]):
        """Update real-time price data"""
        try:
            with self.price_lock:
                if 'M1' in market_data and not market_data['M1'].empty:
                    latest_price = market_data['M1']['close'].iloc[-1]
                    timestamp = datetime.now()
                    
                    if symbol not in self.price_data:
                        self.price_data[symbol] = []
                    
                    self.price_data[symbol].append({
                        'price': latest_price,
                        'timestamp': timestamp
                    })
                    
                    # Keep only recent data (last 1000 points)
                    if len(self.price_data[symbol]) > 1000:
                        self.price_data[symbol] = self.price_data[symbol][-1000:]
                        
        except Exception as e:
            self.logger.error(f"Error updating price data for {symbol}: {e}")
    
    def _find_direct_arbitrage(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Find direct arbitrage opportunities between brokers/venues"""
        try:
            # In a real implementation, this would compare prices across different brokers
            # For simulation, we'll detect unusual price movements that might indicate
            # temporary mispricing
            
            if symbol not in self.price_data or len(self.price_data[symbol]) < 10:
                return None
            
            recent_prices = [p['price'] for p in self.price_data[symbol][-10:]]
            
            # Look for sudden price jumps that might indicate mispricing
            price_changes = np.diff(recent_prices)
            avg_change = np.mean(np.abs(price_changes))
            latest_change = abs(price_changes[-1])
            
            # If latest change is significantly larger than average
            if avg_change > 0 and latest_change > 3 * avg_change:
                # Potential arbitrage opportunity
                direction = -1 if price_changes[-1] > 0 else 1  # Fade the move
                
                return {
                    'direction': direction,
                    'strength': 0.9,
                    'entry_price': recent_prices[-1],
                    'stop_loss': recent_prices[-1] * (1 + direction * 0.001),  # 0.1% stop
                    'take_profit': recent_prices[-1] * (1 - direction * 0.002),  # 0.2% target
                    'reason': 'Direct Arbitrage - Price Anomaly',
                    'type': 'direct_arbitrage',
                    'urgency': 'immediate'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding direct arbitrage for {symbol}: {e}")
            return None
    
    def _find_statistical_arbitrage(self, symbol: str, market_data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Find statistical arbitrage opportunities using correlation analysis"""
        try:
            # Find correlation pairs involving this symbol
            relevant_pairs = []
            for pair_name, pair_info in self.correlation_pairs.items():
                if symbol in [pair_info['symbol1'], pair_info['symbol2']]:
                    relevant_pairs.append((pair_name, pair_info))
            
            if not relevant_pairs:
                return None
            
            for pair_name, pair_info in relevant_pairs:
                symbol1 = pair_info['symbol1']
                symbol2 = pair_info['symbol2']
                
                # Check if we have data for both symbols
                if (symbol1 not in self.price_data or symbol2 not in self.price_data or
                    len(self.price_data[symbol1]) < self.lookback_period or
                    len(self.price_data[symbol2]) < self.lookback_period):
                    continue
                
                # Get recent price data
                prices1 = [p['price'] for p in self.price_data[symbol1][-self.lookback_period:]]
                prices2 = [p['price'] for p in self.price_data[symbol2][-self.lookback_period:]]
                
                # Calculate price ratio
                ratios = np.array(prices1) / np.array(prices2)
                
                # Calculate z-score of current ratio
                current_ratio = ratios[-1]
                mean_ratio = np.mean(ratios[:-1])  # Exclude current point
                std_ratio = np.std(ratios[:-1])
                
                if std_ratio > 0:
                    z_score = (current_ratio - mean_ratio) / std_ratio
                    
                    # Check for significant deviation
                    if abs(z_score) > self.z_score_threshold:
                        # Determine which symbol to trade
                        if symbol == symbol1:
                            # If ratio is too high, sell symbol1 (expecting ratio to decrease)
                            direction = -1 if z_score > 0 else 1
                        else:  # symbol == symbol2
                            # If ratio is too high, buy symbol2 (expecting ratio to decrease)
                            direction = 1 if z_score > 0 else -1
                        
                        strength = min(abs(z_score) / 4.0, 1.0)  # Normalize to 0-1
                        
                        if strength >= self.min_signal_strength:
                            current_price = prices1[-1] if symbol == symbol1 else prices2[-1]
                            
                            return {
                                'direction': direction,
                                'strength': strength,
                                'entry_price': current_price,
                                'stop_loss': current_price * (1 + direction * 0.005),  # 0.5% stop
                                'take_profit': current_price * (1 - direction * 0.01),  # 1% target
                                'reason': f'Statistical Arbitrage - {pair_name} Z-Score: {z_score:.2f}',
                                'type': 'statistical_arbitrage',
                                'pair': pair_name,
                                'z_score': z_score
                            }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding statistical arbitrage for {symbol}: {e}")
            return None
    
    def _find_triangular_arbitrage(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Find triangular arbitrage opportunities in currency pairs"""
        try:
            # Triangular arbitrage works with three currency pairs
            # For example: EUR/USD, GBP/USD, EUR/GBP
            
            triangular_sets = [
                ['EURUSD', 'GBPUSD', 'EURGBP'],
                ['EURUSD', 'USDJPY', 'EURJPY'],
                ['GBPUSD', 'USDJPY', 'GBPJPY']
            ]
            
            for currency_set in triangular_sets:
                if symbol not in currency_set:
                    continue
                
                # Check if we have price data for all three pairs
                if not all(pair in self.price_data and len(self.price_data[pair]) > 0 
                          for pair in currency_set):
                    continue
                
                # Get latest prices
                prices = {}
                for pair in currency_set:
                    prices[pair] = self.price_data[pair][-1]['price']
                
                # Calculate implied rates and check for arbitrage
                arbitrage_opportunity = self._calculate_triangular_arbitrage(
                    currency_set, prices, symbol
                )
                
                if arbitrage_opportunity:
                    return arbitrage_opportunity
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding triangular arbitrage for {symbol}: {e}")
            return None
    
    def _calculate_triangular_arbitrage(self, currency_set: List[str], 
                                      prices: Dict[str, float], 
                                      target_symbol: str) -> Optional[Dict[str, Any]]:
        """Calculate triangular arbitrage opportunity"""
        try:
            if currency_set == ['EURUSD', 'GBPUSD', 'EURGBP']:
                eur_usd = prices['EURUSD']
                gbp_usd = prices['GBPUSD']
                eur_gbp = prices['EURGBP']
                
                # Calculate implied EUR/GBP from EUR/USD and GBP/USD
                implied_eur_gbp = eur_usd / gbp_usd
                actual_eur_gbp = eur_gbp
                
                # Check for arbitrage opportunity
                price_difference = abs(implied_eur_gbp - actual_eur_gbp) / actual_eur_gbp
                
                if price_difference > self.min_price_difference / 100:
                    if target_symbol == 'EURGBP':
                        # If implied > actual, buy EURGBP
                        direction = 1 if implied_eur_gbp > actual_eur_gbp else -1
                        
                        return {
                            'direction': direction,
                            'strength': min(price_difference * 10, 1.0),
                            'entry_price': actual_eur_gbp,
                            'stop_loss': actual_eur_gbp * (1 + direction * 0.002),
                            'take_profit': actual_eur_gbp * (1 - direction * price_difference * 0.5),
                            'reason': f'Triangular Arbitrage - EUR/USD/GBP, Diff: {price_difference*100:.3f}%',
                            'type': 'triangular_arbitrage',
                            'price_difference': price_difference
                        }
            
            # Add similar logic for other triangular sets
            # ... (implementation for other currency triangles)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating triangular arbitrage: {e}")
            return None
    
    def _check_execution_feasibility(self, signal: Dict[str, Any]) -> bool:
        """Check if arbitrage can be executed within time constraints"""
        try:
            # Check if we have recent price data (within max latency)
            current_time = datetime.now()
            max_age = timedelta(milliseconds=self.max_latency_ms)
            
            # In real implementation, check data freshness from all required sources
            return True  # Simplified for now
            
        except Exception as e:
            self.logger.error(f"Error checking execution feasibility: {e}")
            return False
    
    def manage_position(self, position: Dict, mt5_connector, order_manager):
        """Manage arbitrage positions with tight risk control"""
        try:
            symbol = position['symbol']
            ticket = position['ticket']
            open_time = datetime.fromtimestamp(position['time'])
            current_time = datetime.now()
            
            # Arbitrage positions should be closed quickly
            position_age_seconds = (current_time - open_time).total_seconds()
            
            # Close if held too long (arbitrage opportunities are temporary)
            max_hold_time = self.execution_timeout / 1000  # Convert to seconds
            if position_age_seconds > max_hold_time:
                order_manager.close_position(ticket, "Arbitrage timeout")
                return
            
            # Quick profit taking for arbitrage
            if position['profit'] > 0:
                # Take profit immediately if we have any profit
                order_manager.close_position(ticket, "Arbitrage profit secured")
                return
            
            # Tight stop loss management
            current_loss_pct = abs(position['profit']) / position['volume'] / 100000  # Rough calculation
            if current_loss_pct > 0.001:  # 0.1% loss
                order_manager.close_position(ticket, "Arbitrage stop loss")
                return
            
        except Exception as e:
            self.logger.error(f"Error managing arbitrage position {position.get('ticket', 0)}: {e}")
    
    def update_correlation_parameters(self, symbol1: str, symbol2: str, 
                                    lookback_days: int = 30):
        """Update correlation parameters based on recent data"""
        try:
            if (symbol1 not in self.price_data or symbol2 not in self.price_data or
                len(self.price_data[symbol1]) < 100 or len(self.price_data[symbol2]) < 100):
                return
            
            # Get recent price data
            prices1 = [p['price'] for p in self.price_data[symbol1][-lookback_days*24*60:]]  # Assuming 1-minute data
            prices2 = [p['price'] for p in self.price_data[symbol2][-lookback_days*24*60:]]
            
            # Calculate returns
            returns1 = np.diff(np.log(prices1))
            returns2 = np.diff(np.log(prices2))
            
            # Calculate correlation
            correlation = np.corrcoef(returns1, returns2)[0, 1]
            
            # Calculate price ratio statistics
            ratios = np.array(prices1) / np.array(prices2)
            ratio_mean = np.mean(ratios)
            ratio_std = np.std(ratios)
            
            # Update correlation pairs
            pair_key = f"{symbol1}_{symbol2}"
            if pair_key in self.correlation_pairs:
                self.correlation_pairs[pair_key].update({
                    'correlation': correlation,
                    'ratio_mean': ratio_mean,
                    'ratio_std': ratio_std
                })
                
                self.logger.info(f"Updated correlation parameters for {pair_key}: "
                               f"corr={correlation:.3f}, ratio_mean={ratio_mean:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error updating correlation parameters: {e}")
    
    def get_arbitrage_opportunities(self) -> Dict[str, Any]:
        """Get current arbitrage opportunities"""
        try:
            opportunities = {}
            
            for pair_name, pair_info in self.correlation_pairs.items():
                symbol1 = pair_info['symbol1']
                symbol2 = pair_info['symbol2']
                
                if (symbol1 in self.price_data and symbol2 in self.price_data and
                    len(self.price_data[symbol1]) > 0 and len(self.price_data[symbol2]) > 0):
                    
                    price1 = self.price_data[symbol1][-1]['price']
                    price2 = self.price_data[symbol2][-1]['price']
                    
                    current_ratio = price1 / price2
                    expected_ratio = pair_info['ratio_mean']
                    
                    deviation = abs(current_ratio - expected_ratio) / expected_ratio
                    
                    opportunities[pair_name] = {
                        'symbol1': symbol1,
                        'symbol2': symbol2,
                        'price1': price1,
                        'price2': price2,
                        'current_ratio': current_ratio,
                        'expected_ratio': expected_ratio,
                        'deviation_pct': deviation * 100,
                        'correlation': pair_info['correlation'],
                        'opportunity_score': deviation * pair_info['correlation']
                    }
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error getting arbitrage opportunities: {e}")
            return {}
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """Get arbitrage strategy status"""
        try:
            total_profit = sum(self.arbitrage_profits) if self.arbitrage_profits else 0
            avg_profit = total_profit / len(self.arbitrage_profits) if self.arbitrage_profits else 0
            
            return {
                'strategy_name': self.strategy_name,
                'signals_generated': self.signals_generated,
                'trades_executed': self.trades_executed,
                'total_arbitrage_profit': total_profit,
                'average_arbitrage_profit': avg_profit,
                'settings': {
                    'min_price_difference': self.min_price_difference,
                    'execution_timeout': self.execution_timeout,
                    'max_latency_ms': self.max_latency_ms,
                    'z_score_threshold': self.z_score_threshold
                },
                'correlation_pairs': len(self.correlation_pairs),
                'price_data_symbols': len(self.price_data),
                'current_opportunities': len(self.get_arbitrage_opportunities())
            }
        except Exception as e:
            self.logger.error(f"Error getting arbitrage strategy status: {e}")
            return {}
    
    def record_arbitrage_result(self, profit: float, trade_type: str):
        """Record arbitrage trade result"""
        try:
            self.arbitrage_profits.append(profit)
            self.trades_executed += 1
            
            # Keep only recent results
            if len(self.arbitrage_profits) > 100:
                self.arbitrage_profits = self.arbitrage_profits[-100:]
            
            self.logger.info(f"Arbitrage trade completed: {trade_type}, Profit: ${profit:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error recording arbitrage result: {e}")
