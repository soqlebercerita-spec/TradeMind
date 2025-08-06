
"""
Main GUI Window for AuraTrade Bot
Modern, user-friendly interface with all required features
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox,
                            QDoubleSpinBox, QTextEdit, QTableWidget, QTableWidgetItem,
                            QGroupBox, QProgressBar, QTabWidget, QMessageBox, QFrame,
                            QScrollArea, QCheckBox)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap
from datetime import datetime, timedelta
import pandas as pd
import csv
import os
from typing import Dict, List, Any, Optional

from utils.logger import Logger
from gui.dashboard import TradingDashboard

class MainWindow(QMainWindow):
    """Modern main window for AuraTrade Bot"""
    
    def __init__(self, trading_engine, order_manager, risk_manager, data_manager):
        super().__init__()
        self.logger = Logger().get_logger()
        
        # Core components
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.data_manager = data_manager
        
        # GUI state
        self.bot_running = False
        self.current_positions = []
        self.trade_history = []
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        self.setup_ui()
        self.apply_modern_theme()
        self.logger.info("Main GUI window initialized")
    
    def setup_ui(self):
        """Setup the complete user interface"""
        self.setWindowTitle("AuraTrade Bot v2.0 - Professional Trading System")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_control_tab()
        self.create_monitoring_tab()
        self.create_strategy_tab()
        self.create_history_tab()
        self.create_settings_tab()
        
        # Status bar
        self.statusBar().showMessage("AuraTrade Bot Ready - Target: 75%+ Win Rate")
        
    def create_control_tab(self):
        """Create main control tab"""
        control_widget = QWidget()
        layout = QGridLayout(control_widget)
        
        # Bot Control Section
        bot_control_group = QGroupBox("🤖 Bot Control")
        bot_control_layout = QVBoxLayout(bot_control_group)
        
        # Start/Stop buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("🚀 START BOT")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_bot)
        self.start_button.setMinimumHeight(50)
        
        self.stop_button = QPushButton("⛔ STOP BOT")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(50)
        
        self.emergency_stop = QPushButton("🚨 EMERGENCY STOP")
        self.emergency_stop.setObjectName("emergencyButton")
        self.emergency_stop.clicked.connect(self.emergency_stop_all)
        self.emergency_stop.setMinimumHeight(50)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.emergency_stop)
        bot_control_layout.addLayout(button_layout)
        
        # Strategy Selection
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("Strategy:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["Scalping", "HFT", "Pattern", "Hybrid"])
        self.strategy_combo.setCurrentText("Scalping")
        strategy_layout.addWidget(self.strategy_combo)
        
        strategy_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1"])
        self.timeframe_combo.setCurrentText("M1")
        strategy_layout.addWidget(self.timeframe_combo)
        
        strategy_layout.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"])
        self.symbol_combo.setCurrentText("EURUSD")
        strategy_layout.addWidget(self.symbol_combo)
        
        bot_control_layout.addLayout(strategy_layout)
        
        # TP/SL Settings
        tp_sl_layout = QHBoxLayout()
        tp_sl_layout.addWidget(QLabel("TP (pips):"))
        self.tp_spin = QSpinBox()
        self.tp_spin.setRange(5, 500)
        self.tp_spin.setValue(40)
        tp_sl_layout.addWidget(self.tp_spin)
        
        tp_sl_layout.addWidget(QLabel("SL (pips):"))
        self.sl_spin = QSpinBox()
        self.sl_spin.setRange(5, 200)
        self.sl_spin.setValue(20)
        tp_sl_layout.addWidget(self.sl_spin)
        
        tp_sl_layout.addWidget(QLabel("Max Positions:"))
        self.max_pos_spin = QSpinBox()
        self.max_pos_spin.setRange(1, 10)
        self.max_pos_spin.setValue(5)
        tp_sl_layout.addWidget(self.max_pos_spin)
        
        bot_control_layout.addLayout(tp_sl_layout)
        
        layout.addWidget(bot_control_group, 0, 0)
        
        # Account Info Section
        account_group = QGroupBox("💰 Account Information")
        account_layout = QGridLayout(account_group)
        
        self.balance_label = QLabel("Balance: $0.00")
        self.equity_label = QLabel("Equity: $0.00")
        self.margin_label = QLabel("Free Margin: $0.00")
        self.leverage_label = QLabel("Leverage: 1:100")
        
        account_layout.addWidget(self.balance_label, 0, 0)
        account_layout.addWidget(self.equity_label, 0, 1)
        account_layout.addWidget(self.margin_label, 1, 0)
        account_layout.addWidget(self.leverage_label, 1, 1)
        
        layout.addWidget(account_group, 0, 1)
        
        # Live P&L Section
        pnl_group = QGroupBox("📊 Live Report")
        pnl_layout = QGridLayout(pnl_group)
        
        self.floating_pnl_label = QLabel("Floating P&L: $0.00")
        self.daily_pnl_label = QLabel("Daily P&L: $0.00")
        self.win_rate_label = QLabel("Win Rate: 0.0%")
        self.trades_today_label = QLabel("Trades Today: 0")
        
        pnl_layout.addWidget(self.floating_pnl_label, 0, 0)
        pnl_layout.addWidget(self.daily_pnl_label, 0, 1)
        pnl_layout.addWidget(self.win_rate_label, 1, 0)
        pnl_layout.addWidget(self.trades_today_label, 1, 1)
        
        layout.addWidget(pnl_group, 1, 0)
        
        # Manual Trading Section
        manual_group = QGroupBox("🎯 Manual Trading")
        manual_layout = QHBoxLayout(manual_group)
        
        self.manual_buy_button = QPushButton("📈 BUY")
        self.manual_buy_button.setObjectName("buyButton")
        self.manual_buy_button.clicked.connect(self.manual_buy)
        
        self.manual_sell_button = QPushButton("📉 SELL")
        self.manual_sell_button.setObjectName("sellButton")
        self.manual_sell_button.clicked.connect(self.manual_sell)
        
        self.close_all_button = QPushButton("❌ CLOSE ALL")
        self.close_all_button.setObjectName("closeButton")
        self.close_all_button.clicked.connect(self.close_all_positions)
        
        manual_layout.addWidget(self.manual_buy_button)
        manual_layout.addWidget(self.manual_sell_button)
        manual_layout.addWidget(self.close_all_button)
        
        layout.addWidget(manual_group, 1, 1)
        
        self.tab_widget.addTab(control_widget, "🎛️ Control Panel")
    
    def create_monitoring_tab(self):
        """Create monitoring tab with positions and logs"""
        monitoring_widget = QWidget()
        layout = QVBoxLayout(monitoring_widget)
        
        # Open Positions Table
        positions_group = QGroupBox("📋 Open Positions")
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Volume", "Entry Price", 
            "Current Price", "Profit", "Actions"
        ])
        self.positions_table.setAlternatingRowColors(True)
        positions_layout.addWidget(self.positions_table)
        
        layout.addWidget(positions_group)
        
        # Activity Log
        log_group = QGroupBox("📝 Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        self.clear_log_button = QPushButton("🗑️ Clear Log")
        self.clear_log_button.clicked.connect(self.clear_log)
        self.export_log_button = QPushButton("💾 Export Log")
        self.export_log_button.clicked.connect(self.export_log)
        
        log_controls.addWidget(self.clear_log_button)
        log_controls.addWidget(self.export_log_button)
        log_controls.addStretch()
        
        log_layout.addLayout(log_controls)
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(monitoring_widget, "📊 Monitoring")
    
    def create_strategy_tab(self):
        """Create strategy configuration tab"""
        strategy_widget = QWidget()
        layout = QVBoxLayout(strategy_widget)
        
        # Strategy Settings
        strategy_group = QGroupBox("⚙️ Strategy Configuration")
        strategy_layout = QGridLayout(strategy_group)
        
        # Individual strategy enable/disable
        self.scalping_enabled = QCheckBox("Enable Scalping Strategy")
        self.scalping_enabled.setChecked(True)
        self.hft_enabled = QCheckBox("Enable HFT Strategy") 
        self.hft_enabled.setChecked(True)
        self.pattern_enabled = QCheckBox("Enable Pattern Strategy")
        self.pattern_enabled.setChecked(True)
        
        strategy_layout.addWidget(self.scalping_enabled, 0, 0)
        strategy_layout.addWidget(self.hft_enabled, 0, 1)
        strategy_layout.addWidget(self.pattern_enabled, 0, 2)
        
        # Risk Settings
        risk_layout = QGridLayout()
        risk_layout.addWidget(QLabel("Risk per Trade (%):"), 0, 0)
        self.risk_per_trade = QDoubleSpinBox()
        self.risk_per_trade.setRange(0.1, 5.0)
        self.risk_per_trade.setValue(1.0)
        self.risk_per_trade.setSingleStep(0.1)
        risk_layout.addWidget(self.risk_per_trade, 0, 1)
        
        risk_layout.addWidget(QLabel("Daily Risk Limit (%):"), 1, 0)
        self.daily_risk_limit = QDoubleSpinBox()
        self.daily_risk_limit.setRange(1.0, 20.0)
        self.daily_risk_limit.setValue(5.0)
        risk_layout.addWidget(self.daily_risk_limit, 1, 1)
        
        strategy_layout.addLayout(risk_layout, 1, 0, 1, 3)
        
        layout.addWidget(strategy_group)
        
        # Performance Metrics
        performance_group = QGroupBox("📈 Performance Metrics")
        performance_layout = QGridLayout(performance_group)
        
        self.total_trades_label = QLabel("Total Trades: 0")
        self.profitable_trades_label = QLabel("Profitable: 0")
        self.losing_trades_label = QLabel("Losing: 0")
        self.avg_profit_label = QLabel("Avg Profit: $0.00")
        self.max_drawdown_label = QLabel("Max Drawdown: 0.0%")
        self.sharpe_ratio_label = QLabel("Sharpe Ratio: 0.00")
        
        performance_layout.addWidget(self.total_trades_label, 0, 0)
        performance_layout.addWidget(self.profitable_trades_label, 0, 1)
        performance_layout.addWidget(self.losing_trades_label, 0, 2)
        performance_layout.addWidget(self.avg_profit_label, 1, 0)
        performance_layout.addWidget(self.max_drawdown_label, 1, 1)
        performance_layout.addWidget(self.sharpe_ratio_label, 1, 2)
        
        layout.addWidget(performance_group)
        
        self.tab_widget.addTab(strategy_widget, "🧠 Strategy")
    
    def create_history_tab(self):
        """Create trade history tab"""
        history_widget = QWidget()
        layout = QVBoxLayout(history_widget)
        
        # Trade History Table
        history_group = QGroupBox("📊 Trade History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(10)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Type", "Volume", "Entry", "Exit", 
            "Profit", "Duration", "Strategy", "Comment"
        ])
        self.history_table.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_table)
        
        # History controls
        history_controls = QHBoxLayout()
        self.export_csv_button = QPushButton("📁 Export to CSV")
        self.export_csv_button.clicked.connect(self.export_to_csv)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Today", "This Week", "This Month"])
        
        history_controls.addWidget(QLabel("Filter:"))
        history_controls.addWidget(self.filter_combo)
        history_controls.addStretch()
        history_controls.addWidget(self.export_csv_button)
        
        history_layout.addLayout(history_controls)
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(history_widget, "📋 History")
    
    def create_settings_tab(self):
        """Create settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Connection Settings
        connection_group = QGroupBox("🔌 Connection Settings")
        connection_layout = QGridLayout(connection_group)
        
        self.connection_status = QLabel("Status: Connected")
        self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        connection_layout.addWidget(self.connection_status, 0, 0)
        
        self.reconnect_button = QPushButton("🔄 Reconnect")
        self.reconnect_button.clicked.connect(self.reconnect_mt5)
        connection_layout.addWidget(self.reconnect_button, 0, 1)
        
        layout.addWidget(connection_group)
        
        # Notification Settings
        notification_group = QGroupBox("🔔 Notifications")
        notification_layout = QGridLayout(notification_group)
        
        self.telegram_enabled = QCheckBox("Enable Telegram Notifications")
        self.telegram_enabled.setChecked(True)
        notification_layout.addWidget(self.telegram_enabled, 0, 0)
        
        self.sound_enabled = QCheckBox("Enable Sound Alerts")
        self.sound_enabled.setChecked(True)
        notification_layout.addWidget(self.sound_enabled, 0, 1)
        
        layout.addWidget(notification_group)
        
        # Auto-trading Settings
        auto_group = QGroupBox("🤖 Auto-Trading Settings")
        auto_layout = QGridLayout(auto_group)
        
        self.auto_close_friday = QCheckBox("Auto-close positions on Friday")
        self.auto_close_friday.setChecked(True)
        auto_layout.addWidget(self.auto_close_friday, 0, 0)
        
        self.avoid_news = QCheckBox("Avoid trading during news")
        self.avoid_news.setChecked(True)
        auto_layout.addWidget(self.avoid_news, 0, 1)
        
        layout.addWidget(auto_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "⚙️ Settings")
    
    def apply_modern_theme(self):
        """Apply modern dark theme to the interface"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #2d2d2d;
            }
            
            QTabBar::tab {
                background-color: #3d3d3d;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 100px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton#startButton {
                background-color: #16a085;
            }
            
            QPushButton#startButton:hover {
                background-color: #138d75;
            }
            
            QPushButton#stopButton {
                background-color: #e74c3c;
            }
            
            QPushButton#stopButton:hover {
                background-color: #c0392b;
            }
            
            QPushButton#emergencyButton {
                background-color: #8e44ad;
                font-size: 14px;
            }
            
            QPushButton#emergencyButton:hover {
                background-color: #7d3c98;
            }
            
            QPushButton#buyButton {
                background-color: #27ae60;
            }
            
            QPushButton#buyButton:hover {
                background-color: #229954;
            }
            
            QPushButton#sellButton {
                background-color: #e74c3c;
            }
            
            QPushButton#sellButton:hover {
                background-color: #c0392b;
            }
            
            QPushButton#closeButton {
                background-color: #f39c12;
            }
            
            QPushButton#closeButton:hover {
                background-color: #e67e22;
            }
            
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                min-width: 100px;
            }
            
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #3d3d3d;
                color: #ffffff;
                gridline-color: #555555;
                border: 1px solid #3d3d3d;
            }
            
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-family: Consolas, Monaco, monospace;
            }
            
            QCheckBox {
                color: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            
            QStatusBar {
                background-color: #3d3d3d;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
        """)
    
    def start_bot(self):
        """Start the trading bot"""
        try:
            if not self.bot_running:
                success = self.trading_engine.start()
                if success:
                    self.bot_running = True
                    self.start_button.setEnabled(False)
                    self.stop_button.setEnabled(True)
                    self.log_message("✅ Bot started successfully")
                    self.statusBar().showMessage("Bot Running - Trading Active")
                else:
                    self.log_message("❌ Failed to start bot")
                    QMessageBox.critical(self, "Error", "Failed to start trading bot")
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            QMessageBox.critical(self, "Error", f"Error starting bot: {e}")
    
    def stop_bot(self):
        """Stop the trading bot"""
        try:
            if self.bot_running:
                self.trading_engine.stop()
                self.bot_running = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.log_message("⛔ Bot stopped")
                self.statusBar().showMessage("Bot Stopped - Ready to Start")
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
    
    def emergency_stop_all(self):
        """Emergency stop all trading"""
        reply = QMessageBox.question(
            self, 'Emergency Stop', 
            'This will immediately stop all trading and close all positions.\nContinue?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Stop bot
                if self.bot_running:
                    self.trading_engine.stop()
                    self.bot_running = False
                
                # Close all positions
                self.order_manager.emergency_close_all()
                
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.log_message("🚨 EMERGENCY STOP - All positions closed")
                self.statusBar().showMessage("Emergency Stop Executed")
                
            except Exception as e:
                self.logger.error(f"Error in emergency stop: {e}")
    
    def manual_buy(self):
        """Manual buy order"""
        try:
            symbol = self.symbol_combo.currentText()
            volume = 0.01  # Fixed volume for manual trades
            
            result = self.order_manager.place_market_order(
                symbol=symbol,
                action='buy',
                volume=volume,
                sl_pips=self.sl_spin.value(),
                tp_pips=self.tp_spin.value(),
                comment="Manual_BUY"
            )
            
            if result and result.get('retcode') == 10009:
                self.log_message(f"📈 Manual BUY: {volume} {symbol}")
            else:
                self.log_message(f"❌ Manual BUY failed: {symbol}")
                
        except Exception as e:
            self.logger.error(f"Error in manual buy: {e}")
    
    def manual_sell(self):
        """Manual sell order"""
        try:
            symbol = self.symbol_combo.currentText()
            volume = 0.01
            
            result = self.order_manager.place_market_order(
                symbol=symbol,
                action='sell',
                volume=volume,
                sl_pips=self.sl_spin.value(),
                tp_pips=self.tp_spin.value(),
                comment="Manual_SELL"
            )
            
            if result and result.get('retcode') == 10009:
                self.log_message(f"📉 Manual SELL: {volume} {symbol}")
            else:
                self.log_message(f"❌ Manual SELL failed: {symbol}")
                
        except Exception as e:
            self.logger.error(f"Error in manual sell: {e}")
    
    def close_all_positions(self):
        """Close all open positions"""
        reply = QMessageBox.question(
            self, 'Close All Positions', 
            'Close all open positions?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                closed_count = self.order_manager.close_all_orders()
                self.log_message(f"❌ Closed {closed_count} positions")
            except Exception as e:
                self.logger.error(f"Error closing all positions: {e}")
    
    def update_display(self):
        """Update all display elements"""
        try:
            self.update_account_info()
            self.update_positions_table()
            self.update_performance_metrics()
            self.update_connection_status()
        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
    
    def update_account_info(self):
        """Update account information display"""
        try:
            if hasattr(self.trading_engine, 'mt5_connector'):
                account_info = self.trading_engine.mt5_connector.get_account_info()
                
                self.balance_label.setText(f"Balance: ${account_info.get('balance', 0):.2f}")
                self.equity_label.setText(f"Equity: ${account_info.get('equity', 0):.2f}")
                self.margin_label.setText(f"Free Margin: ${account_info.get('free_margin', 0):.2f}")
                self.leverage_label.setText(f"Leverage: 1:{account_info.get('leverage', 100)}")
                
                # Update P&L
                profit = account_info.get('profit', 0)
                self.floating_pnl_label.setText(f"Floating P&L: ${profit:.2f}")
                
                # Update daily stats
                if hasattr(self.trading_engine, 'stats'):
                    stats = self.trading_engine.stats
                    self.daily_pnl_label.setText(f"Daily P&L: ${stats.get('daily_pnl', 0):.2f}")
                    self.win_rate_label.setText(f"Win Rate: {stats.get('win_rate', 0):.1f}%")
                    self.trades_today_label.setText(f"Trades Today: {stats.get('trades_today', 0)}")
                    
        except Exception as e:
            self.logger.error(f"Error updating account info: {e}")
    
    def update_positions_table(self):
        """Update positions table"""
        try:
            if hasattr(self.trading_engine, 'mt5_connector'):
                positions = self.trading_engine.mt5_connector.get_positions()
                
                self.positions_table.setRowCount(len(positions))
                
                for i, position in enumerate(positions):
                    self.positions_table.setItem(i, 0, QTableWidgetItem(str(position.get('ticket', ''))))
                    self.positions_table.setItem(i, 1, QTableWidgetItem(position.get('symbol', '')))
                    self.positions_table.setItem(i, 2, QTableWidgetItem("BUY" if position.get('type') == 0 else "SELL"))
                    self.positions_table.setItem(i, 3, QTableWidgetItem(f"{position.get('volume', 0):.2f}"))
                    self.positions_table.setItem(i, 4, QTableWidgetItem(f"{position.get('price_open', 0):.5f}"))
                    self.positions_table.setItem(i, 5, QTableWidgetItem(f"{position.get('price_current', 0):.5f}"))
                    
                    # Color profit/loss
                    profit = position.get('profit', 0)
                    profit_item = QTableWidgetItem(f"${profit:.2f}")
                    if profit >= 0:
                        profit_item.setForeground(QColor('#27ae60'))
                    else:
                        profit_item.setForeground(QColor('#e74c3c'))
                    self.positions_table.setItem(i, 6, profit_item)
                    
                    # Close button
                    close_button = QPushButton("Close")
                    close_button.clicked.connect(lambda checked, ticket=position.get('ticket'): self.close_position(ticket))
                    self.positions_table.setCellWidget(i, 7, close_button)
                    
        except Exception as e:
            self.logger.error(f"Error updating positions table: {e}")
    
    def update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # This would be implemented with actual trading history analysis
            # For now, showing placeholder values
            pass
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def update_connection_status(self):
        """Update connection status"""
        try:
            if hasattr(self.trading_engine, 'mt5_connector'):
                connected = self.trading_engine.mt5_connector.check_connection()
                if connected:
                    self.connection_status.setText("Status: Connected")
                    self.connection_status.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.connection_status.setText("Status: Disconnected")
                    self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        except Exception as e:
            self.logger.error(f"Error updating connection status: {e}")
    
    def close_position(self, ticket: int):
        """Close specific position"""
        try:
            result = self.trading_engine.mt5_connector.close_position(ticket)
            if result and result.get('retcode') == 10009:
                self.log_message(f"✅ Position #{ticket} closed")
            else:
                self.log_message(f"❌ Failed to close position #{ticket}")
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
    
    def log_message(self, message: str):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.log_text.append(full_message)
        
        # Keep log size manageable
        if self.log_text.document().blockCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
            cursor.removeSelectedText()
    
    def clear_log(self):
        """Clear activity log"""
        self.log_text.clear()
        self.log_message("📝 Log cleared")
    
    def export_log(self):
        """Export activity log to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AuraTrade_log_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(self.log_text.toPlainText())
            
            self.log_message(f"💾 Log exported to {filename}")
            QMessageBox.information(self, "Export Complete", f"Log exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting log: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export log: {e}")
    
    def export_to_csv(self):
        """Export trade history to CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AuraTrade_history_{timestamp}.csv"
            
            # Get trade history from order manager
            if hasattr(self.order_manager, 'get_order_history'):
                history = self.order_manager.get_order_history()
                
                if history:
                    with open(filename, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Timestamp', 'Symbol', 'Action', 'Volume', 'Entry Price', 'Profit', 'Strategy', 'Comment'])
                        
                        for trade in history:
                            writer.writerow([
                                trade.get('timestamp', ''),
                                trade.get('symbol', ''),
                                trade.get('action', ''),
                                trade.get('volume', ''),
                                trade.get('entry_price', ''),
                                trade.get('profit', 0),
                                trade.get('strategy', ''),
                                trade.get('comment', '')
                            ])
                    
                    self.log_message(f"📁 Trade history exported to {filename}")
                    QMessageBox.information(self, "Export Complete", f"Trade history exported to {filename}")
                else:
                    QMessageBox.information(self, "No Data", "No trade history available to export")
            else:
                QMessageBox.warning(self, "Export Error", "Trade history not available")
                
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")
    
    def reconnect_mt5(self):
        """Reconnect to MT5"""
        try:
            if hasattr(self.trading_engine, 'mt5_connector'):
                success = self.trading_engine.mt5_connector.reconnect()
                if success:
                    self.log_message("🔄 Reconnected to MT5")
                else:
                    self.log_message("❌ Failed to reconnect to MT5")
        except Exception as e:
            self.logger.error(f"Error reconnecting: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.bot_running:
            reply = QMessageBox.question(
                self, 'Close Application',
                'Trading bot is still running. Stop bot before closing?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.stop_bot()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
