"""
Main GUI Window for AuraTrade Bot
Modern PyQt5 interface with all required features
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import pandas as pd
from typing import Dict, Any

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, mt5_connector, trading_engine, order_manager, portfolio, strategies, technical_analysis, data_manager):
        super().__init__()
        self.mt5_connector = mt5_connector
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.portfolio = portfolio
        self.strategies = strategies
        self.technical_analysis = technical_analysis
        self.data_manager = data_manager

        # GUI update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gui)

        # Initialize UI
        self.init_ui()
        self.setup_connections()

        # Start GUI updates
        self.update_timer.start(1000)  # Update every second

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("AuraTrade Bot v2.0 - Professional Trading System")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)

        # Set application icon and style
        self.setStyleSheet(self.get_dark_theme_style())

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create left panel (controls)
        left_panel = self.create_left_panel()

        # Create right panel (info and logs)
        right_panel = self.create_right_panel()

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        # Create status bar
        self.create_status_bar()

    def create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        panel.setMaximumWidth(400)

        layout = QVBoxLayout(panel)

        # Symbol Selection
        symbol_group = QGroupBox("Trading Symbol")
        symbol_layout = QVBoxLayout(symbol_group)

        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)
        self.symbol_combo.addItems(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'ETHUSD'])
        self.symbol_combo.setCurrentText('EURUSD')
        symbol_layout.addWidget(QLabel("Select or Enter Symbol:"))
        symbol_layout.addWidget(self.symbol_combo)

        layout.addWidget(symbol_group)

        # Trading Settings
        settings_group = QGroupBox("Trading Settings")
        settings_layout = QFormLayout(settings_group)

        self.lot_size_spin = QDoubleSpinBox()
        self.lot_size_spin.setRange(0.01, 100.0)
        self.lot_size_spin.setSingleStep(0.01)
        self.lot_size_spin.setValue(0.01)
        self.lot_size_spin.setDecimals(2)

        self.max_trades_spin = QSpinBox()
        self.max_trades_spin.setRange(1, 50)
        self.max_trades_spin.setValue(10)

        settings_layout.addRow("Lot Size:", self.lot_size_spin)
        settings_layout.addRow("Max Open Trades:", self.max_trades_spin)

        layout.addWidget(settings_group)

        # TP/SL Settings
        tpsl_group = QGroupBox("Take Profit / Stop Loss")
        tpsl_layout = QVBoxLayout(tpsl_group)

        # Scalping TP/SL
        scalping_frame = QFrame()
        scalping_layout = QFormLayout(scalping_frame)

        self.scalping_tp_spin = QDoubleSpinBox()
        self.scalping_tp_spin.setRange(1, 1000)
        self.scalping_tp_spin.setValue(8)
        self.scalping_tp_spin.valueChanged.connect(self.calculate_scalping_profit)

        self.scalping_sl_spin = QDoubleSpinBox()
        self.scalping_sl_spin.setRange(1, 1000)
        self.scalping_sl_spin.setValue(12)
        self.scalping_sl_spin.valueChanged.connect(self.calculate_scalping_loss)

        self.scalping_tp_type = QComboBox()
        self.scalping_tp_type.addItems(['pips', 'price', 'percent'])
        self.scalping_tp_type.currentTextChanged.connect(self.calculate_scalping_profit)

        self.scalping_sl_type = QComboBox()
        self.scalping_sl_type.addItems(['pips', 'price', 'percent'])
        self.scalping_sl_type.currentTextChanged.connect(self.calculate_scalping_loss)

        scalping_layout.addRow("Scalping TP:", self.scalping_tp_spin)
        scalping_layout.addRow("TP Type:", self.scalping_tp_type)
        scalping_layout.addRow("Scalping SL:", self.scalping_sl_spin)
        scalping_layout.addRow("SL Type:", self.scalping_sl_type)

        # Profit/Loss Display
        self.scalping_profit_label = QLabel("Profit: $0.00 (0 pips, 0.00%)")
        self.scalping_profit_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        self.scalping_loss_label = QLabel("Loss: $0.00 (0 pips, 0.00%)")
        self.scalping_loss_label.setStyleSheet("color: #F44336; font-weight: bold;")

        tpsl_layout.addWidget(QLabel("Scalping Settings:"))
        tpsl_layout.addWidget(scalping_frame)
        tpsl_layout.addWidget(self.scalping_profit_label)
        tpsl_layout.addWidget(self.scalping_loss_label)

        # General TP/SL
        general_frame = QFrame()
        general_layout = QFormLayout(general_frame)

        self.general_tp_spin = QDoubleSpinBox()
        self.general_tp_spin.setRange(1, 1000)
        self.general_tp_spin.setValue(40)
        self.general_tp_spin.valueChanged.connect(self.calculate_general_profit)

        self.general_sl_spin = QDoubleSpinBox()
        self.general_sl_spin.setRange(1, 1000)
        self.general_sl_spin.setValue(20)
        self.general_sl_spin.valueChanged.connect(self.calculate_general_loss)

        self.general_tp_type = QComboBox()
        self.general_tp_type.addItems(['pips', 'price', 'percent'])
        self.general_tp_type.currentTextChanged.connect(self.calculate_general_profit)

        self.general_sl_type = QComboBox()
        self.general_sl_type.addItems(['pips', 'price', 'percent'])
        self.general_sl_type.currentTextChanged.connect(self.calculate_general_loss)

        general_layout.addRow("General TP:", self.general_tp_spin)
        general_layout.addRow("TP Type:", self.general_tp_type)
        general_layout.addRow("General SL:", self.general_sl_spin)
        general_layout.addRow("SL Type:", self.general_sl_type)

        self.general_profit_label = QLabel("Profit: $0.00 (0 pips, 0.00%)")
        self.general_profit_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        self.general_loss_label = QLabel("Loss: $0.00 (0 pips, 0.00%)")
        self.general_loss_label.setStyleSheet("color: #F44336; font-weight: bold;")

        tpsl_layout.addWidget(QLabel("General Settings:"))
        tpsl_layout.addWidget(general_frame)
        tpsl_layout.addWidget(self.general_profit_label)
        tpsl_layout.addWidget(self.general_loss_label)

        layout.addWidget(tpsl_group)

        # Strategy Selection
        strategy_group = QGroupBox("Strategy Selection")
        strategy_layout = QVBoxLayout(strategy_group)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['Scalping', 'Intraday', 'HFT', 'Arbitrage'])
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)

        strategy_layout.addWidget(QLabel("Active Strategy:"))
        strategy_layout.addWidget(self.strategy_combo)

        layout.addWidget(strategy_group)

        # Control Buttons
        buttons_group = QGroupBox("Bot Control")
        buttons_layout = QVBoxLayout(buttons_group)

        self.start_button = QPushButton("🚀 START BOT")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.start_button.clicked.connect(self.start_bot)

        self.stop_button = QPushButton("🛑 STOP BOT")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)

        self.close_all_button = QPushButton("❌ CLOSE ALL POSITIONS")
        self.close_all_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """)
        self.close_all_button.clicked.connect(self.close_all_positions)

        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.close_all_button)

        layout.addWidget(buttons_group)

        # Add stretch to push everything up
        layout.addStretch()

        return panel

    def create_right_panel(self) -> QWidget:
        """Create right information panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tab widget
        tabs = QTabWidget()

        # Account Info Tab
        account_tab = self.create_account_tab()
        tabs.addTab(account_tab, "Account Info")

        # Positions Tab
        positions_tab = self.create_positions_tab()
        tabs.addTab(positions_tab, "Open Positions")

        # Logs Tab
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "Trading Logs")

        # Analysis Tab
        analysis_tab = self.create_analysis_tab()
        tabs.addTab(analysis_tab, "Market Analysis")

        layout.addWidget(tabs)

        return panel

    def create_account_tab(self) -> QWidget:
        """Create account information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Account info group
        account_group = QGroupBox("Account Information")
        account_layout = QGridLayout(account_group)

        # Create labels for account info
        self.balance_label = QLabel("$0.00")
        self.equity_label = QLabel("$0.00")
        self.free_margin_label = QLabel("$0.00")
        self.margin_level_label = QLabel("0.00%")
        self.profit_label = QLabel("$0.00")

        # Style the labels
        for label in [self.balance_label, self.equity_label, self.free_margin_label, 
                     self.margin_level_label, self.profit_label]:
            label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")

        account_layout.addWidget(QLabel("Balance:"), 0, 0)
        account_layout.addWidget(self.balance_label, 0, 1)
        account_layout.addWidget(QLabel("Equity:"), 1, 0)
        account_layout.addWidget(self.equity_label, 1, 1)
        account_layout.addWidget(QLabel("Free Margin:"), 2, 0)
        account_layout.addWidget(self.free_margin_label, 2, 1)
        account_layout.addWidget(QLabel("Margin Level:"), 3, 0)
        account_layout.addWidget(self.margin_level_label, 3, 1)
        account_layout.addWidget(QLabel("Floating P&L:"), 4, 0)
        account_layout.addWidget(self.profit_label, 4, 1)

        layout.addWidget(account_group)

        # Performance group
        performance_group = QGroupBox("Today's Performance")
        performance_layout = QGridLayout(performance_group)

        self.trades_today_label = QLabel("0")
        self.win_rate_label = QLabel("0.00%")
        self.daily_pnl_label = QLabel("$0.00")
        self.drawdown_label = QLabel("0.00%")

        for label in [self.trades_today_label, self.win_rate_label, 
                     self.daily_pnl_label, self.drawdown_label]:
            label.setStyleSheet("font-size: 14px; font-weight: bold;")

        performance_layout.addWidget(QLabel("Trades Today:"), 0, 0)
        performance_layout.addWidget(self.trades_today_label, 0, 1)
        performance_layout.addWidget(QLabel("Win Rate:"), 1, 0)
        performance_layout.addWidget(self.win_rate_label, 1, 1)
        performance_layout.addWidget(QLabel("Daily P&L:"), 2, 0)
        performance_layout.addWidget(self.daily_pnl_label, 2, 1)
        performance_layout.addWidget(QLabel("Max Drawdown:"), 3, 0)
        performance_layout.addWidget(self.drawdown_label, 3, 1)

        layout.addWidget(performance_group)
        layout.addStretch()

        return widget

    def create_positions_tab(self) -> QWidget:
        """Create positions tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            'Ticket', 'Symbol', 'Type', 'Volume', 'Open Price', 'Current Price', 'Profit', 'Time'
        ])

        # Style the table
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.positions_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(QLabel("Open Positions:"))
        layout.addWidget(self.positions_table)

        return widget

    def create_logs_tab(self) -> QWidget:
        """Create logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # Limit to 1000 lines

        # Style the log area
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: 1px solid #555555;
            }
        """)

        # Log controls
        controls_layout = QHBoxLayout()

        clear_logs_button = QPushButton("Clear Logs")
        clear_logs_button.clicked.connect(self.clear_logs)

        export_logs_button = QPushButton("Export Logs")
        export_logs_button.clicked.connect(self.export_logs)

        controls_layout.addWidget(clear_logs_button)
        controls_layout.addWidget(export_logs_button)
        controls_layout.addStretch()

        layout.addWidget(QLabel("Trading Activity Log:"))
        layout.addWidget(self.log_text)
        layout.addLayout(controls_layout)

        return widget

    def create_analysis_tab(self) -> QWidget:
        """Create market analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Analysis display
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)

        layout.addWidget(QLabel("Real-time Market Analysis:"))
        layout.addWidget(self.analysis_text)

        return widget

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()

        # Connection status
        self.connection_label = QLabel("❌ Disconnected")
        self.connection_label.setStyleSheet("color: #F44336; font-weight: bold;")

        # Bot status
        self.bot_status_label = QLabel("⏹️ Stopped")
        self.bot_status_label.setStyleSheet("color: #757575; font-weight: bold;")

        # Time label
        self.time_label = QLabel()
        self.update_time()

        self.status_bar.addWidget(self.connection_label)
        self.status_bar.addPermanentWidget(self.bot_status_label)
        self.status_bar.addPermanentWidget(self.time_label)

    def setup_connections(self):
        """Setup signal connections"""
        pass

    def update_gui(self):
        """Update GUI with current information"""
        try:
            self.update_time()
            self.update_account_info()
            self.update_positions_table()
            self.update_connection_status()
            self.update_bot_status()
            self.update_analysis()
        except Exception as e:
            self.log_message(f"Error updating GUI: {e}", "ERROR")

    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(f"🕐 {current_time}")

    def update_account_info(self):
        """Update account information"""
        try:
            if hasattr(self.mt5_connector, 'get_account_info'):
                account = self.mt5_connector.get_account_info()
                if account:
                    self.balance_label.setText(f"${account.get('balance', 0):.2f}")
                    self.equity_label.setText(f"${account.get('equity', 0):.2f}")
                    self.free_margin_label.setText(f"${account.get('free_margin', 0):.2f}")
                    self.margin_level_label.setText(f"{account.get('margin_level', 0):.2f}%")

                    profit = account.get('profit', 0)
                    self.profit_label.setText(f"${profit:.2f}")
                    if profit > 0:
                        self.profit_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
                    elif profit < 0:
                        self.profit_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
                    else:
                        self.profit_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #757575;")
        except Exception as e:
            pass

    def update_positions_table(self):
        """Update positions table"""
        try:
            if hasattr(self.mt5_connector, 'get_positions'):
                positions = self.mt5_connector.get_positions()
                self.positions_table.setRowCount(len(positions))

                for i, pos in enumerate(positions):
                    self.positions_table.setItem(i, 0, QTableWidgetItem(str(pos.get('ticket', ''))))
                    self.positions_table.setItem(i, 1, QTableWidgetItem(pos.get('symbol', '')))
                    self.positions_table.setItem(i, 2, QTableWidgetItem('Buy' if pos.get('type') == 0 else 'Sell'))
                    self.positions_table.setItem(i, 3, QTableWidgetItem(f"{pos.get('volume', 0):.2f}"))
                    self.positions_table.setItem(i, 4, QTableWidgetItem(f"{pos.get('price_open', 0):.5f}"))
                    self.positions_table.setItem(i, 5, QTableWidgetItem(f"{pos.get('price_current', 0):.5f}"))

                    profit = pos.get('profit', 0)
                    profit_item = QTableWidgetItem(f"${profit:.2f}")
                    if profit > 0:
                        profit_item.setForeground(QColor('#4CAF50'))
                    elif profit < 0:
                        profit_item.setForeground(QColor('#F44336'))
                    self.positions_table.setItem(i, 6, profit_item)

                    self.positions_table.setItem(i, 7, QTableWidgetItem(
                        datetime.fromtimestamp(pos.get('time', 0)).strftime('%H:%M:%S')
                    ))
        except Exception as e:
            pass

    def update_connection_status(self):
        """Update connection status"""
        try:
            if hasattr(self.mt5_connector, 'check_connection'):
                connected = self.mt5_connector.check_connection()
                if connected:
                    self.connection_label.setText("✅ Connected")
                    self.connection_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                else:
                    self.connection_label.setText("❌ Disconnected")
                    self.connection_label.setStyleSheet("color: #F44336; font-weight: bold;")
        except Exception:
            self.connection_label.setText("❌ Error")
            self.connection_label.setStyleSheet("color: #F44336; font-weight: bold;")

    def update_bot_status(self):
        """Update bot status"""
        try:
            if hasattr(self.trading_engine, 'running') and self.trading_engine.running:
                self.bot_status_label.setText("🟢 Running")
                self.bot_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.bot_status_label.setText("⏹️ Stopped")
                self.bot_status_label.setStyleSheet("color: #757575; font-weight: bold;")

            # Update performance metrics
            if hasattr(self.trading_engine, 'get_status'):
                status = self.trading_engine.get_status()
                self.trades_today_label.setText(str(status.get('trades_today', 0)))
                self.win_rate_label.setText(f"{status.get('win_rate', 0):.1f}%")

                daily_pnl = status.get('daily_pnl', 0)
                self.daily_pnl_label.setText(f"${daily_pnl:.2f}")
                if daily_pnl > 0:
                    self.daily_pnl_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
                elif daily_pnl < 0:
                    self.daily_pnl_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #F44336;")
                else:
                    self.daily_pnl_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #757575;")

                self.drawdown_label.setText(f"{status.get('max_drawdown', 0):.2f}%")

        except Exception as e:
            pass

    def update_analysis(self):
        """Update market analysis display"""
        try:
            if hasattr(self.trading_engine, 'get_latest_analysis'):
                symbol = self.symbol_combo.currentText()
                analysis = self.trading_engine.get_latest_analysis(symbol)

                if analysis:
                    analysis_text = f"Analysis for {symbol} - {analysis['timestamp'].strftime('%H:%M:%S')}\n\n"

                    # Display indicators
                    indicators = analysis.get('indicators', {})
                    analysis_text += "Technical Indicators:\n"
                    for name, value in indicators.items():
                        if isinstance(value, (int, float)):
                            analysis_text += f"  {name}: {value:.4f}\n"

                    # Display signals
                    signals = analysis.get('signals', [])
                    if signals:
                        analysis_text += f"\nSignals ({len(signals)}):\n"
                        for signal in signals:
                            analysis_text += f"  {signal.get('action', '').upper()} - "
                            analysis_text += f"Confidence: {signal.get('confidence', 0):.2f} - "
                            analysis_text += f"Reason: {signal.get('reason', 'N/A')}\n"

                    # Display spread
                    spread = analysis.get('spread', 0)
                    analysis_text += f"\nSpread: {spread:.1f} pips\n"

                    self.analysis_text.setText(analysis_text)
        except Exception as e:
            pass

    def calculate_scalping_profit(self):
        """Calculate and display scalping profit"""
        self._calculate_and_display_profit(
            self.scalping_tp_spin.value(),
            self.scalping_tp_type.currentText(),
            self.scalping_profit_label,
            'profit'
        )

    def calculate_scalping_loss(self):
        """Calculate and display scalping loss"""
        self._calculate_and_display_profit(
            self.scalping_sl_spin.value(),
            self.scalping_sl_type.currentText(),
            self.scalping_loss_label,
            'loss'
        )

    def calculate_general_profit(self):
        """Calculate and display general profit"""
        self._calculate_and_display_profit(
            self.general_tp_spin.value(),
            self.general_tp_type.currentText(),
            self.general_profit_label,
            'profit'
        )

    def calculate_general_loss(self):
        """Calculate and display general loss"""
        self._calculate_and_display_profit(
            self.general_sl_spin.value(),
            self.general_sl_type.currentText(),
            self.general_loss_label,
            'loss'
        )

    def _calculate_and_display_profit(self, value: float, value_type: str, label: QLabel, calc_type: str):
        """Calculate and display profit/loss values"""
        try:
            symbol = self.symbol_combo.currentText()
            lot_size = self.lot_size_spin.value()

            # Simple calculation for display
            if value_type == 'pips':
                pips = value
                if 'JPY' in symbol:
                    usd_value = pips * lot_size
                elif 'XAU' in symbol:
                    usd_value = pips * lot_size
                else:
                    usd_value = pips * lot_size * 10
                percent = (usd_value / 10000) * 100  # Assuming $10,000 account
            elif value_type == 'percent':
                percent = value
                usd_value = (percent / 100) * 10000
                if 'JPY' in symbol:
                    pips = usd_value / lot_size
                else:
                    pips = usd_value / (lot_size * 10)
            else:  # price
                pips = value  # Simplified
                usd_value = pips * lot_size * 10
                percent = (usd_value / 10000) * 100

            display_text = f"{'Profit' if calc_type == 'profit' else 'Loss'}: ${usd_value:.2f} ({pips:.0f} pips, {percent:.2f}%)"
            label.setText(display_text)

        except Exception as e:
            label.setText(f"{'Profit' if calc_type == 'profit' else 'Loss'}: Calculation Error")

    def start_bot(self):
        """Start the trading bot"""
        try:
            if hasattr(self.trading_engine, 'start'):
                self.trading_engine.start()
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.log_message("Trading bot started", "INFO")
        except Exception as e:
            self.log_message(f"Error starting bot: {e}", "ERROR")

    def stop_bot(self):
        """Stop the trading bot"""
        try:
            if hasattr(self.trading_engine, 'stop'):
                self.trading_engine.stop()
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.log_message("Trading bot stopped", "INFO")
        except Exception as e:
            self.log_message(f"Error stopping bot: {e}", "ERROR")

    def close_all_positions(self):
        """Close all open positions"""
        try:
            reply = QMessageBox.question(self, 'Confirm Close All', 
                                       'Are you sure you want to close all positions?',
                                       QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                if hasattr(self.mt5_connector, 'get_positions'):
                    positions = self.mt5_connector.get_positions()
                    for pos in positions:
                        self.mt5_connector.close_position(pos['ticket'])
                    self.log_message(f"Closed {len(positions)} positions", "INFO")
        except Exception as e:
            self.log_message(f"Error closing positions: {e}", "ERROR")

    def on_strategy_changed(self, strategy_name: str):
        """Handle strategy change"""
        try:
            strategy_map = {
                'Scalping': 'scalping',
                'Intraday': 'pattern',
                'HFT': 'hft',
                'Arbitrage': 'arbitrage'
            }

            if hasattr(self.trading_engine, 'set_strategy'):
                self.trading_engine.set_strategy(strategy_map.get(strategy_name, 'scalping'))
                self.log_message(f"Strategy changed to: {strategy_name}", "INFO")
        except Exception as e:
            self.log_message(f"Error changing strategy: {e}", "ERROR")

    def log_message(self, message: str, level: str = "INFO"):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding for different log levels
        if level == "ERROR":
            color = "#F44336"
        elif level == "WARNING":
            color = "#FF9800"
        elif level == "SUCCESS":
            color = "#4CAF50"
        else:
            color = "#ffffff"

        formatted_message = f'<span style="color: #888888">[{timestamp}]</span> <span style="color: {color}"><b>{level}:</b> {message}</span>'
        self.log_text.append(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self):
        """Clear the log display"""
        self.log_text.clear()
        self.log_message("Logs cleared", "INFO")

    def export_logs(self):
        """Export logs to file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Logs", 
                f"auratrade_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt)"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.log_message(f"Logs exported to: {filename}", "SUCCESS")
        except Exception as e:
            self.log_message(f"Error exporting logs: {e}", "ERROR")

    def get_dark_theme_style(self) -> str:
        """Get dark theme stylesheet"""
        return """
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
            border: 2px solid #555555;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }

        QComboBox, QDoubleSpinBox, QSpinBox {
            border: 2px solid #555555;
            border-radius: 4px;
            padding: 5px;
            background-color: #3c3c3c;
        }

        QComboBox:hover, QDoubleSpinBox:hover, QSpinBox:hover {
            border-color: #2196F3;
        }

        QTableWidget {
            gridline-color: #555555;
            background-color: #3c3c3c;
            alternate-background-color: #484848;
        }

        QHeaderView::section {
            background-color: #555555;
            padding: 5px;
            border: 1px solid #666666;
        }

        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }

        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            padding: 8px 16px;
            border: 1px solid #555555;
        }

        QTabBar::tab:selected {
            background-color: #2196F3;
        }

        QLabel {
            color: #ffffff;
        }

        QTextEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
        }

        QScrollBar:vertical {
            background-color: #3c3c3c;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        """

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Stop the bot if running
            if hasattr(self.trading_engine, 'running') and self.trading_engine.running:
                reply = QMessageBox.question(self, 'Confirm Exit', 
                                           'Trading bot is running. Stop bot and exit?',
                                           QMessageBox.Yes | QMessageBox.No)

                if reply == QMessageBox.Yes:
                    self.stop_bot()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
        except Exception as e:
            event.accept()