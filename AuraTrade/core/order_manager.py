
"""
Order management system for AuraTrade Bot
Handles order placement, modification, and risk management
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger, log_trade, log_error
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
        self.daily_stats = {
            'orders_placed': 0,
            'orders_closed': 0,
            'total_profit': 0.0,
            'wins': 0,
            'losses': 0
        }
        
        # Risk limits
        self.max_orders_per_symbol = 3
        self.max_daily_orders = 100
        self.min_order_interval = 5  # seconds between orders
        self.last_order_time = {}
        
        self.logger.info("Order Manager initialized with risk controls")
    
    def place_market_order(self, symbol: str, action: str, volume: float, 
                          sl_pips: float = 0, tp_pips: float = 0, 
                          comment: str = "AuraTrade") -> Optional[Dict[str, Any]]:
        """Place market order with comprehensive risk checks"""
        try:
            # Pre-trade risk checks
            if not self._pre_trade_checks(symbol, action, volume):
                return None
            
            # Get current price
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                log_error("OrderManager", f"No tick data for {symbol}", None)
                return None
            
            # Calculate SL and TP prices
            sl_price, tp_price = self._calculate_sl_tp_prices(symbol, action, tick, sl_pips, tp_pips)
            
            # Execute order
            result = self.mt5_connector.send_order(
                action=action,
                symbol=symbol,
                volume=volume,
                price=0.0,  # Market order
                sl=sl_price,
                tp=tp_price,
                comment=comment
            )
            
            if result and result.get('retcode') == 10009:
                # Order successful
                order_data = {
                    'ticket': result.get('deal', 0),
                    'symbol': symbol,
                    'action': action,
                    'volume': volume,
                    'entry_price': result.get('price', 0),
                    'sl_price': sl_price,
                    'tp_price': tp_price,
                    'timestamp': datetime.now(),
                    'comment': comment,
                    'status': 'OPEN'
                }
                
                # Track order
                self.active_orders[order_data['ticket']] = order_data
                self.order_history.append(order_data.copy())
                
                # Update stats
                self.daily_stats['orders_placed'] += 1
                self.last_order_time[symbol] = time.time()
                
                # Log trade
                log_trade(action, symbol, volume, result.get('price', 0))
                
                # Send notification
                if self.notifier and self.notifier.enabled:
                    self.notifier.send_trade_signal(
                        action.upper(),
                        symbol,
                        volume,
                        result.get('price', 0),
                        f"Order placed: {comment}"
                    )
                
                self.logger.info(f"Order placed: {action.upper()} {volume} {symbol} at {result.get('price', 0):.5f}")
                return result
            else:
                error_msg = result.get('comment', 'Unknown error') if result else 'Connection error'
                log_error("OrderManager", f"Order failed: {error_msg}", None)
                return None
                
        except Exception as e:
            log_error("OrderManager", f"Error placing order: {e}", e)
            return None
    
    def close_order(self, ticket: int) -> bool:
        """Close specific order by ticket"""
        try:
            if ticket not in self.active_orders:
                self.logger.warning(f"Order {ticket} not found in active orders")
                return False
            
            result = self.mt5_connector.close_position(ticket)
            
            if result and result.get('retcode') == 10009:
                # Order closed successfully
                order_data = self.active_orders[ticket]
                order_data['close_price'] = result.get('price', 0)
                order_data['close_time'] = datetime.now()
                order_data['profit'] = result.get('profit', 0)
                order_data['status'] = 'CLOSED'
                
                # Update stats
                self.daily_stats['orders_closed'] += 1
                self.daily_stats['total_profit'] += result.get('profit', 0)
                
                if result.get('profit', 0) > 0:
                    self.daily_stats['wins'] += 1
                else:
                    self.daily_stats['losses'] += 1
                
                # Remove from active orders
                del self.active_orders[ticket]
                
                # Send notification
                if self.notifier and self.notifier.enabled:
                    profit = result.get('profit', 0)
                    self.notifier.send_trade_signal(
                        "CLOSE",
                        order_data['symbol'],
                        order_data['volume'],
                        result.get('price', 0),
                        f"Position closed | P&L: ${profit:.2f}"
                    )
                
                self.logger.info(f"Order {ticket} closed with profit: ${result.get('profit', 0):.2f}")
                return True
            else:
                log_error("OrderManager", f"Failed to close order {ticket}", None)
                return False
                
        except Exception as e:
            log_error("OrderManager", f"Error closing order {ticket}: {e}", e)
            return False
    
    def close_all_orders(self, symbol: str = None) -> int:
        """Close all orders or all orders for specific symbol"""
        try:
            closed_count = 0
            orders_to_close = list(self.active_orders.keys())
            
            for ticket in orders_to_close:
                order_data = self.active_orders[ticket]
                
                # Filter by symbol if specified
                if symbol and order_data['symbol'] != symbol:
                    continue
                
                if self.close_order(ticket):
                    closed_count += 1
                
                time.sleep(0.1)  # Small delay between closes
            
            self.logger.info(f"Closed {closed_count} orders" + (f" for {symbol}" if symbol else ""))
            return closed_count
            
        except Exception as e:
            log_error("OrderManager", f"Error closing all orders: {e}", e)
            return 0
    
    def emergency_close_all(self) -> int:
        """Emergency close all positions immediately"""
        try:
            self.logger.warning("EMERGENCY CLOSE ALL INITIATED")
            
            # Get all positions from MT5
            positions = self.mt5_connector.get_positions()
            closed_count = 0
            
            for position in positions:
                try:
                    result = self.mt5_connector.close_position(position['ticket'])
                    if result and result.get('retcode') == 10009:
                        closed_count += 1
                        
                        # Update our tracking if order exists
                        if position['ticket'] in self.active_orders:
                            del self.active_orders[position['ticket']]
                            
                except Exception as e:
                    self.logger.error(f"Error closing position {position['ticket']}: {e}")
            
            # Send emergency notification
            if self.notifier and self.notifier.enabled:
                self.notifier.send_system_status(
                    "emergency_close",
                    f"EMERGENCY CLOSE EXECUTED - {closed_count} positions closed"
                )
            
            self.logger.warning(f"Emergency close completed: {closed_count} positions closed")
            return closed_count
            
        except Exception as e:
            log_error("OrderManager", f"Error in emergency close: {e}", e)
            return 0
    
    def modify_order(self, ticket: int, sl_price: float = None, tp_price: float = None) -> bool:
        """Modify order SL/TP"""
        try:
            if ticket not in self.active_orders:
                return False
            
            result = self.mt5_connector.modify_position(ticket, sl=sl_price, tp=tp_price)
            
            if result and result.get('retcode') == 10009:
                # Update our tracking
                order_data = self.active_orders[ticket]
                if sl_price:
                    order_data['sl_price'] = sl_price
                if tp_price:
                    order_data['tp_price'] = tp_price
                
                self.logger.info(f"Order {ticket} modified - SL: {sl_price}, TP: {tp_price}")
                return True
            
            return False
            
        except Exception as e:
            log_error("OrderManager", f"Error modifying order {ticket}: {e}", e)
            return False
    
    def _pre_trade_checks(self, symbol: str, action: str, volume: float) -> bool:
        """Comprehensive pre-trade risk checks"""
        try:
            # Check daily order limit
            if self.daily_stats['orders_placed'] >= self.max_daily_orders:
                self.logger.warning("Daily order limit reached")
                return False
            
            # Check order interval
            current_time = time.time()
            if symbol in self.last_order_time:
                time_since_last = current_time - self.last_order_time[symbol]
                if time_since_last < self.min_order_interval:
                    self.logger.warning(f"Order interval too short for {symbol}")
                    return False
            
            # Check symbol-specific order limit
            symbol_orders = sum(1 for order in self.active_orders.values() 
                              if order['symbol'] == symbol)
            if symbol_orders >= self.max_orders_per_symbol:
                self.logger.warning(f"Too many open orders for {symbol}")
                return False
            
            # Risk manager checks
            if not self.risk_manager.can_open_position(symbol, volume):
                self.logger.warning("Risk manager rejected order")
                return False
            
            # Volume checks
            if volume <= 0 or volume > 10.0:  # Reasonable volume limits
                self.logger.warning(f"Invalid volume: {volume}")
                return False
            
            # Action validation
            if action.lower() not in ['buy', 'sell']:
                self.logger.warning(f"Invalid action: {action}")
                return False
            
            return True
            
        except Exception as e:
            log_error("OrderManager", f"Error in pre-trade checks: {e}", e)
            return False
    
    def _calculate_sl_tp_prices(self, symbol: str, action: str, tick: Dict, 
                               sl_pips: float, tp_pips: float) -> Tuple[float, float]:
        """Calculate SL and TP prices based on pips"""
        try:
            # Get symbol info for pip value
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0, 0.0
            
            point = symbol_info.get('point', 0.0001)
            digits = symbol_info.get('digits', 5)
            
            # Adjust point for JPY pairs
            if 'JPY' in symbol:
                pip_value = point * 100
            else:
                pip_value = point * 10
            
            current_price = tick['ask'] if action.lower() == 'buy' else tick['bid']
            
            sl_price = 0.0
            tp_price = 0.0
            
            if sl_pips > 0:
                if action.lower() == 'buy':
                    sl_price = current_price - (sl_pips * pip_value)
                else:
                    sl_price = current_price + (sl_pips * pip_value)
                
                sl_price = round(sl_price, digits)
            
            if tp_pips > 0:
                if action.lower() == 'buy':
                    tp_price = current_price + (tp_pips * pip_value)
                else:
                    tp_price = current_price - (tp_pips * pip_value)
                
                tp_price = round(tp_price, digits)
            
            return sl_price, tp_price
            
        except Exception as e:
            log_error("OrderManager", f"Error calculating SL/TP: {e}", e)
            return 0.0, 0.0
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active orders"""
        return list(self.active_orders.values())
    
    def get_order_history(self, days: int = 1) -> List[Dict[str, Any]]:
        """Get order history for specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            return [order for order in self.order_history 
                   if order['timestamp'] >= cutoff_date]
        except Exception as e:
            log_error("OrderManager", f"Error getting order history: {e}", e)
            return []
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily trading statistics"""
        stats = self.daily_stats.copy()
        
        # Calculate win rate
        total_closed = stats['wins'] + stats['losses']
        stats['win_rate'] = (stats['wins'] / total_closed * 100) if total_closed > 0 else 0.0
        
        # Calculate average profit per trade
        stats['avg_profit'] = (stats['total_profit'] / total_closed) if total_closed > 0 else 0.0
        
        # Add active orders count
        stats['active_orders'] = len(self.active_orders)
        
        return stats
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of new day)"""
        self.daily_stats = {
            'orders_placed': 0,
            'orders_closed': 0,
            'total_profit': 0.0,
            'wins': 0,
            'losses': 0
        }
        self.logger.info("Daily statistics reset")
    
    def update_order_tracking(self):
        """Update order tracking from MT5 positions"""
        try:
            # Get current positions from MT5
            mt5_positions = self.mt5_connector.get_positions()
            mt5_tickets = {pos['ticket'] for pos in mt5_positions}
            
            # Check for orders that were closed externally
            closed_tickets = []
            for ticket in list(self.active_orders.keys()):
                if ticket not in mt5_tickets:
                    # Order was closed externally
                    closed_tickets.append(ticket)
            
            # Remove closed orders from tracking
            for ticket in closed_tickets:
                if ticket in self.active_orders:
                    order_data = self.active_orders[ticket]
                    order_data['status'] = 'CLOSED_EXTERNAL'
                    order_data['close_time'] = datetime.now()
                    del self.active_orders[ticket]
                    self.daily_stats['orders_closed'] += 1
            
            if closed_tickets:
                self.logger.info(f"Updated tracking: {len(closed_tickets)} orders closed externally")
                
        except Exception as e:
            log_error("OrderManager", f"Error updating order tracking: {e}", e)
    
    def cleanup_old_history(self, days: int = 30):
        """Clean up old order history"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            initial_count = len(self.order_history)
            
            self.order_history = [order for order in self.order_history 
                                if order['timestamp'] >= cutoff_date]
            
            cleaned_count = initial_count - len(self.order_history)
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old order records")
                
        except Exception as e:
            log_error("OrderManager", f"Error cleaning up history: {e}", e)
    
    def get_order_summary(self) -> str:
        """Get formatted order summary"""
        try:
            stats = self.get_daily_stats()
            
            summary = f"""
Order Manager Summary:
• Active Orders: {stats['active_orders']}
• Orders Placed Today: {stats['orders_placed']}
• Orders Closed Today: {stats['orders_closed']}
• Win Rate: {stats['win_rate']:.1f}%
• Total Profit: ${stats['total_profit']:.2f}
• Average Profit: ${stats['avg_profit']:.2f}
• Wins/Losses: {stats['wins']}/{stats['losses']}
"""
            return summary.strip()
            
        except Exception as e:
            log_error("OrderManager", f"Error generating summary: {e}", e)
            return "Error generating order summary"
