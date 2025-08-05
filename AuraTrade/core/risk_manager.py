
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
        self.mt5_connector = mt5_connector
        
        # Risk parameters
        self.max_risk_per_trade = 0.02  # 2% per trade
        self.max_daily_risk = 0.05  # 5% daily
        self.max_drawdown = 0.10  # 10% max drawdown
        self.max_positions = 5  # Max concurrent positions
        self.max_positions_per_symbol = 2  # Max per symbol
        self.max_exposure_per_currency = 0.20  # 20% exposure per currency
        
        # Tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.start_balance = 0.0
        self.peak_balance = 0.0
        self.trade_history = []
        
        # Emergency stops
        self.emergency_stop = False
        self.trading_disabled = False
        
        self.logger.info("Risk Manager initialized")
    
    def initialize(self):
        """Initialize risk manager with current account state"""
        try:
            account_info = self.mt5_connector.get_account_info()
            self.start_balance = account_info.get('balance', 0.0)
            self.peak_balance = self.start_balance
            
            self.logger.info(f"Risk Manager initialized - Start Balance: ${self.start_balance:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error initializing risk manager: {e}")
    
    def check_global_risk(self) -> bool:
        """Check global risk limits"""
        try:
            if self.emergency_stop or self.trading_disabled:
                return False
            
            account_info = self.mt5_connector.get_account_info()
            current_balance = account_info.get('balance', 0.0)
            equity = account_info.get('equity', 0.0)
            
            # Check maximum drawdown
            if self.start_balance > 0:
                current_drawdown = (self.start_balance - current_balance) / self.start_balance
                if current_drawdown > self.max_drawdown:
                    self.logger.error(f"Maximum drawdown exceeded: {current_drawdown:.2%}")
                    self.emergency_stop = True
                    return False
            
            # Check daily risk limit
            daily_risk = abs(self.daily_pnl) / self.start_balance if self.start_balance > 0 else 0
            if daily_risk > self.max_daily_risk:
                self.logger.warning(f"Daily risk limit exceeded: {daily_risk:.2%}")
                return False
            
            # Check number of positions
            positions = self.mt5_connector.get_positions()
            if len(positions) >= self.max_positions:
                self.logger.warning(f"Maximum positions reached: {len(positions)}")
                return False
            
            # Check margin level
            margin_level = account_info.get('margin_level', 1000.0)
            if margin_level < 200.0:  # Below 200% margin level
                self.logger.warning(f"Low margin level: {margin_level:.1f}%")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in global risk check: {e}")
            return False
    
    def check_trade_risk(self, symbol: str, lot_size: float, price: float) -> Dict[str, Any]:
        """Check if a specific trade is allowed"""
        try:
            # Check if trading is disabled
            if self.emergency_stop or self.trading_disabled:
                return {'allowed': False, 'reason': 'Trading disabled'}
            
            # Check symbol-specific position limits
            positions = self.mt5_connector.get_positions()
            symbol_positions = [p for p in positions if p['symbol'] == symbol]
            
            if len(symbol_positions) >= self.max_positions_per_symbol:
                return {'allowed': False, 'reason': f'Max positions for {symbol} reached'}
            
            # Check currency exposure
            currency_exposure = self._calculate_currency_exposure(symbol)
            if currency_exposure > self.max_exposure_per_currency:
                return {'allowed': False, 'reason': f'Currency exposure limit exceeded: {currency_exposure:.1%}'}
            
            # Check trade size vs account balance
            account_info = self.mt5_connector.get_account_info()
            balance = account_info.get('balance', 0.0)
            
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info is None:
                return {'allowed': False, 'reason': 'Symbol info not available'}
            
            # Calculate trade value
            trade_value = lot_size * symbol_info['trade_contract_size'] * price
            risk_percentage = trade_value / balance if balance > 0 else 1.0
            
            if risk_percentage > self.max_risk_per_trade:
                return {'allowed': False, 'reason': f'Trade risk too high: {risk_percentage:.2%}'}
            
            # Check spread
            spread_pips = symbol_info['spread'] * symbol_info['point'] * 10
            if spread_pips > 5.0:  # Max 5 pip spread
                return {'allowed': False, 'reason': f'Spread too wide: {spread_pips:.1f} pips'}
            
            return {'allowed': True, 'reason': 'Trade approved'}
            
        except Exception as e:
            self.logger.error(f"Error in trade risk check: {e}")
            return {'allowed': False, 'reason': f'Risk check error: {e}'}
    
    def _calculate_currency_exposure(self, symbol: str) -> float:
        """Calculate current exposure to a currency"""
        try:
            # Extract base and quote currencies
            if len(symbol) >= 6:
                base_currency = symbol[:3]
                quote_currency = symbol[3:6]
            else:
                return 0.0
            
            positions = self.mt5_connector.get_positions()
            account_info = self.mt5_connector.get_account_info()
            balance = account_info.get('balance', 1.0)
            
            total_exposure = 0.0
            
            for position in positions:
                pos_symbol = position['symbol']
                if len(pos_symbol) >= 6:
                    pos_base = pos_symbol[:3]
                    pos_quote = pos_symbol[3:6]
                    
                    # Calculate position value
                    position_value = abs(position['volume'] * position['price_current'])
                    
                    # Check if currencies match
                    if pos_base == base_currency or pos_quote == base_currency:
                        total_exposure += position_value
            
            return total_exposure / balance if balance > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating currency exposure: {e}")
            return 0.0
    
    def on_order_placed(self, order_info: Dict[str, Any]):
        """Handle order placement event"""
        try:
            self.daily_trades += 1
            self.trade_history.append({
                'time': datetime.now(),
                'action': 'open',
                'ticket': order_info['ticket'],
                'symbol': order_info['symbol'],
                'volume': order_info['volume'],
                'price': order_info['price']
            })
            
            self.logger.info(f"Order placed tracked - Daily trades: {self.daily_trades}")
            
        except Exception as e:
            self.logger.error(f"Error tracking order placement: {e}")
    
    def on_order_closed(self, ticket: int, order_info: Dict[str, Any]):
        """Handle order closure event"""
        try:
            # Get position profit
            positions = self.mt5_connector.get_positions()
            position = next((p for p in positions if p['ticket'] == ticket), None)
            
            profit = position['profit'] if position else 0.0
            self.daily_pnl += profit
            
            # Update peak balance
            account_info = self.mt5_connector.get_account_info()
            current_balance = account_info.get('balance', 0.0)
            self.peak_balance = max(self.peak_balance, current_balance)
            
            self.trade_history.append({
                'time': datetime.now(),
                'action': 'close',
                'ticket': ticket,
                'symbol': order_info['symbol'],
                'profit': profit
            })
            
            self.logger.info(f"Order closure tracked - Profit: ${profit:.2f}, Daily P&L: ${self.daily_pnl:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error tracking order closure: {e}")
    
    def check_emergency_conditions(self) -> bool:
        """Check for emergency stop conditions"""
        try:
            account_info = self.mt5_connector.get_account_info()
            balance = account_info.get('balance', 0.0)
            equity = account_info.get('equity', 0.0)
            margin_level = account_info.get('margin_level', 1000.0)
            
            # Check for margin call
            if margin_level < 100.0:
                self.logger.error("EMERGENCY: Margin call level reached!")
                self.emergency_stop = True
                return True
            
            # Check for large unrealized losses
            unrealized_loss = balance - equity
            if unrealized_loss > balance * 0.05:  # 5% unrealized loss
                self.logger.error(f"EMERGENCY: Large unrealized loss: ${unrealized_loss:.2f}")
                self.emergency_stop = True
                return True
            
            # Check for consecutive losses
            recent_trades = self.trade_history[-10:]  # Last 10 trades
            consecutive_losses = 0
            
            for trade in reversed(recent_trades):
                if trade['action'] == 'close' and trade.get('profit', 0) < 0:
                    consecutive_losses += 1
                else:
                    break
            
            if consecutive_losses >= 5:
                self.logger.error(f"EMERGENCY: {consecutive_losses} consecutive losses")
                self.emergency_stop = True
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking emergency conditions: {e}")
            return False
    
    def reset_daily_limits(self):
        """Reset daily limits (should be called at start of new day)"""
        try:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            
            # Update start balance for new day
            account_info = self.mt5_connector.get_account_info()
            self.start_balance = account_info.get('balance', 0.0)
            
            self.logger.info("Daily limits reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting daily limits: {e}")
    
    def enable_trading(self):
        """Enable trading"""
        self.trading_disabled = False
        self.emergency_stop = False
        self.logger.info("Trading enabled")
    
    def disable_trading(self, reason: str = "Manual disable"):
        """Disable trading"""
        self.trading_disabled = True
        self.logger.warning(f"Trading disabled: {reason}")
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        try:
            account_info = self.mt5_connector.get_account_info()
            balance = account_info.get('balance', 0.0)
            equity = account_info.get('equity', 0.0)
            
            # Calculate drawdown
            current_drawdown = 0.0
            if self.start_balance > 0:
                current_drawdown = (self.start_balance - balance) / self.start_balance
            
            # Calculate daily risk
            daily_risk = 0.0
            if self.start_balance > 0:
                daily_risk = abs(self.daily_pnl) / self.start_balance
            
            positions = self.mt5_connector.get_positions()
            
            return {
                'emergency_stop': self.emergency_stop,
                'trading_disabled': self.trading_disabled,
                'balance': balance,
                'equity': equity,
                'start_balance': self.start_balance,
                'peak_balance': self.peak_balance,
                'current_drawdown': current_drawdown,
                'max_drawdown': self.max_drawdown,
                'daily_pnl': self.daily_pnl,
                'daily_risk': daily_risk,
                'max_daily_risk': self.max_daily_risk,
                'daily_trades': self.daily_trades,
                'open_positions': len(positions),
                'max_positions': self.max_positions,
                'margin_level': account_info.get('margin_level', 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk status: {e}")
            return {'error': str(e)}
