
"""
Trading Dashboard for AuraTrade Bot
Real-time trading dashboard with comprehensive controls
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QProgressBar, QGroupBox, QFrame, QTextEdit, QLCDNumber)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.logger import Logger

class TradingDashboard(QWidget):
    """Real-time trading dashboard"""
    
    def __init__(self, trading_engine=None, order_manager=None, risk_manager=None):
        super().__init__()
        self.logger = Logger().get_logger()
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        
        # Dashboard data
        self.account_data = {}
        self.positions_data = []
        self.performance_data = {}
        
        self._setup_ui()
        self._setup_timers()
        
        self.logger.info("Trading Dashboard initialized")
    
    def _setup_ui(self):
        """Setup dashboard UI"""
        layout = QVBoxLayout()
        
        # Account info section
        account_group = self._create_account_section()
        layout.addWidget(account_group)
        
        # Performance metrics
        performance_group = self._create_performance_section()
        layout.addWidget(performance_group)
        
        # Active positions
        positions_group = self._create_positions_section()
        layout.addWidget(positions_group)
        
        # Market overview
        market_group = self._create_market_section()
        layout.addWidget(market_group)
        
        self.setLayout(layout)
    
    def _create_account_section(self) -> QGroupBox:
        """Create account information section"""
        group = QGroupBox("Account Information")
        layout = QGridLayout()
        
        # Account labels
        self.balance_label = QLabel("$0.00")
        self.equity_label = QLabel("$0.00")
        self.margin_label = QLabel("$0.00")
        self.free_margin_label = QLabel("$0.00")
        self.margin_level_label = QLabel("0%")
        
        # Style labels
        for label in [self.balance_label, self.equity_label, self.margin_label, 
                     self.free_margin_label, self.margin_level_label]:
            label.setFont(QFont("Arial", 12, QFont.Bold))
            label.setAlignment(Qt.AlignCenter)
        
        # Add to layout
        layout.addWidget(QLabel("Balance:"), 0, 0)
        layout.addWidget(self.balance_label, 0, 1)
        layout.addWidget(QLabel("Equity:"), 0, 2)
        layout.addWidget(self.equity_label, 0, 3)
        
        layout.addWidget(QLabel("Margin:"), 1, 0)
        layout.addWidget(self.margin_label, 1, 1)
        layout.addWidget(QLabel("Free Margin:"), 1, 2)
        layout.addWidget(self.free_margin_label, 1, 3)
        
        layout.addWidget(QLabel("Margin Level:"), 2, 0)
        layout.addWidget(self.margin_level_label, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_performance_section(self) -> QGroupBox:
        """Create performance metrics section"""
        group = QGroupBox("Performance Metrics")
        layout = QGridLayout()
        
        # Performance displays
        self.trades_today_lcd = QLCDNumber(3)
        self.win_rate_lcd = QLCDNumber(4)
        self.daily_pnl_lcd = QLCDNumber(6)
        
        # Progress bars
        self.win_rate_bar = QProgressBar()
        self.win_rate_bar.setRange(0, 100)
        self.win_rate_bar.setTextVisible(True)
        
        self.daily_target_bar = QProgressBar()
        self.daily_target_bar.setRange(0, 1000)  # $1000 daily target
        self.daily_target_bar.setTextVisible(True)
        
        # Add to layout
        layout.addWidget(QLabel("Trades Today:"), 0, 0)
        layout.addWidget(self.trades_today_lcd, 0, 1)
        
        layout.addWidget(QLabel("Win Rate:"), 1, 0)
        layout.addWidget(self.win_rate_lcd, 1, 1)
        layout.addWidget(self.win_rate_bar, 1, 2)
        
        layout.addWidget(QLabel("Daily P&L:"), 2, 0)
        layout.addWidget(self.daily_pnl_lcd, 2, 1)
        layout.addWidget(self.daily_target_bar, 2, 2)
        
        group.setLayout(layout)
        return group
    
    def _create_positions_section(self) -> QGroupBox:
        """Create positions table section"""
        group = QGroupBox("Active Positions")
        layout = QVBoxLayout()
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Volume", "Price", "Current", "P&L", "Action"
        ])
        
        # Style table
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.verticalHeader().setVisible(False)
        self.positions_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.positions_table)
        group.setLayout(layout)
        return group
    
    def _create_market_section(self) -> QGroupBox:
        """Create market overview section"""
        group = QGroupBox("Market Overview")
        layout = QGridLayout()
        
        # Symbol prices
        self.symbol_labels = {}
        self.price_labels = {}
        
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        for i, symbol in enumerate(symbols):
            row = i // 2
            col = (i % 2) * 2
            
            self.symbol_labels[symbol] = QLabel(symbol)
            self.price_labels[symbol] = QLabel("-.----")
            
            self.symbol_labels[symbol].setFont(QFont("Arial", 10, QFont.Bold))
            self.price_labels[symbol].setFont(QFont("Arial", 10))
            
            layout.addWidget(self.symbol_labels[symbol], row, col)
            layout.addWidget(self.price_labels[symbol], row, col + 1)
        
        group.setLayout(layout)
        return group
    
    def _setup_timers(self):
        """Setup update timers"""
        # Account update timer
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        self.account_timer.start(1000)  # 1 second
        
        # Positions update timer
        self.positions_timer = QTimer()
        self.positions_timer.timeout.connect(self.update_positions)
        self.positions_timer.start(2000)  # 2 seconds
        
        # Performance update timer
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance)
        self.performance_timer.start(5000)  # 5 seconds
        
        # Market data timer
        self.market_timer = QTimer()
        self.market_timer.timeout.connect(self.update_market_data)
        self.market_timer.start(500)  # 0.5 seconds
    
    def update_account_info(self):
        """Update account information"""
        try:
            if not self.trading_engine:
                return
            
            # Get account info from trading engine
            if hasattr(self.trading_engine, 'mt5_connector'):
                account_info = self.trading_engine.mt5_connector.get_account_info()
                
                if account_info:
                    balance = account_info.get('balance', 0)
                    equity = account_info.get('equity', 0)
                    margin = account_info.get('margin', 0)
                    free_margin = account_info.get('margin_free', 0)
                    margin_level = account_info.get('margin_level', 0)
                    
                    # Update labels
                    self.balance_label.setText(f"${balance:.2f}")
                    self.equity_label.setText(f"${equity:.2f}")
                    self.margin_label.setText(f"${margin:.2f}")
                    self.free_margin_label.setText(f"${free_margin:.2f}")
                    self.margin_level_label.setText(f"{margin_level:.1f}%")
                    
                    # Color coding for margin level
                    if margin_level < 200:
                        self.margin_level_label.setStyleSheet("color: red; font-weight: bold;")
                    elif margin_level < 500:
                        self.margin_level_label.setStyleSheet("color: orange; font-weight: bold;")
                    else:
                        self.margin_level_label.setStyleSheet("color: green; font-weight: bold;")
        
        except Exception as e:
            self.logger.error(f"Error updating account info: {e}")
    
    def update_positions(self):
        """Update positions table"""
        try:
            if not self.trading_engine or not hasattr(self.trading_engine, 'mt5_connector'):
                return
            
            positions = self.trading_engine.mt5_connector.get_positions()
            
            # Update table
            self.positions_table.setRowCount(len(positions))
            
            for row, position in enumerate(positions):
                # Create table items
                items = [
                    QTableWidgetItem(str(position.get('ticket', ''))),
                    QTableWidgetItem(position.get('symbol', '')),
                    QTableWidgetItem('Buy' if position.get('type', 0) == 0 else 'Sell'),
                    QTableWidgetItem(f"{position.get('volume', 0):.2f}"),
                    QTableWidgetItem(f"{position.get('price_open', 0):.5f}"),
                    QTableWidgetItem(f"{position.get('price_current', 0):.5f}"),
                    QTableWidgetItem(f"{position.get('profit', 0):.2f}"),
                ]
                
                # Add items to table
                for col, item in enumerate(items):
                    if col == 6:  # P&L column
                        profit = position.get('profit', 0)
                        if profit > 0:
                            item.setForeground(QColor('green'))
                        elif profit < 0:
                            item.setForeground(QColor('red'))
                    
                    self.positions_table.setItem(row, col, item)
                
                # Add close button
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(
                    lambda checked, ticket=position.get('ticket'): self.close_position(ticket)
                )
                self.positions_table.setCellWidget(row, 7, close_btn)
        
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def update_performance(self):
        """Update performance metrics"""
        try:
            if not self.trading_engine:
                return
            
            status = self.trading_engine.get_status()
            
            # Update LCDs
            self.trades_today_lcd.display(status.get('trades_today', 0))
            self.win_rate_lcd.display(status.get('win_rate', 0))
            self.daily_pnl_lcd.display(status.get('daily_pnl', 0))
            
            # Update progress bars
            win_rate = status.get('win_rate', 0)
            self.win_rate_bar.setValue(int(win_rate))
            
            daily_pnl = status.get('daily_pnl', 0)
            target_progress = min(100, max(0, (daily_pnl / 1000) * 100))
            self.daily_target_bar.setValue(int(daily_pnl if daily_pnl > 0 else 0))
            
            # Color coding for P&L LCD
            if daily_pnl > 0:
                self.daily_pnl_lcd.setStyleSheet("color: green;")
            elif daily_pnl < 0:
                self.daily_pnl_lcd.setStyleSheet("color: red;")
            else:
                self.daily_pnl_lcd.setStyleSheet("color: black;")
        
        except Exception as e:
            self.logger.error(f"Error updating performance: {e}")
    
    def update_market_data(self):
        """Update market data prices"""
        try:
            if not self.trading_engine or not hasattr(self.trading_engine, 'mt5_connector'):
                return
            
            for symbol in self.price_labels.keys():
                tick = self.trading_engine.mt5_connector.get_tick(symbol)
                if tick:
                    bid = tick.get('bid', 0)
                    ask = tick.get('ask', 0)
                    self.price_labels[symbol].setText(f"{bid:.5f}/{ask:.5f}")
        
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
    
    def close_position(self, ticket: int):
        """Close specific position"""
        try:
            if self.trading_engine and hasattr(self.trading_engine, 'mt5_connector'):
                result = self.trading_engine.mt5_connector.close_position(ticket)
                if result.get('retcode') == 10009:
                    self.logger.info(f"Position #{ticket} closed successfully")
                else:
                    self.logger.error(f"Failed to close position #{ticket}: {result.get('comment')}")
        
        except Exception as e:
            self.logger.error(f"Error closing position {ticket}: {e}")
"""
Trading Dashboard for AuraTrade Bot
Real-time trading dashboard with charts and metrics
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
from typing import Dict, Any

class TradingDashboard(QWidget):
    """Real-time trading dashboard"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize dashboard UI"""
        layout = QVBoxLayout(self)
        
        # Dashboard content
        self.metrics_widget = self.create_metrics_widget()
        layout.addWidget(self.metrics_widget)
    
    def create_metrics_widget(self) -> QWidget:
        """Create metrics display widget"""
        widget = QGroupBox("Trading Metrics")
        layout = QGridLayout(widget)
        
        # Placeholder metrics
        self.balance_label = QLabel("Balance: $0.00")
        self.profit_label = QLabel("P&L: $0.00")
        self.trades_label = QLabel("Trades: 0")
        self.win_rate_label = QLabel("Win Rate: 0%")
        
        layout.addWidget(self.balance_label, 0, 0)
        layout.addWidget(self.profit_label, 0, 1)
        layout.addWidget(self.trades_label, 1, 0)
        layout.addWidget(self.win_rate_label, 1, 1)
        
        return widget
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update dashboard metrics"""
        try:
            self.balance_label.setText(f"Balance: ${metrics.get('balance', 0):.2f}")
            self.profit_label.setText(f"P&L: ${metrics.get('profit', 0):.2f}")
            self.trades_label.setText(f"Trades: {metrics.get('trades', 0)}")
            self.win_rate_label.setText(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
        except Exception as e:
            pass
