
#!/usr/bin/env python3
"""
AuraTrade - High-Performance Trading Bot
Fixed and optimized for Windows compatibility
"""

import sys
import os
import time
import threading
import signal
from datetime import datetime
from typing import Dict, List
import MetaTrader5 as mt5

# Fix encoding for Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtWidgets import QApplication
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt5 not available - running in console mode only")

from config.config import Config
from config.credentials import Credentials
from config.settings import Settings
from core.mt5_connector import MT5Connector
from core.trading_engine import TradingEngine
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.position_sizing import PositionSizing
from data.data_manager import DataManager
from utils.logger import Logger
from utils.notifier import TelegramNotifier

# Import strategies
from strategies.hft_strategy import HFTStrategy
from strategies.scalping_strategy import ScalpingStrategy
from strategies.pattern_strategy import PatternStrategy

# Import analysis
from analysis.technical_analysis import TechnicalAnalysis

# Import GUI if available
if GUI_AVAILABLE:
    from gui.main_window import MainWindow

class MLEngine:
    """Placeholder ML engine"""
    def __init__(self):
        pass

class AuraTradeBot:
    """High-performance trading bot optimized for Windows"""

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

        self.logger.info("AuraTrade Bot initialized")

    def initialize_components(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing AuraTrade components...")

            # Validate credentials first
            validation = self.credentials.validate_credentials()
            if not validation['mt5_configured']:
                self.logger.error("MT5 credentials not configured properly")
                self.logger.info("Please configure MT5 credentials in config/credentials.py")
                print("\n" + "="*60)
                print("CONFIGURATION REQUIRED:")
                print("Edit AuraTrade/config/credentials.py")
                print("Set your MT5 login, password, and server")
                print("="*60)
                return False

            # Initialize MT5 connector first
            self.mt5_connector = MT5Connector()
            if not self.mt5_connector.connect():
                self.logger.error("Failed to connect to MT5")
                self.logger.info("Make sure MT5 terminal is running and credentials are correct")
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
            strategies = {
                'hft': HFTStrategy(),
                'scalping': ScalpingStrategy(),
                'pattern': PatternStrategy()
            }

            # Initialize technical analysis
            technical_analysis = TechnicalAnalysis()

            # Initialize trading engine
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

            self.logger.info("All components initialized successfully")
            
            # Send startup notification
            if self.notifier and self.notifier.enabled:
                try:
                    account_info = self.mt5_connector.get_account_info()
                    self.notifier.send_system_status(
                        "initialized",
                        f"AuraTrade Bot Ready\nAccount: {account_info.get('login', 'N/A')}\nBalance: ${account_info.get('balance', 0):.2f}"
                    )
                except Exception as e:
                    self.logger.warning(f"Could not send startup notification: {e}")
            
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False

    def initialize_gui(self):
        """Initialize PyQt5 GUI if available"""
        if not GUI_AVAILABLE:
            self.logger.info("GUI not available - running in console mode")
            return True
            
        try:
            self.logger.info("Initializing GUI...")

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

            self.logger.info("GUI initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize GUI: {e}")
            return False

    def start_trading(self):
        """Start the trading engine"""
        try:
            self.logger.info("Starting high-performance trading engine...")

            # Start data updates
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
            self.data_manager.start_data_updates(symbols)

            # Start trading engine
            self.trading_engine.start()

            self.running = True
            self.logger.info("Trading engine started successfully")

            # Send running notification
            if self.notifier and self.notifier.enabled:
                try:
                    self.notifier.send_system_status("running", "AuraTrade Bot is now active")
                except Exception as e:
                    self.logger.warning(f"Could not send running notification: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start trading: {e}")
            return False

    def stop_trading(self):
        """Stop the trading engine and cleanup"""
        try:
            self.logger.info("Stopping AuraTrade Bot...")
            self.running = False

            # Stop data updates
            if self.data_manager:
                self.data_manager.stop_data_updates()

            # Stop trading engine
            if self.trading_engine:
                self.trading_engine.stop()

            # Get final statistics
            if self.trading_engine:
                try:
                    status = self.trading_engine.get_status()
                    final_stats = (
                        f"Final Statistics:\n"
                        f"Trades Today: {status.get('trades_today', 0)}\n"
                        f"Win Rate: {status.get('win_rate', 0):.1f}%\n"
                        f"Daily P&L: ${status.get('daily_pnl', 0):.2f}"
                    )

                    # Send shutdown notification with stats
                    if self.notifier and self.notifier.enabled:
                        self.notifier.send_system_status("stopped", f"AuraTrade Bot stopped\n{final_stats}")
                except Exception as e:
                    self.logger.warning(f"Could not get final statistics: {e}")

            # Disconnect MT5
            if self.mt5_connector:
                self.mt5_connector.disconnect()

            # Close GUI
            if self.app:
                self.app.quit()

            self.logger.info("Bot stopped successfully")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def run(self):
        """Main execution method"""
        try:
            print("AuraTrade Bot v2.0 - High Performance Trading System")
            print("Target: 75%+ Win Rate with Conservative Risk Management")
            print("=" * 60)

            # Initialize components
            if not self.initialize_components():
                self.logger.error("Failed to initialize components")
                return False

            # Initialize GUI if available
            if GUI_AVAILABLE:
                if not self.initialize_gui():
                    self.logger.error("Failed to initialize GUI")
                    return False

            # Start trading
            if not self.start_trading():
                self.logger.error("Failed to start trading")
                return False

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, lambda s, f: self.stop_trading())
            signal.signal(signal.SIGTERM, lambda s, f: self.stop_trading())

            self.logger.info("AuraTrade Bot is running - Target: 75%+ Win Rate")

            if GUI_AVAILABLE and self.main_window:
                # Show main window and start GUI event loop
                self.main_window.show()
                return self.app.exec_()
            else:
                # Console mode - keep running
                print("\nRunning in console mode...")
                print("Press Ctrl+C to stop the bot")
                try:
                    while self.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutdown requested by user")
                    self.stop_trading()
                return 0

        except Exception as e:
            self.logger.error(f"Critical error in main execution: {e}")
            return False
        finally:
            self.stop_trading()

def main():
    """Entry point"""
    try:
        # Create and run bot
        bot = AuraTradeBot()
        exit_code = bot.run()
        sys.exit(exit_code if exit_code else 0)

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
