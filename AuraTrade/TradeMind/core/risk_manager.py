"""
Risk management system for controlling trading exposure and protecting capital
Handles position sizing, stop losses, take profits, and overall risk monitoring
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd

from config.config import Config
from config.settings import Settings
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.config = Config()
        self.settings = Settings()
        self.mt5_connector = mt5_connector
        
        # Risk tracking
        self.daily_risk_used = 0.0
        self.total_exposure = 0.0
        self.peak_equity = 0.0
        self.max_drawdown = 0.0
        
        # Risk limits
        self.emergency_stop_triggered = False
        self.daily_limit_reached = False
        
    def calculate_position_size(self, symbol: str, risk_amount: float, 
                              entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk amount and stop loss"""
        try:
            if stop_loss <= 0 or entry_price <= 0:
                return 0.0
            
            # Get symbol information
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            # Calculate risk per lot
            pip_value = self._calculate_pip_value(symbol, symbol_info)
            if pip_value <= 0:
                return 0.0
            
            # Calculate stop loss distance in pips
            sl_distance_pips = abs(entry_price - stop_loss) / symbol_info['point']
            if symbol_info['digits'] == 5 or symbol_info['digits'] == 3:
                sl_distance_pips /= 10  # Convert to actual pips
            
            # Calculate risk per lot
            risk_per_lot = sl_distance_pips * pip_value
            
            if risk_per_lot <= 0:
                return 0.0
            
            # Calculate position size
            position_size = risk_amount / risk_per_lot
            
            # Round to symbol's lot step
            lot_step = symbol_info.get('volume_step', 0.01)
            position_size = math.floor(position_size / lot_step) * lot_step
            
            # Apply limits
            min_lot = symbol_info.get('volume_min', 0.01)
            max_lot = symbol_info.get('volume_max', 100.0)
            
            position_size = max(min_lot, min(position_size, max_lot))
            
            # Apply maximum position size based on account equity
            max_position_by_equity = self._calculate_max_position_by_equity(symbol)
            position_size = min(position_size, max_position_by_equity)
            
            return round(position_size, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
    
    def calculate_risk_amount(self, symbol: str) -> float:
        """Calculate risk amount for a trade"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0
            
            equity = account_info['equity']
            
            # Calculate base risk amount
            risk_percentage = self.settings.risk.max_risk_per_trade / 100
            base_risk = equity * risk_percentage
            
            # Adjust for daily risk used
            remaining_daily_risk = self._calculate_remaining_daily_risk()
            
            # Use the minimum of base risk and remaining daily risk
            risk_amount = min(base_risk, remaining_daily_risk)
            
            # Apply minimum risk amount
            min_risk = equity * 0.001  # 0.1% minimum
            risk_amount = max(risk_amount, min_risk)
            
            return risk_amount
            
        except Exception as e:
            self.logger.error(f"Error calculating risk amount: {e}")
            return 0.0
    
    def calculate_sl_tp(self, symbol: str, entry_price: float, direction: int, 
                       volume: float) -> Optional[Dict[str, float]]:
        """Calculate stop loss and take profit levels"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return None
            
            equity = account_info['equity']
            
            # Calculate risk amount for this trade
            risk_percentage = self.settings.risk.default_sl_percentage / 100
            risk_amount = equity * risk_percentage
            
            # Calculate profit target amount
            profit_percentage = self.settings.risk.default_tp_percentage / 100
            profit_amount = equity * profit_percentage
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return None
            
            # Calculate pip value
            pip_value = self._calculate_pip_value(symbol, symbol_info)
            if pip_value <= 0:
                return None
            
            # Calculate stop loss distance in pips
            sl_distance_pips = risk_amount / (volume * pip_value)
            
            # Calculate take profit distance in pips
            tp_distance_pips = profit_amount / (volume * pip_value)
            
            # Convert pips to price distance
            point = symbol_info['point']
            if symbol_info['digits'] == 5 or symbol_info['digits'] == 3:
                point *= 10  # Adjust for 5/3 digit brokers
            
            sl_distance_price = sl_distance_pips * point
            tp_distance_price = tp_distance_pips * point
            
            # Calculate actual SL and TP levels
            if direction > 0:  # Buy
                stop_loss = entry_price - sl_distance_price
                take_profit = entry_price + tp_distance_price
            else:  # Sell
                stop_loss = entry_price + sl_distance_price
                take_profit = entry_price - tp_distance_price
            
            # Round to symbol digits
            digits = symbol_info['digits']
            stop_loss = round(stop_loss, digits)
            take_profit = round(take_profit, digits)
            
            return {
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'sl_distance_pips': sl_distance_pips,
                'tp_distance_pips': tp_distance_pips
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating SL/TP for {symbol}: {e}")
            return None
    
    def calculate_trailing_stop(self, position: Dict, bid: float, ask: float, 
                              trail_distance: float) -> Optional[float]:
        """Calculate trailing stop level for position"""
        try:
            position_type = position['type']
            current_sl = position['sl']
            entry_price = position['price_open']
            
            # Determine current price based on position type
            if position_type == 0:  # Buy position
                current_price = bid
                # Calculate new trailing stop
                new_sl = current_price - (entry_price - current_sl)
                
                # Only update if new SL is higher (more favorable)
                if current_sl == 0 or new_sl > current_sl:
                    return new_sl
            else:  # Sell position
                current_price = ask
                # Calculate new trailing stop
                new_sl = current_price + (current_sl - entry_price)
                
                # Only update if new SL is lower (more favorable)
                if current_sl == 0 or new_sl < current_sl:
                    return new_sl
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating trailing stop: {e}")
            return None
    
    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a new position based on risk limits"""
        try:
            # Check daily risk limit
            if self.daily_limit_reached:
                return False
            
            # Check if emergency stop is triggered
            if self.emergency_stop_triggered:
                return False
            
            # Check total exposure limit
            if self._check_exposure_limit():
                return False
            
            # Check symbol-specific limits
            if self._check_symbol_exposure(symbol):
                return False
            
            # Check correlation limits
            if self._check_correlation_limits(symbol):
                return False
            
            # Check drawdown limits
            if self._check_drawdown_limits():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking if can open position for {symbol}: {e}")
            return False
    
    def check_emergency_stop(self) -> bool:
        """Check if emergency stop should be triggered"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return False
            
            equity = account_info['equity']
            balance = account_info['balance']
            
            # Update peak equity
            if equity > self.peak_equity:
                self.peak_equity = equity
            
            # Calculate current drawdown
            if self.peak_equity > 0:
                current_drawdown = ((self.peak_equity - equity) / self.peak_equity) * 100
                self.max_drawdown = max(self.max_drawdown, current_drawdown)
            else:
                current_drawdown = 0
            
            # Check emergency stop conditions
            emergency_dd_limit = self.config.ERROR_SETTINGS['emergency_stop_drawdown']
            
            if current_drawdown >= emergency_dd_limit:
                self.logger.critical(f"Emergency stop triggered: Drawdown {current_drawdown:.2f}% >= {emergency_dd_limit}%")
                self.emergency_stop_triggered = True
                return True
            
            # Check daily loss limit
            daily_loss_limit = abs(self.settings.performance_targets['daily_loss_limit'])
            daily_pnl_percentage = ((equity - balance) / balance) * 100
            
            if daily_pnl_percentage <= -daily_loss_limit:
                self.logger.warning(f"Daily loss limit reached: {daily_pnl_percentage:.2f}%")
                self.daily_limit_reached = True
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking emergency stop: {e}")
            return False
    
    def update_risk_metrics(self):
        """Update risk tracking metrics"""
        try:
            positions = self.mt5_connector.get_positions()
            account_info = self.mt5_connector.get_account_info()
            
            if not account_info:
                return
            
            equity = account_info['equity']
            
            # Calculate total exposure
            total_exposure = 0.0
            for position in positions:
                position_value = position['volume'] * position['price_open']
                total_exposure += position_value
            
            self.total_exposure = (total_exposure / equity) * 100 if equity > 0 else 0
            
            # Calculate daily risk used
            self._calculate_daily_risk_used()
            
            # Update drawdown metrics
            if equity > self.peak_equity:
                self.peak_equity = equity
            
            if self.peak_equity > 0:
                current_dd = ((self.peak_equity - equity) / self.peak_equity) * 100
                self.max_drawdown = max(self.max_drawdown, current_dd)
            
        except Exception as e:
            self.logger.error(f"Error updating risk metrics: {e}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return {}
            
            equity = account_info['equity']
            balance = account_info['balance']
            
            # Calculate current drawdown
            current_dd = 0.0
            if self.peak_equity > 0:
                current_dd = ((self.peak_equity - equity) / self.peak_equity) * 100
            
            # Calculate daily P&L
            daily_pnl = equity - balance
            daily_pnl_percentage = (daily_pnl / balance) * 100 if balance > 0 else 0
            
            return {
                'account_equity': equity,
                'account_balance': balance,
                'daily_pnl': daily_pnl,
                'daily_pnl_percentage': daily_pnl_percentage,
                'current_drawdown': current_dd,
                'max_drawdown': self.max_drawdown,
                'peak_equity': self.peak_equity,
                'total_exposure': self.total_exposure,
                'daily_risk_used': self.daily_risk_used,
                'remaining_daily_risk': self._calculate_remaining_daily_risk(),
                'emergency_stop_triggered': self.emergency_stop_triggered,
                'daily_limit_reached': self.daily_limit_reached,
                'risk_limits': {
                    'max_risk_per_trade': self.settings.risk.max_risk_per_trade,
                    'max_daily_risk': self.settings.risk.max_daily_risk,
                    'max_total_exposure': self.settings.risk.max_total_exposure,
                    'max_drawdown': self.settings.risk.max_drawdown
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk summary: {e}")
            return {}
    
    def _calculate_pip_value(self, symbol: str, symbol_info: Dict) -> float:
        """Calculate pip value for symbol"""
        try:
            # Get account currency
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0
            
            account_currency = account_info.get('currency', 'USD')
            
            # Basic pip value calculation
            contract_size = symbol_info.get('trade_contract_size', 100000)
            point = symbol_info.get('point', 0.00001)
            
            # Adjust for digit precision
            if symbol_info['digits'] == 5 or symbol_info['digits'] == 3:
                pip_value = (point * 10) * contract_size
            else:
                pip_value = point * contract_size
            
            # For cross-currency pairs, we might need conversion
            # For simplicity, assume direct calculation
            # In production, you'd need proper currency conversion
            
            return pip_value
            
        except Exception as e:
            self.logger.error(f"Error calculating pip value for {symbol}: {e}")
            return 0.0
    
    def _calculate_max_position_by_equity(self, symbol: str) -> float:
        """Calculate maximum position size based on account equity"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.01
            
            equity = account_info['equity']
            
            # Maximum 2% of equity per position (conservative)
            max_position_value = equity * 0.02
            
            # Get current price to calculate lot size
            current_price = self.mt5_connector.get_current_price(symbol)
            if not current_price:
                return 0.01
            
            # Use ask price for calculation
            price = current_price[1]
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.01
            
            contract_size = symbol_info.get('trade_contract_size', 100000)
            
            # Calculate maximum lots
            max_lots = max_position_value / (price * contract_size)
            
            # Round down to lot step
            lot_step = symbol_info.get('volume_step', 0.01)
            max_lots = math.floor(max_lots / lot_step) * lot_step
            
            # Apply minimum
            min_lot = symbol_info.get('volume_min', 0.01)
            max_lots = max(max_lots, min_lot)
            
            return max_lots
            
        except Exception as e:
            self.logger.error(f"Error calculating max position by equity: {e}")
            return 0.01
    
    def _calculate_remaining_daily_risk(self) -> float:
        """Calculate remaining daily risk allowance"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0
            
            equity = account_info['equity']
            max_daily_risk_amount = equity * (self.settings.risk.max_daily_risk / 100)
            
            return max(0, max_daily_risk_amount - self.daily_risk_used)
            
        except Exception as e:
            self.logger.error(f"Error calculating remaining daily risk: {e}")
            return 0.0
    
    def _calculate_daily_risk_used(self):
        """Calculate how much daily risk has been used"""
        try:
            positions = self.mt5_connector.get_positions()
            self.daily_risk_used = 0.0
            
            for position in positions:
                if position['sl'] > 0:
                    # Calculate risk for this position
                    entry_price = position['price_open']
                    sl_price = position['sl']
                    volume = position['volume']
                    
                    # Get symbol info for pip value calculation
                    symbol_info = self.mt5_connector.get_symbol_info(position['symbol'])
                    if symbol_info:
                        pip_value = self._calculate_pip_value(position['symbol'], symbol_info)
                        sl_distance_pips = abs(entry_price - sl_price) / symbol_info['point']
                        
                        if symbol_info['digits'] == 5 or symbol_info['digits'] == 3:
                            sl_distance_pips /= 10
                        
                        position_risk = sl_distance_pips * pip_value * volume
                        self.daily_risk_used += position_risk
            
        except Exception as e:
            self.logger.error(f"Error calculating daily risk used: {e}")
    
    def _check_exposure_limit(self) -> bool:
        """Check if total exposure limit would be exceeded"""
        try:
            max_exposure = self.settings.risk.max_total_exposure
            return self.total_exposure >= max_exposure
        except Exception as e:
            self.logger.error(f"Error checking exposure limit: {e}")
            return True
    
    def _check_symbol_exposure(self, symbol: str) -> bool:
        """Check symbol-specific exposure limits"""
        try:
            positions = self.mt5_connector.get_positions()
            symbol_positions = [p for p in positions if p['symbol'] == symbol]
            
            # Limit to 3 positions per symbol
            return len(symbol_positions) >= 3
            
        except Exception as e:
            self.logger.error(f"Error checking symbol exposure for {symbol}: {e}")
            return True
    
    def _check_correlation_limits(self, symbol: str) -> bool:
        """Check correlation limits between positions"""
        try:
            # Simplified correlation check
            # In production, you'd calculate actual correlations
            positions = self.mt5_connector.get_positions()
            
            correlated_symbols = {
                'EURUSD': ['GBPUSD', 'AUDUSD'],
                'GBPUSD': ['EURUSD', 'EURGBP'],
                'USDJPY': ['EURJPY', 'GBPJPY'],
                'XAUUSD': ['XAGUSD']  # Gold and Silver
            }
            
            if symbol in correlated_symbols:
                for position in positions:
                    if position['symbol'] in correlated_symbols[symbol]:
                        # Already have correlated position
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking correlation limits: {e}")
            return False
    
    def _check_drawdown_limits(self) -> bool:
        """Check if drawdown limits would be exceeded"""
        try:
            max_dd_limit = self.settings.risk.max_drawdown
            return self.max_drawdown >= max_dd_limit
        except Exception as e:
            self.logger.error(f"Error checking drawdown limits: {e}")
            return True
    
    def reset_daily_limits(self):
        """Reset daily risk limits (call at start of new trading day)"""
        try:
            self.daily_risk_used = 0.0
            self.daily_limit_reached = False
            self.logger.info("Daily risk limits reset")
        except Exception as e:
            self.logger.error(f"Error resetting daily limits: {e}")
    
    def reset_emergency_stop(self):
        """Reset emergency stop (manual override)"""
        try:
            self.emergency_stop_triggered = False
            self.logger.warning("Emergency stop manually reset")
        except Exception as e:
            self.logger.error(f"Error resetting emergency stop: {e}")
