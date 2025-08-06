"""
Order management system for AuraTrade Bot
Handles order placement, modification, and risk management
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from core.mt5_connector import MT5Connector
from utils.logger import Logger, log_trade, log_error

class OrderManager:
    """Advanced order management with risk controls"""

    def __init__(self, mt5_connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.risk_manager = None
        self.notifier = None

        # Order tracking
        self.active_orders = {}
        self.order_history = []
        self.daily_trades = 0
        self.max_daily_trades = 100

        # Risk limits
        self.max_slippage = 3  # pips
        self.max_spread = 5    # pips

        self.logger.info("Order Manager initialized")
    
    def set_components(self, risk_manager=None, notifier=None):
        """Set optional components"""
        if risk_manager:
            self.risk_manager = risk_manager
        if notifier:
            self.notifier = notifier

    def place_market_order(self, symbol: str, action: str, volume: float, 
                          sl_pips: float = None, tp_pips: float = None, 
                          comment: str = "AuraTrade") -> Dict[str, Any]:
        """Place market order with risk management"""
        try:
            # Validate parameters
            if not self._validate_order_params(symbol, action, volume):
                return {'retcode': -1, 'comment': 'Invalid parameters'}

            # Check daily limits
            if self.daily_trades >= self.max_daily_trades:
                self.logger.warning("Daily trade limit reached")
                return {'retcode': -2, 'comment': 'Daily limit reached'}

            # Get current prices
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return {'retcode': -3, 'comment': 'No price data'}

            # Check spread
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            point = symbol_info.get('point', 0.00001)
            spread = (tick['ask'] - tick['bid']) / point

            if spread > self.max_spread:
                self.logger.warning(f"Spread too wide for {symbol}: {spread:.1f} pips")
                return {'retcode': -4, 'comment': 'Spread too wide'}

            # Determine order type and price
            if action.lower() == 'buy':
                order_type = 0  # MT5 BUY
                price = tick['ask']
            else:
                order_type = 1  # MT5 SELL
                price = tick['bid']

            # Calculate SL/TP prices
            sl_price = None
            tp_price = None

            if sl_pips:
                if action.lower() == 'buy':
                    sl_price = price - (sl_pips * point)
                else:
                    sl_price = price + (sl_pips * point)

            if tp_pips:
                if action.lower() == 'buy':
                    tp_price = price + (tp_pips * point)
                else:
                    tp_price = price - (tp_pips * point)

            # Place order via MT5
            request = {
                'action': 1,  # TRADE_ACTION_DEAL
                'symbol': symbol,
                'volume': volume,
                'type': order_type,
                'price': price,
                'sl': sl_price,
                'tp': tp_price,
                'comment': comment,
                'type_time': 0,  # ORDER_TIME_GTC
                'type_filling': 0,  # ORDER_FILLING_FOK
            }

            result = self.mt5_connector.send_order(request)

            if result and result.get('retcode') == 10009:
                # Order successful
                self.daily_trades += 1
                order_info = {
                    'ticket': result.get('order'),
                    'symbol': symbol,
                    'action': action,
                    'volume': volume,
                    'price': price,
                    'sl': sl_price,
                    'tp': tp_price,
                    'timestamp': datetime.now(),
                    'comment': comment
                }

                self.active_orders[result.get('order')] = order_info
                self.order_history.append(order_info)

                # Log successful trade
                log_trade(action, symbol, volume, price)
                self.logger.info(f"Order placed: {action.upper()} {volume} {symbol} at {price:.5f}")

                # Send notification
                if self.notifier and self.notifier.enabled:
                    self.notifier.send_trade_signal(
                        action.upper(), symbol, volume, price,
                        f"SL: {sl_price:.5f} | TP: {tp_price:.5f}" if sl_price else "No SL/TP"
                    )

            return result

        except Exception as e:
            log_error(f"Error placing order: {e}")
            return {'retcode': -999, 'comment': str(e)}

    def place_pending_order(self, symbol: str, order_type: int, volume: float, 
                           price: float, sl: float = None, tp: float = None,
                           comment: str = "AuraTrade_Pending") -> Dict[str, Any]:
        """Place pending order"""
        try:
            request = {
                'action': 0,  # TRADE_ACTION_PENDING
                'symbol': symbol,
                'volume': volume,
                'type': order_type,
                'price': price,
                'sl': sl,
                'tp': tp,
                'comment': comment,
                'type_time': 0,  # ORDER_TIME_GTC
            }

            result = self.mt5_connector.send_order(request)

            if result and result.get('retcode') == 10009:
                self.logger.info(f"Pending order placed: {symbol} at {price:.5f}")

            return result

        except Exception as e:
            log_error(f"Error placing pending order: {e}")
            return {'retcode': -999, 'comment': str(e)}

    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Modify existing position"""
        try:
            # Get position info
            positions = self.mt5_connector.get_positions()
            position = next((p for p in positions if p['ticket'] == ticket), None)

            if not position:
                return {'retcode': -5, 'comment': 'Position not found'}

            request = {
                'action': 2,  # TRADE_ACTION_SLTP
                'symbol': position['symbol'],
                'position': ticket,
                'sl': sl or position.get('sl', 0),
                'tp': tp or position.get('tp', 0),
            }

            result = self.mt5_connector.send_order(request)

            if result and result.get('retcode') == 10009:
                self.logger.info(f"Position modified: #{ticket}")

            return result

        except Exception as e:
            log_error(f"Error modifying position: {e}")
            return {'retcode': -999, 'comment': str(e)}

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close position"""
        try:
            result = self.mt5_connector.close_position(ticket)

            if result and result.get('retcode') == 10009:
                # Remove from active orders
                if ticket in self.active_orders:
                    del self.active_orders[ticket]
                self.logger.info(f"Position closed: #{ticket}")

            return result

        except Exception as e:
            log_error(f"Error closing position: {e}")
            return {'retcode': -999, 'comment': str(e)}

    def close_all_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Close all positions for symbol or all symbols"""
        try:
            positions = self.mt5_connector.get_positions()
            results = []

            for position in positions:
                if symbol is None or position['symbol'] == symbol:
                    result = self.close_position(position['ticket'])
                    results.append(result)

            self.logger.info(f"Closed {len(results)} positions")
            return results

        except Exception as e:
            log_error(f"Error closing all positions: {e}")
            return []

    def cancel_order(self, ticket: int) -> Dict[str, Any]:
        """Cancel pending order"""
        try:
            request = {
                'action': 3,  # TRADE_ACTION_REMOVE
                'order': ticket,
            }

            result = self.mt5_connector.send_order(request)

            if result and result.get('retcode') == 10009:
                self.logger.info(f"Order cancelled: #{ticket}")

            return result

        except Exception as e:
            log_error(f"Error cancelling order: {e}")
            return {'retcode': -999, 'comment': str(e)}

    def send_market_order(self, action: str, symbol: str, volume: float, 
                         tp: float = None, sl: float = None, comment: str = "AuraTrade") -> Dict[str, Any]:
        """Simplified market order interface"""
        return self.place_market_order(symbol, action, volume, 
                                     sl_pips=sl, tp_pips=tp, comment=comment)

    def _validate_order_params(self, symbol: str, action: str, volume: float) -> bool:
        """Validate order parameters"""
        try:
            # Check symbol
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False

            # Check action
            if action.lower() not in ['buy', 'sell']:
                self.logger.error(f"Invalid action: {action}")
                return False

            # Check volume
            min_volume = symbol_info.get('volume_min', 0.01)
            max_volume = symbol_info.get('volume_max', 100.0)

            if volume < min_volume or volume > max_volume:
                self.logger.error(f"Invalid volume: {volume} (min: {min_volume}, max: {max_volume})")
                return False

            # Check risk management
            if not self.risk_manager.can_open_position(symbol, volume):
                self.logger.warning("Risk manager rejected order")
                return False

            return True

        except Exception as e:
            log_error(f"Error validating order params: {e}")
            return False

    def get_active_orders(self) -> Dict[int, Dict[str, Any]]:
        """Get active orders"""
        return self.active_orders.copy()

    def get_order_history(self) -> List[Dict[str, Any]]:
        """Get order history"""
        return self.order_history.copy()

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily trading statistics"""
        return {
            'daily_trades': self.daily_trades,
            'max_daily_trades': self.max_daily_trades,
            'active_orders_count': len(self.active_orders),
            'total_orders': len(self.order_history)
        }

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_trades = 0
        self.order_history.clear()
        self.logger.info("Daily statistics reset")