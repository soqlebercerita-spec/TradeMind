
"""
Swing Trading Strategy for AuraTrade Bot
Medium-term trend following with higher timeframes
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from utils.logger import Logger, log_info, log_error

class SwingStrategy:
    """Swing trading strategy for medium-term trends"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Swing Strategy"
        
        # Strategy parameters
        self.params = {
            'timeframe': 'H1',           # 1-hour charts
            'target_pips': 50,           # 50 pip target
            'stop_loss_pips': 30,        # 30 pip stop loss
            'min_confidence': 0.65,      # Minimum signal confidence
            'trend_period': 50,          # Trend detection period
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'adx_period': 14,
            'min_trend_strength': 25     # Minimum ADX for trend trades
        }
        
        # Performance tracking
        self.active_positions = {}
        self.trades_this_week = 0
        self.wins_this_week = 0
        
        log_info("SwingStrategy", "Swing strategy initialized")
    
    def analyze(self, symbol: str, data: pd.DataFrame, current_spread: float) -> Optional[Dict[str, Any]]:
        """Analyze market for swing trading opportunities"""
        try:
            if data.empty or len(data) < 100:
                return None
            
            # Don't open new positions if we already have one for this symbol
            if symbol in self.active_positions:
                return None
            
            # Calculate indicators
            indicators = self._calculate_indicators(data)
            if not indicators:
                return None
            
            # Generate signals
            signals = self._generate_signals(indicators, symbol)
            
            return signals
            
        except Exception as e:
            log_error("SwingStrategy", f"Error analyzing {symbol}", e)
            return None
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Calculate technical indicators for swing trading"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            # Trend indicators
            sma_20 = pd.Series(close).rolling(window=20).mean().values
            sma_50 = pd.Series(close).rolling(window=50).mean().values
            ema_20 = pd.Series(close).ewm(span=20).mean().values
            
            # MACD
            ema_12 = pd.Series(close).ewm(span=self.params['macd_fast']).mean()
            ema_26 = pd.Series(close).ewm(span=self.params['macd_slow']).mean()
            macd_line = (ema_12 - ema_26).values
            macd_signal = pd.Series(macd_line).ewm(span=self.params['macd_signal']).mean().values
            macd_histogram = macd_line - macd_signal
            
            # RSI
            delta = pd.Series(close).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).values
            
            # ADX for trend strength
            high_low = high - low
            high_close = np.abs(high - np.roll(close, 1))
            low_close = np.abs(low - np.roll(close, 1))
            tr = np.maximum(high_low, np.maximum(high_close, low_close))
            
            # Simplified ADX calculation
            plus_dm = np.where((high - np.roll(high, 1)) > (np.roll(low, 1) - low), 
                              np.maximum(high - np.roll(high, 1), 0), 0)
            minus_dm = np.where((np.roll(low, 1) - low) > (high - np.roll(high, 1)), 
                               np.maximum(np.roll(low, 1) - low, 0), 0)
            
            tr_smooth = pd.Series(tr).rolling(window=14).mean().values
            plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).mean() / tr_smooth).values
            minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).mean() / tr_smooth).values
            
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
            adx = pd.Series(dx).rolling(window=14).mean().values
            
            # Bollinger Bands
            bb_middle = pd.Series(close).rolling(window=self.params['bb_period']).mean().values
            bb_std = pd.Series(close).rolling(window=self.params['bb_period']).std().values
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            # Support and Resistance levels
            resistance = self._find_resistance_levels(high, close)
            support = self._find_support_levels(low, close)
            
            return {
                'close': close[-1],
                'sma_20': sma_20[-1] if not np.isnan(sma_20[-1]) else close[-1],
                'sma_50': sma_50[-1] if not np.isnan(sma_50[-1]) else close[-1],
                'ema_20': ema_20[-1] if not np.isnan(ema_20[-1]) else close[-1],
                'macd': macd_line[-1] if not np.isnan(macd_line[-1]) else 0,
                'macd_signal': macd_signal[-1] if not np.isnan(macd_signal[-1]) else 0,
                'macd_histogram': macd_histogram[-1] if not np.isnan(macd_histogram[-1]) else 0,
                'rsi': rsi[-1] if not np.isnan(rsi[-1]) else 50,
                'adx': adx[-1] if not np.isnan(adx[-1]) else 25,
                'plus_di': plus_di[-1] if not np.isnan(plus_di[-1]) else 25,
                'minus_di': minus_di[-1] if not np.isnan(minus_di[-1]) else 25,
                'bb_upper': bb_upper[-1] if not np.isnan(bb_upper[-1]) else close[-1] * 1.02,
                'bb_middle': bb_middle[-1] if not np.isnan(bb_middle[-1]) else close[-1],
                'bb_lower': bb_lower[-1] if not np.isnan(bb_lower[-1]) else close[-1] * 0.98,
                'resistance': resistance,
                'support': support
            }
            
        except Exception as e:
            log_error("SwingStrategy", "Error calculating indicators", e)
            return None
    
    def _find_resistance_levels(self, high: np.ndarray, close: np.ndarray) -> List[float]:
        """Find resistance levels from recent highs"""
        try:
            current_price = close[-1]
            recent_highs = []
            
            # Look for swing highs in the last 50 periods
            for i in range(2, min(50, len(high) - 2)):
                if (high[-i] > high[-i-1] and high[-i] > high[-i-2] and 
                    high[-i] > high[-i+1] and high[-i] > high[-i+2]):
                    if high[-i] > current_price:  # Only resistance above current price
                        recent_highs.append(high[-i])
            
            # Return top 3 resistance levels
            return sorted(set(recent_highs), reverse=True)[:3]
            
        except Exception:
            return []
    
    def _find_support_levels(self, low: np.ndarray, close: np.ndarray) -> List[float]:
        """Find support levels from recent lows"""
        try:
            current_price = close[-1]
            recent_lows = []
            
            # Look for swing lows in the last 50 periods
            for i in range(2, min(50, len(low) - 2)):
                if (low[-i] < low[-i-1] and low[-i] < low[-i-2] and 
                    low[-i] < low[-i+1] and low[-i] < low[-i+2]):
                    if low[-i] < current_price:  # Only support below current price
                        recent_lows.append(low[-i])
            
            # Return top 3 support levels
            return sorted(set(recent_lows), reverse=True)[:3]
            
        except Exception:
            return []
    
    def _generate_signals(self, indicators: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """Generate swing trading signals"""
        try:
            buy_score = 0
            sell_score = 0
            
            # Current values
            price = indicators['close']
            sma_20 = indicators['sma_20']
            sma_50 = indicators['sma_50']
            ema_20 = indicators['ema_20']
            macd = indicators['macd']
            macd_signal = indicators['macd_signal']
            macd_hist = indicators['macd_histogram']
            rsi = indicators['rsi']
            adx = indicators['adx']
            plus_di = indicators['plus_di']
            minus_di = indicators['minus_di']
            
            # Check trend strength first
            if adx < self.params['min_trend_strength']:
                return None  # No trade in weak trend conditions
            
            # Main trend signals (40% weight)
            if price > sma_20 > sma_50:  # Bullish alignment
                buy_score += 3
            elif price < sma_20 < sma_50:  # Bearish alignment
                sell_score += 3
            
            # MACD signals (25% weight)
            if macd > macd_signal and macd_hist > 0:  # MACD bullish
                buy_score += 2
            elif macd < macd_signal and macd_hist < 0:  # MACD bearish
                sell_score += 2
            
            # ADX/DI signals (20% weight)
            if plus_di > minus_di and adx > 25:  # Strong bullish trend
                buy_score += 1.5
            elif minus_di > plus_di and adx > 25:  # Strong bearish trend
                sell_score += 1.5
            
            # RSI confirmation (10% weight)
            if 30 < rsi < 70:  # RSI in neutral zone
                if rsi > 50:
                    buy_score += 0.5
                else:
                    sell_score += 0.5
            
            # Momentum confirmation (5% weight)
            if price > ema_20:
                buy_score += 0.5
            else:
                sell_score += 0.5
            
            # Support/Resistance consideration
            resistance_levels = indicators.get('resistance', [])
            support_levels = indicators.get('support', [])
            
            # Reduce buy signal if near resistance
            if resistance_levels and any(abs(price - r) / price < 0.005 for r in resistance_levels[:2]):
                buy_score *= 0.7
            
            # Reduce sell signal if near support
            if support_levels and any(abs(price - s) / price < 0.005 for s in support_levels[:2]):
                sell_score *= 0.7
            
            # Determine signal
            total_possible_score = 7.5
            
            if buy_score > sell_score and buy_score >= 4.5:
                confidence = min(buy_score / total_possible_score, 0.9)
                if confidence >= self.params['min_confidence']:
                    return {
                        'action': 'BUY',
                        'confidence': confidence,
                        'stop_loss_pips': self.params['stop_loss_pips'],
                        'take_profit_pips': self.params['target_pips'],
                        'signal_strength': buy_score,
                        'indicators': indicators,
                        'strategy': self.name,
                        'timestamp': datetime.now(),
                        'entry_reason': (f"Trend: {price>sma_20>sma_50}, MACD: {macd>macd_signal}, "
                                       f"ADX: {adx:.1f}, RSI: {rsi:.1f}")
                    }
            
            elif sell_score > buy_score and sell_score >= 4.5:
                confidence = min(sell_score / total_possible_score, 0.9)
                if confidence >= self.params['min_confidence']:
                    return {
                        'action': 'SELL',
                        'confidence': confidence,
                        'stop_loss_pips': self.params['stop_loss_pips'],
                        'take_profit_pips': self.params['target_pips'],
                        'signal_strength': sell_score,
                        'indicators': indicators,
                        'strategy': self.name,
                        'timestamp': datetime.now(),
                        'entry_reason': (f"Trend: {price<sma_20<sma_50}, MACD: {macd<macd_signal}, "
                                       f"ADX: {adx:.1f}, RSI: {rsi:.1f}")
                    }
            
            return None
            
        except Exception as e:
            log_error("SwingStrategy", "Error generating signals", e)
            return None
    
    def on_trade_opened(self, trade_info: Dict[str, Any]):
        """Handle trade opened event"""
        try:
            symbol = trade_info.get('symbol')
            self.active_positions[symbol] = {
                'ticket': trade_info.get('ticket'),
                'open_time': datetime.now(),
                'open_price': trade_info.get('price'),
                'action': trade_info.get('action')
            }
            
            self.trades_this_week += 1
            
            log_info("SwingStrategy", 
                    f"Swing trade opened: {symbol} {trade_info.get('action')} "
                    f"@ {trade_info.get('price', 0):.5f}")
            
        except Exception as e:
            log_error("SwingStrategy", "Error handling trade opened", e)
    
    def on_trade_closed(self, trade_info: Dict[str, Any]):
        """Handle trade closed event"""
        try:
            symbol = trade_info.get('symbol')
            if symbol in self.active_positions:
                del self.active_positions[symbol]
            
            profit = trade_info.get('profit', 0)
            if profit > 0:
                self.wins_this_week += 1
            
            win_rate = (self.wins_this_week / self.trades_this_week * 100) if self.trades_this_week > 0 else 0
            
            log_info("SwingStrategy", 
                    f"Swing trade closed: {symbol} "
                    f"P&L: ${profit:.2f}, Win Rate: {win_rate:.1f}%")
            
        except Exception as e:
            log_error("SwingStrategy", "Error handling trade closed", e)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information and statistics"""
        try:
            win_rate = (self.wins_this_week / self.trades_this_week * 100) if self.trades_this_week > 0 else 0
            
            return {
                'name': self.name,
                'type': 'Swing Trading',
                'timeframe': self.params['timeframe'],
                'target_pips': self.params['target_pips'],
                'stop_loss_pips': self.params['stop_loss_pips'],
                'trades_this_week': self.trades_this_week,
                'wins_this_week': self.wins_this_week,
                'win_rate': win_rate,
                'active_positions': len(self.active_positions),
                'min_trend_strength': self.params['min_trend_strength'],
                'status': 'Active'
            }
            
        except Exception as e:
            log_error("SwingStrategy", "Error getting strategy info", e)
            return {'name': self.name, 'status': 'Error'}
    
    def reset_weekly_stats(self):
        """Reset weekly statistics"""
        self.trades_this_week = 0
        self.wins_this_week = 0
        log_info("SwingStrategy", "Weekly statistics reset")
