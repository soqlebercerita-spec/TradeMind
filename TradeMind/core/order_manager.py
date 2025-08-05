"""
Order management system for placing, modifying, and closing trades
Handles all trade execution with proper error handling and logging
"""

import MetaTrader5 as mt5
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import time

from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger
from utils.notifier import TelegramNotifier

class OrderManager:
    """Manages all trading orders and positions"""
    
    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager, 
                 notifier: TelegramNotifier):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.notifier = notifier
        
        # Order tracking
        self.active_orders = {}
        self.order_history = []
        self.order_lock = threading.Lock()
        
        # Magic numbers for different strategies
        self.strategy_magic_numbers = {
            'hft': 100001,
            'scalping': 100002,
            'arbitrage': 100003,
            'pattern': 100004,
            'manual': 100000
        }
        
        # Order execution settings
        self.max_slippage = 3  # Maximum slippage in pips
        self.order_timeout = 10  # Order timeout in seconds
        self.retry_attempts = 3  # Number of retry attempts
        
    def place_market_order(self, trade_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Place a market order"""
        try:
            with self.order_lock:
                symbol = trade_request['symbol']
                direction = trade_request['direction']  # 1 for buy, -1 for sell
                volume = trade_request['volume']
                strategy = trade_request.get('strategy', 'manual')
                
                # Get current price
                current_price = self.mt5_connector.get_current_price(symbol)
                if not current_price:
                    self.logger.error(f"Failed to get current price for {symbol}")
                    return None
                
                bid, ask = current_price
                
                # Determine order type and price
                if direction > 0:  # Buy order
                    order_type = mt5.ORDER_TYPE_BUY
                    entry_price = ask
                else:  # Sell order
                    order_type = mt5.ORDER_TYPE_SELL
                    entry_price = bid
                
                # Calculate stop loss and take profit if not provided
                sl = trade_request.get('stop_loss', 0)
                tp = trade_request.get('take_profit', 0)
                
                if sl == 0 or tp == 0:
                    calculated_levels = self.risk_manager.calculate_sl_tp(
                        symbol, entry_price, direction, volume
                    )
                    if calculated_levels:
                        if sl == 0:
                            sl = calculated_levels['stop_loss']
                        if tp == 0:
                            tp = calculated_levels['take_profit']
                
                # Create order comment
                comment = f"AT_{strategy}_{datetime.now().strftime('%H%M%S')}"
                
                # Get magic number for strategy
                magic = self.strategy_magic_numbers.get(strategy, self.strategy_magic_numbers['manual'])
                
                # Place the order
                result = self.mt5_connector.place_order(
                    symbol=symbol,
                    order_type=order_type,
                    volume=volume,
                    price=entry_price,
                    sl=sl,
                    tp=tp,
                    comment=comment,
                    magic=magic
                )
                
                if result:
                    # Record the order
                    order_info = {
                        'ticket': result.get('order', 0),
                        'symbol': symbol,
                        'type': 'market',
                        'direction': direction,
                        'volume': volume,
                        'entry_price': entry_price,
                        'stop_loss': sl,
                        'take_profit': tp,
                        'strategy': strategy,
                        'timestamp': datetime.now(),
                        'status': 'filled',
                        'comment': comment,
                        'magic': magic
                    }
                    
                    self.active_orders[result.get('order', 0)] = order_info
                    self.order_history.append(order_info)
                    
                    self.logger.info(f"Market order placed: {symbol} {direction} {volume} lots @ {entry_price}")
                    
                    return order_info
                else:
                    self.logger.error(f"Failed to place market order for {symbol}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Exception placing market order: {e}")
            return None
    
    def place_pending_order(self, trade_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Place a pending order (limit or stop)"""
        try:
            with self.order_lock:
                symbol = trade_request['symbol']
                direction = trade_request['direction']
                volume = trade_request['volume']
                entry_price = trade_request['entry_price']
                order_type_str = trade_request.get('order_type', 'limit')
                strategy = trade_request.get('strategy', 'manual')
                
                # Get current price for comparison
                current_price = self.mt5_connector.get_current_price(symbol)
                if not current_price:
                    return None
                
                bid, ask = current_price
                market_price = ask if direction > 0 else bid
                
                # Determine MT5 order type
                if order_type_str.lower() == 'limit':
                    if direction > 0:  # Buy limit (below market)
                        if entry_price >= market_price:
                            self.logger.error("Buy limit price must be below market price")
                            return None
                        order_type = mt5.ORDER_TYPE_BUY_LIMIT
                    else:  # Sell limit (above market)
                        if entry_price <= market_price:
                            self.logger.error("Sell limit price must be above market price")
                            return None
                        order_type = mt5.ORDER_TYPE_SELL_LIMIT
                else:  # Stop order
                    if direction > 0:  # Buy stop (above market)
                        if entry_price <= market_price:
                            self.logger.error("Buy stop price must be above market price")
                            return None
                        order_type = mt5.ORDER_TYPE_BUY_STOP
                    else:  # Sell stop (below market)
                        if entry_price >= market_price:
                            self.logger.error("Sell stop price must be below market price")
                            return None
                        order_type = mt5.ORDER_TYPE_SELL_STOP
                
                # Calculate stop loss and take profit
                sl = trade_request.get('stop_loss', 0)
                tp = trade_request.get('take_profit', 0)
                
                if sl == 0 or tp == 0:
                    calculated_levels = self.risk_manager.calculate_sl_tp(
                        symbol, entry_price, direction, volume
                    )
                    if calculated_levels:
                        if sl == 0:
                            sl = calculated_levels['stop_loss']
                        if tp == 0:
                            tp = calculated_levels['take_profit']
                
                # Create order
                comment = f"AT_{strategy}_{datetime.now().strftime('%H%M%S')}"
                magic = self.strategy_magic_numbers.get(strategy, self.strategy_magic_numbers['manual'])
                
                result = self.mt5_connector.place_order(
                    symbol=symbol,
                    order_type=order_type,
                    volume=volume,
                    price=entry_price,
                    sl=sl,
                    tp=tp,
                    comment=comment,
                    magic=magic
                )
                
                if result:
                    order_info = {
                        'ticket': result.get('order', 0),
                        'symbol': symbol,
                        'type': 'pending',
                        'order_type': order_type_str,
                        'direction': direction,
                        'volume': volume,
                        'entry_price': entry_price,
                        'stop_loss': sl,
                        'take_profit': tp,
                        'strategy': strategy,
                        'timestamp': datetime.now(),
                        'status': 'pending',
                        'comment': comment,
                        'magic': magic
                    }
                    
                    self.active_orders[result.get('order', 0)] = order_info
                    self.order_history.append(order_info)
                    
                    self.logger.info(f"Pending order placed: {symbol} {order_type_str} {direction} {volume} lots @ {entry_price}")
                    
                    return order_info
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Exception placing pending order: {e}")
            return None
    
    def modify_order(self, ticket: int, new_price: float = 0, new_sl: float = 0, 
                    new_tp: float = 0) -> bool:
        """Modify an existing order or position"""
        try:
            with self.order_lock:
                # Check if it's a pending order
                orders = self.mt5_connector.get_orders()
                order = next((o for o in orders if o['ticket'] == ticket), None)
                
                if order:
                    # Modify pending order
                    # Note: MT5 doesn't support direct order modification
                    # We need to cancel and place new order
                    self.logger.info(f"Modifying pending order {ticket} requires cancel and replace")
                    return False
                
                # Check if it's a position
                if new_sl > 0 or new_tp > 0:
                    result = self.mt5_connector.modify_position(ticket, new_sl, new_tp)
                    if result:
                        # Update our records
                        if ticket in self.active_orders:
                            if new_sl > 0:
                                self.active_orders[ticket]['stop_loss'] = new_sl
                            if new_tp > 0:
                                self.active_orders[ticket]['take_profit'] = new_tp
                        
                        self.logger.info(f"Position {ticket} modified: SL={new_sl}, TP={new_tp}")
                        return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Exception modifying order {ticket}: {e}")
            return False
    
    def close_position(self, ticket: int, reason: str = "Manual close") -> bool:
        """Close a specific position"""
        try:
            with self.order_lock:
                result = self.mt5_connector.close_position(ticket)
                
                if result:
                    # Update our records
                    if ticket in self.active_orders:
                        self.active_orders[ticket]['status'] = 'closed'
                        self.active_orders[ticket]['close_reason'] = reason
                        self.active_orders[ticket]['close_time'] = datetime.now()
                        
                        # Move to history and remove from active
                        del self.active_orders[ticket]
                    
                    self.logger.info(f"Position {ticket} closed: {reason}")
                    
                    # Send notification
                    if self.notifier:
                        self.notifier.send_message(f"Position {ticket} closed: {reason}")
                    
                    return True
                else:
                    self.logger.error(f"Failed to close position {ticket}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Exception closing position {ticket}: {e}")
            return False
    
    def cancel_order(self, ticket: int) -> bool:
        """Cancel a pending order"""
        try:
            with self.order_lock:
                # Get order details
                orders = self.mt5_connector.get_orders()
                order = next((o for o in orders if o['ticket'] == ticket), None)
                
                if not order:
                    self.logger.error(f"Order {ticket} not found")
                    return False
                
                # Create cancel request
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": ticket,
                }
                
                # Send cancel request
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    # Update our records
                    if ticket in self.active_orders:
                        self.active_orders[ticket]['status'] = 'cancelled'
                        self.active_orders[ticket]['cancel_time'] = datetime.now()
                        del self.active_orders[ticket]
                    
                    self.logger.info(f"Order {ticket} cancelled successfully")
                    return True
                else:
                    error_msg = f"Failed to cancel order {ticket}: {result.retcode if result else 'Unknown error'}"
                    self.logger.error(error_msg)
                    return False
                    
        except Exception as e:
            self.logger.error(f"Exception cancelling order {ticket}: {e}")
            return False
    
    def close_all_positions(self, symbol: str = None, strategy: str = None) -> int:
        """Close multiple positions based on criteria"""
        closed_count = 0
        
        try:
            positions = self.mt5_connector.get_positions()
            
            for position in positions:
                should_close = True
                
                # Filter by symbol if specified
                if symbol and position['symbol'] != symbol:
                    should_close = False
                
                # Filter by strategy if specified
                if strategy and strategy not in position.get('comment', ''):
                    should_close = False
                
                if should_close:
                    if self.close_position(position['ticket'], f"Bulk close ({symbol or 'all'})"):
                        closed_count += 1
                        time.sleep(0.1)  # Brief delay between closes
            
            self.logger.info(f"Closed {closed_count} positions")
            
        except Exception as e:
            self.logger.error(f"Exception closing positions: {e}")
        
        return closed_count
    
    def emergency_stop(self) -> bool:
        """Emergency stop - close all positions immediately"""
        try:
            self.logger.warning("EMERGENCY STOP: Closing all positions")
            
            # Get all positions
            positions = self.mt5_connector.get_positions()
            
            closed_count = 0
            for position in positions:
                if self.close_position(position['ticket'], "EMERGENCY STOP"):
                    closed_count += 1
            
            # Cancel all pending orders
            orders = self.mt5_connector.get_orders()
            cancelled_count = 0
            for order in orders:
                if self.cancel_order(order['ticket']):
                    cancelled_count += 1
            
            self.logger.warning(f"Emergency stop completed: {closed_count} positions closed, {cancelled_count} orders cancelled")
            
            # Send emergency notification
            if self.notifier:
                self.notifier.send_message(
                    f"🚨 EMERGENCY STOP EXECUTED\n"
                    f"Positions closed: {closed_count}\n"
                    f"Orders cancelled: {cancelled_count}"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Exception during emergency stop: {e}")
            return False
    
    def get_position_info(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a position"""
        try:
            positions = self.mt5_connector.get_positions()
            position = next((p for p in positions if p['ticket'] == ticket), None)
            
            if position:
                # Enhance with our tracking data
                if ticket in self.active_orders:
                    order_info = self.active_orders[ticket]
                    position.update({
                        'strategy': order_info.get('strategy', 'unknown'),
                        'entry_reason': order_info.get('comment', ''),
                        'open_timestamp': order_info.get('timestamp')
                    })
                
                return position
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Exception getting position info for {ticket}: {e}")
            return None
    
    def get_order_statistics(self) -> Dict[str, Any]:
        """Get order execution statistics"""
        try:
            stats = {
                'total_orders': len(self.order_history),
                'active_orders': len(self.active_orders),
                'orders_by_strategy': {},
                'orders_by_symbol': {},
                'success_rate': 0,
                'average_fill_time': 0
            }
            
            # Analyze order history
            successful_orders = 0
            fill_times = []
            
            for order in self.order_history:
                strategy = order.get('strategy', 'unknown')
                symbol = order.get('symbol', 'unknown')
                
                # Count by strategy
                stats['orders_by_strategy'][strategy] = stats['orders_by_strategy'].get(strategy, 0) + 1
                
                # Count by symbol
                stats['orders_by_symbol'][symbol] = stats['orders_by_symbol'].get(symbol, 0) + 1
                
                # Success rate calculation
                if order.get('status') == 'filled':
                    successful_orders += 1
                
                # Fill time calculation (placeholder)
                if 'fill_time' in order:
                    fill_times.append(order['fill_time'])
            
            if stats['total_orders'] > 0:
                stats['success_rate'] = (successful_orders / stats['total_orders']) * 100
            
            if fill_times:
                stats['average_fill_time'] = sum(fill_times) / len(fill_times)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Exception calculating order statistics: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 7):
        """Clean up old order records"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Remove old records from history
            self.order_history = [
                order for order in self.order_history 
                if order.get('timestamp', datetime.now()) > cutoff_date
            ]
            
            self.logger.info(f"Cleaned up order records older than {days} days")
            
        except Exception as e:
            self.logger.error(f"Exception cleaning up old records: {e}")
    
    def validate_order_request(self, trade_request: Dict[str, Any]) -> bool:
        """Validate order request parameters"""
        try:
            required_fields = ['symbol', 'direction', 'volume']
            
            for field in required_fields:
                if field not in trade_request:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate direction
            if trade_request['direction'] not in [-1, 1]:
                self.logger.error("Direction must be -1 (sell) or 1 (buy)")
                return False
            
            # Validate volume
            volume = trade_request['volume']
            if volume <= 0:
                self.logger.error("Volume must be positive")
                return False
            
            # Get symbol info for validation
            symbol_info = self.mt5_connector.get_symbol_info(trade_request['symbol'])
            if not symbol_info:
                self.logger.error(f"Invalid symbol: {trade_request['symbol']}")
                return False
            
            # Check minimum and maximum volume
            min_volume = symbol_info.get('volume_min', 0.01)
            max_volume = symbol_info.get('volume_max', 100)
            
            if volume < min_volume or volume > max_volume:
                self.logger.error(f"Volume {volume} outside allowed range [{min_volume}, {max_volume}]")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Exception validating order request: {e}")
            return False
