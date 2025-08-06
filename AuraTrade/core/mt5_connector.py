
"""
MetaTrader 5 Connector for AuraTrade Bot
Handles MT5 connection, data retrieval, and order execution
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import time
import threading
from utils.logger import Logger

class MT5Connector:
    """Enhanced MT5 connector with robust connection management"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.connected = False
        self.account_info = {}
        self.symbols_info = {}
        self.connection_lock = threading.Lock()
        
        # Connection retry settings
        self.max_retries = 3
        self.retry_delay = 2
        
        self.logger.info("MT5 Connector initialized")
    
    def connect(self, login: int = None, password: str = None, server: str = None) -> bool:
        """Connect to MT5 terminal"""
        try:
            with self.connection_lock:
                if self.connected:
                    return True
                
                # Initialize MT5
                if not mt5.initialize():
                    self.logger.error("Failed to initialize MT5")
                    return False
                
                # Login if credentials provided
                if login and password and server:
                    if not mt5.login(login, password, server):
                        self.logger.error(f"Failed to login to MT5: {mt5.last_error()}")
                        mt5.shutdown()
                        return False
                
                # Verify connection
                account_info = mt5.account_info()
                if account_info is None:
                    self.logger.error("Failed to get account info")
                    mt5.shutdown()
                    return False
                
                self.account_info = account_info._asdict()
                self.connected = True
                
                self.logger.info(f"Connected to MT5 - Account: {self.account_info.get('login')}")
                self.logger.info(f"Balance: ${self.account_info.get('balance', 0):.2f}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        try:
            with self.connection_lock:
                if self.connected:
                    mt5.shutdown()
                    self.connected = False
                    self.logger.info("Disconnected from MT5")
                    
        except Exception as e:
            self.logger.error(f"Error disconnecting from MT5: {e}")
    
    def check_connection(self) -> bool:
        """Check if MT5 is connected"""
        try:
            if not self.connected:
                return False
            
            # Test connection with account info
            account_info = mt5.account_info()
            return account_info is not None
            
        except Exception as e:
            self.logger.error(f"Error checking connection: {e}")
            return False
    
    def reconnect(self) -> bool:
        """Reconnect to MT5"""
        self.logger.info("Attempting to reconnect to MT5...")
        self.disconnect()
        time.sleep(1)
        return self.connect()
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            if not self.check_connection():
                return {}
            
            account_info = mt5.account_info()
            if account_info:
                return account_info._asdict()
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        try:
            if symbol in self.symbols_info:
                return self.symbols_info[symbol]
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                info_dict = symbol_info._asdict()
                self.symbols_info[symbol] = info_dict
                return info_dict
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return {}
    
    def get_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current tick for symbol"""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick._asdict()
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting tick for {symbol}: {e}")
            return None
    
    def get_rates(self, symbol: str, timeframe: int = 1, start: int = 0, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical rates"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, start, count)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        try:
            positions = mt5.positions_get()
            if positions:
                return [pos._asdict() for pos in positions]
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get pending orders"""
        try:
            orders = mt5.orders_get()
            if orders:
                return [order._asdict() for order in orders]
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []
    
    def send_order(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send order to MT5"""
        try:
            if not self.check_connection():
                return {'retcode': -1, 'comment': 'Not connected'}
            
            result = mt5.order_send(request)
            if result:
                return result._asdict()
            
            return {'retcode': -999, 'comment': 'Order failed'}
            
        except Exception as e:
            self.logger.error(f"Error sending order: {e}")
            return {'retcode': -999, 'comment': str(e)}
    
    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close position by ticket"""
        try:
            # Get position info
            positions = self.get_positions()
            position = next((p for p in positions if p['ticket'] == ticket), None)
            
            if not position:
                return {'retcode': -1, 'comment': 'Position not found'}
            
            # Prepare close request
            symbol = position['symbol']
            volume = position['volume']
            position_type = position['type']
            
            # Determine close type
            if position_type == 0:  # Buy position
                close_type = 1  # Sell
                price = mt5.symbol_info_tick(symbol).bid
            else:  # Sell position
                close_type = 0  # Buy
                price = mt5.symbol_info_tick(symbol).ask
            
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': volume,
                'type': close_type,
                'position': ticket,
                'price': price,
                'comment': 'Close by AuraTrade',
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC,
            }
            
            result = self.send_order(request)
            
            if result.get('retcode') == 10009:
                self.logger.info(f"Position #{ticket} closed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error closing position {ticket}: {e}")
            return {'retcode': -999, 'comment': str(e)}
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Modify position SL/TP"""
        try:
            positions = self.get_positions()
            position = next((p for p in positions if p['ticket'] == ticket), None)
            
            if not position:
                return {'retcode': -1, 'comment': 'Position not found'}
            
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'symbol': position['symbol'],
                'position': ticket,
                'sl': sl or position.get('sl', 0),
                'tp': tp or position.get('tp', 0),
            }
            
            return self.send_order(request)
            
        except Exception as e:
            self.logger.error(f"Error modifying position {ticket}: {e}")
            return {'retcode': -999, 'comment': str(e)}
    
    def get_symbols(self) -> List[str]:
        """Get available symbols"""
        try:
            symbols = mt5.symbols_get()
            if symbols:
                return [symbol.name for symbol in symbols if symbol.visible]
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting symbols: {e}")
            return []
    
    def is_market_open(self, symbol: str = "EURUSD") -> bool:
        """Check if market is open for trading"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            return symbol_info.get('trade_mode', 0) == 4  # Full trading mode
            
        except Exception as e:
            self.logger.error(f"Error checking market status: {e}")
            return False
