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
    """High-performance trading engine with 75%+ win rate target"""

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
        self.trading_thread = None
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        self.timeframes = ['M1', 'M5', 'M15', 'H1']

        # Performance tracking
        self.trades_today = 0
        self.wins_today = 0
        self.losses_today = 0
        self.daily_pnl = 0.0
        self.start_time = datetime.now()

        # Strategy settings
        self.strategy_weights = {
            'hft': 0.3,
            'scalping': 0.4,
            'pattern': 0.3
        }

        self.logger.info("TradingEngine initialized with target 75%+ win rate")

    def start(self) -> bool:
        """Start the trading engine"""
        try:
            if self.running:
                self.logger.warning("Trading engine already running")
                return False

            self.logger.info("Starting high-performance trading engine...")

            # Validate all components
            if not self._validate_components():
                return False

            # Initialize strategies
            self._initialize_strategies()

            # Start trading thread
            self.running = True
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()

            self.logger.info("Trading engine started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error starting trading engine: {e}")
            return False

    def stop(self) -> None:
        """Stop the trading engine"""
        try:
            self.logger.info("Stopping trading engine...")
            self.running = False

            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=5)

            # Close all positions if needed
            self._emergency_close_all()

            self.logger.info("Trading engine stopped")

        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")

    def _trading_loop(self) -> None:
        """Main trading loop"""
        self.logger.info("Trading loop started")

        while self.running:
            try:
                # Check if trading should be stopped due to risk
                if self.risk_manager.should_stop_trading():
                    self.logger.warning("Trading stopped by risk manager")
                    break

                # Update market data
                self._update_market_data()

                # Process each symbol
                for symbol in self.symbols:
                    if not self.running:
                        break

                    self._process_symbol(symbol)

                # Update trailing stops
                self.order_manager.update_trailing_stops()

                # Update performance metrics
                self._update_performance()

                # Sleep before next iteration
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                time.sleep(5)  # Wait before retry

        self.logger.info("Trading loop ended")

    def _update_market_data(self) -> None:
        """Update market data for all symbols"""
        try:
            for symbol in self.symbols:
                for timeframe in self.timeframes:
                    # This would trigger data manager updates
                    pass

        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")

    def _process_symbol(self, symbol: str) -> None:
        """Process trading signals for a symbol"""
        try:
            # Get latest data
            data = self.data_manager.get_latest_data(symbol, 'M5', 100)
            if data is None or data.empty:
                return

            # Check each strategy
            for strategy_name, strategy in self.strategies.items():
                try:
                    if not self.running:
                        break

                    # Get strategy signal
                    signal = self._get_strategy_signal(strategy, symbol, data)

                    if signal and signal['action'] != 'hold':
                        # Validate with risk manager
                        volume = self.position_sizing.calculate_position_size(
                            symbol, signal.get('confidence', 0.5)
                        )

                        if volume > 0 and self.risk_manager.validate_order(symbol, volume):
                            # Execute trade
                            self._execute_trade(symbol, signal, volume, strategy_name)

                except Exception as e:
                    self.logger.error(f"Error processing strategy {strategy_name}: {e}")

        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {e}")

    def _get_strategy_signal(self, strategy: Any, symbol: str, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Get trading signal from strategy"""
        try:
            if hasattr(strategy, 'analyze'):
                return strategy.analyze(symbol, data)
            return None
        except Exception as e:
            self.logger.error(f"Error getting strategy signal: {e}")
            return None

    def _execute_trade(self, symbol: str, signal: Dict[str, Any], volume: float, strategy: str) -> None:
        """Execute trade based on signal"""
        try:
            order_type = signal['action']  # 'buy' or 'sell'
            confidence = signal.get('confidence', 0.5)

            # Calculate SL/TP based on confidence and balance percentage
            sl_pct = 1.0 / confidence  # Higher confidence = tighter SL
            tp_pct = 2.0 * confidence  # Higher confidence = wider TP

            # Place order
            result = self.order_manager.place_market_order(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                sl_pct=sl_pct,
                tp_pct=tp_pct,
                comment=f"AuraTrade-{strategy}"
            )

            if result['success']:
                self.trades_today += 1
                self.logger.info(f"Trade executed: {symbol} {order_type} {volume} via {strategy}")

                # Send notification
                if self.notifier and self.notifier.enabled:
                    message = (
                        f"🎯 Trade Signal Executed\n"
                        f"Strategy: {strategy}\n"
                        f"Symbol: {symbol}\n"
                        f"Action: {order_type.upper()}\n"
                        f"Volume: {volume}\n"
                        f"Confidence: {confidence:.2f}\n"
                        f"Target Win Rate: 75%+"
                    )
                    self.notifier.send_trade_signal(message)
            else:
                self.logger.warning(f"Failed to execute trade: {result['error']}")

        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")

    def _update_performance(self) -> None:
        """Update performance metrics"""
        try:
            # Get current positions
            positions = self.order_manager.get_active_orders()

            # Calculate current P&L
            current_pnl = sum(pos.get('profit', 0) for pos in positions)

            # Update daily P&L (simplified)
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                # This is a simplified calculation
                self.daily_pnl = account_info.get('profit', 0)

            # Calculate win rate
            total_trades = self.wins_today + self.losses_today
            win_rate = (self.wins_today / total_trades * 100) if total_trades > 0 else 0

            # Log performance every 100 trades
            if self.trades_today % 100 == 0 and self.trades_today > 0:
                self.logger.info(f"Performance Update - Trades: {self.trades_today}, Win Rate: {win_rate:.1f}%, P&L: ${self.daily_pnl:.2f}")

        except Exception as e:
            self.logger.error(f"Error updating performance: {e}")

    def _validate_components(self) -> bool:
        """Validate all required components"""
        components = [
            ('MT5 Connector', self.mt5_connector),
            ('Order Manager', self.order_manager),
            ('Risk Manager', self.risk_manager),
            ('Position Sizing', self.position_sizing),
            ('Data Manager', self.data_manager)
        ]

        for name, component in components:
            if component is None:
                self.logger.error(f"Missing component: {name}")
                return False

        # Check MT5 connection
        if not self.mt5_connector.is_connected():
            self.logger.error("MT5 not connected")
            return False

        self.logger.info("All components validated successfully")
        return True

    def _initialize_strategies(self) -> None:
        """Initialize all trading strategies"""
        try:
            for name, strategy in self.strategies.items():
                if hasattr(strategy, 'initialize'):
                    strategy.initialize()
                self.logger.info(f"Strategy initialized: {name}")
        except Exception as e:
            self.logger.error(f"Error initializing strategies: {e}")

    def _emergency_close_all(self) -> None:
        """Emergency close all positions"""
        try:
            self.logger.warning("Emergency close all positions")
            result = self.order_manager.close_all_orders()

            if self.notifier and self.notifier.enabled:
                self.notifier.send_system_status(
                    "emergency_stop",
                    f"Emergency stop executed. Closed {result.get('closed', 0)} positions"
                )

        except Exception as e:
            self.logger.error(f"Error in emergency close: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current trading engine status"""
        try:
            total_trades = self.wins_today + self.losses_today
            win_rate = (self.wins_today / total_trades * 100) if total_trades > 0 else 0

            positions = self.order_manager.get_active_orders()
            risk_metrics = self.risk_manager.get_risk_metrics()

            runtime = datetime.now() - self.start_time

            return {
                'running': self.running,
                'runtime': str(runtime).split('.')[0],
                'trades_today': self.trades_today,
                'wins_today': self.wins_today,
                'losses_today': self.losses_today,
                'win_rate': win_rate,
                'daily_pnl': self.daily_pnl,
                'active_positions': len(positions),
                'symbols_trading': len(self.symbols),
                'risk_metrics': risk_metrics,
                'target_win_rate': 75.0
            }

        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'running': False, 'error': str(e)}

    def force_close_symbol(self, symbol: str) -> Dict[str, Any]:
        """Force close all positions for specific symbol"""
        try:
            return self.order_manager.close_all_orders(symbol)
        except Exception as e:
            self.logger.error(f"Error force closing {symbol}: {e}")
            return {'success': False, 'error': str(e)}

    def update_strategy_weights(self, weights: Dict[str, float]) -> None:
        """Update strategy weights"""
        try:
            self.strategy_weights.update(weights)
            self.logger.info(f"Strategy weights updated: {self.strategy_weights}")
        except Exception as e:
            self.logger.error(f"Error updating strategy weights: {e}")