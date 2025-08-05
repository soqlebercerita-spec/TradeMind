"""
Position sizing algorithms for optimal trade sizing
Implements Kelly Criterion, risk-based, and fixed sizing methods
"""

import math
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

from config.config import Config
from config.settings import Settings
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger

class PositionSizing:
    """Advanced position sizing algorithms"""
    
    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager):
        self.logger = Logger().get_logger()
        self.config = Config()
        self.settings = Settings()
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        
        # Historical performance tracking for Kelly Criterion
        self.trade_history = {}
        self.win_rates = {}
        self.avg_win_loss_ratios = {}
        
    def calculate_position_size(self, symbol: str, risk_amount: float, 
                              entry_price: float, stop_loss: float,
                              method: str = None) -> float:
        """Calculate optimal position size using specified method"""
        try:
            if method is None:
                method = self.settings.risk.position_sizing_method
            
            if method == 'fixed':
                return self._calculate_fixed_size(symbol)
            elif method == 'risk_based':
                return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
            elif method == 'kelly':
                return self._calculate_kelly_size(symbol, risk_amount, entry_price, stop_loss)
            elif method == 'volatility_adjusted':
                return self._calculate_volatility_adjusted_size(symbol, risk_amount, entry_price, stop_loss)
            elif method == 'correlation_adjusted':
                return self._calculate_correlation_adjusted_size(symbol, risk_amount, entry_price, stop_loss)
            else:
                self.logger.warning(f"Unknown position sizing method: {method}, using risk_based")
                return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
                
        except Exception as e:
            self.logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
    
    def _calculate_fixed_size(self, symbol: str) -> float:
        """Calculate fixed position size"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            # Fixed size based on symbol type
            if 'XAU' in symbol or 'GOLD' in symbol:
                return 0.1  # 0.1 lots for gold
            elif 'BTC' in symbol or 'crypto' in symbol.lower():
                return 0.01  # 0.01 lots for crypto
            else:
                return 0.01  # 0.01 lots for forex
                
        except Exception as e:
            self.logger.error(f"Error calculating fixed size for {symbol}: {e}")
            return 0.01
    
    def _calculate_risk_based_size(self, symbol: str, risk_amount: float,
                                 entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk amount"""
        try:
            if stop_loss <= 0 or entry_price <= 0 or risk_amount <= 0:
                return 0.0
            
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            # Calculate stop loss distance in price
            sl_distance = abs(entry_price - stop_loss)
            
            # Calculate pip value
            pip_value = self._calculate_pip_value(symbol, symbol_info)
            if pip_value <= 0:
                return 0.0
            
            # Convert price distance to pips
            point = symbol_info['point']
            sl_distance_pips = sl_distance / point
            
            # Adjust for 5/3 digit brokers
            if symbol_info['digits'] == 5 or symbol_info['digits'] == 3:
                sl_distance_pips /= 10
            
            # Calculate position size
            if sl_distance_pips > 0:
                position_size = risk_amount / (sl_distance_pips * pip_value)
            else:
                return 0.0
            
            # Apply limits
            position_size = self._apply_position_limits(symbol, position_size)
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating risk-based size for {symbol}: {e}")
            return 0.0
    
    def _calculate_kelly_size(self, symbol: str, risk_amount: float,
                            entry_price: float, stop_loss: float) -> float:
        """Calculate position size using Kelly Criterion"""
        try:
            # Get historical performance for this symbol
            win_rate = self._get_win_rate(symbol)
            avg_win_loss_ratio = self._get_avg_win_loss_ratio(symbol)
            
            if win_rate <= 0 or avg_win_loss_ratio <= 0:
                # Fall back to risk-based sizing if no history
                return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
            
            # Kelly formula: f = (bp - q) / b
            # where:
            # f = fraction of capital to wager
            # b = odds received on the wager (avg_win_loss_ratio)
            # p = probability of winning (win_rate)
            # q = probability of losing (1 - win_rate)
            
            b = avg_win_loss_ratio
            p = win_rate
            q = 1 - p
            
            kelly_fraction = (b * p - q) / b
            
            # Apply Kelly fraction limit for safety
            max_kelly_fraction = self.settings.risk.kelly_fraction
            kelly_fraction = min(kelly_fraction, max_kelly_fraction)
            kelly_fraction = max(kelly_fraction, 0.01)  # Minimum 1%
            
            # Get account equity
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0
            
            equity = account_info['equity']
            
            # Calculate Kelly risk amount
            kelly_risk_amount = equity * kelly_fraction
            
            # Use the minimum of Kelly risk and provided risk amount
            final_risk_amount = min(kelly_risk_amount, risk_amount)
            
            # Calculate position size using risk-based method with Kelly risk
            return self._calculate_risk_based_size(symbol, final_risk_amount, entry_price, stop_loss)
            
        except Exception as e:
            self.logger.error(f"Error calculating Kelly size for {symbol}: {e}")
            return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
    
    def _calculate_volatility_adjusted_size(self, symbol: str, risk_amount: float,
                                          entry_price: float, stop_loss: float) -> float:
        """Calculate position size adjusted for market volatility"""
        try:
            # Get ATR for volatility measurement
            rates = self.mt5_connector.get_rates(symbol, 60, 100)  # H1 timeframe, 100 periods
            if rates is None or len(rates) < 20:
                return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
            
            # Calculate ATR
            atr = self._calculate_atr(rates, 14)
            if atr <= 0:
                return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
            
            # Get current volatility relative to historical average
            avg_atr = atr.tail(50).mean()  # 50-period average ATR
            current_atr = atr.iloc[-1]
            
            volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
            
            # Adjust risk amount based on volatility
            # Reduce position size in high volatility, increase in low volatility
            if volatility_ratio > 1.5:  # High volatility
                adjusted_risk = risk_amount * 0.7  # Reduce by 30%
            elif volatility_ratio < 0.5:  # Low volatility
                adjusted_risk = risk_amount * 1.3  # Increase by 30%
            else:
                adjusted_risk = risk_amount
            
            # Calculate position size with adjusted risk
            return self._calculate_risk_based_size(symbol, adjusted_risk, entry_price, stop_loss)
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility-adjusted size for {symbol}: {e}")
            return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
    
    def _calculate_correlation_adjusted_size(self, symbol: str, risk_amount: float,
                                           entry_price: float, stop_loss: float) -> float:
        """Calculate position size adjusted for portfolio correlation"""
        try:
            # Get existing positions
            positions = self.mt5_connector.get_positions()
            if not positions:
                return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
            
            # Calculate correlation adjustment factor
            correlation_factor = self._calculate_portfolio_correlation(symbol, positions)
            
            # Adjust risk based on correlation
            # Higher correlation = lower position size
            if correlation_factor > 0.7:
                adjusted_risk = risk_amount * 0.5  # High correlation, reduce significantly
            elif correlation_factor > 0.4:
                adjusted_risk = risk_amount * 0.8  # Medium correlation, reduce moderately
            else:
                adjusted_risk = risk_amount  # Low correlation, no adjustment
            
            return self._calculate_risk_based_size(symbol, adjusted_risk, entry_price, stop_loss)
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation-adjusted size for {symbol}: {e}")
            return self._calculate_risk_based_size(symbol, risk_amount, entry_price, stop_loss)
    
    def _calculate_pip_value(self, symbol: str, symbol_info: Dict) -> float:
        """Calculate pip value for position sizing"""
        try:
            contract_size = symbol_info.get('trade_contract_size', 100000)
            point = symbol_info.get('point', 0.00001)
            
            # Adjust for 5/3 digit brokers
            if symbol_info['digits'] == 5 or symbol_info['digits'] == 3:
                pip_value = (point * 10) * contract_size
            else:
                pip_value = point * contract_size
            
            # For cross-currency pairs, we might need conversion
            # Simplified calculation for now
            return pip_value
            
        except Exception as e:
            self.logger.error(f"Error calculating pip value for {symbol}: {e}")
            return 0.0
    
    def _apply_position_limits(self, symbol: str, position_size: float) -> float:
        """Apply position size limits and constraints"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.01
            
            # Get symbol limits
            min_lot = symbol_info.get('volume_min', 0.01)
            max_lot = symbol_info.get('volume_max', 100.0)
            lot_step = symbol_info.get('volume_step', 0.01)
            
            # Round to lot step
            position_size = math.floor(position_size / lot_step) * lot_step
            
            # Apply min/max limits
            position_size = max(min_lot, min(position_size, max_lot))
            
            # Apply global position limits from settings
            max_position_global = self.config.POSITION_SETTINGS['max_lot_size']
            position_size = min(position_size, max_position_global)
            
            return round(position_size, 2)
            
        except Exception as e:
            self.logger.error(f"Error applying position limits for {symbol}: {e}")
            return 0.01
    
    def _calculate_atr(self, df, period: int = 14):
        """Calculate Average True Range"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # Calculate ATR using exponential moving average
            atr = tr.ewm(span=period).mean()
            
            return atr
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return None
    
    def _get_win_rate(self, symbol: str) -> float:
        """Get historical win rate for symbol"""
        try:
            if symbol not in self.win_rates:
                # Initialize with default value
                self.win_rates[symbol] = 0.5  # 50% default
            
            return self.win_rates[symbol]
            
        except Exception as e:
            self.logger.error(f"Error getting win rate for {symbol}: {e}")
            return 0.5
    
    def _get_avg_win_loss_ratio(self, symbol: str) -> float:
        """Get average win/loss ratio for symbol"""
        try:
            if symbol not in self.avg_win_loss_ratios:
                # Initialize with default value
                self.avg_win_loss_ratios[symbol] = 1.5  # 1.5:1 default
            
            return self.avg_win_loss_ratios[symbol]
            
        except Exception as e:
            self.logger.error(f"Error getting avg win/loss ratio for {symbol}: {e}")
            return 1.5
    
    def _calculate_portfolio_correlation(self, symbol: str, positions: List[Dict]) -> float:
        """Calculate correlation between new symbol and existing portfolio"""
        try:
            if not positions:
                return 0.0
            
            # Simplified correlation calculation
            # In production, you'd calculate actual price correlations
            
            # Define known correlations
            correlations = {
                'EURUSD': {'GBPUSD': 0.8, 'AUDUSD': 0.7, 'NZDUSD': 0.6},
                'GBPUSD': {'EURUSD': 0.8, 'EURGBP': -0.9, 'GBPJPY': 0.7},
                'USDJPY': {'EURJPY': 0.8, 'GBPJPY': 0.7, 'AUDJPY': 0.6},
                'XAUUSD': {'XAGUSD': 0.8, 'EURUSD': -0.3},  # Gold often inverse to USD
                'BTCUSD': {'ETHUSD': 0.9}  # Crypto correlations
            }
            
            max_correlation = 0.0
            
            for position in positions:
                pos_symbol = position['symbol']
                
                # Check direct correlation
                if symbol in correlations and pos_symbol in correlations[symbol]:
                    correlation = abs(correlations[symbol][pos_symbol])
                    max_correlation = max(max_correlation, correlation)
                elif pos_symbol in correlations and symbol in correlations[pos_symbol]:
                    correlation = abs(correlations[pos_symbol][symbol])
                    max_correlation = max(max_correlation, correlation)
                else:
                    # Default low correlation for unrelated pairs
                    max_correlation = max(max_correlation, 0.1)
            
            return max_correlation
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio correlation: {e}")
            return 0.0
    
    def update_trade_performance(self, symbol: str, profit: float, 
                               entry_price: float, exit_price: float):
        """Update trade performance statistics for Kelly Criterion"""
        try:
            if symbol not in self.trade_history:
                self.trade_history[symbol] = {'wins': [], 'losses': []}
            
            if profit > 0:
                # Winning trade
                win_amount = abs(profit)
                self.trade_history[symbol]['wins'].append(win_amount)
            else:
                # Losing trade
                loss_amount = abs(profit)
                self.trade_history[symbol]['losses'].append(loss_amount)
            
            # Update win rate
            total_trades = len(self.trade_history[symbol]['wins']) + len(self.trade_history[symbol]['losses'])
            wins = len(self.trade_history[symbol]['wins'])
            
            if total_trades > 0:
                self.win_rates[symbol] = wins / total_trades
            
            # Update average win/loss ratio
            if (len(self.trade_history[symbol]['wins']) > 0 and 
                len(self.trade_history[symbol]['losses']) > 0):
                
                avg_win = np.mean(self.trade_history[symbol]['wins'])
                avg_loss = np.mean(self.trade_history[symbol]['losses'])
                
                if avg_loss > 0:
                    self.avg_win_loss_ratios[symbol] = avg_win / avg_loss
            
            # Keep only recent history (last 100 trades)
            if len(self.trade_history[symbol]['wins']) > 100:
                self.trade_history[symbol]['wins'] = self.trade_history[symbol]['wins'][-100:]
            if len(self.trade_history[symbol]['losses']) > 100:
                self.trade_history[symbol]['losses'] = self.trade_history[symbol]['losses'][-100:]
            
        except Exception as e:
            self.logger.error(f"Error updating trade performance for {symbol}: {e}")
    
    def get_optimal_position_size(self, symbol: str, signal_strength: float,
                                market_conditions: Dict) -> float:
        """Get optimal position size considering multiple factors"""
        try:
            # Base risk calculation
            base_risk = self.risk_manager.calculate_risk_amount(symbol)
            
            # Adjust for signal strength
            signal_adjusted_risk = base_risk * signal_strength
            
            # Adjust for market conditions
            if market_conditions.get('volatility', 'normal') == 'high':
                volatility_adjustment = 0.7
            elif market_conditions.get('volatility', 'normal') == 'low':
                volatility_adjustment = 1.2
            else:
                volatility_adjustment = 1.0
            
            final_risk = signal_adjusted_risk * volatility_adjustment
            
            # Calculate position size (requires entry and stop loss prices)
            # This is a simplified version - in practice, you'd have these prices
            current_price = self.mt5_connector.get_current_price(symbol)
            if not current_price:
                return 0.0
            
            # Estimate stop loss at 1% of price (simplified)
            entry_price = current_price[1]  # Ask price
            stop_loss = entry_price * 0.99  # 1% stop loss
            
            return self.calculate_position_size(symbol, final_risk, entry_price, stop_loss)
            
        except Exception as e:
            self.logger.error(f"Error getting optimal position size for {symbol}: {e}")
            return 0.0
    
    def get_position_sizing_summary(self) -> Dict[str, any]:
        """Get position sizing statistics and summary"""
        try:
            summary = {
                'method': self.settings.risk.position_sizing_method,
                'kelly_fraction': self.settings.risk.kelly_fraction,
                'symbols_tracked': len(self.trade_history),
                'win_rates': self.win_rates.copy(),
                'avg_win_loss_ratios': self.avg_win_loss_ratios.copy(),
                'trade_counts': {}
            }
            
            # Calculate trade counts
            for symbol, history in self.trade_history.items():
                total_trades = len(history['wins']) + len(history['losses'])
                summary['trade_counts'][symbol] = {
                    'total': total_trades,
                    'wins': len(history['wins']),
                    'losses': len(history['losses'])
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting position sizing summary: {e}")
            return {}
