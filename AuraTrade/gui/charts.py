"""
Trading charts widget for AuraTrade Bot GUI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                           QLabel, QPushButton)
from PyQt5.QtCore import QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from utils.logger import Logger

class TradingChartWidget(QWidget):
    """Trading charts display widget"""

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)

        self.data_manager = data_manager
        self.logger = Logger().get_logger()

        self.current_symbol = 'EURUSD'
        self.current_timeframe = 'M15'

        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        """Setup chart UI"""
        layout = QVBoxLayout(self)

        # Controls
        controls_layout = QHBoxLayout()

        # Symbol selector
        controls_layout.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'])
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        controls_layout.addWidget(self.symbol_combo)

        # Timeframe selector
        controls_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['M1', 'M5', 'M15', 'M30', 'H1', 'H4'])
        self.timeframe_combo.setCurrentText('M15')
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        controls_layout.addWidget(self.timeframe_combo)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_chart)
        controls_layout.addWidget(self.refresh_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Chart
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Set dark theme for chart
        plt.style.use('dark_background')

    def setup_timer(self):
        """Setup chart update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(5000)  # Update every 5 seconds

    def on_symbol_changed(self, symbol):
        """Handle symbol change"""
        self.current_symbol = symbol
        self.update_chart()

    def on_timeframe_changed(self, timeframe):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        self.update_chart()

    def update_chart(self):
        """Update chart display"""
        try:
            # Get data
            data = self.data_manager.get_rates(self.current_symbol, self.current_timeframe, 100)

            if data is None or len(data) < 10:
                return

            # Clear figure
            self.figure.clear()

            # Create subplots
            ax1 = self.figure.add_subplot(2, 1, 1)
            ax2 = self.figure.add_subplot(2, 1, 2)

            # Plot candlestick chart (simplified)
            self.plot_candlesticks(ax1, data)

            # Plot volume (use tick_volume if available)
            if 'tick_volume' in data.columns:
                ax2.bar(range(len(data)), data['tick_volume'], color='blue', alpha=0.7)
                ax2.set_title('Volume')
            else:
                # Plot RSI instead
                self.plot_rsi(ax2, data)

            # Format chart
            ax1.set_title(f"{self.current_symbol} - {self.current_timeframe}")
            ax1.grid(True, alpha=0.3)
            ax2.grid(True, alpha=0.3)

            # Adjust layout
            self.figure.tight_layout()

            # Refresh canvas
            self.canvas.draw()

        except Exception as e:
            self.logger.error(f"Error updating chart: {e}")

    def plot_candlesticks(self, ax, data):
        """Plot simple candlestick chart"""
        try:
            # Use simple line chart for now (candlesticks require mplfinance)
            ax.plot(data.index, data['close'], label='Close', color='white', linewidth=1)

            # Add moving averages
            if len(data) >= 20:
                sma_20 = data['close'].rolling(20).mean()
                ax.plot(data.index, sma_20, label='SMA 20', color='yellow', alpha=0.7)

            if len(data) >= 50:
                sma_50 = data['close'].rolling(50).mean()
                ax.plot(data.index, sma_50, label='SMA 50', color='orange', alpha=0.7)

            ax.legend()
            ax.set_ylabel('Price')

        except Exception as e:
            self.logger.error(f"Error plotting candlesticks: {e}")

    def plot_rsi(self, ax, data):
        """Plot RSI indicator"""
        try:
            # Calculate RSI
            rsi = self.calculate_rsi(data['close'], 14)

            ax.plot(data.index, rsi, label='RSI', color='purple')
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.7)
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.7)
            ax.axhline(y=50, color='white', linestyle='-', alpha=0.3)

            ax.set_ylim(0, 100)
            ax.set_title('RSI (14)')
            ax.legend()

        except Exception as e:
            self.logger.error(f"Error plotting RSI: {e}")

    def calculate_rsi(self, series, period=14):
        """Calculate RSI"""
        try:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

        except Exception:
            return pd.Series()