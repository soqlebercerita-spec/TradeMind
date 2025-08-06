
"""
High-performance trading engine for AuraTrade Bot
Manages multiple strategies and executes trades with risk management
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

from core.mt5_connector import MT5Connector
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.position_sizing import PositionSizing
from data.data_manager import DataManager
from utils.logger import Logger, log_trade, log_system
from utils.notifier import TelegramNotifier

class TradingEngine:
    """High-performance trading engine with multiple strategies"""
    
    def __init__(self, mt5_connector: MT5Connector, order_manager: OrderManager,
                 risk_manager: RiskManager, position_sizing: PositionSizing,
                 data_manager: DataManager, ml_engine: Any, notifier: TelegramNotifier,
                 strategies: Dict[str, Any], technical_analysis: Any):
        
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.order_manager = order_manager  
        self.risk_manager = risk_manager
        self.position_sizing = position_sizing
        self.data_manager = data_manager
        self.ml_engine = ml_engine
        self.notifier = notifier
        self.strategies = strategies
        self.technical_analysis = technical_analysis
        
        # Engine state
        self.running = False
        self.engine_thread = None
        
        # Trading metrics
        self.stats = {
            'trades_today': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'daily_pnl': 0.0,
            'total_profit': 0.0,
            'max_drawdown': 0.0,
            'active_positions': 0,
            'last_trade_time': None
        }
        
        # Active symbols
        self.active_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
        
        # Trading session
        self.session_start = datetime.now()
        
        self.logger.info("Trading engine initialized with multiple strategies")
    
    def start(self):
        """Start the trading engine"""
        try:
            if self.running:
                self.logger.warning("Trading engine is already running")
                return
            
            self.logger.info("Starting high-performance trading engine...")
            
            # Verify MT5 connection
            if not self.mt5_connector.check_connection():
                if not self.mt5_connector.reconnect():
                    raise Exception("Cannot start engine - MT5 not connected")
            
            # Reset daily stats
            self._reset_daily_stats()
            
            # Start engine thread
            self.running = True
            self.engine_thread = threading.Thread(target=self._engine_loop, daemon=True)
            self.engine_thread.start()
            
            # Send notification
            if self.notifier and self.notifier.enabled:
                self.notifier.send_trade_signal(
                    "ENGINE_START",
                    "SYSTEM",
                    0.0,
                    0.0,
                    "AuraTrade Engine Started - Target: 85%+ Win Rate"
                )
            
            log_system("Trading engine started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start trading engine: {e}")
            raise
    
    def stop(self):
        """Stop the trading engine"""
        try:
            self.logger.info("Stopping trading engine...")
            self.running = False
            
            # Wait for engine thread to finish
            if self.engine_thread and self.engine_thread.is_alive():
                self.engine_thread.join(timeout=5)
            
            # Close all positions if requested
            self._emergency_close_all()
            
            # Final statistics
            self._update_statistics()
            final_stats = self._get_session_summary()
            
            # Send notification
            if self.notifier and self.notifier.enabled:
                self.notifier.send_trade_signal(
                    "ENGINE_STOP",
                    "SYSTEM", 
                    0.0,
                    self.stats['daily_pnl'],
                    f"Engine Stopped\n{final_stats}"
                )
            
            log_system("Trading engine stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")
    
    def _engine_loop(self):
        """Main trading engine loop"""
        self.logger.info("Trading engine loop started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Check MT5 connection
                if not self.mt5_connector.check_connection():
                    self.logger.warning("MT5 connection lost - attempting reconnect")
                    if not self.mt5_connector.reconnect():
                        self.logger.error("Failed to reconnect to MT5")
                        time.sleep(5)
                        continue
                
                # Update statistics
                self._update_statistics()
                
                # Check risk limits
                if not self._check_risk_limits():
                    self.logger.warning("Risk limits exceeded - pausing trading")
                    time.sleep(60)
                    continue
                
                # Process each symbol
                for symbol in self.active_symbols:
                    if not self.running:
                        break
                    
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")
                
                # Update positions
                self._update_positions()
                
                # Performance monitoring
                loop_time = time.time() - start_time
                if loop_time > 1.0:
                    self.logger.warning(f"Engine loop took {loop_time:.2f}s - optimization needed")
                
                # Sleep to maintain performance
                time.sleep(max(0.1, 0.5 - loop_time))
                
            except Exception as e:
                self.logger.error(f"Critical error in engine loop: {e}")
                time.sleep(1)
        
        self.logger.info("Trading engine loop stopped")
    
    def _process_symbol(self, symbol: str):
        """Process trading signals for a symbol"""
        try:
            # Get current market data
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return
            
            # Get historical data for analysis
            rates = self.mt5_connector.get_rates(symbol, 1, 0, 100)
            if rates is None or len(rates) < 50:
                return
            
            # Run technical analysis
            signals = self._analyze_symbol(symbol, rates, tick)
            
            # Process signals from all strategies
            for strategy_name, strategy in self.strategies.items():
                try:
                    if hasattr(strategy, 'analyze'):
                        strategy_signal = strategy.analyze(symbol, rates, tick)
                        if strategy_signal and strategy_signal.get('action'):
                            self._execute_strategy_signal(symbol, strategy_signal, strategy_name)
                except Exception as e:
                    self.logger.error(f"Error in {strategy_name} for {symbol}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {e}")
    
    def _analyze_symbol(self, symbol: str, rates: pd.DataFrame, tick: Dict) -> Dict:
        """Analyze symbol using technical indicators"""
        try:
            if not hasattr(self.technical_analysis, 'analyze_trends'):
                return {}
            
            # Get technical analysis
            analysis = self.technical_analysis.analyze_trends(rates)
            
            # Combine with current tick
            signals = {
                'symbol': symbol,
                'current_price': tick['bid'],
                'trend': analysis.get('trend', 'NEUTRAL'),
                'rsi': analysis.get('rsi', 50),
                'macd': analysis.get('macd', 0),
                'bb_position': analysis.get('bollinger_position', 'MIDDLE'),
                'volume_trend': analysis.get('volume_trend', 'NORMAL'),
                'timestamp': datetime.now()
            }
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {symbol}: {e}")
            return {}
    
    def _execute_strategy_signal(self, symbol: str, signal: Dict, strategy_name: str):
        """Execute trading signal from strategy"""
        try:
            action = signal.get('action')
            confidence = signal.get('confidence', 0.5)
            
            # Minimum confidence threshold
            if confidence < 0.6:
                return
            
            # Check if we can trade this symbol
            if not self._can_trade_symbol(symbol):
                return
            
            # Calculate position size
            risk_amount = self.position_sizing.calculate_position_size(
                symbol, signal.get('stop_loss_pips', 20)
            )
            
            if risk_amount <= 0:
                return
            
            # Prepare order parameters
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return
            
            if action.upper() == 'BUY':
                price = tick['ask']
                sl_pips = signal.get('stop_loss_pips', 20)
                tp_pips = signal.get('take_profit_pips', 40)
            elif action.upper() == 'SELL':
                price = tick['bid']
                sl_pips = signal.get('stop_loss_pips', 20)
                tp_pips = signal.get('take_profit_pips', 40)
            else:
                return
            
            # Execute order
            result = self.order_manager.place_market_order(
                symbol=symbol,
                action=action.lower(),
                volume=risk_amount,
                sl_pips=sl_pips,
                tp_pips=tp_pips,
                comment=f"{strategy_name}_Auto"
            )
            
            if result and result.get('retcode') == 10009:
                self.stats['trades_today'] += 1
                self.stats['last_trade_time'] = datetime.now()
                
                # Log successful trade
                log_trade(action, symbol, risk_amount, price)
                
                # Send notification
                if self.notifier and self.notifier.enabled:
                    self.notifier.send_trade_signal(
                        action.upper(),
                        symbol,
                        risk_amount,
                        price,
                        f"{strategy_name} Signal | Confidence: {confidence:.1%}"
                    )
                
                self.logger.info(f"Trade executed: {action.upper()} {symbol} | {strategy_name}")
            
        except Exception as e:
            self.logger.error(f"Error executing signal for {symbol}: {e}")
    
    def _can_trade_symbol(self, symbol: str) -> bool:
        """Check if we can trade a symbol"""
        try:
            # Check existing positions
            positions = self.mt5_connector.get_positions()
            symbol_positions = [p for p in positions if p['symbol'] == symbol]
            
            # Limit positions per symbol
            if len(symbol_positions) >= 2:
                return False
            
            # Check daily trade limit
            if self.stats['trades_today'] >= 50:
                return False
            
            # Check risk limits
            account_info = self.mt5_connector.get_account_info()
            if account_info.get('margin_level', 1000) < 200:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking trade eligibility for {symbol}: {e}")
            return False
    
    def _update_positions(self):
        """Update and manage existing positions"""
        try:
            positions = self.mt5_connector.get_positions()
            self.stats['active_positions'] = len(positions)
            
            for position in positions:
                # Check for trailing stop
                self._check_trailing_stop(position)
                
                # Check for time-based exits
                self._check_time_exit(position)
                
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def _check_trailing_stop(self, position: Dict):
        """Implement trailing stop logic"""
        try:
            symbol = position['symbol']
            ticket = position['ticket']
            profit = position['profit']
            
            # Only trail profitable positions
            if profit <= 0:
                return
            
            # Get current price
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return
            
            # Implement trailing stop (example: 50% of profit)
            current_price = tick['bid'] if position['type'] == 0 else tick['ask']
            entry_price = position['price_open']
            
            if position['type'] == 0:  # Buy position
                trail_distance = (current_price - entry_price) * 0.5
                new_sl = entry_price + trail_distance
                
                # Only move SL up
                if new_sl > entry_price:
                    self.mt5_connector.modify_position(ticket, sl=new_sl)
                    self.logger.info(f"Trailing stop updated for #{ticket}: {new_sl:.5f}")
            
        except Exception as e:
            self.logger.error(f"Error in trailing stop: {e}")
    
    def _check_time_exit(self, position: Dict):
        """Check for time-based position exits"""
        try:
            # Close positions after 4 hours
            position_time = datetime.fromtimestamp(position['time'])
            if datetime.now() - position_time > timedelta(hours=4):
                result = self.mt5_connector.close_position(position['ticket'])
                if result.get('retcode') == 10009:
                    self.logger.info(f"Position #{position['ticket']} closed due to time limit")
        
        except Exception as e:
            self.logger.error(f"Error in time exit check: {e}")
    
    def _check_risk_limits(self) -> bool:
        """Check if risk limits allow trading"""
        try:
            account_info = self.mt5_connector.get_account_info()
            
            # Check drawdown
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            
            if balance > 0:
                drawdown = (balance - equity) / balance * 100
                if drawdown > 10:  # 10% max drawdown
                    return False
            
            # Check margin level
            margin_level = account_info.get('margin_level', 1000)
            if margin_level < 150:  # 150% minimum margin level
                return False
            
            # Check daily loss limit
            if self.stats['daily_pnl'] < -500:  # $500 daily loss limit
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking risk limits: {e}")
            return False
    
    def _update_statistics(self):
        """Update trading statistics"""
        try:
            # Get current account info
            account_info = self.mt5_connector.get_account_info()
            positions = self.mt5_connector.get_positions()
            
            # Calculate daily P&L
            session_profit = sum(pos['profit'] for pos in positions)
            self.stats['daily_pnl'] = session_profit
            
            # Update win rate (simplified calculation)
            if self.stats['trades_today'] > 0:
                self.stats['win_rate'] = (self.stats['wins'] / self.stats['trades_today']) * 100
            
            # Update active positions
            self.stats['active_positions'] = len(positions)
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def _reset_daily_stats(self):
        """Reset daily statistics"""
        self.stats.update({
            'trades_today': 0,
            'wins': 0,
            'losses': 0,
            'daily_pnl': 0.0,
            'last_trade_time': None
        })
        self.session_start = datetime.now()
    
    def _emergency_close_all(self):
        """Emergency close all positions"""
        try:
            positions = self.mt5_connector.get_positions()
            for position in positions:
                result = self.mt5_connector.close_position(position['ticket'])
                if result.get('retcode') == 10009:
                    self.logger.info(f"Emergency close: Position #{position['ticket']}")
        except Exception as e:
            self.logger.error(f"Error in emergency close: {e}")
    
    def _get_session_summary(self) -> str:
        """Get trading session summary"""
        session_time = datetime.now() - self.session_start
        return (
            f"Session Summary:\n"
            f"Duration: {session_time}\n"
            f"Trades: {self.stats['trades_today']}\n"
            f"Win Rate: {self.stats['win_rate']:.1f}%\n"
            f"P&L: ${self.stats['daily_pnl']:.2f}\n"
            f"Active Positions: {self.stats['active_positions']}"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            'running': self.running,
            'connected': self.mt5_connector.check_connection(),
            'trades_today': self.stats['trades_today'],
            'win_rate': self.stats['win_rate'],
            'daily_pnl': self.stats['daily_pnl'],
            'active_positions': self.stats['active_positions'],
            'last_trade_time': self.stats['last_trade_time'],
            'session_start': self.session_start,
            'active_symbols': self.active_symbols
        }
    
    def force_close_all(self):
        """Force close all positions (manual trigger)"""
        self._emergency_close_all()
    
    def pause_trading(self):
        """Pause trading (keep engine running but stop new trades)"""
        # This could be implemented with a pause flag
        pass
    
    def resume_trading(self):
        """Resume trading after pause"""
        # Resume from pause
        pass
"""
Advanced Trading Engine for AuraTrade Bot
Multi-strategy execution engine with risk management
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from utils.logger import Logger

class TradingEngine:
    """Advanced trading engine with multi-strategy support"""
    
    def __init__(self, mt5_connector, order_manager, risk_manager, position_sizing, 
                 data_manager, ml_engine, notifier, strategies, technical_analysis):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_sizing = position_sizing
        self.data_manager = data_manager
        self.ml_engine = ml_engine
        self.notifier = notifier
        self.strategies = strategies
        self.technical_analysis = technical_analysis
        
        # Engine state
        self.running = False
        self.trading_thread = None
        self.last_analysis = {}
        self.active_strategy = 'scalping'
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        
        # Performance tracking
        self.trades_today = 0
        self.wins_today = 0
        self.daily_pnl = 0.0
        self.start_balance = 0.0
        self.max_drawdown = 0.0
        
        # Trading limits
        self.max_trades_per_hour = 20
        self.max_trades_per_day = 100
        self.last_trade_times = []
        
        self.logger.info("Trading Engine initialized")
    
    def start(self):
        """Start the trading engine"""
        if self.running:
            self.logger.warning("Trading engine already running")
            return
        
        try:
            # Initialize starting balance
            account_info = self.mt5_connector.get_account_info()
            self.start_balance = account_info.get('balance', 0)
            
            self.running = True
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()
            
            self.logger.info("Trading engine started successfully")
            
            # Send notification
            if self.notifier and self.notifier.enabled:
                self.notifier.send_system_status("started", 
                    f"Trading Engine Active\nStrategy: {self.active_strategy.upper()}\nSymbols: {', '.join(self.symbols)}")
            
        except Exception as e:
            self.logger.error(f"Error starting trading engine: {e}")
            self.running = False
    
    def stop(self):
        """Stop the trading engine"""
        self.running = False
        
        if self.trading_thread and self.trading_thread.is_alive():
            self.trading_thread.join(timeout=5)
        
        # Get final statistics
        final_stats = self._get_session_summary()
        self.logger.info(f"Trading engine stopped. Session summary: {final_stats}")
        
        # Send notification
        if self.notifier and self.notifier.enabled:
            self.notifier.send_system_status("stopped", 
                f"Trading Engine Stopped\n{final_stats}")
    
    def _trading_loop(self):
        """Main trading loop"""
        self.logger.info("Trading loop started")
        
        while self.running:
            try:
                # Check market hours and conditions
                if not self._can_trade():
                    time.sleep(10)
                    continue
                
                # Process each symbol
                for symbol in self.symbols:
                    if not self.running:
                        break
                    
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Check daily limits and risk
                if self._check_daily_limits():
                    self.logger.warning("Daily limits reached, stopping trading")
                    self.running = False
                    break
                
                time.sleep(1)  # Main loop interval
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                time.sleep(5)
        
        self.logger.info("Trading loop ended")
    
    def _process_symbol(self, symbol: str):
        """Process trading signals for a symbol"""
        try:
            # Get market data
            rates = self.data_manager.get_rates(symbol, count=100)
            if rates is None or len(rates) < 50:
                return
            
            # Get current tick
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return
            
            # Check spread
            spread = (tick['ask'] - tick['bid']) / self.mt5_connector.get_symbol_info(symbol).get('point', 0.00001)
            if spread > 5:  # Max 5 pips spread
                return
            
            # Perform technical analysis
            indicators = self.technical_analysis.calculate_all_indicators(rates)
            
            # Get trading signals from active strategy
            strategy = self.strategies.get(self.active_strategy)
            if not strategy:
                return
            
            signals = strategy.get_signals(rates, indicators, tick)
            
            # Enhance signals with ML
            enhanced_signals = self.ml_engine.enhance_signals(signals, rates, indicators)
            
            # Process valid signals
            for signal in enhanced_signals:
                if self._validate_signal(signal, symbol):
                    self._execute_signal(signal, symbol, tick)
            
            # Store analysis for GUI
            self.last_analysis[symbol] = {
                'timestamp': datetime.now(),
                'indicators': indicators,
                'signals': enhanced_signals,
                'tick': tick,
                'spread': spread
            }
            
        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {e}")
    
    def _validate_signal(self, signal: Dict, symbol: str) -> bool:
        """Validate trading signal"""
        try:
            # Check confidence threshold
            if signal.get('confidence', 0) < 0.65:
                return False
            
            # Check risk management
            if not self.risk_manager.can_open_position(symbol, signal.get('volume', 0.01)):
                return False
            
            # Check position limits
            positions = self.mt5_connector.get_positions()
            symbol_positions = [p for p in positions if p['symbol'] == symbol]
            if len(symbol_positions) >= 3:  # Max 3 positions per symbol
                return False
            
            # Check total positions
            if len(positions) >= 10:  # Max 10 total positions
                return False
            
            # Check hourly trade limit
            current_time = datetime.now()
            hour_ago = current_time - timedelta(hours=1)
            recent_trades = [t for t in self.last_trade_times if t > hour_ago]
            if len(recent_trades) >= self.max_trades_per_hour:
                return False
            
            # Check daily trade limit
            if self.trades_today >= self.max_trades_per_day:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating signal: {e}")
            return False
    
    def _execute_signal(self, signal: Dict, symbol: str, tick: Dict):
        """Execute trading signal"""
        try:
            action = signal.get('action', 'buy')
            volume = signal.get('volume', 0.01)
            
            # Calculate position size
            calculated_volume = self.position_sizing.calculate_position_size(
                symbol, signal.get('risk_percent', 1.0)
            )
            volume = min(volume, calculated_volume)
            
            # Calculate TP/SL
            tp_pips = signal.get('tp_pips', 40)
            sl_pips = signal.get('sl_pips', 20)
            
            current_price = tick['ask'] if action == 'buy' else tick['bid']
            point = self.mt5_connector.get_symbol_info(symbol).get('point', 0.00001)
            
            if action == 'buy':
                tp_price = current_price + (tp_pips * point)
                sl_price = current_price - (sl_pips * point)
            else:
                tp_price = current_price - (tp_pips * point)
                sl_price = current_price + (sl_pips * point)
            
            # Send order
            result = self.order_manager.send_market_order(
                action=action,
                symbol=symbol,
                volume=volume,
                tp=tp_price,
                sl=sl_price,
                comment=f"AuraTrade-{self.active_strategy}"
            )
            
            if result and result.get('retcode') == 10009:
                self.trades_today += 1
                self.last_trade_times.append(datetime.now())
                
                self.logger.info(f"Order executed: {action.upper()} {volume} {symbol} at {current_price}")
                
                # Send notification
                if self.notifier and self.notifier.enabled:
                    profit_potential = tp_pips * self._get_pip_value(symbol, volume)
                    self.notifier.send_trade_notification(
                        action, symbol, volume, current_price, 
                        f"Strategy: {self.active_strategy}, Confidence: {signal.get('confidence', 0):.2f}, Potential: ${profit_potential:.2f}"
                    )
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
    
    def _can_trade(self) -> bool:
        """Check if trading is allowed"""
        try:
            # Check connection
            if not self.mt5_connector.check_connection():
                return False
            
            # Check market hours (simplified)
            current_hour = datetime.now().hour
            if current_hour in [0, 1, 2, 22, 23]:  # Avoid low liquidity hours
                return False
            
            # Check weekend
            weekday = datetime.now().weekday()
            if weekday == 6:  # Sunday
                return False
            
            # Check account status
            account = self.mt5_connector.get_account_info()
            if not account or account.get('margin_level', 0) < 200:
                return False
            
            # Check daily loss limit
            if self.daily_pnl < -500:  # Max $500 daily loss
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking trading conditions: {e}")
            return False
    
    def _update_performance_metrics(self):
        """Update performance tracking"""
        try:
            account = self.mt5_connector.get_account_info()
            if account:
                current_balance = account.get('balance', self.start_balance)
                self.daily_pnl = current_balance - self.start_balance
                
                # Update drawdown
                equity = account.get('equity', current_balance)
                drawdown = (self.start_balance - equity) / self.start_balance * 100
                self.max_drawdown = max(self.max_drawdown, drawdown)
                
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def _check_daily_limits(self) -> bool:
        """Check if daily limits are reached"""
        try:
            # Check max daily loss
            if self.daily_pnl <= -500:  # $500 daily loss limit
                self.logger.warning(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
                return True
            
            # Check max drawdown
            if self.max_drawdown >= 5.0:  # 5% max drawdown
                self.logger.warning(f"Max drawdown reached: {self.max_drawdown:.2f}%")
                return True
            
            # Check profit target (auto-stop at 10% profit)
            if self.daily_pnl >= 1000:  # $1000 profit target
                self.logger.info(f"Daily profit target reached: ${self.daily_pnl:.2f}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking daily limits: {e}")
            return False
    
    def _get_pip_value(self, symbol: str, volume: float) -> float:
        """Calculate pip value for profit/loss calculations"""
        if 'JPY' in symbol:
            return volume  # $1 per pip for standard lot
        elif 'XAU' in symbol:
            return volume  # $1 per pip for gold
        else:
            return volume * 10  # $10 per pip for major pairs
    
    def _get_session_summary(self) -> str:
        """Get trading session summary"""
        win_rate = (self.wins_today / max(self.trades_today, 1)) * 100
        return f"Trades: {self.trades_today}, Win Rate: {win_rate:.1f}%, P&L: ${self.daily_pnl:.2f}, Max DD: {self.max_drawdown:.2f}%"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading engine status"""
        return {
            'running': self.running,
            'active_strategy': self.active_strategy,
            'symbols': self.symbols,
            'trades_today': self.trades_today,
            'wins_today': self.wins_today,
            'daily_pnl': self.daily_pnl,
            'max_drawdown': self.max_drawdown,
            'win_rate': (self.wins_today / max(self.trades_today, 1)) * 100,
            'last_analysis': self.last_analysis,
            'start_balance': self.start_balance
        }
    
    def set_strategy(self, strategy: str):
        """Change active trading strategy"""
        if strategy in self.strategies:
            self.active_strategy = strategy
            self.logger.info(f"Strategy changed to: {strategy}")
            return True
        return False
    
    def set_symbols(self, symbols: List[str]):
        """Set trading symbols"""
        self.symbols = symbols
        self.logger.info(f"Symbols updated: {symbols}")
    
    def get_latest_analysis(self, symbol: str) -> Optional[Dict]:
        """Get latest analysis for symbol"""
        return self.last_analysis.get(symbol)
