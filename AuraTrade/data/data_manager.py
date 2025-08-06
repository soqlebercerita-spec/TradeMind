
"""
Data Management Module for AuraTrade Bot
Real-time data feeds, symbol detection, and market analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import threading
import time
import queue
from core.mt5_connector import MT5Connector
from utils.logger import Logger, log_info, log_error

class DataManager:
    """Advanced data management with auto-symbol detection and real-time feeds"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Data storage
        self.symbol_data = {}
        self.tick_data = {}
        self.historical_data = {}
        
        # Auto-symbol detection
        self.available_symbols = []
        self.active_symbols = []
        
        # Real-time data feeds
        self.data_threads = {}
        self.data_queues = {}
        self.feed_active = False
        
        # Data callbacks
        self.data_callbacks = {}
        
        # Market analysis data
        self.market_sessions = {
            'asian': {'start': 0, 'end': 9},    # GMT hours
            'london': {'start': 8, 'end': 16},
            'ny': {'start': 13, 'end': 22}
        }
        
        self.logger.info("Data Manager initialized")
        
        # Initialize symbol detection
        self._detect_available_symbols()
    
    def _detect_available_symbols(self):
        """Auto-detect available symbols from MT5"""
        try:
            # In mock mode, use predefined symbols
            self.available_symbols = [
                'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD',
                'USDCAD', 'NZDUSD', 'EURJPY', 'GBPJPY', 'AUDJPY',
                'XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD'
            ]
            
            # Filter working symbols (those with valid data)
            working_symbols = []
            for symbol in self.available_symbols:
                symbol_info = self.mt5_connector.get_symbol_info(symbol)
                if symbol_info:
                    working_symbols.append(symbol)
            
            self.available_symbols = working_symbols
            self.active_symbols = self.available_symbols[:8]  # Top 8 symbols
            
            log_info("DataManager", f"Detected {len(self.available_symbols)} available symbols")
            log_info("DataManager", f"Active symbols: {', '.join(self.active_symbols)}")
            
        except Exception as e:
            log_error("DataManager", "Error detecting symbols", e)
            # Fallback to major pairs
            self.available_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
            self.active_symbols = self.available_symbols
    
    def start_data_updates(self, symbols: Optional[List[str]] = None):
        """Start real-time data updates for specified symbols"""
        try:
            if symbols is None:
                symbols = self.active_symbols
            
            self.feed_active = True
            
            for symbol in symbols:
                if symbol in self.data_threads:
                    continue  # Already running
                
                # Create data queue for symbol
                self.data_queues[symbol] = queue.Queue(maxsize=1000)
                
                # Start data feed thread
                thread = threading.Thread(
                    target=self._data_feed_worker,
                    args=(symbol,),
                    daemon=True,
                    name=f"DataFeed-{symbol}"
                )
                thread.start()
                self.data_threads[symbol] = thread
                
            log_info("DataManager", f"Started data feeds for {len(symbols)} symbols")
            
        except Exception as e:
            log_error("DataManager", "Error starting data updates", e)
    
    def stop_data_updates(self):
        """Stop all data updates"""
        try:
            self.feed_active = False
            
            # Wait for threads to finish
            for symbol, thread in self.data_threads.items():
                if thread.is_alive():
                    thread.join(timeout=2)
            
            self.data_threads.clear()
            self.data_queues.clear()
            
            log_info("DataManager", "All data feeds stopped")
            
        except Exception as e:
            log_error("DataManager", "Error stopping data updates", e)
    
    def _data_feed_worker(self, symbol: str):
        """Worker thread for real-time data feed"""
        try:
            while self.feed_active:
                # Get current tick
                tick = self.mt5_connector.get_tick(symbol)
                if tick:
                    # Store tick data
                    self._store_tick_data(symbol, tick)
                    
                    # Update symbol data
                    self._update_symbol_data(symbol, tick)
                    
                    # Call registered callbacks
                    self._call_data_callbacks(symbol, tick)
                    
                    # Add to queue for other consumers
                    try:
                        self.data_queues[symbol].put_nowait({
                            'type': 'tick',
                            'symbol': symbol,
                            'data': tick,
                            'timestamp': time.time()
                        })
                    except queue.Full:
                        # Remove oldest item and add new one
                        try:
                            self.data_queues[symbol].get_nowait()
                            self.data_queues[symbol].put_nowait({
                                'type': 'tick',
                                'symbol': symbol,
                                'data': tick,
                                'timestamp': time.time()
                            })
                        except queue.Empty:
                            pass
                
                time.sleep(0.1)  # 100ms update rate
                
        except Exception as e:
            log_error("DataManager", f"Error in data feed worker for {symbol}", e)
    
    def _store_tick_data(self, symbol: str, tick: Dict):
        """Store tick data with timestamp"""
        try:
            if symbol not in self.tick_data:
                self.tick_data[symbol] = []
            
            tick_record = {
                'timestamp': datetime.now(),
                'bid': tick.get('bid', 0),
                'ask': tick.get('ask', 0),
                'spread': tick.get('ask', 0) - tick.get('bid', 0)
            }
            
            self.tick_data[symbol].append(tick_record)
            
            # Keep only last 1000 ticks per symbol
            if len(self.tick_data[symbol]) > 1000:
                self.tick_data[symbol] = self.tick_data[symbol][-1000:]
                
        except Exception as e:
            log_error("DataManager", f"Error storing tick data for {symbol}", e)
    
    def _update_symbol_data(self, symbol: str, tick: Dict):
        """Update symbol data with current information"""
        try:
            if symbol not in self.symbol_data:
                self.symbol_data[symbol] = {
                    'symbol': symbol,
                    'last_update': None,
                    'bid': 0,
                    'ask': 0,
                    'spread': 0,
                    'daily_high': 0,
                    'daily_low': 0,
                    'daily_change': 0,
                    'volatility': 0
                }
            
            data = self.symbol_data[symbol]
            data['last_update'] = datetime.now()
            data['bid'] = tick.get('bid', 0)
            data['ask'] = tick.get('ask', 0)
            data['spread'] = data['ask'] - data['bid']
            
            # Calculate daily statistics
            self._update_daily_stats(symbol)
            
        except Exception as e:
            log_error("DataManager", f"Error updating symbol data for {symbol}", e)
    
    def _update_daily_stats(self, symbol: str):
        """Update daily statistics for symbol"""
        try:
            if symbol not in self.tick_data or not self.tick_data[symbol]:
                return
            
            # Get today's tick data
            today = datetime.now().date()
            today_ticks = [
                t for t in self.tick_data[symbol] 
                if t['timestamp'].date() == today
            ]
            
            if not today_ticks:
                return
            
            bids = [t['bid'] for t in today_ticks]
            
            if bids:
                self.symbol_data[symbol]['daily_high'] = max(bids)
                self.symbol_data[symbol]['daily_low'] = min(bids)
                
                if len(bids) > 1:
                    first_price = bids[0]
                    last_price = bids[-1]
                    self.symbol_data[symbol]['daily_change'] = ((last_price - first_price) / first_price) * 100
                    
                    # Simple volatility calculation (standard deviation)
                    self.symbol_data[symbol]['volatility'] = np.std(bids) / np.mean(bids) * 100
                
        except Exception as e:
            log_error("DataManager", f"Error updating daily stats for {symbol}", e)
    
    def _call_data_callbacks(self, symbol: str, tick: Dict):
        """Call registered data callbacks"""
        try:
            if symbol in self.data_callbacks:
                for callback in self.data_callbacks[symbol]:
                    try:
                        callback(symbol, tick)
                    except Exception as e:
                        log_error("DataManager", f"Error in data callback for {symbol}", e)
                        
        except Exception as e:
            log_error("DataManager", "Error calling data callbacks", e)
    
    def get_historical_data(self, symbol: str, timeframe: int, count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical OHLC data for symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{timeframe}_{count}"
            if cache_key in self.historical_data:
                cached_data = self.historical_data[cache_key]
                # Check if cache is recent (less than 1 minute old)
                if datetime.now() - cached_data['timestamp'] < timedelta(minutes=1):
                    return cached_data['data']
            
            # Get fresh data from MT5
            rates = self.mt5_connector.get_rates(symbol, timeframe, 0, count)
            
            if rates is not None and len(rates) > 0:
                # Cache the data
                self.historical_data[cache_key] = {
                    'data': rates,
                    'timestamp': datetime.now()
                }
                
                return rates
            
            return None
            
        except Exception as e:
            log_error("DataManager", f"Error getting historical data for {symbol}", e)
            return None
    
    def get_current_tick(self, symbol: str) -> Optional[Dict]:
        """Get current tick for symbol"""
        try:
            return self.mt5_connector.get_tick(symbol)
        except Exception as e:
            log_error("DataManager", f"Error getting current tick for {symbol}", e)
            return None
    
    def get_symbol_data(self, symbol: str) -> Optional[Dict]:
        """Get symbol data with statistics"""
        return self.symbol_data.get(symbol)
    
    def get_tick_history(self, symbol: str, count: int = 100) -> List[Dict]:
        """Get recent tick history for symbol"""
        try:
            if symbol not in self.tick_data:
                return []
            
            return self.tick_data[symbol][-count:]
            
        except Exception as e:
            log_error("DataManager", f"Error getting tick history for {symbol}", e)
            return []
    
    def register_data_callback(self, symbol: str, callback: Callable):
        """Register callback for real-time data updates"""
        try:
            if symbol not in self.data_callbacks:
                self.data_callbacks[symbol] = []
            
            self.data_callbacks[symbol].append(callback)
            log_info("DataManager", f"Registered data callback for {symbol}")
            
        except Exception as e:
            log_error("DataManager", f"Error registering callback for {symbol}", e)
    
    def unregister_data_callback(self, symbol: str, callback: Callable):
        """Unregister data callback"""
        try:
            if symbol in self.data_callbacks and callback in self.data_callbacks[symbol]:
                self.data_callbacks[symbol].remove(callback)
                log_info("DataManager", f"Unregistered data callback for {symbol}")
                
        except Exception as e:
            log_error("DataManager", f"Error unregistering callback for {symbol}", e)
    
    def get_market_session(self) -> str:
        """Get current market session"""
        try:
            current_hour = datetime.utcnow().hour
            
            active_sessions = []
            for session, times in self.market_sessions.items():
                if times['start'] <= current_hour <= times['end']:
                    active_sessions.append(session)
            
            if not active_sessions:
                return "closed"
            
            # Return the most active session
            if "ny" in active_sessions:
                return "ny"
            elif "london" in active_sessions:
                return "london"
            elif "asian" in active_sessions:
                return "asian"
            else:
                return active_sessions[0]
                
        except Exception as e:
            log_error("DataManager", "Error getting market session", e)
            return "unknown"
    
    def is_high_volatility_time(self) -> bool:
        """Check if current time is high volatility period"""
        try:
            session = self.get_market_session()
            current_hour = datetime.utcnow().hour
            
            # London-NY overlap (13:00-16:00 GMT) is highest volatility
            if 13 <= current_hour <= 16:
                return True
            
            # London open (08:00-10:00 GMT) is high volatility
            if 8 <= current_hour <= 10:
                return True
            
            # NY open (13:00-15:00 GMT) is high volatility
            if 13 <= current_hour <= 15:
                return True
            
            return False
            
        except Exception as e:
            log_error("DataManager", "Error checking volatility time", e)
            return False
    
    def get_spread_analysis(self, symbol: str) -> Dict[str, Any]:
        """Analyze spread patterns for symbol"""
        try:
            if symbol not in self.tick_data or not self.tick_data[symbol]:
                return {'status': 'no_data'}
            
            recent_ticks = self.tick_data[symbol][-50:]  # Last 50 ticks
            spreads = [t['spread'] for t in recent_ticks]
            
            if not spreads:
                return {'status': 'no_data'}
            
            avg_spread = np.mean(spreads)
            current_spread = spreads[-1]
            min_spread = min(spreads)
            max_spread = max(spreads)
            
            # Determine spread status
            if current_spread <= avg_spread * 0.8:
                spread_status = "tight"
            elif current_spread >= avg_spread * 1.5:
                spread_status = "wide"
            else:
                spread_status = "normal"
            
            return {
                'status': 'ok',
                'current_spread': current_spread,
                'avg_spread': avg_spread,
                'min_spread': min_spread,
                'max_spread': max_spread,
                'spread_status': spread_status,
                'spread_pips': current_spread * 10000  # Convert to pips for major pairs
            }
            
        except Exception as e:
            log_error("DataManager", f"Error analyzing spread for {symbol}", e)
            return {'status': 'error'}
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols"""
        return self.available_symbols.copy()
    
    def get_active_symbols(self) -> List[str]:
        """Get list of currently active symbols"""
        return self.active_symbols.copy()
    
    def set_active_symbols(self, symbols: List[str]):
        """Set active symbols for trading"""
        try:
            # Validate symbols
            valid_symbols = [s for s in symbols if s in self.available_symbols]
            
            if not valid_symbols:
                log_error("DataManager", "No valid symbols provided")
                return False
            
            self.active_symbols = valid_symbols
            log_info("DataManager", f"Active symbols updated: {', '.join(valid_symbols)}")
            
            # Restart data feeds for new symbols
            if self.feed_active:
                self.stop_data_updates()
                time.sleep(1)
                self.start_data_updates()
            
            return True
            
        except Exception as e:
            log_error("DataManager", "Error setting active symbols", e)
            return False
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report"""
        try:
            report = {
                'timestamp': datetime.now(),
                'feed_status': 'active' if self.feed_active else 'inactive',
                'symbols': {}
            }
            
            for symbol in self.active_symbols:
                symbol_report = {
                    'data_available': symbol in self.tick_data,
                    'tick_count': len(self.tick_data.get(symbol, [])),
                    'last_update': None,
                    'spread_status': 'unknown'
                }
                
                if symbol in self.symbol_data:
                    symbol_report['last_update'] = self.symbol_data[symbol]['last_update']
                
                # Check spread
                spread_analysis = self.get_spread_analysis(symbol)
                if spread_analysis['status'] == 'ok':
                    symbol_report['spread_status'] = spread_analysis['spread_status']
                
                report['symbols'][symbol] = symbol_report
            
            return report
            
        except Exception as e:
            log_error("DataManager", "Error generating data quality report", e)
            return {'error': str(e)}
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old tick data to save memory"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for symbol in list(self.tick_data.keys()):
                if symbol in self.tick_data:
                    # Filter out old ticks
                    self.tick_data[symbol] = [
                        tick for tick in self.tick_data[symbol]
                        if tick['timestamp'] > cutoff_time
                    ]
                    
                    # Remove empty entries
                    if not self.tick_data[symbol]:
                        del self.tick_data[symbol]
            
            # Clean historical data cache
            for cache_key in list(self.historical_data.keys()):
                if self.historical_data[cache_key]['timestamp'] < cutoff_time:
                    del self.historical_data[cache_key]
            
            log_info("DataManager", f"Cleaned up data older than {max_age_hours} hours")
            
        except Exception as e:
            log_error("DataManager", "Error cleaning up old data", e)
