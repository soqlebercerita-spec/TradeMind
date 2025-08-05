"""
MetaTrader 5 connection and management module
Handles all MT5 operations including connection, account management, and data retrieval
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import time
import threading
from config.credentials import Credentials
from utils.logger import Logger

class MT5Connector:
    """MetaTrader 5 connection manager with auto-reconnect"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.credentials = Credentials()
        self.connected = False
        self.auto_reconnect = True
        self.connection_lock = threading.Lock()
        self.last_connection_attempt = 0
        self.reconnect_interval = 30  # seconds

    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        with self.connection_lock:
            try:
                self.logger.info("Connecting to MetaTrader 5...")

                # Initialize MT5 connection
                if not mt5.initialize():
                    error = mt5.last_error()
                    self.logger.error(f"Failed to initialize MT5: {error}")
                    return False

                # Login with credentials
                login_result = mt5.login(
                    login=self.credentials.MT5_LOGIN,
                    password=self.credentials.MT5_PASSWORD,
                    server=self.credentials.MT5_SERVER
                )

                if not login_result:
                    error = mt5.last_error()
                    self.logger.error(f"Failed to login to MT5: {error}")
                    mt5.shutdown()
                    return False

                # Verify connection
                account_info = mt5.account_info()
                if account_info is None:
                    self.logger.error("Failed to get account info")
                    mt5.shutdown()
                    return False

                self.connected = True
                self.logger.info(f"Connected to MT5 - Account: {account_info.login}, Balance: ${account_info.balance:.2f}")
                return True

            except Exception as e:
                self.logger.error(f"Exception during MT5 connection: {e}")
                return False

    def disconnect(self):
        """Disconnect from MT5"""
        with self.connection_lock:
            try:
                if self.connected:
                    mt5.shutdown()
                    self.connected = False
                    self.logger.info("Disconnected from MT5")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")

    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        try:
            if not self.connected:
                return False

            # Test connection with account info
            account_info = mt5.account_info()
            return account_info is not None
        except:
            return False

    def ensure_connection(self) -> bool:
        """Ensure MT5 connection is active, reconnect if needed"""
        if self.is_connected():
            return True

        if not self.auto_reconnect:
            return False

        # Throttle reconnection attempts
        current_time = time.time()
        if current_time - self.last_connection_attempt < self.reconnect_interval:
            return False

        self.last_connection_attempt = current_time
        self.logger.info("Attempting to reconnect to MT5...")
        return self.connect()

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.ensure_connection():
            return {}

        try:
            account_info = mt5.account_info()
            if account_info is None:
                return {}

            return {
                'login': account_info.login,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'profit': account_info.profit,
                'server': account_info.server,
                'currency': account_info.currency,
                'company': account_info.company
            }
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        if not self.ensure_connection():
            return []

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': pos.type,
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'time': pos.time,
                    'comment': pos.comment
                })
            return result
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        if not self.ensure_connection():
            return None

        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None

            return {
                'symbol': symbol_info.name,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'spread': symbol_info.spread,
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'trade_contract_size': symbol_info.trade_contract_size,
                'trade_tick_value': symbol_info.trade_tick_value,
                'trade_tick_size': symbol_info.trade_tick_size,
                'margin_initial': symbol_info.margin_initial,
                'session_deals': symbol_info.session_deals,
                'session_buy_orders': symbol_info.session_buy_orders,
                'session_sell_orders': symbol_info.session_sell_orders,
                'volume_high': symbol_info.volume_high,
                'volume_low': symbol_info.volume_low
            }
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None

    def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical rates"""
        if not self.ensure_connection():
            return None

        try:
            # Convert timeframe string to MT5 constant
            tf_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }

            if timeframe not in tf_map:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return None

            rates = mt5.copy_rates_from_pos(symbol, tf_map[timeframe], 0, count)
            if rates is None or len(rates) == 0:
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            return df
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None

    def send_order(self, symbol: str, order_type: int, lot: float, price: float = 0.0, 
                   sl: float = 0.0, tp: float = 0.0, comment: str = "") -> Dict[str, Any]:
        """Send trading order"""
        if not self.ensure_connection():
            return {'success': False, 'error': 'Not connected to MT5'}

        try:
            # Get symbol info for filling mode
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {'success': False, 'error': f'Symbol {symbol} not found'}

            # Prepare request
            if price == 0.0:
                if order_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]:
                    price = symbol_info.ask if order_type == mt5.ORDER_TYPE_BUY else symbol_info.bid

            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': lot,
                'type': order_type,
                'price': price,
                'sl': sl,
                'tp': tp,
                'deviation': 10,
                'magic': 12345,
                'comment': comment,
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC
            }

            # Send order
            result = mt5.order_send(request)
            if result is None:
                return {'success': False, 'error': 'Order send failed'}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f'Order failed: {result.comment}',
                    'retcode': result.retcode
                }

            return {
                'success': True,
                'ticket': result.order,
                'volume': result.volume,
                'price': result.price,
                'comment': result.comment
            }

        except Exception as e:
            self.logger.error(f"Error sending order: {e}")
            return {'success': False, 'error': str(e)}

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close position by ticket"""
        if not self.ensure_connection():
            return {'success': False, 'error': 'Not connected to MT5'}

        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return {'success': False, 'error': 'Position not found'}

            pos = position[0]

            # Determine opposite order type
            if pos.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info(pos.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info(pos.symbol).ask

            # Prepare close request
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'position': ticket,
                'symbol': pos.symbol,
                'volume': pos.volume,
                'type': order_type,
                'price': price,
                'deviation': 10,
                'magic': 12345,
                'comment': 'Close position',
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC
            }

            # Send close order
            result = mt5.order_send(request)
            if result is None:
                return {'success': False, 'error': 'Close order failed'}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f'Close failed: {result.comment}',
                    'retcode': result.retcode
                }

            return {
                'success': True,
                'ticket': result.order,
                'volume': result.volume,
                'price': result.price
            }

        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}

    def modify_position(self, ticket: int, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Modify position SL/TP"""
        if not self.ensure_connection():
            return {'success': False, 'error': 'Not connected to MT5'}

        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return {'success': False, 'error': 'Position not found'}

            pos = position[0]

            # Prepare modify request
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'position': ticket,
                'symbol': pos.symbol,
                'sl': sl,
                'tp': tp
            }

            # Send modify order
            result = mt5.order_send(request)
            if result is None:
                return {'success': False, 'error': 'Modify order failed'}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f'Modify failed: {result.comment}',
                    'retcode': result.retcode
                }

            return {'success': True, 'message': 'Position modified successfully'}

        except Exception as e:
            self.logger.error(f"Error modifying position: {e}")
            return {'success': False, 'error': str(e)}