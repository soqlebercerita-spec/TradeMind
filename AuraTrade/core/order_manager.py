
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
    """Order management and execution system"""
    
    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager, 
                 notifier: TelegramNotifier):
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.notifier = notifier
        self.logger = Logger().get_logger()
        
        # Order tracking
        self.active_orders = {}
        self.order_history = []
        
    def place_market_order(self, trade_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Place a market order"""
        try:
            symbol = trade_request['symbol']
            direction = trade_request['direction']  # 1 for buy, -1 for sell
            volume = trade_request['volume']
            
            # Get current prices
            current_price = self.mt5_connector.get_current_price(symbol)
            if not current_price:
                self.logger.error(f"Could not get current price for {symbol}")
                return None
            
            bid, ask = current_price
            
            # Determine order type and price
            if direction > 0:  # Buy order
                order_type = mt5.ORDER_TYPE_BUY
                price = ask
            else:  # Sell order
                order_type = mt5.ORDER_TYPE_SELL
                price = bid
            
            # Calculate stop loss and take profit
            sl = trade_request.get('stop_loss', 0)
            tp = trade_request.get('take_profit', 0)
            
            # Place order
            result = self.mt5_connector.place_order(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                price=price,
                sl=sl,
                tp=tp,
                comment=f"AuraTrade-{trade_request.get('strategy', 'Manual')}"
            )
            
            if result:
                # Log successful order
                self.logger.info(f"✅ Market order placed: {symbol} {direction} {volume} lots")
                
                # Add to order tracking
                order_info = {
                    'ticket': result.get('order', 0),
                    'symbol': symbol,
                    'direction': direction,
                    'volume': volume,
                    'price': price,
                    'sl': sl,
                    'tp': tp,
                    'timestamp': datetime.now(),
                    'strategy': trade_request.get('strategy', 'Manual')
                }
                
                self.active_orders[result.get('order', 0)] = order_info
                self.order_history.append(order_info)
                
                # Send notification
                if self.notifier:
                    action = "BUY" if direction > 0 else "SELL"
                    self.notifier.notify_trade_opened(symbol, action, volume, price, tp, sl)
                
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error placing market order: {e}")
            return None
    
    def close_position(self, ticket: int, reason: str = "Manual close") -> bool:
        """Close a specific position"""
        try:
            result = self.mt5_connector.close_position(ticket)
            
            if result:
                self.logger.info(f"✅ Position {ticket} closed: {reason}")
                
                # Remove from active orders
                if ticket in self.active_orders:
                    order_info = self.active_orders.pop(ticket)
                    
                    # Send notification
                    if self.notifier:
                        # Get final position info for profit calculation
                        # This is simplified - in practice, get actual profit from MT5
                        self.notifier.send_message(f"Position closed: {order_info['symbol']} - {reason}")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error closing position {ticket}: {e}")
            return False
    
    def close_all_positions(self, reason: str = "Close all") -> int:
        """Close all open positions"""
        try:
            positions = self.mt5_connector.get_positions()
            closed_count = 0
            
            for position in positions:
                if self.close_position(position['ticket'], reason):
                    closed_count += 1
            
            self.logger.info(f"✅ Closed {closed_count} positions: {reason}")
            return closed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error closing all positions: {e}")
            return 0
    
    def emergency_stop(self) -> bool:
        """Emergency stop - close all positions immediately"""
        try:
            self.logger.warning("🚨 EMERGENCY STOP - Closing all positions")
            
            closed_count = self.close_all_positions("EMERGENCY STOP")
            
            # Send emergency notification
            if self.notifier:
                self.notifier.send_message(f"🚨 EMERGENCY STOP EXECUTED - {closed_count} positions closed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error during emergency stop: {e}")
            return False
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions"""
        try:
            return self.mt5_connector.get_positions()
        except Exception as e:
            self.logger.error(f"❌ Error getting active positions: {e}")
            return []
    
    def get_order_history(self) -> List[Dict[str, Any]]:
        """Get order history"""
        return self.order_history.copy()
