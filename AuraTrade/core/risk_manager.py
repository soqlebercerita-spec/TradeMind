
"""
Risk management system for AuraTrade Bot
Implements conservative risk controls for high win rate trading
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class RiskManager:
    """Conservative risk management for high win rate trading"""

    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Risk parameters
        self.max_risk_per_trade = 2.0  # 2% per trade
        self.max_daily_risk = 6.0      # 6% daily risk
        self.max_drawdown = 10.0       # 10% max drawdown
        self.max_positions = 5         # Max concurrent positions
        self.max_symbol_exposure = 3.0 # Max 3% per symbol
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # Risk metrics
        self.current_drawdown = 0.0
        self.peak_equity = 0.0
        
        self.logger.info("RiskManager initialized with conservative parameters")

    def validate_order(self, symbol: str, volume: float) -> bool:
        """Validate if order meets risk criteria"""
        try:
            # Check daily reset
            self._check_daily_reset()
            
            # Get account info
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                self.logger.warning("Cannot get account info for risk validation")
                return False

            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            
            # Update peak equity and drawdown
            if equity > self.peak_equity:
                self.peak_equity = equity
            
            self.current_drawdown = ((self.peak_equity - equity) / self.peak_equity) * 100
            
            # Check maximum drawdown
            if self.current_drawdown > self.max_drawdown:
                self.logger.warning(f"Max drawdown exceeded: {self.current_drawdown:.2f}%")
                return False
            
            # Check daily risk limit
            if abs(self.daily_pnl) > (balance * self.max_daily_risk / 100):
                self.logger.warning(f"Daily risk limit exceeded: {self.daily_pnl:.2f}")
                return False
            
            # Check maximum positions
            positions = self.mt5_connector.get_positions()
            if len(positions) >= self.max_positions:
                self.logger.warning(f"Maximum positions limit reached: {len(positions)}")
                return False
            
            # Check symbol exposure
            symbol_exposure = self._calculate_symbol_exposure(symbol, volume, balance)
            if symbol_exposure > self.max_symbol_exposure:
                self.logger.warning(f"Symbol exposure limit exceeded: {symbol_exposure:.2f}%")
                return False
            
            # Check trade size risk
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info:
                contract_size = symbol_info.get('trade_contract_size', 100000)
                trade_value = volume * contract_size
                trade_risk = (trade_value / balance) * 100
                
                if trade_risk > self.max_risk_per_trade:
                    self.logger.warning(f"Trade risk too high: {trade_risk:.2f}%")
                    return False
            
            self.logger.info(f"Order validated: {symbol} {volume} lots")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating order: {e}")
            return False

    def calculate_position_size(self, symbol: str, risk_pct: float = None) -> float:
        """Calculate optimal position size based on risk"""
        try:
            if risk_pct is None:
                risk_pct = self.max_risk_per_trade
            
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.01  # Minimum lot
            
            balance = account_info.get('balance', 0)
            risk_amount = balance * (risk_pct / 100)
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.01
            
            contract_size = symbol_info.get('trade_contract_size', 100000)
            tick_value = symbol_info.get('trade_tick_value', 1)
            
            # Calculate position size (conservative approach)
            # Assume 50 pip stop loss for calculation
            pip_value = tick_value * 10  # Approximate pip value
            stop_loss_pips = 50
            
            position_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Round to valid lot size (0.01 increments)
            position_size = round(position_size / 0.01) * 0.01
            
            # Apply limits
            min_lot = 0.01
            max_lot = min(1.0, balance / 10000)  # Conservative max lot
            
            position_size = max(min_lot, min(position_size, max_lot))
            
            self.logger.info(f"Calculated position size for {symbol}: {position_size}")
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.01

    def update_daily_pnl(self, pnl: float) -> None:
        """Update daily P&L tracking"""
        try:
            self._check_daily_reset()
            self.daily_pnl += pnl
            self.daily_trades += 1
            
            self.logger.info(f"Daily P&L updated: ${self.daily_pnl:.2f}, Trades: {self.daily_trades}")
            
        except Exception as e:
            self.logger.error(f"Error updating daily P&L: {e}")

    def should_stop_trading(self) -> bool:
        """Check if trading should be stopped due to risk limits"""
        try:
            # Check daily reset
            self._check_daily_reset()
            
            # Check drawdown limit
            if self.current_drawdown > self.max_drawdown:
                self.logger.warning("Trading stopped: Maximum drawdown exceeded")
                return True
            
            # Check daily loss limit
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                balance = account_info.get('balance', 0)
                daily_loss_limit = balance * (self.max_daily_risk / 100)
                
                if self.daily_pnl < -daily_loss_limit:
                    self.logger.warning("Trading stopped: Daily loss limit exceeded")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking stop trading condition: {e}")
            return False

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        try:
            account_info = self.mt5_connector.get_account_info()
            positions = self.mt5_connector.get_positions()
            
            total_exposure = 0.0
            if account_info and positions:
                balance = account_info.get('balance', 0)
                for pos in positions:
                    total_exposure += abs(pos.get('profit', 0))
            
            return {
                'current_drawdown': self.current_drawdown,
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades,
                'active_positions': len(positions),
                'total_exposure': total_exposure,
                'max_drawdown': self.max_drawdown,
                'max_daily_risk': self.max_daily_risk,
                'max_positions': self.max_positions
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return {}

    def _check_daily_reset(self) -> None:
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = current_date
            self.logger.info("Daily risk counters reset")

    def _calculate_symbol_exposure(self, symbol: str, volume: float, balance: float) -> float:
        """Calculate exposure percentage for symbol"""
        try:
            # Get existing exposure
            positions = self.mt5_connector.get_positions()
            existing_volume = sum(pos['volume'] for pos in positions if pos['symbol'] == symbol)
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            contract_size = symbol_info.get('trade_contract_size', 100000)
            current_price = symbol_info.get('bid', 1.0)
            
            # Calculate total exposure
            total_volume = existing_volume + volume
            total_value = total_volume * contract_size * current_price
            
            exposure_pct = (total_value / balance) * 100 if balance > 0 else 0
            return exposure_pct
            
        except Exception as e:
            self.logger.error(f"Error calculating symbol exposure: {e}")
            return 0.0

    def set_risk_parameters(self, max_risk_per_trade: float = None, 
                           max_daily_risk: float = None, 
                           max_drawdown: float = None) -> None:
        """Update risk parameters"""
        try:
            if max_risk_per_trade is not None:
                self.max_risk_per_trade = max_risk_per_trade
            if max_daily_risk is not None:
                self.max_daily_risk = max_daily_risk
            if max_drawdown is not None:
                self.max_drawdown = max_drawdown
                
            self.logger.info(f"Risk parameters updated: Risk/Trade: {self.max_risk_per_trade}%, Daily: {self.max_daily_risk}%, Drawdown: {self.max_drawdown}%")
            
        except Exception as e:
            self.logger.error(f"Error setting risk parameters: {e}")
