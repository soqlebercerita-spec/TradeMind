"""
Trading dashboard for AuraTrade Bot GUI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
                           QTextEdit, QProgressBar, QGridLayout, QMessageBox)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from utils.logger import Logger

class TradingDashboard(QWidget):
    """Main trading dashboard widget"""

    emergency_stop_requested = pyqtSignal()

    def __init__(self, trading_engine, order_manager, risk_manager, parent=None):
        super().__init__(parent)

        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.logger = Logger().get_logger()

        self.setup_ui()
        self.setup_timers()

    def setup_ui(self):
        """Setup dashboard UI"""
        layout = QVBoxLayout(self)

        # Account info section
        account_group = self.create_account_info_section()
        layout.addWidget(account_group)

        # Control buttons
        controls_group = self.create_control_section()
        layout.addWidget(controls_group)

        # Trading status
        status_group = self.create_status_section()
        layout.addWidget(status_group)

        # Positions table
        positions_group = self.create_positions_section()
        layout.addWidget(positions_group)

        # Log section
        log_group = self.create_log_section()
        layout.addWidget(log_group)

    def create_account_info_section(self):
        """Create account information section"""
        group = QGroupBox("Account Information")
        layout = QGridLayout(group)

        # Account labels
        self.balance_label = QLabel("Balance: $0.00")
        self.equity_label = QLabel("Equity: $0.00")
        self.margin_label = QLabel("Margin: $0.00")
        self.free_margin_label = QLabel("Free Margin: $0.00")

        # Style labels
        font = QFont()
        font.setBold(True)
        for label in [self.balance_label, self.equity_label, self.margin_label, self.free_margin_label]:
            label.setFont(font)

        layout.addWidget(self.balance_label, 0, 0)
        layout.addWidget(self.equity_label, 0, 1)
        layout.addWidget(self.margin_label, 1, 0)
        layout.addWidget(self.free_margin_label, 1, 1)

        return group

    def create_control_section(self):
        """Create control buttons section"""
        group = QGroupBox("Trading Controls")
        layout = QHBoxLayout(group)

        self.start_button = QPushButton("Start Trading")
        self.stop_button = QPushButton("Stop Trading")
        self.emergency_button = QPushButton("EMERGENCY STOP")
        self.close_all_button = QPushButton("Close All Positions")

        # Style emergency button
        self.emergency_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        # Connect buttons
        self.start_button.clicked.connect(self.start_trading)
        self.stop_button.clicked.connect(self.stop_trading)
        self.emergency_button.clicked.connect(self.emergency_stop)
        self.close_all_button.clicked.connect(self.close_all_positions)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.emergency_button)
        layout.addWidget(self.close_all_button)

        return group

    def create_status_section(self):
        """Create trading status section"""
        group = QGroupBox("Trading Status")
        layout = QGridLayout(group)

        # Status labels
        self.status_label = QLabel("Status: Stopped")
        self.trades_today_label = QLabel("Trades Today: 0")
        self.win_rate_label = QLabel("Win Rate: 0.0%")
        self.daily_pnl_label = QLabel("Daily P&L: $0.00")

        # Progress bars
        self.win_rate_progress = QProgressBar()
        self.win_rate_progress.setMaximum(100)
        self.win_rate_progress.setValue(0)

        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.trades_today_label, 0, 1)
        layout.addWidget(self.win_rate_label, 1, 0)
        layout.addWidget(self.daily_pnl_label, 1, 1)
        layout.addWidget(QLabel("Win Rate Progress:"), 2, 0)
        layout.addWidget(self.win_rate_progress, 2, 1)

        return group

    def create_positions_section(self):
        """Create positions table section"""
        group = QGroupBox("Open Positions")
        layout = QVBoxLayout(group)

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Volume", "Price", "S/L", "T/P", "Profit"
        ])

        # Style table
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.positions_table)

        return group

    def create_log_section(self):
        """Create log display section"""
        group = QGroupBox("Trading Log")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)

        # Style log
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)

        layout.addWidget(self.log_text)

        return group

    def setup_timers(self):
        """Setup update timers"""
        # Account info timer
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        self.account_timer.start(2000)  # Update every 2 seconds

        # Positions timer
        self.positions_timer = QTimer()
        self.positions_timer.timeout.connect(self.update_positions)
        self.positions_timer.start(1000)  # Update every second

        # Status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second

    def update_account_info(self):
        """Update account information display"""
        try:
            if hasattr(self.trading_engine, 'mt5_connector'):
                account_info = self.trading_engine.mt5_connector.get_account_info()

                if account_info:
                    balance = account_info.get('balance', 0)
                    equity = account_info.get('equity', 0)
                    margin = account_info.get('margin', 0)
                    margin_free = account_info.get('margin_free', 0)

                    self.balance_label.setText(f"Balance: ${balance:.2f}")
                    self.equity_label.setText(f"Equity: ${equity:.2f}")
                    self.margin_label.setText(f"Margin: ${margin:.2f}")
                    self.free_margin_label.setText(f"Free Margin: ${margin_free:.2f}")

                    # Color code equity vs balance
                    if equity > balance:
                        self.equity_label.setStyleSheet("color: green;")
                    elif equity < balance:
                        self.equity_label.setStyleSheet("color: red;")
                    else:
                        self.equity_label.setStyleSheet("color: white;")

        except Exception as e:
            self.logger.error(f"Error updating account info: {e}")

    def update_positions(self):
        """Update positions table"""
        try:
            if hasattr(self.order_manager, 'get_active_positions'):
                positions = self.order_manager.get_active_positions()

                self.positions_table.setRowCount(len(positions))

                for row, pos in enumerate(positions):
                    self.positions_table.setItem(row, 0, QTableWidgetItem(str(pos.get('ticket', ''))))
                    self.positions_table.setItem(row, 1, QTableWidgetItem(str(pos.get('symbol', ''))))

                    pos_type = "BUY" if pos.get('type', 0) == 0 else "SELL"
                    self.positions_table.setItem(row, 2, QTableWidgetItem(pos_type))

                    self.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos.get('volume', 0):.2f}"))
                    self.positions_table.setItem(row, 4, QTableWidgetItem(f"{pos.get('price_open', 0):.5f}"))
                    self.positions_table.setItem(row, 5, QTableWidgetItem(f"{pos.get('sl', 0):.5f}"))
                    self.positions_table.setItem(row, 6, QTableWidgetItem(f"{pos.get('tp', 0):.5f}"))

                    profit = pos.get('profit', 0)
                    profit_item = QTableWidgetItem(f"${profit:.2f}")

                    # Color code profit
                    if profit > 0:
                        profit_item.setForeground(QColor('green'))
                    elif profit < 0:
                        profit_item.setForeground(QColor('red'))

                    self.positions_table.setItem(row, 7, profit_item)

        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")

    def update_status(self):
        """Update trading status"""
        try:
            if hasattr(self.trading_engine, 'get_status'):
                status = self.trading_engine.get_status()

                # Update status labels
                running = status.get('running', False)
                status_text = "Running" if running else "Stopped"
                self.status_label.setText(f"Status: {status_text}")

                trades_today = status.get('trades_today', 0)
                self.trades_today_label.setText(f"Trades Today: {trades_today}")

                win_rate = status.get('win_rate', 0)
                self.win_rate_label.setText(f"Win Rate: {win_rate:.1f}%")
                self.win_rate_progress.setValue(int(win_rate))

                daily_pnl = status.get('daily_pnl', 0)
                self.daily_pnl_label.setText(f"Daily P&L: ${daily_pnl:.2f}")

                # Color code daily P&L
                if daily_pnl > 0:
                    self.daily_pnl_label.setStyleSheet("color: green;")
                elif daily_pnl < 0:
                    self.daily_pnl_label.setStyleSheet("color: red;")
                else:
                    self.daily_pnl_label.setStyleSheet("color: white;")

        except Exception as e:
            self.logger.error(f"Error updating status: {e}")

    def start_trading(self):
        """Start trading"""
        try:
            if hasattr(self.trading_engine, 'start'):
                self.trading_engine.start()
                self.log_message("Trading started")
        except Exception as e:
            self.logger.error(f"Error starting trading: {e}")

    def stop_trading(self):
        """Stop trading"""
        try:
            if hasattr(self.trading_engine, 'stop'):
                self.trading_engine.stop()
                self.log_message("Trading stopped")
        except Exception as e:
            self.logger.error(f"Error stopping trading: {e}")

    def emergency_stop(self):
        """Emergency stop"""
        try:
            reply = QMessageBox.warning(
                self, 'Emergency Stop',
                'This will immediately stop trading and close all positions!\n\nAre you sure?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.emergency_stop_requested.emit()
                self.log_message("EMERGENCY STOP ACTIVATED")
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")

    def close_all_positions(self):
        """Close all positions"""
        try:
            reply = QMessageBox.question(
                self, 'Close All Positions',
                'Close all open positions?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if hasattr(self.order_manager, 'close_all_positions'):
                    count = self.order_manager.close_all_positions()
                    self.log_message(f"Closed {count} positions")
        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")

    def log_message(self, message: str):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)

        # Limit log size
        if self.log_text.document().lineCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()