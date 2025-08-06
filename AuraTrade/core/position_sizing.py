
"""
Position Sizing Module for AuraTrade Bot
Advanced position sizing based on risk management and market conditions
"""

import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger, log_error

class PositionSizing:
    """Advanced position sizing with multiple calculation methods"""
    
    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        
        # Position sizing parameters
        self.sizing_params = {
            'default_risk_percent': 1.0,     # 1% risk per trade
            'min_volume': 0.01,              # Minimum lot size
            'max_volume': 1.0,               # Maximum lot size
            'volume_step': 0.01,             # Volume increment
            'conservative_mode': True,       # Conservative sizing
            'volatility_adjustment': True,   # Adjust for volatility
            'correlation_adjustment': True,  # Adjust for correlation
        }
        
        # Volatility tracking
        self.symbol_volatility = {}
        self.last_volatility_update = {}
        
        self.logger.info("Position Sizing module initialized")
    
    def calculate_position_size(self, symbol: str, stop_loss_pips: float, 
                               risk_percent: float = None) -> float:
        """Calculate optimal position size based on risk and market conditions"""
        try:
            # Use default risk if not specified
            if risk_percent is None:
                risk_percent = self.sizing_params['default_risk_percent']
            
            # Get account information
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                self.logger.error("Cannot get account info for position sizing")
                return 0.0
            
            # Get symbol information
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"Cannot get symbol info for {symbol}")
                return 0.0
            
            # Basic position size calculation
            base_volume = self._calculate_base_volume(
                account_info, symbol_info, stop_loss_pips, risk_percent
            )
            
            if base_volume <= 0:
                return 0.0
            
            # Apply adjustments
            adjusted_volume = base_volume
            
            # Volatility adjustment
            if self.sizing_params['volatility_adjustment']:
                vol_adjustment = self._get_volatility_adjustment(symbol)
                adjusted_volume *= vol_adjustment
            
            # Correlation adjustment
            if self.sizing_params['correlation_adjustment']:
                corr_adjustment = self._get_correlation_adjustment(symbol)
                adjusted_volume *= corr_adjustment
            
            # Conservative mode adjustment
            if self.sizing_params['conservative_mode']:
                adjusted_volume *= 0.8  # 20% reduction for safety
            
            # Normalize volume
            final_volume = self._normalize_volume(adjusted_volume, symbol_info)
            
            self.logger.info(f"Position size for {symbol}: {final_volume:.2f} lots (Risk: {risk_percent}%, SL: {stop_loss_pips} pips)")
            
            return final_volume
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating position size: {e}", e)
            return 0.0
    
    def _calculate_base_volume(self, account_info: Dict, symbol_info: Dict, 
                              stop_loss_pips: float, risk_percent: float) -> float:
        """Calculate base position size using risk-based formula"""
        try:
            balance = account_info.get('balance', 0)
            if balance <= 0:
                return 0.0
            
            # Risk amount in account currency
            risk_amount = balance * (risk_percent / 100.0)
            
            # Get pip value
            pip_value = self._calculate_pip_value(symbol_info, balance)
            if pip_value <= 0:
                return 0.0
            
            # Calculate position size
            # Volume = Risk Amount / (Stop Loss Pips × Pip Value)
            volume = risk_amount / (stop_loss_pips * pip_value)
            
            return max(volume, 0.0)
            
        except Exception as e:
            log_error("PositionSizing", f"Error in base volume calculation: {e}", e)
            return 0.0
    
    def _calculate_pip_value(self, symbol_info: Dict, account_balance: float) -> float:
        """Calculate pip value for position sizing"""
        try:
            symbol = symbol_info.get('symbol', '')
            point = symbol_info.get('point', 0.0001)
            contract_size = symbol_info.get('contract_size', 100000)
            
            # For JPY pairs, pip is 0.01, for others 0.0001
            if 'JPY' in symbol:
                pip_size = point * 100
            else:
                pip_size = point * 10
            
            # Pip value for 1 lot
            pip_value = pip_size * contract_size
            
            # Convert to account currency if needed
            # For now, assuming USD account
            return pip_value
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating pip value: {e}", e)
            return 10.0  # Default fallback
    
    def _get_volatility_adjustment(self, symbol: str) -> float:
        """Get volatility-based adjustment factor"""
        try:
            # Update volatility if needed
            self._update_symbol_volatility(symbol)
            
            volatility = self.symbol_volatility.get(symbol, 1.0)
            
            # Adjust position size based on volatility
            # Higher volatility = smaller position
            if volatility > 2.0:
                return 0.5  # High volatility - reduce by 50%
            elif volatility > 1.5:
                return 0.7  # Medium-high volatility - reduce by 30%
            elif volatility > 1.0:
                return 0.85  # Medium volatility - reduce by 15%
            elif volatility < 0.5:
                return 1.2  # Low volatility - increase by 20%
            else:
                return 1.0  # Normal volatility
                
        except Exception as e:
            log_error("PositionSizing", f"Error getting volatility adjustment: {e}", e)
            return 1.0
    
    def _update_symbol_volatility(self, symbol: str):
        """Update volatility data for symbol"""
        try:
            current_time = datetime.now()
            
            # Check if update is needed (every 5 minutes)
            if symbol in self.last_volatility_update:
                time_diff = current_time - self.last_volatility_update[symbol]
                if time_diff.total_seconds() < 300:  # 5 minutes
                    return
            
            # Get historical data
            rates = self.mt5_connector.get_rates(symbol, 1, 0, 50)  # 50 periods
            if rates is None or len(rates) < 20:
                return
            
            # Calculate volatility (standard deviation of returns)
            returns = rates['close'].pct_change().dropna()
            volatility = returns.std() * 100  # As percentage
            
            self.symbol_volatility[symbol] = volatility
            self.last_volatility_update[symbol] = current_time
            
            self.logger.debug(f"Updated volatility for {symbol}: {volatility:.2f}%")
            
        except Exception as e:
            log_error("PositionSizing", f"Error updating volatility for {symbol}: {e}", e)
    
    def _get_correlation_adjustment(self, symbol: str) -> float:
        """Get correlation-based adjustment factor"""
        try:
            positions = self.mt5_connector.get_positions()
            if not positions:
                return 1.0
            
            # Define currency correlation groups
            correlation_groups = {
                'EUR_STRONG': ['EURUSD', 'EURJPY', 'EURGBP'],
                'USD_STRONG': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'JPY_STRONG': ['USDJPY', 'EURJPY', 'GBPJPY'],
                'COMMODITY': ['XAUUSD', 'XAGUSD', 'BTCUSD']
            }
            
            # Count correlated positions
            correlated_count = 0
            for position in positions:
                pos_symbol = position['symbol']
                
                # Check if current symbol and position symbol are in same group
                for group_symbols in correlation_groups.values():
                    if symbol in group_symbols and pos_symbol in group_symbols:
                        correlated_count += 1
                        break
            
            # Reduce position size based on correlation
            if correlated_count >= 3:
                return 0.3  # Strong correlation - reduce by 70%
            elif correlated_count == 2:
                return 0.5  # Medium correlation - reduce by 50%
            elif correlated_count == 1:
                return 0.7  # Some correlation - reduce by 30%
            else:
                return 1.0  # No correlation
                
        except Exception as e:
            log_error("PositionSizing", f"Error getting correlation adjustment: {e}", e)
            return 1.0
    
    def _normalize_volume(self, volume: float, symbol_info: Dict) -> float:
        """Normalize volume to valid trading size"""
        try:
            min_volume = self.sizing_params['min_volume']
            max_volume = self.sizing_params['max_volume']
            volume_step = self.sizing_params['volume_step']
            
            # Apply min/max limits
            volume = max(min_volume, min(volume, max_volume))
            
            # Round to valid step
            volume = round(volume / volume_step) * volume_step
            
            # Ensure minimum volume
            if volume < min_volume:
                volume = min_volume
            
            return round(volume, 2)
            
        except Exception as e:
            log_error("PositionSizing", f"Error normalizing volume: {e}", e)
            return self.sizing_params['min_volume']
    
    def calculate_risk_for_volume(self, symbol: str, volume: float, 
                                 stop_loss_pips: float) -> float:
        """Calculate risk percentage for given volume and stop loss"""
        try:
            account_info = self.mt5_connector.get_account_info()
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            
            if not account_info or not symbol_info:
                return 0.0
            
            balance = account_info.get('balance', 0)
            if balance <= 0:
                return 0.0
            
            # Calculate pip value
            pip_value = self._calculate_pip_value(symbol_info, balance)
            
            # Calculate risk amount
            risk_amount = volume * stop_loss_pips * pip_value
            
            # Convert to percentage
            risk_percent = (risk_amount / balance) * 100
            
            return risk_percent
            
        except Exception as e:
            log_error("PositionSizing", f"Error calculating risk for volume: {e}", e)
            return 0.0
    
    def get_optimal_volume_for_risk(self, symbol: str, target_risk_percent: float, 
                                   stop_loss_pips: float) -> float:
        """Get optimal volume for specific risk percentage"""
        try:
            # Calculate base volume for target risk
            base_volume = self.calculate_position_size(symbol, stop_loss_pips, target_risk_percent)
            
            # Verify the actual risk
            actual_risk = self.calculate_risk_for_volume(symbol, base_volume, stop_loss_pips)
            
            # Adjust if needed
            if actual_risk > target_risk_percent * 1.1:  # 10% tolerance
                adjustment_factor = target_risk_percent / actual_risk
                base_volume *= adjustment_factor
                
                # Normalize again
                symbol_info = self.mt5_connector.get_symbol_info(symbol)
                if symbol_info:
                    base_volume = self._normalize_volume(base_volume, symbol_info)
            
            return base_volume
            
        except Exception as e:
            log_error("PositionSizing", f"Error getting optimal volume: {e}", e)
            return 0.0
    
    def get_position_value(self, symbol: str, volume: float) -> Dict[str, float]:
        """Get position value information"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            tick = self.mt5_connector.get_tick(symbol)
            
            if not symbol_info or not tick:
                return {}
            
            contract_size = symbol_info.get('contract_size', 100000)
            current_price = tick.get('bid', 0)
            
            # Calculate position value
            position_value = volume * contract_size
            notional_value = position_value * current_price
            
            # Calculate pip value
            pip_value = self._calculate_pip_value(symbol_info, 10000)  # Per $10k
            position_pip_value = pip_value * volume
            
            return {
                'volume': volume,
                'position_value': position_value,
                'notional_value': notional_value,
                'pip_value': position_pip_value,
                'current_price': current_price
            }
            
        except Exception as e:
            log_error("PositionSizing", f"Error getting position value: {e}", e)
            return {}
    
    def update_sizing_parameters(self, new_params: Dict[str, Any]):
        """Update position sizing parameters"""
        try:
            for key, value in new_params.items():
                if key in self.sizing_params:
                    old_value = self.sizing_params[key]
                    self.sizing_params[key] = value
                    self.logger.info(f"Sizing parameter {key} updated: {old_value} -> {value}")
                else:
                    self.logger.warning(f"Unknown sizing parameter: {key}")
                    
        except Exception as e:
            log_error("PositionSizing", f"Error updating sizing parameters: {e}", e)
    
    def get_sizing_recommendation(self, symbol: str, stop_loss_pips: float) -> Dict[str, Any]:
        """Get comprehensive position sizing recommendation"""
        try:
            # Calculate different risk levels
            conservative_volume = self.calculate_position_size(symbol, stop_loss_pips, 0.5)
            normal_volume = self.calculate_position_size(symbol, stop_loss_pips, 1.0)
            aggressive_volume = self.calculate_position_size(symbol, stop_loss_pips, 2.0)
            
            # Get current market conditions
            volatility = self.symbol_volatility.get(symbol, 1.0)
            vol_adjustment = self._get_volatility_adjustment(symbol)
            corr_adjustment = self._get_correlation_adjustment(symbol)
            
            recommendation = {
                'symbol': symbol,
                'stop_loss_pips': stop_loss_pips,
                'volumes': {
                    'conservative': conservative_volume,
                    'normal': normal_volume,
                    'aggressive': aggressive_volume
                },
                'recommended': normal_volume,  # Default recommendation
                'market_conditions': {
                    'volatility': volatility,
                    'volatility_adjustment': vol_adjustment,
                    'correlation_adjustment': corr_adjustment
                },
                'risk_analysis': {
                    'conservative_risk': self.calculate_risk_for_volume(symbol, conservative_volume, stop_loss_pips),
                    'normal_risk': self.calculate_risk_for_volume(symbol, normal_volume, stop_loss_pips),
                    'aggressive_risk': self.calculate_risk_for_volume(symbol, aggressive_volume, stop_loss_pips)
                }
            }
            
            # Adjust recommendation based on conditions
            if vol_adjustment < 0.7:  # High volatility
                recommendation['recommended'] = conservative_volume
                recommendation['reason'] = 'High volatility detected - using conservative sizing'
            elif corr_adjustment < 0.7:  # High correlation
                recommendation['recommended'] = conservative_volume
                recommendation['reason'] = 'High correlation with existing positions - using conservative sizing'
            else:
                recommendation['reason'] = 'Normal market conditions - using standard sizing'
            
            return recommendation
            
        except Exception as e:
            log_error("PositionSizing", f"Error getting sizing recommendation: {e}", e)
            return {}
"""
Position Sizing Calculator for AuraTrade Bot
Dynamic lot size calculation based on risk management
"""

from typing import Dict, Optional
from utils.logger import Logger

class PositionSizing:
    """Dynamic position sizing based on risk management"""
    
    def __init__(self, mt5_connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Default settings
        self.default_risk_percent = 1.0  # 1% risk per trade
        self.min_lot_size = 0.01
        self.max_lot_size = 10.0
        
        self.logger.info("Position Sizing initialized")
    
    def calculate_position_size(self, symbol: str, risk_percent: float = None, 
                              stop_loss_pips: float = 20) -> float:
        """Calculate optimal position size based on risk"""
        try:
            if risk_percent is None:
                risk_percent = self.default_risk_percent
            
            # Get account info
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return self.min_lot_size
            
            balance = account_info.get('balance', 0)
            if balance <= 0:
                return self.min_lot_size
            
            # Calculate risk amount in USD
            risk_amount = balance * (risk_percent / 100)
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return self.min_lot_size
            
            # Calculate pip value
            pip_value = self.calculate_pip_value(symbol)
            if pip_value <= 0:
                return self.min_lot_size
            
            # Calculate position size
            # Position Size = Risk Amount / (Stop Loss in Pips * Pip Value)
            calculated_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Apply limits
            calculated_size = max(self.min_lot_size, calculated_size)
            calculated_size = min(self.max_lot_size, calculated_size)
            
            # Round to symbol's volume step
            volume_step = symbol_info.get('volume_step', 0.01)
            calculated_size = round(calculated_size / volume_step) * volume_step
            
            self.logger.info(f"Calculated position size for {symbol}: {calculated_size:.2f}")
            return calculated_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return self.min_lot_size
    
    def calculate_pip_value(self, symbol: str) -> float:
        """Calculate pip value for the symbol"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 1.0
            
            # Get current tick
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return 1.0
            
            point = symbol_info.get('point', 0.00001)
            contract_size = symbol_info.get('trade_contract_size', 100000)
            
            # For most forex pairs
            if 'JPY' in symbol:
                pip_value = (0.01 / tick.get('ask', 1)) * contract_size
            elif 'XAU' in symbol or 'GOLD' in symbol:
                pip_value = 0.1 * contract_size / 100
            else:
                pip_value = (0.0001 / tick.get('ask', 1)) * contract_size
            
            return pip_value
            
        except Exception as e:
            self.logger.error(f"Error calculating pip value for {symbol}: {e}")
            return 1.0
    
    def get_recommended_lot_size(self, symbol: str, account_balance: float = None) -> float:
        """Get recommended lot size based on account balance"""
        try:
            if account_balance is None:
                account_info = self.mt5_connector.get_account_info()
                account_balance = account_info.get('balance', 0) if account_info else 0
            
            # Conservative lot sizing
            if account_balance < 1000:
                return 0.01
            elif account_balance < 5000:
                return 0.02
            elif account_balance < 10000:
                return 0.05
            elif account_balance < 50000:
                return 0.1
            else:
                return min(account_balance / 100000, 1.0)  # 1% of balance as max
                
        except Exception as e:
            self.logger.error(f"Error getting recommended lot size: {e}")
            return 0.01
