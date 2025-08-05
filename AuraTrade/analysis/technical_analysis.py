
"""
Technical Analysis Module for AuraTrade Bot
Comprehensive technical indicators and analysis tools
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import talib
from utils.logger import Logger, log_info, log_error

class TechnicalAnalysis:
    """Advanced technical analysis engine"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.cache = {}
        self.cache_timeout = 60  # seconds
        
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive technical analysis for a symbol"""
        try:
            if data.empty or len(data) < 50:
                return {}
                
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'trend': self.analyze_trend(data),
                'momentum': self.analyze_momentum(data),
                'volatility': self.analyze_volatility(data),
                'support_resistance': self.find_support_resistance(data),
                'patterns': self.detect_patterns(data),
                'signals': self.generate_signals(data),
                'risk_metrics': self.calculate_risk_metrics(data)
            }
            
            return analysis
            
        except Exception as e:
            log_error("TechnicalAnalysis", f"Error analyzing {symbol}", e)
            return {}
    
    def analyze_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend direction and strength"""
        try:
            close = data['close'].values
            
            # Moving averages
            sma_20 = talib.SMA(close, timeperiod=20)
            sma_50 = talib.SMA(close, timeperiod=50)
            ema_12 = talib.EMA(close, timeperiod=12)
            ema_26 = talib.EMA(close, timeperiod=26)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close)
            
            # ADX for trend strength
            high = data['high'].values
            low = data['low'].values
            adx = talib.ADX(high, low, close, timeperiod=14)
            
            # Current values
            current_price = close[-1]
            current_sma20 = sma_20[-1] if not np.isnan(sma_20[-1]) else current_price
            current_sma50 = sma_50[-1] if not np.isnan(sma_50[-1]) else current_price
            current_adx = adx[-1] if not np.isnan(adx[-1]) else 25
            current_macd = macd[-1] if not np.isnan(macd[-1]) else 0
            current_signal = macd_signal[-1] if not np.isnan(macd_signal[-1]) else 0
            
            # Trend determination
            trend_direction = "NEUTRAL"
            if current_price > current_sma20 > current_sma50 and current_macd > current_signal:
                trend_direction = "BULLISH"
            elif current_price < current_sma20 < current_sma50 and current_macd < current_signal:
                trend_direction = "BEARISH"
            
            # Trend strength
            trend_strength = "WEAK"
            if current_adx > 40:
                trend_strength = "VERY_STRONG"
            elif current_adx > 25:
                trend_strength = "STRONG"
            elif current_adx > 15:
                trend_strength = "MODERATE"
            
            return {
                'direction': trend_direction,
                'strength': trend_strength,
                'adx': current_adx,
                'sma_20': current_sma20,
                'sma_50': current_sma50,
                'macd': current_macd,
                'macd_signal': current_signal,
                'price_vs_sma20': (current_price - current_sma20) / current_sma20 * 100
            }
            
        except Exception as e:
            log_error("TechnicalAnalysis", "Error in trend analysis", e)
            return {}
    
    def analyze_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum indicators"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            # RSI
            rsi = talib.RSI(close, timeperiod=14)
            
            # Stochastic
            slowk, slowd = talib.STOCH(high, low, close)
            
            # Williams %R
            willr = talib.WILLR(high, low, close, timeperiod=14)
            
            # CCI
            cci = talib.CCI(high, low, close, timeperiod=14)
            
            # Current values
            current_rsi = rsi[-1] if not np.isnan(rsi[-1]) else 50
            current_stoch_k = slowk[-1] if not np.isnan(slowk[-1]) else 50
            current_willr = willr[-1] if not np.isnan(willr[-1]) else -50
            current_cci = cci[-1] if not np.isnan(cci[-1]) else 0
            
            # Momentum assessment
            momentum_score = 0
            
            # RSI scoring
            if current_rsi > 70:
                momentum_score -= 2  # Overbought
            elif current_rsi > 60:
                momentum_score += 1  # Bullish
            elif current_rsi < 30:
                momentum_score += 2  # Oversold (bullish reversal)
            elif current_rsi < 40:
                momentum_score -= 1  # Bearish
            
            # Stochastic scoring
            if current_stoch_k > 80:
                momentum_score -= 1
            elif current_stoch_k < 20:
                momentum_score += 1
            
            momentum_signal = "NEUTRAL"
            if momentum_score >= 2:
                momentum_signal = "BULLISH"
            elif momentum_score <= -2:
                momentum_signal = "BEARISH"
            
            return {
                'signal': momentum_signal,
                'score': momentum_score,
                'rsi': current_rsi,
                'stoch_k': current_stoch_k,
                'willr': current_willr,
                'cci': current_cci,
                'overbought': current_rsi > 70 or current_stoch_k > 80,
                'oversold': current_rsi < 30 or current_stoch_k < 20
            }
            
        except Exception as e:
            log_error("TechnicalAnalysis", "Error in momentum analysis", e)
            return {}
    
    def analyze_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volatility and market conditions"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            
            # ATR
            atr = talib.ATR(high, low, close, timeperiod=14)
            
            # Current values
            current_price = close[-1]
            current_bb_upper = bb_upper[-1] if not np.isnan(bb_upper[-1]) else current_price * 1.02
            current_bb_lower = bb_lower[-1] if not np.isnan(bb_lower[-1]) else current_price * 0.98
            current_bb_middle = bb_middle[-1] if not np.isnan(bb_middle[-1]) else current_price
            current_atr = atr[-1] if not np.isnan(atr[-1]) else current_price * 0.01
            
            # Bollinger Band position
            bb_position = (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower)
            
            # Volatility level
            atr_percent = (current_atr / current_price) * 100
            volatility_level = "LOW"
            if atr_percent > 2.0:
                volatility_level = "HIGH"
            elif atr_percent > 1.0:
                volatility_level = "MEDIUM"
            
            # Squeeze detection
            bb_width = (current_bb_upper - current_bb_lower) / current_bb_middle
            is_squeeze = bb_width < 0.1  # Adjust threshold as needed
            
            return {
                'level': volatility_level,
                'atr': current_atr,
                'atr_percent': atr_percent,
                'bb_upper': current_bb_upper,
                'bb_middle': current_bb_middle,
                'bb_lower': current_bb_lower,
                'bb_position': bb_position,
                'bb_width': bb_width,
                'is_squeeze': is_squeeze,
                'near_bb_upper': bb_position > 0.8,
                'near_bb_lower': bb_position < 0.2
            }
            
        except Exception as e:
            log_error("TechnicalAnalysis", "Error in volatility analysis", e)
            return {}
    
    def find_support_resistance(self, data: pd.DataFrame) -> Dict[str, List[float]]:
        """Find key support and resistance levels"""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            
            # Pivot points
            pivot_high = []
            pivot_low = []
            
            for i in range(2, len(data) - 2):
                # High pivot
                if (high[i] > high[i-1] and high[i] > high[i-2] and 
                    high[i] > high[i+1] and high[i] > high[i+2]):
                    pivot_high.append(high[i])
                
                # Low pivot
                if (low[i] < low[i-1] and low[i] < low[i-2] and 
                    low[i] < low[i+1] and low[i] < low[i+2]):
                    pivot_low.append(low[i])
            
            # Get recent significant levels
            current_price = close[-1]
            resistance_levels = [r for r in pivot_high if r > current_price][-3:]
            support_levels = [s for s in pivot_low if s < current_price][-3:]
            
            return {
                'resistance': sorted(resistance_levels)[:3],
                'support': sorted(support_levels, reverse=True)[:3],
                'pivot_highs': pivot_high,
                'pivot_lows': pivot_low
            }
            
        except Exception as e:
            log_error("TechnicalAnalysis", "Error finding support/resistance", e)
            return {'resistance': [], 'support': [], 'pivot_highs': [], 'pivot_lows': []}
    
    def detect_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect chart patterns"""
        try:
            open_prices = data['open'].values
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            
            # Candlestick patterns
            patterns = {}
            
            # Doji
            doji = talib.CDLDOJI(open_prices, high, low, close)
            patterns['doji'] = bool(doji[-1] != 0)
            
            # Hammer
            hammer = talib.CDLHAMMER(open_prices, high, low, close)
            patterns['hammer'] = bool(hammer[-1] != 0)
            
            # Engulfing
            engulfing = talib.CDLENGULFING(open_prices, high, low, close)
            patterns['engulfing'] = bool(engulfing[-1] != 0)
            
            # Morning Star
            morning_star = talib.CDLMORNINGSTAR(open_prices, high, low, close)
            patterns['morning_star'] = bool(morning_star[-1] != 0)
            
            # Evening Star
            evening_star = talib.CDLEVENINGSTAR(open_prices, high, low, close)
            patterns['evening_star'] = bool(evening_star[-1] != 0)
            
            # Pattern summary
            bullish_patterns = ['hammer', 'morning_star'] + ['engulfing' if engulfing[-1] > 0 else None]
            bearish_patterns = ['evening_star'] + ['engulfing' if engulfing[-1] < 0 else None]
            
            bullish_count = sum(1 for p in bullish_patterns if p and patterns.get(p, False))
            bearish_count = sum(1 for p in bearish_patterns if p and patterns.get(p, False))
            
            pattern_signal = "NEUTRAL"
            if bullish_count > bearish_count:
                pattern_signal = "BULLISH"
            elif bearish_count > bullish_count:
                pattern_signal = "BEARISH"
            
            return {
                'signal': pattern_signal,
                'patterns': patterns,
                'bullish_count': bullish_count,
                'bearish_count': bearish_count
            }
            
        except Exception as e:
            log_error("TechnicalAnalysis", "Error detecting patterns", e)
            return {'signal': 'NEUTRAL', 'patterns': {}, 'bullish_count': 0, 'bearish_count': 0}
    
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate combined trading signals"""
        try:
            # Get all analysis components
            trend = self.analyze_trend(data)
            momentum = self.analyze_momentum(data)
            volatility = self.analyze_volatility(data)
            patterns = self.detect_patterns(data)
            
            # Signal scoring
            signal_score = 0
            confidence = 0.5
            
            # Trend component (40% weight)
            if trend.get('direction') == 'BULLISH':
                signal_score += 2
            elif trend.get('direction') == 'BEARISH':
                signal_score -= 2
            
            # Momentum component (30% weight)
            if momentum.get('signal') == 'BULLISH':
                signal_score += 1.5
            elif momentum.get('signal') == 'BEARISH':
                signal_score -= 1.5
            
            # Pattern component (20% weight)
            if patterns.get('signal') == 'BULLISH':
                signal_score += 1
            elif patterns.get('signal') == 'BEARISH':
                signal_score -= 1
            
            # Volatility adjustment (10% weight)
            if volatility.get('level') == 'HIGH':
                signal_score *= 0.8  # Reduce signal strength in high volatility
            
            # Determine final signal
            signal = "NEUTRAL"
            if signal_score >= 2.5:
                signal = "STRONG_BUY"
                confidence = min(0.9, 0.5 + abs(signal_score) * 0.1)
            elif signal_score >= 1.5:
                signal = "BUY"
                confidence = min(0.8, 0.5 + abs(signal_score) * 0.1)
            elif signal_score <= -2.5:
                signal = "STRONG_SELL"
                confidence = min(0.9, 0.5 + abs(signal_score) * 0.1)
            elif signal_score <= -1.5:
                signal = "SELL"
                confidence = min(0.8, 0.5 + abs(signal_score) * 0.1)
            
            return {
                'signal': signal,
                'score': signal_score,
                'confidence': confidence,
                'components': {
                    'trend': trend.get('direction', 'NEUTRAL'),
                    'momentum': momentum.get('signal', 'NEUTRAL'),
                    'patterns': patterns.get('signal', 'NEUTRAL'),
                    'volatility': volatility.get('level', 'MEDIUM')
                }
            }
            
        except Exception as e:
            log_error("TechnicalAnalysis", "Error generating signals", e)
            return {'signal': 'NEUTRAL', 'score': 0, 'confidence': 0.5, 'components': {}}
    
    def calculate_risk_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate risk metrics for position sizing"""
        try:
            close = data['close'].values
            
            # Volatility measures
            returns = np.diff(close) / close[:-1]
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Value at Risk (95% confidence)
            var_95 = np.percentile(returns, 5)
            
            # Maximum drawdown
            peak = np.maximum.accumulate(close)
            drawdown = (close - peak) / peak
            max_drawdown = np.min(drawdown)
            
            return {
                'volatility': volatility,
                'var_95': var_95,
                'max_drawdown': max_drawdown,
                'current_drawdown': drawdown[-1]
            }
            
        except Exception as e:
            log_error("TechnicalAnalysis", "Error calculating risk metrics", e)
            return {'volatility': 0.1, 'var_95': -0.02, 'max_drawdown': -0.05, 'current_drawdown': 0}
