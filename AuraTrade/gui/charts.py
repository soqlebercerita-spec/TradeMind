
"""
Charts and visualization for AuraTrade Bot
Real-time price charts and technical indicators
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
try:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
from utils.logger import Logger

class TradingChart(QWidget):
    """Real-time trading chart with technical indicators"""
    
    def __init__(self, symbol: str = "EURUSD"):
        super().__init__()
        self.logger = Logger().get_logger()
        self.symbol = symbol
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        
        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Chart data
        self.price_data = pd.DataFrame()
        self.indicators = {}
        
        # Chart settings
        self.chart_style = 'dark_background'
        plt.style.use(self.chart_style)
        
        self.logger.info(f"Trading chart initialized for {symbol}")
    
    def update_data(self, rates_data: pd.DataFrame, indicators_data: Dict = None):
        """Update chart with new data"""
        try:
            if rates_data is None or rates_data.empty:
                return
            
            self.price_data = rates_data.copy()
            if indicators_data:
                self.indicators = indicators_data.copy()
            
            self._plot_chart()
            
        except Exception as e:
            self.logger.error(f"Error updating chart data: {e}")
    
    def _plot_chart(self):
        """Plot the main chart with indicators"""
        try:
            self.figure.clear()
            
            if self.price_data.empty:
                return
            
            # Create subplots
            gs = self.figure.add_gridspec(3, 1, height_ratios=[3, 1, 1], hspace=0.1)
            ax1 = self.figure.add_subplot(gs[0])  # Price chart
            ax2 = self.figure.add_subplot(gs[1])  # RSI
            ax3 = self.figure.add_subplot(gs[2])  # Volume
            
            # Plot candlestick chart
            self._plot_candlesticks(ax1)
            
            # Plot moving averages
            self._plot_moving_averages(ax1)
            
            # Plot Bollinger Bands
            self._plot_bollinger_bands(ax1)
            
            # Plot RSI
            self._plot_rsi(ax2)
            
            # Plot volume
            self._plot_volume(ax3)
            
            # Format axes
            self._format_axes(ax1, ax2, ax3)
            
            # Update canvas
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error plotting chart: {e}")
    
    def _plot_candlesticks(self, ax):
        """Plot candlestick chart"""
        try:
            data = self.price_data
            
            # Calculate colors
            colors = ['green' if close >= open_price else 'red' 
                     for close, open_price in zip(data['close'], data['open'])]
            
            # Plot high-low lines
            for i, (high, low) in enumerate(zip(data['high'], data['low'])):
                ax.plot([i, i], [low, high], color='gray', linewidth=0.5)
            
            # Plot open-close rectangles
            for i, (open_price, close, color) in enumerate(zip(data['open'], data['close'], colors)):
                height = abs(close - open_price)
                bottom = min(open_price, close)
                ax.bar(i, height, bottom=bottom, color=color, alpha=0.8, width=0.8)
            
            ax.set_title(f"{self.symbol} - {data.index[-1] if not data.empty else 'No Data'}", 
                        fontsize=12, fontweight='bold')
            ax.set_ylabel('Price', fontsize=10)
            
        except Exception as e:
            self.logger.error(f"Error plotting candlesticks: {e}")
    
    def _plot_moving_averages(self, ax):
        """Plot moving averages"""
        try:
            if 'ema_50' in self.indicators:
                ax.plot(self.indicators['ema_50'], label='EMA 50', color='blue', linewidth=1)
            
            if 'wma_5' in self.indicators:
                ax.plot(self.indicators['wma_5'], label='WMA 5', color='orange', linewidth=1)
            
            if 'wma_10' in self.indicators:
                ax.plot(self.indicators['wma_10'], label='WMA 10', color='purple', linewidth=1)
            
            ax.legend(loc='upper left', fontsize=8)
            
        except Exception as e:
            self.logger.error(f"Error plotting moving averages: {e}")
    
    def _plot_bollinger_bands(self, ax):
        """Plot Bollinger Bands"""
        try:
            if all(k in self.indicators for k in ['bb_upper', 'bb_middle', 'bb_lower']):
                ax.plot(self.indicators['bb_upper'], label='BB Upper', color='gray', linestyle='--', alpha=0.7)
                ax.plot(self.indicators['bb_middle'], label='BB Middle', color='gray', linestyle='-', alpha=0.7)
                ax.plot(self.indicators['bb_lower'], label='BB Lower', color='gray', linestyle='--', alpha=0.7)
                
                # Fill between bands
                ax.fill_between(range(len(self.indicators['bb_upper'])), 
                               self.indicators['bb_upper'], 
                               self.indicators['bb_lower'], 
                               alpha=0.1, color='gray')
            
        except Exception as e:
            self.logger.error(f"Error plotting Bollinger Bands: {e}")
    
    def _plot_rsi(self, ax):
        """Plot RSI indicator"""
        try:
            if 'rsi' in self.indicators:
                ax.plot(self.indicators['rsi'], label='RSI', color='yellow', linewidth=1)
                ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought')
                ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold')
                ax.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
                
                ax.set_ylabel('RSI', fontsize=10)
                ax.set_ylim(0, 100)
                ax.legend(loc='upper right', fontsize=8)
            
        except Exception as e:
            self.logger.error(f"Error plotting RSI: {e}")
    
    def _plot_volume(self, ax):
        """Plot volume"""
        try:
            if 'tick_volume' in self.price_data.columns:
                volume = self.price_data['tick_volume']
                colors = ['green' if close >= open_price else 'red' 
                         for close, open_price in zip(self.price_data['close'], self.price_data['open'])]
                
                ax.bar(range(len(volume)), volume, color=colors, alpha=0.6)
                ax.set_ylabel('Volume', fontsize=10)
            
        except Exception as e:
            self.logger.error(f"Error plotting volume: {e}")
    
    def _format_axes(self, ax1, ax2, ax3):
        """Format chart axes"""
        try:
            # Remove x-axis labels for top charts
            ax1.set_xticklabels([])
            ax2.set_xticklabels([])
            
            # Set grid
            for ax in [ax1, ax2, ax3]:
                ax.grid(True, alpha=0.3)
                ax.set_facecolor('black')
            
            # Set colors
            for ax in [ax1, ax2, ax3]:
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
            
        except Exception as e:
            self.logger.error(f"Error formatting axes: {e}")

class MultiSymbolChart(QWidget):
    """Multiple symbol chart display"""
    
    def __init__(self, symbols: List[str] = None):
        super().__init__()
        self.logger = Logger().get_logger()
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        self.charts = {}
        
        self._setup_charts()
        self.logger.info("Multi-symbol chart initialized")
    
    def _setup_charts(self):
        """Setup individual charts for each symbol"""
        try:
            layout = QVBoxLayout()
            
            for symbol in self.symbols:
                chart = TradingChart(symbol)
                self.charts[symbol] = chart
                layout.addWidget(chart)
            
            self.setLayout(layout)
            
        except Exception as e:
            self.logger.error(f"Error setting up charts: {e}")
    
    def update_symbol_data(self, symbol: str, rates_data: pd.DataFrame, indicators_data: Dict = None):
        """Update data for specific symbol"""
        if symbol in self.charts:
            self.charts[symbol].update_data(rates_data, indicators_data)

class ChartManager:
    """Manages all chart instances"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.active_charts = {}
        self.logger.info("Chart Manager initialized")
    
    def create_chart(self, symbol: str) -> TradingChart:
        """Create new chart for symbol"""
        try:
            chart = TradingChart(symbol)
            self.active_charts[symbol] = chart
            self.logger.info(f"Chart created for {symbol}")
            return chart
            
        except Exception as e:
            self.logger.error(f"Error creating chart for {symbol}: {e}")
            return None
    
    def update_chart(self, symbol: str, rates_data: pd.DataFrame, indicators_data: Dict = None):
        """Update chart with new data"""
        if symbol in self.active_charts:
            self.active_charts[symbol].update_data(rates_data, indicators_data)
    
    def get_chart(self, symbol: str) -> Optional[TradingChart]:
        """Get chart for symbol"""
        return self.active_charts.get(symbol)
    
    def remove_chart(self, symbol: str):
        """Remove chart for symbol"""
        if symbol in self.active_charts:
            del self.active_charts[symbol]
            self.logger.info(f"Chart removed for {symbol}")
