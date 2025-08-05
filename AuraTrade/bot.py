#!/usr/bin/env python3
"""
AuraTrade - High-Performance Trading Bot
Optimized for 85%+ win rate with conservative risk management
"""

import sys
import os
import time
import threading
from datetime import datetime
from typing import Dict, List
import MetaTrader5 as mt5
from PyQt5.QtWidgets import QApplication

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from config.credentials import Credentials
from config.settings import Settings
from core.mt5_connector import MT5Connector
from core.trading_engine import TradingEngine
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.position_sizing import PositionSizing
from data.data_manager import DataManager
from gui.main_window import MainWindow
from utils.logger import Logger
from utils.notifier import TelegramNotifier as Notifier # Alias TelegramNotifier to Notifier for brevity
from utils.notifier import TelegramNotifier

class MLEngine:
    """Placeholder ML engine"""
    def __init__(self):
        pass

class AuraTradeBot:
    """High-performance trading bot optimized for 85%+ win rate"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.config = Config()
        self.credentials = Credentials()
        self.settings = Settings()
        self.running = False

        # GUI Application
        self.app = None
        self.main_window = None

        # Core components
        self.mt5_connector = None
        self.trading_engine = None
        self.order_manager = None
        self.risk_manager = None
        self.position_sizing = None
        self.ml_engine = None
        self.data_manager = None
        self.notifier = None

        self.logger.info("🤖 AuraTrade Bot initialized")

        # Initialize notification system
        self.notifier = Notifier()
        self.logger.info("📱 Notification system initialized")

        # Send startup notification
        if self.notifier.enabled:
            self.notifier.send_message(
                "🚀 <b>AuraTrade Bot Started</b>\n\n"
                "✅ System: Online\n"
                "📱 Notifications: Active\n"
                "💹 Ready for trading signals\n"
                f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.logger.info("✅ Startup notification sent to Telegram")


    def initialize_components(self):
        """Initialize all system components"""
        try:
            self.logger.info("🔧 Initializing AuraTrade components...")

            # Validate credentials first
            validation = self.credentials.validate_credentials()
            if not validation['mt5_configured']:
                self.logger.error("❌ MT5 credentials not configured properly")
                self.logger.info("💡 Please configure MT5 credentials in config/credentials.py")
                return False

            # Initialize MT5 connector first
            self.mt5_connector = MT5Connector()
            if not self.mt5_connector.connect():
                self.logger.error("❌ Failed to connect to MT5")
                self.logger.info("💡 Make sure MT5 terminal is running and credentials are correct")
                return False

            # Initialize notification system
            self.notifier = TelegramNotifier()
            if self.notifier.enabled:
                self.notifier.test_connection()

            # Initialize data manager
            self.data_manager = DataManager(self.mt5_connector)

            # Initialize risk management
            self.risk_manager = RiskManager(self.mt5_connector)
            self.position_sizing = PositionSizing(self.mt5_connector, self.risk_manager)

            # Initialize order manager
            self.order_manager = OrderManager(self.mt5_connector, self.risk_manager, self.notifier)

            # Initialize ML engine (placeholder)
            self.ml_engine = MLEngine()

            # Initialize strategies
            from strategies.hft_strategy import HFTStrategy
            from strategies.scalping_strategy import ScalpingStrategy
            from strategies.pattern_strategy import PatternStrategy
            from analysis.technical_analysis import TechnicalAnalysis

            strategies = {
                'hft': HFTStrategy(),
                'scalping': ScalpingStrategy(),
                'pattern': PatternStrategy()
            }

            technical_analysis = TechnicalAnalysis()

            # Initialize trading engine (optimized for high win rate)
            self.trading_engine = TradingEngine(
                self.mt5_connector,
                self.order_manager,
                self.risk_manager,
                self.position_sizing,
                self.data_manager,
                self.ml_engine,
                self.notifier,
                strategies,
                technical_analysis
            )

            self.logger.info("✅ All components initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            return False

    def initialize_gui(self):
        """Initialize PyQt5 GUI"""
        try:
            self.logger.info("🖥️ Initializing GUI...")

            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("AuraTrade Bot")
            self.app.setApplicationVersion("2.0.0")

            # Create main window
            self.main_window = MainWindow(
                self.trading_engine,
                self.order_manager,
                self.risk_manager,
                self.data_manager
            )

            self.logger.info("✅ GUI initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize GUI: {e}")
            return False

    def start_trading(self):
        """Start the trading engine"""
        try:
            self.logger.info("🚀 Starting high-performance trading engine...")

            # Send startup notification
            if self.notifier:
                account_info = self.mt5_connector.get_account_info()
                self.notifier.send_system_status(
                    "starting",
                    f"AuraTrade Bot v2.0 - Target Win Rate: 85%+\n"
                    f"Account: {account_info.get('login', 'N/A')}\n"
                    f"Balance: ${account_info.get('balance', 0):.2f}"
                )

            # Start data updates
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
            self.data_manager.start_data_updates(symbols)

            # Start trading engine
            self.trading_engine.start()

            self.running = True
            self.logger.info("✅ Trading engine started successfully")

            # Send running notification
            if self.notifier:
                self.notifier.send_system_status("running", "AuraTrade Bot is now active - Conservative Risk Mode")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start trading: {e}")
            return False

    def stop_trading(self):
        """Stop the trading engine and cleanup"""
        try:
            self.logger.info("🛑 Stopping AuraTrade Bot...")
            self.running = False

            # Stop data updates
            if self.data_manager:
                self.data_manager.stop_data_updates()

            # Stop trading engine
            if self.trading_engine:
                self.trading_engine.stop()

            # Get final statistics
            if self.trading_engine:
                status = self.trading_engine.get_status()
                final_stats = (
                    f"Final Statistics:\n"
                    f"Trades Today: {status.get('trades_today', 0)}\n"
                    f"Win Rate: {status.get('win_rate', 0):.1f}%\n"
                    f"Daily P&L: ${status.get('daily_pnl', 0):.2f}"
                )

                # Send shutdown notification with stats
                if self.notifier:
                    self.notifier.send_system_status("stopped", f"AuraTrade Bot stopped\n{final_stats}")

            # Disconnect MT5
            if self.mt5_connector:
                self.mt5_connector.disconnect()

            # Close GUI
            if self.app:
                self.app.quit()

            self.logger.info("✅ Bot stopped successfully")

        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

    def run(self):
        """Main execution method"""
        try:
            self.logger.info("🤖 Starting AuraTrade Bot v2.0 - High Performance Edition")

            # Initialize components
            if not self.initialize_components():
                self.logger.error("❌ Failed to initialize components")
                return False

            # Initialize GUI
            if not self.initialize_gui():
                self.logger.error("❌ Failed to initialize GUI")
                return False

            # Start trading
            if not self.start_trading():
                self.logger.error("❌ Failed to start trading")
                return False

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, lambda s, f: self.stop_trading())
            signal.signal(signal.SIGTERM, lambda s, f: self.stop_trading())

            # Show main window
            self.main_window.show()

            self.logger.info("🎯 AuraTrade Bot is running - Target: 85%+ Win Rate")

            # Start GUI event loop
            return self.app.exec_()

        except Exception as e:
            self.logger.error(f"❌ Critical error in main execution: {e}")
            return False
        finally:
            self.stop_trading()

def main():
    """Entry point"""
    try:
        print("🚀 AuraTrade Bot v2.0 - High Performance Trading System")
        print("🎯 Target: 85%+ Win Rate with Conservative Risk Management")
        print("=" * 60)

        # Create and run bot
        bot = AuraTradeBot()
        exit_code = bot.run()
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()