
"""
Risk Management System for AuraTrade Bot
Advanced risk control and position sizing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class RiskLimits:
    max_risk_per_trade: float = 1.0  # %
    max_daily_risk: float = 5.0  # %
    max_weekly_risk: float = 15.0  # %
    max_monthly_risk: float = 30.0  # %
    max_drawdown: float = 10.0  # %
    max_positions: int = 10
    max_positions_per_symbol: int = 3
    max_correlation_exposure: float = 20.0  # %
    min_margin_level: float = 200.0  # %
    emergency_stop_drawdown: float = 15.0  # %
    max_consecutive_losses: int = 5

@dataclass
class RiskMetrics:
    current_risk: float = 0.0
    daily_risk: float = 0.0
    weekly_risk: float = 0.0
    monthly_risk: float = 0.0
    current_drawdown: float = 0.0
    margin_level: float = 0.0
    open_positions: int = 0
    consecutive_losses: int = 0
    risk_level: RiskLevel = RiskLevel.LOW

class RiskManager:
    """Advanced risk management system"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.mt5 = mt5_connector
        self.logger = Logger().get_logger()
        
        # Risk parameters
        self.limits = RiskLimits()
        self.current_metrics = RiskMetrics()
        
        # Trading history for risk calculations
        self.trade_history: List[Dict] = []
        self.daily_stats: Dict[str, Dict] = {}
        
        # Emergency stops
        self.emergency_stop_active = False
        self.last_balance_check = 0.0
        self.peak_balance = 0.0
        
        # Risk monitoring
        self.monitoring_enabled = True
        self.risk_alerts_sent = set()
        
        self.logger.info("RiskManager initialized")
    
    def set_risk_limits(self, limits: RiskLimits):
        """Update risk limits"""
        self.limits = limits
        self.logger.info(f"Risk limits updated: {limits}")
    
    def check_trade_risk(self, symbol: str, volume: float, order_type: str = "BUY") -> bool:
        """Check if trade meets risk requirements"""
        try:
            # Update current metrics
            self.update_risk_metrics()
            
            # Check emergency stop
            if self.emergency_stop_active:
                self.logger.warning("Emergency stop active - trade rejected")
                return False
            
            # Check maximum positions
            if self.current_metrics.open_positions >= self.limits.max_positions:
                self.logger.warning(f"Maximum positions limit reached: {self.limits.max_positions}")
                return False
            
            # Check positions per symbol
            positions = self.mt5.get_positions(symbol)
            if len(positions) >= self.limits.max_positions_per_symbol:
                self.logger.warning(f"Maximum positions per symbol limit reached for {symbol}")
                return False
            
            # Check margin level
            account_info = self.mt5.get_account_info()
            if account_info and account_info['margin_level'] < self.limits.min_margin_level:
                self.logger.warning(f"Insufficient margin level: {account_info['margin_level']}%")
                return False
            
            # Calculate trade risk
            trade_risk = self.calculate_trade_risk(symbol, volume)
            
            # Check per-trade risk
            if trade_risk > self.limits.max_risk_per_trade:
                self.logger.warning(f"Trade risk {trade_risk:.2f}% exceeds limit {self.limits.max_risk_per_trade}%")
                return False
            
            # Check daily risk
            if self.current_metrics.daily_risk + trade_risk > self.limits.max_daily_risk:
                self.logger.warning(f"Daily risk limit would be exceeded")
                return False
            
            # Check drawdown
            if self.current_metrics.current_drawdown > self.limits.max_drawdown:
                self.logger.warning(f"Maximum drawdown exceeded: {self.current_metrics.current_drawdown:.2f}%")
                return False
            
            # Check consecutive losses
            if self.current_metrics.consecutive_losses >= self.limits.max_consecutive_losses:
                self.logger.warning(f"Maximum consecutive losses reached: {self.current_metrics.consecutive_losses}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking trade risk: {e}")
            return False
    
    def calculate_trade_risk(self, symbol: str, volume: float) -> float:
        """Calculate risk percentage for a trade"""
        try:
            account_info = self.mt5.get_account_info()
            if not account_info:
                return 0.0
            
            balance = account_info['balance']
            if balance <= 0:
                return 0.0
            
            # Get symbol info
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            # Calculate potential loss (assuming 2% stop loss)
            pip_value = self.calculate_pip_value(symbol, volume)
            stop_loss_pips = 20  # Default 20 pips stop loss
            potential_loss = pip_value * stop_loss_pips
            
            # Calculate risk percentage
            risk_percentage = (potential_loss / balance) * 100
            
            return risk_percentage
            
        except Exception as e:
            self.logger.error(f"Error calculating trade risk: {e}")
            return 0.0
    
    def calculate_pip_value(self, symbol: str, volume: float) -> float:
        """Calculate pip value for position"""
        try:
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            contract_size = symbol_info['trade_contract_size']
            point = symbol_info['point']
            digits = symbol_info['digits']
            
            # Calculate pip size (usually 10 * point for most pairs)
            if digits == 5 or digits == 3:
                pip_size = point * 10
            else:
                pip_size = point
            
            # Calculate pip value
            pip_value = volume * contract_size * pip_size
            
            # Convert to account currency if needed
            base_currency = symbol_info['currency_base']
            account_info = self.mt5.get_account_info()
            account_currency = account_info['currency'] if account_info else 'USD'
            
            if base_currency != account_currency:
                # Simple conversion (in real implementation, get actual rates)
                conversion_rate = 1.0  # Placeholder
                pip_value *= conversion_rate
            
            return pip_value
            
        except Exception as e:
            self.logger.error(f"Error calculating pip value: {e}")
            return 0.0
    
    def update_risk_metrics(self):
        """Update current risk metrics"""
        try:
            account_info = self.mt5.get_account_info()
            if not account_info:
                return
            
            balance = account_info['balance']
            equity = account_info['equity']
            margin_level = account_info['margin_level']
            
            # Update peak balance for drawdown calculation
            if balance > self.peak_balance:
                self.peak_balance = balance
                self.last_balance_check = balance
            
            # Calculate current drawdown
            if self.peak_balance > 0:
                drawdown = ((self.peak_balance - equity) / self.peak_balance) * 100
                self.current_metrics.current_drawdown = max(0, drawdown)
            
            # Update margin level
            self.current_metrics.margin_level = margin_level
            
            # Count open positions
            positions = self.mt5.get_positions()
            self.current_metrics.open_positions = len(positions)
            
            # Calculate daily/weekly/monthly risk
            self._calculate_period_risks()
            
            # Update consecutive losses
            self._update_consecutive_losses()
            
            # Determine risk level
            self._determine_risk_level()
            
            # Check emergency conditions
            self._check_emergency_conditions()
            
        except Exception as e:
            self.logger.error(f"Error updating risk metrics: {e}")
    
    def _calculate_period_risks(self):
        """Calculate daily, weekly, monthly risks"""
        try:
            now = datetime.now()
            today = now.date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            # Get recent trade history
            history = self.mt5.get_order_history(days=30)
            
            daily_pnl = 0.0
            weekly_pnl = 0.0
            monthly_pnl = 0.0
            
            account_info = self.mt5.get_account_info()
            balance = account_info['balance'] if account_info else 1.0
            
            for trade in history:
                trade_date = trade['time'].date()
                pnl = trade.get('profit', 0.0)
                
                if trade_date == today:
                    daily_pnl += pnl
                
                if trade_date >= week_start:
                    weekly_pnl += pnl
                
                if trade_date >= month_start:
                    monthly_pnl += pnl
            
            # Calculate risk percentages (negative PnL as risk)
            self.current_metrics.daily_risk = abs(min(0, daily_pnl) / balance * 100)
            self.current_metrics.weekly_risk = abs(min(0, weekly_pnl) / balance * 100)
            self.current_metrics.monthly_risk = abs(min(0, monthly_pnl) / balance * 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating period risks: {e}")
    
    def _update_consecutive_losses(self):
        """Update consecutive losses count"""
        try:
            history = self.mt5.get_order_history(days=7)
            consecutive_losses = 0
            
            # Sort by time (most recent first)
            history.sort(key=lambda x: x['time'], reverse=True)
            
            for trade in history:
                if trade.get('profit', 0) < 0:
                    consecutive_losses += 1
                else:
                    break  # Stop at first winning trade
            
            self.current_metrics.consecutive_losses = consecutive_losses
            
        except Exception as e:
            self.logger.error(f"Error updating consecutive losses: {e}")
    
    def _determine_risk_level(self):
        """Determine current risk level"""
        try:
            risk_score = 0
            
            # Drawdown score
            if self.current_metrics.current_drawdown > 15:
                risk_score += 4
            elif self.current_metrics.current_drawdown > 10:
                risk_score += 3
            elif self.current_metrics.current_drawdown > 5:
                risk_score += 2
            elif self.current_metrics.current_drawdown > 2:
                risk_score += 1
            
            # Daily risk score
            if self.current_metrics.daily_risk > 4:
                risk_score += 3
            elif self.current_metrics.daily_risk > 3:
                risk_score += 2
            elif self.current_metrics.daily_risk > 2:
                risk_score += 1
            
            # Consecutive losses score
            if self.current_metrics.consecutive_losses > 5:
                risk_score += 3
            elif self.current_metrics.consecutive_losses > 3:
                risk_score += 2
            elif self.current_metrics.consecutive_losses > 1:
                risk_score += 1
            
            # Margin level score
            if self.current_metrics.margin_level < 150:
                risk_score += 4
            elif self.current_metrics.margin_level < 200:
                risk_score += 2
            elif self.current_metrics.margin_level < 300:
                risk_score += 1
            
            # Determine risk level
            if risk_score >= 10:
                self.current_metrics.risk_level = RiskLevel.VERY_HIGH
            elif risk_score >= 7:
                self.current_metrics.risk_level = RiskLevel.HIGH
            elif risk_score >= 4:
                self.current_metrics.risk_level = RiskLevel.MEDIUM
            elif risk_score >= 2:
                self.current_metrics.risk_level = RiskLevel.LOW
            else:
                self.current_metrics.risk_level = RiskLevel.VERY_LOW
            
        except Exception as e:
            self.logger.error(f"Error determining risk level: {e}")
    
    def _check_emergency_conditions(self):
        """Check for emergency stop conditions"""
        try:
            emergency_triggered = False
            
            # Check emergency drawdown
            if self.current_metrics.current_drawdown >= self.limits.emergency_stop_drawdown:
                self.logger.critical(f"Emergency stop: Drawdown {self.current_metrics.current_drawdown:.2f}% >= {self.limits.emergency_stop_drawdown}%")
                emergency_triggered = True
            
            # Check margin level
            if self.current_metrics.margin_level < 100:
                self.logger.critical(f"Emergency stop: Margin level {self.current_metrics.margin_level:.1f}% < 100%")
                emergency_triggered = True
            
            # Check consecutive losses
            if self.current_metrics.consecutive_losses >= self.limits.max_consecutive_losses * 2:
                self.logger.critical(f"Emergency stop: Too many consecutive losses {self.current_metrics.consecutive_losses}")
                emergency_triggered = True
            
            if emergency_triggered and not self.emergency_stop_active:
                self.activate_emergency_stop()
            
        except Exception as e:
            self.logger.error(f"Error checking emergency conditions: {e}")
    
    def activate_emergency_stop(self):
        """Activate emergency stop"""
        try:
            self.emergency_stop_active = True
            self.logger.critical("🚨 EMERGENCY STOP ACTIVATED!")
            
            # Close all positions (if order manager is available)
            # This would be handled by the order manager
            
        except Exception as e:
            self.logger.error(f"Error activating emergency stop: {e}")
    
    def deactivate_emergency_stop(self):
        """Deactivate emergency stop"""
        try:
            self.emergency_stop_active = False
            self.logger.info("Emergency stop deactivated")
            
        except Exception as e:
            self.logger.error(f"Error deactivating emergency stop: {e}")
    
    def calculate_optimal_lot_size(self, symbol: str, risk_percent: float = None, 
                                  stop_loss_pips: float = 20) -> float:
        """Calculate optimal lot size based on risk"""
        try:
            if risk_percent is None:
                risk_percent = self.limits.max_risk_per_trade
            
            account_info = self.mt5.get_account_info()
            if not account_info:
                return 0.01
            
            balance = account_info['balance']
            risk_amount = balance * (risk_percent / 100)
            
            # Calculate pip value for 1 lot
            pip_value_per_lot = self.calculate_pip_value(symbol, 1.0)
            
            if pip_value_per_lot <= 0:
                return 0.01
            
            # Calculate optimal lot size
            optimal_lots = risk_amount / (stop_loss_pips * pip_value_per_lot)
            
            # Get symbol constraints
            symbol_info = self.mt5.get_symbol_info(symbol)
            if symbol_info:
                min_lot = symbol_info['volume_min']
                max_lot = symbol_info['volume_max']
                lot_step = symbol_info['volume_step']
                
                # Ensure lot size is within bounds
                optimal_lots = max(min_lot, min(max_lot, optimal_lots))
                
                # Round to lot step
                if lot_step > 0:
                    optimal_lots = round(optimal_lots / lot_step) * lot_step
            
            return round(optimal_lots, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal lot size: {e}")
            return 0.01
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        try:
            self.update_risk_metrics()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'risk_level': self.current_metrics.risk_level.value,
                'emergency_stop_active': self.emergency_stop_active,
                'metrics': {
                    'current_drawdown': round(self.current_metrics.current_drawdown, 2),
                    'daily_risk': round(self.current_metrics.daily_risk, 2),
                    'weekly_risk': round(self.current_metrics.weekly_risk, 2),
                    'monthly_risk': round(self.current_metrics.monthly_risk, 2),
                    'margin_level': round(self.current_metrics.margin_level, 1),
                    'open_positions': self.current_metrics.open_positions,
                    'consecutive_losses': self.current_metrics.consecutive_losses
                },
                'limits': {
                    'max_risk_per_trade': self.limits.max_risk_per_trade,
                    'max_daily_risk': self.limits.max_daily_risk,
                    'max_drawdown': self.limits.max_drawdown,
                    'max_positions': self.limits.max_positions,
                    'min_margin_level': self.limits.min_margin_level,
                    'emergency_stop_drawdown': self.limits.emergency_stop_drawdown
                },
                'warnings': self._get_risk_warnings()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating risk report: {e}")
            return {'error': str(e)}
    
    def _get_risk_warnings(self) -> List[str]:
        """Get current risk warnings"""
        warnings = []
        
        try:
            if self.current_metrics.current_drawdown > self.limits.max_drawdown * 0.8:
                warnings.append(f"High drawdown: {self.current_metrics.current_drawdown:.1f}%")
            
            if self.current_metrics.daily_risk > self.limits.max_daily_risk * 0.8:
                warnings.append(f"High daily risk: {self.current_metrics.daily_risk:.1f}%")
            
            if self.current_metrics.margin_level < self.limits.min_margin_level * 1.2:
                warnings.append(f"Low margin level: {self.current_metrics.margin_level:.1f}%")
            
            if self.current_metrics.consecutive_losses >= 3:
                warnings.append(f"Consecutive losses: {self.current_metrics.consecutive_losses}")
            
            if self.current_metrics.open_positions > self.limits.max_positions * 0.8:
                warnings.append(f"High position count: {self.current_metrics.open_positions}")
            
        except Exception as e:
            self.logger.error(f"Error getting risk warnings: {e}")
        
        return warnings
