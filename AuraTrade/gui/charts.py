
"""
Chart components for AuraTrade Bot GUI
Real-time price charts and technical analysis visualization
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QComboBox, QCheckBox, QGroupBox,
                           QScrollArea, QFrame)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QPen
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from utils.logger import Logger

class SimpleChart(QWidget):
    """Simple price chart widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger().get_logger()
        self.price_data = []
        self.indicators = {}
        self.max_points = 100
        
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3d3d3d;")
        
    def update_data(self, rates: pd.DataFrame, indicators: Dict = None):
        """Update chart with new data"""
        try:
            if rates is not None and len(rates) > 0:
                # Keep only last max_points
                self.price_data = rates.tail(self.max_points)
                
            if indicators:
                self.indicators = indicators
                
            self.update()  # Trigger repaint
            
        except Exception as e:
            self.logger.error(f"Error updating chart data: {e}")
    
    def paintEvent(self, event):
        """Paint the chart"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Background
            painter.fillRect(self.rect(), QColor("#1e1e1e"))
            
            if len(self.price_data) < 2:
                # Draw "No Data" message
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.drawText(self.rect(), Qt.AlignCenter, "No Price Data Available")
                return
            
            # Calculate drawing area
            margin = 20
            chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)
            
            # Get price range
            prices = self.price_data['close'].values
            min_price = np.min(prices)
            max_price = np.max(prices)
            price_range = max_price - min_price
            
            if price_range == 0:
                price_range = min_price * 0.01  # 1% range if prices are same
            
            # Draw price line
            painter.setPen(QPen(QColor("#00ff00"), 2))
            
            points = []
            for i, price in enumerate(prices):
                x = chart_rect.left() + (i * chart_rect.width() / (len(prices) - 1))
                y = chart_rect.bottom() - ((price - min_price) / price_range) * chart_rect.height()
                points.append((x, y))
            
            # Draw the price line
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            
            # Draw grid
            painter.setPen(QPen(QColor("#3d3d3d"), 1))
            
            # Horizontal grid lines
            for i in range(5):
                y = chart_rect.top() + (i * chart_rect.height() / 4)
                painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)
            
            # Vertical grid lines
            for i in range(5):
                x = chart_rect.left() + (i * chart_rect.width() / 4)
                painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())
            
            # Draw price labels
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawText(chart_rect.right() + 5, chart_rect.top() + 10, f"{max_price:.5f}")
            painter.drawText(chart_rect.right() + 5, chart_rect.bottom(), f"{min_price:.5f}")
            
            # Draw current price
            if len(prices) > 0:
                current_price = prices[-1]
                painter.setPen(QPen(QColor("#ffff00"), 2))
                painter.drawText(chart_rect.right() + 5, chart_rect.center().y(), f"{current_price:.5f}")
            
        except Exception as e:
            self.logger.error(f"Error painting chart: {e}")

class ChartControls(QWidget):
    """Chart control panel"""
    
    symbolChanged = pyqtSignal(str)
    timeframeChanged = pyqtSignal(str)
    indicatorToggled = pyqtSignal(str, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the control UI"""
        layout = QVBoxLayout(self)
        
        # Symbol selection
        symbol_group = QGroupBox("Symbol")
        symbol_layout = QHBoxLayout(symbol_group)
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"])
        self.symbol_combo.currentTextChanged.connect(self.symbolChanged.emit)
        symbol_layout.addWidget(self.symbol_combo)
        
        layout.addWidget(symbol_group)
        
        # Timeframe selection
        timeframe_group = QGroupBox("Timeframe")
        timeframe_layout = QHBoxLayout(timeframe_group)
        
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1"])
        self.timeframe_combo.currentTextChanged.connect(self.timeframeChanged.emit)
        timeframe_layout.addWidget(self.timeframe_combo)
        
        layout.addWidget(timeframe_group)
        
        # Indicators
        indicators_group = QGroupBox("Indicators")
        indicators_layout = QVBoxLayout(indicators_group)
        
        self.ma_checkbox = QCheckBox("Moving Averages")
        self.ma_checkbox.setChecked(True)
        self.ma_checkbox.toggled.connect(lambda checked: self.indicatorToggled.emit("MA", checked))
        indicators_layout.addWidget(self.ma_checkbox)
        
        self.rsi_checkbox = QCheckBox("RSI")
        self.rsi_checkbox.setChecked(True)
        self.rsi_checkbox.toggled.connect(lambda checked: self.indicatorToggled.emit("RSI", checked))
        indicators_layout.addWidget(self.rsi_checkbox)
        
        self.macd_checkbox = QCheckBox("MACD")
        self.macd_checkbox.toggled.connect(lambda checked: self.indicatorToggled.emit("MACD", checked))
        indicators_layout.addWidget(self.macd_checkbox)
        
        self.bb_checkbox = QCheckBox("Bollinger Bands")
        self.bb_checkbox.toggled.connect(lambda checked: self.indicatorToggled.emit("BB", checked))
        indicators_layout.addWidget(self.bb_checkbox)
        
        layout.addWidget(indicators_group)
        
        layout.addStretch()

class ChartWidget(QWidget):
    """Complete chart widget with controls"""
    
    def __init__(self, data_manager=None, parent=None):
        super().__init__(parent)
        self.logger = Logger().get_logger()
        self.data_manager = data_manager
        
        self.setup_ui()
        self.setup_timer()
        
        # Current settings
        self.current_symbol = "EURUSD"
        self.current_timeframe = "M1"
        self.active_indicators = {"MA": True, "RSI": True}
        
    def setup_ui(self):
        """Setup the chart UI"""
        layout = QHBoxLayout(self)
        
        # Chart area
        self.chart = SimpleChart()
        layout.addWidget(self.chart, 3)  # 3/4 of space
        
        # Controls area
        self.controls = ChartControls()
        self.controls.symbolChanged.connect(self.on_symbol_changed)
        self.controls.timeframeChanged.connect(self.on_timeframe_changed)
        self.controls.indicatorToggled.connect(self.on_indicator_toggled)
        
        layout.addWidget(self.controls, 1)  # 1/4 of space
        
    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(1000)  # Update every second
        
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change"""
        self.current_symbol = symbol
        self.logger.info(f"Chart symbol changed to: {symbol}")
        self.update_chart()
        
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        self.logger.info(f"Chart timeframe changed to: {timeframe}")
        self.update_chart()
        
    def on_indicator_toggled(self, indicator: str, enabled: bool):
        """Handle indicator toggle"""
        self.active_indicators[indicator] = enabled
        self.logger.info(f"Indicator {indicator} {'enabled' if enabled else 'disabled'}")
        self.update_chart()
        
    def update_chart(self):
        """Update chart with latest data"""
        try:
            if not self.data_manager:
                return
                
            # Get latest data
            rates = self.data_manager.get_rates(
                symbol=self.current_symbol,
                timeframe=self.current_timeframe,
                count=100
            )
            
            if rates is not None and len(rates) > 0:
                # Calculate indicators if enabled
                indicators = {}
                
                if self.active_indicators.get("MA", False):
                    indicators['ma_20'] = rates['close'].rolling(window=20).mean()
                    indicators['ma_50'] = rates['close'].rolling(window=50).mean()
                
                if self.active_indicators.get("RSI", False):
                    indicators['rsi'] = self._calculate_rsi(rates)
                
                if self.active_indicators.get("MACD", False):
                    macd_data = self._calculate_macd(rates)
                    indicators.update(macd_data)
                
                if self.active_indicators.get("BB", False):
                    bb_data = self._calculate_bollinger_bands(rates)
                    indicators.update(bb_data)
                
                # Update chart
                self.chart.update_data(rates, indicators)
                
        except Exception as e:
            self.logger.error(f"Error updating chart: {e}")
    
    def _calculate_rsi(self, rates: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = rates['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(rates), index=rates.index)
    
    def _calculate_macd(self, rates: pd.DataFrame) -> Dict:
        """Calculate MACD"""
        try:
            exp1 = rates['close'].ewm(span=12).mean()
            exp2 = rates['close'].ewm(span=26).mean()
            
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9).mean()
            
            return {
                'macd_line': macd_line,
                'macd_signal': signal_line
            }
        except:
            return {'macd_line': pd.Series([0] * len(rates)), 'macd_signal': pd.Series([0] * len(rates))}
    
    def _calculate_bollinger_bands(self, rates: pd.DataFrame) -> Dict:
        """Calculate Bollinger Bands"""
        try:
            sma = rates['close'].rolling(window=20).mean()
            std = rates['close'].rolling(window=20).std()
            
            return {
                'bb_upper': sma + (std * 2),
                'bb_middle': sma,
                'bb_lower': sma - (std * 2)
            }
        except:
            return {'bb_upper': pd.Series([0] * len(rates)), 'bb_middle': pd.Series([0] * len(rates)), 'bb_lower': pd.Series([0] * len(rates))}
