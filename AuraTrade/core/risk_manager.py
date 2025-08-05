
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
        self.mt5_connector = mt5_connector
        self.logger = Logger().get_logger()
        
        # Conservative risk parameters for high win rate
        self.max_risk_per_trade = 0.5  # 0.5% per trade
        self.max_daily_risk = 2.0      # 2% daily risk
        self.max_total_exposure = 5.0   # 5% total exposure
        self.max_drawdown = 3.0        # 3% max drawdown
        
        # Position limits
        self.max_positions_per_symbol = 1
        self.max_total_positions = 5
        
        # Tracking
        self.daily_risk_used = 0.0
        self.current_drawdown = 0.0
        self.peak_equity = 0.0
        
    def calculate_position_size(self, symbol: str, risk_amount: float, 
                              entry_price: float, stop_loss: float) -> float:
        """Calculate optimal position size based on risk"""
        try:
            if stop_loss == 0 or entry_price == 0:
                return 0.0
            
            # Calculate risk in pips
            pip_size = self._get_pip_size(symbol)
            risk_pips = abs(entry_price - stop_loss) / pip_size
            
            if risk_pips <= 0:
                return 0.0
            
            # Calculate position size
            # Risk amount / (risk in pips * pip value per lot)
            pip_value_per_lot = self._get_pip_value_per_lot(symbol)
            position_size = risk_amount / (risk_pips * pip_value_per_lot)
            
            # Round to appropriate decimal places
            position_size = round(position_size, 2)
            
            # Apply additional risk checks
            max_allowed = self._get_max_allowed_position_size(symbol)
            position_size = min(position_size, max_allowed)
            
            return max(position_size, 0.01)  # Minimum 0.01 lots
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating position size: {e}")
            return 0.0
    
    def can_open_position(self, symbol: str, risk_amount: float = None) -> bool:
        """Check if new position can be opened"""
        try:
            # Check daily risk limit
            if self.daily_risk_used >= self.max_daily_risk:
                self.logger.warning(f"⚠️ Daily risk limit reached: {self.daily_risk_used:.2f}%")
                return False
            
            # Check total positions limit
            current_positions = len(self.mt5_connector.get_positions())
            if current_positions >= self.max_total_positions:
                self.logger.warning(f"⚠️ Max total positions reached: {current_positions}")
                return False
            
            # Check positions per symbol
            positions = self.mt5_connector.get_positions()
            symbol_positions = len([p for p in positions if p['symbol'] == symbol])
            if symbol_positions >= self.max_positions_per_symbol:
                self.logger.warning(f"⚠️ Max positions for {symbol} reached: {symbol_positions}")
                return False
            
            # Check drawdown
            if self.current_drawdown >= self.max_drawdown:
                self.logger.warning(f"⚠️ Max drawdown reached: {self.current_drawdown:.2f}%")
                return False
            
            # Check total exposure
            if self._calculate_total_exposure() >= self.max_total_exposure:
                self.logger.warning(f"⚠️ Max total exposure reached")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking position limits: {e}")
            return False
    
    def update_risk_metrics(self):
        """Update risk tracking metrics"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return
            
            current_equity = account_info['equity']
            
            # Update peak equity
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            
            # Calculate current drawdown
            if self.peak_equity > 0:
                self.current_drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
            
            # Update daily risk used (simplified calculation)
            positions = self.mt5_connector.get_positions()
            total_risk = 0.0
            
            for position in positions:
                # Calculate risk for each position
                if position['sl'] > 0:
                    risk_pips = abs(position['price_open'] - position['sl'])
                    # Simplified risk calculation
                    position_risk = (risk_pips * position['volume']) / current_equity * 100
                    total_risk += position_risk
            
            self.daily_risk_used = min(total_risk, self.max_daily_risk)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating risk metrics: {e}")
    
    def check_emergency_stop(self) -> bool:
        """Check if emergency stop should be triggered"""
        try:
            # Update metrics first
            self.update_risk_metrics()
            
            # Check drawdown
            if self.current_drawdown >= self.max_drawdown:
                self.logger.error(f"🚨 EMERGENCY: Max drawdown exceeded: {self.current_drawdown:.2f}%")
                return True
            
            # Check daily risk
            if self.daily_risk_used >= self.max_daily_risk:
                self.logger.error(f"🚨 EMERGENCY: Daily risk limit exceeded: {self.daily_risk_used:.2f}%")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking emergency stop: {e}")
            return True  # Error state triggers emergency stop
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        pip_sizes = {
            'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01,
            'USDCHF': 0.0001, 'AUDUSD': 0.0001, 'USDCAD': 0.0001,
            'NZDUSD': 0.0001, 'XAUUSD': 0.1, 'BTCUSD': 1.0
        }
        return pip_sizes.get(symbol, 0.0001)
    
    def _get_pip_value_per_lot(self, symbol: str) -> float:
        """Get pip value per lot for symbol"""
        # Simplified calculation - in practice, this depends on account currency
        pip_values = {
            'EURUSD': 10.0, 'GBPUSD': 10.0, 'USDJPY': 10.0,
            'USDCHF': 10.0, 'AUDUSD': 10.0, 'USDCAD': 10.0,
            'NZDUSD': 10.0, 'XAUUSD': 1.0, 'BTCUSD': 0.1
        }
        return pip_values.get(symbol, 10.0)
    
    def _get_max_allowed_position_size(self, symbol: str) -> float:
        """Get maximum allowed position size for symbol"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.01
            
            # Conservative position sizing: max 1% of equity per position
            max_risk_amount = account_info['equity'] * 0.01
            
            # Convert to lots (simplified)
            return min(max_risk_amount / 1000, 10.0)  # Max 10 lots
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating max position size: {e}")
            return 0.01
    
    def _calculate_total_exposure(self) -> float:
        """Calculate total portfolio exposure"""
        try:
            positions = self.mt5_connector.get_positions()
            account_info = self.mt5_connector.get_account_info()
            
            if not account_info:
                return 0.0
            
            total_exposure = 0.0
            for position in positions:
                # Calculate exposure as percentage of equity
                position_value = position['volume'] * position['price_open']
                exposure = (position_value / account_info['equity']) * 100
                total_exposure += exposure
            
            return total_exposure
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating total exposure: {e}")
            return 0.0
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        self.update_risk_metrics()
        
        return {
            'daily_risk_used': self.daily_risk_used,
            'max_daily_risk': self.max_daily_risk,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'total_exposure': self._calculate_total_exposure(),
            'max_total_exposure': self.max_total_exposure,
            'peak_equity': self.peak_equity,
            'risk_per_trade': self.max_risk_per_trade
        }
