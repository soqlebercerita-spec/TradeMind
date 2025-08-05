
"""
Live chart integration for AuraTrade Bot GUI
"""

import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class ChartWidget(QWidget):
    """Advanced chart widget with technical indicators"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.symbol = "EURUSD"
        self.timeframe = "M15"
        self.data = pd.DataFrame()
        self.indicators = {}
        
        self.setup_ui()
        self.setup_chart()
        
    def setup_ui(self):
        """Setup chart UI"""
        layout = QVBoxLayout(self)
        
        # Chart controls
        controls = QHBoxLayout()
        
        # Symbol selector
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD', 'USDJPY'])
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        controls.addWidget(QLabel("Symbol:"))
        controls.addWidget(self.symbol_combo)
        
        # Timeframe selector
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'])
        self.timeframe_combo.setCurrentText('M15')
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        controls.addWidget(QLabel("Timeframe:"))
        controls.addWidget(self.timeframe_combo)
        
        # Indicator checkboxes
        self.sma_check = QCheckBox("SMA")
        self.sma_check.toggled.connect(self.update_indicators)
        controls.addWidget(self.sma_check)
        
        self.ema_check = QCheckBox("EMA")
        self.ema_check.toggled.connect(self.update_indicators)
        controls.addWidget(self.ema_check)
        
        self.bollinger_check = QCheckBox("Bollinger")
        self.bollinger_check.toggled.connect(self.update_indicators)
        controls.addWidget(self.bollinger_check)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Chart area
        self.chart_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.chart_widget)
        
    def setup_chart(self):
        """Setup the main chart"""
        # Main price plot
        self.price_plot = self.chart_widget.addPlot(title="Price Chart")
        self.price_plot.setLabel('left', 'Price')
        self.price_plot.setLabel('bottom', 'Time')
        self.price_plot.showGrid(x=True, y=True)
        
        # Candlestick items
        self.candlestick_item = CandlestickItem()
        self.price_plot.addItem(self.candlestick_item)
        
        # Indicator lines
        self.sma_line = self.price_plot.plot(pen=pg.mkPen('blue', width=2), name="SMA")
        self.ema_line = self.price_plot.plot(pen=pg.mkPen('red', width=2), name="EMA")
        self.bb_upper = self.price_plot.plot(pen=pg.mkPen('gray', width=1), name="BB Upper")
        self.bb_lower = self.price_plot.plot(pen=pg.mkPen('gray', width=1), name="BB Lower")
        
        # Volume plot
        self.chart_widget.nextRow()
        self.volume_plot = self.chart_widget.addPlot(title="Volume")
        self.volume_plot.setLabel('left', 'Volume')
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.8, brush='lightblue')
        self.volume_plot.addItem(self.volume_bars)
        
        # RSI plot
        self.chart_widget.nextRow()
        self.rsi_plot = self.chart_widget.addPlot(title="RSI")
        self.rsi_plot.setLabel('left', 'RSI')
        self.rsi_plot.setYRange(0, 100)
        self.rsi_line = self.rsi_plot.plot(pen=pg.mkPen('purple', width=2))
        
        # RSI levels
        self.rsi_plot.addLine(y=70, pen=pg.mkPen('red', style=Qt.DashLine))
        self.rsi_plot.addLine(y=30, pen=pg.mkPen('green', style=Qt.DashLine))
        
    def update_data(self, data: pd.DataFrame):
        """Update chart with new data"""
        if data.empty:
            return
            
        self.data = data.copy()
        self.update_candlesticks()
        self.update_volume()
        self.update_indicators()
        
    def update_candlesticks(self):
        """Update candlestick chart"""
        if self.data.empty:
            return
            
        # Prepare candlestick data
        times = np.arange(len(self.data))
        opens = self.data['open'].values
        highs = self.data['high'].values
        lows = self.data['low'].values
        closes = self.data['close'].values
        
        self.candlestick_item.setData(times, opens, highs, lows, closes)
        
    def update_volume(self):
        """Update volume bars"""
        if self.data.empty or 'volume' not in self.data.columns:
            return
            
        times = np.arange(len(self.data))
        volumes = self.data['volume'].values
        
        self.volume_bars.setOpts(x=times, height=volumes)
        
    def update_indicators(self):
        """Update technical indicators"""
        if self.data.empty:
            return
            
        times = np.arange(len(self.data))
        
        # SMA
        if self.sma_check.isChecked():
            sma = self.calculate_sma(self.data['close'], 20)
            self.sma_line.setData(times, sma)
            self.sma_line.show()
        else:
            self.sma_line.hide()
            
        # EMA
        if self.ema_check.isChecked():
            ema = self.calculate_ema(self.data['close'], 20)
            self.ema_line.setData(times, ema)
            self.ema_line.show()
        else:
            self.ema_line.hide()
            
        # Bollinger Bands
        if self.bollinger_check.isChecked():
            bb_upper, bb_lower = self.calculate_bollinger_bands(self.data['close'])
            self.bb_upper.setData(times, bb_upper)
            self.bb_lower.setData(times, bb_lower)
            self.bb_upper.show()
            self.bb_lower.show()
        else:
            self.bb_upper.hide()
            self.bb_lower.hide()
            
        # RSI
        rsi = self.calculate_rsi(self.data['close'])
        self.rsi_line.setData(times, rsi)
        
    def calculate_sma(self, prices: pd.Series, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean().fillna(0).values
        
    def calculate_ema(self, prices: pd.Series, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period).mean().fillna(0).values
        
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2) -> tuple:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        
        upper = (sma + (rolling_std * std)).fillna(0).values
        lower = (sma - (rolling_std * std)).fillna(0).values
        
        return upper, lower
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> np.ndarray:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50).values
        
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change"""
        self.symbol = symbol
        self.symbol_changed.emit(symbol)
        
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        self.timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        
    # Signals
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)


class CandlestickItem(pg.GraphicsObject):
    """Custom candlestick chart item"""
    
    def __init__(self):
        pg.GraphicsObject.__init__(self)
        self.data = None
        
    def setData(self, times, opens, highs, lows, closes):
        """Set candlestick data"""
        self.data = {
            'times': times,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes
        }
        self.prepareGeometryChange()
        self.update()
        
    def paint(self, painter, option, widget):
        """Paint candlesticks"""
        if self.data is None:
            return
            
        painter.setPen(pg.mkPen('black', width=1))
        
        times = self.data['times']
        opens = self.data['opens']
        highs = self.data['highs']
        lows = self.data['lows']
        closes = self.data['closes']
        
        width = 0.8
        
        for i in range(len(times)):
            x = times[i]
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]
            
            if np.isnan(o) or np.isnan(h) or np.isnan(l) or np.isnan(c):
                continue
                
            # Draw high-low line
            painter.drawLine(QPointF(x, l), QPointF(x, h))
            
            # Draw body
            if c > o:  # Green candle
                painter.setBrush(pg.mkBrush('green'))
                painter.drawRect(QRectF(x - width/2, o, width, c - o))
            else:  # Red candle
                painter.setBrush(pg.mkBrush('red'))
                painter.drawRect(QRectF(x - width/2, c, width, o - c))
                
    def boundingRect(self):
        """Return bounding rectangle"""
        if self.data is None:
            return QRectF()
            
        times = self.data['times']
        highs = self.data['highs']
        lows = self.data['lows']
        
        if len(times) == 0:
            return QRectF()
            
        min_time = min(times) - 1
        max_time = max(times) + 1
        min_price = min(lows[~np.isnan(lows)])
        max_price = max(highs[~np.isnan(highs)])
        
        return QRectF(min_time, min_price, max_time - min_time, max_price - min_price)
"""
Live chart integration for AuraTrade Bot GUI
Displays real-time price charts with technical indicators
"""

import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class TradingChartWidget(QWidget):
    """Real-time trading chart widget"""
    
    symbol_changed = pyqtSignal(str)
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_symbol = "EURUSD"
        self.current_timeframe = "M15"
        
        self.setup_ui()
        self.setup_chart()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Symbol selector
        control_layout.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "BTCUSD"])
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        control_layout.addWidget(self.symbol_combo)
        
        # Timeframe selector
        control_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1"])
        self.timeframe_combo.setCurrentText("M15")
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        control_layout.addWidget(self.timeframe_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_chart)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Chart widget
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground('black')
        self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.chart_widget)
        
    def setup_chart(self):
        """Setup the chart plotting"""
        # Main price plot
        self.price_plot = self.chart_widget.plot(pen=pg.mkPen('cyan', width=2))
        
        # Moving averages
        self.sma20_plot = self.chart_widget.plot(pen=pg.mkPen('yellow', width=1))
        self.sma50_plot = self.chart_widget.plot(pen=pg.mkPen('orange', width=1))
        
        # Support/Resistance lines
        self.support_line = pg.InfiniteLine(angle=0, pen=pg.mkPen('green', width=2, style=pg.QtCore.Qt.DashLine))
        self.resistance_line = pg.InfiniteLine(angle=0, pen=pg.mkPen('red', width=2, style=pg.QtCore.Qt.DashLine))
        
        self.chart_widget.addItem(self.support_line)
        self.chart_widget.addItem(self.resistance_line)
        
        # Labels
        self.chart_widget.setLabel('left', 'Price')
        self.chart_widget.setLabel('bottom', 'Time')
        self.chart_widget.setTitle(f'{self.current_symbol} - {self.current_timeframe}')
        
    def setup_timer(self):
        """Setup timer for real-time updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(5000)  # Update every 5 seconds
        
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change"""
        self.current_symbol = symbol
        self.symbol_changed.emit(symbol)
        self.refresh_chart()
        
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        self.refresh_chart()
        
    def update_chart(self):
        """Update chart with latest data"""
        try:
            # Get latest data from data manager
            data = self.data_manager.get_latest_data(self.current_symbol, self.current_timeframe, 200)
            
            if data is not None and len(data) > 0:
                # Extract time and price data
                times = np.arange(len(data))
                prices = data['close'].values
                
                # Update main price plot
                self.price_plot.setData(times, prices)
                
                # Calculate and plot moving averages
                if len(prices) >= 20:
                    sma20 = np.convolve(prices, np.ones(20)/20, mode='valid')
                    sma20_times = times[19:]
                    self.sma20_plot.setData(sma20_times, sma20)
                
                if len(prices) >= 50:
                    sma50 = np.convolve(prices, np.ones(50)/50, mode='valid')
                    sma50_times = times[49:]
                    self.sma50_plot.setData(sma50_times, sma50)
                
                # Update support/resistance levels
                recent_high = np.max(prices[-50:]) if len(prices) >= 50 else np.max(prices)
                recent_low = np.min(prices[-50:]) if len(prices) >= 50 else np.min(prices)
                
                self.resistance_line.setPos(recent_high)
                self.support_line.setPos(recent_low)
                
                # Update title with current price
                current_price = prices[-1]
                self.chart_widget.setTitle(f'{self.current_symbol} - {self.current_timeframe} - {current_price:.5f}')
                
        except Exception as e:
            print(f"Error updating chart: {e}")
    
    def refresh_chart(self):
        """Force refresh the chart"""
        self.update_chart()
    
    def add_trade_marker(self, price: float, trade_type: str, time_index: int = None):
        """Add trade entry/exit marker to chart"""
        try:
            if time_index is None:
                time_index = len(self.price_plot.getData()[0]) - 1
            
            color = 'green' if trade_type.lower() == 'buy' else 'red'
            symbol = '▲' if trade_type.lower() == 'buy' else '▼'
            
            # Add scatter plot for trade marker
            scatter = pg.ScatterPlotItem([time_index], [price], 
                                       pen=pg.mkPen(color, width=2),
                                       brush=pg.mkBrush(color),
                                       size=15,
                                       symbol=symbol)
            
            self.chart_widget.addItem(scatter)
            
        except Exception as e:
            print(f"Error adding trade marker: {e}")
