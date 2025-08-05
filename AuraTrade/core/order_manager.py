
"""
Order management system for AuraTrade Bot
Handles order placement, modification, and risk management
"""

import MetaTrader5 as mt5
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger
from utils.notifier import TelegramNotifier

class OrderManager:
    """Advanced order management with risk controls"""

    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager, notifier: TelegramNotifier):
        self.logger = Logger().get_logger()
        self.mt5 = mt5_connector
        self.risk_manager = risk_manager
        self.notifier = notifier
        
        # Order tracking
        self.pending_orders = {}
        self.active_positions = {}
        self.order_history = []
        
        # Risk limits
        self.max_positions = 10
        self.max_daily_trades = 50
        self.daily_trade_count = 0
        
        self.logger.info("OrderManager initialized")

    def send_market_order(self, symbol: str, order_type: str, volume: float, 
                         sl: float = 0.0, tp: float = 0.0, comment: str = "") -> Dict[str, Any]:
        """Send market order with risk validation"""
        try:
            # Validate order
            if not self._validate_order(symbol, volume):
                return {'success': False, 'error': 'Order validation failed'}

            # Convert order type
            mt5_order_type = mt5.ORDER_TYPE_BUY if order_type.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
            
            # Send order
            result = self.mt5.send_order(symbol, mt5_order_type, volume, 0.0, sl, tp, comment)
            
            if result['success']:
                self.daily_trade_count += 1
                self._track_order(result, symbol, order_type, volume)
                
                # Send notification
                if self.notifier.enabled:
                    self.notifier.send_trade_notification(
                        'OPENED', symbol, order_type, volume, 
                        result.get('price', 0), sl, tp
                    )
                
                self.logger.info(f"Market order executed: {symbol} {order_type} {volume}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error sending market order: {e}")
            return {'success': False, 'error': str(e)}

    def close_position(self, ticket: int, reason: str = "Manual") -> Dict[str, Any]:
        """Close position with tracking"""
        try:
            result = self.mt5.close_position(ticket)
            
            if result['success']:
                # Update tracking
                if ticket in self.active_positions:
                    position = self.active_positions.pop(ticket)
                    
                    # Send notification
                    if self.notifier.enabled:
                        self.notifier.send_trade_notification(
                            'CLOSED', position.get('symbol', ''), 
                            position.get('type', ''), position.get('volume', 0),
                            result.get('price', 0), 0, 0, reason
                        )
                
                self.logger.info(f"Position closed: {ticket} - {reason}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}

    def modify_position(self, ticket: int, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Modify position SL/TP"""
        try:
            result = self.mt5.modify_position(ticket, sl, tp)
            
            if result['success']:
                # Update tracking
                if ticket in self.active_positions:
                    self.active_positions[ticket].update({'sl': sl, 'tp': tp})
                
                self.logger.info(f"Position modified: {ticket} SL:{sl} TP:{tp}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error modifying position: {e}")
            return {'success': False, 'error': str(e)}

    def update_positions(self):
        """Update active positions tracking"""
        try:
            positions = self.mt5.get_positions()
            current_tickets = {pos['ticket'] for pos in positions}
            
            # Update active positions
            self.active_positions = {pos['ticket']: pos for pos in positions}
            
            return len(positions)
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
            return 0

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily trading statistics"""
        try:
            positions = self.mt5.get_positions()
            total_profit = sum(pos['profit'] for pos in positions)
            
            return {
                'daily_trades': self.daily_trade_count,
                'active_positions': len(positions),
                'total_profit': total_profit,
                'max_positions': self.max_positions,
                'max_daily_trades': self.max_daily_trades
            }
            
        except Exception as e:
            self.logger.error(f"Error getting daily stats: {e}")
            return {}

    def _validate_order(self, symbol: str, volume: float) -> bool:
        """Validate order before sending"""
        try:
            # Check daily trade limit
            if self.daily_trade_count >= self.max_daily_trades:
                self.logger.warning("Daily trade limit reached")
                return False
            
            # Check position limit
            if len(self.active_positions) >= self.max_positions:
                self.logger.warning("Maximum positions limit reached")
                return False
            
            # Check risk manager
            if not self.risk_manager.can_open_position(symbol, volume):
                self.logger.warning("Risk manager rejected order")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating order: {e}")
            return False

    def _track_order(self, result: Dict, symbol: str, order_type: str, volume: float):
        """Track order for monitoring"""
        try:
            if 'ticket' in result:
                self.active_positions[result['ticket']] = {
                    'symbol': symbol,
                    'type': order_type,
                    'volume': volume,
                    'time': datetime.now(),
                    'price': result.get('price', 0)
                }
                
                self.order_history.append({
                    'ticket': result['ticket'],
                    'symbol': symbol,
                    'type': order_type,
                    'volume': volume,
                    'time': datetime.now(),
                    'status': 'OPENED'
                })
                
        except Exception as e:
            self.logger.error(f"Error tracking order: {e}")

    def cleanup_daily_stats(self):
        """Reset daily statistics"""
        self.daily_trade_count = 0
        self.logger.info("Daily statistics reset")
