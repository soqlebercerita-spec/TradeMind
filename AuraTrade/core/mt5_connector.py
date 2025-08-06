
"""
MT5 Connector for AuraTrade Bot
Complete MetaTrader 5 connection and data management
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import time
import threading
from utils.logger import Logger

class MT5Connector:
    """MetaTrader 5 connection and data management"""
    
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize MT5 connector"""
        self.logger = Logger().get_logger()
        self.credentials = credentials
        self.connected = False
        self.connection_lock = threading.Lock()
        self.last_connection_check = 0
        self.connection_check_interval = 60  # Check every minute
        
        # Connection parameters
        self.login = credentials.get('login')
        self.password = credentials.get('password')
        self.server = credentials.get('server')
        self.timeout = credentials.get('timeout', 60000)
        
        self.logger.info("MT5Connector initialized")
    
    def connect(self) -> bool:
        """Connect to MT5"""
        with self.connection_lock:
            try:
                self.logger.info("Connecting to MT5...")
                
                # Initialize MT5
                if not mt5.initialize():
                    self.logger.error("MT5 initialization failed")
                    return False
                
                # Login if credentials provided
                if self.login and self.password and self.server:
                    if not mt5.login(
                        login=int(self.login),
                        password=self.password,
                        server=self.server,
                        timeout=self.timeout
                    ):
                        error = mt5.last_error()
                        self.logger.error(f"MT5 login failed: {error}")
                        mt5.shutdown()
                        return False
                    
                    self.logger.info(f"Connected to MT5 server: {self.server}")
                else:
                    self.logger.info("Connected to MT5 without login (demo mode)")
                
                self.connected = True
                self.last_connection_check = time.time()
                return True
                
            except Exception as e:
                self.logger.error(f"MT5 connection error: {e}")
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
                self.logger.error(f"Error disconnecting from MT5: {e}")
    
    def check_connection(self) -> bool:
        """Check MT5 connection status"""
        current_time = time.time()
        
        # Check periodically to avoid overhead
        if current_time - self.last_connection_check < self.connection_check_interval:
            return self.connected
        
        try:
            # Test connection with a simple call
            account_info = mt5.account_info()
            if account_info is None:
                self.connected = False
            else:
                self.connected = True
            
            self.last_connection_check = current_time
            return self.connected
            
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            self.connected = False
            return False
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            if not self.check_connection():
                return None
            
            info = mt5.account_info()
            if info is None:
                return None
            
            return {
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'margin_free': info.margin_free,
                'margin_level': info.margin_level,
                'profit': info.profit,
                'currency': info.currency,
                'leverage': info.leverage,
                'server': info.server,
                'name': info.name,
                'login': info.login
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        try:
            if not self.check_connection():
                return None
            
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
            
            return {
                'symbol': info.name,
                'bid': info.bid,
                'ask': info.ask,
                'spread': info.spread,
                'digits': info.digits,
                'point': info.point,
                'trade_mode': info.trade_mode,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
                'trade_contract_size': info.trade_contract_size,
                'margin_initial': info.margin_initial,
                'currency_base': info.currency_base,
                'currency_profit': info.currency_profit,
                'currency_margin': info.currency_margin
            }
            
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_symbols(self) -> List[str]:
        """Get available symbols"""
        try:
            if not self.check_connection():
                return []
            
            symbols = mt5.symbols_get()
            if symbols is None:
                return []
            
            return [symbol.name for symbol in symbols if symbol.visible]
            
        except Exception as e:
            self.logger.error(f"Error getting symbols: {e}")
            return []
    
    def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical rates"""
        try:
            if not self.check_connection():
                return None
            
            # Convert timeframe string to MT5 constant
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
                'MN1': mt5.TIMEFRAME_MN1
            }
            
            tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_M1)
            
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
            if rates is None:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def get_ticks(self, symbol: str, count: int = 100) -> Optional[pd.DataFrame]:
        """Get recent ticks"""
        try:
            if not self.check_connection():
                return None
            
            ticks = mt5.copy_ticks_from_pos(symbol, 0, count, mt5.COPY_TICKS_ALL)
            if ticks is None:
                return None
            
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting ticks for {symbol}: {e}")
            return None
    
    def send_order(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send trading order"""
        try:
            if not self.check_connection():
                return None
            
            # Validate request
            required_fields = ['action', 'symbol', 'volume', 'type']
            for field in required_fields:
                if field not in request:
                    self.logger.error(f"Missing required field: {field}")
                    return None
            
            result = mt5.order_send(request)
            if result is None:
                return None
            
            return {
                'retcode': result.retcode,
                'deal': result.deal,
                'order': result.order,
                'volume': result.volume,
                'price': result.price,
                'bid': result.bid,
                'ask': result.ask,
                'comment': result.comment,
                'request_id': result.request_id,
                'retcode_external': result.retcode_external
            }
            
        except Exception as e:
            self.logger.error(f"Error sending order: {e}")
            return None
    
    def get_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open positions"""
        try:
            if not self.check_connection():
                return []
            
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'time': pos.time,
                    'type': pos.type,
                    'magic': pos.magic,
                    'identifier': pos.identifier,
                    'reason': pos.reason,
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'price_current': pos.price_current,
                    'swap': pos.swap,
                    'profit': pos.profit,
                    'symbol': pos.symbol,
                    'comment': pos.comment,
                    'external_id': pos.external_id
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get pending orders"""
        try:
            if not self.check_connection():
                return []
            
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()
            
            if orders is None:
                return []
            
            result = []
            for order in orders:
                result.append({
                    'ticket': order.ticket,
                    'time_setup': order.time_setup,
                    'type': order.type,
                    'state': order.state,
                    'magic': order.magic,
                    'volume_initial': order.volume_initial,
                    'volume_current': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'symbol': order.symbol,
                    'comment': order.comment,
                    'external_id': order.external_id
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []
    
    def close_position(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Close position by ticket"""
        try:
            if not self.check_connection():
                return None
            
            # Get position info
            positions = self.get_positions()
            position = None
            
            for pos in positions:
                if pos['ticket'] == ticket:
                    position = pos
                    break
            
            if not position:
                self.logger.error(f"Position {ticket} not found")
                return None
            
            # Prepare close request
            symbol = position['symbol']
            volume = position['volume']
            position_type = position['type']
            
            # Determine close type and price
            if position_type == 0:  # BUY position
                close_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:  # SELL position
                close_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': volume,
                'type': close_type,
                'position': ticket,
                'price': price,
                'deviation': 20,
                'magic': position['magic'],
                'comment': 'Position closed by AuraTrade',
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC
            }
            
            return self.send_order(request)
            
        except Exception as e:
            self.logger.error(f"Error closing position {ticket}: {e}")
            return None
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> Optional[Dict[str, Any]]:
        """Modify position SL/TP"""
        try:
            if not self.check_connection():
                return None
            
            # Get position info
            positions = self.get_positions()
            position = None
            
            for pos in positions:
                if pos['ticket'] == ticket:
                    position = pos
                    break
            
            if not position:
                self.logger.error(f"Position {ticket} not found")
                return None
            
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'position': ticket,
                'sl': sl if sl is not None else position['sl'],
                'tp': tp if tp is not None else position['tp']
            }
            
            return self.send_order(request)
            
        except Exception as e:
            self.logger.error(f"Error modifying position {ticket}: {e}")
            return None
    
    def get_market_hours(self, symbol: str) -> Dict[str, Any]:
        """Get market trading hours"""
        try:
            if not self.check_connection():
                return {}
            
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return {}
            
            return {
                'trading_allowed': symbol_info['trade_mode'] != 0,
                'session_deals': True,
                'session_buy_orders': True,
                'session_sell_orders': True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market hours for {symbol}: {e}")
            return {}
    
    def calculate_margin(self, symbol: str, volume: float, order_type: int) -> Optional[float]:
        """Calculate required margin"""
        try:
            if not self.check_connection():
                return None
            
            margin = mt5.order_calc_margin(order_type, symbol, volume, 0.0)
            return margin
            
        except Exception as e:
            self.logger.error(f"Error calculating margin: {e}")
            return None
    
    def calculate_profit(self, symbol: str, volume: float, order_type: int, 
                        price_open: float, price_close: float) -> Optional[float]:
        """Calculate profit"""
        try:
            if not self.check_connection():
                return None
            
            profit = mt5.order_calc_profit(order_type, symbol, volume, price_open, price_close)
            return profit
            
        except Exception as e:
            self.logger.error(f"Error calculating profit: {e}")
            return None
