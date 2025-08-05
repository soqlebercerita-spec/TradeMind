
"""
Arbitrage Strategy for AuraTrade Bot
Cross-broker and cross-instrument arbitrage opportunities
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from utils.logger import Logger, log_info, log_error

class ArbitrageStrategy:
    """Arbitrage trading strategy for price discrepancies"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Arbitrage Strategy"
        
        # Strategy parameters
        self.params = {
            'min_spread_profit': 0.5,    # Minimum spread profit in pips
            'max_execution_delay': 2,     # Maximum execution delay in seconds
            'correlation_threshold': 0.85, # Minimum correlation for pairs
            'min_confidence': 0.8,        # High confidence required
            'risk_per_trade': 0.5,       # Lower risk for arbitrage
            'max_positions': 2,           # Max simultaneous arbitrage positions
        }
        
        # Arbitrage pairs and correlations
        self.arbitrage_pairs = {
            'EURUSD_GBPUSD': ['EURUSD', 'GBPUSD'],
            'XAUUSD_XAGUSD': ['XAUUSD', 'XAGUSD'],
            'BTCUSD_ETHUSD': ['BTCUSD', 'ETHUSD']
        }
        
        # Performance tracking
        self.active_arbitrage = {}
        self.arbitrage_count = 0
        self.successful_arbitrage = 0
        
        log_info("ArbitrageStrategy", "Arbitrage strategy initialized")
    
    def analyze(self, symbols_data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Analyze multiple symbols for arbitrage opportunities"""
        try:
            if len(symbols_data) < 2:
                return None
            
            # Check each arbitrage pair
            for pair_name, symbols in self.arbitrage_pairs.items():
                if all(symbol in symbols_data for symbol in symbols):
                    opportunity = self._check_arbitrage_opportunity(
                        pair_name, symbols, symbols_data
                    )
                    if opportunity:
                        return opportunity
            
            # Check correlation-based opportunities
            correlation_opportunity = self._check_correlation_arbitrage(symbols_data)
            if correlation_opportunity:
                return correlation_opportunity
            
            return None
            
        except Exception as e:
            log_error("ArbitrageStrategy", "Error analyzing arbitrage opportunities", e)
            return None
    
    def _check_arbitrage_opportunity(self, pair_name: str, symbols: List[str], 
                                   symbols_data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Check for arbitrage opportunity between specific pairs"""
        try:
            symbol1, symbol2 = symbols
            data1 = symbols_data[symbol1]
            data2 = symbols_data[symbol2]
            
            if data1.empty or data2.empty or len(data1) < 20 or len(data2) < 20:
                return None
            
            # Get current prices
            price1 = data1['close'].iloc[-1]
            price2 = data2['close'].iloc[-1]
            
            # Calculate normalized prices and correlation
            returns1 = data1['close'].pct_change().dropna()
            returns2 = data2['close'].pct_change().dropna()
            
            if len(returns1) < 10 or len(returns2) < 10:
                return None
            
            # Align the series
            min_length = min(len(returns1), len(returns2))
            correlation = np.corrcoef(returns1.iloc[-min_length:], 
                                    returns2.iloc[-min_length:])[0, 1]
            
            if abs(correlation) < self.params['correlation_threshold']:
                return None
            
            # Calculate price ratio and check for divergence
            ratio_series = (data1['close'] / data2['close']).dropna()
            if len(ratio_series) < 20:
                return None
            
            current_ratio = ratio_series.iloc[-1]
            mean_ratio = ratio_series.rolling(20).mean().iloc[-1]
            std_ratio = ratio_series.rolling(20).std().iloc[-1]
            
            # Check for significant divergence
            z_score = (current_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0
            
            if abs(z_score) > 2:  # Significant divergence
                # Determine trade direction
                if z_score > 2:  # Ratio too high, short symbol1, long symbol2
                    action1, action2 = 'SELL', 'BUY'
                    confidence = min(0.95, 0.8 + abs(z_score) * 0.05)
                else:  # Ratio too low, long symbol1, short symbol2
                    action1, action2 = 'BUY', 'SELL'
                    confidence = min(0.95, 0.8 + abs(z_score) * 0.05)
                
                if confidence >= self.params['min_confidence']:
                    return {
                        'action': 'ARBITRAGE',
                        'pair_name': pair_name,
                        'symbol1': symbol1,
                        'symbol2': symbol2,
                        'action1': action1,
                        'action2': action2,
                        'confidence': confidence,
                        'z_score': z_score,
                        'correlation': correlation,
                        'current_ratio': current_ratio,
                        'mean_ratio': mean_ratio,
                        'strategy': self.name,
                        'timestamp': datetime.now(),
                        'entry_reason': f"Ratio divergence: {z_score:.2f} std devs"
                    }
            
            return None
            
        except Exception as e:
            log_error("ArbitrageStrategy", f"Error checking {pair_name} arbitrage", e)
            return None
    
    def _check_correlation_arbitrage(self, symbols_data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Check for correlation-based arbitrage opportunities"""
        try:
            symbols = list(symbols_data.keys())
            
            # Check all pairs of symbols
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    if symbol1 == symbol2:
                        continue
                    
                    data1 = symbols_data[symbol1]
                    data2 = symbols_data[symbol2]
                    
                    if data1.empty or data2.empty or len(data1) < 30 or len(data2) < 30:
                        continue
                    
                    # Calculate correlation
                    returns1 = data1['close'].pct_change().dropna()
                    returns2 = data2['close'].pct_change().dropna()
                    
                    min_length = min(len(returns1), len(returns2))
                    if min_length < 20:
                        continue
                    
                    correlation = np.corrcoef(returns1.iloc[-min_length:], 
                                           returns2.iloc[-min_length:])[0, 1]
                    
                    # Look for temporary correlation breakdown
                    short_correlation = np.corrcoef(returns1.iloc[-5:], 
                                                  returns2.iloc[-5:])[0, 1]
                    
                    if (abs(correlation) > self.params['correlation_threshold'] and 
                        abs(short_correlation) < 0.3):  # Correlation breakdown
                        
                        # Calculate expected vs actual price movement
                        recent_return1 = returns1.iloc[-1]
                        recent_return2 = returns2.iloc[-1]
                        
                        expected_return2 = recent_return1 * correlation
                        return_difference = recent_return2 - expected_return2
                        
                        if abs(return_difference) > 0.002:  # Significant difference
                            # Determine trade direction based on correlation
                            if correlation > 0:  # Positive correlation
                                if return_difference > 0:  # Symbol2 moved too much up
                                    action1, action2 = 'BUY', 'SELL'
                                else:  # Symbol2 moved too much down
                                    action1, action2 = 'SELL', 'BUY'
                            else:  # Negative correlation
                                if return_difference > 0:  # Symbol2 moved up (should move down)
                                    action1, action2 = 'SELL', 'SELL'
                                else:  # Symbol2 moved down (should move up)
                                    action1, action2 = 'BUY', 'BUY'
                            
                            confidence = min(0.9, 0.7 + abs(return_difference) * 100)
                            
                            if confidence >= self.params['min_confidence']:
                                return {
                                    'action': 'CORRELATION_ARBITRAGE',
                                    'pair_name': f"{symbol1}_{symbol2}",
                                    'symbol1': symbol1,
                                    'symbol2': symbol2,
                                    'action1': action1,
                                    'action2': action2,
                                    'confidence': confidence,
                                    'correlation': correlation,
                                    'short_correlation': short_correlation,
                                    'return_difference': return_difference,
                                    'strategy': self.name,
                                    'timestamp': datetime.now(),
                                    'entry_reason': f"Correlation breakdown: {correlation:.2f} vs {short_correlation:.2f}"
                                }
            
            return None
            
        except Exception as e:
            log_error("ArbitrageStrategy", "Error checking correlation arbitrage", e)
            return None
    
    def calculate_arbitrage_size(self, symbol1: str, symbol2: str, 
                               account_balance: float) -> Tuple[float, float]:
        """Calculate appropriate position sizes for arbitrage"""
        try:
            # Use smaller position sizes for arbitrage
            risk_amount = account_balance * (self.params['risk_per_trade'] / 100)
            
            # Simple equal risk allocation
            # In practice, this should consider contract sizes and correlations
            base_size = min(0.1, risk_amount / 1000)  # Conservative sizing
            
            return base_size, base_size
            
        except Exception as e:
            log_error("ArbitrageStrategy", "Error calculating arbitrage size", e)
            return 0.01, 0.01
    
    def on_arbitrage_opened(self, arbitrage_info: Dict[str, Any]):
        """Handle arbitrage position opened"""
        try:
            pair_name = arbitrage_info.get('pair_name')
            self.active_arbitrage[pair_name] = {
                'open_time': datetime.now(),
                'symbol1': arbitrage_info.get('symbol1'),
                'symbol2': arbitrage_info.get('symbol2'),
                'action1': arbitrage_info.get('action1'),
                'action2': arbitrage_info.get('action2'),
                'confidence': arbitrage_info.get('confidence')
            }
            
            self.arbitrage_count += 1
            
            log_info("ArbitrageStrategy", 
                    f"Arbitrage opened: {pair_name} - "
                    f"{arbitrage_info.get('symbol1')} {arbitrage_info.get('action1')}, "
                    f"{arbitrage_info.get('symbol2')} {arbitrage_info.get('action2')}")
            
        except Exception as e:
            log_error("ArbitrageStrategy", "Error handling arbitrage opened", e)
    
    def on_arbitrage_closed(self, arbitrage_info: Dict[str, Any]):
        """Handle arbitrage position closed"""
        try:
            pair_name = arbitrage_info.get('pair_name')
            if pair_name in self.active_arbitrage:
                del self.active_arbitrage[pair_name]
            
            total_profit = arbitrage_info.get('total_profit', 0)
            if total_profit > 0:
                self.successful_arbitrage += 1
            
            success_rate = (self.successful_arbitrage / self.arbitrage_count * 100) if self.arbitrage_count > 0 else 0
            
            log_info("ArbitrageStrategy", 
                    f"Arbitrage closed: {pair_name} - "
                    f"Total P&L: ${total_profit:.2f}, Success Rate: {success_rate:.1f}%")
            
        except Exception as e:
            log_error("ArbitrageStrategy", "Error handling arbitrage closed", e)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information and statistics"""
        try:
            success_rate = (self.successful_arbitrage / self.arbitrage_count * 100) if self.arbitrage_count > 0 else 0
            
            return {
                'name': self.name,
                'type': 'Arbitrage',
                'arbitrage_pairs': list(self.arbitrage_pairs.keys()),
                'total_arbitrage': self.arbitrage_count,
                'successful_arbitrage': self.successful_arbitrage,
                'success_rate': success_rate,
                'active_arbitrage': len(self.active_arbitrage),
                'max_positions': self.params['max_positions'],
                'min_spread_profit': self.params['min_spread_profit'],
                'correlation_threshold': self.params['correlation_threshold'],
                'status': 'Active' if len(self.active_arbitrage) < self.params['max_positions'] else 'Full'
            }
            
        except Exception as e:
            log_error("ArbitrageStrategy", "Error getting strategy info", e)
            return {'name': self.name, 'status': 'Error'}
    
    def reset_statistics(self):
        """Reset arbitrage statistics"""
        self.arbitrage_count = 0
        self.successful_arbitrage = 0
        log_info("ArbitrageStrategy", "Arbitrage statistics reset")
