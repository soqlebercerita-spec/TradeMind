
#!/usr/bin/env python3
"""
AuraTrade Bot - Main Launcher
Institutional Trading Bot with MT5 Integration
"""

import sys
import os
import asyncio
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from config.credentials import Credentials
from config.settings import Settings
from core.trading_engine import TradingEngine
from gui.main_window import MainWindow
from utils.logger import Logger
from utils.notifier import Notifier

class AuraTradeBot:
    """Main AuraTrade Bot orchestrator"""
    
    def __init__(self):
        self.config = Config()
        self.credentials = Credentials()
        self.settings = Settings()
        self.logger = Logger("AuraTradeBot")
        self.notifier = Notifier()
        self.trading_engine = None
        self.gui = None
        
    def initialize(self):
        """Initialize all bot components"""
        try:
            self.logger.info("🚀 Starting AuraTrade Bot...")
            
            # Validate credentials
            if not self.credentials.is_mt5_configured():
                self.logger.error("❌ MT5 credentials not configured!")
                missing = self.credentials.get_missing_credentials()
                self.logger.error(f"Missing: {missing}")
                return False
            
            # Initialize trading engine
            self.trading_engine = TradingEngine()
            if not self.trading_engine.initialize():
                self.logger.error("❌ Failed to initialize trading engine!")
                return False
            
            self.logger.info("✅ AuraTrade Bot initialized successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False
    
    def start_gui(self):
        """Start GUI application"""
        try:
            app = QApplication(sys.argv)
            app.setApplicationName("AuraTrade Bot")
            
            self.gui = MainWindow(self.trading_engine)
            self.gui.show()
            
            # Start trading engine in background
            if self.trading_engine:
                engine_thread = threading.Thread(target=self.trading_engine.start)
                engine_thread.daemon = True
                engine_thread.start()
            
            return app.exec_()
            
        except Exception as e:
            self.logger.error(f"❌ GUI startup failed: {e}")
            return 1
    
    def run(self):
        """Main bot execution"""
        if not self.initialize():
            return 1
        
        # Send startup notification
        self.notifier.send_message("🚀 AuraTrade Bot Started Successfully!")
        
        # Start GUI
        return self.start_gui()

def main():
    """Main entry point"""
    bot = AuraTradeBot()
    exit_code = bot.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
