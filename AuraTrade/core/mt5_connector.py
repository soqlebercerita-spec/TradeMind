
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
    """MetaTrader 5 connection and data management"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.credentials = Credentials()
        self.connected = False
        self.account_info = {}
        self.symbols_info = {}
        self.connection_lock = threading.Lock()
        
        # Connection monitoring
        self.last_heartbeat = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def connect(self) -> bool:
        """Establish connection to MetaTrader 5"""
        try:
            with self.connection_lock:
                # Check if MT5 is already initialized
                if not mt5.initialize():
                    self.logger.error("Failed to initialize MT5 - Make sure MT5 terminal is running")
                    return False
                
                # Get credentials
                mt5_creds = self.credentials.MT5
                
                if not mt5_creds['login'] or not mt5_creds['password']:
                    self.logger.error("MT5 credentials not configured properly")
                    return False
                
                # Attempt login
                if not mt5.login(
                    login=mt5_creds['login'], 
                    password=mt5_creds['password'], 
                    server=mt5_creds['server']
                ):
                    error = mt5.last_error()
                    self.logger.error(f"Failed to login to MT5: {error}")
                    return False
                
                # Verify connection and get account info
                account_info = mt5.account_info()
                if not account_info:
                    self.logger.error("Failed to get account information")
                    return False
                
                self.account_info = account_info._asdict()
                self.connected = True
                self.last_heartbeat = datetime.now()
                self.reconnect_attempts = 0
                
                self.logger.info(f"✅ Connected to MT5 successfully")
                self.logger.info(f"Account: {self.account_info['login']}")
                self.logger.info(f"Server: {self.account_info['server']}")
                self.logger.info(f"Balance: ${self.account_info['balance']:.2f}")
                self.logger.info(f"Equity: ${self.account_info['equity']:.2f}")
                
                # Initialize symbols info
                self._initialize_symbols()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Exception during MT5 connection: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from MetaTrader 5"""
        try:
            with self.connection_lock:
                if self.connected:
                    mt5.shutdown()
                    self.connected = False
                    self.logger.info("Disconnected from MT5")
                return True
        except Exception as e:
            self.logger.error(f"Error during MT5 disconnection: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        try:
            if not self.connected:
                return False
            
            # Perform heartbeat check
            account_info = mt5.account_info()
            if account_info is None:
                self.connected = False
                return False
            
            self.last_heartbeat = datetime.now()
            return True
            
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            self.connected = False
            return False
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to MT5"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("Maximum reconnection attempts reached")
            return False
        
        self.logger.info(f"Attempting to reconnect to MT5 (attempt {self.reconnect_attempts + 1})")
        self.reconnect_attempts += 1
        
        # Disconnect first
        self.disconnect()
        time.sleep(5)
        
        # Attempt connection
        return self.connect()
    
    def _initialize_symbols(self) -> None:
        """Initialize symbols information cache"""
        try:
            symbols = mt5.symbols_get()
            if symbols:
                for symbol in symbols:
                    symbol_info = symbol._asdict()
                    self.symbols_info[symbol_info['name']] = symbol_info
                    
                self.logger.info(f"Initialized {len(self.symbols_info)} symbols")
            else:
                self.logger.warning("No symbols available")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize symbols: {e}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information"""
        try:
            if not self.is_connected():
                if not self.reconnect():
                    return {}
            
            account_info = mt5.account_info()
            if account_info:
                self.account_info = account_info._asdict()
                return self.account_info
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            return {}
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        try:
            if symbol in self.symbols_info:
                return self.symbols_info[symbol]
            
            # Try to get from MT5 if not cached
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                symbol_dict = symbol_info._asdict()
                self.symbols_info[symbol] = symbol_dict
                return symbol_dict
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    def get_rates(self, symbol: str, timeframe: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """Get historical rates for symbol"""
        try:
            if not self.is_connected():
                if not self.reconnect():
                    return None
            
            # Map timeframe string to MT5 constant
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }
            
            mt5_timeframe = timeframe_map.get(timeframe)
            if mt5_timeframe is None:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return None
            
            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                return df
            else:
                self.logger.warning(f"No rates data for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get rates for {symbol}: {e}")
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        try:
            if not self.is_connected():
                if not self.reconnect():
                    return []
            
            positions = mt5.positions_get()
            if positions:
                return [pos._asdict() for pos in positions]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return []
    
    def place_order(self, symbol: str, order_type: int, volume: float, 
                   price: float = 0.0, sl: float = 0.0, tp: float = 0.0,
                   comment: str = "AuraTrade", magic: int = 123456) -> Optional[Dict[str, Any]]:
        """Place a trading order"""
        try:
            if not self.is_connected():
                if not self.reconnect():
                    return None
            
            # Get symbol info for proper price formatting
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"Symbol {symbol} not found")
                return None
            
            # Format prices according to symbol digits
            digits = symbol_info['digits']
            if price > 0:
                price = round(price, digits)
            if sl > 0:
                sl = round(sl, digits)
            if tp > 0:
                tp = round(tp, digits)
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price if price > 0 else 0,
                "sl": sl,
                "tp": tp,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ Order placed successfully: {result.order}")
                return result._asdict()
            else:
                error_msg = f"❌ Order failed: {result.retcode if result else 'Unknown error'}"
                if result:
                    error_msg += f" - {result.comment}"
                self.logger.error(error_msg)
                return None
                
        except Exception as e:
            self.logger.error(f"Exception placing order: {e}")
            return None
    
    def close_position(self, position_ticket: int) -> bool:
        """Close a specific position"""
        try:
            if not self.is_connected():
                if not self.reconnect():
                    return False
            
            # Get position info
            positions = mt5.positions_get(ticket=position_ticket)
            if not positions:
                self.logger.error(f"Position {position_ticket} not found")
                return False
            
            position = positions[0]
            
            # Determine opposite order type
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
            else:
                order_type = mt5.ORDER_TYPE_BUY
            
            # Create close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": position_ticket,
                "magic": position.magic,
                "comment": "Close by AuraTrade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ Position {position_ticket} closed successfully")
                return True
            else:
                error_msg = f"❌ Failed to close position {position_ticket}: {result.retcode if result else 'Unknown error'}"
                self.logger.error(error_msg)
                return False
                
        except Exception as e:
            self.logger.error(f"Exception closing position {position_ticket}: {e}")
            return False
    
    def get_current_price(self, symbol: str) -> Optional[Tuple[float, float]]:
        """Get current bid/ask prices for symbol"""
        try:
            if not self.is_connected():
                if not self.reconnect():
                    return None
            
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return (tick.bid, tick.ask)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            return None
    
    def get_spread(self, symbol: str) -> Optional[float]:
        """Get current spread for symbol in pips"""
        try:
            prices = self.get_current_price(symbol)
            if not prices:
                return None
            
            bid, ask = prices
            symbol_info = self.get_symbol_info(symbol)
            
            if not symbol_info:
                return None
            
            # Calculate spread in pips
            point = symbol_info['point']
            spread_points = ask - bid
            spread_pips = spread_points / (point * 10) if point > 0 else 0
            
            return spread_pips
            
        except Exception as e:
            self.logger.error(f"Failed to get spread for {symbol}: {e}")
            return None
    
    def is_market_open(self, symbol: str) -> bool:
        """Check if market is open for trading"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return False
            
            # Check if symbol is available for trading
            return symbol_info.get('trade_mode', 0) == mt5.SYMBOL_TRADE_MODE_FULL
            
        except Exception as e:
            self.logger.error(f"Failed to check market status for {symbol}: {e}")
            return False
