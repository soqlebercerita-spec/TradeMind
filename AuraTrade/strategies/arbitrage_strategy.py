
"""
Arbitrage Strategy for AuraTrade Bot
High-frequency arbitrage opportunities detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import Logger

class ArbitrageStrategy:
    """Arbitrage strategy for price differences exploitation"""
    
    def __init__(self, params: Dict = None):
        self.name = "Arbitrage"
        self.logger = Logger().get_logger()
        
        # Default parameters
        self.params = {
            'min_spread_pips': 2.0,
            'max_spread_pips': 10.0,
            'correlation_threshold': 0.8,
            'price_difference_threshold': 0.0001,
            'max_hold_time': 300,  # 5 minutes
            'symbols_pair': ['EURUSD', 'GBPUSD'],
            'volume': 0.01,
            'stop_loss_pips': 10,
            'take_profit_pips': 5
        }
        
        if params:
            self.params.update(params)
            
        self.active_opportunities = []
        self.correlation_data = {}
        self.price_history = {}
        
        self.logger.info(f"Arbitrage strategy initialized with params: {self.params}")
    
    def analyze_market(self, market_data: Dict) -> Dict[str, any]:
        """Analyze market for arbitrage opportunities"""
        try:
            signals = []
            opportunities = []
            
            # Update price history
            self._update_price_history(market_data)
            
            # Check for price discrepancies
            price_discrepancies = self._detect_price_discrepancies(market_data)
            
            # Check correlation arbitrage
            correlation_opps = self._detect_correlation_arbitrage(market_data)
            
            # Check cross-pair arbitrage
            cross_pair_opps = self._detect_cross_pair_arbitrage(market_data)
            
            opportunities.extend(price_discrepancies)
            opportunities.extend(correlation_opps)
            opportunities.extend(cross_pair_opps)
            
            # Generate signals from opportunities
            for opp in opportunities:
                if self._validate_opportunity(opp):
                    signals.append({
                        'action': opp['action'],
                        'symbol': opp['symbol'],
                        'confidence': opp['confidence'],
                        'reason': f"Arbitrage: {opp['type']}",
                        'entry_price': opp['entry_price'],
                        'stop_loss': opp['stop_loss'],
                        'take_profit': opp['take_profit'],
                        'volume': self.params['volume'],
                        'urgency': 'high',  # Arbitrage opportunities are time-sensitive
                        'max_hold_time': self.params['max_hold_time']
                    })
            
            return {
                'signals': signals,
                'opportunities': opportunities,
                'strategy': self.name,
                'timestamp': datetime.now(),
                'market_conditions': self._assess_market_conditions(market_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error in arbitrage market analysis: {e}")
            return {'signals': [], 'opportunities': []}
    
    def _update_price_history(self, market_data: Dict):
        """Update price history for analysis"""
        try:
            timestamp = datetime.now()
            
            for symbol, data in market_data.items():
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                
                # Add current price data
                self.price_history[symbol].append({
                    'timestamp': timestamp,
                    'bid': data.get('bid', 0),
                    'ask': data.get('ask', 0),
                    'spread': data.get('ask', 0) - data.get('bid', 0)
                })
                
                # Keep only last 1000 entries
                if len(self.price_history[symbol]) > 1000:
                    self.price_history[symbol] = self.price_history[symbol][-1000:]
                    
        except Exception as e:
            self.logger.error(f"Error updating price history: {e}")
    
    def _detect_price_discrepancies(self, market_data: Dict) -> List[Dict]:
        """Detect price discrepancies between similar instruments"""
        opportunities = []
        
        try:
            # Check for unusual spreads
            for symbol, data in market_data.items():
                current_spread = data.get('ask', 0) - data.get('bid', 0)
                
                if symbol in self.price_history and len(self.price_history[symbol]) > 10:
                    # Calculate average spread
                    recent_spreads = [h['spread'] for h in self.price_history[symbol][-10:]]
                    avg_spread = np.mean(recent_spreads)
                    
                    # If current spread is unusually wide, it might be an opportunity
                    if current_spread > avg_spread * 2:
                        opportunities.append({
                            'type': 'wide_spread',
                            'symbol': symbol,
                            'action': 'buy' if data.get('bid', 0) < avg_spread else 'sell',
                            'confidence': 0.7,
                            'entry_price': data.get('bid' if data.get('bid', 0) < avg_spread else 'ask', 0),
                            'stop_loss': data.get('bid', 0) - (self.params['stop_loss_pips'] * 0.0001),
                            'take_profit': data.get('ask', 0) + (self.params['take_profit_pips'] * 0.0001),
                            'expected_profit_pips': self.params['take_profit_pips']
                        })
                        
        except Exception as e:
            self.logger.error(f"Error detecting price discrepancies: {e}")
            
        return opportunities
    
    def _detect_correlation_arbitrage(self, market_data: Dict) -> List[Dict]:
        """Detect arbitrage opportunities based on correlation"""
        opportunities = []
        
        try:
            symbols = list(market_data.keys())
            
            # Check pairs for correlation arbitrage
            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    symbol1, symbol2 = symbols[i], symbols[j]
                    
                    # Calculate correlation if enough history
                    if (symbol1 in self.price_history and symbol2 in self.price_history and
                        len(self.price_history[symbol1]) > 20 and len(self.price_history[symbol2]) > 20):
                        
                        correlation = self._calculate_correlation(symbol1, symbol2)
                        
                        if abs(correlation) > self.params['correlation_threshold']:
                            # Check if prices are diverging from correlation
                            divergence = self._check_correlation_divergence(symbol1, symbol2, market_data)
                            
                            if divergence:
                                opportunities.append(divergence)
                                
        except Exception as e:
            self.logger.error(f"Error detecting correlation arbitrage: {e}")
            
        return opportunities
    
    def _detect_cross_pair_arbitrage(self, market_data: Dict) -> List[Dict]:
        """Detect triangular arbitrage opportunities"""
        opportunities = []
        
        try:
            # Example: EURUSD, GBPUSD, EURGBP
            required_pairs = ['EURUSD', 'GBPUSD', 'EURGBP']
            
            if all(pair in market_data for pair in required_pairs):
                eur_usd = market_data['EURUSD']
                gbp_usd = market_data['GBPUSD']
                eur_gbp = market_data['EURGBP']
                
                # Calculate synthetic EURGBP from EURUSD/GBPUSD
                synthetic_eur_gbp = eur_usd.get('bid', 0) / gbp_usd.get('ask', 0)
                actual_eur_gbp = eur_gbp.get('bid', 0)
                
                # Check for arbitrage opportunity
                price_diff = abs(synthetic_eur_gbp - actual_eur_gbp)
                
                if price_diff > self.params['price_difference_threshold']:
                    if synthetic_eur_gbp > actual_eur_gbp:
                        # Buy EURGBP, sell synthetic
                        opportunities.append({
                            'type': 'triangular_arbitrage',
                            'symbol': 'EURGBP',
                            'action': 'buy',
                            'confidence': 0.8,
                            'entry_price': actual_eur_gbp,
                            'stop_loss': actual_eur_gbp - (self.params['stop_loss_pips'] * 0.0001),
                            'take_profit': synthetic_eur_gbp,
                            'expected_profit_pips': price_diff * 10000
                        })
                    else:
                        # Sell EURGBP, buy synthetic
                        opportunities.append({
                            'type': 'triangular_arbitrage',
                            'symbol': 'EURGBP',
                            'action': 'sell',
                            'confidence': 0.8,
                            'entry_price': actual_eur_gbp,
                            'stop_loss': actual_eur_gbp + (self.params['stop_loss_pips'] * 0.0001),
                            'take_profit': synthetic_eur_gbp,
                            'expected_profit_pips': price_diff * 10000
                        })
                        
        except Exception as e:
            self.logger.error(f"Error detecting cross pair arbitrage: {e}")
            
        return opportunities
    
    def _calculate_correlation(self, symbol1: str, symbol2: str) -> float:
        """Calculate price correlation between two symbols"""
        try:
            if (symbol1 not in self.price_history or symbol2 not in self.price_history or
                len(self.price_history[symbol1]) < 20 or len(self.price_history[symbol2]) < 20):
                return 0.0
            
            # Get last 20 mid prices for each symbol
            prices1 = [(h['bid'] + h['ask']) / 2 for h in self.price_history[symbol1][-20:]]
            prices2 = [(h['bid'] + h['ask']) / 2 for h in self.price_history[symbol2][-20:]]
            
            # Calculate percentage changes
            changes1 = np.diff(prices1) / prices1[:-1]
            changes2 = np.diff(prices2) / prices2[:-1]
            
            # Calculate correlation
            correlation = np.corrcoef(changes1, changes2)[0, 1]
            
            return correlation if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return 0.0
    
    def _check_correlation_divergence(self, symbol1: str, symbol2: str, market_data: Dict) -> Optional[Dict]:
        """Check if correlated pairs are diverging"""
        try:
            correlation = self._calculate_correlation(symbol1, symbol2)
            
            if abs(correlation) < self.params['correlation_threshold']:
                return None
            
            # Get current price changes
            if (len(self.price_history[symbol1]) > 1 and len(self.price_history[symbol2]) > 1):
                
                # Calculate recent price movements
                price1_change = ((market_data[symbol1]['bid'] + market_data[symbol1]['ask']) / 2 - 
                               (self.price_history[symbol1][-2]['bid'] + self.price_history[symbol1][-2]['ask']) / 2)
                
                price2_change = ((market_data[symbol2]['bid'] + market_data[symbol2]['ask']) / 2 - 
                               (self.price_history[symbol2][-2]['bid'] + self.price_history[symbol2][-2]['ask']) / 2)
                
                # Check if movements are diverging from expected correlation
                expected_direction = 1 if correlation > 0 else -1
                actual_direction = 1 if (price1_change * price2_change) > 0 else -1
                
                if expected_direction != actual_direction and abs(price1_change) > self.params['price_difference_threshold']:
                    # Arbitrage opportunity detected
                    stronger_symbol = symbol1 if abs(price1_change) > abs(price2_change) else symbol2
                    weaker_symbol = symbol2 if stronger_symbol == symbol1 else symbol1
                    
                    return {
                        'type': 'correlation_divergence',
                        'symbol': weaker_symbol,
                        'action': 'buy' if price1_change < 0 else 'sell',
                        'confidence': min(0.9, abs(correlation)),
                        'entry_price': market_data[weaker_symbol]['ask' if price1_change < 0 else 'bid'],
                        'stop_loss': market_data[weaker_symbol]['ask' if price1_change < 0 else 'bid'] * (1 + (self.params['stop_loss_pips'] * 0.0001)),
                        'take_profit': market_data[weaker_symbol]['ask' if price1_change < 0 else 'bid'] * (1 + (self.params['take_profit_pips'] * 0.0001)),
                        'expected_profit_pips': self.params['take_profit_pips']
                    }
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking correlation divergence: {e}")
            return None
    
    def _validate_opportunity(self, opportunity: Dict) -> bool:
        """Validate arbitrage opportunity"""
        try:
            # Check minimum profit threshold
            if opportunity.get('expected_profit_pips', 0) < self.params['min_spread_pips']:
                return False
            
            # Check maximum risk
            if opportunity.get('expected_profit_pips', 0) > self.params['max_spread_pips']:
                return False
            
            # Check confidence level
            if opportunity.get('confidence', 0) < 0.6:
                return False
            
            # Check if opportunity is not too stale
            if hasattr(opportunity, 'timestamp'):
                age = datetime.now() - opportunity['timestamp']
                if age.total_seconds() > 10:  # 10 seconds max
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating opportunity: {e}")
            return False
    
    def _assess_market_conditions(self, market_data: Dict) -> Dict[str, any]:
        """Assess current market conditions for arbitrage"""
        try:
            conditions = {
                'volatility': 'medium',
                'spread_conditions': 'normal',
                'arbitrage_opportunities': len(self.active_opportunities),
                'market_hours': self._get_market_session(),
                'recommended_exposure': self.params['volume']
            }
            
            # Calculate average spreads
            total_spread = 0
            symbol_count = 0
            
            for symbol, data in market_data.items():
                spread = data.get('ask', 0) - data.get('bid', 0)
                total_spread += spread
                symbol_count += 1
            
            if symbol_count > 0:
                avg_spread = total_spread / symbol_count
                if avg_spread > 0.0003:  # 3 pips average
                    conditions['spread_conditions'] = 'wide'
                elif avg_spread < 0.0001:  # 1 pip average
                    conditions['spread_conditions'] = 'tight'
            
            return conditions
            
        except Exception as e:
            self.logger.error(f"Error assessing market conditions: {e}")
            return {'volatility': 'unknown', 'spread_conditions': 'unknown'}
    
    def _get_market_session(self) -> str:
        """Determine current market session"""
        try:
            now = datetime.now()
            hour = now.hour
            
            # Simplified market sessions (UTC)
            if 22 <= hour or hour < 6:
                return 'sydney'
            elif 6 <= hour < 8:
                return 'tokyo_open'
            elif 8 <= hour < 14:
                return 'london'
            elif 14 <= hour < 22:
                return 'new_york'
            else:
                return 'off_hours'
                
        except:
            return 'unknown'
    
    def get_strategy_info(self) -> Dict[str, any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Arbitrage',
            'description': 'High-frequency arbitrage opportunities detection',
            'risk_level': 'Low-Medium',
            'avg_trade_duration': f"{self.params['max_hold_time']} seconds",
            'profit_target': f"{self.params['take_profit_pips']} pips",
            'stop_loss': f"{self.params['stop_loss_pips']} pips",
            'active_opportunities': len(self.active_opportunities),
            'pairs_monitored': self.params['symbols_pair']
        }
"""
Arbitrage Strategy for AuraTrade Bot
Price difference exploitation strategy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from utils.logger import Logger

class ArbitrageStrategy:
    """Arbitrage trading strategy"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Arbitrage"
        self.timeframe = "M1"
        
        # Strategy parameters
        self.max_spread = 2.0
        self.tp_pips = 5
        self.sl_pips = 10
        
        self.logger.info("Arbitrage Strategy initialized")
    
    def analyze(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Optional[Dict]:
        """Analyze arbitrage opportunities"""
        try:
            if len(rates) < 10:
                return None
            
            # Basic arbitrage logic placeholder
            return None  # Requires multiple brokers
            
        except Exception as e:
            self.logger.error(f"Error in arbitrage analysis: {e}")
            return None
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'timeframe': self.timeframe,
            'tp_pips': self.tp_pips,
            'sl_pips': self.sl_pips,
            'max_spread': self.max_spread,
            'risk_level': 'Low',
            'description': 'Arbitrage trading strategy'
        }
