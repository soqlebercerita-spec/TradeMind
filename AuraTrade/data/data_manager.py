
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
"""
Data Manager for AuraTrade Bot
Real-time and historical data management
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from utils.logger import Logger

class DataManager:
    """Data management for real-time and historical data"""
    
    def __init__(self, mt5_connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Data cache
        self.rates_cache = {}
        self.cache_duration = 60  # seconds
        
        # Timeframes
        self.timeframes = {
            'M1': 1,
            'M5': 5,
            'M15': 15,
            'M30': 30,
            'H1': 16385,
            'H4': 16388,
            'D1': 16408
        }
        
        self.logger.info("Data Manager initialized")
    
    def get_rates(self, symbol: str, timeframe: str = 'M1', count: int = 100) -> Optional[pd.DataFrame]:
        """Get historical rates with caching"""
        try:
            # Check cache
            cache_key = f"{symbol}_{timeframe}_{count}"
            if cache_key in self.rates_cache:
                cached_data, cached_time = self.rates_cache[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_duration:
                    return cached_data
            
            # Get timeframe value
            tf_value = self.timeframes.get(timeframe, 1)
            
            # Get rates from MT5
            rates = self.mt5_connector.get_rates(symbol, tf_value, 0, count)
            
            if rates is not None and len(rates) > 0:
                # Cache the data
                self.rates_cache[cache_key] = (rates, datetime.now())
                return rates
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def get_current_tick(self, symbol: str) -> Optional[Dict]:
        """Get current tick data"""
        try:
            return self.mt5_connector.get_tick(symbol)
        except Exception as e:
            self.logger.error(f"Error getting tick for {symbol}: {e}")
            return None
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market data"""
        try:
            # Get current tick
            tick = self.get_current_tick(symbol)
            if not tick:
                return {}
            
            # Get rates
            rates = self.get_rates(symbol, 'M1', 100)
            if rates is None or len(rates) == 0:
                return {}
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            
            # Calculate basic statistics
            latest_close = rates['close'].iloc[-1]
            high_24h = rates['high'].tail(24).max() if len(rates) >= 24 else rates['high'].max()
            low_24h = rates['low'].tail(24).min() if len(rates) >= 24 else rates['low'].min()
            
            # Calculate spread
            spread = tick['ask'] - tick['bid']
            point = symbol_info.get('point', 0.00001)
            spread_pips = spread / point
            
            return {
                'symbol': symbol,
                'bid': tick['bid'],
                'ask': tick['ask'],
                'last': tick.get('last', tick['bid']),
                'spread': spread,
                'spread_pips': spread_pips,
                'close': latest_close,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'change_24h': ((latest_close - rates['close'].iloc[-25]) / rates['close'].iloc[-25] * 100) if len(rates) >= 25 else 0,
                'timestamp': datetime.now(),
                'rates_count': len(rates)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return {}
    
    def calculate_volatility(self, symbol: str, period: int = 20) -> float:
        """Calculate price volatility"""
        try:
            rates = self.get_rates(symbol, 'M1', period + 10)
            if rates is None or len(rates) < period:
                return 0.0
            
            returns = rates['close'].pct_change().tail(period)
            volatility = returns.std() * np.sqrt(period)  # Annualized
            
            return volatility
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def get_support_resistance(self, symbol: str, period: int = 50) -> Dict[str, List[float]]:
        """Calculate support and resistance levels"""
        try:
            rates = self.get_rates(symbol, 'M1', period)
            if rates is None or len(rates) < period:
                return {'support': [], 'resistance': []}
            
            highs = rates['high'].values
            lows = rates['low'].values
            
            # Simple support/resistance calculation
            resistance_levels = []
            support_levels = []
            
            # Find local maxima for resistance
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
                   highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    resistance_levels.append(highs[i])
            
            # Find local minima for support
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
                   lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    support_levels.append(lows[i])
            
            # Sort and take most significant levels
            resistance_levels = sorted(set(resistance_levels), reverse=True)[:3]
            support_levels = sorted(set(support_levels))[:3]
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance: {e}")
            return {'support': [], 'resistance': []}
    
    def is_market_open(self, symbol: str = 'EURUSD') -> bool:
        """Check if market is open"""
        try:
            return self.mt5_connector.is_market_open(symbol)
        except Exception as e:
            self.logger.error(f"Error checking market status: {e}")
            return False
    
    def clear_cache(self):
        """Clear data cache"""
        self.rates_cache.clear()
        self.logger.info("Data cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            'cached_items': len(self.rates_cache),
            'cache_duration': self.cache_duration,
            'cache_keys': list(self.rates_cache.keys())
        }
