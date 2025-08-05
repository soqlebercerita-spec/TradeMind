
"""
Position Sizing Module for AuraTrade Bot
Advanced position sizing based on risk management
"""

import math
from typing import Dict, Optional, Any
from utils.logger import Logger, log_info, log_error

class PositionSizing:
    """Advanced position sizing with risk-based calculations"""
    
    def __init__(self, mt5_connector, risk_manager):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        
        # Position sizing parameters
        self.params = {
            'default_risk_percent': 1.0,  # 1% risk per trade
            'max_risk_percent': 2.0,      # Maximum 2% risk
            'min_lot_size': 0.01,         # Minimum position size
            'max_lot_size': 10.0,         # Maximum position size
            'kelly_enabled': True,        # Use Kelly criterion
            'volatility_adjustment': True  # Adjust for volatility
        }
        
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: float, risk_percent: Optional[float] = None) -> float:
        """Calculate optimal position size based on risk"""
        try:
            # Get account info
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return self.params['min_lot_size']
            
            balance = account_info.get('balance', 0)
            if balance <= 0:
                return self.params['min_lot_size']
            
            # Use provided risk or default
            risk_pct = risk_percent or self.params['default_risk_percent']
            risk_pct = min(risk_pct, self.params['max_risk_percent'])
            
            # Calculate risk amount
            risk_amount = balance * (risk_pct / 100)
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return self.params['min_lot_size']
            
            # Calculate stop loss distance in price
            stop_distance = abs(entry_price - stop_loss)
            if stop_distance <= 0:
                return self.params['min_lot_size']
            
            # Calculate pip value and position size
            pip_value = self._calculate_pip_value(symbol, symbol_info)
            stop_distance_pips = stop_distance / symbol_info.get('point', 0.00001)
            
            if pip_value > 0 and stop_distance_pips > 0:
                position_size = risk_amount / (stop_distance_pips * pip_value)
            else:
                position_size = self.params['min_lot_size']
            
            # Apply Kelly criterion adjustment if enabled
            if self.params['kelly_enabled']:
                kelly_adjustment = self._calculate_kelly_adjustment(symbol)
                position_size *= kelly_adjustment
            
            # Apply volatility adjustment
            if self.params['volatility_adjustment']:
                volatility_adjustment = self._calculate_volatility_adjustment(symbol)
                position_size *= volatility_adjustment
            
            # Apply limits
            position_size = max(self.params['min_lot_size'], position_size)
            position_size = min(self.params['max_lot_size'], position_size)
            
            # Round to valid lot size
            position_size = self._round_to_valid_lot_size(position_size, symbol_info)
            
            log_info("PositionSizing", 
                    f"{symbol}: Risk=${risk_amount:.2f}, Size={position_size:.2f} lots, "
                    f"Stop={stop_distance_pips:.1f} pips")
            
            return position_size
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating position size for {symbol}", e)
            return self.params['min_lot_size']
    
    def calculate_dynamic_position_size(self, symbol: str, signal_strength: float, 
                                      confidence: float) -> float:
        """Calculate position size based on signal strength and confidence"""
        try:
            # Base risk adjustment based on signal strength and confidence
            base_risk = self.params['default_risk_percent']
            
            # Adjust risk based on signal strength (0.0 to 1.0)
            strength_multiplier = 0.5 + (signal_strength * 0.5)  # 0.5x to 1.0x
            
            # Adjust risk based on confidence (0.0 to 1.0)
            confidence_multiplier = 0.3 + (confidence * 0.7)  # 0.3x to 1.0x
            
            # Combined risk percentage
            adjusted_risk = base_risk * strength_multiplier * confidence_multiplier
            adjusted_risk = min(adjusted_risk, self.params['max_risk_percent'])
            
            # Get current price for stop loss calculation
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return self.params['min_lot_size']
            
            current_price = tick.get('bid', 0)
            
            # Estimate stop loss based on volatility
            estimated_stop_loss_pips = self._estimate_stop_loss_pips(symbol)
            point = self.mt5_connector.get_symbol_info(symbol).get('point', 0.00001)
            stop_loss_price = current_price - (estimated_stop_loss_pips * point)
            
            return self.calculate_position_size(symbol, current_price, stop_loss_price, adjusted_risk)
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating dynamic position size for {symbol}", e)
            return self.params['min_lot_size']
    
    def _calculate_pip_value(self, symbol: str, symbol_info: Dict[str, Any]) -> float:
        """Calculate pip value for the symbol"""
        try:
            contract_size = symbol_info.get('contract_size', 100000)
            point = symbol_info.get('point', 0.00001)
            
            # Get current price for cross-currency calculations
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return 1.0
            
            current_price = tick.get('bid', 1.0)
            
            # Calculate pip value based on symbol type
            if symbol.endswith('USD'):
                # Direct quote (XXX/USD)
                pip_value = contract_size * point
            elif symbol.startswith('USD'):
                # Indirect quote (USD/XXX)
                pip_value = (contract_size * point) / current_price
            else:
                # Cross currency - approximate
                pip_value = contract_size * point
            
            return pip_value
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating pip value for {symbol}", e)
            return 1.0
    
    def _calculate_kelly_adjustment(self, symbol: str) -> float:
        """Calculate Kelly criterion adjustment"""
        try:
            # Get historical performance for the symbol
            # This is a simplified Kelly calculation
            win_rate = 0.65  # Assume 65% win rate - should be calculated from history
            avg_win_loss_ratio = 1.5  # Assume 1.5:1 win/loss ratio
            
            # Kelly formula: f = (bp - q) / b
            # where b = odds (win/loss ratio), p = win probability, q = loss probability
            p = win_rate
            q = 1 - win_rate
            b = avg_win_loss_ratio
            
            kelly_fraction = (b * p - q) / b
            
            # Conservative Kelly (use 25% of full Kelly)
            kelly_adjustment = max(0.1, min(1.0, kelly_fraction * 0.25))
            
            return kelly_adjustment
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating Kelly adjustment for {symbol}", e)
            return 0.5
    
    def _calculate_volatility_adjustment(self, symbol: str) -> float:
        """Calculate volatility-based position size adjustment"""
        try:
            # Get recent price data to calculate volatility
            # This is simplified - in practice, use historical data
            
            # Assume different volatility levels for different instruments
            volatility_adjustments = {
                'EURUSD': 1.0,   # Base volatility
                'GBPUSD': 0.9,   # Slightly more volatile
                'USDJPY': 0.95,
                'XAUUSD': 0.7,   # Much more volatile
                'XAGUSD': 0.6,
                'BTCUSD': 0.3,   # Extremely volatile
                'ETHUSD': 0.4
            }
            
            # Default adjustment if symbol not found
            adjustment = volatility_adjustments.get(symbol, 0.8)
            
            return adjustment
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating volatility adjustment for {symbol}", e)
            return 0.8
    
    def _estimate_stop_loss_pips(self, symbol: str) -> float:
        """Estimate appropriate stop loss in pips based on volatility"""
        try:
            # Symbol-specific stop loss estimates
            stop_loss_pips = {
                'EURUSD': 20,
                'GBPUSD': 25,
                'USDJPY': 20,
                'USDCHF': 20,
                'AUDUSD': 25,
                'USDCAD': 25,
                'NZDUSD': 30,
                'XAUUSD': 500,   # Gold in points
                'XAGUSD': 50,    # Silver in points
                'BTCUSD': 1000,  # Bitcoin
                'ETHUSD': 100    # Ethereum
            }
            
            return stop_loss_pips.get(symbol, 25)
            
        except Exception as e:
            log_error("PositionSizing", f"Error estimating stop loss for {symbol}", e)
            return 25
    
    def _round_to_valid_lot_size(self, position_size: float, symbol_info: Dict[str, Any]) -> float:
        """Round position size to valid lot size increments"""
        try:
            # Most brokers use 0.01 lot increments
            lot_step = 0.01
            
            # Round to nearest valid step
            rounded_size = round(position_size / lot_step) * lot_step
            
            return max(self.params['min_lot_size'], rounded_size)
            
        except Exception as e:
            log_error("PositionSizing", f"Error rounding lot size", e)
            return self.params['min_lot_size']
    
    def get_max_position_size(self, symbol: str) -> float:
        """Get maximum allowed position size for symbol"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return self.params['min_lot_size']
            
            # Calculate max size based on maximum risk
            balance = account_info.get('balance', 0)
            max_risk = balance * (self.params['max_risk_percent'] / 100)
            
            # Estimate minimum stop loss for max calculation
            min_stop_pips = self._estimate_stop_loss_pips(symbol) * 0.5
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            pip_value = self._calculate_pip_value(symbol, symbol_info)
            
            if pip_value > 0 and min_stop_pips > 0:
                max_size = max_risk / (min_stop_pips * pip_value)
                max_size = min(max_size, self.params['max_lot_size'])
            else:
                max_size = self.params['max_lot_size']
            
            return max_size
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating max position size for {symbol}", e)
            return self.params['max_lot_size']
