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

class ChartWidget(QWidget if PYQT_AVAILABLE else object):
    """Real-time chart widget for price display"""

    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.init_ui()
        else:
            pass

        self.logger = Logger().get_logger()
        self.figure = Figure(figsize=(12, 8), facecolor='#2b2b2b')
        self.canvas = FigureCanvas(self.figure) if PYQT_AVAILABLE else None
        self.data_cache = {}

    def init_ui(self):
        """Initialize the UI"""
        if not PYQT_AVAILABLE:
            return

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # Set dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)

    def plot_candlestick_chart(self, symbol: str, rates: pd.DataFrame, indicators: Dict):
        """Plot candlestick chart with indicators"""
        try:
            if rates is None or len(rates) < 20:
                return

            self.figure.clear()

            # Create subplots
            ax1 = self.figure.add_subplot(3, 1, 1)  # Price
            ax2 = self.figure.add_subplot(3, 1, 2)  # Volume
            ax3 = self.figure.add_subplot(3, 1, 3)  # Oscillators

            # Plot candlesticks (simplified as line chart)
            ax1.plot(rates.index, rates['close'], color='#2196F3', linewidth=2, label='Close Price')
            ax1.fill_between(rates.index, rates['low'], rates['high'], alpha=0.3, color='#2196F3')

            # Plot moving averages if available
            if 'ma_10' in indicators:
                ax1.plot(rates.index, indicators['ma_10'], color='#FF9800', linewidth=1, label='MA10')
            if 'ema_50' in indicators:
                ax1.plot(rates.index, indicators['ema_50'], color='#4CAF50', linewidth=1, label='EMA50')

            # Plot Bollinger Bands if available
            if all(k in indicators for k in ['bb_upper', 'bb_middle', 'bb_lower']):
                ax1.plot(rates.index, indicators['bb_upper'], color='#9C27B0', alpha=0.7, linewidth=1)
                ax1.plot(rates.index, indicators['bb_middle'], color='#9C27B0', alpha=0.7, linewidth=1)
                ax1.plot(rates.index, indicators['bb_lower'], color='#9C27B0', alpha=0.7, linewidth=1)
                ax1.fill_between(rates.index, indicators['bb_upper'], indicators['bb_lower'],
                               alpha=0.1, color='#9C27B0')

            ax1.set_title(f'{symbol} - Real-time Price Chart', color='white', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price', color='white')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            ax1.set_facecolor('#1e1e1e')

            # Plot volume
            if 'tick_volume' in rates.columns:
                ax2.bar(rates.index, rates['tick_volume'], color='#607D8B', alpha=0.7, width=0.8)
            ax2.set_ylabel('Volume', color='white')
            ax2.grid(True, alpha=0.3)
            ax2.set_facecolor('#1e1e1e')

            # Plot RSI if available
            if 'rsi' in indicators:
                ax3.plot(rates.index, indicators['rsi'], color='#FF5722', linewidth=2, label='RSI')
                ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                ax3.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
                ax3.set_ylim(0, 100)
                ax3.set_ylabel('RSI', color='white')
                ax3.legend(loc='upper left')

            # Plot MACD if available
            if all(k in indicators for k in ['macd_line', 'macd_signal', 'macd_histogram']):
                ax3_twin = ax3.twinx()
                ax3_twin.plot(rates.index, indicators['macd_line'], color='#00BCD4', linewidth=1, label='MACD')
                ax3_twin.plot(rates.index, indicators['macd_signal'], color='#FFC107', linewidth=1, label='Signal')
                ax3_twin.bar(rates.index, indicators['macd_histogram'], color='gray', alpha=0.3, width=0.8)
                ax3_twin.legend(loc='upper right')
                ax3_twin.set_ylabel('MACD', color='white')

            ax3.grid(True, alpha=0.3)
            ax3.set_facecolor('#1e1e1e')
            ax3.set_xlabel('Time', color='white')

            # Style the figure
            self.figure.patch.set_facecolor('#2b2b2b')

            for ax in [ax1, ax2, ax3]:
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')

            plt.tight_layout()

            if self.canvas:
                self.canvas.draw()

        except Exception as e:
            self.logger.error(f"Error plotting chart: {e}")

    def update_chart(self, symbol: str, rates: pd.DataFrame, indicators: Dict):
        """Update chart with new data"""
        self.plot_candlestick_chart(symbol, rates, indicators)

    def save_chart(self, filename: str):
        """Save chart to file"""
        try:
            self.figure.savefig(filename, facecolor='#2b2b2b', dpi=300, bbox_inches='tight')
            self.logger.info(f"Chart saved to: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving chart: {e}")
            return False

class TechnicalAnalysisChart:
    """Technical analysis visualization"""

    def __init__(self):
        self.logger = Logger().get_logger()

    def create_indicator_summary(self, indicators: Dict) -> str:
        """Create text summary of indicators"""
        try:
            summary = "Technical Indicators Summary:\n"
            summary += "=" * 40 + "\n"

            if 'rsi' in indicators:
                rsi = indicators['rsi']
                rsi_signal = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
                summary += f"RSI: {rsi:.2f} ({rsi_signal})\n"

            if 'ma_10' in indicators and 'ema_50' in indicators:
                ma_10 = indicators['ma_10']
                ema_50 = indicators['ema_50']
                trend = "Bullish" if ma_10 > ema_50 else "Bearish"
                summary += f"Trend (MA10 vs EMA50): {trend}\n"

            if 'macd_line' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd_line']
                signal = indicators['macd_signal']
                macd_signal = "Bullish" if macd > signal else "Bearish"
                summary += f"MACD: {macd:.4f} ({macd_signal})\n"

            if 'stoch_k' in indicators:
                stoch = indicators['stoch_k']
                stoch_signal = "Oversold" if stoch < 20 else "Overbought" if stoch > 80 else "Neutral"
                summary += f"Stochastic: {stoch:.2f} ({stoch_signal})\n"

            if 'bb_upper' in indicators and 'bb_lower' in indicators:
                summary += f"Bollinger Bands: Upper {indicators['bb_upper']:.5f}, Lower {indicators['bb_lower']:.5f}\n"

            if 'atr' in indicators:
                summary += f"ATR (Volatility): {indicators['atr']:.5f}\n"

            return summary

        except Exception as e:
            self.logger.error(f"Error creating indicator summary: {e}")
            return "Error generating summary"

    def analyze_signal_strength(self, indicators: Dict) -> Dict:
        """Analyze overall signal strength"""
        try:
            signals = {
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0,
                'overall': 'NEUTRAL',
                'strength': 0.5,
                'details': []
            }

            # RSI analysis
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi < 30:
                    signals['bullish_count'] += 1
                    signals['details'].append("RSI Oversold (Bullish)")
                elif rsi > 70:
                    signals['bearish_count'] += 1
                    signals['details'].append("RSI Overbought (Bearish)")
                else:
                    signals['neutral_count'] += 1
                    signals['details'].append("RSI Neutral")

            # Moving average analysis
            if 'ma_10' in indicators and 'ema_50' in indicators:
                if indicators['ma_10'] > indicators['ema_50']:
                    signals['bullish_count'] += 1
                    signals['details'].append("MA10 > EMA50 (Bullish)")
                else:
                    signals['bearish_count'] += 1
                    signals['details'].append("MA10 < EMA50 (Bearish)")

            # MACD analysis
            if 'macd_line' in indicators and 'macd_signal' in indicators:
                if indicators['macd_line'] > indicators['macd_signal']:
                    signals['bullish_count'] += 1
                    signals['details'].append("MACD Bullish Cross")
                else:
                    signals['bearish_count'] += 1
                    signals['details'].append("MACD Bearish Cross")

            # Stochastic analysis
            if 'stoch_k' in indicators:
                stoch = indicators['stoch_k']
                if stoch < 20:
                    signals['bullish_count'] += 1
                    signals['details'].append("Stochastic Oversold (Bullish)")
                elif stoch > 80:
                    signals['bearish_count'] += 1
                    signals['details'].append("Stochastic Overbought (Bearish)")
                else:
                    signals['neutral_count'] += 1
                    signals['details'].append("Stochastic Neutral")

            # Determine overall signal
            total_signals = signals['bullish_count'] + signals['bearish_count'] + signals['neutral_count']

            if total_signals > 0:
                bullish_ratio = signals['bullish_count'] / total_signals
                bearish_ratio = signals['bearish_count'] / total_signals

                if bullish_ratio > 0.6:
                    signals['overall'] = 'BULLISH'
                    signals['strength'] = 0.5 + (bullish_ratio - 0.5)
                elif bearish_ratio > 0.6:
                    signals['overall'] = 'BEARISH'
                    signals['strength'] = 0.5 - (bearish_ratio - 0.5)
                else:
                    signals['overall'] = 'NEUTRAL'
                    signals['strength'] = 0.5

            return signals

        except Exception as e:
            self.logger.error(f"Error analyzing signal strength: {e}")
            return {'overall': 'ERROR', 'strength': 0.5, 'details': ['Analysis error']}

class PatternRecognitionChart:
    """Chart pattern recognition and visualization"""

    def __init__(self):
        self.logger = Logger().get_logger()

    def detect_chart_patterns(self, rates: pd.DataFrame) -> List[Dict]:
        """Detect common chart patterns"""
        patterns = []

        try:
            if len(rates) < 20:
                return patterns

            # Simple pattern detection
            close_prices = rates['close'].values
            high_prices = rates['high'].values
            low_prices = rates['low'].values

            # Double top/bottom detection (simplified)
            recent_highs = []
            recent_lows = []

            for i in range(5, len(close_prices) - 5):
                # Local maxima
                if (high_prices[i] > high_prices[i-1] and high_prices[i] > high_prices[i+1] and
                    high_prices[i] > high_prices[i-2] and high_prices[i] > high_prices[i+2]):
                    recent_highs.append((i, high_prices[i]))

                # Local minima
                if (low_prices[i] < low_prices[i-1] and low_prices[i] < low_prices[i+1] and
                    low_prices[i] < low_prices[i-2] and low_prices[i] < low_prices[i+2]):
                    recent_lows.append((i, low_prices[i]))

            # Check for double top
            if len(recent_highs) >= 2:
                last_two_highs = recent_highs[-2:]
                if abs(last_two_highs[0][1] - last_two_highs[1][1]) / last_two_highs[0][1] < 0.002:  # Within 0.2%
                    patterns.append({
                        'type': 'Double Top',
                        'signal': 'BEARISH',
                        'confidence': 0.7,
                        'description': 'Double top pattern detected - potential bearish reversal'
                    })

            # Check for double bottom
            if len(recent_lows) >= 2:
                last_two_lows = recent_lows[-2:]
                if abs(last_two_lows[0][1] - last_two_lows[1][1]) / last_two_lows[0][1] < 0.002:  # Within 0.2%
                    patterns.append({
                        'type': 'Double Bottom',
                        'signal': 'BULLISH',
                        'confidence': 0.7,
                        'description': 'Double bottom pattern detected - potential bullish reversal'
                    })

            # Triangle pattern detection (simplified)
            if len(rates) >= 20:
                recent_data = rates.tail(20)
                highs_trend = np.polyfit(range(len(recent_data)), recent_data['high'], 1)[0]
                lows_trend = np.polyfit(range(len(recent_data)), recent_data['low'], 1)[0]

                if abs(highs_trend) < 0.0001 and abs(lows_trend) < 0.0001:  # Converging lines
                    patterns.append({
                        'type': 'Triangle',
                        'signal': 'NEUTRAL',
                        'confidence': 0.6,
                        'description': 'Triangle pattern - await breakout direction'
                    })

        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")

        return patterns

    def detect_support_resistance(self, rates: pd.DataFrame) -> Dict:
        """Detect support and resistance levels"""
        try:
            if len(rates) < 50:
                return {'support': [], 'resistance': []}

            close_prices = rates['close'].values
            high_prices = rates['high'].values
            low_prices = rates['low'].values

            support_levels = []
            resistance_levels = []

            # Find significant price levels
            for i in range(10, len(close_prices) - 10):
                # Resistance levels (local maxima)
                if (high_prices[i] >= max(high_prices[i-5:i+5]) and
                    high_prices[i] >= high_prices[-1] * 0.999):  # Near current price

                    # Count touches
                    touches = sum(1 for price in high_prices[i-10:i+10]
                                 if abs(price - high_prices[i]) / high_prices[i] < 0.001)

                    if touches >= 2:
                        resistance_levels.append({
                            'level': high_prices[i],
                            'strength': min(touches / 3, 1.0),
                            'touches': touches
                        })

                # Support levels (local minima)
                if (low_prices[i] <= min(low_prices[i-5:i+5]) and
                    low_prices[i] <= low_prices[-1] * 1.001):  # Near current price

                    # Count touches
                    touches = sum(1 for price in low_prices[i-10:i+10]
                                 if abs(price - low_prices[i]) / low_prices[i] < 0.001)

                    if touches >= 2:
                        support_levels.append({
                            'level': low_prices[i],
                            'strength': min(touches / 3, 1.0),
                            'touches': touches
                        })

            # Sort by strength and keep top 3
            support_levels = sorted(support_levels, key=lambda x: x['strength'], reverse=True)[:3]
            resistance_levels = sorted(resistance_levels, key=lambda x: x['strength'], reverse=True)[:3]

            return {
                'support': support_levels,
                'resistance': resistance_levels
            }

        except Exception as e:
            self.logger.error(f"Error detecting support/resistance: {e}")
            return {'support': [], 'resistance': []}

    def calculate_fibonacci_levels(self, rates: pd.DataFrame) -> Dict:
        """Calculate Fibonacci retracement levels"""
        try:
            if len(rates) < 20:
                return {}

            # Find swing high and low
            recent_data = rates.tail(50)  # Last 50 bars

            swing_high = recent_data['high'].max()
            swing_low = recent_data['low'].min()

            diff = swing_high - swing_low

            fib_levels = {
                '0.0%': swing_low,
                '23.6%': swing_low + diff * 0.236,
                '38.2%': swing_low + diff * 0.382,
                '50.0%': swing_low + diff * 0.5,
                '61.8%': swing_low + diff * 0.618,
                '78.6%': swing_low + diff * 0.786,
                '100.0%': swing_high
            }

            return fib_levels

        except Exception as e:
            self.logger.error(f"Error calculating Fibonacci levels: {e}")
            return {}

# Export classes for use
__all__ = ['ChartWidget', 'TechnicalAnalysisChart', 'PatternRecognitionChart']