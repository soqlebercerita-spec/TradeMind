
"""
Mock MetaTrader 5 Connector for AuraTrade Bot
Simulates MT5 functionality for development and testing in Replit environment
"""

import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from utils.logger import Logger

class MockMT5Account:
    """Mock MT5 account info"""
    def __init__(self):
        self.login = 12345678
        self.balance = 10000.0
        self.equity = 10000.0
        self.margin = 0.0
        self.free_margin = 10000.0
        self.leverage = 100
        self.currency = "USD"

class MockMT5Symbol:
    """Mock symbol info"""
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bid = self._generate_price(symbol)
        self.ask = self.bid + 0.00020  # 2 pip spread
        self.point = 0.00001
        self.digits = 5
        self.spread = 20
        
    def _generate_price(self, symbol: str) -> float:
        """Generate realistic price for symbol"""
        base_prices = {
            'EURUSD': 1.08500,
            'GBPUSD': 1.27500,
            'USDJPY': 148.50,
            'USDCHF': 0.87500,
            'AUDUSD': 0.66500,
            'USDCAD': 1.35500,
            'NZDUSD': 0.61500,
            'XAUUSD': 2050.00,
            'XAGUSD': 25.50,
            'BTCUSD': 42000.00,
            'ETHUSD': 2500.00
        }
        base = base_prices.get(symbol, 1.0)
        # Add small random variation
        return base + random.uniform(-0.01, 0.01) * base

class MockMT5Position:
    """Mock position"""
    def __init__(self, ticket: int, symbol: str, volume: float, type_pos: int, price_open: float):
        self.ticket = ticket
        self.symbol = symbol
        self.volume = volume
        self.type = type_pos  # 0=BUY, 1=SELL
        self.price_open = price_open
        self.price_current = price_open
        self.profit = 0.0
        self.swap = 0.0
        self.comment = "Mock Position"
        self.time = int(time.time())

class MT5Connector:
    """Mock MT5 Connector - Simulates real MT5 trading"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.connected = False
        self.account = MockMT5Account()
        self.symbols = {}
        self.positions = {}
        self.orders = {}
        self.next_ticket = 1000000
        self.price_update_thread = None
        self.running = False
        
        # Initialize symbols
        symbol_list = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
        for symbol in symbol_list:
            self.symbols[symbol] = MockMT5Symbol(symbol)
        
        self.logger.info("Mock MT5 Connector initialized")

    def connect(self, login: int = None, password: str = None, server: str = None) -> bool:
        """Simulate MT5 connection"""
        try:
            self.logger.info("Connecting to Mock MT5...")
            
            # Simulate connection delay
            time.sleep(1)
            
            self.connected = True
            self.running = True
            
            # Start price update thread
            self._start_price_updates()
            
            self.logger.info(f"✅ Connected to Mock MT5 - Account: {self.account.login}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Mock MT5: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from MT5"""
        try:
            self.connected = False
            self.running = False
            
            if self.price_update_thread and self.price_update_thread.is_alive():
                self.price_update_thread.join(timeout=2)
            
            self.logger.info("Disconnected from Mock MT5")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            return False

    def _start_price_updates(self):
        """Start background price updates"""
        def update_prices():
            while self.running:
                try:
                    for symbol_info in self.symbols.values():
                        # Simulate price movement
                        change = random.uniform(-0.001, 0.001)
                        symbol_info.bid += change * symbol_info.bid
                        symbol_info.ask = symbol_info.bid + 0.00020
                        
                        # Update position profits
                        self._update_position_profits(symbol_info.symbol)
                    
                    time.sleep(1)  # Update every second
                    
                except Exception as e:
                    self.logger.error(f"Error updating prices: {e}")
        
        self.price_update_thread = threading.Thread(target=update_prices, daemon=True)
        self.price_update_thread.start()

    def _update_position_profits(self, symbol: str):
        """Update profits for positions"""
        current_price = self.symbols[symbol].bid
        
        for position in self.positions.values():
            if position.symbol == symbol:
                position.price_current = current_price
                
                if position.type == 0:  # BUY
                    position.profit = (current_price - position.price_open) * position.volume * 100000
                else:  # SELL
                    position.profit = (position.price_open - current_price) * position.volume * 100000

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.connected:
            return {}
        
        # Calculate total floating profit
        total_profit = sum(pos.profit for pos in self.positions.values())
        self.account.equity = self.account.balance + total_profit
        
        return {
            'login': self.account.login,
            'balance': self.account.balance,
            'equity': self.account.equity,
            'margin': self.account.margin,
            'free_margin': self.account.free_margin,
            'leverage': self.account.leverage,
            'currency': self.account.currency
        }

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        if symbol not in self.symbols:
            return None
        
        sym = self.symbols[symbol]
        return {
            'symbol': sym.symbol,
            'bid': sym.bid,
            'ask': sym.ask,
            'point': sym.point,
            'digits': sym.digits,
            'spread': sym.spread
        }

    def get_rates(self, symbol: str, timeframe: str, count: int = 1000) -> pd.DataFrame:
        """Get historical rates (simulated)"""
        try:
            if symbol not in self.symbols:
                return pd.DataFrame()
            
            # Generate mock historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=count)
            
            dates = pd.date_range(start=start_time, end=end_time, periods=count)
            base_price = self.symbols[symbol].bid
            
            # Generate OHLC data with random walk
            data = []
            current_price = base_price
            
            for i, date in enumerate(dates):
                # Random price movement
                change = random.uniform(-0.002, 0.002)
                current_price += change * current_price
                
                # Generate OHLC
                high = current_price + random.uniform(0, 0.001) * current_price
                low = current_price - random.uniform(0, 0.001) * current_price
                open_price = current_price + random.uniform(-0.0005, 0.0005) * current_price
                close_price = current_price
                volume = random.randint(100, 1000)
                
                data.append({
                    'time': date,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close_price,
                    'tick_volume': volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return pd.DataFrame()

    def order_send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send trading order (simulated)"""
        try:
            action = request.get('action')
            symbol = request.get('symbol')
            volume = request.get('volume', 0.01)
            order_type = request.get('type')
            price = request.get('price', 0)
            sl = request.get('sl', 0)
            tp = request.get('tp', 0)
            comment = request.get('comment', '')
            
            if not self.connected:
                return {'retcode': 10004, 'comment': 'Not connected'}
            
            # Generate ticket
            ticket = self.next_ticket
            self.next_ticket += 1
            
            # Get current price
            if symbol not in self.symbols:
                return {'retcode': 10013, 'comment': 'Invalid symbol'}
            
            current_symbol = self.symbols[symbol]
            
            if action == 1:  # Market order
                if order_type == 0:  # BUY
                    execution_price = current_symbol.ask
                else:  # SELL
                    execution_price = current_symbol.bid
                
                # Create position
                position = MockMT5Position(ticket, symbol, volume, order_type, execution_price)
                self.positions[ticket] = position
                
                self.logger.info(f"Order executed: {symbol} {volume} @ {execution_price}")
                
                return {
                    'retcode': 10009,  # TRADE_RETCODE_DONE
                    'deal': ticket,
                    'order': ticket,
                    'volume': volume,
                    'price': execution_price,
                    'comment': 'Order executed successfully'
                }
            
            return {'retcode': 10006, 'comment': 'Request rejected'}
            
        except Exception as e:
            self.logger.error(f"Error sending order: {e}")
            return {'retcode': 10004, 'comment': f'Error: {str(e)}'}

    def positions_get(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open positions"""
        try:
            positions = []
            for position in self.positions.values():
                if symbol is None or position.symbol == symbol:
                    positions.append({
                        'ticket': position.ticket,
                        'symbol': position.symbol,
                        'volume': position.volume,
                        'type': position.type,
                        'price_open': position.price_open,
                        'price_current': position.price_current,
                        'profit': position.profit,
                        'swap': position.swap,
                        'comment': position.comment,
                        'time': position.time
                    })
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    def position_close(self, ticket: int) -> Dict[str, Any]:
        """Close position"""
        try:
            if ticket not in self.positions:
                return {'retcode': 10013, 'comment': 'Position not found'}
            
            position = self.positions[ticket]
            
            # Update account balance
            self.account.balance += position.profit
            
            # Remove position
            del self.positions[ticket]
            
            self.logger.info(f"Position closed: {ticket} with profit {position.profit:.2f}")
            
            return {
                'retcode': 10009,
                'comment': 'Position closed successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {'retcode': 10004, 'comment': f'Error: {str(e)}'}

    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected

    def get_last_error(self) -> int:
        """Get last error code"""
        return 0

    def get_symbols(self) -> List[str]:
        """Get available symbols"""
        return list(self.symbols.keys())

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """Select symbol for market watch"""
        if symbol not in self.symbols and enable:
            self.symbols[symbol] = MockMT5Symbol(symbol)
        return True

    def reconnect(self) -> bool:
        """Reconnect to MT5"""
        self.logger.info("Attempting to reconnect...")
        self.disconnect()
        time.sleep(2)
        return self.connect()
