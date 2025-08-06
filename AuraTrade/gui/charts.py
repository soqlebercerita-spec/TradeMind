
"""
Charts and visualization for AuraTrade Bot
Real-time price charts and technical indicators
"""

import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

# Handle PyQt5 import gracefully
try:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
    from PyQt5.QtCore import QTimer, pyqtSignal
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    PYQT_AVAILABLE = True
except ImportError:
    print("PyQt5 not available, charts will run in matplotlib-only mode")
    PYQT_AVAILABLE = False
    # Dummy classes for when PyQt5 is not available
    class QWidget:
        pass
    class FigureCanvas:
        pass

from utils.logger import Logger

class ChartWidget(QWidget if PYQT_AVAILABLE else object):
    """Advanced chart widget for price data and indicators"""
    
    # Signals for PyQt5
    if PYQT_AVAILABLE:
        symbol_changed = pyqtSignal(str)
        timeframe_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        self.logger = Logger().get_logger()
        self.current_symbol = 'EURUSD'
        self.current_timeframe = 'M5'
        self.data = None
        self.indicators = {}
        
        if PYQT_AVAILABLE:
            self.setup_ui()
            self.setup_chart()
            self.setup_timer()
        else:
            self.setup_matplotlib_only()
        
        self.logger.info("Chart widget initialized")
    
    def setup_ui(self):
        """Setup UI components"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            layout = QVBoxLayout(self)
            
            # Control panel
            control_panel = QHBoxLayout()
            
            # Symbol selector
            self.symbol_label = QLabel("Symbol:")
            self.symbol_combo = QComboBox()
            self.symbol_combo.addItems(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD'])
            self.symbol_combo.setCurrentText(self.current_symbol)
            self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
            
            # Timeframe selector
            self.timeframe_label = QLabel("Timeframe:")
            self.timeframe_combo = QComboBox()
            self.timeframe_combo.addItems(['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'])
            self.timeframe_combo.setCurrentText(self.current_timeframe)
            self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
            
            # Refresh button
            self.refresh_button = QPushButton("Refresh")
            self.refresh_button.clicked.connect(self.refresh_chart)
            
            control_panel.addWidget(self.symbol_label)
            control_panel.addWidget(self.symbol_combo)
            control_panel.addWidget(self.timeframe_label)
            control_panel.addWidget(self.timeframe_combo)
            control_panel.addWidget(self.refresh_button)
            control_panel.addStretch()
            
            layout.addLayout(control_panel)
            
        except Exception as e:
            self.logger.error(f"Error setting up UI: {e}")
    
    def setup_chart(self):
        """Setup matplotlib chart"""
        try:
            # Create figure and canvas
            self.figure = Figure(figsize=(12, 8), dpi=100)
            self.figure.patch.set_facecolor('#1e1e1e')
            
            if PYQT_AVAILABLE:
                self.canvas = FigureCanvas(self.figure)
                self.layout().addWidget(self.canvas)
            
            # Create subplots
            self.ax_price = self.figure.add_subplot(3, 1, 1)
            self.ax_volume = self.figure.add_subplot(3, 1, 2, sharex=self.ax_price)
            self.ax_indicators = self.figure.add_subplot(3, 1, 3, sharex=self.ax_price)
            
            # Style the subplots
            for ax in [self.ax_price, self.ax_volume, self.ax_indicators]:
                ax.set_facecolor('#2d2d2d')
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')
            
            self.figure.tight_layout()
            
        except Exception as e:
            self.logger.error(f"Error setting up chart: {e}")
    
    def setup_matplotlib_only(self):
        """Setup for matplotlib-only mode"""
        try:
            plt.style.use('dark_background')
            self.figure, (self.ax_price, self.ax_volume, self.ax_indicators) = plt.subplots(3, 1, figsize=(12, 8))
            self.figure.patch.set_facecolor('#1e1e1e')
            
        except Exception as e:
            self.logger.error(f"Error setting up matplotlib-only mode: {e}")
    
    def setup_timer(self):
        """Setup refresh timer"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            self.timer = QTimer()
            self.timer.timeout.connect(self.auto_refresh)
            self.timer.start(5000)  # Refresh every 5 seconds
            
        except Exception as e:
            self.logger.error(f"Error setting up timer: {e}")
    
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change"""
        try:
            self.current_symbol = symbol
            if PYQT_AVAILABLE:
                self.symbol_changed.emit(symbol)
            self.refresh_chart()
            
        except Exception as e:
            self.logger.error(f"Error changing symbol: {e}")
    
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        try:
            self.current_timeframe = timeframe
            if PYQT_AVAILABLE:
                self.timeframe_changed.emit(timeframe)
            self.refresh_chart()
            
        except Exception as e:
            self.logger.error(f"Error changing timeframe: {e}")
    
    def update_data(self, data: pd.DataFrame, indicators: Dict = None):
        """Update chart with new data"""
        try:
            self.data = data
            self.indicators = indicators or {}
            self.plot_chart()
            
        except Exception as e:
            self.logger.error(f"Error updating data: {e}")
    
    def plot_chart(self):
        """Plot the main chart"""
        if self.data is None or len(self.data) == 0:
            return
        
        try:
            # Clear previous plots
            self.ax_price.clear()
            self.ax_volume.clear()
            self.ax_indicators.clear()
            
            # Plot candlestick chart
            self.plot_candlesticks()
            
            # Plot moving averages
            self.plot_moving_averages()
            
            # Plot volume
            self.plot_volume()
            
            # Plot technical indicators
            self.plot_technical_indicators()
            
            # Set titles and labels
            self.ax_price.set_title(f'{self.current_symbol} - {self.current_timeframe}', color='white', fontsize=14, fontweight='bold')
            self.ax_price.set_ylabel('Price', color='white')
            self.ax_volume.set_ylabel('Volume', color='white')
            self.ax_indicators.set_ylabel('Indicators', color='white')
            self.ax_indicators.set_xlabel('Time', color='white')
            
            # Style the axes
            for ax in [self.ax_price, self.ax_volume, self.ax_indicators]:
                ax.grid(True, alpha=0.3, color='gray')
                ax.set_facecolor('#2d2d2d')
                ax.tick_params(colors='white')
            
            # Adjust layout
            self.figure.tight_layout()
            
            # Refresh canvas
            if PYQT_AVAILABLE and hasattr(self, 'canvas'):
                self.canvas.draw()
            else:
                plt.draw()
                
        except Exception as e:
            self.logger.error(f"Error plotting chart: {e}")
    
    def plot_candlesticks(self):
        """Plot candlestick chart"""
        try:
            if 'open' not in self.data.columns:
                return
            
            # Prepare data
            dates = range(len(self.data))
            opens = self.data['open'].values
            highs = self.data['high'].values
            lows = self.data['low'].values
            closes = self.data['close'].values
            
            # Plot candlesticks
            for i in range(len(self.data)):
                color = 'lime' if closes[i] >= opens[i] else 'red'
                
                # Candle body
                body_height = abs(closes[i] - opens[i])
                body_bottom = min(opens[i], closes[i])
                
                self.ax_price.bar(dates[i], body_height, bottom=body_bottom, 
                                width=0.6, color=color, alpha=0.8)
                
                # Wicks
                self.ax_price.plot([dates[i], dates[i]], [lows[i], highs[i]], 
                                color='white', linewidth=1)
            
            # Set x-axis limits
            self.ax_price.set_xlim(-1, len(self.data))
            
        except Exception as e:
            self.logger.error(f"Error plotting candlesticks: {e}")
    
    def plot_moving_averages(self):
        """Plot moving averages"""
        try:
            if len(self.data) < 50:
                return
            
            closes = self.data['close']
            dates = range(len(self.data))
            
            # Calculate and plot moving averages
            ma20 = closes.rolling(window=20).mean()
            ma50 = closes.rolling(window=50).mean()
            
            if len(ma20.dropna()) > 0:
                self.ax_price.plot(dates, ma20, color='orange', linewidth=2, label='MA20', alpha=0.8)
            
            if len(ma50.dropna()) > 0:
                self.ax_price.plot(dates, ma50, color='cyan', linewidth=2, label='MA50', alpha=0.8)
            
            # Add legend
            self.ax_price.legend(loc='upper left', facecolor='#2d2d2d', edgecolor='white')
            
        except Exception as e:
            self.logger.error(f"Error plotting moving averages: {e}")
    
    def plot_volume(self):
        """Plot volume bars"""
        try:
            if 'tick_volume' not in self.data.columns and 'real_volume' not in self.data.columns:
                # Generate fake volume data for demo
                volumes = np.random.randint(100, 1000, len(self.data))
            else:
                volumes = self.data.get('tick_volume', self.data.get('real_volume', [])).values
            
            if len(volumes) == 0:
                return
            
            dates = range(len(self.data))
            colors = ['lime' if self.data['close'].iloc[i] >= self.data['open'].iloc[i] else 'red' 
                     for i in range(len(self.data))]
            
            self.ax_volume.bar(dates, volumes, color=colors, alpha=0.6)
            
        except Exception as e:
            self.logger.error(f"Error plotting volume: {e}")
    
    def plot_technical_indicators(self):
        """Plot technical indicators"""
        try:
            if not self.indicators:
                return
            
            dates = range(len(self.data))
            
            # Plot RSI if available
            if 'rsi' in self.indicators:
                rsi = self.indicators['rsi']
                if isinstance(rsi, (list, np.ndarray)) and len(rsi) == len(self.data):
                    self.ax_indicators.plot(dates, rsi, color='yellow', linewidth=2, label='RSI')
                    self.ax_indicators.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                    self.ax_indicators.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                    self.ax_indicators.set_ylim(0, 100)
                elif isinstance(rsi, (int, float)):
                    # Single RSI value
                    rsi_line = [rsi] * len(dates)
                    self.ax_indicators.plot(dates, rsi_line, color='yellow', linewidth=2, label=f'RSI: {rsi:.1f}')
                    self.ax_indicators.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                    self.ax_indicators.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                    self.ax_indicators.set_ylim(0, 100)
            
            # Plot MACD if available
            if 'macd' in self.indicators:
                macd_data = self.indicators['macd']
                if isinstance(macd_data, dict):
                    macd_line = macd_data.get('macd', 0)
                    signal_line = macd_data.get('signal', 0)
                    
                    if isinstance(macd_line, (list, np.ndarray)) and len(macd_line) == len(self.data):
                        self.ax_indicators.plot(dates, macd_line, color='blue', linewidth=2, label='MACD')
                        if isinstance(signal_line, (list, np.ndarray)) and len(signal_line) == len(self.data):
                            self.ax_indicators.plot(dates, signal_line, color='red', linewidth=2, label='Signal')
            
            # Add legend
            if self.indicators:
                self.ax_indicators.legend(loc='upper left', facecolor='#2d2d2d', edgecolor='white')
            
        except Exception as e:
            self.logger.error(f"Error plotting technical indicators: {e}")
    
    def refresh_chart(self):
        """Refresh chart data"""
        try:
            # This method should be called by the main application
            # to update chart with new data
            if hasattr(self, 'data') and self.data is not None:
                self.plot_chart()
                
        except Exception as e:
            self.logger.error(f"Error refreshing chart: {e}")
    
    def auto_refresh(self):
        """Auto refresh chart (called by timer)"""
        try:
            # Request new data from parent
            if hasattr(self.parent(), 'request_chart_data'):
                self.parent().request_chart_data(self.current_symbol, self.current_timeframe)
                
        except Exception as e:
            self.logger.error(f"Error in auto refresh: {e}")
    
    def add_indicator(self, name: str, data: any):
        """Add indicator data"""
        self.indicators[name] = data
        if hasattr(self, 'data') and self.data is not None:
            self.plot_chart()
    
    def remove_indicator(self, name: str):
        """Remove indicator"""
        if name in self.indicators:
            del self.indicators[name]
            self.plot_chart()
    
    def export_chart(self, filename: str):
        """Export chart to file"""
        try:
            if hasattr(self, 'figure'):
                self.figure.savefig(filename, facecolor='#1e1e1e', dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart exported to {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exporting chart: {e}")

# Utility function for standalone chart creation
def create_standalone_chart(data: pd.DataFrame, symbol: str = "EURUSD", indicators: Dict = None):
    """Create a standalone chart without PyQt5"""
    try:
        plt.style.use('dark_background')
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
        fig.patch.set_facecolor('#1e1e1e')
        
        if data is None or len(data) == 0:
            plt.text(0.5, 0.5, 'No data available', transform=ax1.transAxes, 
                    ha='center', va='center', fontsize=20, color='white')
            plt.show()
            return
        
        # Plot candlesticks
        dates = range(len(data))
        for i in range(len(data)):
            color = 'lime' if data['close'].iloc[i] >= data['open'].iloc[i] else 'red'
            
            # Candle body
            body_height = abs(data['close'].iloc[i] - data['open'].iloc[i])
            body_bottom = min(data['open'].iloc[i], data['close'].iloc[i])
            
            ax1.bar(dates[i], body_height, bottom=body_bottom, 
                   width=0.6, color=color, alpha=0.8)
            
            # Wicks
            ax1.plot([dates[i], dates[i]], [data['low'].iloc[i], data['high'].iloc[i]], 
                    color='white', linewidth=1)
        
        # Moving averages
        if len(data) >= 20:
            ma20 = data['close'].rolling(window=20).mean()
            ax1.plot(dates, ma20, color='orange', linewidth=2, label='MA20')
        
        if len(data) >= 50:
            ma50 = data['close'].rolling(window=50).mean()
            ax1.plot(dates, ma50, color='cyan', linewidth=2, label='MA50')
        
        ax1.set_title(f'{symbol} Price Chart', color='white', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price', color='white')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Volume
        if 'tick_volume' in data.columns:
            volumes = data['tick_volume'].values
        else:
            volumes = np.random.randint(100, 1000, len(data))
        
        colors = ['lime' if data['close'].iloc[i] >= data['open'].iloc[i] else 'red' 
                 for i in range(len(data))]
        ax2.bar(dates, volumes, color=colors, alpha=0.6)
        ax2.set_ylabel('Volume', color='white')
        ax2.grid(True, alpha=0.3)
        
        # Indicators
        if indicators:
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if isinstance(rsi, (int, float)):
                    rsi_line = [rsi] * len(dates)
                    ax3.plot(dates, rsi_line, color='yellow', linewidth=2, label=f'RSI: {rsi:.1f}')
                else:
                    ax3.plot(dates, rsi, color='yellow', linewidth=2, label='RSI')
                ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                ax3.set_ylim(0, 100)
        
        ax3.set_ylabel('Indicators', color='white')
        ax3.set_xlabel('Time', color='white')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"Error creating standalone chart: {e}")
