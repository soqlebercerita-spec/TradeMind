
"""
Trading dashboard for AuraTrade Bot GUI
Displays trade statistics, P&L, equity curve, and performance metrics
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class TradingDashboard(QWidget):
    """Main trading dashboard widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trading_data = {
            'equity': [],
            'balance': [],
            'trades': [],
            'drawdown': [],
            'timestamps': []
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dashboard UI"""
        main_layout = QVBoxLayout(self)
        
        # Top row - Key metrics
        metrics_layout = QHBoxLayout()
        
        # Account metrics
        account_group = QGroupBox("Account Metrics")
        account_layout = QGridLayout(account_group)
        
        self.balance_label = QLabel("$0.00")
        self.balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        account_layout.addWidget(QLabel("Balance:"), 0, 0)
        account_layout.addWidget(self.balance_label, 0, 1)
        
        self.equity_label = QLabel("$0.00")
        self.equity_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        account_layout.addWidget(QLabel("Equity:"), 1, 0)
        account_layout.addWidget(self.equity_label, 1, 1)
        
        self.margin_label = QLabel("$0.00")
        account_layout.addWidget(QLabel("Margin:"), 2, 0)
        account_layout.addWidget(self.margin_label, 2, 1)
        
        self.free_margin_label = QLabel("$0.00")
        account_layout.addWidget(QLabel("Free Margin:"), 3, 0)
        account_layout.addWidget(self.free_margin_label, 3, 1)
        
        metrics_layout.addWidget(account_group)
        
        # Trading metrics
        trading_group = QGroupBox("Trading Metrics")
        trading_layout = QGridLayout(trading_group)
        
        self.total_trades_label = QLabel("0")
        self.total_trades_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        trading_layout.addWidget(QLabel("Total Trades:"), 0, 0)
        trading_layout.addWidget(self.total_trades_label, 0, 1)
        
        self.win_rate_label = QLabel("0%")
        self.win_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        trading_layout.addWidget(QLabel("Win Rate:"), 1, 0)
        trading_layout.addWidget(self.win_rate_label, 1, 1)
        
        self.profit_factor_label = QLabel("0.00")
        trading_layout.addWidget(QLabel("Profit Factor:"), 2, 0)
        trading_layout.addWidget(self.profit_factor_label, 2, 1)
        
        self.max_dd_label = QLabel("0%")
        self.max_dd_label.setStyleSheet("color: #F44336;")
        trading_layout.addWidget(QLabel("Max Drawdown:"), 3, 0)
        trading_layout.addWidget(self.max_dd_label, 3, 1)
        
        metrics_layout.addWidget(trading_group)
        
        # Daily P&L
        daily_group = QGroupBox("Today's Performance")
        daily_layout = QGridLayout(daily_group)
        
        self.daily_pnl_label = QLabel("$0.00")
        self.daily_pnl_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        daily_layout.addWidget(QLabel("Daily P&L:"), 0, 0)
        daily_layout.addWidget(self.daily_pnl_label, 0, 1)
        
        self.daily_trades_label = QLabel("0")
        daily_layout.addWidget(QLabel("Trades Today:"), 1, 0)
        daily_layout.addWidget(self.daily_trades_label, 1, 1)
        
        self.daily_wins_label = QLabel("0")
        daily_layout.addWidget(QLabel("Wins:"), 2, 0)
        daily_layout.addWidget(self.daily_wins_label, 2, 1)
        
        self.daily_losses_label = QLabel("0")
        daily_layout.addWidget(QLabel("Losses:"), 3, 0)
        daily_layout.addWidget(self.daily_losses_label, 3, 1)
        
        metrics_layout.addWidget(daily_group)
        
        main_layout.addLayout(metrics_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        
        # Equity curve
        equity_group = QGroupBox("Equity Curve")
        equity_layout = QVBoxLayout(equity_group)
        
        self.equity_chart = pg.PlotWidget(title="Equity & Balance")
        self.equity_chart.setLabel('left', 'Amount ($)')
        self.equity_chart.setLabel('bottom', 'Time')
        self.equity_chart.showGrid(x=True, y=True)
        
        self.equity_line = self.equity_chart.plot(pen=pg.mkPen('#4CAF50', width=2), name="Equity")
        self.balance_line = self.equity_chart.plot(pen=pg.mkPen('#2196F3', width=2), name="Balance")
        
        equity_layout.addWidget(self.equity_chart)
        charts_layout.addWidget(equity_group)
        
        # Drawdown chart
        dd_group = QGroupBox("Drawdown")
        dd_layout = QVBoxLayout(dd_group)
        
        self.dd_chart = pg.PlotWidget(title="Drawdown %")
        self.dd_chart.setLabel('left', 'Drawdown (%)')
        self.dd_chart.setLabel('bottom', 'Time')
        self.dd_chart.showGrid(x=True, y=True)
        
        self.dd_line = self.dd_chart.plot(pen=pg.mkPen('#F44336', width=2), name="Drawdown")
        self.dd_chart.getPlotItem().invertY(True)  # Invert Y axis for drawdown
        
        dd_layout.addWidget(self.dd_chart)
        charts_layout.addWidget(dd_group)
        
        main_layout.addLayout(charts_layout)
        
        # Open positions table
        positions_group = QGroupBox("Open Positions")
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Type", "Volume", "Open Price", "Current Price", "P&L", "TP", "SL"
        ])
        self.positions_table.horizontalHeader().setStretchLastSection(True)
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        positions_layout.addWidget(self.positions_table)
        
        # Emergency stop button
        emergency_layout = QHBoxLayout()
        emergency_layout.addStretch()
        
        self.emergency_button = QPushButton("🚨 EMERGENCY STOP")
        self.emergency_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        self.emergency_button.clicked.connect(self.emergency_stop_clicked)
        
        emergency_layout.addWidget(self.emergency_button)
        emergency_layout.addStretch()
        
        positions_layout.addLayout(emergency_layout)
        main_layout.addWidget(positions_group)
        
    def update_account_metrics(self, balance: float, equity: float, margin: float, free_margin: float):
        """Update account metrics display"""
        self.balance_label.setText(f"${balance:,.2f}")
        self.equity_label.setText(f"${equity:,.2f}")
        self.margin_label.setText(f"${margin:,.2f}")
        self.free_margin_label.setText(f"${free_margin:,.2f}")
        
        # Update color based on equity vs balance
        if equity > balance:
            self.equity_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        elif equity < balance:
            self.equity_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #F44336;")
        else:
            self.equity_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
    
    def update_trading_metrics(self, total_trades: int, win_rate: float, profit_factor: float, max_drawdown: float):
        """Update trading performance metrics"""
        self.total_trades_label.setText(str(total_trades))
        self.win_rate_label.setText(f"{win_rate:.1f}%")
        self.profit_factor_label.setText(f"{profit_factor:.2f}")
        self.max_dd_label.setText(f"{max_drawdown:.2f}%")
        
        # Color coding for win rate
        if win_rate >= 60:
            self.win_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        elif win_rate >= 50:
            self.win_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FB8C00;")
        else:
            self.win_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
    
    def update_daily_performance(self, daily_pnl: float, trades: int, wins: int, losses: int):
        """Update daily performance metrics"""
        self.daily_pnl_label.setText(f"${daily_pnl:,.2f}")
        self.daily_trades_label.setText(str(trades))
        self.daily_wins_label.setText(str(wins))
        self.daily_losses_label.setText(str(losses))
        
        # Color code daily P&L
        if daily_pnl > 0:
            self.daily_pnl_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        elif daily_pnl < 0:
            self.daily_pnl_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
        else:
            self.daily_pnl_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666;")
    
    def update_equity_curve(self, timestamps: List[datetime], equity_data: List[float], balance_data: List[float]):
        """Update equity curve chart"""
        if len(timestamps) == 0:
            return
            
        # Convert timestamps to seconds since epoch
        x_data = [(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]  # Hours
        
        self.equity_line.setData(x_data, equity_data)
        self.balance_line.setData(x_data, balance_data)
        
        # Store data for reference
        self.trading_data['timestamps'] = timestamps
        self.trading_data['equity'] = equity_data
        self.trading_data['balance'] = balance_data
    
    def update_drawdown_chart(self, timestamps: List[datetime], drawdown_data: List[float]):
        """Update drawdown chart"""
        if len(timestamps) == 0:
            return
            
        # Convert timestamps to hours
        x_data = [(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]
        
        self.dd_line.setData(x_data, drawdown_data)
        
        # Store data
        self.trading_data['drawdown'] = drawdown_data
    
    def update_positions_table(self, positions: List[Dict[str, Any]]):
        """Update open positions table"""
        self.positions_table.setRowCount(len(positions))
        
        for row, pos in enumerate(positions):
            self.positions_table.setItem(row, 0, QTableWidgetItem(pos.get('symbol', '')))
            self.positions_table.setItem(row, 1, QTableWidgetItem(pos.get('type', '')))
            self.positions_table.setItem(row, 2, QTableWidgetItem(f"{pos.get('volume', 0):.2f}"))
            self.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos.get('price_open', 0):.5f}"))
            self.positions_table.setItem(row, 4, QTableWidgetItem(f"{pos.get('price_current', 0):.5f}"))
            
            # P&L with color coding
            pnl = pos.get('profit', 0)
            pnl_item = QTableWidgetItem(f"${pnl:.2f}")
            if pnl > 0:
                pnl_item.setForeground(QBrush(QColor('#4CAF50')))
            elif pnl < 0:
                pnl_item.setForeground(QBrush(QColor('#F44336')))
            self.positions_table.setItem(row, 5, pnl_item)
            
            self.positions_table.setItem(row, 6, QTableWidgetItem(f"{pos.get('tp', 0):.5f}"))
            self.positions_table.setItem(row, 7, QTableWidgetItem(f"{pos.get('sl', 0):.5f}"))
    
    def add_trade_to_history(self, trade_data: Dict[str, Any]):
        """Add completed trade to history"""
        self.trading_data['trades'].append(trade_data)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        trades = self.trading_data.get('trades', [])
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'max_drawdown': 0
            }
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit', 0) < 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        
        total_wins = sum(t.get('profit', 0) for t in winning_trades)
        total_losses = abs(sum(t.get('profit', 0) for t in losing_trades))
        
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        total_pnl = sum(t.get('profit', 0) for t in trades)
        
        # Max drawdown
        drawdowns = self.trading_data.get('drawdown', [0])
        max_drawdown = max(drawdowns) if drawdowns else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown
        }
    
    def emergency_stop_clicked(self):
        """Handle emergency stop button click"""
        reply = QMessageBox.question(
            self, 
            "Emergency Stop", 
            "Are you sure you want to stop all trading activities?\n\nThis will:\n- Close all open positions\n- Stop all strategies\n- Disable auto-trading",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.emergency_stop_triggered.emit()
    
    # Signals
    emergency_stop_triggered = pyqtSignal()


class PerformanceWidget(QWidget):
    """Detailed performance analysis widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup performance analysis UI"""
        layout = QVBoxLayout(self)
        
        # Performance metrics table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        
        # Add standard metrics
        metrics = [
            "Total Return %", "Annualized Return %", "Sharpe Ratio", 
            "Sortino Ratio", "Max Drawdown %", "Calmar Ratio",
            "Total Trades", "Win Rate %", "Profit Factor",
            "Average Win $", "Average Loss $", "Largest Win $",
            "Largest Loss $", "Average Trade Duration", "Recovery Factor"
        ]
        
        self.metrics_table.setRowCount(len(metrics))
        for i, metric in enumerate(metrics):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(i, 1, QTableWidgetItem("0.00"))
            
        layout.addWidget(self.metrics_table)
    
    def update_performance_metrics(self, metrics: Dict[str, float]):
        """Update performance metrics display"""
        metric_mapping = {
            "Total Return %": "total_return_pct",
            "Annualized Return %": "annualized_return_pct",
            "Sharpe Ratio": "sharpe_ratio",
            "Sortino Ratio": "sortino_ratio",
            "Max Drawdown %": "max_drawdown_pct",
            "Calmar Ratio": "calmar_ratio",
            "Total Trades": "total_trades",
            "Win Rate %": "win_rate_pct",
            "Profit Factor": "profit_factor",
            "Average Win $": "avg_win",
            "Average Loss $": "avg_loss",
            "Largest Win $": "largest_win",
            "Largest Loss $": "largest_loss",
            "Average Trade Duration": "avg_duration",
            "Recovery Factor": "recovery_factor"
        }
        
        for row in range(self.metrics_table.rowCount()):
            metric_name = self.metrics_table.item(row, 0).text()
            metric_key = metric_mapping.get(metric_name)
            
            if metric_key and metric_key in metrics:
                value = metrics[metric_key]
                
                # Format value based on type
                if "%" in metric_name:
                    formatted_value = f"{value:.2f}%"
                elif "$" in metric_name:
                    formatted_value = f"${value:,.2f}"
                elif metric_name == "Total Trades":
                    formatted_value = f"{int(value)}"
                else:
                    formatted_value = f"{value:.2f}"
                
                self.metrics_table.setItem(row, 1, QTableWidgetItem(formatted_value))
"""
Trading dashboard for AuraTrade Bot GUI
Displays trading statistics, P&L, equity curve, and performance metrics
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                           QProgressBar, QGroupBox, QTextEdit)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class TradingDashboard(QWidget):
    """Main trading dashboard widget"""
    
    emergency_stop_requested = pyqtSignal()
    
    def __init__(self, trading_engine, order_manager, risk_manager, parent=None):
        super().__init__(parent)
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout(self)
        
        # Top row - Account info and controls
        top_layout = QHBoxLayout()
        
        # Account info group
        account_group = QGroupBox("Account Information")
        account_layout = QGridLayout(account_group)
        
        self.balance_label = QLabel("$0.00")
        self.balance_label.setFont(QFont("Arial", 14, QFont.Bold))
        account_layout.addWidget(QLabel("Balance:"), 0, 0)
        account_layout.addWidget(self.balance_label, 0, 1)
        
        self.equity_label = QLabel("$0.00")
        self.equity_label.setFont(QFont("Arial", 14, QFont.Bold))
        account_layout.addWidget(QLabel("Equity:"), 1, 0)
        account_layout.addWidget(self.equity_label, 1, 1)
        
        self.margin_label = QLabel("$0.00")
        account_layout.addWidget(QLabel("Margin:"), 2, 0)
        account_layout.addWidget(self.margin_label, 2, 1)
        
        self.free_margin_label = QLabel("$0.00")
        account_layout.addWidget(QLabel("Free Margin:"), 3, 0)
        account_layout.addWidget(self.free_margin_label, 3, 1)
        
        top_layout.addWidget(account_group)
        
        # Daily P&L group
        pnl_group = QGroupBox("Daily Performance")
        pnl_layout = QGridLayout(pnl_group)
        
        self.daily_pnl_label = QLabel("$0.00")
        self.daily_pnl_label.setFont(QFont("Arial", 14, QFont.Bold))
        pnl_layout.addWidget(QLabel("Daily P&L:"), 0, 0)
        pnl_layout.addWidget(self.daily_pnl_label, 0, 1)
        
        self.daily_pnl_percent_label = QLabel("0.00%")
        pnl_layout.addWidget(QLabel("Daily %:"), 1, 0)
        pnl_layout.addWidget(self.daily_pnl_percent_label, 1, 1)
        
        self.trades_today_label = QLabel("0")
        pnl_layout.addWidget(QLabel("Trades Today:"), 2, 0)
        pnl_layout.addWidget(self.trades_today_label, 2, 1)
        
        self.win_rate_label = QLabel("0%")
        pnl_layout.addWidget(QLabel("Win Rate:"), 3, 0)
        pnl_layout.addWidget(self.win_rate_label, 3, 1)
        
        top_layout.addWidget(pnl_group)
        
        # Risk group
        risk_group = QGroupBox("Risk Management")
        risk_layout = QGridLayout(risk_group)
        
        self.drawdown_label = QLabel("0.00%")
        risk_layout.addWidget(QLabel("Current DD:"), 0, 0)
        risk_layout.addWidget(self.drawdown_label, 0, 1)
        
        self.max_drawdown_label = QLabel("0.00%")
        risk_layout.addWidget(QLabel("Max DD:"), 1, 0)
        risk_layout.addWidget(self.max_drawdown_label, 1, 1)
        
        self.risk_used_label = QLabel("0.00%")
        risk_layout.addWidget(QLabel("Risk Used:"), 2, 0)
        risk_layout.addWidget(self.risk_used_label, 2, 1)
        
        # Risk progress bar
        self.risk_progress = QProgressBar()
        self.risk_progress.setMaximum(100)
        risk_layout.addWidget(QLabel("Risk Level:"), 3, 0)
        risk_layout.addWidget(self.risk_progress, 3, 1)
        
        top_layout.addWidget(risk_group)
        
        # Controls group
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        self.emergency_stop_btn = QPushButton("🚨 EMERGENCY STOP")
        self.emergency_stop_btn.setStyleSheet("QPushButton { background-color: red; font-weight: bold; }")
        self.emergency_stop_btn.clicked.connect(self.emergency_stop_requested.emit)
        controls_layout.addWidget(self.emergency_stop_btn)
        
        self.status_label = QLabel("Status: Initializing...")
        controls_layout.addWidget(self.status_label)
        
        top_layout.addWidget(controls_group)
        
        layout.addLayout(top_layout)
        
        # Middle row - Charts
        charts_layout = QHBoxLayout()
        
        # Equity curve
        equity_group = QGroupBox("Equity Curve")
        equity_layout = QVBoxLayout(equity_group)
        
        self.equity_chart = pg.PlotWidget()
        self.equity_chart.setBackground('black')
        self.equity_chart.showGrid(x=True, y=True, alpha=0.3)
        self.equity_chart.setLabel('left', 'Equity ($)')
        self.equity_chart.setLabel('bottom', 'Time')
        self.equity_plot = self.equity_chart.plot(pen=pg.mkPen('cyan', width=2))
        
        equity_layout.addWidget(self.equity_chart)
        charts_layout.addWidget(equity_group)
        
        # P&L Distribution
        pnl_dist_group = QGroupBox("P&L Distribution")
        pnl_dist_layout = QVBoxLayout(pnl_dist_group)
        
        self.pnl_chart = pg.PlotWidget()
        self.pnl_chart.setBackground('black')
        self.pnl_chart.showGrid(x=True, y=True, alpha=0.3)
        self.pnl_chart.setLabel('left', 'Frequency')
        self.pnl_chart.setLabel('bottom', 'P&L ($)')
        
        pnl_dist_layout.addWidget(self.pnl_chart)
        charts_layout.addWidget(pnl_dist_group)
        
        layout.addLayout(charts_layout)
        
        # Bottom row - Tables
        tables_layout = QHBoxLayout()
        
        # Open positions table
        positions_group = QGroupBox("Open Positions")
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Type", "Volume", "Entry", "Current", "P&L", "Strategy", "Time"
        ])
        positions_layout.addWidget(self.positions_table)
        tables_layout.addWidget(positions_group)
        
        # Recent trades table
        trades_group = QGroupBox("Recent Trades")
        trades_layout = QVBoxLayout(trades_group)
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(7)
        self.trades_table.setHorizontalHeaderLabels([
            "Symbol", "Type", "Volume", "Entry", "Exit", "P&L", "Strategy"
        ])
        trades_layout.addWidget(self.trades_table)
        tables_layout.addWidget(trades_group)
        
        layout.addLayout(tables_layout)
        
        # Log area
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: black; color: white; font-family: monospace;")
        log_layout.addWidget(self.log_text)
        
        layout.addLayout(log_layout)
        
    def setup_timer(self):
        """Setup timer for regular updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def update_dashboard(self):
        """Update all dashboard components"""
        try:
            self.update_account_info()
            self.update_performance_metrics()
            self.update_risk_metrics()
            self.update_positions_table()
            self.update_trades_table()
            self.update_charts()
            self.update_status()
            
        except Exception as e:
            self.log_message(f"Error updating dashboard: {e}")
    
    def update_account_info(self):
        """Update account information display"""
        try:
            if hasattr(self.trading_engine, 'mt5_connector'):
                account_info = self.trading_engine.mt5_connector.get_account_info()
                if account_info:
                    self.balance_label.setText(f"${account_info.get('balance', 0):.2f}")
                    self.equity_label.setText(f"${account_info.get('equity', 0):.2f}")
                    self.margin_label.setText(f"${account_info.get('margin', 0):.2f}")
                    self.free_margin_label.setText(f"${account_info.get('margin_free', 0):.2f}")
                    
                    # Color coding for equity
                    equity = account_info.get('equity', 0)
                    balance = account_info.get('balance', 0)
                    
                    if equity > balance:
                        self.equity_label.setStyleSheet("color: green;")
                    elif equity < balance:
                        self.equity_label.setStyleSheet("color: red;")
                    else:
                        self.equity_label.setStyleSheet("color: white;")
                        
        except Exception as e:
            self.log_message(f"Error updating account info: {e}")
    
    def update_performance_metrics(self):
        """Update daily performance metrics"""
        try:
            # Get order statistics
            stats = self.order_manager.get_order_statistics()
            
            # Calculate daily P&L (simplified)
            if hasattr(self.trading_engine, 'mt5_connector'):
                account_info = self.trading_engine.mt5_connector.get_account_info()
                if account_info:
                    balance = account_info.get('balance', 0)
                    equity = account_info.get('equity', 0)
                    daily_pnl = equity - balance
                    daily_pnl_percent = (daily_pnl / balance * 100) if balance > 0 else 0
                    
                    self.daily_pnl_label.setText(f"${daily_pnl:.2f}")
                    self.daily_pnl_percent_label.setText(f"{daily_pnl_percent:.2f}%")
                    
                    # Color coding
                    if daily_pnl > 0:
                        self.daily_pnl_label.setStyleSheet("color: green;")
                        self.daily_pnl_percent_label.setStyleSheet("color: green;")
                    elif daily_pnl < 0:
                        self.daily_pnl_label.setStyleSheet("color: red;")
                        self.daily_pnl_percent_label.setStyleSheet("color: red;")
                    else:
                        self.daily_pnl_label.setStyleSheet("color: white;")
                        self.daily_pnl_percent_label.setStyleSheet("color: white;")
            
            # Update trade statistics
            self.trades_today_label.setText(str(stats.get('total_orders', 0)))
            self.win_rate_label.setText(f"{stats.get('success_rate', 0):.1f}%")
            
        except Exception as e:
            self.log_message(f"Error updating performance metrics: {e}")
    
    def update_risk_metrics(self):
        """Update risk management display"""
        try:
            risk_summary = self.risk_manager.get_risk_summary()
            
            current_dd = risk_summary.get('current_drawdown', 0)
            max_dd = risk_summary.get('max_drawdown', 0)
            daily_risk_used = risk_summary.get('daily_risk_used', 0)
            
            self.drawdown_label.setText(f"{current_dd:.2f}%")
            self.max_drawdown_label.setText(f"{max_dd:.2f}%")
            
            # Calculate risk percentage (simplified)
            max_daily_risk = risk_summary.get('risk_limits', {}).get('max_daily_risk', 5)
            risk_percent = (daily_risk_used / max_daily_risk * 100) if max_daily_risk > 0 else 0
            
            self.risk_used_label.setText(f"{risk_percent:.1f}%")
            self.risk_progress.setValue(int(risk_percent))
            
            # Color coding for risk progress bar
            if risk_percent < 50:
                self.risk_progress.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            elif risk_percent < 80:
                self.risk_progress.setStyleSheet("QProgressBar::chunk { background-color: yellow; }")
            else:
                self.risk_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
                
        except Exception as e:
            self.log_message(f"Error updating risk metrics: {e}")
    
    def update_positions_table(self):
        """Update open positions table"""
        try:
            if hasattr(self.trading_engine, 'mt5_connector'):
                positions = self.trading_engine.mt5_connector.get_positions()
                
                self.positions_table.setRowCount(len(positions))
                
                for row, position in enumerate(positions):
                    self.positions_table.setItem(row, 0, QTableWidgetItem(position.get('symbol', '')))
                    self.positions_table.setItem(row, 1, QTableWidgetItem('Buy' if position.get('type', 0) == 0 else 'Sell'))
                    self.positions_table.setItem(row, 2, QTableWidgetItem(f"{position.get('volume', 0):.2f}"))
                    self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position.get('price_open', 0):.5f}"))
                    self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position.get('price_current', 0):.5f}"))
                    
                    # P&L with color coding
                    pnl = position.get('profit', 0)
                    pnl_item = QTableWidgetItem(f"${pnl:.2f}")
                    if pnl > 0:
                        pnl_item.setForeground(QColor('green'))
                    elif pnl < 0:
                        pnl_item.setForeground(QColor('red'))
                    self.positions_table.setItem(row, 5, pnl_item)
                    
                    self.positions_table.setItem(row, 6, QTableWidgetItem(position.get('comment', '')[:10]))
                    
                    # Time (simplified)
                    time_str = str(position.get('time', ''))[:19]
                    self.positions_table.setItem(row, 7, QTableWidgetItem(time_str))
                    
        except Exception as e:
            self.log_message(f"Error updating positions table: {e}")
    
    def update_trades_table(self):
        """Update recent trades table"""
        try:
            # Get recent trades from order history
            recent_trades = self.order_manager.order_history[-10:]  # Last 10 trades
            
            self.trades_table.setRowCount(len(recent_trades))
            
            for row, trade in enumerate(recent_trades):
                self.trades_table.setItem(row, 0, QTableWidgetItem(trade.get('symbol', '')))
                self.trades_table.setItem(row, 1, QTableWidgetItem('Buy' if trade.get('direction', 0) > 0 else 'Sell'))
                self.trades_table.setItem(row, 2, QTableWidgetItem(f"{trade.get('volume', 0):.2f}"))
                self.trades_table.setItem(row, 3, QTableWidgetItem(f"{trade.get('entry_price', 0):.5f}"))
                self.trades_table.setItem(row, 4, QTableWidgetItem(f"{trade.get('exit_price', 0):.5f}"))
                
                # P&L (simplified calculation)
                entry_price = trade.get('entry_price', 0)
                exit_price = trade.get('exit_price', entry_price)
                volume = trade.get('volume', 0)
                direction = trade.get('direction', 1)
                
                if exit_price > 0 and entry_price > 0:
                    pnl = (exit_price - entry_price) * direction * volume * 100000  # Simplified
                    pnl_item = QTableWidgetItem(f"${pnl:.2f}")
                    
                    if pnl > 0:
                        pnl_item.setForeground(QColor('green'))
                    elif pnl < 0:
                        pnl_item.setForeground(QColor('red'))
                    
                    self.trades_table.setItem(row, 5, pnl_item)
                else:
                    self.trades_table.setItem(row, 5, QTableWidgetItem("$0.00"))
                
                self.trades_table.setItem(row, 6, QTableWidgetItem(trade.get('strategy', '')[:10]))
                
        except Exception as e:
            self.log_message(f"Error updating trades table: {e}")
    
    def update_charts(self):
        """Update equity curve and P&L distribution charts"""
        try:
            # Update equity curve (simplified - using dummy data for now)
            if hasattr(self.trading_engine, 'mt5_connector'):
                account_info = self.trading_engine.mt5_connector.get_account_info()
                if account_info:
                    equity = account_info.get('equity', 0)
                    
                    # Add current equity point
                    if not hasattr(self, 'equity_data'):
                        self.equity_data = []
                        self.equity_times = []
                    
                    self.equity_data.append(equity)
                    self.equity_times.append(len(self.equity_data))
                    
                    # Keep only last 100 points
                    if len(self.equity_data) > 100:
                        self.equity_data = self.equity_data[-100:]
                        self.equity_times = self.equity_times[-100:]
                    
                    # Update plot
                    self.equity_plot.setData(self.equity_times, self.equity_data)
                    
        except Exception as e:
            self.log_message(f"Error updating charts: {e}")
    
    def update_status(self):
        """Update system status"""
        try:
            if hasattr(self.trading_engine, 'running') and self.trading_engine.running:
                self.status_label.setText("Status: Running ✅")
            else:
                self.status_label.setText("Status: Stopped ❌")
                
        except Exception as e:
            self.status_label.setText("Status: Error ⚠️")
    
    def log_message(self, message: str):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Keep only last 100 lines
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > 100:
            self.log_text.setPlainText('\n'.join(lines[-100:]))
