
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
