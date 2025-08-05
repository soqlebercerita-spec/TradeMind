"""
Technical Analysis module for AuraTrade Bot
Manual calculation of all technical indicators without TA-Lib
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from utils.logger import Logger

class TechnicalAnalysis:
    """Technical analysis indicators calculated manually"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        
        # Default periods for indicators
        self.default_periods = {
            "sma": [20, 50, 100, 200],
            "ema": [12, 26, 50],
            "wma": [21],
            "rsi": 14,
            "stoch_k": 14,
            "stoch_d": 3,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "atr": 14,
            "bb_period": 20,
            "bb_deviation": 2.0,
            "adx": 14
        }
    
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive technical analysis"""
        try:
            if data is None or len(data) < 50:
                return {}
            
            analysis_results = {}
            
            # Moving Averages
            analysis_results["sma"] = self.calculate_sma_analysis(data)
            analysis_results["ema"] = self.calculate_ema_analysis(data)
            analysis_results["wma"] = self.calculate_wma_analysis(data)
            
            # Oscillators
            analysis_results["rsi"] = self.calculate_rsi(data)
            analysis_results["stochastic"] = self.calculate_stochastic(data)
            analysis_results["macd"] = self.calculate_macd(data)
            
            # Volatility Indicators
            analysis_results["atr"] = self.calculate_atr(data)
            analysis_results["bollinger_bands"] = self.calculate_bollinger_bands(data)
            
            # Trend Indicators
            analysis_results["adx"] = self.calculate_adx(data)
            
            # Volume Analysis
            if "volume" in data.columns:
                analysis_results["volume_analysis"] = self.calculate_volume_analysis(data)
            
            # Price Action
            analysis_results["price_action"] = self.calculate_price_action(data)
            
            # Support and Resistance
            analysis_results["support_resistance"] = self.calculate_support_resistance(data)
            
            self.logger.debug(f"Technical analysis completed with {len(analysis_results)} indicators")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis: {e}")
            return {}
    
    def calculate_sma_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Simple Moving Average analysis"""
        try:
            close_prices = data["close"].values
            sma_results = {"values": {}, "signals": {}, "trend": "neutral"}
            
            for period in self.default_periods["sma"]:
                if len(close_prices) >= period:
                    sma_values = self.calculate_sma(close_prices, period)
                    sma_results["values"][f"sma_{period}"] = sma_values
                    
                    # Generate signals
                    current_price = close_prices[-1]
                    current_sma = sma_values[-1] if len(sma_values) > 0 else 0
                    
                    if current_price > current_sma:
                        sma_results["signals"][f"sma_{period}"] = "bullish"
                    elif current_price < current_sma:
                        sma_results["signals"][f"sma_{period}"] = "bearish"
                    else:
                        sma_results["signals"][f"sma_{period}"] = "neutral"
            
            # Determine overall trend
            bullish_count = sum(1 for signal in sma_results["signals"].values() if signal == "bullish")
            bearish_count = sum(1 for signal in sma_results["signals"].values() if signal == "bearish")
            
            if bullish_count > bearish_count:
                sma_results["trend"] = "bullish"
            elif bearish_count > bullish_count:
                sma_results["trend"] = "bearish"
            
            return sma_results
            
        except Exception as e:
            self.logger.error(f"Error calculating SMA analysis: {e}")
            return {"values": {}, "signals": {}, "trend": "neutral"}
    
    def calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        try:
            if len(prices) < period:
                return np.array([])
            
            sma = np.convolve(prices, np.ones(period)/period, mode='valid')
            return sma
            
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {e}")
            return np.array([])
    
    def calculate_ema_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Exponential Moving Average analysis"""
        try:
            close_prices = data["close"].values
            ema_results = {"values": {}, "signals": {}, "trend": "neutral", "slope": 0.0}
            
            for period in self.default_periods["ema"]:
                if len(close_prices) >= period:
                    ema_values = self.calculate_ema(close_prices, period)
                    ema_results["values"][f"ema_{period}"] = ema_values
                    
                    # Generate signals
                    current_price = close_prices[-1]
                    current_ema = ema_values[-1] if len(ema_values) > 0 else 0
                    
                    if current_price > current_ema:
                        ema_results["signals"][f"ema_{period}"] = "bullish"
                    elif current_price < current_ema:
                        ema_results["signals"][f"ema_{period}"] = "bearish"
                    else:
                        ema_results["signals"][f"ema_{period}"] = "neutral"
            
            # Calculate EMA slope (trend strength)
            if "ema_12" in ema_results["values"] and len(ema_results["values"]["ema_12"]) >= 5:
                ema_12 = ema_results["values"]["ema_12"]
                slope = (ema_12[-1] - ema_12[-5]) / ema_12[-5] if ema_12[-5] != 0 else 0
                ema_results["slope"] = slope
            
            # Determine overall trend
            bullish_count = sum(1 for signal in ema_results["signals"].values() if signal == "bullish")
            bearish_count = sum(1 for signal in ema_results["signals"].values() if signal == "bearish")
            
            if bullish_count > bearish_count:
                ema_results["trend"] = "bullish"
            elif bearish_count > bullish_count:
                ema_results["trend"] = "bearish"
            
            return ema_results
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA analysis: {e}")
            return {"values": {}, "signals": {}, "trend": "neutral", "slope": 0.0}
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return np.array([])
            
            alpha = 2.0 / (period + 1.0)
            ema = np.zeros(len(prices))
            ema[0] = prices[0]
            
            for i in range(1, len(prices)):
                ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
            
            return ema
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return np.array([])
    
    def calculate_wma_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Weighted Moving Average analysis"""
        try:
            close_prices = data["close"].values
            wma_results = {"values": {}, "signals": {}, "trend": "neutral"}
            
            for period in self.default_periods["wma"]:
                if len(close_prices) >= period:
                    wma_values = self.calculate_wma(close_prices, period)
                    wma_results["values"][f"wma_{period}"] = wma_values
                    
                    # Generate signals
                    current_price = close_prices[-1]
                    current_wma = wma_values[-1] if len(wma_values) > 0 else 0
                    
                    if current_price > current_wma:
                        wma_results["signals"][f"wma_{period}"] = "bullish"
                    elif current_price < current_wma:
                        wma_results["signals"][f"wma_{period}"] = "bearish"
                    else:
                        wma_results["signals"][f"wma_{period}"] = "neutral"
            
            return wma_results
            
        except Exception as e:
            self.logger.error(f"Error calculating WMA analysis: {e}")
            return {"values": {}, "signals": {}, "trend": "neutral"}
    
    def calculate_wma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Weighted Moving Average"""
        try:
            if len(prices) < period:
                return np.array([])
            
            weights = np.arange(1, period + 1)
            wma = np.zeros(len(prices) - period + 1)
            
            for i in range(len(wma)):
                wma[i] = np.dot(prices[i:i+period], weights) / weights.sum()
            
            return wma
            
        except Exception as e:
            self.logger.error(f"Error calculating WMA: {e}")
            return np.array([])
    
    def calculate_rsi(self, data: pd.DataFrame, period: Optional[int] = None) -> Dict[str, Any]:
        """Calculate Relative Strength Index"""
        try:
            if period is None:
                period = self.default_periods["rsi"]
            
            close_prices = data["close"].values
            
            if len(close_prices) < period + 1:
                return {"value": 50, "signal": "neutral", "trend": "neutral"}
            
            # Calculate price changes
            deltas = np.diff(close_prices)
            
            # Separate gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gains and losses
            avg_gains = np.zeros(len(gains))
            avg_losses = np.zeros(len(losses))
            
            # Initial averages
            avg_gains[period-1] = np.mean(gains[:period])
            avg_losses[period-1] = np.mean(losses[:period])
            
            # Smoothed averages
            for i in range(period, len(gains)):
                avg_gains[i] = (avg_gains[i-1] * (period-1) + gains[i]) / period
                avg_losses[i] = (avg_losses[i-1] * (period-1) + losses[i]) / period
            
            # Calculate RS and RSI
            rs = np.divide(avg_gains, avg_losses, out=np.zeros_like(avg_gains), where=avg_losses!=0)
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi[-1] if len(rsi) > 0 else 50
            
            # Generate signals
            if current_rsi > 70:
                signal = "overbought"
                trend = "bearish"
            elif current_rsi < 30:
                signal = "oversold"
                trend = "bullish"
            elif current_rsi > 50:
                signal = "bullish"
                trend = "bullish"
            else:
                signal = "bearish"
                trend = "bearish"
            
            return {
                "value": current_rsi,
                "values": rsi,
                "signal": signal,
                "trend": trend,
                "overbought": current_rsi > 70,
                "oversold": current_rsi < 30
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return {"value": 50, "signal": "neutral", "trend": "neutral"}
    
    def calculate_stochastic(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Stochastic Oscillator"""
        try:
            k_period = self.default_periods["stoch_k"]
            d_period = self.default_periods["stoch_d"]
            
            if len(data) < k_period:
                return {"k": 50, "d": 50, "signal": "neutral"}
            
            high_prices = data["high"].values
            low_prices = data["low"].values
            close_prices = data["close"].values
            
            # Calculate %K
            k_values = np.zeros(len(close_prices))
            
            for i in range(k_period-1, len(close_prices)):
                highest_high = np.max(high_prices[i-k_period+1:i+1])
                lowest_low = np.min(low_prices[i-k_period+1:i+1])
                
                if highest_high != lowest_low:
                    k_values[i] = ((close_prices[i] - lowest_low) / (highest_high - lowest_low)) * 100
                else:
                    k_values[i] = 50
            
            # Calculate %D (moving average of %K)
            d_values = np.zeros(len(k_values))
            for i in range(d_period-1, len(k_values)):
                d_values[i] = np.mean(k_values[i-d_period+1:i+1])
            
            current_k = k_values[-1]
            current_d = d_values[-1]
            
            # Generate signals
            if current_k > 80 and current_d > 80:
                signal = "overbought"
            elif current_k < 20 and current_d < 20:
                signal = "oversold"
            elif current_k > current_d:
                signal = "bullish"
            elif current_k < current_d:
                signal = "bearish"
            else:
                signal = "neutral"
            
            return {
                "k": current_k,
                "d": current_d,
                "k_values": k_values,
                "d_values": d_values,
                "signal": signal,
                "overbought": current_k > 80 and current_d > 80,
                "oversold": current_k < 20 and current_d < 20
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic: {e}")
            return {"k": 50, "d": 50, "signal": "neutral"}
    
    def calculate_macd(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            fast_period = self.default_periods["macd_fast"]
            slow_period = self.default_periods["macd_slow"]
            signal_period = self.default_periods["macd_signal"]
            
            close_prices = data["close"].values
            
            if len(close_prices) < slow_period:
                return {"macd": 0, "signal": 0, "histogram": 0, "trend": "neutral"}
            
            # Calculate EMAs
            ema_fast = self.calculate_ema(close_prices, fast_period)
            ema_slow = self.calculate_ema(close_prices, slow_period)
            
            # Align arrays
            min_length = min(len(ema_fast), len(ema_slow))
            ema_fast = ema_fast[-min_length:]
            ema_slow = ema_slow[-min_length:]
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate Signal line
            signal_line = self.calculate_ema(macd_line, signal_period)
            
            # Align MACD and Signal arrays
            min_length = min(len(macd_line), len(signal_line))
            macd_line = macd_line[-min_length:]
            signal_line = signal_line[-min_length:]
            
            # Calculate Histogram
            histogram = macd_line - signal_line
            
            current_macd = macd_line[-1] if len(macd_line) > 0 else 0
            current_signal = signal_line[-1] if len(signal_line) > 0 else 0
            current_histogram = histogram[-1] if len(histogram) > 0 else 0
            
            # Generate signals
            if current_macd > current_signal and current_macd > 0:
                trend = "bullish"
            elif current_macd < current_signal and current_macd < 0:
                trend = "bearish"
            else:
                trend = "neutral"
            
            # Check for crossovers
            crossover = "none"
            if len(histogram) >= 2:
                if histogram[-2] < 0 and histogram[-1] > 0:
                    crossover = "bullish"
                elif histogram[-2] > 0 and histogram[-1] < 0:
                    crossover = "bearish"
            
            return {
                "macd": current_macd,
                "signal": current_signal,
                "histogram": current_histogram,
                "macd_values": macd_line,
                "signal_values": signal_line,
                "histogram_values": histogram,
                "trend": trend,
                "crossover": crossover
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return {"macd": 0, "signal": 0, "histogram": 0, "trend": "neutral"}
    
    def calculate_atr(self, data: pd.DataFrame, period: Optional[int] = None) -> Dict[str, Any]:
        """Calculate Average True Range"""
        try:
            if period is None:
                period = self.default_periods["atr"]
            
            if len(data) < period + 1:
                return {"value": 0, "trend": "neutral"}
            
            high_prices = data["high"].values
            low_prices = data["low"].values
            close_prices = data["close"].values
            
            # Calculate True Range
            tr_values = np.zeros(len(high_prices))
            
            for i in range(1, len(high_prices)):
                tr1 = high_prices[i] - low_prices[i]
                tr2 = abs(high_prices[i] - close_prices[i-1])
                tr3 = abs(low_prices[i] - close_prices[i-1])
                tr_values[i] = max(tr1, tr2, tr3)
            
            # Calculate ATR using smoothed moving average
            atr_values = np.zeros(len(tr_values))
            atr_values[period] = np.mean(tr_values[1:period+1])
            
            for i in range(period+1, len(tr_values)):
                atr_values[i] = (atr_values[i-1] * (period-1) + tr_values[i]) / period
            
            current_atr = atr_values[-1]
            
            # Determine trend
            if len(atr_values) >= 10:
                recent_atr = np.mean(atr_values[-5:])
                previous_atr = np.mean(atr_values[-10:-5])
                
                if recent_atr > previous_atr * 1.1:
                    trend = "expanding"
                elif recent_atr < previous_atr * 0.9:
                    trend = "contracting"
                else:
                    trend = "stable"
            else:
                trend = "neutral"
            
            return {
                "value": current_atr,
                "values": atr_values,
                "trend": trend,
                "tr_values": tr_values
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return {"value": 0, "trend": "neutral"}
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Bollinger Bands"""
        try:
            period = self.default_periods["bb_period"]
            std_dev = self.default_periods["bb_deviation"]
            
            close_prices = data["close"].values
            
            if len(close_prices) < period:
                return {"upper": 0, "middle": 0, "lower": 0, "position": 0.5}
            
            # Calculate middle line (SMA)
            middle_band = self.calculate_sma(close_prices, period)
            
            # Calculate standard deviation
            bb_upper = np.zeros(len(middle_band))
            bb_lower = np.zeros(len(middle_band))
            
            for i in range(len(middle_band)):
                data_slice = close_prices[i:i+period]
                std = np.std(data_slice)
                bb_upper[i] = middle_band[i] + (std * std_dev)
                bb_lower[i] = middle_band[i] - (std * std_dev)
            
            current_price = close_prices[-1]
            current_upper = bb_upper[-1] if len(bb_upper) > 0 else current_price
            current_middle = middle_band[-1] if len(middle_band) > 0 else current_price
            current_lower = bb_lower[-1] if len(bb_lower) > 0 else current_price
            
            # Calculate position within bands (0 = lower band, 1 = upper band)
            if current_upper != current_lower:
                position = (current_price - current_lower) / (current_upper - current_lower)
            else:
                position = 0.5
            
            position = max(0, min(1, position))  # Clamp between 0 and 1
            
            # Calculate band width
            band_width = (current_upper - current_lower) / current_middle if current_middle != 0 else 0
            
            # Determine squeeze condition
            squeeze = band_width < 0.1  # Arbitrary threshold for squeeze
            
            return {
                "upper": current_upper,
                "middle": current_middle,
                "lower": current_lower,
                "upper_values": bb_upper,
                "middle_values": middle_band,
                "lower_values": bb_lower,
                "position": position,
                "width": band_width,
                "squeeze": squeeze
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return {"upper": 0, "middle": 0, "lower": 0, "position": 0.5}
    
    def calculate_adx(self, data: pd.DataFrame, period: Optional[int] = None) -> Dict[str, Any]:
        """Calculate Average Directional Index"""
        try:
            if period is None:
                period = self.default_periods["adx"]
            
            if len(data) < period + 1:
                return {"adx": 0, "di_plus": 0, "di_minus": 0, "trend_strength": "weak"}
            
            high_prices = data["high"].values
            low_prices = data["low"].values
            close_prices = data["close"].values
            
            # Calculate True Range and Directional Movement
            tr_values = np.zeros(len(high_prices))
            dm_plus = np.zeros(len(high_prices))
            dm_minus = np.zeros(len(high_prices))
            
            for i in range(1, len(high_prices)):
                # True Range
                tr1 = high_prices[i] - low_prices[i]
                tr2 = abs(high_prices[i] - close_prices[i-1])
                tr3 = abs(low_prices[i] - close_prices[i-1])
                tr_values[i] = max(tr1, tr2, tr3)
                
                # Directional Movement
                high_diff = high_prices[i] - high_prices[i-1]
                low_diff = low_prices[i-1] - low_prices[i]
                
                if high_diff > low_diff and high_diff > 0:
                    dm_plus[i] = high_diff
                else:
                    dm_plus[i] = 0
                
                if low_diff > high_diff and low_diff > 0:
                    dm_minus[i] = low_diff
                else:
                    dm_minus[i] = 0
            
            # Calculate smoothed True Range and DM
            tr_smooth = np.zeros(len(tr_values))
            dm_plus_smooth = np.zeros(len(dm_plus))
            dm_minus_smooth = np.zeros(len(dm_minus))
            
            # Initial values
            tr_smooth[period] = np.sum(tr_values[1:period+1])
            dm_plus_smooth[period] = np.sum(dm_plus[1:period+1])
            dm_minus_smooth[period] = np.sum(dm_minus[1:period+1])
            
            # Smoothed values
            for i in range(period+1, len(tr_values)):
                tr_smooth[i] = tr_smooth[i-1] - (tr_smooth[i-1]/period) + tr_values[i]
                dm_plus_smooth[i] = dm_plus_smooth[i-1] - (dm_plus_smooth[i-1]/period) + dm_plus[i]
                dm_minus_smooth[i] = dm_minus_smooth[i-1] - (dm_minus_smooth[i-1]/period) + dm_minus[i]
            
            # Calculate DI+ and DI-
            di_plus = np.divide(dm_plus_smooth * 100, tr_smooth, out=np.zeros_like(dm_plus_smooth), where=tr_smooth!=0)
            di_minus = np.divide(dm_minus_smooth * 100, tr_smooth, out=np.zeros_like(dm_minus_smooth), where=tr_smooth!=0)
            
            # Calculate DX
            dx = np.zeros(len(di_plus))
            for i in range(len(di_plus)):
                di_sum = di_plus[i] + di_minus[i]
                if di_sum != 0:
                    dx[i] = abs(di_plus[i] - di_minus[i]) / di_sum * 100
            
            # Calculate ADX
            adx = np.zeros(len(dx))
            adx[period*2] = np.mean(dx[period:period*2])
            
            for i in range(period*2+1, len(dx)):
                adx[i] = (adx[i-1] * (period-1) + dx[i]) / period
            
            current_adx = adx[-1]
            current_di_plus = di_plus[-1]
            current_di_minus = di_minus[-1]
            
            # Determine trend strength
            if current_adx > 50:
                trend_strength = "very_strong"
            elif current_adx > 25:
                trend_strength = "strong"
            elif current_adx > 20:
                trend_strength = "moderate"
            else:
                trend_strength = "weak"
            
            return {
                "adx": current_adx,
                "di_plus": current_di_plus,
                "di_minus": current_di_minus,
                "adx_values": adx,
                "di_plus_values": di_plus,
                "di_minus_values": di_minus,
                "trend_strength": trend_strength
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return {"adx": 0, "di_plus": 0, "di_minus": 0, "trend_strength": "weak"}
    
    def calculate_volume_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume-based indicators"""
        try:
            if "volume" not in data.columns:
                return {"on_balance_volume": 0, "volume_trend": "neutral"}
            
            close_prices = data["close"].values
            volume = data["volume"].values
            
            # On-Balance Volume
            obv = np.zeros(len(volume))
            obv[0] = volume[0]
            
            for i in range(1, len(volume)):
                if close_prices[i] > close_prices[i-1]:
                    obv[i] = obv[i-1] + volume[i]
                elif close_prices[i] < close_prices[i-1]:
                    obv[i] = obv[i-1] - volume[i]
                else:
                    obv[i] = obv[i-1]
            
            # Volume trend
            if len(volume) >= 20:
                recent_volume = np.mean(volume[-10:])
                previous_volume = np.mean(volume[-20:-10])
                
                if recent_volume > previous_volume * 1.2:
                    volume_trend = "increasing"
                elif recent_volume < previous_volume * 0.8:
                    volume_trend = "decreasing"
                else:
                    volume_trend = "stable"
            else:
                volume_trend = "neutral"
            
            # Volume-Price Trend
            vpt = np.zeros(len(volume))
            for i in range(1, len(volume)):
                price_change = (close_prices[i] - close_prices[i-1]) / close_prices[i-1]
                vpt[i] = vpt[i-1] + (volume[i] * price_change)
            
            return {
                "on_balance_volume": obv[-1],
                "obv_values": obv,
                "volume_trend": volume_trend,
                "volume_price_trend": vpt[-1],
                "vpt_values": vpt,
                "average_volume": np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating volume analysis: {e}")
            return {"on_balance_volume": 0, "volume_trend": "neutral"}
    
    def calculate_price_action(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate price action indicators"""
        try:
            if len(data) < 10:
                return {"momentum": 0, "volatility": 0, "trend": "neutral"}
            
            close_prices = data["close"].values
            high_prices = data["high"].values
            low_prices = data["low"].values
            
            # Price momentum
            if len(close_prices) >= 10:
                momentum = (close_prices[-1] - close_prices[-10]) / close_prices[-10]
            else:
                momentum = 0
            
            # Volatility (standard deviation of returns)
            if len(close_prices) >= 20:
                returns = np.diff(close_prices[-20:]) / close_prices[-21:-1]
                volatility = np.std(returns)
            else:
                returns = np.diff(close_prices) / close_prices[:-1]
                volatility = np.std(returns) if len(returns) > 0 else 0
            
            # Price range analysis
            recent_ranges = []
            for i in range(max(1, len(data)-10), len(data)):
                range_pct = (high_prices[i] - low_prices[i]) / close_prices[i]
                recent_ranges.append(range_pct)
            
            avg_range = np.mean(recent_ranges) if recent_ranges else 0
            
            # Trend determination
            if momentum > 0.01:
                trend = "bullish"
            elif momentum < -0.01:
                trend = "bearish"
            else:
                trend = "neutral"
            
            return {
                "momentum": momentum,
                "volatility": volatility,
                "trend": trend,
                "average_range": avg_range,
                "current_range": recent_ranges[-1] if recent_ranges else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating price action: {e}")
            return {"momentum": 0, "volatility": 0, "trend": "neutral"}
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate support and resistance levels"""
        try:
            if len(data) < 20:
                return {"support_levels": [], "resistance_levels": [], "current_level": "neutral"}
            
            high_prices = data["high"].values
            low_prices = data["low"].values
            close_prices = data["close"].values
            
            # Find pivot points
            support_levels = []
            resistance_levels = []
            
            # Look for local minima (support) and maxima (resistance)
            window = 5
            for i in range(window, len(data) - window):
                # Check for local minimum (support)
                is_support = True
                for j in range(i - window, i + window + 1):
                    if j != i and low_prices[j] < low_prices[i]:
                        is_support = False
                        break
                
                if is_support:
                    support_levels.append(low_prices[i])
                
                # Check for local maximum (resistance)
                is_resistance = True
                for j in range(i - window, i + window + 1):
                    if j != i and high_prices[j] > high_prices[i]:
                        is_resistance = False
                        break
                
                if is_resistance:
                    resistance_levels.append(high_prices[i])
            
            # Remove duplicates and sort
            support_levels = sorted(list(set(support_levels)))
            resistance_levels = sorted(list(set(resistance_levels)))
            
            # Find nearest levels to current price
            current_price = close_prices[-1]
            
            nearest_support = 0
            nearest_resistance = 0
            
            for level in support_levels:
                if level < current_price:
                    nearest_support = max(nearest_support, level)
            
            for level in resistance_levels:
                if level > current_price:
                    if nearest_resistance == 0:
                        nearest_resistance = level
                    else:
                        nearest_resistance = min(nearest_resistance, level)
            
            # Determine current level position
            if nearest_support > 0 and nearest_resistance > 0:
                support_distance = current_price - nearest_support
                resistance_distance = nearest_resistance - current_price
                
                if support_distance < resistance_distance:
                    current_level = "near_support"
                else:
                    current_level = "near_resistance"
            elif nearest_support > 0:
                current_level = "above_support"
            elif nearest_resistance > 0:
                current_level = "below_resistance"
            else:
                current_level = "neutral"
            
            return {
                "support_levels": support_levels[-5:],  # Last 5 support levels
                "resistance_levels": resistance_levels[:5],  # Next 5 resistance levels
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "current_level": current_level
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance: {e}")
            return {"support_levels": [], "resistance_levels": [], "current_level": "neutral"}
