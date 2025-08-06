
"""
Order Manager for AuraTrade Bot
Complete order execution and management system
"""

import MetaTrader5 as mt5
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from core.mt5_connector import MT5Connector
from utils.logger import Logger, log_trade

class OrderType(Enum):
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP

class OrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class OrderRequest:
    symbol: str
    order_type: OrderType
    volume: float
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    magic: int = 0
    comment: str = "AuraTrade"
    deviation: int = 20
    expiration: Optional[datetime] = None

@dataclass
class OrderResult:
    success: bool
    order_id: Optional[int] = None
    deal_id: Optional[int] = None
    message: str = ""
    retcode: int = 0
    executed_volume: float = 0.0
    executed_price: float = 0.0

class OrderManager:
    """Advanced order management system"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.mt5 = mt5_connector
        self.logger = Logger().get_logger()
        
        # Order tracking
        self.pending_orders: Dict[int, OrderRequest] = {}
        self.executed_orders: Dict[int, Dict] = {}
        self.failed_orders: Dict[int, Dict] = {}
        
        # Risk manager and notifier (will be set later)
        self.risk_manager = None
        self.notifier = None
        
        # Order execution settings
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.max_slippage = 3
        self.default_magic = 12345
        
        # Threading
        self.order_lock = threading.Lock()
        self.monitoring_thread = None
        self.monitoring_active = False
        
        self.logger.info("OrderManager initialized")
    
    def set_components(self, risk_manager=None, notifier=None):
        """Set additional components"""
        self.risk_manager = risk_manager
        self.notifier = notifier
    
    def start_monitoring(self):
        """Start order monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_orders, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Order monitoring started")
    
    def stop_monitoring(self):
        """Stop order monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Order monitoring stopped")
    
    def _monitor_orders(self):
        """Monitor pending orders"""
        while self.monitoring_active:
            try:
                with self.order_lock:
                    # Check pending orders status
                    orders_to_remove = []
                    for order_id in self.pending_orders.keys():
                        status = self._check_order_status(order_id)
                        if status != OrderStatus.PENDING:
                            orders_to_remove.append(order_id)
                    
                    # Remove completed orders from pending
                    for order_id in orders_to_remove:
                        if order_id in self.pending_orders:
                            del self.pending_orders[order_id]
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in order monitoring: {e}")
                time.sleep(5)
    
    def _check_order_status(self, order_id: int) -> OrderStatus:
        """Check individual order status"""
        try:
            # Check if order still exists in pending orders
            orders = self.mt5.get_orders()
            for order in orders:
                if order['ticket'] == order_id:
                    return OrderStatus.PENDING
            
            # Check if it was executed (became a position)
            positions = self.mt5.get_positions()
            for pos in positions:
                if pos['identifier'] == order_id:
                    self.executed_orders[order_id] = pos
                    return OrderStatus.EXECUTED
            
            # If not found anywhere, it might have been cancelled or failed
            return OrderStatus.CANCELLED
            
        except Exception as e:
            self.logger.error(f"Error checking order status: {e}")
            return OrderStatus.FAILED
    
    def place_market_order(self, symbol: str, order_type: OrderType, volume: float,
                          sl: float = None, tp: float = None, comment: str = "AuraTrade") -> OrderResult:
        """Place market order"""
        try:
            # Validate inputs
            if not self._validate_order_inputs(symbol, order_type, volume):
                return OrderResult(False, message="Invalid order parameters")
            
            # Check risk limits
            if self.risk_manager and not self.risk_manager.check_trade_risk(symbol, volume):
                return OrderResult(False, message="Risk limits exceeded")
            
            # Get current prices
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return OrderResult(False, message=f"Cannot get symbol info for {symbol}")
            
            # Determine price based on order type
            if order_type in [OrderType.BUY, OrderType.BUY_STOP, OrderType.BUY_LIMIT]:
                price = symbol_info['ask']
            else:
                price = symbol_info['bid']
            
            # Prepare order request
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': volume,
                'type': order_type.value,
                'price': price,
                'deviation': self.max_slippage,
                'magic': self.default_magic,
                'comment': comment,
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC
            }
            
            # Add SL/TP if provided
            if sl:
                request['sl'] = sl
            if tp:
                request['tp'] = tp
            
            # Execute order with retries
            result = self._execute_order_with_retries(request)
            
            # Log trade
            if result.success:
                log_trade(symbol, order_type.name, volume, result.executed_price, sl, tp, "OPENED")
                
                # Send notification
                if self.notifier:
                    self.notifier.send_trade_notification(
                        action="OPENED",
                        symbol=symbol,
                        order_type=order_type.name,
                        volume=volume,
                        price=result.executed_price,
                        sl=sl,
                        tp=tp
                    )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            return OrderResult(False, message=str(e))
    
    def place_pending_order(self, symbol: str, order_type: OrderType, volume: float,
                           price: float, sl: float = None, tp: float = None, 
                           expiration: datetime = None, comment: str = "AuraTrade") -> OrderResult:
        """Place pending order"""
        try:
            # Validate inputs
            if not self._validate_order_inputs(symbol, order_type, volume):
                return OrderResult(False, message="Invalid order parameters")
            
            if order_type in [OrderType.BUY, OrderType.SELL]:
                return OrderResult(False, message="Use place_market_order for market orders")
            
            # Check risk limits
            if self.risk_manager and not self.risk_manager.check_trade_risk(symbol, volume):
                return OrderResult(False, message="Risk limits exceeded")
            
            # Prepare order request
            request = {
                'action': mt5.TRADE_ACTION_PENDING,
                'symbol': symbol,
                'volume': volume,
                'type': order_type.value,
                'price': price,
                'magic': self.default_magic,
                'comment': comment,
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_RETURN
            }
            
            # Add SL/TP if provided
            if sl:
                request['sl'] = sl
            if tp:
                request['tp'] = tp
            
            # Add expiration if provided
            if expiration:
                request['type_time'] = mt5.ORDER_TIME_SPECIFIED
                request['expiration'] = int(expiration.timestamp())
            
            # Execute order
            result = self._execute_order_with_retries(request)
            
            # Track pending order
            if result.success and result.order_id:
                order_request = OrderRequest(symbol, order_type, volume, price, sl, tp, 
                                           self.default_magic, comment, self.max_slippage, expiration)
                with self.order_lock:
                    self.pending_orders[result.order_id] = order_request
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing pending order: {e}")
            return OrderResult(False, message=str(e))
    
    def _execute_order_with_retries(self, request: Dict[str, Any]) -> OrderResult:
        """Execute order with retry mechanism"""
        last_error = ""
        
        for attempt in range(self.max_retries):
            try:
                result = self.mt5.send_order(request)
                
                if result and result.get('retcode') == mt5.TRADE_RETCODE_DONE:
                    return OrderResult(
                        success=True,
                        order_id=result.get('order'),
                        deal_id=result.get('deal'),
                        executed_volume=result.get('volume', 0),
                        executed_price=result.get('price', 0),
                        message="Order executed successfully"
                    )
                else:
                    error_code = result.get('retcode', 0) if result else 0
                    last_error = f"Order failed with code {error_code}"
                    
                    # Wait before retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        return OrderResult(False, message=f"Order failed after {self.max_retries} attempts: {last_error}")
    
    def close_position(self, ticket: int, volume: float = None, comment: str = "Closed by AuraTrade") -> OrderResult:
        """Close position"""
        try:
            result_dict = self.mt5.close_position(ticket)
            
            if result_dict and result_dict.get('retcode') == mt5.TRADE_RETCODE_DONE:
                # Log trade closure
                positions = self.mt5.get_positions()
                for pos in positions:
                    if pos['ticket'] == ticket:
                        log_trade(
                            pos['symbol'], 
                            "CLOSE", 
                            pos['volume'], 
                            result_dict.get('price', 0),
                            pos.get('sl', 0),
                            pos.get('tp', 0),
                            "CLOSED"
                        )
                        break
                
                return OrderResult(
                    success=True,
                    deal_id=result_dict.get('deal'),
                    executed_price=result_dict.get('price', 0),
                    message="Position closed successfully"
                )
            else:
                error_code = result_dict.get('retcode', 0) if result_dict else 0
                return OrderResult(False, message=f"Failed to close position: {error_code}")
                
        except Exception as e:
            self.logger.error(f"Error closing position {ticket}: {e}")
            return OrderResult(False, message=str(e))
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> OrderResult:
        """Modify position SL/TP"""
        try:
            result_dict = self.mt5.modify_position(ticket, sl, tp)
            
            if result_dict and result_dict.get('retcode') == mt5.TRADE_RETCODE_DONE:
                return OrderResult(
                    success=True,
                    message="Position modified successfully"
                )
            else:
                error_code = result_dict.get('retcode', 0) if result_dict else 0
                return OrderResult(False, message=f"Failed to modify position: {error_code}")
                
        except Exception as e:
            self.logger.error(f"Error modifying position {ticket}: {e}")
            return OrderResult(False, message=str(e))
    
    def cancel_order(self, order_id: int) -> OrderResult:
        """Cancel pending order"""
        try:
            request = {
                'action': mt5.TRADE_ACTION_REMOVE,
                'order': order_id
            }
            
            result = self.mt5.send_order(request)
            
            if result and result.get('retcode') == mt5.TRADE_RETCODE_DONE:
                # Remove from pending orders
                with self.order_lock:
                    if order_id in self.pending_orders:
                        del self.pending_orders[order_id]
                
                return OrderResult(
                    success=True,
                    message="Order cancelled successfully"
                )
            else:
                error_code = result.get('retcode', 0) if result else 0
                return OrderResult(False, message=f"Failed to cancel order: {error_code}")
                
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return OrderResult(False, message=str(e))
    
    def _validate_order_inputs(self, symbol: str, order_type: OrderType, volume: float) -> bool:
        """Validate order inputs"""
        try:
            # Check symbol
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            
            # Check volume
            if volume < symbol_info['volume_min'] or volume > symbol_info['volume_max']:
                self.logger.error(f"Invalid volume {volume} for {symbol}")
                return False
            
            # Check volume step
            volume_step = symbol_info['volume_step']
            if volume_step > 0 and (volume % volume_step) != 0:
                self.logger.error(f"Volume {volume} not aligned with step {volume_step}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating order inputs: {e}")
            return False
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get position summary"""
        try:
            positions = self.mt5.get_positions()
            
            summary = {
                'total_positions': len(positions),
                'buy_positions': 0,
                'sell_positions': 0,
                'total_profit': 0.0,
                'total_volume': 0.0,
                'symbols': set()
            }
            
            for pos in positions:
                if pos['type'] == 0:  # Buy
                    summary['buy_positions'] += 1
                else:  # Sell
                    summary['sell_positions'] += 1
                
                summary['total_profit'] += pos['profit']
                summary['total_volume'] += pos['volume']
                summary['symbols'].add(pos['symbol'])
            
            summary['symbols'] = list(summary['symbols'])
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting position summary: {e}")
            return {}
    
    def get_order_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get order history"""
        try:
            from_date = datetime.now() - timedelta(days=days)
            to_date = datetime.now()
            
            deals = mt5.history_deals_get(from_date, to_date)
            if deals is None:
                return []
            
            history = []
            for deal in deals:
                history.append({
                    'ticket': deal.ticket,
                    'order': deal.order,
                    'time': datetime.fromtimestamp(deal.time),
                    'type': deal.type,
                    'entry': deal.entry,
                    'magic': deal.magic,
                    'position_id': deal.position_id,
                    'volume': deal.volume,
                    'price': deal.price,
                    'commission': deal.commission,
                    'swap': deal.swap,
                    'profit': deal.profit,
                    'symbol': deal.symbol,
                    'comment': deal.comment
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting order history: {e}")
            return []
    
    def emergency_close_all(self) -> Dict[str, Any]:
        """Emergency close all positions"""
        try:
            self.logger.warning("Emergency close all positions initiated")
            
            positions = self.mt5.get_positions()
            results = {
                'total_positions': len(positions),
                'closed_positions': 0,
                'failed_positions': 0,
                'errors': []
            }
            
            for pos in positions:
                try:
                    result = self.close_position(pos['ticket'], comment="Emergency close")
                    if result.success:
                        results['closed_positions'] += 1
                    else:
                        results['failed_positions'] += 1
                        results['errors'].append(f"Failed to close {pos['ticket']}: {result.message}")
                except Exception as e:
                    results['failed_positions'] += 1
                    results['errors'].append(f"Error closing {pos['ticket']}: {str(e)}")
            
            # Cancel all pending orders
            orders = self.mt5.get_orders()
            for order in orders:
                try:
                    self.cancel_order(order['ticket'])
                except Exception as e:
                    results['errors'].append(f"Error cancelling order {order['ticket']}: {str(e)}")
            
            # Send notification
            if self.notifier:
                self.notifier.send_system_status(
                    "emergency",
                    f"🚨 Emergency Close All Executed\n"
                    f"Closed: {results['closed_positions']}/{results['total_positions']}\n"
                    f"Failed: {results['failed_positions']}"
                )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in emergency close all: {e}")
            return {'error': str(e)}
