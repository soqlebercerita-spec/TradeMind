
"""
Data management system for AuraTrade Bot
Handles market data retrieval, processing, and caching
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import time
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class DataManager:
    """Market data management system"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.mt5_connector = mt5_connector
        self.logger = Logger().get_logger()
        
        # Data cache
        self.data_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_expiry = 30  # Cache for 30 seconds
        
        # Supported timeframes
        self.timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
        
        # Data update thread
        self.update_thread = None
        self.updating = False
        
    def get_rates(self, symbol: str, timeframe: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """Get historical rates with caching"""
        try:
            cache_key = f"{symbol}_{timeframe}_{count}"
            
            with self.cache_lock:
                # Check cache first
                if cache_key in self.data_cache:
                    cached_data, timestamp = self.data_cache[cache_key]
                    if (datetime.now() - timestamp).seconds < self.cache_expiry:
                        return cached_data.copy()
            
            # Get fresh data from MT5
            data = self.mt5_connector.get_rates(symbol, timeframe, count)
            
            if data is not None and not data.empty:
                with self.cache_lock:
                    # Cache the data
                    self.data_cache[cache_key] = (data.copy(), datetime.now())
                
                return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting rates for {symbol} {timeframe}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current bid/ask prices"""
        try:
            prices = self.mt5_connector.get_current_price(symbol)
            if prices:
                bid, ask = prices
                return {
                    'bid': bid,
                    'ask': ask,
                    'spread': ask - bid,
                    'mid': (bid + ask) / 2,
                    'timestamp': datetime.now()
                }
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting current price for {symbol}: {e}")
            return None
    
    def update_symbol_data(self, symbol: str):
        """Update data for specific symbol"""
        try:
            for timeframe in ['M1', 'M5', 'M15', 'H1']:
                self.get_rates(symbol, timeframe, 500)
                
        except Exception as e:
            self.logger.error(f"❌ Error updating data for {symbol}: {e}")
    
    def start_data_updates(self, symbols: List[str]):
        """Start background data updates"""
        try:
            if self.updating:
                return
            
            self.updating = True
            self.update_thread = threading.Thread(
                target=self._data_update_loop, 
                args=(symbols,), 
                daemon=True
            )
            self.update_thread.start()
            
            self.logger.info("📊 Data update service started")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting data updates: {e}")
    
    def stop_data_updates(self):
        """Stop background data updates"""
        try:
            self.updating = False
            if self.update_thread:
                self.update_thread.join(timeout=5)
            
            self.logger.info("📊 Data update service stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping data updates: {e}")
    
    def _data_update_loop(self, symbols: List[str]):
        """Background data update loop"""
        while self.updating:
            try:
                for symbol in symbols:
                    if not self.updating:
                        break
                    
                    self.update_symbol_data(symbol)
                    time.sleep(1)  # Small delay between symbols
                
                # Wait before next full update cycle
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"❌ Error in data update loop: {e}")
                time.sleep(10)
    
    def clear_cache(self):
        """Clear data cache"""
        try:
            with self.cache_lock:
                self.data_cache.clear()
            
            self.logger.info("🗑️ Data cache cleared")
            
        except Exception as e:
            self.logger.error(f"❌ Error clearing cache: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        try:
            with self.cache_lock:
                return {
                    'cached_items': len(self.data_cache),
                    'cache_keys': list(self.data_cache.keys()),
                    'cache_expiry_seconds': self.cache_expiry,
                    'updating': self.updating
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting cache info: {e}")
            return {}
