
"""
Risk management system for AuraTrade Bot
Implements conservative risk controls for high win rate trading
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class RiskManager:
    """Advanced risk management system"""

    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5 = mt5_connector
        
        # Risk parameters
        self.max_risk_per_trade = 0.02  # 2% per trade
        self.max_daily_risk = 0.05      # 5% daily
        self.max_drawdown = 0.10        # 10% max drawdown
        self.max_exposure = 0.20        # 20% max exposure
        
        # Tracking
        self.daily_risk_used = 0.0
        self.current_exposure = 0.0
        self.daily_trades = 0
        self.daily_losses = 0
        self.consecutive_losses = 0
        
        # Emergency stops
        self.emergency_stop = False
        self.max_consecutive_losses = 5
        
        self.logger.info("RiskManager initialized")

    def can_open_position(self, symbol: str, volume: float) -> bool:
        """Check if position can be opened based on risk rules"""
        try:
            # Emergency stop check
            if self.emergency_stop:
                self.logger.warning("Emergency stop active - no new positions")
                return False
            
            # Get account info
            account = self.mt5.get_account_info()
            if not account:
                return False
            
            balance = account.get('balance', 0)
            equity = account.get('equity', 0)
            
            # Check drawdown
            if balance > 0:
                current_drawdown = (balance - equity) / balance
                if current_drawdown > self.max_drawdown:
                    self.logger.warning(f"Max drawdown exceeded: {current_drawdown:.2%}")
                    return False
            
            # Calculate position risk
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return False
            
            # Estimate position value
            position_value = volume * symbol_info.get('trade_contract_size', 100000)
            position_risk = position_value * self.max_risk_per_trade
            
            # Check daily risk limit
            if self.daily_risk_used + position_risk > balance * self.max_daily_risk:
                self.logger.warning("Daily risk limit would be exceeded")
                return False
            
            # Check exposure limit
            if self.current_exposure + position_value > balance * self.max_exposure:
                self.logger.warning("Exposure limit would be exceeded")
                return False
            
            # Check consecutive losses
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.logger.warning("Too many consecutive losses - trading paused")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking position risk: {e}")
            return False

    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: float, risk_amount: float = None) -> float:
        """Calculate optimal position size based on risk"""
        try:
            # Get account info
            account = self.mt5.get_account_info()
            if not account:
                return 0.0
            
            balance = account.get('balance', 0)
            if balance <= 0:
                return 0.0
            
            # Use default risk if not specified
            if risk_amount is None:
                risk_amount = balance * self.max_risk_per_trade
            
            # Get symbol info
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            # Calculate pip value
            pip_size = symbol_info.get('point', 0.0001)
            tick_value = symbol_info.get('trade_tick_value', 1.0)
            
            # Calculate distance to stop loss
            if stop_loss <= 0 or entry_price <= 0:
                return 0.0
            
            sl_distance = abs(entry_price - stop_loss)
            if sl_distance <= 0:
                return 0.0
            
            # Calculate position size
            pip_distance = sl_distance / pip_size
            risk_per_pip = tick_value
            
            if pip_distance > 0 and risk_per_pip > 0:
                position_size = risk_amount / (pip_distance * risk_per_pip)
                
                # Apply minimum and maximum limits
                min_lot = symbol_info.get('volume_min', 0.01)
                max_lot = min(symbol_info.get('volume_max', 100.0), 10.0)  # Cap at 10 lots
                
                position_size = max(min_lot, min(position_size, max_lot))
                
                # Round to lot step
                lot_step = symbol_info.get('volume_step', 0.01)
                position_size = round(position_size / lot_step) * lot_step
                
                return position_size
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0

    def calculate_sl_tp(self, symbol: str, order_type: str, entry_price: float, 
                       balance: float) -> Dict[str, float]:
        """Calculate SL and TP based on percentage of balance"""
        try:
            # Risk per trade (2% of balance)
            risk_amount = balance * self.max_risk_per_trade
            
            # Reward ratio (1:2 risk-reward)
            reward_amount = risk_amount * 2.0
            
            # Get symbol info
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return {'sl': 0.0, 'tp': 0.0}
            
            pip_value = symbol_info.get('trade_tick_value', 1.0)
            pip_size = symbol_info.get('point', 0.0001)
            
            # Calculate pip distance for risk amount
            if pip_value > 0:
                risk_pips = risk_amount / pip_value
                reward_pips = reward_amount / pip_value
                
                if order_type.upper() == 'BUY':
                    sl = entry_price - (risk_pips * pip_size)
                    tp = entry_price + (reward_pips * pip_size)
                else:  # SELL
                    sl = entry_price + (risk_pips * pip_size)
                    tp = entry_price - (reward_pips * pip_size)
                
                return {
                    'sl': round(sl, symbol_info.get('digits', 5)),
                    'tp': round(tp, symbol_info.get('digits', 5))
                }
            
            return {'sl': 0.0, 'tp': 0.0}
            
        except Exception as e:
            self.logger.error(f"Error calculating SL/TP: {e}")
            return {'sl': 0.0, 'tp': 0.0}

    def update_risk_metrics(self, trade_result: Dict[str, Any]):
        """Update risk metrics after trade"""
        try:
            profit = trade_result.get('profit', 0)
            
            # Update daily metrics
            self.daily_trades += 1
            
            if profit < 0:
                self.daily_losses += 1
                self.consecutive_losses += 1
                self.daily_risk_used += abs(profit)
            else:
                self.consecutive_losses = 0
            
            # Check for emergency stop conditions
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.emergency_stop = True
                self.logger.warning("Emergency stop activated due to consecutive losses")
            
            # Update exposure
            self._update_exposure()
            
        except Exception as e:
            self.logger.error(f"Error updating risk metrics: {e}")

    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        try:
            account = self.mt5.get_account_info()
            balance = account.get('balance', 0) if account else 0
            
            return {
                'emergency_stop': self.emergency_stop,
                'daily_risk_used': self.daily_risk_used,
                'daily_risk_limit': balance * self.max_daily_risk,
                'current_exposure': self.current_exposure,
                'max_exposure': balance * self.max_exposure,
                'consecutive_losses': self.consecutive_losses,
                'max_consecutive_losses': self.max_consecutive_losses,
                'daily_trades': self.daily_trades,
                'daily_losses': self.daily_losses
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk status: {e}")
            return {}

    def reset_daily_limits(self):
        """Reset daily risk limits"""
        self.daily_risk_used = 0.0
        self.daily_trades = 0
        self.daily_losses = 0
        self.emergency_stop = False
        self.logger.info("Daily risk limits reset")

    def _update_exposure(self):
        """Update current exposure calculation"""
        try:
            positions = self.mt5.get_positions()
            total_exposure = 0
            
            for pos in positions:
                symbol_info = self.mt5.get_symbol_info(pos['symbol'])
                if symbol_info:
                    contract_size = symbol_info.get('trade_contract_size', 100000)
                    exposure = pos['volume'] * contract_size
                    total_exposure += exposure
            
            self.current_exposure = total_exposure
            
        except Exception as e:
            self.logger.error(f"Error updating exposure: {e}")
