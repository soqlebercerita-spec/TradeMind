
"""
High-performance Trading Engine for AuraTrade Bot
Manages all trading operations, strategies, and risk controls
"""

import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from core.mt5_connector import MT5Connector
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.position_sizing import PositionSizing
from data.data_manager import DataManager
from utils.logger import Logger
from utils.notifier import TelegramNotifier

class TradingEngine:
    """High-performance trading engine with multi-strategy support"""

    def __init__(self, mt5_connector: MT5Connector, order_manager: OrderManager,
                 risk_manager: RiskManager, position_sizing: PositionSizing,
                 data_manager: DataManager, ml_engine, notifier: TelegramNotifier,
                 strategies: Dict, technical_analysis):
        
        self.logger = Logger().get_logger()
        self.mt5 = mt5_connector
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
        self.monitoring_thread = None
        
        # Trading configuration
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        self.timeframes = ['M1', 'M5', 'M15']
        self.strategy_weights = {
            'hft': 0.4,
            'scalping': 0.3,
            'pattern': 0.3
        }
        
        # Performance tracking
        self.trades_today = 0
        self.wins_today = 0
        self.daily_pnl = 0.0
        self.start_balance = 0.0
        
        self.logger.info("TradingEngine initialized")

    def start(self):
        """Start the trading engine"""
        try:
            if self.running:
                self.logger.warning("Trading engine already running")
                return
            
            self.logger.info("Starting high-performance trading engine...")
            
            # Get initial balance
            account = self.mt5.get_account_info()
            self.start_balance = account.get('balance', 0) if account else 0
            
            # Start engine
            self.running = True
            
            # Start trading thread
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            self.logger.info("Trading engine started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting trading engine: {e}")
            self.running = False

    def stop(self):
        """Stop the trading engine"""
        try:
            self.logger.info("Stopping trading engine...")
            self.running = False
            
            # Wait for threads to finish
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=5)
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            self.logger.info("Trading engine stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")

    def _trading_loop(self):
        """Main trading loop"""
        self.logger.info("Trading loop started")
        
        while self.running:
            try:
                # Check MT5 connection
                if not self.mt5.ensure_connection():
                    self.logger.warning("MT5 connection lost, retrying...")
                    time.sleep(30)
                    continue
                
                # Process each symbol
                for symbol in self.symbols:
                    if not self.running:
                        break
                    
                    self._process_symbol(symbol)
                
                # Brief pause between cycles
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                time.sleep(5)
        
        self.logger.info("Trading loop stopped")

    def _monitoring_loop(self):
        """Position monitoring and management loop"""
        self.logger.info("Monitoring loop started")
        
        while self.running:
            try:
                # Update positions
                self.order_manager.update_positions()
                
                # Check risk limits
                risk_status = self.risk_manager.get_risk_status()
                if risk_status.get('emergency_stop', False):
                    self.logger.warning("Emergency stop triggered - closing all positions")
                    self._close_all_positions("Emergency stop")
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Sleep before next check
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
        
        self.logger.info("Monitoring loop stopped")

    def _process_symbol(self, symbol: str):
        """Process trading signals for a symbol"""
        try:
            # Get latest data
            data = {}
            for tf in self.timeframes:
                df = self.data_manager.get_realtime_data(symbol, tf)
                if df is not None and len(df) > 0:
                    data[tf] = df
            
            if not data:
                return
            
            # Generate signals from each strategy
            signals = []
            
            for strategy_name, strategy in self.strategies.items():
                try:
                    weight = self.strategy_weights.get(strategy_name, 0.0)
                    if weight > 0:
                        signal = strategy.generate_signal(symbol, data)
                        if signal and signal.get('action') != 'HOLD':
                            signal['weight'] = weight
                            signal['strategy'] = strategy_name
                            signals.append(signal)
                except Exception as e:
                    self.logger.error(f"Error in strategy {strategy_name}: {e}")
            
            # Process signals
            if signals:
                self._execute_signals(symbol, signals)
                
        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {e}")

    def _execute_signals(self, symbol: str, signals: List[Dict]):
        """Execute trading signals with risk management"""
        try:
            # Combine signals
            combined_signal = self._combine_signals(signals)
            
            if not combined_signal or combined_signal['action'] == 'HOLD':
                return
            
            # Check if we can open position
            if not self.risk_manager.can_open_position(symbol, 0.1):  # Base volume check
                return
            
            # Get account info
            account = self.mt5.get_account_info()
            if not account:
                return
            
            balance = account.get('balance', 0)
            if balance <= 0:
                return
            
            # Calculate position size
            entry_price = combined_signal.get('entry_price', 0)
            if entry_price <= 0:
                symbol_info = self.mt5.get_symbol_info(symbol)
                if symbol_info:
                    entry_price = symbol_info.get('ask' if combined_signal['action'] == 'BUY' else 'bid', 0)
            
            # Calculate SL and TP
            sl_tp = self.risk_manager.calculate_sl_tp(
                symbol, combined_signal['action'], entry_price, balance
            )
            
            if sl_tp['sl'] <= 0:
                return
            
            # Calculate position size
            volume = self.risk_manager.calculate_position_size(
                symbol, entry_price, sl_tp['sl']
            )
            
            if volume <= 0:
                return
            
            # Execute order
            result = self.order_manager.send_market_order(
                symbol=symbol,
                order_type=combined_signal['action'],
                volume=volume,
                sl=sl_tp['sl'],
                tp=sl_tp['tp'],
                comment=f"Auto-{combined_signal.get('strategy', 'Mixed')}"
            )
            
            if result['success']:
                self.logger.info(f"Order executed: {symbol} {combined_signal['action']} {volume}")
                self.trades_today += 1
            else:
                self.logger.warning(f"Order failed: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            self.logger.error(f"Error executing signals: {e}")

    def _combine_signals(self, signals: List[Dict]) -> Optional[Dict]:
        """Combine multiple strategy signals"""
        try:
            if not signals:
                return None
            
            # Weight-based signal combination
            buy_weight = 0.0
            sell_weight = 0.0
            
            for signal in signals:
                weight = signal.get('weight', 0.0)
                if signal['action'] == 'BUY':
                    buy_weight += weight
                elif signal['action'] == 'SELL':
                    sell_weight += weight
            
            # Determine final action
            if buy_weight > sell_weight and buy_weight > 0.5:
                action = 'BUY'
                confidence = buy_weight
            elif sell_weight > buy_weight and sell_weight > 0.5:
                action = 'SELL'
                confidence = sell_weight
            else:
                return {'action': 'HOLD'}
            
            # Get best signal for entry details
            best_signal = max(signals, key=lambda x: x.get('confidence', 0))
            
            return {
                'action': action,
                'confidence': confidence,
                'entry_price': best_signal.get('entry_price', 0),
                'strategy': 'Combined'
            }
            
        except Exception as e:
            self.logger.error(f"Error combining signals: {e}")
            return None

    def _close_all_positions(self, reason: str = "Manual"):
        """Close all open positions"""
        try:
            positions = self.mt5.get_positions()
            for pos in positions:
                self.order_manager.close_position(pos['ticket'], reason)
                time.sleep(0.5)  # Avoid overwhelming the broker
            
            self.logger.info(f"Closed {len(positions)} positions - {reason}")
            
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")

    def _update_performance_metrics(self):
        """Update performance tracking"""
        try:
            account = self.mt5.get_account_info()
            if not account:
                return
            
            current_balance = account.get('balance', 0)
            self.daily_pnl = current_balance - self.start_balance
            
            # Update win rate calculation
            positions = self.mt5.get_positions()
            winning_positions = sum(1 for pos in positions if pos['profit'] > 0)
            
            if self.trades_today > 0:
                self.wins_today = winning_positions
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get trading engine status"""
        try:
            account = self.mt5.get_account_info()
            risk_status = self.risk_manager.get_risk_status()
            
            win_rate = (self.wins_today / self.trades_today * 100) if self.trades_today > 0 else 0
            
            return {
                'running': self.running,
                'connected': self.mt5.is_connected(),
                'balance': account.get('balance', 0) if account else 0,
                'equity': account.get('equity', 0) if account else 0,
                'trades_today': self.trades_today,
                'wins_today': self.wins_today,
                'win_rate': win_rate,
                'daily_pnl': self.daily_pnl,
                'emergency_stop': risk_status.get('emergency_stop', False),
                'active_positions': len(self.mt5.get_positions()),
                'strategies_loaded': len(self.strategies)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'running': False, 'error': str(e)}

    def force_close_all(self):
        """Force close all positions (emergency)"""
        self.logger.warning("Force closing all positions")
        self._close_all_positions("Force close")
