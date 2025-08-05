
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

    def __init__(self, mt5_connector: MT5Connector, risk_manager: 'RiskManager', notifier: TelegramNotifier):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.notifier = notifier
        self.active_orders = {}
        self.pending_orders = {}
        
        self.logger.info("OrderManager initialized")

    def place_market_order(self, symbol: str, order_type: str, volume: float, 
                          sl_pct: float = 0.0, tp_pct: float = 0.0, 
                          comment: str = "AuraTrade") -> Dict[str, Any]:
        """Place market order with percentage-based SL/TP"""
        try:
            # Validate order with risk manager
            if not self.risk_manager.validate_order(symbol, volume):
                return {'success': False, 'error': 'Order rejected by risk manager'}

            # Get current price
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return {'success': False, 'error': f'Cannot get symbol info for {symbol}'}

            current_price = symbol_info['ask'] if order_type == 'buy' else symbol_info['bid']
            
            # Calculate SL/TP based on percentage
            sl_price = 0.0
            tp_price = 0.0
            
            if sl_pct > 0:
                if order_type == 'buy':
                    sl_price = current_price * (1 - sl_pct / 100)
                else:
                    sl_price = current_price * (1 + sl_pct / 100)
            
            if tp_pct > 0:
                if order_type == 'buy':
                    tp_price = current_price * (1 + tp_pct / 100)
                else:
                    tp_price = current_price * (1 - tp_pct / 100)

            # Convert order type
            mt5_order_type = mt5.ORDER_TYPE_BUY if order_type == 'buy' else mt5.ORDER_TYPE_SELL

            # Place order
            result = self.mt5_connector.send_order(
                symbol=symbol,
                order_type=mt5_order_type,
                lot=volume,
                sl=sl_price,
                tp=tp_price,
                comment=comment
            )

            if result['success']:
                # Store order info
                order_info = {
                    'ticket': result['ticket'],
                    'symbol': symbol,
                    'type': order_type,
                    'volume': volume,
                    'price': result['price'],
                    'sl': sl_price,
                    'tp': tp_price,
                    'time': datetime.now(),
                    'comment': comment
                }
                self.active_orders[result['ticket']] = order_info

                # Send notification
                if self.notifier and self.notifier.enabled:
                    message = (
                        f"🎯 Order Executed\n"
                        f"Symbol: {symbol}\n"
                        f"Type: {order_type.upper()}\n"
                        f"Volume: {volume}\n"
                        f"Price: {result['price']}\n"
                        f"SL: {sl_price:.5f}\n"
                        f"TP: {tp_price:.5f}"
                    )
                    self.notifier.send_trade_signal(message)

                self.logger.info(f"Order placed successfully: {result['ticket']}")
                return result

            else:
                self.logger.error(f"Failed to place order: {result['error']}")
                return result

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}

    def close_order(self, ticket: int, reason: str = "Manual close") -> Dict[str, Any]:
        """Close order by ticket"""
        try:
            result = self.mt5_connector.close_position(ticket)
            
            if result['success']:
                # Remove from active orders
                if ticket in self.active_orders:
                    order_info = self.active_orders.pop(ticket)
                    
                    # Send notification
                    if self.notifier and self.notifier.enabled:
                        message = (
                            f"❌ Position Closed\n"
                            f"Ticket: {ticket}\n"
                            f"Symbol: {order_info.get('symbol', 'N/A')}\n"
                            f"Reason: {reason}\n"
                            f"Close Price: {result['price']}"
                        )
                        self.notifier.send_trade_signal(message)

                self.logger.info(f"Order closed successfully: {ticket}")
                return result
            else:
                self.logger.error(f"Failed to close order: {result['error']}")
                return result

        except Exception as e:
            self.logger.error(f"Error closing order: {e}")
            return {'success': False, 'error': str(e)}

    def modify_order(self, ticket: int, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Modify order SL/TP"""
        try:
            result = self.mt5_connector.modify_position(ticket, sl, tp)
            
            if result['success']:
                # Update stored order info
                if ticket in self.active_orders:
                    self.active_orders[ticket]['sl'] = sl
                    self.active_orders[ticket]['tp'] = tp

                self.logger.info(f"Order modified successfully: {ticket}")
                return result
            else:
                self.logger.error(f"Failed to modify order: {result['error']}")
                return result

        except Exception as e:
            self.logger.error(f"Error modifying order: {e}")
            return {'success': False, 'error': str(e)}

    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active orders"""
        try:
            positions = self.mt5_connector.get_positions()
            
            # Update internal tracking
            current_tickets = {pos['ticket'] for pos in positions}
            stored_tickets = set(self.active_orders.keys())
            
            # Remove closed positions from tracking
            for ticket in stored_tickets - current_tickets:
                if ticket in self.active_orders:
                    del self.active_orders[ticket]
            
            return positions
        except Exception as e:
            self.logger.error(f"Error getting active orders: {e}")
            return []

    def close_all_orders(self, symbol: str = None) -> Dict[str, Any]:
        """Close all orders or all orders for specific symbol"""
        try:
            positions = self.get_active_orders()
            closed_count = 0
            failed_count = 0

            for position in positions:
                if symbol is None or position['symbol'] == symbol:
                    result = self.close_order(position['ticket'], "Close all")
                    if result['success']:
                        closed_count += 1
                    else:
                        failed_count += 1

            self.logger.info(f"Closed {closed_count} orders, {failed_count} failed")
            return {'success': True, 'closed': closed_count, 'failed': failed_count}

        except Exception as e:
            self.logger.error(f"Error closing all orders: {e}")
            return {'success': False, 'error': str(e)}

    def get_order_status(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get order status by ticket"""
        try:
            positions = self.get_active_orders()
            for pos in positions:
                if pos['ticket'] == ticket:
                    return pos
            return None
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return None

    def update_trailing_stops(self) -> None:
        """Update trailing stops for profitable positions"""
        try:
            positions = self.get_active_orders()
            
            for position in positions:
                if position['profit'] > 0:  # Only for profitable positions
                    self._update_trailing_stop(position)

        except Exception as e:
            self.logger.error(f"Error updating trailing stops: {e}")

    def _update_trailing_stop(self, position: Dict[str, Any]) -> None:
        """Update trailing stop for individual position"""
        try:
            symbol = position['symbol']
            ticket = position['ticket']
            current_price = position['price_current']
            open_price = position['price_open']
            current_sl = position['sl']
            
            # Get symbol info for point calculation
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return

            # Calculate trailing distance (1% of price)
            trail_distance = current_price * 0.01

            new_sl = 0.0
            should_update = False

            if position['type'] == 0:  # Buy position
                new_sl = current_price - trail_distance
                if current_sl == 0.0 or new_sl > current_sl:
                    should_update = True
            else:  # Sell position
                new_sl = current_price + trail_distance
                if current_sl == 0.0 or new_sl < current_sl:
                    should_update = True

            if should_update:
                result = self.modify_order(ticket, new_sl, position['tp'])
                if result['success']:
                    self.logger.info(f"Trailing stop updated for {ticket}: {new_sl:.5f}")

        except Exception as e:
            self.logger.error(f"Error updating trailing stop: {e}")
