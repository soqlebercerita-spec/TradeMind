
"""
Data management system for AuraTrade Bot
Handles real-time market data and historical analysis
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from core.mt5_connector import MT5Connector
from utils.logger import Logger, log_error

class DataManager:
    """Manages market data feeds and historical analysis"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Data storage
        self.live_data = {}
        self.historical_data = {}
        self.tick_data = {}
        
        # Data update thread
        self.data_thread = None
        self.update_running = False
        self.update_interval = 1  # seconds
        
        # Symbols to track
        self.active_symbols = []
        
        self.logger.info("Data Manager initialized")
    
    def start_data_updates(self, symbols: List[str]):
        """Start real-time data updates for symbols"""
        try:
            self.active_symbols = symbols
            
            if self.update_running:
                self.logger.warning("Data updates already running")
                return
            
            self.logger.info(f"Starting data updates for symbols: {symbols}")
            
            # Initialize data storage
            for symbol in symbols:
                self.live_data[symbol] = {
                    'bid': 0.0,
                    'ask': 0.0,
                    'spread': 0.0,
                    'last_update': None
                }
                self.tick_data[symbol] = []
                self.historical_data[symbol] = None
            
            # Load initial historical data
            self._load_historical_data()
            
            # Start update thread
            self.update_running = True
            self.data_thread = threading.Thread(target=self._data_update_loop, daemon=True)
            self.data_thread.start()
            
            self.logger.info("Data updates started successfully")
            
        except Exception as e:
            log_error("DataManager", "Failed to start data updates", e)
    
    def stop_data_updates(self):
        """Stop real-time data updates"""
        try:
            self.logger.info("Stopping data updates...")
            self.update_running = False
            
            if self.data_thread and self.data_thread.is_alive():
                self.data_thread.join(timeout=5)
            
            self.logger.info("Data updates stopped")
            
        except Exception as e:
            log_error("DataManager", "Error stopping data updates", e)
    
    def _data_update_loop(self):
        """Main data update loop"""
        self.logger.info("Data update loop started")
        
        while self.update_running:
            try:
                start_time = time.time()
                
                # Update live data for all symbols
                for symbol in self.active_symbols:
                    self._update_symbol_data(symbol)
                
                # Performance monitoring
                loop_time = time.time() - start_time
                
                # Sleep to maintain update interval
                sleep_time = max(0, self.update_interval - loop_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                log_error("DataManager", "Error in data update loop", e)
                time.sleep(1)
        
        self.logger.info("Data update loop stopped")
    
    def _update_symbol_data(self, symbol: str):
        """Update data for a single symbol"""
        try:
            # Get current tick
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return
            
            # Update live data
            bid = tick['bid']
            ask = tick['ask']
            spread = ask - bid
            
            self.live_data[symbol].update({
                'bid': bid,
                'ask': ask,
                'spread': spread,
                'last_update': datetime.now()
            })
            
            # Store tick data (keep last 1000 ticks)
            tick_record = {
                'timestamp': datetime.now(),
                'bid': bid,
                'ask': ask,
                'spread': spread
            }
            
            self.tick_data[symbol].append(tick_record)
            if len(self.tick_data[symbol]) > 1000:
                self.tick_data[symbol] = self.tick_data[symbol][-1000:]
            
        except Exception as e:
            log_error("DataManager", f"Error updating data for {symbol}", e)
    
    def _load_historical_data(self):
        """Load historical data for all symbols"""
        try:
            for symbol in self.active_symbols:
                # Get historical rates (last 500 bars)
                rates = self.mt5_connector.get_rates(symbol, 1, 0, 500)
                
                if rates is not None and len(rates) > 0:
                    self.historical_data[symbol] = rates
                    self.logger.info(f"Loaded {len(rates)} historical bars for {symbol}")
                else:
                    self.logger.warning(f"No historical data available for {symbol}")
                    
        except Exception as e:
            log_error("DataManager", "Error loading historical data", e)
    
    def get_live_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current live data for symbol"""
        return self.live_data.get(symbol)
    
    def get_historical_data(self, symbol: str, bars: int = None) -> Optional[pd.DataFrame]:
        """Get historical data for symbol"""
        try:
            data = self.historical_data.get(symbol)
            
            if data is None:
                # Try to fetch fresh data
                data = self.mt5_connector.get_rates(symbol, 1, 0, bars or 100)
                if data is not None:
                    self.historical_data[symbol] = data
            
            if data is not None and bars:
                return data.tail(bars)
            
            return data
            
        except Exception as e:
            log_error("DataManager", f"Error getting historical data for {symbol}", e)
            return None
    
    def get_tick_data(self, symbol: str, count: int = None) -> List[Dict[str, Any]]:
        """Get recent tick data for symbol"""
        try:
            ticks = self.tick_data.get(symbol, [])
            
            if count:
                return ticks[-count:]
            
            return ticks
            
        except Exception as e:
            log_error("DataManager", f"Error getting tick data for {symbol}", e)
            return []
    
    def calculate_spread_statistics(self, symbol: str, minutes: int = 60) -> Dict[str, float]:
        """Calculate spread statistics for the last N minutes"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_ticks = [
                tick for tick in self.tick_data.get(symbol, [])
                if tick['timestamp'] >= cutoff_time
            ]
            
            if not recent_ticks:
                return {}
            
            spreads = [tick['spread'] for tick in recent_ticks]
            
            return {
                'avg_spread': sum(spreads) / len(spreads),
                'min_spread': min(spreads),
                'max_spread': max(spreads),
                'current_spread': spreads[-1] if spreads else 0.0,
                'spread_volatility': pd.Series(spreads).std() if len(spreads) > 1 else 0.0,
                'sample_count': len(spreads)
            }
            
        except Exception as e:
            log_error("DataManager", f"Error calculating spread statistics for {symbol}", e)
            return {}
    
    def get_market_hours_info(self) -> Dict[str, Any]:
        """Get market trading hours information"""
        try:
            current_time = datetime.now()
            
            # Simplified market hours (UTC)
            market_sessions = {
                'sydney': {'start': 21, 'end': 6},
                'tokyo': {'start': 0, 'end': 9},
                'london': {'start': 7, 'end': 16},
                'new_york': {'start': 12, 'end': 21}
            }
            
            current_hour = current_time.hour
            active_sessions = []
            
            for session, hours in market_sessions.items():
                if hours['start'] <= current_hour < hours['end']:
                    active_sessions.append(session)
            
            # Check if it's weekend
            is_weekend = current_time.weekday() >= 5
            
            return {
                'current_time': current_time,
                'active_sessions': active_sessions,
                'is_weekend': is_weekend,
                'market_open': len(active_sessions) > 0 and not is_weekend,
                'liquidity_level': 'HIGH' if len(active_sessions) >= 2 else 'MEDIUM' if active_sessions else 'LOW'
            }
            
        except Exception as e:
            log_error("DataManager", "Error getting market hours info", e)
            return {}
    
    def get_symbol_activity(self, symbol: str, minutes: int = 30) -> Dict[str, Any]:
        """Get symbol trading activity for the last N minutes"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_ticks = [
                tick for tick in self.tick_data.get(symbol, [])
                if tick['timestamp'] >= cutoff_time
            ]
            
            if not recent_ticks:
                return {}
            
            # Calculate price movements
            prices = [(tick['bid'] + tick['ask']) / 2 for tick in recent_ticks]
            
            if len(prices) < 2:
                return {}
            
            price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            
            return {
                'tick_count': len(recent_ticks),
                'price_range': max(prices) - min(prices),
                'avg_price': sum(prices) / len(prices),
                'volatility': pd.Series(price_changes).std() if len(price_changes) > 1 else 0.0,
                'trend': 'UP' if prices[-1] > prices[0] else 'DOWN' if prices[-1] < prices[0] else 'FLAT',
                'activity_level': 'HIGH' if len(recent_ticks) > minutes * 10 else 'MEDIUM' if len(recent_ticks) > minutes * 5 else 'LOW'
            }
            
        except Exception as e:
            log_error("DataManager", f"Error getting symbol activity for {symbol}", e)
            return {}
    
    def export_data(self, symbol: str, format_type: str = 'csv') -> Optional[str]:
        """Export symbol data to file"""
        try:
            historical_data = self.get_historical_data(symbol)
            
            if historical_data is None or len(historical_data) == 0:
                self.logger.warning(f"No data to export for {symbol}")
                return None
            
            filename = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
            
            if format_type.lower() == 'csv':
                historical_data.to_csv(filename, index=False)
            elif format_type.lower() == 'json':
                historical_data.to_json(filename, orient='records', date_format='iso')
            else:
                self.logger.error(f"Unsupported export format: {format_type}")
                return None
            
            self.logger.info(f"Data exported to {filename}")
            return filename
            
        except Exception as e:
            log_error("DataManager", f"Error exporting data for {symbol}", e)
            return None
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get current data manager status"""
        try:
            status = {
                'update_running': self.update_running,
                'active_symbols': self.active_symbols,
                'data_counts': {},
                'last_updates': {},
                'connection_status': self.mt5_connector.check_connection()
            }
            
            for symbol in self.active_symbols:
                # Data counts
                status['data_counts'][symbol] = {
                    'historical_bars': len(self.historical_data.get(symbol, [])),
                    'tick_count': len(self.tick_data.get(symbol, []))
                }
                
                # Last update times
                live_data = self.live_data.get(symbol, {})
                status['last_updates'][symbol] = live_data.get('last_update')
            
            return status
            
        except Exception as e:
            log_error("DataManager", "Error getting data status", e)
            return {}
    
    def refresh_symbol_data(self, symbol: str):
        """Manually refresh data for a symbol"""
        try:
            # Reload historical data
            rates = self.mt5_connector.get_rates(symbol, 1, 0, 500)
            if rates is not None:
                self.historical_data[symbol] = rates
                self.logger.info(f"Refreshed historical data for {symbol}: {len(rates)} bars")
            
            # Update live data
            self._update_symbol_data(symbol)
            
        except Exception as e:
            log_error("DataManager", f"Error refreshing data for {symbol}", e)
