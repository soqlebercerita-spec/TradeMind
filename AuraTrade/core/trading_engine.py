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
        self.analysis_thread = None

        # Performance tracking
        self.trades_today = 0
        self.wins = 0
        self.losses = 0
        self.daily_pnl = 0.0
        self.start_balance = 0.0

        # Configuration
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        self.check_interval = 1.0  # seconds
        self.max_concurrent_trades = 5
        self.min_confidence = 70.0

        self.logger.info("Trading Engine initialized")

    def start(self):
        """Start the trading engine"""
        try:
            if self.running:
                self.logger.warning("Trading engine already running")
                return

            self.logger.info("Starting high-performance trading engine...")
            self.running = True

            # Record start balance
            account_info = self.mt5_connector.get_account_info()
            self.start_balance = account_info.get('balance', 0.0)

            # Start trading thread
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()

            # Start analysis thread
            self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
            self.analysis_thread.start()

            self.logger.info("Trading engine started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start trading engine: {e}")
            self.running = False

    def stop(self):
        """Stop the trading engine"""
        try:
            self.logger.info("Stopping trading engine...")
            self.running = False

            # Wait for threads to complete
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=5.0)

            if self.analysis_thread and self.analysis_thread.is_alive():
                self.analysis_thread.join(timeout=5.0)

            self.logger.info("Trading engine stopped")

        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")

    def _trading_loop(self):
        """Main trading loop"""
        self.logger.info("Trading loop started")

        while self.running:
            try:
                # Check MT5 connection
                if not self.mt5_connector.ensure_connection():
                    self.logger.warning("MT5 connection lost, retrying...")
                    time.sleep(10)
                    continue

                # Check risk limits
                if not self.risk_manager.check_global_risk():
                    self.logger.warning("Global risk limits exceeded, pausing trading")
                    time.sleep(60)
                    continue

                # Process each symbol
                for symbol in self.symbols:
                    if not self.running:
                        break

                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")

                # Check existing positions
                self._manage_positions()

                # Update performance metrics
                self._update_performance()

                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                time.sleep(5)

        self.logger.info("Trading loop ended")

    def _analysis_loop(self):
        """Analysis and signal generation loop"""
        self.logger.info("Analysis loop started")

        while self.running:
            try:
                # Update market data
                for symbol in self.symbols:
                    if not self.running:
                        break

                    # Get latest data
                    df = self.mt5_connector.get_rates(symbol, 'M1', 100)
                    if df is not None and len(df) > 0:
                        self.data_manager.update_symbol_data(symbol, df)

                time.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                time.sleep(30)

        self.logger.info("Analysis loop ended")

    def _process_symbol(self, symbol: str):
        """Process trading signals for a symbol"""
        try:
            # Get market data
            df = self.data_manager.get_symbol_data(symbol)
            if df is None or len(df) < 50:
                return

            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info is None:
                return

            # Check market conditions
            if not self._check_market_conditions(symbol_info):
                return

            # Check position limits
            current_positions = len([p for p in self.mt5_connector.get_positions() 
                                   if p['symbol'] == symbol])
            if current_positions >= 2:  # Max 2 positions per symbol
                return

            # Generate signals from all strategies
            signals = []

            for strategy_name, strategy in self.strategies.items():
                try:
                    signal = strategy.generate_signal(df, symbol_info)
                    if signal and signal.get('confidence', 0) >= self.min_confidence:
                        signal['strategy'] = strategy_name
                        signals.append(signal)
                except Exception as e:
                    self.logger.error(f"Error in {strategy_name} strategy: {e}")

            # Process signals
            if signals:
                best_signal = max(signals, key=lambda x: x.get('confidence', 0))
                self._execute_signal(symbol, best_signal)

        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {e}")

    def _check_market_conditions(self, symbol_info: Dict[str, Any]) -> bool:
        """Check if market conditions are suitable for trading"""
        try:
            # Check spread
            spread_pips = symbol_info['spread'] * symbol_info['point'] * 10
            if spread_pips > 3.0:
                return False

            # Check trading hours (avoid low liquidity periods)
            current_hour = datetime.now().hour
            if current_hour < 8 or current_hour > 17:
                return False

            # Check volatility
            if symbol_info.get('volume_high', 0) == 0:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking market conditions: {e}")
            return False

    def _execute_signal(self, symbol: str, signal: Dict[str, Any]):
        """Execute trading signal"""
        try:
            # Check total positions
            total_positions = len(self.mt5_connector.get_positions())
            if total_positions >= self.max_concurrent_trades:
                return

            # Calculate position size
            account_info = self.mt5_connector.get_account_info()
            lot_size = self.position_sizing.calculate_lot_size(
                symbol, signal['direction'], signal.get('confidence', 70)
            )

            if lot_size <= 0:
                return

            # Calculate SL/TP based on percentage
            entry_price = signal['price']
            balance = account_info['balance']

            # Risk 2% of balance per trade
            risk_amount = balance * 0.02
            symbol_info = self.mt5_connector.get_symbol_info(symbol)

            if signal['direction'] == 'BUY':
                # Stop loss 1.5% below entry
                sl_price = entry_price * 0.985
                # Take profit 3% above entry (2:1 RR)
                tp_price = entry_price * 1.03
                order_type = 0  # BUY
            else:
                # Stop loss 1.5% above entry
                sl_price = entry_price * 1.015
                # Take profit 3% below entry
                tp_price = entry_price * 0.97
                order_type = 1  # SELL

            # Place order
            result = self.order_manager.place_order(
                symbol=symbol,
                order_type=order_type,
                lot_size=lot_size,
                price=entry_price,
                sl=sl_price,
                tp=tp_price,
                comment=f"{signal['strategy']} - Conf: {signal['confidence']:.1f}%"
            )

            if result['success']:
                self.trades_today += 1
                self.logger.info(f"Order placed: {symbol} {signal['direction']} {lot_size} lots")

                # Send notification
                if self.notifier and self.notifier.enabled:
                    message = (
                        f"🎯 New Trade Opened\n"
                        f"Symbol: {symbol}\n"
                        f"Direction: {signal['direction']}\n"
                        f"Lot Size: {lot_size}\n"
                        f"Entry: {entry_price:.5f}\n"
                        f"SL: {sl_price:.5f}\n"
                        f"TP: {tp_price:.5f}\n"
                        f"Strategy: {signal['strategy']}\n"
                        f"Confidence: {signal['confidence']:.1f}%"
                    )
                    self.notifier.send_trade_alert(message)

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")

    def _manage_positions(self):
        """Manage existing positions"""
        try:
            positions = self.mt5_connector.get_positions()

            for position in positions:
                # Check for trailing stop
                self._check_trailing_stop(position)

                # Check for emergency close conditions
                if position['profit'] < -500:  # Emergency close at $500 loss
                    self.logger.warning(f"Emergency closing position {position['ticket']} due to large loss")
                    self.mt5_connector.close_position(position['ticket'])

                    if self.notifier and self.notifier.enabled:
                        message = f"🚨 Emergency Close\nTicket: {position['ticket']}\nLoss: ${position['profit']:.2f}"
                        self.notifier.send_trade_alert(message)

        except Exception as e:
            self.logger.error(f"Error managing positions: {e}")

    def _check_trailing_stop(self, position: Dict[str, Any]):
        """Check and update trailing stop"""
        try:
            symbol = position['symbol']
            ticket = position['ticket']

            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info is None:
                return

            current_price = symbol_info['bid'] if position['type'] == 0 else symbol_info['ask']
            entry_price = position['price_open']
            current_sl = position['sl']

            # Only trail if in profit
            if position['profit'] <= 0:
                return

            trailing_distance = entry_price * 0.01  # 1% trailing distance

            if position['type'] == 0:  # BUY position
                new_sl = current_price - trailing_distance
                if current_sl == 0 or new_sl > current_sl:
                    self.mt5_connector.modify_position(ticket, sl=new_sl, tp=position['tp'])
                    self.logger.info(f"Trailing stop updated for {ticket}: {new_sl:.5f}")
            else:  # SELL position
                new_sl = current_price + trailing_distance
                if current_sl == 0 or new_sl < current_sl:
                    self.mt5_connector.modify_position(ticket, sl=new_sl, tp=position['tp'])
                    self.logger.info(f"Trailing stop updated for {ticket}: {new_sl:.5f}")

        except Exception as e:
            self.logger.error(f"Error checking trailing stop: {e}")

    def _update_performance(self):
        """Update performance metrics"""
        try:
            account_info = self.mt5_connector.get_account_info()
            current_balance = account_info.get('balance', 0.0)
            self.daily_pnl = current_balance - self.start_balance

            # Update win/loss statistics
            # This would typically be done when positions are closed
            # For now, we'll estimate based on current positions
            positions = self.mt5_connector.get_positions()
            winning_positions = len([p for p in positions if p['profit'] > 0])
            losing_positions = len([p for p in positions if p['profit'] < 0])

            total_trades = self.wins + self.losses
            if total_trades > 0:
                win_rate = (self.wins / total_trades) * 100
            else:
                win_rate = 0

        except Exception as e:
            self.logger.error(f"Error updating performance: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current trading engine status"""
        try:
            account_info = self.mt5_connector.get_account_info()
            positions = self.mt5_connector.get_positions()

            total_trades = self.wins + self.losses
            win_rate = (self.wins / total_trades * 100) if total_trades > 0 else 0

            return {
                'running': self.running,
                'connected': self.mt5_connector.is_connected(),
                'balance': account_info.get('balance', 0.0),
                'equity': account_info.get('equity', 0.0),
                'free_margin': account_info.get('free_margin', 0.0),
                'open_positions': len(positions),
                'trades_today': self.trades_today,
                'wins': self.wins,
                'losses': self.losses,
                'win_rate': win_rate,
                'daily_pnl': self.daily_pnl,
                'total_profit': sum([p['profit'] for p in positions])
            }

        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {
                'running': self.running,
                'connected': False,
                'error': str(e)
            }