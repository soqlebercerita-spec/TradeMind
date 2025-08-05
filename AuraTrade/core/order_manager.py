
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
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.notifier = notifier
        
        # Order tracking
        self.active_orders = {}
        self.order_history = []
        
        self.logger.info("Order Manager initialized")
    
    def place_order(self, symbol: str, order_type: int, lot_size: float, 
                   price: float = 0.0, sl: float = 0.0, tp: float = 0.0, 
                   comment: str = "") -> Dict[str, Any]:
        """Place a trading order with risk checks"""
        try:
            self.logger.info(f"Placing order: {symbol} {'BUY' if order_type == 0 else 'SELL'} {lot_size} lots")
            
            # Pre-trade risk checks
            risk_check = self.risk_manager.check_trade_risk(symbol, lot_size, price)
            if not risk_check['allowed']:
                self.logger.warning(f"Trade blocked by risk manager: {risk_check['reason']}")
                return {'success': False, 'error': risk_check['reason']}
            
            # Validate lot size
            lot_size = self._validate_lot_size(symbol, lot_size)
            if lot_size <= 0:
                return {'success': False, 'error': 'Invalid lot size'}
            
            # Validate SL/TP levels
            sl, tp = self._validate_sl_tp(symbol, order_type, price, sl, tp)
            
            # Send order to MT5
            result = self.mt5_connector.send_order(
                symbol=symbol,
                order_type=order_type,
                lot=lot_size,
                price=price,
                sl=sl,
                tp=tp,
                comment=comment
            )
            
            if result['success']:
                # Track the order
                order_info = {
                    'ticket': result['ticket'],
                    'symbol': symbol,
                    'type': order_type,
                    'volume': lot_size,
                    'price': result['price'],
                    'sl': sl,
                    'tp': tp,
                    'time': datetime.now(),
                    'comment': comment
                }
                
                self.active_orders[result['ticket']] = order_info
                self.order_history.append(order_info)
                
                # Update risk manager
                self.risk_manager.on_order_placed(order_info)
                
                self.logger.info(f"Order placed successfully - Ticket: {result['ticket']}")
                
                return {
                    'success': True,
                    'ticket': result['ticket'],
                    'price': result['price'],
                    'volume': lot_size
                }
            else:
                self.logger.error(f"Order placement failed: {result['error']}")
                return result
                
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_order(self, ticket: int, partial_volume: float = 0.0) -> Dict[str, Any]:
        """Close an order (full or partial)"""
        try:
            self.logger.info(f"Closing order: {ticket}")
            
            result = self.mt5_connector.close_position(ticket)
            
            if result['success']:
                # Remove from active orders
                if ticket in self.active_orders:
                    order_info = self.active_orders[ticket]
                    del self.active_orders[ticket]
                    
                    # Update risk manager
                    self.risk_manager.on_order_closed(ticket, order_info)
                    
                    # Send notification if enabled
                    if self.notifier and self.notifier.enabled:
                        positions = self.mt5_connector.get_positions()
                        position = next((p for p in positions if p['ticket'] == ticket), None)
                        if position:
                            profit = position['profit']
                            message = (
                                f"{'✅' if profit > 0 else '❌'} Position Closed\n"
                                f"Ticket: {ticket}\n"
                                f"Symbol: {order_info['symbol']}\n"
                                f"Profit: ${profit:.2f}"
                            )
                            self.notifier.send_trade_alert(message)
                
                self.logger.info(f"Order closed successfully - Ticket: {ticket}")
                return result
            else:
                self.logger.error(f"Order closure failed: {result['error']}")
                return result
                
        except Exception as e:
            self.logger.error(f"Error closing order: {e}")
            return {'success': False, 'error': str(e)}
    
    def modify_order(self, ticket: int, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Modify order SL/TP"""
        try:
            self.logger.info(f"Modifying order: {ticket}")
            
            # Get current position info
            positions = self.mt5_connector.get_positions()
            position = next((p for p in positions if p['ticket'] == ticket), None)
            
            if not position:
                return {'success': False, 'error': 'Position not found'}
            
            # Use current values if not specified
            if sl is None:
                sl = position['sl']
            if tp is None:
                tp = position['tp']
            
            # Validate SL/TP levels
            sl, tp = self._validate_sl_tp(position['symbol'], position['type'], 
                                        position['price_current'], sl, tp)
            
            result = self.mt5_connector.modify_position(ticket, sl, tp)
            
            if result['success']:
                # Update active order info
                if ticket in self.active_orders:
                    self.active_orders[ticket]['sl'] = sl
                    self.active_orders[ticket]['tp'] = tp
                
                self.logger.info(f"Order modified successfully - Ticket: {ticket}")
                return result
            else:
                self.logger.error(f"Order modification failed: {result['error']}")
                return result
                
        except Exception as e:
            self.logger.error(f"Error modifying order: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_all_orders(self, symbol: str = None) -> Dict[str, Any]:
        """Close all orders (optionally for specific symbol)"""
        try:
            self.logger.info(f"Closing all orders{' for ' + symbol if symbol else ''}")
            
            positions = self.mt5_connector.get_positions()
            closed_count = 0
            errors = []
            
            for position in positions:
                if symbol is None or position['symbol'] == symbol:
                    result = self.close_order(position['ticket'])
                    if result['success']:
                        closed_count += 1
                    else:
                        errors.append(f"Failed to close {position['ticket']}: {result['error']}")
            
            return {
                'success': len(errors) == 0,
                'closed_count': closed_count,
                'errors': errors
            }
            
        except Exception as e:
            self.logger.error(f"Error closing all orders: {e}")
            return {'success': False, 'error': str(e)}
    
    def _validate_lot_size(self, symbol: str, lot_size: float) -> float:
        """Validate and adjust lot size"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info is None:
                return 0.0
            
            # Get symbol specifications (these would be retrieved from MT5)
            min_lot = 0.01  # Typically 0.01 for forex
            max_lot = 100.0  # Typically 100 for forex
            lot_step = 0.01  # Typically 0.01 for forex
            
            # Adjust to valid range
            lot_size = max(min_lot, min(max_lot, lot_size))
            
            # Round to lot step
            lot_size = round(lot_size / lot_step) * lot_step
            
            return lot_size
            
        except Exception as e:
            self.logger.error(f"Error validating lot size: {e}")
            return 0.0
    
    def _validate_sl_tp(self, symbol: str, order_type: int, price: float, 
                       sl: float, tp: float) -> tuple:
        """Validate and adjust SL/TP levels"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info is None:
                return sl, tp
            
            # Minimum distance (typically 10 points for major pairs)
            min_distance = 10 * symbol_info['point']
            
            if order_type == 0:  # BUY order
                # SL should be below price
                if sl > 0 and sl >= price - min_distance:
                    sl = price - min_distance
                # TP should be above price
                if tp > 0 and tp <= price + min_distance:
                    tp = price + min_distance
            else:  # SELL order
                # SL should be above price
                if sl > 0 and sl <= price + min_distance:
                    sl = price + min_distance
                # TP should be below price
                if tp > 0 and tp >= price - min_distance:
                    tp = price - min_distance
            
            return sl, tp
            
        except Exception as e:
            self.logger.error(f"Error validating SL/TP: {e}")
            return sl, tp
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get list of active orders"""
        try:
            # Sync with MT5 positions
            positions = self.mt5_connector.get_positions()
            mt5_tickets = {p['ticket'] for p in positions}
            
            # Remove closed orders from tracking
            closed_tickets = set(self.active_orders.keys()) - mt5_tickets
            for ticket in closed_tickets:
                if ticket in self.active_orders:
                    del self.active_orders[ticket]
            
            return list(self.active_orders.values())
            
        except Exception as e:
            self.logger.error(f"Error getting active orders: {e}")
            return []
    
    def get_order_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history"""
        return self.order_history[-limit:] if limit > 0 else self.order_history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get order statistics"""
        try:
            total_orders = len(self.order_history)
            active_orders = len(self.active_orders)
            
            # Calculate win/loss from closed positions
            # This would typically come from trade history
            wins = 0
            losses = 0
            total_profit = 0.0
            
            return {
                'total_orders': total_orders,
                'active_orders': active_orders,
                'wins': wins,
                'losses': losses,
                'win_rate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0,
                'total_profit': total_profit
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
