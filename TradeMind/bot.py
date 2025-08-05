#!/usr/bin/env python3
"""
AuraTrade - Institutional Trading Bot
Main launcher and orchestrator for the entire trading system.
"""

import sys
import os
import asyncio
import signal
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from core.mt5_connector import MT5Connector
from core.trading_engine import TradingEngine
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.position_sizing import PositionSizing
from core.ml_engine import MLEngine
from data.data_manager import DataManager
from gui.main_window import MainWindow
from utils.logger import Logger
from utils.notifier import TelegramNotifier

class AuraTradeBot:
    """Main bot orchestrator class"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.config = Config()
        self.running = False
        self.components = {}
        
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
        
    def initialize_components(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing AuraTrade components...")
            
            # Initialize MT5 connector first
            self.mt5_connector = MT5Connector()
            if not self.mt5_connector.connect():
                self.logger.error("Failed to connect to MT5")
                return False
            
            # Initialize notifier
            self.notifier = TelegramNotifier()
            
            # Initialize data manager
            self.data_manager = DataManager(self.mt5_connector)
            
            # Initialize risk and position sizing
            self.risk_manager = RiskManager(self.mt5_connector)
            self.position_sizing = PositionSizing(self.mt5_connector, self.risk_manager)
            
            # Initialize order manager
            self.order_manager = OrderManager(self.mt5_connector, self.risk_manager, self.notifier)
            
            # Initialize ML engine
            self.ml_engine = MLEngine()
            
            # Initialize trading engine
            self.trading_engine = TradingEngine(
                mt5_connector=self.mt5_connector,
                data_manager=self.data_manager,
                order_manager=self.order_manager,
                risk_manager=self.risk_manager,
                position_sizing=self.position_sizing,
                ml_engine=self.ml_engine,
                notifier=self.notifier
            )
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def initialize_gui(self):
        """Initialize PyQt5 GUI"""
        try:
            self.app = QApplication(sys.argv)
            self.main_window = MainWindow(
                trading_engine=self.trading_engine,
                mt5_connector=self.mt5_connector,
                data_manager=self.data_manager,
                risk_manager=self.risk_manager
            )
            
            self.logger.info("GUI initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GUI: {e}")
            return False
    
    def start_trading(self):
        """Start the trading engine"""
        try:
            self.logger.info("Starting trading engine...")
            self.running = True
            
            # Start trading engine in separate thread
            trading_thread = threading.Thread(target=self.trading_engine.start, daemon=True)
            trading_thread.start()
            
            # Send startup notification
            if self.notifier:
                self.notifier.send_message(
                    "🚀 AuraTrade Bot Started\n"
                    f"Account: {self.mt5_connector.get_account_info()['login']}\n"
                    f"Balance: ${self.mt5_connector.get_account_info()['balance']:.2f}\n"
                    f"Server: {self.mt5_connector.get_account_info()['server']}"
                )
            
            self.logger.info("Trading engine started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start trading: {e}")
            return False
    
    def stop_trading(self):
        """Stop the trading engine and cleanup"""
        try:
            self.logger.info("Stopping AuraTrade Bot...")
            self.running = False
            
            # Stop trading engine
            if self.trading_engine:
                self.trading_engine.stop()
            
            # Close all positions if emergency stop
            if self.order_manager:
                self.order_manager.emergency_stop()
            
            # Send shutdown notification
            if self.notifier:
                self.notifier.send_message("🛑 AuraTrade Bot Stopped")
            
            # Disconnect MT5
            if self.mt5_connector:
                self.mt5_connector.disconnect()
            
            self.logger.info("Bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def run(self):
        """Main execution method"""
        try:
            self.logger.info("Starting AuraTrade Bot...")
            
            # Initialize components
            if not self.initialize_components():
                self.logger.error("Failed to initialize components")
                return False
            
            # Initialize GUI
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
            
            # Show main window
            self.main_window.show()
            
            # Start GUI event loop
            return self.app.exec_()
            
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
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
