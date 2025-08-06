
#!/usr/bin/env python3
"""
AuraTrade Bot - Advanced Automated Trading System
High-performance MT5 trading bot with multiple strategies
"""

import sys
import os
import time
import threading
import signal
from datetime import datetime
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check GUI availability
GUI_AVAILABLE = False
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    GUI_AVAILABLE = True
except ImportError:
    print("⚠️ GUI libraries not available. Running in console mode.")

# Core imports
try:
    from config.config import Config
    from config.credentials import Credentials
    from config.settings import Settings
    from core.mt5_connector import MT5Connector
    from core.trading_engine import TradingEngine
    from core.order_manager import OrderManager
    from core.risk_manager import RiskManager
    from data.data_manager import DataManager
    from utils.logger import Logger
    from utils.notifier import ConsoleNotifier
except ImportError as e:
    print(f"❌ Critical import error: {e}")
    sys.exit(1)

# Import GUI if available
if GUI_AVAILABLE:
    try:
        from gui.main_window import MainWindow
    except ImportError as e:
        print(f"⚠️ GUI import error: {e}")
        GUI_AVAILABLE = False

class AuraTradeBot:
    """Main AuraTrade Bot class"""
    
    def __init__(self):
        """Initialize AuraTrade Bot"""
        print("🚀 Initializing AuraTrade Bot v2.0...")
        
        # Initialize logger first
        self.logger = Logger().get_logger()
        self.logger.info("Starting AuraTrade Bot initialization")
        
        # Initialize core components
        self.config = Config()
        self.credentials = Credentials()
        self.settings = Settings()
        
        # Initialize connectors and managers
        self.mt5_connector = None
        self.trading_engine = None
        self.order_manager = None
        self.risk_manager = None
        self.data_manager = None
        self.notifier = None
        
        # GUI components
        self.app = None
        self.main_window = None
        
        # State management
        self.running = False
        self.shutdown_flag = threading.Event()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("AuraTrade Bot initialized successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()
    
    def initialize_components(self) -> bool:
        """Initialize all bot components"""
        try:
            self.logger.info("Initializing bot components...")
            
            # Initialize MT5 connector
            self.mt5_connector = MT5Connector()
            
            # Initialize order manager
            self.order_manager = OrderManager(self.mt5_connector)
            
            # Initialize risk manager
            self.risk_manager = RiskManager(self.config.RISK_CONFIG)
            
            # Initialize data manager
            self.data_manager = DataManager(self.mt5_connector)
            
            # Initialize trading engine
            self.trading_engine = TradingEngine(
                self.mt5_connector,
                self.order_manager,
                self.risk_manager,
                self.data_manager,
                self.config,
                self.settings
            )
            
            # Initialize notifier
            self.notifier = ConsoleNotifier()
            
            self.logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            return False
    
    def connect_mt5(self) -> bool:
        """Connect to MetaTrader 5"""
        try:
            self.logger.info("Connecting to MetaTrader 5...")
            
            # Get credentials
            mt5_creds = self.credentials.get_mt5_credentials()
            
            if not self.credentials.is_mt5_configured():
                self.logger.warning("⚠️ MT5 credentials not configured. Attempting connection without login...")
                success = self.mt5_connector.connect()
            else:
                success = self.mt5_connector.connect(
                    login=int(mt5_creds['login']) if mt5_creds['login'] else None,
                    password=mt5_creds['password'],
                    server=mt5_creds['server']
                )
            
            if success:
                self.logger.info("✅ Connected to MT5 successfully")
                
                # Get account info
                account_info = self.mt5_connector.get_account_info()
                if account_info:
                    self.logger.info(f"Account: {account_info.get('login', 'N/A')} | "
                                   f"Balance: ${account_info.get('balance', 0):.2f} | "
                                   f"Server: {account_info.get('server', 'N/A')}")
                
                return True
            else:
                self.logger.error("❌ Failed to connect to MT5")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ MT5 connection error: {e}")
            return False
    
    def initialize_gui(self) -> bool:
        """Initialize GUI if available"""
        if not GUI_AVAILABLE:
            self.logger.info("GUI not available, running in console mode")
            return False
            
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

            self.logger.info("✅ GUI initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize GUI: {e}")
            return False

    def start_trading(self) -> bool:
        """Start the trading engine"""
        try:
            self.logger.info("Starting high-performance trading engine...")

            # Start data updates
            symbols = self.settings.get_enabled_symbols()
            self.data_manager.start_data_updates(symbols)

            # Start trading engine
            success = self.trading_engine.start()
            
            if success:
                self.running = True
                self.logger.info("✅ Trading engine started successfully")

                # Send running notification
                if self.notifier and self.notifier.enabled:
                    try:
                        self.notifier.send_system_status("running", "AuraTrade Bot is now active")
                    except Exception as e:
                        self.logger.warning(f"Could not send running notification: {e}")

                return True
            else:
                self.logger.error("❌ Failed to start trading engine")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error starting trading: {e}")
            return False

    def stop_trading(self) -> bool:
        """Stop the trading engine"""
        try:
            self.logger.info("Stopping trading engine...")
            
            if self.trading_engine:
                self.trading_engine.stop()
            
            if self.data_manager:
                self.data_manager.stop_data_updates()
            
            self.running = False
            self.logger.info("✅ Trading engine stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping trading: {e}")
            return False

    def run_console_mode(self):
        """Run bot in console mode"""
        self.logger.info("🖥️ Running in console mode")
        
        print("\n" + "="*60)
        print("🤖 AuraTrade Bot - Console Mode")
        print("="*60)
        print(f"Status: {'🟢 RUNNING' if self.running else '🔴 STOPPED'}")
        print(f"MT5 Connected: {'✅' if self.mt5_connector.connected else '❌'}")
        print(f"Credentials: {self.credentials.get_credential_status()}")
        print("="*60)
        
        try:
            while not self.shutdown_flag.is_set():
                time.sleep(1)
                
                # Print periodic status
                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    if self.mt5_connector.connected:
                        account_info = self.mt5_connector.get_account_info()
                        if account_info:
                            print(f"💰 Balance: ${account_info.get('balance', 0):.2f} | "
                                f"Equity: ${account_info.get('equity', 0):.2f}")
                    
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        
        self.shutdown()

    def run_gui_mode(self):
        """Run bot with GUI"""
        self.logger.info("🖥️ Running in GUI mode")
        
        # Show main window
        self.main_window.show()
        
        # Start Qt event loop
        return self.app.exec_()

    def shutdown(self):
        """Shutdown the bot gracefully"""
        self.logger.info("🛑 Shutting down AuraTrade Bot...")
        
        # Set shutdown flag
        self.shutdown_flag.set()
        
        # Stop trading
        if self.running:
            self.stop_trading()
        
        # Disconnect MT5
        if self.mt5_connector:
            self.mt5_connector.disconnect()
        
        # Send shutdown notification
        if self.notifier and self.notifier.enabled:
            try:
                self.notifier.send_system_status("stopped", "AuraTrade Bot shutdown complete")
            except:
                pass
        
        self.logger.info("✅ AuraTrade Bot shutdown complete")
        
        # Exit GUI if running
        if self.app:
            self.app.quit()

    def run(self):
        """Main run method"""
        try:
            # Initialize components
            if not self.initialize_components():
                self.logger.error("❌ Failed to initialize components")
                return 1
            
            # Connect to MT5
            if not self.connect_mt5():
                self.logger.error("❌ Failed to connect to MT5")
                return 1
            
            # Start trading
            if not self.start_trading():
                self.logger.error("❌ Failed to start trading")
                return 1
            
            # Initialize and run GUI or console mode
            if self.initialize_gui():
                return self.run_gui_mode()
            else:
                self.run_console_mode()
                return 0
                
        except Exception as e:
            self.logger.error(f"❌ Critical error in main run: {e}")
            return 1
        finally:
            self.shutdown()

def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                        🤖 AURATRADE BOT v2.0                       ║
    ║               Advanced Automated Trading System                   ║
    ║                    Target: 75%+ Win Rate                         ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Create and run bot
    bot = AuraTradeBot()
    exit_code = bot.run()
    
    print("\n👋 Thank you for using AuraTrade Bot!")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
