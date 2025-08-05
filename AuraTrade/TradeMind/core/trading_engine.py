"""
Main trading engine that orchestrates all trading activities
Manages strategy execution, signal processing, and trade coordination
"""

import threading
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from config.config import Config
from config.settings import Settings
from core.mt5_connector import MT5Connector
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.position_sizing import PositionSizing
from core.ml_engine import MLEngine
from data.data_manager import DataManager
from strategies.hft_strategy import HFTStrategy
from strategies.scalping_strategy import ScalpingStrategy
from strategies.arbitrage_strategy import ArbitrageStrategy
from strategies.pattern_strategy import PatternStrategy
from analysis.technical_analysis import TechnicalAnalysis
from analysis.market_conditions import MarketConditions
from analysis.sentiment_analyzer import SentimentAnalyzer
from utils.logger import Logger
from utils.notifier import TelegramNotifier

class TradingEngine:
    """Main trading engine that coordinates all trading activities"""
    
    def __init__(self, mt5_connector: MT5Connector, data_manager: DataManager,
                 order_manager: OrderManager, risk_manager: RiskManager,
                 position_sizing: PositionSizing, ml_engine: MLEngine,
                 notifier: TelegramNotifier):
        
        self.logger = Logger().get_logger()
        self.config = Config()
        self.settings = Settings()
        
        # Core components
        self.mt5_connector = mt5_connector
        self.data_manager = data_manager
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_sizing = position_sizing
        self.ml_engine = ml_engine
        self.notifier = notifier
        
        # Analysis modules
        self.technical_analysis = TechnicalAnalysis()
        self.market_conditions = MarketConditions()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Trading strategies
        self.strategies = {
            'hft': HFTStrategy(self.config, self.settings),
            'scalping': ScalpingStrategy(self.config, self.settings),
            'arbitrage': ArbitrageStrategy(self.config, self.settings),
            'pattern': PatternStrategy(self.config, self.settings)
        }
        
        # Control flags
        self.running = False
        self.paused = False
        self.emergency_stop = False
        
        # Threading
        self.main_thread = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Performance tracking
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_trade_time = None
        
        # Signal aggregation
        self.signals_cache = {}
        self.signal_weights = {
            'technical': 0.4,
            'pattern': 0.3,
            'sentiment': 0.2,
            'ml': 0.1
        }
        
    def start(self):
        """Start the trading engine"""
        try:
            if self.running:
                self.logger.warning("Trading engine is already running")
                return
            
            self.logger.info("Starting AuraTrade trading engine...")
            self.running = True
            self.emergency_stop = False
            
            # Reset daily counters if new day
            self._reset_daily_counters()
            
            # Start main trading loop
            self.main_thread = threading.Thread(target=self._main_trading_loop, daemon=True)
            self.main_thread.start()
            
            self.logger.info("Trading engine started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start trading engine: {e}")
            self.running = False
    
    def stop(self):
        """Stop the trading engine"""
        try:
            self.logger.info("Stopping trading engine...")
            self.running = False
            
            # Wait for main thread to finish
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=10)
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            self.logger.info("Trading engine stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")
    
    def pause(self):
        """Pause trading operations"""
        self.paused = True
        self.logger.info("Trading engine paused")
    
    def resume(self):
        """Resume trading operations"""
        self.paused = False
        self.logger.info("Trading engine resumed")
    
    def emergency_stop_all(self):
        """Emergency stop - close all positions and stop trading"""
        try:
            self.logger.warning("EMERGENCY STOP ACTIVATED")
            self.emergency_stop = True
            self.running = False
            
            # Close all positions immediately
            self.order_manager.emergency_stop()
            
            # Send emergency notification
            if self.notifier:
                self.notifier.send_message(
                    "🚨 EMERGENCY STOP ACTIVATED\n"
                    "All positions closed and trading stopped."
                )
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
    
    def _main_trading_loop(self):
        """Main trading loop that runs continuously"""
        self.logger.info("Main trading loop started")
        
        while self.running and not self.emergency_stop:
            try:
                # Check if paused
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Check connection
                if not self.mt5_connector.is_connected():
                    self.logger.warning("MT5 connection lost, attempting reconnection...")
                    if not self.mt5_connector.reconnect():
                        time.sleep(10)
                        continue
                
                # Check daily limits
                if self._check_daily_limits():
                    self.logger.info("Daily limits reached, stopping trading for today")
                    break
                
                # Check risk limits
                if self.risk_manager.check_emergency_stop():
                    self.emergency_stop_all()
                    break
                
                # Update market data
                self._update_market_data()
                
                # Process trading signals
                self._process_trading_signals()
                
                # Monitor existing positions
                self._monitor_positions()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Brief sleep to prevent excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in main trading loop: {e}")
                time.sleep(1)
        
        self.logger.info("Main trading loop ended")
    
    def _update_market_data(self):
        """Update market data for all symbols"""
        try:
            # Get active symbols from all strategies
            active_symbols = set()
            for strategy_name in self.settings.get_active_strategies():
                symbols = self.settings.get_strategy_symbols(strategy_name)
                active_symbols.update(symbols)
            
            # Update data for each symbol
            for symbol in active_symbols:
                if not self.config.is_trading_hours(symbol):
                    continue
                
                # Update data in background
                self.executor.submit(self.data_manager.update_symbol_data, symbol)
                
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
    
    def _process_trading_signals(self):
        """Process trading signals from all strategies and sources"""
        try:
            # Get active symbols and strategies
            active_strategies = self.settings.get_active_strategies()
            
            for strategy_name in active_strategies:
                strategy = self.strategies.get(strategy_name)
                if not strategy:
                    continue
                
                symbols = self.settings.get_strategy_symbols(strategy_name)
                
                for symbol in symbols:
                    # Skip if market closed or spread too wide
                    if not self._is_symbol_tradeable(symbol):
                        continue
                    
                    # Generate signals in parallel
                    self.executor.submit(self._generate_symbol_signals, symbol, strategy_name)
                    
        except Exception as e:
            self.logger.error(f"Error processing trading signals: {e}")
    
    def _generate_symbol_signals(self, symbol: str, strategy_name: str):
        """Generate trading signals for specific symbol and strategy"""
        try:
            strategy = self.strategies[strategy_name]
            timeframes = self.settings.get_strategy_timeframes(strategy_name)
            
            # Get market data
            market_data = {}
            for tf in timeframes:
                data = self.data_manager.get_rates(symbol, tf)
                if data is not None and len(data) > 0:
                    market_data[tf] = data
            
            if not market_data:
                return
            
            # Generate technical analysis signals
            technical_signals = self._get_technical_signals(symbol, market_data)
            
            # Generate pattern signals
            pattern_signals = self._get_pattern_signals(symbol, market_data)
            
            # Generate sentiment signals
            sentiment_signals = self._get_sentiment_signals(symbol)
            
            # Generate ML signals if enabled
            ml_signals = {}
            if self.config.ML_SETTINGS['enabled']:
                ml_signals = self._get_ml_signals(symbol, market_data)
            
            # Aggregate all signals
            aggregated_signal = self._aggregate_signals(
                technical_signals, pattern_signals, sentiment_signals, ml_signals
            )
            
            # Check strategy-specific conditions
            strategy_signal = strategy.generate_signal(symbol, market_data, aggregated_signal)
            
            # Execute trade if signal is strong enough
            if strategy_signal and abs(strategy_signal['strength']) >= strategy.min_signal_strength:
                self._execute_trading_signal(symbol, strategy_name, strategy_signal)
                
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol} ({strategy_name}): {e}")
    
    def _get_technical_signals(self, symbol: str, market_data: Dict) -> Dict:
        """Get technical analysis signals"""
        try:
            signals = {}
            
            for timeframe, data in market_data.items():
                if len(data) < 50:  # Need sufficient data
                    continue
                
                # Calculate technical indicators
                indicators = self.technical_analysis.calculate_all_indicators(data)
                
                # Generate signals from indicators
                tf_signals = self.technical_analysis.generate_signals(data, indicators)
                signals[timeframe] = tf_signals
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error getting technical signals for {symbol}: {e}")
            return {}
    
    def _get_pattern_signals(self, symbol: str, market_data: Dict) -> Dict:
        """Get pattern recognition signals"""
        try:
            pattern_strategy = self.strategies.get('pattern')
            if not pattern_strategy:
                return {}
            
            signals = {}
            for timeframe, data in market_data.items():
                if len(data) < 20:
                    continue
                
                tf_signals = pattern_strategy.analyze_patterns(data)
                signals[timeframe] = tf_signals
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error getting pattern signals for {symbol}: {e}")
            return {}
    
    def _get_sentiment_signals(self, symbol: str) -> Dict:
        """Get sentiment analysis signals"""
        try:
            return self.sentiment_analyzer.get_symbol_sentiment(symbol)
        except Exception as e:
            self.logger.error(f"Error getting sentiment signals for {symbol}: {e}")
            return {}
    
    def _get_ml_signals(self, symbol: str, market_data: Dict) -> Dict:
        """Get machine learning signals"""
        try:
            if not self.config.ML_SETTINGS['enabled']:
                return {}
            
            # Use primary timeframe data for ML prediction
            primary_tf = list(market_data.keys())[0]
            data = market_data[primary_tf]
            
            return self.ml_engine.predict_direction(symbol, data)
            
        except Exception as e:
            self.logger.error(f"Error getting ML signals for {symbol}: {e}")
            return {}
    
    def _aggregate_signals(self, technical: Dict, pattern: Dict, 
                          sentiment: Dict, ml: Dict) -> Dict:
        """Aggregate signals from different sources with weights"""
        try:
            aggregated = {
                'direction': 0,  # -1 (sell), 0 (neutral), 1 (buy)
                'strength': 0,   # 0-1 confidence
                'components': {
                    'technical': technical,
                    'pattern': pattern,
                    'sentiment': sentiment,
                    'ml': ml
                }
            }
            
            total_weight = 0
            weighted_direction = 0
            weighted_strength = 0
            
            # Technical analysis
            if technical:
                tech_dir = self._extract_direction(technical)
                tech_strength = self._extract_strength(technical)
                weight = self.signal_weights['technical']
                
                weighted_direction += tech_dir * weight
                weighted_strength += tech_strength * weight
                total_weight += weight
            
            # Pattern analysis
            if pattern:
                pattern_dir = self._extract_direction(pattern)
                pattern_strength = self._extract_strength(pattern)
                weight = self.signal_weights['pattern']
                
                weighted_direction += pattern_dir * weight
                weighted_strength += pattern_strength * weight
                total_weight += weight
            
            # Sentiment analysis
            if sentiment:
                sent_dir = sentiment.get('direction', 0)
                sent_strength = sentiment.get('strength', 0)
                weight = self.signal_weights['sentiment']
                
                weighted_direction += sent_dir * weight
                weighted_strength += sent_strength * weight
                total_weight += weight
            
            # ML analysis
            if ml:
                ml_dir = ml.get('direction', 0)
                ml_strength = ml.get('confidence', 0)
                weight = self.signal_weights['ml']
                
                weighted_direction += ml_dir * weight
                weighted_strength += ml_strength * weight
                total_weight += weight
            
            # Normalize by total weight
            if total_weight > 0:
                aggregated['direction'] = weighted_direction / total_weight
                aggregated['strength'] = weighted_strength / total_weight
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Error aggregating signals: {e}")
            return {'direction': 0, 'strength': 0, 'components': {}}
    
    def _extract_direction(self, signals: Dict) -> float:
        """Extract overall direction from signal dictionary"""
        try:
            if isinstance(signals, dict):
                # If signals have timeframes
                if any(isinstance(v, dict) for v in signals.values()):
                    directions = []
                    for tf_signals in signals.values():
                        if isinstance(tf_signals, dict) and 'direction' in tf_signals:
                            directions.append(tf_signals['direction'])
                    return sum(directions) / len(directions) if directions else 0
                
                # Direct signal format
                return signals.get('direction', 0)
            
            return 0
            
        except Exception:
            return 0
    
    def _extract_strength(self, signals: Dict) -> float:
        """Extract overall strength from signal dictionary"""
        try:
            if isinstance(signals, dict):
                # If signals have timeframes
                if any(isinstance(v, dict) for v in signals.values()):
                    strengths = []
                    for tf_signals in signals.values():
                        if isinstance(tf_signals, dict) and 'strength' in tf_signals:
                            strengths.append(tf_signals['strength'])
                    return sum(strengths) / len(strengths) if strengths else 0
                
                # Direct signal format
                return signals.get('strength', 0)
            
            return 0
            
        except Exception:
            return 0
    
    def _execute_trading_signal(self, symbol: str, strategy_name: str, signal: Dict):
        """Execute a trading signal"""
        try:
            # Check if we can trade this symbol
            if not self._can_trade_symbol(symbol, strategy_name):
                return
            
            # Determine trade direction
            if signal['strength'] > 0:
                direction = 1 if signal['direction'] > 0 else -1
            else:
                return
            
            # Calculate position size
            risk_amount = self.risk_manager.calculate_risk_amount(symbol)
            position_size = self.position_sizing.calculate_position_size(
                symbol, risk_amount, signal.get('entry_price', 0),
                signal.get('stop_loss', 0)
            )
            
            if position_size <= 0:
                return
            
            # Create trade request
            trade_request = {
                'symbol': symbol,
                'direction': direction,
                'volume': position_size,
                'strategy': strategy_name,
                'signal_strength': signal['strength'],
                'entry_reason': signal.get('reason', 'Signal'),
                'stop_loss': signal.get('stop_loss', 0),
                'take_profit': signal.get('take_profit', 0)
            }
            
            # Execute trade
            result = self.order_manager.place_market_order(trade_request)
            
            if result:
                self.trades_today += 1
                self.last_trade_time = datetime.now()
                
                self.logger.info(f"Trade executed: {symbol} {direction} {position_size} lots ({strategy_name})")
                
                # Send notification
                if self.notifier:
                    self.notifier.send_trade_notification(trade_request, result)
            
        except Exception as e:
            self.logger.error(f"Error executing trading signal for {symbol}: {e}")
    
    def _monitor_positions(self):
        """Monitor existing positions for management"""
        try:
            positions = self.mt5_connector.get_positions()
            
            for position in positions:
                # Check for trailing stops
                if self.settings.risk.trailing_stop:
                    self._update_trailing_stop(position)
                
                # Check for time-based exits
                self._check_time_based_exit(position)
                
                # Check for strategy-specific position management
                self._strategy_position_management(position)
                
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")
    
    def _update_trailing_stop(self, position: Dict):
        """Update trailing stop for position"""
        try:
            symbol = position['symbol']
            current_price = self.mt5_connector.get_current_price(symbol)
            
            if not current_price:
                return
            
            bid, ask = current_price
            
            # Calculate new trailing stop
            new_sl = self.risk_manager.calculate_trailing_stop(
                position, bid, ask, self.settings.risk.trailing_distance
            )
            
            if new_sl and new_sl != position['sl']:
                # Update stop loss
                self.mt5_connector.modify_position(position['ticket'], sl=new_sl)
                
        except Exception as e:
            self.logger.error(f"Error updating trailing stop for position {position.get('ticket', 0)}: {e}")
    
    def _check_time_based_exit(self, position: Dict):
        """Check if position should be closed based on time"""
        try:
            # Get position age
            open_time = datetime.fromtimestamp(position['time'])
            age_hours = (datetime.now() - open_time).total_seconds() / 3600
            
            # Close old positions (24 hours for non-swing strategies)
            if age_hours > 24:
                comment = position.get('comment', '')
                if 'swing' not in comment.lower():
                    self.order_manager.close_position(position['ticket'], "Time-based exit")
                    
        except Exception as e:
            self.logger.error(f"Error checking time-based exit for position {position.get('ticket', 0)}: {e}")
    
    def _strategy_position_management(self, position: Dict):
        """Strategy-specific position management"""
        try:
            comment = position.get('comment', '')
            
            # Extract strategy from comment
            strategy_name = None
            for name in self.strategies.keys():
                if name in comment.lower():
                    strategy_name = name
                    break
            
            if strategy_name and strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]
                strategy.manage_position(position, self.mt5_connector, self.order_manager)
                
        except Exception as e:
            self.logger.error(f"Error in strategy position management: {e}")
    
    def _update_performance_metrics(self):
        """Update performance tracking metrics"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return
            
            # Update daily P&L
            if hasattr(self, 'starting_balance'):
                self.daily_pnl = account_info['equity'] - self.starting_balance
            else:
                self.starting_balance = account_info['balance']
                self.daily_pnl = 0
            
            # Check consecutive losses
            recent_trades = self._get_recent_trades()
            self.consecutive_losses = self._count_consecutive_losses(recent_trades)
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def _is_symbol_tradeable(self, symbol: str) -> bool:
        """Check if symbol is tradeable right now"""
        try:
            # Check market hours
            if not self.config.is_trading_hours(symbol):
                return False
            
            # Check spread
            spread = self.mt5_connector.get_spread(symbol)
            max_spread = self.config.get_max_spread(symbol)
            
            if spread is None or spread > max_spread:
                return False
            
            # Check if market is open for trading
            if not self.mt5_connector.is_market_open(symbol):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking if {symbol} is tradeable: {e}")
            return False
    
    def _can_trade_symbol(self, symbol: str, strategy_name: str) -> bool:
        """Check if we can open new position for symbol"""
        try:
            # Check existing positions
            positions = self.mt5_connector.get_positions()
            symbol_positions = [p for p in positions if p['symbol'] == symbol]
            
            # Check strategy position limits
            strategy_settings = self.settings.strategies.get(strategy_name)
            if strategy_settings and len(symbol_positions) >= strategy_settings.max_positions:
                return False
            
            # Check risk limits
            if not self.risk_manager.can_open_position(symbol):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking if can trade {symbol}: {e}")
            return False
    
    def _reset_daily_counters(self):
        """Reset daily counters if new trading day"""
        try:
            now = datetime.now()
            if not hasattr(self, 'last_reset_date') or self.last_reset_date.date() != now.date():
                self.trades_today = 0
                self.daily_pnl = 0.0
                self.consecutive_losses = 0
                self.last_reset_date = now
                
                # Get starting balance for the day
                account_info = self.mt5_connector.get_account_info()
                if account_info:
                    self.starting_balance = account_info['balance']
                    
                self.logger.info("Daily counters reset for new trading day")
                
        except Exception as e:
            self.logger.error(f"Error resetting daily counters: {e}")
    
    def _check_daily_limits(self) -> bool:
        """Check if daily trading limits are reached"""
        try:
            # Check profit target
            if self.daily_pnl >= self.settings.performance_targets['daily_profit_target']:
                self.logger.info(f"Daily profit target reached: ${self.daily_pnl:.2f}")
                return True
            
            # Check loss limit
            if self.daily_pnl <= self.settings.performance_targets['daily_loss_limit']:
                self.logger.warning(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
                return True
            
            # Check consecutive losses
            if self.consecutive_losses >= self.settings.performance_targets['max_consecutive_losses']:
                self.logger.warning(f"Maximum consecutive losses reached: {self.consecutive_losses}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking daily limits: {e}")
            return False
    
    def _get_recent_trades(self) -> List[Dict]:
        """Get recent trade history"""
        try:
            # This would typically query trade history from MT5
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            self.logger.error(f"Error getting recent trades: {e}")
            return []
    
    def _count_consecutive_losses(self, trades: List[Dict]) -> int:
        """Count consecutive losing trades"""
        try:
            if not trades:
                return 0
            
            consecutive = 0
            for trade in reversed(trades):  # Start from most recent
                if trade.get('profit', 0) < 0:
                    consecutive += 1
                else:
                    break
            
            return consecutive
            
        except Exception as e:
            self.logger.error(f"Error counting consecutive losses: {e}")
            return 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            'running': self.running,
            'paused': self.paused,
            'emergency_stop': self.emergency_stop,
            'trades_today': self.trades_today,
            'daily_pnl': self.daily_pnl,
            'consecutive_losses': self.consecutive_losses,
            'last_trade_time': self.last_trade_time,
            'active_strategies': self.settings.get_active_strategies()
        }
