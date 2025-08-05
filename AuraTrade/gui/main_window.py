"""
Professional PyQt5 GUI for AuraTrade Bot
Real-time trading dashboard with system tray support
"""

import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QTabWidget, QGroupBox, QProgressBar, QSystemTrayIcon, QMenu,
    QAction, QSplitter, QFrame, QScrollArea, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

from utils.logger import Logger

class TradingStatusWidget(QWidget):
    """Real-time trading status display"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # Status indicators
        self.connection_label = QLabel("🔴 Disconnected")
        self.balance_label = QLabel("Balance: $0.00")
        self.equity_label = QLabel("Equity: $0.00")
        self.pnl_label = QLabel("P&L: $0.00")
        self.positions_label = QLabel("Positions: 0")
        self.trades_label = QLabel("Trades Today: 0")
        self.winrate_label = QLabel("Win Rate: 0%")

        # Style labels
        for label in [self.connection_label, self.balance_label, self.equity_label,
                     self.pnl_label, self.positions_label, self.trades_label, self.winrate_label]:
            label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; }")

        # Layout
        layout.addWidget(self.connection_label, 0, 0)
        layout.addWidget(self.balance_label, 0, 1)
        layout.addWidget(self.equity_label, 0, 2)
        layout.addWidget(self.pnl_label, 1, 0)
        layout.addWidget(self.positions_label, 1, 1)
        layout.addWidget(self.trades_label, 1, 2)
        layout.addWidget(self.winrate_label, 2, 0, 1, 3)

        self.setLayout(layout)

    def update_status(self, status: Dict[str, Any]):
        """Update status display"""
        try:
            # Connection status
            if status.get('connected', False):
                self.connection_label.setText("🟢 Connected")
                self.connection_label.setStyleSheet("QLabel { color: green; font-weight: bold; padding: 5px; }")
            else:
                self.connection_label.setText("🔴 Disconnected")
                self.connection_label.setStyleSheet("QLabel { color: red; font-weight: bold; padding: 5px; }")

            # Financial info
            balance = status.get('balance', 0)
            equity = status.get('equity', 0)
            pnl = status.get('daily_pnl', 0)

            self.balance_label.setText(f"Balance: ${balance:,.2f}")
            self.equity_label.setText(f"Equity: ${equity:,.2f}")

            # P&L color coding
            if pnl > 0:
                self.pnl_label.setText(f"P&L: +${pnl:,.2f}")
                self.pnl_label.setStyleSheet("QLabel { color: green; font-weight: bold; padding: 5px; }")
            elif pnl < 0:
                self.pnl_label.setText(f"P&L: -${abs(pnl):,.2f}")
                self.pnl_label.setStyleSheet("QLabel { color: red; font-weight: bold; padding: 5px; }")
            else:
                self.pnl_label.setText("P&L: $0.00")
                self.pnl_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; }")

            # Trading stats
            self.positions_label.setText(f"Positions: {status.get('active_positions', 0)}")
            self.trades_label.setText(f"Trades Today: {status.get('trades_today', 0)}")

            win_rate = status.get('win_rate', 0)
            self.winrate_label.setText(f"Win Rate: {win_rate:.1f}%")

            # Win rate color coding
            if win_rate >= 70:
                self.winrate_label.setStyleSheet("QLabel { color: green; font-weight: bold; padding: 5px; }")
            elif win_rate >= 50:
                self.winrate_label.setStyleSheet("QLabel { color: orange; font-weight: bold; padding: 5px; }")
            else:
                self.winrate_label.setStyleSheet("QLabel { color: red; font-weight: bold; padding: 5px; }")

        except Exception as e:
            print(f"Error updating status: {e}")

class PositionsTable(QTableWidget):
    """Table widget for displaying open positions"""

    def __init__(self):
        super().__init__()
        self.init_table()

    def init_table(self):
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            'Ticket', 'Symbol', 'Type', 'Volume', 'Open Price', 'Current Price', 'P&L', 'Actions'
        ])

        # Style table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)

    def update_positions(self, positions: list):
        """Update positions table"""
        try:
            self.setRowCount(len(positions))

            for row, pos in enumerate(positions):
                self.setItem(row, 0, QTableWidgetItem(str(pos.get('ticket', ''))))
                self.setItem(row, 1, QTableWidgetItem(pos.get('symbol', '')))
                self.setItem(row, 2, QTableWidgetItem('BUY' if pos.get('type', 0) == 0 else 'SELL'))
                self.setItem(row, 3, QTableWidgetItem(f"{pos.get('volume', 0):.2f}"))
                self.setItem(row, 4, QTableWidgetItem(f"{pos.get('price_open', 0):.5f}"))
                self.setItem(row, 5, QTableWidgetItem(f"{pos.get('price_current', 0):.5f}"))

                # P&L with color coding
                pnl = pos.get('profit', 0)
                pnl_item = QTableWidgetItem(f"${pnl:.2f}")
                if pnl > 0:
                    pnl_item.setBackground(QColor(144, 238, 144))  # Light green
                elif pnl < 0:
                    pnl_item.setBackground(QColor(255, 182, 193))  # Light red
                self.setItem(row, 6, pnl_item)

                # Close button
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(lambda checked, ticket=pos.get('ticket'): self.close_position(ticket))
                close_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
                self.setCellWidget(row, 7, close_btn)

        except Exception as e:
            print(f"Error updating positions table: {e}")

    def close_position(self, ticket):
        """Close position signal"""
        # This would connect to the main window's close position method
        print(f"Close position requested: {ticket}")

class LogWidget(QTextEdit):
    """Enhanced log display widget"""

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)  # Limit log entries

        # Style
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)

    def add_log_entry(self, level: str, message: str):
        """Add formatted log entry"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Color coding by level
            colors = {
                'INFO': '#00ff00',
                'WARNING': '#ffff00',
                'ERROR': '#ff0000',
                'DEBUG': '#888888'
            }

            color = colors.get(level.upper(), '#ffffff')

            formatted_message = f'<span style="color: {color};">[{timestamp}] {level.upper()}: {message}</span>'
            self.append(formatted_message)

            # Auto-scroll to bottom
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

        except Exception as e:
            print(f"Error adding log entry: {e}")

class MainWindow(QMainWindow):
    """Professional main window for AuraTrade Bot"""

    def __init__(self, trading_engine=None, order_manager=None, risk_manager=None, data_manager=None):
        super().__init__()

        self.logger = Logger().get_logger()
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.data_manager = data_manager

        # Initialize UI
        self.init_ui()
        self.init_system_tray()
        self.init_timers()

        self.logger.info("MainWindow initialized")

    def init_ui(self):
        """Initialize user interface"""
        try:
            self.setWindowTitle("AuraTrade Bot - Professional Trading System")
            self.setGeometry(100, 100, 1400, 900)
            self.setMinimumSize(1200, 800)

            # Set application style
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    padding: 8px 15px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #4a90e2;
                }
                QGroupBox {
                    border: 2px solid #555555;
                    border-radius: 5px;
                    margin: 10px;
                    padding-top: 10px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 10px 0 10px;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #357abd;
                }
                QPushButton:pressed {
                    background-color: #2968a3;
                }
            """)

            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            # Create main layout with splitter
            main_layout = QVBoxLayout(central_widget)

            # Create control buttons
            control_layout = QHBoxLayout()

            self.start_btn = QPushButton("🚀 Start Trading")
            self.stop_btn = QPushButton("⏹️ Stop Trading")
            self.settings_btn = QPushButton("⚙️ Settings")
            self.close_all_btn = QPushButton("❌ Close All Positions")

            self.start_btn.clicked.connect(self.start_trading)
            self.stop_btn.clicked.connect(self.stop_trading)
            self.settings_btn.clicked.connect(self.show_settings)
            self.close_all_btn.clicked.connect(self.close_all_positions)

            # Style control buttons
            self.start_btn.setStyleSheet("QPushButton { background-color: #28a745; }")
            self.stop_btn.setStyleSheet("QPushButton { background-color: #dc3545; }")
            self.close_all_btn.setStyleSheet("QPushButton { background-color: #fd7e14; }")

            control_layout.addWidget(self.start_btn)
            control_layout.addWidget(self.stop_btn)
            control_layout.addWidget(self.settings_btn)
            control_layout.addWidget(self.close_all_btn)
            control_layout.addStretch()

            main_layout.addLayout(control_layout)

            # Create main splitter
            main_splitter = QSplitter(Qt.Vertical)

            # Top section - Status and positions
            top_widget = QWidget()
            top_layout = QHBoxLayout(top_widget)

            # Status section
            status_group = QGroupBox("Trading Status")
            status_layout = QVBoxLayout(status_group)
            self.status_widget = TradingStatusWidget()
            status_layout.addWidget(self.status_widget)

            # Positions section
            positions_group = QGroupBox("Open Positions")
            positions_layout = QVBoxLayout(positions_group)
            self.positions_table = PositionsTable()
            positions_layout.addWidget(self.positions_table)

            top_layout.addWidget(status_group, 1)
            top_layout.addWidget(positions_group, 2)

            # Create tab widget for bottom section
            self.tab_widget = QTabWidget()

            # Logs tab
            log_tab = QWidget()
            log_layout = QVBoxLayout(log_tab)
            self.log_widget = LogWidget()
            log_layout.addWidget(self.log_widget)
            self.tab_widget.addTab(log_tab, "📋 Logs")

            # Performance tab
            performance_tab = self.create_performance_tab()
            self.tab_widget.addTab(performance_tab, "📊 Performance")

            # Risk tab
            risk_tab = self.create_risk_tab()
            self.tab_widget.addTab(risk_tab, "⚠️ Risk Management")

            # Strategies tab
            strategies_tab = self.create_strategies_tab()
            self.tab_widget.addTab(strategies_tab, "🧠 Strategies")

            # Add widgets to splitter
            main_splitter.addWidget(top_widget)
            main_splitter.addWidget(self.tab_widget)
            main_splitter.setStretchFactor(0, 1)
            main_splitter.setStretchFactor(1, 1)

            main_layout.addWidget(main_splitter)

            # Status bar
            self.statusBar().showMessage("AuraTrade Bot Ready")

        except Exception as e:
            self.logger.error(f"Error initializing UI: {e}")

    def create_performance_tab(self) -> QWidget:
        """Create performance monitoring tab"""
        try:
            widget = QWidget()
            layout = QVBoxLayout(widget)

            # Performance metrics
            metrics_group = QGroupBox("Performance Metrics")
            metrics_layout = QGridLayout(metrics_group)

            self.total_trades_label = QLabel("Total Trades: 0")
            self.win_rate_label = QLabel("Win Rate: 0%")
            self.profit_factor_label = QLabel("Profit Factor: 0.00")
            self.max_drawdown_label = QLabel("Max Drawdown: 0%")
            self.daily_return_label = QLabel("Daily Return: 0%")
            self.monthly_return_label = QLabel("Monthly Return: 0%")

            metrics_layout.addWidget(self.total_trades_label, 0, 0)
            metrics_layout.addWidget(self.win_rate_label, 0, 1)
            metrics_layout.addWidget(self.profit_factor_label, 1, 0)
            metrics_layout.addWidget(self.max_drawdown_label, 1, 1)
            metrics_layout.addWidget(self.daily_return_label, 2, 0)
            metrics_layout.addWidget(self.monthly_return_label, 2, 1)

            layout.addWidget(metrics_group)

            # Performance chart placeholder
            chart_group = QGroupBox("Performance Chart")
            chart_layout = QVBoxLayout(chart_group)
            chart_placeholder = QLabel("Performance chart will be displayed here")
            chart_placeholder.setAlignment(Qt.AlignCenter)
            chart_placeholder.setStyleSheet("QLabel { color: #888888; font-style: italic; }")
            chart_layout.addWidget(chart_placeholder)

            layout.addWidget(chart_group)

            return widget

        except Exception as e:
            self.logger.error(f"Error creating performance tab: {e}")
            return QWidget()

    def create_risk_tab(self) -> QWidget:
        """Create risk management tab"""
        try:
            widget = QWidget()
            layout = QVBoxLayout(widget)

            # Risk metrics
            risk_group = QGroupBox("Risk Metrics")
            risk_layout = QGridLayout(risk_group)

            self.daily_risk_label = QLabel("Daily Risk Used: 0%")
            self.exposure_label = QLabel("Current Exposure: 0%")
            self.consecutive_losses_label = QLabel("Consecutive Losses: 0")
            self.emergency_stop_label = QLabel("Emergency Stop: ❌")

            risk_layout.addWidget(self.daily_risk_label, 0, 0)
            risk_layout.addWidget(self.exposure_label, 0, 1)
            risk_layout.addWidget(self.consecutive_losses_label, 1, 0)
            risk_layout.addWidget(self.emergency_stop_label, 1, 1)

            layout.addWidget(risk_group)

            # Risk controls
            controls_group = QGroupBox("Risk Controls")
            controls_layout = QFormLayout(controls_group)

            self.max_risk_spin = QDoubleSpinBox()
            self.max_risk_spin.setRange(0.01, 0.10)
            self.max_risk_spin.setValue(0.02)
            self.max_risk_spin.setSingleStep(0.01)
            self.max_risk_spin.setSuffix("%")

            self.max_drawdown_spin = QDoubleSpinBox()
            self.max_drawdown_spin.setRange(0.05, 0.50)
            self.max_drawdown_spin.setValue(0.10)
            self.max_drawdown_spin.setSingleStep(0.01)
            self.max_drawdown_spin.setSuffix("%")

            controls_layout.addRow("Max Risk Per Trade:", self.max_risk_spin)
            controls_layout.addRow("Max Drawdown:", self.max_drawdown_spin)

            update_risk_btn = QPushButton("Update Risk Settings")
            update_risk_btn.clicked.connect(self.update_risk_settings)
            controls_layout.addRow(update_risk_btn)

            layout.addWidget(controls_group)

            return widget

        except Exception as e:
            self.logger.error(f"Error creating risk tab: {e}")
            return QWidget()

    def create_strategies_tab(self) -> QWidget:
        """Create strategies monitoring tab"""
        try:
            widget = QWidget()
            layout = QVBoxLayout(widget)

            # Strategy status
            status_group = QGroupBox("Strategy Status")
            status_layout = QGridLayout(status_group)

            self.hft_status_label = QLabel("HFT Strategy: ✅ Active")
            self.scalping_status_label = QLabel("Scalping Strategy: ✅ Active")
            self.swing_status_label = QLabel("Swing Strategy: ✅ Active")
            self.arbitrage_status_label = QLabel("Arbitrage Strategy: ✅ Active")

            status_layout.addWidget(self.hft_status_label, 0, 0)
            status_layout.addWidget(self.scalping_status_label, 0, 1)
            status_layout.addWidget(self.swing_status_label, 1, 0)
            status_layout.addWidget(self.arbitrage_status_label, 1, 1)

            layout.addWidget(status_group)

            # Strategy performance
            performance_group = QGroupBox("Strategy Performance")
            performance_layout = QVBoxLayout(performance_group)

            self.strategy_table = QTableWidget()
            self.strategy_table.setColumnCount(4)
            self.strategy_table.setHorizontalHeaderLabels(['Strategy', 'Trades', 'Win Rate', 'P&L'])

            performance_layout.addWidget(self.strategy_table)
            layout.addWidget(performance_group)

            return widget

        except Exception as e:
            self.logger.error(f"Error creating strategies tab: {e}")
            return QWidget()

    def init_system_tray(self):
        """Initialize system tray functionality"""
        try:
            self.tray_icon = QSystemTrayIcon(self)

            # Create tray menu
            tray_menu = QMenu()

            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)

            hide_action = QAction("Hide", self)
            hide_action.triggered.connect(self.hide)

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.close)

            tray_menu.addAction(show_action)
            tray_menu.addAction(hide_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.setToolTip("AuraTrade Bot")

            # Set tray icon (placeholder)
            icon = self.style().standardIcon(self.style().SP_ComputerIcon)
            self.tray_icon.setIcon(icon)

            self.tray_icon.show()

        except Exception as e:
            self.logger.error(f"Error initializing system tray: {e}")

    def init_timers(self):
        """Initialize update timers"""
        try:
            # Status update timer
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_display)
            self.status_timer.start(2000)  # Update every 2 seconds

            # Log update timer
            self.log_timer = QTimer()
            self.log_timer.timeout.connect(self.update_logs)
            self.log_timer.start(1000)  # Update every 1 second

        except Exception as e:
            self.logger.error(f"Error initializing timers: {e}")

    def update_display(self):
        """Update all display elements"""
        try:
            if self.trading_engine:
                # Get status from trading engine
                status = self.trading_engine.get_status()
                self.status_widget.update_status(status)

                # Update status bar
                if status.get('running', False):
                    self.statusBar().showMessage("🟢 Trading Active")
                else:
                    self.statusBar().showMessage("⏸️ Trading Paused")

                # Update positions table
                if hasattr(self.trading_engine.mt5, 'get_positions'):
                    positions = self.trading_engine.mt5.get_positions()
                    self.positions_table.update_positions(positions)

        except Exception as e:
            self.logger.error(f"Error updating display: {e}")

    def update_logs(self):
        """Update log display"""
        # This would connect to the logging system
        # For now, just add sample entries periodically
        pass

    def start_trading(self):
        """Start trading engine"""
        try:
            if self.trading_engine:
                self.trading_engine.start()
                self.log_widget.add_log_entry("INFO", "Trading engine started")

        except Exception as e:
            self.logger.error(f"Error starting trading: {e}")

    def stop_trading(self):
        """Stop trading engine"""
        try:
            if self.trading_engine:
                self.trading_engine.stop()
                self.log_widget.add_log_entry("INFO", "Trading engine stopped")

        except Exception as e:
            self.logger.error(f"Error stopping trading: {e}")

    def close_all_positions(self):
        """Close all open positions"""
        try:
            if self.trading_engine:
                self.trading_engine.force_close_all()
                self.log_widget.add_log_entry("WARNING", "All positions closed manually")

        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")

    def show_settings(self):
        """Show settings dialog"""
        try:
            dialog = SettingsDialog(self)
            dialog.exec_()

        except Exception as e:
            self.logger.error(f"Error showing settings: {e}")

    def update_risk_settings(self):
        """Update risk management settings"""
        try:
            if self.risk_manager:
                self.risk_manager.max_risk_per_trade = self.max_risk_spin.value()
                self.risk_manager.max_drawdown = self.max_drawdown_spin.value()
                self.log_widget.add_log_entry("INFO", "Risk settings updated")

        except Exception as e:
            self.logger.error(f"Error updating risk settings: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Hide to system tray instead of closing
            if self.tray_icon.isVisible():
                self.hide()
                event.ignore()
            else:
                event.accept()

        except Exception as e:
            self.logger.error(f"Error handling close event: {e}")
            event.accept()

class SettingsDialog(QDialog):
    """Settings configuration dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AuraTrade Settings")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Trading settings
        trading_group = QGroupBox("Trading Settings")
        trading_layout = QFormLayout(trading_group)

        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 50)
        self.max_positions_spin.setValue(10)

        self.max_trades_spin = QSpinBox()
        self.max_trades_spin.setRange(1, 200)
        self.max_trades_spin.setValue(50)

        trading_layout.addRow("Max Positions:", self.max_positions_spin)
        trading_layout.addRow("Max Daily Trades:", self.max_trades_spin)

        layout.addWidget(trading_group)

        # Notification settings
        notification_group = QGroupBox("Notifications")
        notification_layout = QFormLayout(notification_group)

        self.telegram_enabled = QCheckBox()
        self.telegram_token = QLineEdit()
        self.telegram_chat_id = QLineEdit()

        notification_layout.addRow("Enable Telegram:", self.telegram_enabled)
        notification_layout.addRow("Bot Token:", self.telegram_token)
        notification_layout.addRow("Chat ID:", self.telegram_chat_id)

        layout.addWidget(notification_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)