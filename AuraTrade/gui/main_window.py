
"""
Professional GUI for AuraTrade Bot
Modern PyQt5 interface with real-time updates
"""

import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
                            QTabWidget, QGridLayout, QGroupBox, QProgressBar, QLineEdit,
                            QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QSystemTrayIcon, QMenu, QAction, QSplitter, QFrame)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon

from utils.logger import Logger

class StatusUpdateThread(QThread):
    """Thread for updating GUI status"""
    status_updated = pyqtSignal(dict)
    
    def __init__(self, trading_engine, order_manager, risk_manager, data_manager):
        super().__init__()
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.data_manager = data_manager
        self.running = True
    
    def run(self):
        while self.running:
            try:
                status = {}
                
                # Get trading engine status
                if self.trading_engine:
                    status.update(self.trading_engine.get_status())
                
                # Get risk metrics
                if self.risk_manager:
                    status['risk_metrics'] = self.risk_manager.get_risk_metrics()
                
                # Get active positions
                if self.order_manager:
                    status['positions'] = self.order_manager.get_active_orders()
                
                self.status_updated.emit(status)
                self.msleep(1000)  # Update every second
                
            except Exception as e:
                print(f"Error in status update: {e}")
                self.msleep(5000)
    
    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    """Professional main window for AuraTrade Bot"""

    def __init__(self, trading_engine, order_manager, risk_manager, data_manager):
        super().__init__()
        self.logger = Logger().get_logger()
        
        # Core components
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.data_manager = data_manager
        
        # GUI state
        self.is_trading = False
        self.status_thread = None
        
        # Initialize UI
        self.init_ui()
        self.setup_system_tray()
        self.start_status_updates()
        
        self.logger.info("Main window initialized")

    def init_ui(self):
        """Initialize user interface"""
        try:
            self.setWindowTitle("AuraTrade Bot v2.0 - Professional Trading System")
            self.setGeometry(100, 100, 1400, 900)
            self.setMinimumSize(1200, 800)
            
            # Set dark theme
            self.set_dark_theme()
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QHBoxLayout(central_widget)
            
            # Create splitter for resizable panels
            splitter = QSplitter(Qt.Horizontal)
            main_layout.addWidget(splitter)
            
            # Left panel (controls and info)
            left_panel = self.create_left_panel()
            splitter.addWidget(left_panel)
            
            # Right panel (data and logs)
            right_panel = self.create_right_panel()
            splitter.addWidget(right_panel)
            
            # Set splitter proportions
            splitter.setSizes([500, 900])
            
            # Status bar
            self.statusBar().showMessage("AuraTrade Bot Ready - Target: 75%+ Win Rate")
            
            self.logger.info("UI initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing UI: {e}")

    def create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Bot control section
        control_group = QGroupBox("Bot Control")
        control_layout = QVBoxLayout(control_group)
        
        # Start/Stop buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 Start Trading")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.start_button.clicked.connect(self.start_trading)
        
        self.stop_button = QPushButton("⛔ Stop Trading")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.stop_button.clicked.connect(self.stop_trading)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        control_layout.addLayout(button_layout)
        
        # Emergency stop
        self.emergency_button = QPushButton("🛑 EMERGENCY STOP")
        self.emergency_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        self.emergency_button.clicked.connect(self.emergency_stop)
        control_layout.addWidget(self.emergency_button)
        
        layout.addWidget(control_group)
        
        # Account info section
        account_group = QGroupBox("Account Information")
        account_layout = QGridLayout(account_group)
        
        self.balance_label = QLabel("Balance: $0.00")
        self.equity_label = QLabel("Equity: $0.00")
        self.margin_label = QLabel("Margin: $0.00")
        self.free_margin_label = QLabel("Free Margin: $0.00")
        
        account_layout.addWidget(QLabel("💰"), 0, 0)
        account_layout.addWidget(self.balance_label, 0, 1)
        account_layout.addWidget(QLabel("💎"), 1, 0)
        account_layout.addWidget(self.equity_label, 1, 1)
        account_layout.addWidget(QLabel("📊"), 2, 0)
        account_layout.addWidget(self.margin_label, 2, 1)
        account_layout.addWidget(QLabel("💸"), 3, 0)
        account_layout.addWidget(self.free_margin_label, 3, 1)
        
        layout.addWidget(account_group)
        
        # Performance section
        perf_group = QGroupBox("Performance Metrics")
        perf_layout = QGridLayout(perf_group)
        
        self.trades_today_label = QLabel("Trades Today: 0")
        self.win_rate_label = QLabel("Win Rate: 0.0%")
        self.daily_pnl_label = QLabel("Daily P&L: $0.00")
        self.target_label = QLabel("Target: 75%+ Win Rate")
        
        # Progress bar for win rate
        self.win_rate_progress = QProgressBar()
        self.win_rate_progress.setRange(0, 100)
        self.win_rate_progress.setValue(0)
        self.win_rate_progress.setTextVisible(True)
        
        perf_layout.addWidget(QLabel("📈"), 0, 0)
        perf_layout.addWidget(self.trades_today_label, 0, 1)
        perf_layout.addWidget(QLabel("🎯"), 1, 0)
        perf_layout.addWidget(self.win_rate_label, 1, 1)
        perf_layout.addWidget(self.win_rate_progress, 2, 0, 1, 2)
        perf_layout.addWidget(QLabel("💰"), 3, 0)
        perf_layout.addWidget(self.daily_pnl_label, 3, 1)
        perf_layout.addWidget(QLabel("🎯"), 4, 0)
        perf_layout.addWidget(self.target_label, 4, 1)
        
        layout.addWidget(perf_group)
        
        # Risk management section
        risk_group = QGroupBox("Risk Management")
        risk_layout = QGridLayout(risk_group)
        
        self.drawdown_label = QLabel("Drawdown: 0.0%")
        self.positions_label = QLabel("Positions: 0/5")
        self.exposure_label = QLabel("Exposure: 0.0%")
        
        # Risk progress bars
        self.drawdown_progress = QProgressBar()
        self.drawdown_progress.setRange(0, 100)
        self.drawdown_progress.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #ff4444;
            }
        """)
        
        risk_layout.addWidget(QLabel("⚠️"), 0, 0)
        risk_layout.addWidget(self.drawdown_label, 0, 1)
        risk_layout.addWidget(self.drawdown_progress, 1, 0, 1, 2)
        risk_layout.addWidget(QLabel("📊"), 2, 0)
        risk_layout.addWidget(self.positions_label, 2, 1)
        risk_layout.addWidget(QLabel("💹"), 3, 0)
        risk_layout.addWidget(self.exposure_label, 3, 1)
        
        layout.addWidget(risk_group)
        
        # Strategy settings
        strategy_group = QGroupBox("Strategy Settings")
        strategy_layout = QGridLayout(strategy_group)
        
        self.hft_checkbox = QCheckBox("HFT Strategy")
        self.hft_checkbox.setChecked(True)
        self.scalping_checkbox = QCheckBox("Scalping Strategy")
        self.scalping_checkbox.setChecked(True)
        self.pattern_checkbox = QCheckBox("Pattern Strategy")
        self.pattern_checkbox.setChecked(True)
        self.swing_checkbox = QCheckBox("Swing Strategy")
        self.swing_checkbox.setChecked(True)
        self.arbitrage_checkbox = QCheckBox("Arbitrage Strategy")
        self.arbitrage_checkbox.setChecked(True)
        
        strategy_layout.addWidget(self.hft_checkbox, 0, 0)
        strategy_layout.addWidget(self.scalping_checkbox, 0, 1)
        strategy_layout.addWidget(self.pattern_checkbox, 1, 0)
        strategy_layout.addWidget(self.swing_checkbox, 1, 1)
        strategy_layout.addWidget(self.arbitrage_checkbox, 2, 0, 1, 2)
        
        layout.addWidget(strategy_group)
        
        # Add stretch to push everything up
        layout.addStretch()
        
        return panel

    def create_right_panel(self) -> QWidget:
        """Create right data panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Positions tab
        positions_tab = self.create_positions_tab()
        tab_widget.addTab(positions_tab, "📊 Positions")
        
        # Log tab
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "📋 Logs")
        
        # Market data tab
        market_tab = self.create_market_tab()
        tab_widget.addTab(market_tab, "💹 Market")
        
        # Settings tab
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        layout.addWidget(tab_widget)
        
        return panel

    def create_positions_tab(self) -> QWidget:
        """Create positions table tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Volume", "Price", "Current", "P&L", "Actions"
        ])
        
        # Style the table
        self.positions_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #555;
                background-color: #2b2b2b;
                alternate-background-color: #3b3b3b;
            }
            QHeaderView::section {
                background-color: #404040;
                color: white;
                padding: 8px;
                border: 1px solid #555;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.positions_table)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        close_all_btn = QPushButton("Close All Positions")
        close_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        close_all_btn.clicked.connect(self.close_all_positions)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_positions)
        
        button_layout.addWidget(close_all_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return widget

    def create_log_tab(self) -> QWidget:
        """Create log display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # Limit log size
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #555;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # Log controls
        control_layout = QHBoxLayout()
        
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        
        export_logs_btn = QPushButton("Export Logs")
        export_logs_btn.clicked.connect(self.export_logs)
        
        control_layout.addWidget(clear_logs_btn)
        control_layout.addWidget(export_logs_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        return widget

    def create_market_tab(self) -> QWidget:
        """Create market data tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Market data table
        self.market_table = QTableWidget()
        self.market_table.setColumnCount(6)
        self.market_table.setHorizontalHeaderLabels([
            "Symbol", "Bid", "Ask", "Spread", "Change", "Time"
        ])
        
        # Add some sample data
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        self.market_table.setRowCount(len(symbols))
        
        for i, symbol in enumerate(symbols):
            self.market_table.setItem(i, 0, QTableWidgetItem(symbol))
            self.market_table.setItem(i, 1, QTableWidgetItem("0.00000"))
            self.market_table.setItem(i, 2, QTableWidgetItem("0.00000"))
            self.market_table.setItem(i, 3, QTableWidgetItem("0"))
            self.market_table.setItem(i, 4, QTableWidgetItem("0.00%"))
            self.market_table.setItem(i, 5, QTableWidgetItem("00:00:00"))
        
        layout.addWidget(self.market_table)
        
        return widget

    def create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Risk settings
        risk_group = QGroupBox("Risk Settings")
        risk_layout = QGridLayout(risk_group)
        
        risk_layout.addWidget(QLabel("Max Risk per Trade (%):"), 0, 0)
        self.max_risk_spin = QDoubleSpinBox()
        self.max_risk_spin.setRange(0.1, 10.0)
        self.max_risk_spin.setValue(2.0)
        self.max_risk_spin.setSingleStep(0.1)
        risk_layout.addWidget(self.max_risk_spin, 0, 1)
        
        risk_layout.addWidget(QLabel("Max Daily Risk (%):"), 1, 0)
        self.daily_risk_spin = QDoubleSpinBox()
        self.daily_risk_spin.setRange(1.0, 20.0)
        self.daily_risk_spin.setValue(6.0)
        risk_layout.addWidget(self.daily_risk_spin, 1, 1)
        
        risk_layout.addWidget(QLabel("Max Drawdown (%):"), 2, 0)
        self.drawdown_spin = QDoubleSpinBox()
        self.drawdown_spin.setRange(5.0, 50.0)
        self.drawdown_spin.setValue(10.0)
        risk_layout.addWidget(self.drawdown_spin, 2, 1)
        
        layout.addWidget(risk_group)
        
        # Trading settings
        trading_group = QGroupBox("Trading Settings")
        trading_layout = QGridLayout(trading_group)
        
        trading_layout.addWidget(QLabel("Max Positions:"), 0, 0)
        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 20)
        self.max_positions_spin.setValue(5)
        trading_layout.addWidget(self.max_positions_spin, 0, 1)
        
        trading_layout.addWidget(QLabel("Default Lot Size:"), 1, 0)
        self.lot_size_spin = QDoubleSpinBox()
        self.lot_size_spin.setRange(0.01, 10.0)
        self.lot_size_spin.setValue(0.01)
        self.lot_size_spin.setSingleStep(0.01)
        trading_layout.addWidget(self.lot_size_spin, 1, 1)
        
        layout.addWidget(trading_group)
        
        # Apply settings button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        
        return widget

    def set_dark_theme(self):
        """Set dark theme for the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLabel {
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #404040;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)

    def setup_system_tray(self):
        """Setup system tray icon"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(self)
                
                # Create tray menu
                tray_menu = QMenu()
                
                show_action = QAction("Show", self)
                show_action.triggered.connect(self.show)
                tray_menu.addAction(show_action)
                
                quit_action = QAction("Quit", self)
                quit_action.triggered.connect(self.close)
                tray_menu.addAction(quit_action)
                
                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.show()
                
        except Exception as e:
            self.logger.error(f"Error setting up system tray: {e}")

    def start_status_updates(self):
        """Start status update thread"""
        try:
            self.status_thread = StatusUpdateThread(
                self.trading_engine, self.order_manager, 
                self.risk_manager, self.data_manager
            )
            self.status_thread.status_updated.connect(self.update_status)
            self.status_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting status updates: {e}")

    def update_status(self, status: Dict[str, Any]):
        """Update GUI with latest status"""
        try:
            # Update account info (placeholder - would get from MT5)
            self.balance_label.setText(f"Balance: $10,000.00")
            self.equity_label.setText(f"Equity: $10,000.00")
            self.margin_label.setText(f"Margin: $0.00")
            self.free_margin_label.setText(f"Free Margin: $10,000.00")
            
            # Update performance
            trades_today = status.get('trades_today', 0)
            win_rate = status.get('win_rate', 0.0)
            daily_pnl = status.get('daily_pnl', 0.0)
            
            self.trades_today_label.setText(f"Trades Today: {trades_today}")
            self.win_rate_label.setText(f"Win Rate: {win_rate:.1f}%")
            self.daily_pnl_label.setText(f"Daily P&L: ${daily_pnl:.2f}")
            
            # Update win rate progress
            self.win_rate_progress.setValue(int(win_rate))
            
            # Color code win rate
            if win_rate >= 75:
                self.win_rate_progress.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")
            elif win_rate >= 60:
                self.win_rate_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")
            else:
                self.win_rate_progress.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")
            
            # Update risk metrics
            risk_metrics = status.get('risk_metrics', {})
            drawdown = risk_metrics.get('current_drawdown', 0.0)
            active_positions = len(status.get('positions', []))
            
            self.drawdown_label.setText(f"Drawdown: {drawdown:.1f}%")
            self.positions_label.setText(f"Positions: {active_positions}/5")
            self.drawdown_progress.setValue(int(drawdown))
            
            # Update positions table
            self.update_positions_table(status.get('positions', []))
            
            # Update status bar
            if status.get('running', False):
                self.statusBar().showMessage(f"🟢 Trading Active - Win Rate: {win_rate:.1f}% - Target: 75%+")
            else:
                self.statusBar().showMessage("🔴 Trading Stopped")
                
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")

    def update_positions_table(self, positions: List[Dict[str, Any]]):
        """Update positions table"""
        try:
            self.positions_table.setRowCount(len(positions))
            
            for row, position in enumerate(positions):
                self.positions_table.setItem(row, 0, QTableWidgetItem(str(position.get('ticket', ''))))
                self.positions_table.setItem(row, 1, QTableWidgetItem(position.get('symbol', '')))
                self.positions_table.setItem(row, 2, QTableWidgetItem('Buy' if position.get('type') == 0 else 'Sell'))
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position.get('volume', 0):.2f}"))
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position.get('price_open', 0):.5f}"))
                self.positions_table.setItem(row, 5, QTableWidgetItem(f"{position.get('price_current', 0):.5f}"))
                
                profit = position.get('profit', 0)
                profit_item = QTableWidgetItem(f"${profit:.2f}")
                if profit > 0:
                    profit_item.setBackground(QColor(40, 167, 69))  # Green
                elif profit < 0:
                    profit_item.setBackground(QColor(220, 53, 69))  # Red
                
                self.positions_table.setItem(row, 6, profit_item)
                
                # Close button
                close_btn = QPushButton("Close")
                close_btn.setStyleSheet("background-color: #dc3545; color: white; border-radius: 3px;")
                close_btn.clicked.connect(lambda checked, t=position.get('ticket'): self.close_position(t))
                self.positions_table.setCellWidget(row, 7, close_btn)
            
        except Exception as e:
            self.logger.error(f"Error updating positions table: {e}")

    # Button event handlers
    def start_trading(self):
        """Start trading"""
        try:
            if self.trading_engine and not self.is_trading:
                success = self.trading_engine.start()
                if success:
                    self.is_trading = True
                    self.start_button.setEnabled(False)
                    self.stop_button.setEnabled(True)
                    self.log_message("🚀 Trading started successfully")
                else:
                    self.log_message("❌ Failed to start trading")
            
        except Exception as e:
            self.logger.error(f"Error starting trading: {e}")
            self.log_message(f"❌ Error starting trading: {e}")

    def stop_trading(self):
        """Stop trading"""
        try:
            if self.trading_engine and self.is_trading:
                self.trading_engine.stop()
                self.is_trading = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.log_message("⛔ Trading stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading: {e}")
            self.log_message(f"❌ Error stopping trading: {e}")

    def emergency_stop(self):
        """Emergency stop all trading"""
        try:
            reply = QMessageBox.question(self, 'Emergency Stop', 
                                       'Are you sure you want to emergency stop and close all positions?',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                if self.trading_engine:
                    self.trading_engine.stop()
                if self.order_manager:
                    self.order_manager.close_all_orders()
                
                self.is_trading = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.log_message("🛑 EMERGENCY STOP EXECUTED")
            
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")
            self.log_message(f"❌ Error in emergency stop: {e}")

    def close_position(self, ticket: int):
        """Close specific position"""
        try:
            if self.order_manager:
                result = self.order_manager.close_order(ticket)
                if result['success']:
                    self.log_message(f"✅ Position {ticket} closed successfully")
                else:
                    self.log_message(f"❌ Failed to close position {ticket}: {result['error']}")
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            self.log_message(f"❌ Error closing position: {e}")

    def close_all_positions(self):
        """Close all positions"""
        try:
            reply = QMessageBox.question(self, 'Close All Positions', 
                                       'Are you sure you want to close all positions?',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                if self.order_manager:
                    result = self.order_manager.close_all_orders()
                    self.log_message(f"✅ Closed {result.get('closed', 0)} positions")
            
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")
            self.log_message(f"❌ Error closing all positions: {e}")

    def refresh_positions(self):
        """Refresh positions table"""
        try:
            if self.order_manager:
                positions = self.order_manager.get_active_orders()
                self.update_positions_table(positions)
                self.log_message("🔄 Positions refreshed")
            
        except Exception as e:
            self.logger.error(f"Error refreshing positions: {e}")

    def apply_settings(self):
        """Apply risk and trading settings"""
        try:
            if self.risk_manager:
                self.risk_manager.set_risk_parameters(
                    max_risk_per_trade=self.max_risk_spin.value(),
                    max_daily_risk=self.daily_risk_spin.value(),
                    max_drawdown=self.drawdown_spin.value()
                )
                self.log_message("✅ Settings applied successfully")
            
        except Exception as e:
            self.logger.error(f"Error applying settings: {e}")
            self.log_message(f"❌ Error applying settings: {e}")

    def clear_logs(self):
        """Clear log display"""
        self.log_text.clear()

    def export_logs(self):
        """Export logs to file"""
        try:
            with open(f"auratrade_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.log_message("✅ Logs exported successfully")
        except Exception as e:
            self.log_message(f"❌ Error exporting logs: {e}")

    def log_message(self, message: str):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            if self.is_trading:
                reply = QMessageBox.question(self, 'Confirm Exit', 
                                           'Trading is active. Are you sure you want to exit?',
                                           QMessageBox.Yes | QMessageBox.No, 
                                           QMessageBox.No)
                
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                
                # Stop trading before exit
                if self.trading_engine:
                    self.trading_engine.stop()
            
            # Stop status thread
            if self.status_thread:
                self.status_thread.stop()
                self.status_thread.wait(2000)
            
            self.logger.info("Main window closed")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error closing application: {e}")
            event.accept()
