"""
Data Management module for AuraTrade Bot
Handles data retrieval, caching, and real-time updates from multiple sources
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import json
import os

from core.mt5_connector import MT5Connector
from config.config import Config
from utils.logger import Logger

class DataManager:
    """Comprehensive data management system"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger.get_logger(__name__)
        self.mt5_connector = mt5_connector
        self.config = Config()
        
        # Data cache
        self.price_cache = {}
        self.tick_cache = {}
        self.historical_cache = {}
        
        # Cache settings
        self.cache_duration = {
            "tick": 5,      # 5 seconds
            "price": 60,    # 1 minute
            "historical": 300  # 5 minutes
        }
        
        # Data update flags
        self.last_update_times = {}
        self.update_intervals = {
            "tick": 1,      # Update every second
            "price": 5,     # Update every 5 seconds
            "historical": 60   # Update every minute
        }
        
        # Threading
        self.data_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.update_threads = {}
        
        # Real-time data streaming
        self.streaming_active = False
        self.stream_subscribers = {}
        
        # Data backup
        self.backup_enabled = True
        self.backup_path = os.path.join(self.config.DATA_DIR, "backups")
        self._ensure_backup_directory()
        
        # WebSocket connections (for external data feeds)
        self.websocket_connections = {}
        
        self.logger.info("📊 Data Manager initialized")
    
    def _ensure_backup_directory(self):
        """Ensure backup directory exists"""
        try:
            os.makedirs(self.backup_path, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error creating backup directory: {e}")
    
    def start_real_time_updates(self, symbols: List[str] = None):
        """Start real-time data updates for specified symbols"""
        try:
            if symbols is None:
                symbols = self.config.SYMBOLS
            
            self.streaming_active = True
            
            for symbol in symbols:
                # Start tick data updates
                thread_name = f"tick_update_{symbol}"
                if thread_name not in self.update_threads:
                    thread = threading.Thread(
                        target=self._tick_update_worker,
                        args=(symbol,),
                        daemon=True,
                        name=thread_name
                    )
                    thread.start()
                    self.update_threads[thread_name] = thread
                
                # Start price data updates
                thread_name = f"price_update_{symbol}"
                if thread_name not in self.update_threads:
                    thread = threading.Thread(
                        target=self._price_update_worker,
                        args=(symbol,),
                        daemon=True,
                        name=thread_name
                    )
                    thread.start()
                    self.update_threads[thread_name] = thread
            
            self.logger.info(f"🔄 Real-time updates started for {len(symbols)} symbols")
            
        except Exception as e:
            self.logger.error(f"Error starting real-time updates: {e}")
    
    def stop_real_time_updates(self):
        """Stop all real-time data updates"""
        try:
            self.streaming_active = False
            
            # Wait for threads to finish
            for thread_name, thread in self.update_threads.items():
                if thread.is_alive():
                    thread.join(timeout=5)
            
            self.update_threads.clear()
            self.logger.info("🛑 Real-time updates stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping real-time updates: {e}")
    
    def _tick_update_worker(self, symbol: str):
        """Worker thread for tick data updates"""
        try:
            while self.streaming_active:
                try:
                    # Get latest tick data
                    tick_data = self.mt5_connector.get_tick_data(symbol)
                    
                    if tick_data:
                        with self.data_lock:
                            if symbol not in self.tick_cache:
                                self.tick_cache[symbol] = []
                            
                            # Add timestamp
                            tick_data["timestamp"] = time.time()
                            tick_data["symbol"] = symbol
                            
                            # Store tick data
                            self.tick_cache[symbol].append(tick_data)
                            
                            # Keep only recent ticks (last 1000)
                            if len(self.tick_cache[symbol]) > 1000:
                                self.tick_cache[symbol] = self.tick_cache[symbol][-1000:]
                            
                            # Update last update time
                            self.last_update_times[f"tick_{symbol}"] = time.time()
                        
                        # Notify subscribers
                        self._notify_subscribers(symbol, "tick", tick_data)
                    
                    time.sleep(self.update_intervals["tick"])
                    
                except Exception as e:
                    self.logger.error(f"Error in tick update worker for {symbol}: {e}")
                    time.sleep(5)  # Wait longer on error
                    
        except Exception as e:
            self.logger.error(f"Tick update worker for {symbol} crashed: {e}")
    
    def _price_update_worker(self, symbol: str):
        """Worker thread for price data updates"""
        try:
            while self.streaming_active:
                try:
                    # Get latest price data for different timeframes
                    for timeframe_name, timeframe_minutes in self.config.TIMEFRAMES.items():
                        rates_data = self.mt5_connector.get_rates(symbol, timeframe_minutes, 100)
                        
                        if rates_data is not None and len(rates_data) > 0:
                            with self.data_lock:
                                cache_key = f"{symbol}_{timeframe_name}"
                                
                                self.price_cache[cache_key] = {
                                    "data": rates_data,
                                    "timestamp": time.time(),
                                    "symbol": symbol,
                                    "timeframe": timeframe_name
                                }
                                
                                self.last_update_times[f"price_{cache_key}"] = time.time()
                            
                            # Notify subscribers
                            self._notify_subscribers(symbol, f"price_{timeframe_name}", rates_data)
                    
                    time.sleep(self.update_intervals["price"])
                    
                except Exception as e:
                    self.logger.error(f"Error in price update worker for {symbol}: {e}")
                    time.sleep(10)  # Wait longer on error
                    
        except Exception as e:
            self.logger.error(f"Price update worker for {symbol} crashed: {e}")
    
    def get_symbol_data(self, symbol: str, timeframe: str = "M15") -> Optional[pd.DataFrame]:
        """Get cached price data for symbol and timeframe"""
        try:
            cache_key = f"{symbol}_{timeframe}"
            
            with self.data_lock:
                if cache_key in self.price_cache:
                    cache_entry = self.price_cache[cache_key]
                    
                    # Check if cache is still valid
                    cache_age = time.time() - cache_entry["timestamp"]
                    if cache_age < self.cache_duration["price"]:
                        return cache_entry["data"].copy()
            
            # Cache miss or expired - fetch fresh data
            timeframe_minutes = self.config.TIMEFRAMES.get(timeframe, 15)
            fresh_data = self.mt5_connector.get_rates(symbol, timeframe_minutes, 200)
            
            if fresh_data is not None:
                with self.data_lock:
                    self.price_cache[cache_key] = {
                        "data": fresh_data,
                        "timestamp": time.time(),
                        "symbol": symbol,
                        "timeframe": timeframe
                    }
                
                return fresh_data.copy()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting symbol data for {symbol} {timeframe}: {e}")
            return None
    
    def get_tick_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest tick data for symbol"""
        try:
            with self.data_lock:
                if symbol in self.tick_cache and self.tick_cache[symbol]:
                    # Return most recent tick
                    latest_tick = self.tick_cache[symbol][-1].copy()
                    
                    # Check if tick is recent
                    tick_age = time.time() - latest_tick.get("timestamp", 0)
                    if tick_age < self.cache_duration["tick"]:
                        return latest_tick
            
            # Cache miss or expired - fetch fresh tick
            fresh_tick = self.mt5_connector.get_tick_data(symbol)
            if fresh_tick:
                fresh_tick["timestamp"] = time.time()
                fresh_tick["symbol"] = symbol
                
                with self.data_lock:
                    if symbol not in self.tick_cache:
                        self.tick_cache[symbol] = []
                    self.tick_cache[symbol].append(fresh_tick)
                
                return fresh_tick
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting tick data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, timeframe: str, count: int = 1000, 
                          start_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """Get historical data with caching"""
        try:
            cache_key = f"hist_{symbol}_{timeframe}_{count}"
            
            # Check cache first
            with self.data_lock:
                if cache_key in self.historical_cache:
                    cache_entry = self.historical_cache[cache_key]
                    cache_age = time.time() - cache_entry["timestamp"]
                    
                    if cache_age < self.cache_duration["historical"]:
                        return cache_entry["data"].copy()
            
            # Fetch fresh historical data
            timeframe_minutes = self.config.TIMEFRAMES.get(timeframe, 15)
            historical_data = self.mt5_connector.get_rates(symbol, timeframe_minutes, count)
            
            if historical_data is not None:
                with self.data_lock:
                    self.historical_cache[cache_key] = {
                        "data": historical_data,
                        "timestamp": time.time(),
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "count": count
                    }
                
                # Backup historical data
                if self.backup_enabled:
                    self._backup_historical_data(symbol, timeframe, historical_data)
                
                return historical_data.copy()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return None
    
    def get_multiple_symbols_data(self, symbols: List[str], timeframe: str = "M15") -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols concurrently"""
        try:
            results = {}
            
            # Use thread pool for concurrent data retrieval
            future_to_symbol = {}
            
            for symbol in symbols:
                future = self.executor.submit(self.get_symbol_data, symbol, timeframe)
                future_to_symbol[future] = symbol
            
            # Collect results
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    data = future.result(timeout=10)  # 10 second timeout
                    if data is not None:
                        results[symbol] = data
                except Exception as e:
                    self.logger.error(f"Error getting data for {symbol}: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting multiple symbols data: {e}")
            return {}
    
    def update_all_data(self):
        """Update all cached data"""
        try:
            # Update tick data for all symbols
            for symbol in self.config.SYMBOLS:
                self.get_tick_data(symbol)
            
            # Update price data for primary timeframes
            primary_timeframes = [self.config.PRIMARY_TIMEFRAME, self.config.CONFIRMATION_TIMEFRAME]
            
            for symbol in self.config.SYMBOLS:
                for timeframe in primary_timeframes:
                    self.get_symbol_data(symbol, timeframe)
            
        except Exception as e:
            self.logger.error(f"Error updating all data: {e}")
    
    def subscribe_to_updates(self, subscriber_id: str, symbol: str, data_type: str, callback):
        """Subscribe to real-time data updates"""
        try:
            subscription_key = f"{symbol}_{data_type}"
            
            if subscription_key not in self.stream_subscribers:
                self.stream_subscribers[subscription_key] = {}
            
            self.stream_subscribers[subscription_key][subscriber_id] = callback
            
            self.logger.info(f"📡 Subscriber {subscriber_id} registered for {subscription_key}")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to updates: {e}")
    
    def unsubscribe_from_updates(self, subscriber_id: str, symbol: str = None, data_type: str = None):
        """Unsubscribe from data updates"""
        try:
            if symbol and data_type:
                subscription_key = f"{symbol}_{data_type}"
                if subscription_key in self.stream_subscribers:
                    self.stream_subscribers[subscription_key].pop(subscriber_id, None)
            else:
                # Remove subscriber from all subscriptions
                for subscription_key in self.stream_subscribers:
                    self.stream_subscribers[subscription_key].pop(subscriber_id, None)
            
            self.logger.info(f"📡 Subscriber {subscriber_id} unsubscribed")
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from updates: {e}")
    
    def _notify_subscribers(self, symbol: str, data_type: str, data: Any):
        """Notify subscribers of data updates"""
        try:
            subscription_key = f"{symbol}_{data_type}"
            
            if subscription_key in self.stream_subscribers:
                for subscriber_id, callback in self.stream_subscribers[subscription_key].items():
                    try:
                        callback(symbol, data_type, data)
                    except Exception as e:
                        self.logger.error(f"Error notifying subscriber {subscriber_id}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error notifying subscribers: {e}")
    
    def _backup_historical_data(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Backup historical data to file"""
        try:
            if not self.backup_enabled:
                return
            
            backup_file = os.path.join(
                self.backup_path, 
                f"{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            # Save to CSV
            data.to_csv(backup_file, index=True)
            
        except Exception as e:
            self.logger.error(f"Error backing up data: {e}")
    
    def restore_from_backup(self, symbol: str, timeframe: str, date: str) -> Optional[pd.DataFrame]:
        """Restore data from backup file"""
        try:
            backup_file = os.path.join(self.backup_path, f"{symbol}_{timeframe}_{date}.csv")
            
            if os.path.exists(backup_file):
                data = pd.read_csv(backup_file, index_col=0, parse_dates=True)
                self.logger.info(f"📂 Restored data from backup: {backup_file}")
                return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            return None
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Get data quality and availability report"""
        try:
            report = {
                "timestamp": datetime.now(),
                "symbols": {},
                "cache_status": {
                    "tick_cache_size": len(self.tick_cache),
                    "price_cache_size": len(self.price_cache),
                    "historical_cache_size": len(self.historical_cache)
                },
                "streaming_status": {
                    "active": self.streaming_active,
                    "active_threads": len(self.update_threads)
                },
                "overall_health": "good"
            }
            
            issues = []
            
            # Check each symbol
            for symbol in self.config.SYMBOLS:
                symbol_report = {
                    "tick_data": False,
                    "price_data": {},
                    "last_update": None,
                    "data_gaps": False,
                    "quality_score": 0.0
                }
                
                # Check tick data
                if symbol in self.tick_cache and self.tick_cache[symbol]:
                    latest_tick = self.tick_cache[symbol][-1]
                    tick_age = time.time() - latest_tick.get("timestamp", 0)
                    symbol_report["tick_data"] = tick_age < 60  # Less than 1 minute old
                    symbol_report["last_update"] = datetime.fromtimestamp(latest_tick.get("timestamp", 0))
                
                # Check price data for each timeframe
                for timeframe in ["M15", "H1", "D1"]:
                    cache_key = f"{symbol}_{timeframe}"
                    if cache_key in self.price_cache:
                        cache_entry = self.price_cache[cache_key]
                        cache_age = time.time() - cache_entry["timestamp"]
                        symbol_report["price_data"][timeframe] = {
                            "available": True,
                            "age_minutes": cache_age / 60,
                            "bars_count": len(cache_entry["data"]) if cache_entry["data"] is not None else 0
                        }
                    else:
                        symbol_report["price_data"][timeframe] = {"available": False}
                
                # Calculate quality score
                quality_score = 0.0
                if symbol_report["tick_data"]:
                    quality_score += 0.4
                
                available_timeframes = sum(1 for tf_data in symbol_report["price_data"].values() if tf_data["available"])
                quality_score += (available_timeframes / len(symbol_report["price_data"])) * 0.6
                
                symbol_report["quality_score"] = quality_score
                
                if quality_score < 0.7:
                    issues.append(f"Poor data quality for {symbol}")
                
                report["symbols"][symbol] = symbol_report
            
            # Overall health assessment
            avg_quality = np.mean([s["quality_score"] for s in report["symbols"].values()])
            
            if avg_quality > 0.8:
                report["overall_health"] = "excellent"
            elif avg_quality > 0.6:
                report["overall_health"] = "good"
            elif avg_quality > 0.4:
                report["overall_health"] = "fair"
            else:
                report["overall_health"] = "poor"
                
            report["issues"] = issues
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating data quality report: {e}")
            return {"overall_health": "unknown", "error": str(e)}
    
    def cleanup_cache(self, max_age_hours: int = 24):
        """Clean up old cache entries"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            with self.data_lock:
                # Clean tick cache
                for symbol in list(self.tick_cache.keys()):
                    if symbol in self.tick_cache:
                        # Remove old ticks
                        self.tick_cache[symbol] = [
                            tick for tick in self.tick_cache[symbol]
                            if current_time - tick.get("timestamp", 0) < max_age_seconds
                        ]
                        
                        # Remove empty entries
                        if not self.tick_cache[symbol]:
                            del self.tick_cache[symbol]
                
                # Clean price cache
                expired_keys = []
                for cache_key, cache_entry in self.price_cache.items():
                    if current_time - cache_entry["timestamp"] > max_age_seconds:
                        expired_keys.append(cache_key)
                
                for key in expired_keys:
                    del self.price_cache[key]
                
                # Clean historical cache
                expired_keys = []
                for cache_key, cache_entry in self.historical_cache.items():
                    if current_time - cache_entry["timestamp"] > max_age_seconds:
                        expired_keys.append(cache_key)
                
                for key in expired_keys:
                    del self.historical_cache[key]
            
            self.logger.info(f"🧹 Cache cleanup completed - removed entries older than {max_age_hours} hours")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")
    
    def export_data(self, symbol: str, timeframe: str, format: str = "csv") -> Optional[str]:
        """Export data to file"""
        try:
            data = self.get_symbol_data(symbol, timeframe)
            
            if data is None:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "csv":
                filename = f"{symbol}_{timeframe}_{timestamp}.csv"
                filepath = os.path.join(self.config.DATA_DIR, filename)
                data.to_csv(filepath, index=True)
                
            elif format.lower() == "json":
                filename = f"{symbol}_{timeframe}_{timestamp}.json"
                filepath = os.path.join(self.config.DATA_DIR, filename)
                data.to_json(filepath, orient="index", date_format="iso")
                
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return None
            
            self.logger.info(f"📤 Data exported to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return None
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self.data_lock:
                stats = {
                    "tick_cache": {
                        "symbols": len(self.tick_cache),
                        "total_ticks": sum(len(ticks) for ticks in self.tick_cache.values()),
                        "memory_usage_mb": self._estimate_cache_memory_usage(self.tick_cache)
                    },
                    "price_cache": {
                        "entries": len(self.price_cache),
                        "memory_usage_mb": self._estimate_cache_memory_usage(self.price_cache)
                    },
                    "historical_cache": {
                        "entries": len(self.historical_cache),
                        "memory_usage_mb": self._estimate_cache_memory_usage(self.historical_cache)
                    },
                    "last_updates": dict(self.last_update_times),
                    "active_subscriptions": len(self.stream_subscribers)
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting cache statistics: {e}")
            return {}
    
    def _estimate_cache_memory_usage(self, cache_dict: Dict) -> float:
        """Estimate memory usage of cache in MB"""
        try:
            # Rough estimation based on dictionary size
            import sys
            total_size = sys.getsizeof(cache_dict)
            
            for key, value in cache_dict.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(value)
                
                if isinstance(value, list):
                    total_size += sum(sys.getsizeof(item) for item in value)
                elif isinstance(value, dict):
                    total_size += sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in value.items())
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            return 0.0
    
    def force_refresh_symbol(self, symbol: str):
        """Force refresh all data for a symbol"""
        try:
            with self.data_lock:
                # Clear cached data for symbol
                if symbol in self.tick_cache:
                    del self.tick_cache[symbol]
                
                # Clear price cache entries for symbol
                keys_to_remove = [key for key in self.price_cache.keys() if key.startswith(f"{symbol}_")]
                for key in keys_to_remove:
                    del self.price_cache[key]
                
                # Clear historical cache entries for symbol
                keys_to_remove = [key for key in self.historical_cache.keys() if f"_{symbol}_" in key]
                for key in keys_to_remove:
                    del self.historical_cache[key]
            
            # Fetch fresh data
            self.get_tick_data(symbol)
            for timeframe in ["M15", "H1"]:
                self.get_symbol_data(symbol, timeframe)
            
            self.logger.info(f"🔄 Force refreshed data for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error force refreshing symbol {symbol}: {e}")
