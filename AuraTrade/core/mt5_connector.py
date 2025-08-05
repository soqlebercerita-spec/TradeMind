
"""
MetaTrader 5 Connector for AuraTrade Bot
Supports both real MT5 connection and mock mode for development
"""

import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from utils.logger import Logger

class MT5Position:
    """Mock MT5 position"""
    def __init__(self, ticket: int, symbol: str, volume: float, type_: int, price_open: float):
        self.ticket = ticket
        self.symbol = symbol
        self.volume = volume
        self.type = type_  # 0=buy, 1=sell
        self.price_open = price_open
        self.price_current = price_open
        self.profit = 0.0
        self.swap = 0.0
        self.comment = "AuraTrade"
        self.time = int(time.time())

class MT5Order:
    """Mock MT5 order"""
    def __init__(self, ticket: int, symbol: str, volume: float, type_: int, price: float):
        self.ticket = ticket
        self.symbol = symbol
        self.volume = volume
        self.type = type_
        self.price_open = price
        self.state = 1  # filled
        self.time_setup = int(time.time())

class MT5Connector:
    """Enhanced MT5 Connector with mock functionality"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.connected = False
        self.mock_mode = True  # Always mock in Replit
        self.symbols_info = {}
        self.account_info = self._create_mock_account()
        self.positions = {}
        self.orders = {}
        self.order_counter = 10001
        self.price_thread = None
        self.price_running = False
        
        # Initialize mock symbols
        self._initialize_mock_symbols()
        
    def _create_mock_account(self) -> Dict[str, Any]:
        """Create mock account info"""
        return {
            'login': 12345678,
            'balance': 10000.0,
            'equity': 10000.0,
            'margin': 0.0,
            'free_margin': 10000.0,
            'margin_level': 0.0,
            'leverage': 100,
            'currency': 'USD',
            'profit': 0.0,
            'server': 'MockBroker-Demo',
            'name': 'AuraTrade Demo',
            'company': 'MockBroker'
        }
        
    def _initialize_mock_symbols(self):
        """Initialize mock symbol data"""
        symbols = {
            'EURUSD': {'base_price': 1.08500, 'spread': 0.00020, 'digits': 5, 'point': 0.00001},
            'GBPUSD': {'base_price': 1.27500, 'spread': 0.00025, 'digits': 5, 'point': 0.00001},
            'USDJPY': {'base_price': 148.500, 'spread': 0.020, 'digits': 3, 'point': 0.001},
            'USDCHF': {'base_price': 0.87500, 'spread': 0.00025, 'digits': 5, 'point': 0.00001},
            'AUDUSD': {'base_price': 0.66500, 'spread': 0.00020, 'digits': 5, 'point': 0.00001},
            'USDCAD': {'base_price': 1.35500, 'spread': 0.00025, 'digits': 5, 'point': 0.00001},
            'NZDUSD': {'base_price': 0.61500, 'spread': 0.00020, 'digits': 5, 'point': 0.00001},
            'XAUUSD': {'base_price': 2050.00, 'spread': 0.50, 'digits': 2, 'point': 0.01},
            'XAGUSD': {'base_price': 25.500, 'spread': 0.030, 'digits': 3, 'point': 0.001},
            'BTCUSD': {'base_price': 42000.0, 'spread': 10.0, 'digits': 1, 'point': 0.1},
            'ETHUSD': {'base_price': 2500.0, 'spread': 2.0, 'digits': 2, 'point': 0.01}
        }
        
        for symbol, data in symbols.items():
            self.symbols_info[symbol] = {
                'symbol': symbol,
                'bid': data['base_price'],
                'ask': data['base_price'] + data['spread'],
                'point': data['point'],
                'digits': data['digits'],
                'spread': int(data['spread'] / data['point']),
                'contract_size': 100000 if 'USD' in symbol and 'XAU' not in symbol and 'XAG' not in symbol else 1000
            }
    
    def connect(self) -> bool:
        """Connect to MT5 (mock mode)"""
        try:
            self.logger.info("Connecting to MT5 (Mock Mode for Replit)...")
            time.sleep(1)  # Simulate connection time
            
            self.connected = True
            self._start_price_updates()
            
            self.logger.info(f"Connected to MT5 successfully")
            self.logger.info(f"Account: {self.account_info['login']}")
            self.logger.info(f"Balance: ${self.account_info['balance']:.2f}")
            self.logger.info(f"Server: {self.account_info['server']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        try:
            self.connected = False
            self._stop_price_updates()
            self.logger.info("Disconnected from MT5")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def _start_price_updates(self):
        """Start background price updates"""
        if not self.price_running:
            self.price_running = True
            self.price_thread = threading.Thread(target=self._update_prices)
            self.price_thread.daemon = True
            self.price_thread.start()
    
    def _stop_price_updates(self):
        """Stop background price updates"""
        self.price_running = False
        if self.price_thread:
            self.price_thread.join(timeout=1)
    
    def _update_prices(self):
        """Update symbol prices continuously"""
        while self.price_running and self.connected:
            try:
                for symbol in self.symbols_info:
                    self._simulate_price_movement(symbol)
                time.sleep(0.1)  # Update every 100ms
            except Exception as e:
                self.logger.error(f"Error updating prices: {e}")
                break
    
    def _simulate_price_movement(self, symbol: str):
        """Simulate realistic price movement"""
        if symbol not in self.symbols_info:
            return
            
        symbol_info = self.symbols_info[symbol]
        current_bid = symbol_info['bid']
        point = symbol_info['point']
        
        # Simulate price movement
        volatility = {
            'EURUSD': 10, 'GBPUSD': 15, 'USDJPY': 20, 'USDCHF': 8,
            'AUDUSD': 12, 'USDCAD': 10, 'NZDUSD': 15, 'XAUUSD': 100,
            'XAGUSD': 50, 'BTCUSD': 500, 'ETHUSD': 200
        }.get(symbol, 10)
        
        movement = random.uniform(-volatility, volatility) * point
        new_bid = current_bid + movement
        
        # Update prices
        symbol_info['bid'] = new_bid
        symbol_info['ask'] = new_bid + (symbol_info['spread'] * point)
        
        # Update position profits
        self._update_position_profits(symbol)
    
    def _update_position_profits(self, symbol: str):
        """Update profits for positions of given symbol"""
        for position in self.positions.values():
            if position.symbol == symbol:
                current_price = self.symbols_info[symbol]['bid' if position.type == 1 else 'ask']
                if position.type == 0:  # Buy
                    position.profit = (current_price - position.price_open) * position.volume * self.symbols_info[symbol]['contract_size']
                else:  # Sell
                    position.profit = (position.price_open - current_price) * position.volume * self.symbols_info[symbol]['contract_size']
                position.price_current = current_price
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.connected:
            self.logger.warning("Not connected to MT5")
            return {}
        
        # Update equity based on positions
        total_profit = sum(pos.profit for pos in self.positions.values())
        self.account_info['profit'] = total_profit
        self.account_info['equity'] = self.account_info['balance'] + total_profit
        self.account_info['free_margin'] = self.account_info['equity'] - self._calculate_margin()
        
        if self.account_info['equity'] > 0:
            self.account_info['margin_level'] = (self.account_info['equity'] / max(self._calculate_margin(), 1)) * 100
        
        return self.account_info.copy()
    
    def _calculate_margin(self) -> float:
        """Calculate required margin"""
        margin = 0.0
        for position in self.positions.values():
            symbol_info = self.symbols_info.get(position.symbol, {})
            contract_size = symbol_info.get('contract_size', 100000)
            current_price = symbol_info.get('bid', 1.0)
            leverage = self.account_info['leverage']
            margin += (position.volume * contract_size * current_price) / leverage
        return margin
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        return self.symbols_info.get(symbol)
    
    def get_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current tick for symbol"""
        if symbol not in self.symbols_info:
            return None
            
        symbol_info = self.symbols_info[symbol]
        return {
            'symbol': symbol,
            'bid': symbol_info['bid'],
            'ask': symbol_info['ask'],
            'time': int(time.time())
        }
    
    def get_rates(self, symbol: str, timeframe: int, start: int, count: int) -> Optional[pd.DataFrame]:
        """Get historical rates (mock data)"""
        try:
            if symbol not in self.symbols_info:
                return None
            
            # Generate mock OHLC data
            base_price = self.symbols_info[symbol]['bid']
            point = self.symbols_info[symbol]['point']
            
            data = []
            current_time = int(time.time()) - (count * 60)  # 1-minute bars
            
            for i in range(count):
                volatility = random.uniform(0.5, 2.0)
                open_price = base_price + random.uniform(-50, 50) * point
                high_price = open_price + random.uniform(0, 30) * point * volatility
                low_price = open_price - random.uniform(0, 30) * point * volatility
                close_price = open_price + random.uniform(-20, 20) * point
                volume = random.randint(50, 500)
                
                data.append({
                    'time': current_time + (i * 60),
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'tick_volume': volume
                })
            
            df = pd.DataFrame(data)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def send_order(self, action: str, symbol: str, volume: float, price: float = 0.0, 
                   sl: float = 0.0, tp: float = 0.0, comment: str = "AuraTrade") -> Dict[str, Any]:
        """Send trading order"""
        try:
            if not self.connected:
                return {'retcode': 10004, 'comment': 'Not connected'}
            
            if symbol not in self.symbols_info:
                return {'retcode': 10013, 'comment': 'Invalid symbol'}
            
            symbol_info = self.symbols_info[symbol]
            ticket = self.order_counter
            self.order_counter += 1
            
            # Determine order type and price
            if action == 'buy':
                order_type = 0
                execution_price = symbol_info['ask'] if price == 0.0 else price
            elif action == 'sell':
                order_type = 1
                execution_price = symbol_info['bid'] if price == 0.0 else price
            else:
                return {'retcode': 10015, 'comment': 'Invalid action'}
            
            # Create position
            position = MT5Position(ticket, symbol, volume, order_type, execution_price)
            self.positions[ticket] = position
            
            # Create order record
            order = MT5Order(ticket, symbol, volume, order_type, execution_price)
            self.orders[ticket] = order
            
            self.logger.info(f"Order executed: {action.upper()} {volume} {symbol} at {execution_price:.5f}")
            
            return {
                'retcode': 10009,  # TRADE_RETCODE_DONE
                'deal': ticket,
                'order': ticket,
                'volume': volume,
                'price': execution_price,
                'comment': 'Success'
            }
            
        except Exception as e:
            self.logger.error(f"Error sending order: {e}")
            return {'retcode': 10011, 'comment': str(e)}
    
    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close position by ticket"""
        try:
            if ticket not in self.positions:
                return {'retcode': 10013, 'comment': 'Position not found'}
            
            position = self.positions[ticket]
            symbol_info = self.symbols_info[position.symbol]
            
            # Close at current market price
            close_price = symbol_info['bid'] if position.type == 0 else symbol_info['ask']
            
            # Calculate final profit
            if position.type == 0:  # Buy position
                final_profit = (close_price - position.price_open) * position.volume * symbol_info['contract_size']
            else:  # Sell position
                final_profit = (position.price_open - close_price) * position.volume * symbol_info['contract_size']
            
            # Update account balance
            self.account_info['balance'] += final_profit
            
            # Remove position
            del self.positions[ticket]
            
            self.logger.info(f"Position closed: #{ticket} Profit: ${final_profit:.2f}")
            
            return {
                'retcode': 10009,
                'deal': ticket + 10000,
                'order': ticket + 10000,
                'volume': position.volume,
                'price': close_price,
                'profit': final_profit,
                'comment': 'Success'
            }
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {'retcode': 10011, 'comment': str(e)}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        positions = []
        for ticket, position in self.positions.items():
            positions.append({
                'ticket': ticket,
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
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        orders = []
        for ticket, order in self.orders.items():
            orders.append({
                'ticket': ticket,
                'symbol': order.symbol,
                'volume': order.volume,
                'type': order.type,
                'price_open': order.price_open,
                'state': order.state,
                'time_setup': order.time_setup
            })
        return orders
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Modify position SL/TP"""
        try:
            if ticket not in self.positions:
                return {'retcode': 10013, 'comment': 'Position not found'}
            
            # In mock mode, just log the modification
            self.logger.info(f"Position #{ticket} modified - SL: {sl}, TP: {tp}")
            
            return {
                'retcode': 10009,
                'comment': 'Success'
            }
            
        except Exception as e:
            self.logger.error(f"Error modifying position: {e}")
            return {'retcode': 10011, 'comment': str(e)}
    
    def check_connection(self) -> bool:
        """Check if connection is alive"""
        return self.connected
    
    def reconnect(self) -> bool:
        """Reconnect to MT5"""
        if not self.connected:
            return self.connect()
        return True
