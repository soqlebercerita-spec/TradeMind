
"""
AuraTrade Bot - Advanced Automated Trading System
Multi-strategy trading bot with risk management and GUI
"""

import sys
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Core imports
try:
    from core.mt5_connector import MT5Connector
    from core.order_manager import OrderManager
    from core.risk_manager import RiskManager
    from core.position_sizing import PositionSizing
    from core.trading_engine import TradingEngine
    from core.portfolio import Portfolio
except ImportError as e:
    print(f"Error importing core modules: {e}")
    sys.exit(1)

# Strategy imports
try:
    from strategies.scalping_strategy import ScalpingStrategy
    from strategies.hft_strategy import HFTStrategy
    from strategies.pattern_strategy import PatternStrategy
    from strategies.swing_strategy import SwingStrategy
    from strategies.arbitrage_strategy import ArbitrageStrategy
except ImportError as e:
    print(f"Error importing strategies: {e}")
    print("Some strategies may not be available")

# Analysis imports
try:
    from analysis.technical_analysis import TechnicalAnalysis
    from analysis.pattern_recognition import PatternRecognition
except ImportError as e:
    print(f"Error importing analysis modules: {e}")
    sys.exit(1)

# Data and utilities
try:
    from data.data_manager import DataManager
    from utils.logger import Logger, log_system, log_error
    from utils.notifier import TelegramNotifier
    from utils.ml_engine import MLEngine
    from config.config import Config
    from config.credentials import Credentials
    from config.settings import Settings
except ImportError as e:
    print(f"Error importing data/utility modules: {e}")
    sys.exit(1)

# GUI imports (optional)
try:
    from gui.main_window import MainWindow
    from PyQt5.QtWidgets import QApplication
    GUI_AVAILABLE = True
except ImportError as e:
    print(f"GUI not available: {e}")
    GUI_AVAILABLE = False

class AuraTradeBot:
    """Main AuraTrade Bot class"""
    
    def __init__(self):
        """Initialize the trading bot"""
        print("🚀 Initializing AuraTrade Bot...")
        
        # Initialize logger first
        self.logger = Logger().get_logger()
        self.logger.info("AuraTrade Bot starting up...")
        
        # Initialize configuration
        try:
            self.config = Config()
            self.credentials = Credentials()
            self.settings = Settings()
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise
        
        # Validate credentials
        if not self.credentials.validate_mt5_credentials():
            self.logger.warning("MT5 credentials not configured. Please set up .env file")
        
        # Initialize core components
        self.mt5_connector = None
        self.order_manager = None
        self.risk_manager = None
        self.position_sizing = None
        self.portfolio = None
        self.data_manager = None
        self.trading_engine = None
        
        # Initialize analysis components
        self.technical_analysis = None
        self.pattern_recognition = None
        self.ml_engine = None
        
        # Initialize utilities
        self.notifier = None
        
        # Initialize strategies
        self.strategies = {}
        
        # GUI components
        self.gui_app = None
        self.main_window = None
        
        # Bot state
        self.running = False
        self.startup_complete = False
        
        # Initialize all components
        self._initialize_components()
        
        log_system("AuraTrade Bot initialized successfully")
    
    def _initialize_components(self):
        """Initialize all bot components"""
        try:
            # Initialize MT5 connector
            self.logger.info("Initializing MT5 connector...")
            self.mt5_connector = MT5Connector(self.credentials.get_mt5_credentials())
            
            # Initialize order manager
            self.logger.info("Initializing order manager...")
            self.order_manager = OrderManager(self.mt5_connector)
            
            # Initialize risk manager
            self.logger.info("Initializing risk manager...")
            self.risk_manager = RiskManager(self.mt5_connector)
            
            # Initialize position sizing
            self.logger.info("Initializing position sizing...")
            self.position_sizing = PositionSizing(self.mt5_connector)
            
            # Initialize portfolio
            self.logger.info("Initializing portfolio manager...")
            self.portfolio = Portfolio(self.mt5_connector)
            
            # Initialize data manager
            self.logger.info("Initializing data manager...")
            self.data_manager = DataManager(self.mt5_connector)
            
            # Initialize analysis components
            self.logger.info("Initializing technical analysis...")
            self.technical_analysis = TechnicalAnalysis()
            
            self.logger.info("Initializing pattern recognition...")
            self.pattern_recognition = PatternRecognition()
            
            # Initialize ML engine
            self.logger.info("Initializing ML engine...")
            try:
                self.ml_engine = MLEngine()
            except Exception as e:
                self.logger.warning(f"ML engine initialization failed: {e}")
                self.ml_engine = None
            
            # Initialize notifier
            self.logger.info("Initializing notifier...")
            self.notifier = TelegramNotifier(self.credentials.get_telegram_credentials())
            
            # Initialize strategies
            self._initialize_strategies()
            
            # Initialize trading engine
            self.logger.info("Initializing trading engine...")
            self.trading_engine = TradingEngine(
                mt5_connector=self.mt5_connector,
                order_manager=self.order_manager,
                risk_manager=self.risk_manager,
                position_sizing=self.position_sizing,
                data_manager=self.data_manager,
                ml_engine=self.ml_engine,
                notifier=self.notifier,
                strategies=self.strategies,
                technical_analysis=self.technical_analysis
            )
            
            self.startup_complete = True
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def _initialize_strategies(self):
        """Initialize trading strategies"""
        try:
            self.logger.info("Initializing trading strategies...")
            
            # Initialize available strategies
            strategy_classes = {
                'scalping': ScalpingStrategy,
                'hft': HFTStrategy,
                'pattern': PatternStrategy,
                'swing': SwingStrategy,
                'arbitrage': ArbitrageStrategy
            }
            
            for name, strategy_class in strategy_classes.items():
                try:
                    self.strategies[name] = strategy_class()
                    self.logger.info(f"Strategy '{name}' initialized successfully")
                except Exception as e:
                    self.logger.error(f"Error initializing {name} strategy: {e}")
            
            if not self.strategies:
                raise Exception("No strategies could be initialized")
            
            self.logger.info(f"Initialized {len(self.strategies)} strategies: {list(self.strategies.keys())}")
            
        except Exception as e:
            self.logger.error(f"Error initializing strategies: {e}")
            raise
    
    def start(self, gui_mode: bool = True):
        """Start the trading bot"""
        try:
            if not self.startup_complete:
                raise Exception("Bot not properly initialized")
            
            self.logger.info("Starting AuraTrade Bot...")
            
            # Test MT5 connection
            if not self.mt5_connector.check_connection():
                self.logger.info("Attempting to connect to MT5...")
                if not self.mt5_connector.connect():
                    raise Exception("Failed to connect to MT5")
            
            self.running = True
            
            # Send startup notification
            if self.notifier and self.notifier.enabled:
                account_info = self.mt5_connector.get_account_info()
                balance = account_info.get('balance', 0) if account_info else 0
                self.notifier.send_system_status(
                    "started",
                    f"🚀 AuraTrade Bot Started\n"
                    f"Account Balance: ${balance:.2f}\n"
                    f"Strategies: {len(self.strategies)}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            # Start GUI if available and requested
            if gui_mode and GUI_AVAILABLE:
                self._start_gui()
            else:
                self._start_console_mode()
                
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            log_error(str(e))
            raise
    
    def _start_gui(self):
        """Start bot with GUI"""
        try:
            self.logger.info("Starting GUI mode...")
            
            # Create QApplication
            self.gui_app = QApplication(sys.argv)
            self.gui_app.setApplicationName("AuraTrade Bot")
            
            # Create main window
            self.main_window = MainWindow(
                mt5_connector=self.mt5_connector,
                trading_engine=self.trading_engine,
                order_manager=self.order_manager,
                portfolio=self.portfolio,
                strategies=self.strategies,
                technical_analysis=self.technical_analysis,
                data_manager=self.data_manager
            )
            
            # Show main window
            self.main_window.show()
            
            # Start trading engine in background thread
            self._start_trading_engine()
            
            # Run GUI event loop
            self.logger.info("Starting GUI event loop...")
            sys.exit(self.gui_app.exec_())
            
        except Exception as e:
            self.logger.error(f"Error starting GUI: {e}")
            self._start_console_mode()
    
    def _start_console_mode(self):
        """Start bot in console mode"""
        try:
            self.logger.info("Starting console mode...")
            
            # Start trading engine
            self._start_trading_engine()
            
            # Console interface loop
            self._console_interface()
            
        except Exception as e:
            self.logger.error(f"Error in console mode: {e}")
            raise
    
    def _start_trading_engine(self):
        """Start the trading engine in a separate thread"""
        try:
            self.logger.info("Starting trading engine...")
            
            # Start trading engine
            self.trading_engine.start()
            
            # Start portfolio updates
            self._start_portfolio_updates()
            
            self.logger.info("Trading engine started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting trading engine: {e}")
            raise
    
    def _start_portfolio_updates(self):
        """Start portfolio update thread"""
        def update_portfolio():
            while self.running:
                try:
                    if self.portfolio:
                        self.portfolio.update_portfolio()
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    self.logger.error(f"Error updating portfolio: {e}")
                    time.sleep(5)
        
        portfolio_thread = threading.Thread(target=update_portfolio, daemon=True)
        portfolio_thread.start()
    
    def _console_interface(self):
        """Console interface for bot control"""
        try:
            print("\n" + "="*60)
            print("🤖 AURATRADE BOT - CONSOLE INTERFACE")
            print("="*60)
            print("Commands:")
            print("  start   - Start trading")
            print("  stop    - Stop trading")
            print("  status  - Show bot status")
            print("  stats   - Show trading statistics")
            print("  balance - Show account balance")
            print("  positions - Show open positions")
            print("  help    - Show this help")
            print("  quit    - Exit bot")
            print("="*60)
            
            while self.running:
                try:
                    command = input("\nAuraTrade> ").strip().lower()
                    
                    if command == 'quit' or command == 'exit':
                        break
                    elif command == 'start':
                        if hasattr(self.trading_engine, 'start'):
                            self.trading_engine.start()
                            print("✅ Trading started")
                    elif command == 'stop':
                        if hasattr(self.trading_engine, 'stop'):
                            self.trading_engine.stop()
                            print("🛑 Trading stopped")
                    elif command == 'status':
                        self._show_status()
                    elif command == 'stats':
                        self._show_statistics()
                    elif command == 'balance':
                        self._show_balance()
                    elif command == 'positions':
                        self._show_positions()
                    elif command == 'help':
                        print("Available commands: start, stop, status, stats, balance, positions, help, quit")
                    elif command == '':
                        continue
                    else:
                        print(f"Unknown command: {command}. Type 'help' for available commands.")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Error in console interface: {e}")
                    print(f"Error: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in console interface: {e}")
        finally:
            self.stop()
    
    def _show_status(self):
        """Show bot status"""
        try:
            print("\n📊 BOT STATUS")
            print("-" * 40)
            
            # MT5 connection
            connected = self.mt5_connector.check_connection()
            print(f"MT5 Connection: {'✅ Connected' if connected else '❌ Disconnected'}")
            
            # Trading engine status
            if hasattr(self.trading_engine, 'get_status'):
                status = self.trading_engine.get_status()
                print(f"Trading Engine: {'✅ Running' if status.get('running', False) else '❌ Stopped'}")
                print(f"Active Strategy: {status.get('active_strategy', 'None')}")
                print(f"Trades Today: {status.get('trades_today', 0)}")
                print(f"Win Rate: {status.get('win_rate', 0):.1f}%")
            
            # Account info
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                print(f"Account Balance: ${account_info.get('balance', 0):.2f}")
                print(f"Account Equity: ${account_info.get('equity', 0):.2f}")
                print(f"Margin Level: {account_info.get('margin_level', 0):.1f}%")
            
        except Exception as e:
            print(f"Error showing status: {e}")
    
    def _show_statistics(self):
        """Show trading statistics"""
        try:
            print("\n📈 TRADING STATISTICS")
            print("-" * 40)
            
            if self.portfolio:
                metrics = self.portfolio.get_performance_metrics()
                daily_stats = self.portfolio.get_daily_stats()
                
                print(f"Total Trades: {metrics.get('total_trades', 0)}")
                print(f"Winning Trades: {metrics.get('winning_trades', 0)}")
                print(f"Losing Trades: {metrics.get('losing_trades', 0)}")
                print(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
                print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
                print(f"Total Profit: ${metrics.get('total_profit', 0):.2f}")
                print(f"Total Loss: ${metrics.get('total_loss', 0):.2f}")
                print(f"Net Profit: ${metrics.get('net_profit', 0):.2f}")
                print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
                
                print(f"\nToday's Performance:")
                print(f"Trades Today: {daily_stats.get('trades_today', 0)}")
                print(f"Profit Today: ${daily_stats.get('profit_today', 0):.2f}")
                print(f"Win Rate Today: {daily_stats.get('win_rate_today', 0):.1f}%")
            
        except Exception as e:
            print(f"Error showing statistics: {e}")
    
    def _show_balance(self):
        """Show account balance"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                print(f"\n💰 ACCOUNT BALANCE")
                print("-" * 40)
                print(f"Balance: ${account_info.get('balance', 0):.2f}")
                print(f"Equity: ${account_info.get('equity', 0):.2f}")
                print(f"Margin: ${account_info.get('margin', 0):.2f}")
                print(f"Free Margin: ${account_info.get('margin_free', 0):.2f}")
                print(f"Margin Level: {account_info.get('margin_level', 0):.1f}%")
            else:
                print("❌ Unable to retrieve account information")
                
        except Exception as e:
            print(f"Error showing balance: {e}")
    
    def _show_positions(self):
        """Show open positions"""
        try:
            positions = self.mt5_connector.get_positions()
            
            print(f"\n📋 OPEN POSITIONS ({len(positions)})")
            print("-" * 80)
            
            if not positions:
                print("No open positions")
                return
            
            print(f"{'Ticket':<10} {'Symbol':<8} {'Type':<4} {'Volume':<8} {'Price':<10} {'Profit':<10}")
            print("-" * 80)
            
            for pos in positions:
                ticket = str(pos.get('ticket', ''))
                symbol = pos.get('symbol', '')
                pos_type = 'BUY' if pos.get('type', 0) == 0 else 'SELL'
                volume = f"{pos.get('volume', 0):.2f}"
                price = f"{pos.get('price_open', 0):.5f}"
                profit = f"${pos.get('profit', 0):.2f}"
                
                print(f"{ticket:<10} {symbol:<8} {pos_type:<4} {volume:<8} {price:<10} {profit:<10}")
                
        except Exception as e:
            print(f"Error showing positions: {e}")
    
    def stop(self):
        """Stop the trading bot"""
        try:
            self.logger.info("Stopping AuraTrade Bot...")
            self.running = False
            
            # Stop trading engine
            if self.trading_engine:
                self.trading_engine.stop()
            
            # Disconnect from MT5
            if self.mt5_connector:
                self.mt5_connector.disconnect()
            
            # Send notification
            if self.notifier and self.notifier.enabled:
                final_stats = ""
                if self.portfolio:
                    metrics = self.portfolio.get_performance_metrics()
                    final_stats = f"\nFinal Stats:\nTrades: {metrics.get('total_trades', 0)}\nWin Rate: {metrics.get('win_rate', 0):.1f}%\nNet Profit: ${metrics.get('net_profit', 0):.2f}"
                
                self.notifier.send_system_status(
                    "stopped",
                    f"🛑 AuraTrade Bot Stopped{final_stats}"
                )
            
            log_system("AuraTrade Bot stopped successfully")
            print("\n✅ AuraTrade Bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
            print(f"❌ Error stopping bot: {e}")

def main():
    """Main entry point"""
    try:
        print("🚀 AuraTrade Bot - Advanced Trading System")
        print("=" * 50)
        
        # Check for command line arguments
        gui_mode = True
        if len(sys.argv) > 1:
            if '--console' in sys.argv or '--no-gui' in sys.argv:
                gui_mode = False
        
        # Create and start bot
        bot = AuraTradeBot()
        bot.start(gui_mode=gui_mode)
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        log_error(str(e))
    finally:
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
