
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
    
    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager, 
                 notifier: Optional[TelegramNotifier] = None):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.notifier = notifier
        
        # Order tracking
        self.active_orders = {}
        self.order_history = []
        
        # Performance metrics
        self.metrics = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'average_execution_time': 0.0
        }
        
        self.logger.info("Order Manager initialized")
    
    def place_market_order(self, symbol: str, action: str, volume: float,
                          sl_pips: float = 0, tp_pips: float = 0,
                          comment: str = "AuraTrade") -> Optional[Dict[str, Any]]:
        """Place market order with risk management"""
        start_time = time.time()
        
        try:
            # Pre-trade risk checks
            if not self._pre_trade_checks(symbol, action, volume):
                return None
            
            # Get current prices
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                log_error("OrderManager", f"Failed to get tick data for {symbol}")
                return None
            
            # Calculate prices
            if action.lower() == 'buy':
                entry_price = tick['ask']
            else:
                entry_price = tick['bid']
            
            # Calculate SL/TP based on percentage of balance (as requested)
            sl_price, tp_price = self._calculate_sl_tp_by_balance(
                symbol, action, entry_price, sl_pips, tp_pips
            )
            
            # Send order to MT5
            result = self.mt5_connector.send_order(
                action=action.lower(),
                symbol=symbol,
                volume=volume,
                price=entry_price,
                sl=sl_price,
                tp=tp_price,
                comment=comment
            )
            
            # Process result
            execution_time = time.time() - start_time
            self._update_metrics(result, execution_time)
            
            if result and result.get('retcode') == 10009:
                # Successful order
                order_info = {
                    'ticket': result.get('deal'),
                    'symbol': symbol,
                    'action': action,
                    'volume': volume,
                    'entry_price': entry_price,
                    'sl_price': sl_price,
                    'tp_price': tp_price,
                    'timestamp': datetime.now(),
                    'comment': comment,
                    'execution_time': execution_time
                }
                
                self.active_orders[result.get('deal')] = order_info
                self.order_history.append(order_info)
                
                # Log successful trade
                log_trade(action, symbol, volume, entry_price)
                
                # Send notification
                if self.notifier and self.notifier.enabled:
                    self.notifier.send_trade_signal(
                        action.upper(),
                        symbol,
                        volume,
                        entry_price,
                        f"Order executed in {execution_time:.3f}s"
                    )
                
                self.logger.info(f"Market order executed: {action.upper()} {volume} {symbol} @ {entry_price:.5f}")
                return result
            else:
                # Failed order
                error_msg = result.get('comment', 'Unknown error') if result else 'No response'
                log_error("OrderManager", f"Order failed for {symbol}: {error_msg}")
                return None
                
        except Exception as e:
            log_error("OrderManager", f"Error placing market order for {symbol}", e)
            return None
    
    def place_pending_order(self, symbol: str, action: str, volume: float,
                           price: float, sl_pips: float = 0, tp_pips: float = 0,
                           comment: str = "AuraTrade") -> Optional[Dict[str, Any]]:
        """Place pending order (buy/sell stop/limit)"""
        try:
            # Pre-trade checks
            if not self._pre_trade_checks(symbol, action, volume):
                return None
            
            # Calculate SL/TP
            sl_price, tp_price = self._calculate_sl_tp_by_balance(
                symbol, action, price, sl_pips, tp_pips
            )
            
            # For mock connector, we'll treat this as immediate execution
            result = self.mt5_connector.send_order(
                action=action.lower(),
                symbol=symbol,
                volume=volume,
                price=price,
                sl=sl_price,
                tp=tp_price,
                comment=comment
            )
            
            if result and result.get('retcode') == 10009:
                self.logger.info(f"Pending order placed: {action.upper()} {volume} {symbol} @ {price:.5f}")
                return result
            
            return None
            
        except Exception as e:
            log_error("OrderManager", f"Error placing pending order for {symbol}", e)
            return None
    
    def modify_order(self, ticket: int, sl: float = None, tp: float = None) -> bool:
        """Modify existing order SL/TP"""
        try:
            result = self.mt5_connector.modify_position(ticket, sl=sl, tp=tp)
            
            if result and result.get('retcode') == 10009:
                self.logger.info(f"Order #{ticket} modified - SL: {sl}, TP: {tp}")
                
                # Update active order info
                if ticket in self.active_orders:
                    if sl:
                        self.active_orders[ticket]['sl_price'] = sl
                    if tp:
                        self.active_orders[ticket]['tp_price'] = tp
                
                return True
            
            return False
            
        except Exception as e:
            log_error("OrderManager", f"Error modifying order #{ticket}", e)
            return False
    
    def close_order(self, ticket: int) -> bool:
        """Close order by ticket"""
        try:
            result = self.mt5_connector.close_position(ticket)
            
            if result and result.get('retcode') == 10009:
                profit = result.get('profit', 0.0)
                self.logger.info(f"Order #{ticket} closed - Profit: ${profit:.2f}")
                
                # Remove from active orders
                if ticket in self.active_orders:
                    order_info = self.active_orders[ticket]
                    order_info['close_time'] = datetime.now()
                    order_info['profit'] = profit
                    del self.active_orders[ticket]
                
                # Send notification
                if self.notifier and self.notifier.enabled:
                    self.notifier.send_trade_signal(
                        "CLOSE",
                        "POSITION",
                        0.0,
                        profit,
                        f"Position #{ticket} closed"
                    )
                
                return True
            
            return False
            
        except Exception as e:
            log_error("OrderManager", f"Error closing order #{ticket}", e)
            return False
    
    def close_all_orders(self, symbol: str = None) -> int:
        """Close all orders (optionally for specific symbol)"""
        try:
            positions = self.mt5_connector.get_positions()
            closed_count = 0
            
            for position in positions:
                if symbol and position['symbol'] != symbol:
                    continue
                
                if self.close_order(position['ticket']):
                    closed_count += 1
            
            self.logger.info(f"Closed {closed_count} positions" + (f" for {symbol}" if symbol else ""))
            return closed_count
            
        except Exception as e:
            log_error("OrderManager", "Error closing all orders", e)
            return 0
    
    def _pre_trade_checks(self, symbol: str, action: str, volume: float) -> bool:
        """Perform pre-trade risk checks"""
        try:
            # Check connection
            if not self.mt5_connector.check_connection():
                log_error("OrderManager", "MT5 not connected")
                return False
            
            # Check symbol validity
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                log_error("OrderManager", f"Invalid symbol: {symbol}")
                return False
            
            # Risk manager checks
            if not self.risk_manager.can_open_position(symbol, volume):
                log_error("OrderManager", f"Risk manager rejected trade for {symbol}")
                return False
            
            # Check account margin
            account_info = self.mt5_connector.get_account_info()
            margin_level = account_info.get('margin_level', 0)
            
            if margin_level > 0 and margin_level < 200:
                log_error("OrderManager", f"Insufficient margin: {margin_level:.1f}%")
                return False
            
            # Volume checks
            if volume <= 0 or volume > 10.0:  # Max 10 lots
                log_error("OrderManager", f"Invalid volume: {volume}")
                return False
            
            return True
            
        except Exception as e:
            log_error("OrderManager", "Error in pre-trade checks", e)
            return False
    
    def _calculate_sl_tp_by_balance(self, symbol: str, action: str, entry_price: float,
                                   sl_pips: float, tp_pips: float) -> Tuple[float, float]:
        """Calculate SL/TP based on percentage of balance (as requested)"""
        try:
            account_info = self.mt5_connector.get_account_info()
            balance = account_info.get('balance', 10000)
            
            # Risk 1% of balance for SL, target 2% for TP
            risk_amount = balance * 0.01  # 1% risk
            profit_target = balance * 0.02  # 2% target
            
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0, 0.0
            
            point = symbol_info.get('point', 0.00001)
            contract_size = symbol_info.get('contract_size', 100000)
            
            # Calculate pip values
            if 'JPY' in symbol:
                pip_value = (contract_size * 0.01) / entry_price
            else:
                pip_value = (contract_size * point * 10) / entry_price
            
            # Calculate SL/TP distances in pips
            if pip_value > 0:
                sl_distance = risk_amount / pip_value
                tp_distance = profit_target / pip_value
            else:
                sl_distance = sl_pips if sl_pips > 0 else 20
                tp_distance = tp_pips if tp_pips > 0 else 40
            
            # Apply distances to price
            if action.lower() == 'buy':
                sl_price = entry_price - (sl_distance * point * 10) if sl_distance > 0 else 0
                tp_price = entry_price + (tp_distance * point * 10) if tp_distance > 0 else 0
            else:  # sell
                sl_price = entry_price + (sl_distance * point * 10) if sl_distance > 0 else 0
                tp_price = entry_price - (tp_distance * point * 10) if tp_distance > 0 else 0
            
            return sl_price, tp_price
            
        except Exception as e:
            log_error("OrderManager", "Error calculating SL/TP by balance", e)
            # Fallback to pip-based calculation
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            point = symbol_info.get('point', 0.00001) if symbol_info else 0.00001
            
            if action.lower() == 'buy':
                sl_price = entry_price - (sl_pips * point * 10) if sl_pips > 0 else 0
                tp_price = entry_price + (tp_pips * point * 10) if tp_pips > 0 else 0
            else:
                sl_price = entry_price + (sl_pips * point * 10) if sl_pips > 0 else 0
                tp_price = entry_price - (tp_pips * point * 10) if tp_pips > 0 else 0
            
            return sl_price, tp_price
    
    def _update_metrics(self, result: Optional[Dict], execution_time: float):
        """Update order execution metrics"""
        self.metrics['total_orders'] += 1
        
        if result and result.get('retcode') == 10009:
            self.metrics['successful_orders'] += 1
        else:
            self.metrics['failed_orders'] += 1
        
        # Update average execution time
        total_time = self.metrics['average_execution_time'] * (self.metrics['total_orders'] - 1)
        self.metrics['average_execution_time'] = (total_time + execution_time) / self.metrics['total_orders']
    
    def get_active_orders(self) -> Dict[int, Dict[str, Any]]:
        """Get all active orders"""
        return self.active_orders.copy()
    
    def get_order_history(self) -> List[Dict[str, Any]]:
        """Get order history"""
        return self.order_history.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get order management metrics"""
        success_rate = 0.0
        if self.metrics['total_orders'] > 0:
            success_rate = (self.metrics['successful_orders'] / self.metrics['total_orders']) * 100
        
        return {
            **self.metrics,
            'success_rate': success_rate,
            'active_orders_count': len(self.active_orders)
        }
    
    def emergency_close_all(self) -> int:
        """Emergency close all positions"""
        self.logger.warning("EMERGENCY: Closing all positions")
        return self.close_all_orders()
