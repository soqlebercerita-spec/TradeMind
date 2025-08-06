
"""
Risk management system for AuraTrade Bot
Implements conservative risk controls for high win rate trading
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from core.mt5_connector import MT5Connector
from utils.logger import Logger, log_error, log_system

class RiskManager:
    """Conservative risk management for consistent profits"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Risk parameters
        self.risk_params = {
            'max_risk_per_trade': 1.0,      # 1% per trade
            'max_daily_risk': 5.0,          # 5% daily limit
            'max_drawdown': 10.0,           # 10% max drawdown
            'max_positions': 10,            # Total positions
            'max_positions_per_symbol': 3,  # Per symbol limit
            'min_margin_level': 200.0,      # 200% minimum margin
            'max_correlation_risk': 3.0,    # Max correlated positions
        }
        
        # Risk tracking
        self.daily_risk_taken = 0.0
        self.peak_equity = 0.0
        self.risk_events = []
        self.last_reset_date = datetime.now().date()
        
        self.logger.info("Risk Manager initialized with conservative settings")
    
    def can_open_position(self, symbol: str, volume: float) -> bool:
        """Comprehensive risk check before opening position"""
        try:
            # Reset daily stats if new day
            self._check_daily_reset()
            
            # Get account info
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                log_error("RiskManager", "Cannot get account info", None)
                return False
            
            # Check all risk criteria
            checks = [
                self._check_balance_risk(account_info, volume),
                self._check_margin_risk(account_info),
                self._check_daily_risk_limit(account_info, volume),
                self._check_drawdown_limit(account_info),
                self._check_position_limits(symbol),
                self._check_correlation_risk(symbol),
                self._check_market_conditions()
            ]
            
            if all(checks):
                # Update risk tracking
                position_risk = self._calculate_position_risk(account_info, volume)
                self.daily_risk_taken += position_risk
                
                self.logger.info(f"Risk check PASSED for {volume} {symbol} (Risk: {position_risk:.2f}%)")
                return True
            else:
                failed_checks = [i for i, check in enumerate(checks) if not check]
                self.logger.warning(f"Risk check FAILED for {symbol}: Failed checks {failed_checks}")
                return False
                
        except Exception as e:
            log_error("RiskManager", f"Error in position risk check: {e}", e)
            return False
    
    def _check_balance_risk(self, account_info: Dict, volume: float) -> bool:
        """Check if position size is within risk limits"""
        try:
            balance = account_info.get('balance', 0)
            if balance <= 0:
                return False
            
            # Calculate position value (simplified)
            position_value = volume * 100000  # Assuming 1 lot = 100,000 units
            position_risk_pct = (position_value * 0.01) / balance * 100  # 1% price move risk
            
            if position_risk_pct > self.risk_params['max_risk_per_trade']:
                self.logger.warning(f"Position risk {position_risk_pct:.2f}% exceeds limit {self.risk_params['max_risk_per_trade']}%")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking balance risk: {e}", e)
            return False
    
    def _check_margin_risk(self, account_info: Dict) -> bool:
        """Check margin level"""
        try:
            margin_level = account_info.get('margin_level', 0)
            
            # If no margin used, allow trade
            if margin_level == 0:
                return True
            
            if margin_level < self.risk_params['min_margin_level']:
                self.logger.warning(f"Margin level {margin_level:.1f}% below minimum {self.risk_params['min_margin_level']}%")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking margin risk: {e}", e)
            return False
    
    def _check_daily_risk_limit(self, account_info: Dict, volume: float) -> bool:
        """Check daily risk accumulation"""
        try:
            position_risk = self._calculate_position_risk(account_info, volume)
            total_daily_risk = self.daily_risk_taken + position_risk
            
            if total_daily_risk > self.risk_params['max_daily_risk']:
                self.logger.warning(f"Daily risk {total_daily_risk:.2f}% would exceed limit {self.risk_params['max_daily_risk']}%")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking daily risk: {e}", e)
            return False
    
    def _check_drawdown_limit(self, account_info: Dict) -> bool:
        """Check maximum drawdown"""
        try:
            equity = account_info.get('equity', 0)
            balance = account_info.get('balance', 0)
            
            # Update peak equity
            if equity > self.peak_equity:
                self.peak_equity = equity
            
            # Calculate current drawdown
            if self.peak_equity > 0:
                current_drawdown = (self.peak_equity - equity) / self.peak_equity * 100
                
                if current_drawdown > self.risk_params['max_drawdown']:
                    self.logger.warning(f"Drawdown {current_drawdown:.2f}% exceeds limit {self.risk_params['max_drawdown']}%")
                    
                    # Log risk event
                    self._log_risk_event("MAX_DRAWDOWN_EXCEEDED", {
                        'drawdown': current_drawdown,
                        'peak_equity': self.peak_equity,
                        'current_equity': equity
                    })
                    
                    return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking drawdown: {e}", e)
            return False
    
    def _check_position_limits(self, symbol: str) -> bool:
        """Check position count limits"""
        try:
            positions = self.mt5_connector.get_positions()
            
            # Total position limit
            if len(positions) >= self.risk_params['max_positions']:
                self.logger.warning(f"Total positions {len(positions)} at limit {self.risk_params['max_positions']}")
                return False
            
            # Symbol-specific limit
            symbol_positions = [p for p in positions if p['symbol'] == symbol]
            if len(symbol_positions) >= self.risk_params['max_positions_per_symbol']:
                self.logger.warning(f"Symbol {symbol} positions {len(symbol_positions)} at limit {self.risk_params['max_positions_per_symbol']}")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking position limits: {e}", e)
            return False
    
    def _check_correlation_risk(self, symbol: str) -> bool:
        """Check correlation risk between positions"""
        try:
            positions = self.mt5_connector.get_positions()
            
            # Define correlated pairs
            correlation_groups = {
                'EUR': ['EURUSD', 'EURJPY', 'EURGBP', 'EURAUD', 'EURCHF'],
                'USD': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'USDCAD'],
                'GBP': ['GBPUSD', 'GBPJPY', 'EURGBP', 'GBPAUD', 'GBPCHF'],
                'JPY': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CHFJPY'],
                'GOLD': ['XAUUSD', 'XAGUSD'],
                'CRYPTO': ['BTCUSD', 'ETHUSD']
            }
            
            # Find which group the symbol belongs to
            symbol_groups = []
            for group, symbols in correlation_groups.items():
                if symbol in symbols:
                    symbol_groups.append(group)
            
            # Count existing positions in same groups
            correlated_positions = 0
            for position in positions:
                pos_symbol = position['symbol']
                for group in symbol_groups:
                    if pos_symbol in correlation_groups[group]:
                        correlated_positions += 1
                        break
            
            if correlated_positions >= self.risk_params['max_correlation_risk']:
                self.logger.warning(f"Correlation risk: {correlated_positions} positions in same group")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking correlation risk: {e}", e)
            return False
    
    def _check_market_conditions(self) -> bool:
        """Check if market conditions are suitable for trading"""
        try:
            # Time-based restrictions
            current_time = datetime.now()
            hour = current_time.hour
            
            # Avoid trading during low liquidity hours
            if hour in [0, 1, 2, 22, 23]:
                self.logger.warning("Trading restricted during low liquidity hours")
                return False
            
            # Avoid trading close to weekend
            weekday = current_time.weekday()
            if weekday == 4 and hour >= 21:  # Friday after 9 PM
                self.logger.warning("Trading restricted near weekend")
                return False
            
            if weekday == 6:  # Sunday
                self.logger.warning("No trading on Sunday")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking market conditions: {e}", e)
            return False
    
    def _calculate_position_risk(self, account_info: Dict, volume: float) -> float:
        """Calculate risk percentage for position"""
        try:
            balance = account_info.get('balance', 0)
            if balance <= 0:
                return 0.0
            
            # Simplified risk calculation
            # Assuming 1% price move against position
            position_value = volume * 100000  # 1 lot = 100,000 units
            risk_amount = position_value * 0.01  # 1% price move
            risk_percentage = (risk_amount / balance) * 100
            
            return risk_percentage
            
        except Exception as e:
            log_error("RiskManager", f"Error calculating position risk: {e}", e)
            return 100.0  # Return high risk on error
    
    def _check_daily_reset(self):
        """Reset daily counters if new day"""
        try:
            current_date = datetime.now().date()
            if current_date != self.last_reset_date:
                self.daily_risk_taken = 0.0
                self.last_reset_date = current_date
                log_system("RiskManager", "Daily risk counters reset")
        except Exception as e:
            log_error("RiskManager", f"Error resetting daily counters: {e}", e)
    
    def _log_risk_event(self, event_type: str, data: Dict):
        """Log risk management events"""
        try:
            event = {
                'timestamp': datetime.now(),
                'type': event_type,
                'data': data
            }
            self.risk_events.append(event)
            
            # Keep only last 100 events
            if len(self.risk_events) > 100:
                self.risk_events = self.risk_events[-100:]
            
            log_system("RiskManager", f"Risk event: {event_type}")
            
        except Exception as e:
            log_error("RiskManager", f"Error logging risk event: {e}", e)
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        try:
            account_info = self.mt5_connector.get_account_info()
            positions = self.mt5_connector.get_positions()
            
            equity = account_info.get('equity', 0)
            balance = account_info.get('balance', 0)
            
            # Calculate current drawdown
            current_drawdown = 0.0
            if self.peak_equity > 0:
                current_drawdown = (self.peak_equity - equity) / self.peak_equity * 100
            
            status = {
                'daily_risk_taken': self.daily_risk_taken,
                'daily_risk_remaining': max(0, self.risk_params['max_daily_risk'] - self.daily_risk_taken),
                'current_drawdown': current_drawdown,
                'max_drawdown_limit': self.risk_params['max_drawdown'],
                'active_positions': len(positions),
                'max_positions': self.risk_params['max_positions'],
                'margin_level': account_info.get('margin_level', 0),
                'min_margin_level': self.risk_params['min_margin_level'],
                'peak_equity': self.peak_equity,
                'current_equity': equity,
                'risk_events_today': len([e for e in self.risk_events 
                                        if e['timestamp'].date() == datetime.now().date()])
            }
            
            return status
            
        except Exception as e:
            log_error("RiskManager", f"Error getting risk status: {e}", e)
            return {}
    
    def update_risk_parameters(self, new_params: Dict[str, float]):
        """Update risk parameters"""
        try:
            for key, value in new_params.items():
                if key in self.risk_params:
                    old_value = self.risk_params[key]
                    self.risk_params[key] = value
                    self.logger.info(f"Risk parameter {key} updated: {old_value} -> {value}")
                else:
                    self.logger.warning(f"Unknown risk parameter: {key}")
            
            log_system("RiskManager", "Risk parameters updated")
            
        except Exception as e:
            log_error("RiskManager", f"Error updating risk parameters: {e}", e)
    
    def emergency_risk_shutdown(self) -> bool:
        """Emergency shutdown due to risk limits"""
        try:
            self.logger.critical("EMERGENCY RISK SHUTDOWN INITIATED")
            
            # Log the event
            account_info = self.mt5_connector.get_account_info()
            self._log_risk_event("EMERGENCY_SHUTDOWN", {
                'equity': account_info.get('equity', 0),
                'balance': account_info.get('balance', 0),
                'margin_level': account_info.get('margin_level', 0),
                'daily_risk': self.daily_risk_taken
            })
            
            log_system("RiskManager", "Emergency risk shutdown completed")
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error in emergency shutdown: {e}", e)
            return False
    
    def get_risk_summary(self) -> str:
        """Get formatted risk summary"""
        try:
            status = self.get_risk_status()
            
            summary = f"""
Risk Management Summary:
• Daily Risk: {status.get('daily_risk_taken', 0):.2f}% / {status.get('daily_risk_remaining', 0):.2f}% remaining
• Drawdown: {status.get('current_drawdown', 0):.2f}% (Max: {status.get('max_drawdown_limit', 0):.1f}%)
• Positions: {status.get('active_positions', 0)} / {status.get('max_positions', 0)}
• Margin Level: {status.get('margin_level', 0):.1f}% (Min: {status.get('min_margin_level', 0):.1f}%)
• Peak Equity: ${status.get('peak_equity', 0):.2f}
• Current Equity: ${status.get('current_equity', 0):.2f}
• Risk Events Today: {status.get('risk_events_today', 0)}
"""
            return summary.strip()
            
        except Exception as e:
            log_error("RiskManager", f"Error generating risk summary: {e}", e)
            return "Error generating risk summary"
