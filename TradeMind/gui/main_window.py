"""
Main GUI Window for AuraTrade Bot
PyQt5-based trading dashboard and control interface
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QTabWidget, QGroupBox, QScrollArea, QSplitter, QFrame,
    QMessageBox, QProgressBar, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QSlider, QApplication, QStatusBar, QMenuBar, QAction,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter

from core.trading_engine import TradingEngine
from core.mt5_connector import MT5Connector
from gui.charts import ChartWidget
from gui.dashboard import TradingDashboard
from utils.logger import Logger

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, trading_engine: TradingEngine, mt5_connector: MT5Connector):
        super().__init__()
        
        self.logger = Logger.get_logger(__name__)
        self.trading_engine = trading_engine
        self.mt5_connector = mt5_connector
        
        # Window properties
        self.setWindowTitle("AuraTrade - Institutional Trading Bot v1.0")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # Theme and styling
        self.setup_theme()
        
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Initialize components
        self.chart_widget = None
        self.dashboard = None
        self.positions_table = None
        self.log_display = None
        self.status_labels = {}
        
        # Update timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # Update every second
        
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_charts)
        self.chart_timer.start(5000)  # Update charts every 5 seconds
        
        # Create UI
        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_interface()
        self.create_status_bar()
        
        # Connect signals
        self.connect_signals()
        
        # Initial setup
        self.current_symbol = "EURUSD"
        self.current_timeframe = "M15"
        
        self.logger.info("🖥️ Main window initialized")
    
    def setup_theme(self):
        """Setup dark theme for the application"""
        try:
            # Dark theme stylesheet
            dark_style = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #363636;
            }
            
            QTabBar::tab {
                background-color: #444444;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #555555;
            }
            
            QTabBar::tab:selected {
                background-color: #0078d4;
                border-bottom: 2px solid #ffffff;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            
            QPushButton.emergency {
                background-color: #dc3545;
            }
            
            QPushButton.emergency:hover {
                background-color: #c82333;
            }
            
            QPushButton.success {
                background-color: #28a745;
            }
            
            QPushButton.success:hover {
                background-color: #218838;
            }
            
            QTableWidget {
                background-color: #363636;
                alternate-background-color: #404040;
                selection-background-color: #0078d4;
                gridline-color: #555555;
                border: 1px solid #555555;
            }
            
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #555555;
            }
            
            QHeaderView::section {
                background-color: #444444;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #555555;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            QComboBox {
                background-color: #444444;
                border: 1px solid #555555;
                padding: 5px;
                color: #ffffff;
                border-radius: 3px;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 3px;
                border-color: #888888 transparent transparent transparent;
            }
            
            QSpinBox, QDoubleSpinBox {
                background-color: #444444;
                border: 1px solid #555555;
                padding: 5px;
                color: #ffffff;
                border-radius: 3px;
            }
            
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                background-color: #363636;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
            
            QStatusBar {
                background-color: #444444;
                border-top: 1px solid #555555;
                color: #ffffff;
            }
            
            QMenuBar {
                background-color: #444444;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            
            QMenu {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #555555;
            }
            
            QMenu::item {
                padding: 8px 25px;
            }
            
            QMenu::item:selected {
                background-color: #0078d4;
            }
            """
            
            self.setStyleSheet(dark_style)
            
        except Exception as e:
            self.logger.error(f"Error setting up theme: {e}")
    
    def create_menu_bar(self):
        """Create menu bar"""
        try:
            menubar = self.menuBar()
            
            # File menu
            file_menu = menubar.addMenu('File')
            
            export_action = QAction('Export Data', self)
            export_action.setShortcut('Ctrl+E')
            export_action.triggered.connect(self.export_data)
            file_menu.addAction(export_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction('Exit', self)
            exit_action.setShortcut('Ctrl+Q')
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Trading menu
            trading_menu = menubar.addMenu('Trading')
            
            start_trading_action = QAction('Start Trading', self)
            start_trading_action.triggered.connect(self.start_trading)
            trading_menu.addAction(start_trading_action)
            
            stop_trading_action = QAction('Stop Trading', self)
            stop_trading_action.triggered.connect(self.stop_trading)
            trading_menu.addAction(stop_trading_action)
            
            trading_menu.addSeparator()
            
            emergency_stop_action = QAction('Emergency Stop', self)
            emergency_stop_action.setShortcut('Ctrl+Shift+S')
            emergency_stop_action.triggered.connect(self.emergency_stop)
            trading_menu.addAction(emergency_stop_action)
            
            # View menu
            view_menu = menubar.addMenu('View')
            
            refresh_action = QAction('Refresh All', self)
            refresh_action.setShortcut('F5')
            refresh_action.triggered.connect(self.refresh_all_data)
            view_menu.addAction(refresh_action)
            
            # Tools menu
            tools_menu = menubar.addMenu('Tools')
            
            settings_action = QAction('Settings', self)
            settings_action.triggered.connect(self.show_settings)
            tools_menu.addAction(settings_action)
            
            # Help menu
            help_menu = menubar.addMenu('Help')
            
            about_action = QAction('About', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
            
        except Exception as e:
            self.logger.error(f"Error creating menu bar: {e}")
    
    def create_toolbar(self):
        """Create toolbar with quick actions"""
        try:
            # Control buttons layout
            control_layout = QHBoxLayout()
            
            # Symbol selection
            symbol_label = QLabel("Symbol:")
            self.symbol_combo = QComboBox()
            self.symbol_combo.addItems([
                "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
                "USDCHF", "NZDUSD", "EURGBP", "XAUUSD", "BTCUSD"
            ])
            self.symbol_combo.setCurrentText(self.current_symbol)
            self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
            
            # Timeframe selection
            timeframe_label = QLabel("Timeframe:")
            self.timeframe_combo = QComboBox()
            self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1"])
            self.timeframe_combo.setCurrentText(self.current_timeframe)
            self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
            
            # Trading control buttons
            self.start_btn = QPushButton("▶ Start Trading")
            self.start_btn.setObjectName("success")
            self.start_btn.clicked.connect(self.start_trading)
            
            self.stop_btn = QPushButton("⏸ Stop Trading")
            self.stop_btn.clicked.connect(self.stop_trading)
            
            self.emergency_btn = QPushButton("🛑 EMERGENCY STOP")
            self.emergency_btn.setObjectName("emergency")
            self.emergency_btn.clicked.connect(self.emergency_stop)
            
            # Add to layout
            control_layout.addWidget(symbol_label)
            control_layout.addWidget(self.symbol_combo)
            control_layout.addWidget(timeframe_label)
            control_layout.addWidget(self.timeframe_combo)
            control_layout.addStretch()
            control_layout.addWidget(self.start_btn)
            control_layout.addWidget(self.stop_btn)
            control_layout.addWidget(self.emergency_btn)
            
            # Create toolbar widget
            toolbar_widget = QWidget()
            toolbar_widget.setLayout(control_layout)
            toolbar_widget.setMaximumHeight(50)
            
            self.main_layout.addWidget(toolbar_widget)
            
        except Exception as e:
            self.logger.error(f"Error creating toolbar: {e}")
    
    def create_main_interface(self):
        """Create main interface with tabs and panels"""
        try:
            # Create main splitter
            main_splitter = QSplitter(Qt.Horizontal)
            
            # Left panel - Charts and analysis
            left_panel = self.create_left_panel()
            main_splitter.addWidget(left_panel)
            
            # Right panel - Trading info and controls
            right_panel = self.create_right_panel()
            main_splitter.addWidget(right_panel)
            
            # Set splitter proportions
            main_splitter.setSizes([1000, 600])
            
            self.main_layout.addWidget(main_splitter)
            
        except Exception as e:
            self.logger.error(f"Error creating main interface: {e}")
    
    def create_left_panel(self) -> QWidget:
        """Create left panel with charts and analysis"""
        try:
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            
            # Create tab widget for different views
            self.left_tabs = QTabWidget()
            
            # Charts tab
            charts_tab = QWidget()
            charts_layout = QVBoxLayout(charts_tab)
            
            # Chart widget
            self.chart_widget = ChartWidget()
            self.chart_widget.setMinimumHeight(400)
            charts_layout.addWidget(self.chart_widget)
            
            self.left_tabs.addTab(charts_tab, "📊 Charts")
            
            # Market Analysis tab
            analysis_tab = self.create_analysis_tab()
            self.left_tabs.addTab(analysis_tab, "📈 Analysis")
            
            # Strategy Performance tab
            performance_tab = self.create_performance_tab()
            self.left_tabs.addTab(performance_tab, "🎯 Performance")
            
            left_layout.addWidget(self.left_tabs)
            
            return left_widget
            
        except Exception as e:
            self.logger.error(f"Error creating left panel: {e}")
            return QWidget()
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with trading dashboard"""
        try:
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            
            # Create tab widget for trading info
            self.right_tabs = QTabWidget()
            
            # Dashboard tab
            self.dashboard = TradingDashboard(self.trading_engine, self.mt5_connector)
            self.right_tabs.addTab(self.dashboard, "🎛️ Dashboard")
            
            # Positions tab
            positions_tab = self.create_positions_tab()
            self.right_tabs.addTab(positions_tab, "💼 Positions")
            
            # Orders tab
            orders_tab = self.create_orders_tab()
            self.right_tabs.addTab(orders_tab, "📋 Orders")
            
            # Logs tab
            logs_tab = self.create_logs_tab()
            self.right_tabs.addTab(logs_tab, "📝 Logs")
            
            right_layout.addWidget(self.right_tabs)
            
            return right_widget
            
        except Exception as e:
            self.logger.error(f"Error creating right panel: {e}")
            return QWidget()
    
    def create_analysis_tab(self) -> QWidget:
        """Create market analysis tab"""
        try:
            analysis_widget = QWidget()
            analysis_layout = QVBoxLayout(analysis_widget)
            
            # Technical indicators section
            indicators_group = QGroupBox("Technical Indicators")
            indicators_layout = QGridLayout(indicators_group)
            
            # Create indicator displays
            self.indicator_labels = {}
            indicators = [
                ("RSI", "50.0"), ("MACD", "0.0000"), ("ATR", "0.0100"),
                ("BB Position", "50%"), ("EMA Slope", "0.0000"), ("ADX", "25.0")
            ]
            
            for i, (name, default_value) in enumerate(indicators):
                label = QLabel(f"{name}:")
                value_label = QLabel(default_value)
                value_label.setStyleSheet("font-weight: bold; color: #00ff00;")
                
                indicators_layout.addWidget(label, i // 3, (i % 3) * 2)
                indicators_layout.addWidget(value_label, i // 3, (i % 3) * 2 + 1)
                
                self.indicator_labels[name] = value_label
            
            analysis_layout.addWidget(indicators_group)
            
            # Market conditions section
            conditions_group = QGroupBox("Market Conditions")
            conditions_layout = QVBoxLayout(conditions_group)
            
            self.market_condition_label = QLabel("Analyzing...")
            self.volatility_label = QLabel("Volatility: Normal")
            self.trend_label = QLabel("Trend: Neutral")
            self.session_label = QLabel("Session: Loading...")
            
            conditions_layout.addWidget(self.market_condition_label)
            conditions_layout.addWidget(self.volatility_label)
            conditions_layout.addWidget(self.trend_label)
            conditions_layout.addWidget(self.session_label)
            
            analysis_layout.addWidget(conditions_group)
            
            # Sentiment analysis section
            sentiment_group = QGroupBox("Sentiment Analysis")
            sentiment_layout = QVBoxLayout(sentiment_group)
            
            self.sentiment_label = QLabel("Sentiment: Neutral")
            self.news_count_label = QLabel("News Articles: 0")
            
            sentiment_layout.addWidget(self.sentiment_label)
            sentiment_layout.addWidget(self.news_count_label)
            
            analysis_layout.addWidget(sentiment_group)
            
            analysis_layout.addStretch()
            
            return analysis_widget
            
        except Exception as e:
            self.logger.error(f"Error creating analysis tab: {e}")
            return QWidget()
    
    def create_performance_tab(self) -> QWidget:
        """Create strategy performance tab"""
        try:
            performance_widget = QWidget()
            performance_layout = QVBoxLayout(performance_widget)
            
            # Strategy performance section
            strategy_group = QGroupBox("Strategy Performance")
            strategy_layout = QGridLayout(strategy_group)
            
            # Create performance metrics
            self.performance_labels = {}
            metrics = [
                ("Total Trades", "0"), ("Win Rate", "0%"), ("Profit Factor", "0.00"),
                ("Max Drawdown", "0%"), ("Sharpe Ratio", "0.00"), ("Current P/L", "$0.00")
            ]
            
            for i, (name, default_value) in enumerate(metrics):
                label = QLabel(f"{name}:")
                value_label = QLabel(default_value)
                value_label.setStyleSheet("font-weight: bold;")
                
                strategy_layout.addWidget(label, i // 3, (i % 3) * 2)
                strategy_layout.addWidget(value_label, i // 3, (i % 3) * 2 + 1)
                
                self.performance_labels[name] = value_label
            
            performance_layout.addWidget(strategy_group)
            
            # Active strategies section
            active_strategies_group = QGroupBox("Active Strategies")
            active_strategies_layout = QVBoxLayout(active_strategies_group)
            
            self.strategies_table = QTableWidget(0, 4)
            self.strategies_table.setHorizontalHeaderLabels(["Strategy", "Status", "Signals", "P/L"])
            self.strategies_table.setMaximumHeight(200)
            
            active_strategies_layout.addWidget(self.strategies_table)
            performance_layout.addWidget(active_strategies_group)
            
            performance_layout.addStretch()
            
            return performance_widget
            
        except Exception as e:
            self.logger.error(f"Error creating performance tab: {e}")
            return QWidget()
    
    def create_positions_tab(self) -> QWidget:
        """Create positions management tab"""
        try:
            positions_widget = QWidget()
            positions_layout = QVBoxLayout(positions_widget)
            
            # Positions table
            self.positions_table = QTableWidget(0, 8)
            self.positions_table.setHorizontalHeaderLabels([
                "Ticket", "Symbol", "Type", "Volume", "Entry", "Current", "P/L", "Action"
            ])
            
            # Set column widths
            header = self.positions_table.horizontalHeader()
            header.setStretchLastSection(True)
            
            positions_layout.addWidget(self.positions_table)
            
            # Position controls
            controls_layout = QHBoxLayout()
            
            close_all_btn = QPushButton("Close All Positions")
            close_all_btn.clicked.connect(self.close_all_positions)
            
            close_profitable_btn = QPushButton("Close Profitable")
            close_profitable_btn.clicked.connect(self.close_profitable_positions)
            
            close_losing_btn = QPushButton("Close Losing")
            close_losing_btn.clicked.connect(self.close_losing_positions)
            
            controls_layout.addWidget(close_all_btn)
            controls_layout.addWidget(close_profitable_btn)
            controls_layout.addWidget(close_losing_btn)
            controls_layout.addStretch()
            
            positions_layout.addLayout(controls_layout)
            
            return positions_widget
            
        except Exception as e:
            self.logger.error(f"Error creating positions tab: {e}")
            return QWidget()
    
    def create_orders_tab(self) -> QWidget:
        """Create orders history tab"""
        try:
            orders_widget = QWidget()
            orders_layout = QVBoxLayout(orders_widget)
            
            # Orders table
            self.orders_table = QTableWidget(0, 7)
            self.orders_table.setHorizontalHeaderLabels([
                "Time", "Symbol", "Type", "Volume", "Price", "Result", "P/L"
            ])
            
            orders_layout.addWidget(self.orders_table)
            
            return orders_widget
            
        except Exception as e:
            self.logger.error(f"Error creating orders tab: {e}")
            return QWidget()
    
    def create_logs_tab(self) -> QWidget:
        """Create logs display tab"""
        try:
            logs_widget = QWidget()
            logs_layout = QVBoxLayout(logs_widget)
            
            # Log display
            self.log_display = QTextEdit()
            self.log_display.setReadOnly(True)
            self.log_display.setMaximumBlockCount(1000)  # Limit to 1000 lines
            
            logs_layout.addWidget(self.log_display)
            
            # Log controls
            log_controls = QHBoxLayout()
            
            clear_logs_btn = QPushButton("Clear Logs")
            clear_logs_btn.clicked.connect(self.clear_logs)
            
            save_logs_btn = QPushButton("Save Logs")
            save_logs_btn.clicked.connect(self.save_logs)
            
            log_controls.addWidget(clear_logs_btn)
            log_controls.addWidget(save_logs_btn)
            log_controls.addStretch()
            
            logs_layout.addLayout(log_controls)
            
            return logs_widget
            
        except Exception as e:
            self.logger.error(f"Error creating logs tab: {e}")
            return QWidget()
    
    def create_status_bar(self):
        """Create status bar with connection and trading status"""
        try:
            status_bar = QStatusBar()
            self.setStatusBar(status_bar)
            
            # Connection status
            self.connection_status = QLabel("MT5: Disconnected")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
            status_bar.addWidget(self.connection_status)
            
            status_bar.addWidget(QLabel(" | "))
            
            # Trading status
            self.trading_status = QLabel("Trading: Stopped")
            self.trading_status.setStyleSheet("color: red; font-weight: bold;")
            status_bar.addWidget(self.trading_status)
            
            status_bar.addWidget(QLabel(" | "))
            
            # Account balance
            self.balance_status = QLabel("Balance: $0.00")
            status_bar.addWidget(self.balance_status)
            
            status_bar.addWidget(QLabel(" | "))
            
            # Equity
            self.equity_status = QLabel("Equity: $0.00")
            status_bar.addWidget(self.equity_status)
            
            status_bar.addWidget(QLabel(" | "))
            
            # Current time
            self.time_status = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            status_bar.addPermanentWidget(self.time_status)
            
        except Exception as e:
            self.logger.error(f"Error creating status bar: {e}")
    
    def connect_signals(self):
        """Connect signals and slots"""
        try:
            # Connect chart updates
            if self.chart_widget:
                pass  # Chart-specific signals would be connected here
            
        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}")
    
    def update_dashboard(self):
        """Update all dashboard components"""
        try:
            # Update time
            self.time_status.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Update connection status
            if self.mt5_connector.check_connection():
                self.connection_status.setText("MT5: Connected")
                self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.connection_status.setText("MT5: Disconnected")
                self.connection_status.setStyleSheet("color: red; font-weight: bold;")
            
            # Update trading status
            if self.trading_engine.is_running:
                self.trading_status.setText("Trading: Active")
                self.trading_status.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.trading_status.setText("Trading: Stopped")
                self.trading_status.setStyleSheet("color: red; font-weight: bold;")
            
            # Update account info
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                self.balance_status.setText(f"Balance: ${account_info['balance']:.2f}")
                self.equity_status.setText(f"Equity: ${account_info['equity']:.2f}")
            
            # Update positions table
            self.update_positions_table()
            
            # Update dashboard component
            if self.dashboard:
                self.dashboard.update_dashboard()
            
            # Update analysis data
            self.update_analysis_data()
            
            # Update performance metrics
            self.update_performance_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")
    
    def update_charts(self):
        """Update chart displays"""
        try:
            if self.chart_widget:
                # Get current symbol data
                data_manager = self.trading_engine.data_manager
                rates_data = data_manager.get_symbol_data(self.current_symbol, self.current_timeframe)
                
                if rates_data is not None:
                    self.chart_widget.update_chart(self.current_symbol, rates_data)
                
        except Exception as e:
            self.logger.error(f"Error updating charts: {e}")
    
    def update_positions_table(self):
        """Update positions table"""
        try:
            positions = self.mt5_connector.get_positions()
            
            self.positions_table.setRowCount(len(positions))
            
            for row, position in enumerate(positions):
                self.positions_table.setItem(row, 0, QTableWidgetItem(str(position["ticket"])))
                self.positions_table.setItem(row, 1, QTableWidgetItem(position["symbol"]))
                self.positions_table.setItem(row, 2, QTableWidgetItem(position["type"]))
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position['volume']:.2f}"))
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position['price_open']:.5f}"))
                self.positions_table.setItem(row, 5, QTableWidgetItem(f"{position['price_current']:.5f}"))
                
                # Color-code P/L
                pnl_item = QTableWidgetItem(f"${position['profit']:.2f}")
                if position['profit'] > 0:
                    pnl_item.setStyleSheet("color: green; font-weight: bold;")
                elif position['profit'] < 0:
                    pnl_item.setStyleSheet("color: red; font-weight: bold;")
                
                self.positions_table.setItem(row, 6, pnl_item)
                
                # Close button
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(lambda checked, ticket=position["ticket"]: self.close_position(ticket))
                self.positions_table.setCellWidget(row, 7, close_btn)
            
        except Exception as e:
            self.logger.error(f"Error updating positions table: {e}")
    
    def update_analysis_data(self):
        """Update technical analysis data"""
        try:
            # Get analysis data for current symbol
            data_manager = self.trading_engine.data_manager
            rates_data = data_manager.get_symbol_data(self.current_symbol, self.current_timeframe)
            
            if rates_data is not None:
                # Get technical analysis
                technical_signals = self.trading_engine.technical_analysis.analyze(rates_data)
                
                # Update indicator labels
                if "rsi" in technical_signals:
                    rsi_value = technical_signals["rsi"].get("value", 50)
                    self.indicator_labels["RSI"].setText(f"{rsi_value:.1f}")
                
                if "macd" in technical_signals:
                    macd_value = technical_signals["macd"].get("macd", 0)
                    self.indicator_labels["MACD"].setText(f"{macd_value:.4f}")
                
                if "atr" in technical_signals:
                    atr_value = technical_signals["atr"].get("value", 0)
                    self.indicator_labels["ATR"].setText(f"{atr_value:.4f}")
                
                if "bollinger_bands" in technical_signals:
                    bb_position = technical_signals["bollinger_bands"].get("position", 0.5)
                    self.indicator_labels["BB Position"].setText(f"{bb_position*100:.0f}%")
                
                if "ema" in technical_signals:
                    ema_slope = technical_signals["ema"].get("slope", 0)
                    self.indicator_labels["EMA Slope"].setText(f"{ema_slope:.4f}")
                
                if "adx" in technical_signals:
                    adx_value = technical_signals["adx"].get("adx", 25)
                    self.indicator_labels["ADX"].setText(f"{adx_value:.1f}")
                
                # Get market conditions
                tick_data = data_manager.get_tick_data(self.current_symbol)
                if tick_data:
                    market_condition = self.trading_engine.market_conditions.analyze(rates_data, tick_data)
                    
                    overall_condition = market_condition.get("overall_condition", "unknown")
                    self.market_condition_label.setText(f"Overall: {overall_condition.title()}")
                    
                    volatility = market_condition.get("volatility", {})
                    vol_level = volatility.get("level", "unknown")
                    self.volatility_label.setText(f"Volatility: {vol_level.title()}")
                    
                    trend = market_condition.get("trend", {})
                    trend_direction = trend.get("direction", "neutral")
                    trend_strength = trend.get("quality", "weak")
                    self.trend_label.setText(f"Trend: {trend_direction.title()} ({trend_strength})")
                    
                    session = market_condition.get("session", {})
                    active_sessions = session.get("current_sessions", [])
                    if active_sessions:
                        session_text = ", ".join(s.title() for s in active_sessions)
                        self.session_label.setText(f"Session: {session_text}")
                    else:
                        self.session_label.setText("Session: Closed")
                
                # Get sentiment
                sentiment_data = self.trading_engine.sentiment_analyzer.get_symbol_sentiment(self.current_symbol)
                overall_sentiment = sentiment_data.get("overall_sentiment", "neutral")
                self.sentiment_label.setText(f"Sentiment: {overall_sentiment.title()}")
                
                news_count = sentiment_data.get("components", {}).get("news", {}).get("count", 0)
                self.news_count_label.setText(f"News Articles: {news_count}")
                
        except Exception as e:
            self.logger.error(f"Error updating analysis data: {e}")
    
    def update_performance_metrics(self):
        """Update strategy performance metrics"""
        try:
            # Get trading statistics
            stats = self.trading_engine.get_statistics()
            
            # Update performance labels
            self.performance_labels["Total Trades"].setText(str(stats.get("total_trades", 0)))
            
            win_rate = stats.get("win_rate", 0)
            self.performance_labels["Win Rate"].setText(f"{win_rate:.1f}%")
            
            max_drawdown = stats.get("max_drawdown", 0)
            self.performance_labels["Max Drawdown"].setText(f"{max_drawdown:.1f}%")
            
            current_profit = stats.get("current_profit", 0)
            profit_text = f"${current_profit:.2f}"
            profit_label = self.performance_labels["Current P/L"]
            profit_label.setText(profit_text)
            
            if current_profit > 0:
                profit_label.setStyleSheet("font-weight: bold; color: green;")
            elif current_profit < 0:
                profit_label.setStyleSheet("font-weight: bold; color: red;")
            else:
                profit_label.setStyleSheet("font-weight: bold; color: white;")
            
            # Update strategies table
            self.update_strategies_table()
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def update_strategies_table(self):
        """Update active strategies table"""
        try:
            strategies = ["HFT", "Scalping", "Arbitrage", "Pattern"]
            
            self.strategies_table.setRowCount(len(strategies))
            
            for row, strategy in enumerate(strategies):
                self.strategies_table.setItem(row, 0, QTableWidgetItem(strategy))
                
                # Get strategy status (simplified)
                if self.trading_engine.is_running:
                    status = "Active"
                    status_color = "green"
                else:
                    status = "Inactive"
                    status_color = "red"
                
                status_item = QTableWidgetItem(status)
                status_item.setStyleSheet(f"color: {status_color}; font-weight: bold;")
                self.strategies_table.setItem(row, 1, status_item)
                
                # Placeholder for signals and P/L
                self.strategies_table.setItem(row, 2, QTableWidgetItem("0"))
                self.strategies_table.setItem(row, 3, QTableWidgetItem("$0.00"))
            
        except Exception as e:
            self.logger.error(f"Error updating strategies table: {e}")
    
    # Event handlers
    
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change"""
        try:
            self.current_symbol = symbol
            self.logger.info(f"Symbol changed to: {symbol}")
            
            # Update charts immediately
            self.update_charts()
            
        except Exception as e:
            self.logger.error(f"Error changing symbol: {e}")
    
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        try:
            self.current_timeframe = timeframe
            self.logger.info(f"Timeframe changed to: {timeframe}")
            
            # Update charts immediately
            self.update_charts()
            
        except Exception as e:
            self.logger.error(f"Error changing timeframe: {e}")
    
    def start_trading(self):
        """Start trading"""
        try:
            if not self.mt5_connector.check_connection():
                QMessageBox.warning(self, "Warning", "MT5 not connected. Please check connection.")
                return
            
            self.trading_engine.start()
            self.logger.info("Trading started from GUI")
            
            # Update button states
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error starting trading: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start trading: {e}")
    
    def stop_trading(self):
        """Stop trading"""
        try:
            self.trading_engine.stop()
            self.logger.info("Trading stopped from GUI")
            
            # Update button states
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
        except Exception as e:
            self.logger.error(f"Error stopping trading: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop trading: {e}")
    
    def emergency_stop(self):
        """Emergency stop all trading"""
        try:
            reply = QMessageBox.question(
                self, 
                "Emergency Stop", 
                "This will immediately stop all trading and close all positions. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.trading_engine.emergency_stop()
                self.logger.warning("Emergency stop activated from GUI")
                
                # Update button states
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                
                QMessageBox.information(self, "Emergency Stop", "Emergency stop completed.")
            
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")
            QMessageBox.critical(self, "Error", f"Emergency stop failed: {e}")
    
    def close_position(self, ticket: int):
        """Close specific position"""
        try:
            success = self.mt5_connector.close_position(ticket)
            if success:
                self.logger.info(f"Position {ticket} closed from GUI")
            else:
                QMessageBox.warning(self, "Warning", f"Failed to close position {ticket}")
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            QMessageBox.critical(self, "Error", f"Failed to close position: {e}")
    
    def close_all_positions(self):
        """Close all open positions"""
        try:
            reply = QMessageBox.question(
                self,
                "Close All Positions",
                "Close all open positions?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                positions = self.mt5_connector.get_positions()
                for position in positions:
                    self.mt5_connector.close_position(position["ticket"])
                
                self.logger.info("All positions closed from GUI")
                
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")
    
    def close_profitable_positions(self):
        """Close all profitable positions"""
        try:
            positions = self.mt5_connector.get_positions()
            closed_count = 0
            
            for position in positions:
                if position["profit"] > 0:
                    if self.mt5_connector.close_position(position["ticket"]):
                        closed_count += 1
            
            self.logger.info(f"Closed {closed_count} profitable positions from GUI")
            
        except Exception as e:
            self.logger.error(f"Error closing profitable positions: {e}")
    
    def close_losing_positions(self):
        """Close all losing positions"""
        try:
            positions = self.mt5_connector.get_positions()
            closed_count = 0
            
            for position in positions:
                if position["profit"] < 0:
                    if self.mt5_connector.close_position(position["ticket"]):
                        closed_count += 1
            
            self.logger.info(f"Closed {closed_count} losing positions from GUI")
            
        except Exception as e:
            self.logger.error(f"Error closing losing positions: {e}")
    
    def refresh_all_data(self):
        """Refresh all data"""
        try:
            self.trading_engine.data_manager.update_all_data()
            self.logger.info("All data refreshed from GUI")
            
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")
    
    def clear_logs(self):
        """Clear log display"""
        try:
            if self.log_display:
                self.log_display.clear()
                
        except Exception as e:
            self.logger.error(f"Error clearing logs: {e}")
    
    def save_logs(self):
        """Save logs to file"""
        try:
            if self.log_display:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"aura_trade_logs_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(self.log_display.toPlainText())
                
                QMessageBox.information(self, "Logs Saved", f"Logs saved to {filename}")
                
        except Exception as e:
            self.logger.error(f"Error saving logs: {e}")
    
    def export_data(self):
        """Export trading data"""
        try:
            # This would implement data export functionality
            QMessageBox.information(self, "Export", "Data export functionality not implemented yet.")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
    
    def show_settings(self):
        """Show settings dialog"""
        try:
            # This would show a settings dialog
            QMessageBox.information(self, "Settings", "Settings dialog not implemented yet.")
            
        except Exception as e:
            self.logger.error(f"Error showing settings: {e}")
    
    def show_about(self):
        """Show about dialog"""
        try:
            about_text = """
            <h2>AuraTrade - Institutional Trading Bot</h2>
            <p><b>Version:</b> 1.0.0</p>
            <p><b>Description:</b> Advanced algorithmic trading system with MT5 integration</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Multiple trading strategies (HFT, Scalping, Arbitrage, Pattern)</li>
                <li>Advanced risk management</li>
                <li>Real-time technical analysis</li>
                <li>Sentiment analysis</li>
                <li>Live trading dashboard</li>
            </ul>
            <p><b>Copyright:</b> 2024 AuraTrade Systems</p>
            """
            
            QMessageBox.about(self, "About AuraTrade", about_text)
            
        except Exception as e:
            self.logger.error(f"Error showing about: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            reply = QMessageBox.question(
                self,
                "Exit AuraTrade",
                "Are you sure you want to exit?\nAll trading will be stopped.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Stop trading
                if self.trading_engine.is_running:
                    self.trading_engine.stop()
                
                # Stop timers
                self.update_timer.stop()
                self.chart_timer.stop()
                
                self.logger.info("Application closing")
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            self.logger.error(f"Error during close: {e}")
            event.accept()
