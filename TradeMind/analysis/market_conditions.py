"""
Market Conditions Analysis module for AuraTrade Bot
Analyzes current market conditions including volatility, trend strength, and trading sessions
"""

import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class MarketConditions:
    """Market conditions analyzer"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        
        # Market session times (UTC)
        self.market_sessions = {
            "sydney": {"start": 22, "end": 7},
            "tokyo": {"start": 0, "end": 9}, 
            "london": {"start": 8, "end": 17},
            "new_york": {"start": 13, "end": 22}
        }
        
        # Volatility thresholds
        self.volatility_thresholds = {
            "very_low": 0.3,
            "low": 0.6,
            "normal": 1.0,
            "high": 1.5,
            "very_high": 2.5
        }
        
        # Trend strength thresholds
        self.trend_thresholds = {
            "very_weak": 0.2,
            "weak": 0.4,
            "moderate": 0.6,
            "strong": 0.8,
            "very_strong": 1.0
        }
        
        # Market condition history
        self.condition_history = {}
        self.current_volatility = {}
        
    def analyze(self, data: pd.DataFrame, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive market condition analysis"""
        try:
            if data is None or len(data) < 20:
                return self._get_default_conditions()
            
            symbol = tick_data.get("symbol", "UNKNOWN")
            
            # Analyze different aspects of market conditions
            volatility_analysis = self._analyze_volatility(data, tick_data)
            trend_analysis = self._analyze_trend_strength(data)
            session_analysis = self._analyze_trading_session()
            liquidity_analysis = self._analyze_liquidity(data, tick_data)
            momentum_analysis = self._analyze_momentum(data)
            range_analysis = self._analyze_price_range(data)
            correlation_analysis = self._analyze_market_correlation(symbol)
            
            # Combine all analyses
            market_condition = {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "overall_condition": self._determine_overall_condition(
                    volatility_analysis, trend_analysis, session_analysis, 
                    liquidity_analysis, momentum_analysis
                ),
                "volatility": volatility_analysis,
                "trend": trend_analysis,
                "session": session_analysis,
                "liquidity": liquidity_analysis,
                "momentum": momentum_analysis,
                "range": range_analysis,
                "correlation": correlation_analysis,
                "trading_recommendation": self._get_trading_recommendation(
                    volatility_analysis, trend_analysis, session_analysis
                )
            }
            
            # Store in history
            self._store_condition_history(symbol, market_condition)
            
            return market_condition
            
        except Exception as e:
            self.logger.error(f"Error analyzing market conditions: {e}")
            return self._get_default_conditions()
    
    def _analyze_volatility(self, data: pd.DataFrame, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market volatility"""
        try:
            close_prices = data["close"].values
            high_prices = data["high"].values
            low_prices = data["low"].values
            
            # Calculate different volatility measures
            
            # 1. True Range based volatility
            tr_volatility = self._calculate_tr_volatility(data)
            
            # 2. Close-to-close volatility
            if len(close_prices) > 1:
                returns = np.diff(close_prices) / close_prices[:-1]
                close_volatility = np.std(returns) * np.sqrt(1440)  # Annualized for minutes
            else:
                close_volatility = 0
            
            # 3. High-Low volatility
            if len(data) > 1:
                hl_volatility = np.mean((high_prices - low_prices) / close_prices)
            else:
                hl_volatility = 0
                
            # 4. Intraday volatility
            intraday_volatility = self._calculate_intraday_volatility(data)
            
            # 5. Current spread as volatility indicator
            current_spread = tick_data.get("spread", 0)
            symbol_info = tick_data.get("symbol", "")
            spread_volatility = self._normalize_spread_volatility(current_spread, symbol_info)
            
            # Combine volatility measures
            combined_volatility = (
                tr_volatility * 0.3 +
                close_volatility * 0.25 +
                hl_volatility * 0.2 +
                intraday_volatility * 0.15 +
                spread_volatility * 0.1
            )
            
            # Determine volatility level
            volatility_level = self._classify_volatility(combined_volatility)
            
            # Calculate volatility trend
            volatility_trend = self._calculate_volatility_trend(data)
            
            return {
                "current": combined_volatility,
                "level": volatility_level,
                "trend": volatility_trend,
                "components": {
                    "true_range": tr_volatility,
                    "close_to_close": close_volatility,
                    "high_low": hl_volatility,
                    "intraday": intraday_volatility,
                    "spread": spread_volatility
                },
                "percentile": self._calculate_volatility_percentile(combined_volatility, data),
                "expansion_contraction": self._detect_volatility_regime(data)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing volatility: {e}")
            return {"current": 1.0, "level": "normal", "trend": "stable"}
    
    def _calculate_tr_volatility(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate True Range based volatility"""
        try:
            if len(data) < period + 1:
                return 0.0
            
            high_prices = data["high"].values
            low_prices = data["low"].values
            close_prices = data["close"].values
            
            # Calculate True Range
            tr_values = []
            for i in range(1, len(data)):
                tr1 = high_prices[i] - low_prices[i]
                tr2 = abs(high_prices[i] - close_prices[i-1])
                tr3 = abs(low_prices[i] - close_prices[i-1])
                tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
            
            # Calculate ATR
            if len(tr_values) >= period:
                atr = np.mean(tr_values[-period:])
                # Normalize by current price
                current_price = close_prices[-1]
                normalized_atr = atr / current_price if current_price > 0 else 0
                return normalized_atr
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating TR volatility: {e}")
            return 1.0
    
    def _calculate_intraday_volatility(self, data: pd.DataFrame) -> float:
        """Calculate intraday volatility"""
        try:
            if len(data) < 10:
                return 0.0
            
            # Calculate range as percentage of close
            ranges = []
            for i in range(len(data)):
                high = data.iloc[i]["high"]
                low = data.iloc[i]["low"]
                close = data.iloc[i]["close"]
                if close > 0:
                    range_pct = (high - low) / close
                    ranges.append(range_pct)
            
            if ranges:
                return np.mean(ranges[-10:])  # Average of last 10 periods
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating intraday volatility: {e}")
            return 0.0
    
    def _normalize_spread_volatility(self, spread: float, symbol: str) -> float:
        """Normalize spread volatility by symbol"""
        try:
            # Symbol-specific spread normalization
            spread_norms = {
                "EURUSD": 0.0002,
                "GBPUSD": 0.0003,
                "USDJPY": 0.003,
                "XAUUSD": 0.5,
                "BTCUSD": 50.0
            }
            
            norm = spread_norms.get(symbol, 0.0005)
            return spread / norm if norm > 0 else 1.0
            
        except Exception as e:
            self.logger.error(f"Error normalizing spread volatility: {e}")
            return 1.0
    
    def _classify_volatility(self, volatility: float) -> str:
        """Classify volatility level"""
        try:
            if volatility <= self.volatility_thresholds["very_low"]:
                return "very_low"
            elif volatility <= self.volatility_thresholds["low"]:
                return "low"
            elif volatility <= self.volatility_thresholds["normal"]:
                return "normal"
            elif volatility <= self.volatility_thresholds["high"]:
                return "high"
            else:
                return "very_high"
                
        except Exception as e:
            self.logger.error(f"Error classifying volatility: {e}")
            return "normal"
    
    def _calculate_volatility_trend(self, data: pd.DataFrame) -> str:
        """Calculate volatility trend"""
        try:
            if len(data) < 20:
                return "stable"
            
            # Calculate rolling volatility
            window = 10
            recent_vol = []
            previous_vol = []
            
            for i in range(len(data) - window, len(data)):
                if i >= window:
                    segment = data.iloc[i-window:i]
                    vol = self._calculate_segment_volatility(segment)
                    recent_vol.append(vol)
            
            for i in range(len(data) - 2*window, len(data) - window):
                if i >= window:
                    segment = data.iloc[i-window:i]
                    vol = self._calculate_segment_volatility(segment)
                    previous_vol.append(vol)
            
            if recent_vol and previous_vol:
                recent_avg = np.mean(recent_vol)
                previous_avg = np.mean(previous_vol)
                
                change = (recent_avg - previous_avg) / previous_avg if previous_avg > 0 else 0
                
                if change > 0.2:
                    return "expanding"
                elif change < -0.2:
                    return "contracting"
                else:
                    return "stable"
            
            return "stable"
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility trend: {e}")
            return "stable"
    
    def _calculate_segment_volatility(self, segment: pd.DataFrame) -> float:
        """Calculate volatility for a data segment"""
        try:
            if len(segment) < 2:
                return 0.0
            
            close_prices = segment["close"].values
            returns = np.diff(close_prices) / close_prices[:-1]
            return np.std(returns)
            
        except Exception as e:
            return 0.0
    
    def _analyze_trend_strength(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend strength"""
        try:
            if len(data) < 20:
                return {"strength": 0.0, "direction": "neutral", "quality": "weak"}
            
            close_prices = data["close"].values
            
            # 1. Linear regression trend
            x = np.arange(len(close_prices))
            slope, intercept = np.polyfit(x, close_prices, 1)
            
            # Normalize slope
            price_range = np.max(close_prices) - np.min(close_prices)
            normalized_slope = slope / (price_range / len(close_prices)) if price_range > 0 else 0
            
            # 2. Moving average trend
            ma_short = np.mean(close_prices[-5:])
            ma_long = np.mean(close_prices[-20:])
            ma_trend = (ma_short - ma_long) / ma_long if ma_long > 0 else 0
            
            # 3. Directional movement
            up_moves = 0
            down_moves = 0
            for i in range(1, len(close_prices)):
                if close_prices[i] > close_prices[i-1]:
                    up_moves += 1
                elif close_prices[i] < close_prices[i-1]:
                    down_moves += 1
            
            total_moves = up_moves + down_moves
            directional_strength = abs(up_moves - down_moves) / total_moves if total_moves > 0 else 0
            
            # 4. Trend consistency
            trend_consistency = self._calculate_trend_consistency(close_prices)
            
            # Combine trend measures
            combined_strength = abs(
                normalized_slope * 0.3 +
                ma_trend * 0.3 +
                directional_strength * 0.2 +
                trend_consistency * 0.2
            )
            
            # Determine direction
            if normalized_slope > 0 and ma_trend > 0:
                direction = "bullish"
            elif normalized_slope < 0 and ma_trend < 0:
                direction = "bearish"
            else:
                direction = "neutral"
            
            # Classify strength
            strength_level = self._classify_trend_strength(combined_strength)
            
            return {
                "strength": combined_strength,
                "direction": direction,
                "quality": strength_level,
                "components": {
                    "linear_trend": normalized_slope,
                    "ma_trend": ma_trend,
                    "directional": directional_strength,
                    "consistency": trend_consistency
                },
                "slope": slope,
                "r_squared": self._calculate_trend_r_squared(close_prices)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend strength: {e}")
            return {"strength": 0.0, "direction": "neutral", "quality": "weak"}
    
    def _calculate_trend_consistency(self, prices: np.ndarray) -> float:
        """Calculate trend consistency"""
        try:
            if len(prices) < 10:
                return 0.0
            
            # Calculate how often price moves in the same direction as overall trend
            overall_trend = prices[-1] - prices[0]
            consistent_moves = 0
            total_moves = 0
            
            for i in range(1, len(prices)):
                move = prices[i] - prices[i-1]
                if overall_trend > 0 and move > 0:
                    consistent_moves += 1
                elif overall_trend < 0 and move < 0:
                    consistent_moves += 1
                total_moves += 1
            
            return consistent_moves / total_moves if total_moves > 0 else 0.5
            
        except Exception as e:
            return 0.5
    
    def _calculate_trend_r_squared(self, prices: np.ndarray) -> float:
        """Calculate R-squared for trend line fit"""
        try:
            if len(prices) < 3:
                return 0.0
            
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices, 1)
            
            # Calculate R-squared
            y_pred = slope * x + intercept
            ss_res = np.sum((prices - y_pred) ** 2)
            ss_tot = np.sum((prices - np.mean(prices)) ** 2)
            
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            return max(0, min(r_squared, 1))  # Clamp between 0 and 1
            
        except Exception as e:
            return 0.0
    
    def _classify_trend_strength(self, strength: float) -> str:
        """Classify trend strength"""
        try:
            if strength <= self.trend_thresholds["very_weak"]:
                return "very_weak"
            elif strength <= self.trend_thresholds["weak"]:
                return "weak"
            elif strength <= self.trend_thresholds["moderate"]:
                return "moderate"
            elif strength <= self.trend_thresholds["strong"]:
                return "strong"
            else:
                return "very_strong"
                
        except Exception as e:
            return "weak"
    
    def _analyze_trading_session(self) -> Dict[str, Any]:
        """Analyze current trading session"""
        try:
            current_hour = datetime.utcnow().hour
            current_day = datetime.utcnow().weekday()  # 0=Monday, 6=Sunday
            
            # Check if it's weekend
            is_weekend = current_day >= 5  # Saturday or Sunday
            
            # Determine active sessions
            active_sessions = []
            session_overlaps = []
            
            for session_name, times in self.market_sessions.items():
                start_hour = times["start"]
                end_hour = times["end"]
                
                # Handle sessions that cross midnight
                if start_hour > end_hour:
                    is_active = current_hour >= start_hour or current_hour < end_hour
                else:
                    is_active = start_hour <= current_hour < end_hour
                
                if is_active and not is_weekend:
                    active_sessions.append(session_name)
            
            # Check for session overlaps
            if len(active_sessions) > 1:
                session_overlaps = active_sessions
            
            # Determine liquidity level based on active sessions
            liquidity_level = self._determine_session_liquidity(active_sessions)
            
            # Calculate time until next major session
            next_session_info = self._calculate_next_session_time(current_hour)
            
            return {
                "current_sessions": active_sessions,
                "session_overlaps": session_overlaps,
                "liquidity_level": liquidity_level,
                "is_weekend": is_weekend,
                "next_session": next_session_info,
                "market_open": len(active_sessions) > 0 and not is_weekend,
                "peak_hours": len(session_overlaps) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trading session: {e}")
            return {"current_sessions": [], "liquidity_level": "low", "market_open": False}
    
    def _determine_session_liquidity(self, active_sessions: List[str]) -> str:
        """Determine liquidity level based on active sessions"""
        try:
            if not active_sessions:
                return "very_low"
            elif len(active_sessions) == 1:
                # Single session liquidity levels
                session = active_sessions[0]
                if session in ["london", "new_york"]:
                    return "high"
                elif session in ["tokyo"]:
                    return "medium"
                else:
                    return "low"
            else:
                # Multiple sessions = higher liquidity
                if "london" in active_sessions and "new_york" in active_sessions:
                    return "very_high"  # Best overlap
                elif any(major in active_sessions for major in ["london", "new_york"]):
                    return "high"
                else:
                    return "medium"
                    
        except Exception as e:
            return "medium"
    
    def _calculate_next_session_time(self, current_hour: int) -> Dict[str, Any]:
        """Calculate time until next major session"""
        try:
            major_sessions = ["tokyo", "london", "new_york"]
            next_session = None
            hours_until = 24
            
            for session_name in major_sessions:
                start_hour = self.market_sessions[session_name]["start"]
                
                if start_hour > current_hour:
                    hours_diff = start_hour - current_hour
                else:
                    hours_diff = 24 - current_hour + start_hour
                
                if hours_diff < hours_until:
                    hours_until = hours_diff
                    next_session = session_name
            
            return {
                "session": next_session,
                "hours_until": hours_until,
                "start_time": self.market_sessions[next_session]["start"] if next_session else None
            }
            
        except Exception as e:
            return {"session": None, "hours_until": 0}
    
    def _analyze_liquidity(self, data: pd.DataFrame, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market liquidity"""
        try:
            # 1. Spread analysis
            current_spread = tick_data.get("spread", 0)
            
            # 2. Volume analysis (if available)
            volume_analysis = self._analyze_volume_liquidity(data)
            
            # 3. Price impact analysis
            price_impact = self._calculate_price_impact(data)
            
            # 4. Bid-ask spread stability
            spread_stability = self._analyze_spread_stability(current_spread)
            
            # Combine liquidity measures
            liquidity_score = self._calculate_liquidity_score(
                current_spread, volume_analysis, price_impact, spread_stability
            )
            
            return {
                "score": liquidity_score,
                "level": self._classify_liquidity(liquidity_score),
                "current_spread": current_spread,
                "volume_analysis": volume_analysis,
                "price_impact": price_impact,
                "spread_stability": spread_stability
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing liquidity: {e}")
            return {"score": 0.5, "level": "medium"}
    
    def _analyze_volume_liquidity(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume-based liquidity"""
        try:
            if "volume" not in data.columns:
                return {"available": False, "trend": "unknown", "relative": 1.0}
            
            volume = data["volume"].values
            
            if len(volume) < 10:
                return {"available": True, "trend": "unknown", "relative": 1.0}
            
            # Calculate volume trend
            recent_volume = np.mean(volume[-5:])
            historical_volume = np.mean(volume[-20:-5]) if len(volume) >= 20 else np.mean(volume[:-5])
            
            volume_ratio = recent_volume / historical_volume if historical_volume > 0 else 1.0
            
            if volume_ratio > 1.2:
                trend = "increasing"
            elif volume_ratio < 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "available": True,
                "trend": trend,
                "relative": volume_ratio,
                "current": recent_volume,
                "average": historical_volume
            }
            
        except Exception as e:
            return {"available": False, "trend": "unknown", "relative": 1.0}
    
    def _calculate_price_impact(self, data: pd.DataFrame) -> float:
        """Calculate price impact measure"""
        try:
            if len(data) < 10:
                return 0.5
            
            # Calculate average price movement per period
            close_prices = data["close"].values
            price_changes = np.abs(np.diff(close_prices))
            avg_price_change = np.mean(price_changes[-10:])
            
            # Normalize by current price
            current_price = close_prices[-1]
            normalized_impact = avg_price_change / current_price if current_price > 0 else 0.001
            
            return min(normalized_impact * 1000, 1.0)  # Scale and cap at 1.0
            
        except Exception as e:
            return 0.5
    
    def _analyze_spread_stability(self, current_spread: float) -> Dict[str, Any]:
        """Analyze spread stability"""
        try:
            # This would ideally track spread over time
            # For now, classify based on current spread
            
            # Rough spread classifications by symbol type
            if current_spread < 0.0002:  # Very tight spread
                stability = "very_stable"
                score = 0.9
            elif current_spread < 0.0005:  # Normal spread
                stability = "stable"
                score = 0.7
            elif current_spread < 0.001:  # Wide spread
                stability = "moderate"
                score = 0.5
            else:  # Very wide spread
                stability = "unstable"
                score = 0.3
            
            return {
                "stability": stability,
                "score": score,
                "spread": current_spread
            }
            
        except Exception as e:
            return {"stability": "moderate", "score": 0.5}
    
    def _calculate_liquidity_score(self, spread: float, volume_analysis: Dict[str, Any], 
                                 price_impact: float, spread_stability: Dict[str, Any]) -> float:
        """Calculate overall liquidity score"""
        try:
            # Base score from spread (tighter = better)
            spread_score = max(0, 1 - spread * 10000)  # Rough normalization
            
            # Volume score
            volume_score = 0.5  # Default if no volume data
            if volume_analysis.get("available", False):
                volume_ratio = volume_analysis.get("relative", 1.0)
                volume_score = min(volume_ratio, 2.0) / 2.0  # Normalize
            
            # Price impact score (lower impact = better liquidity)
            impact_score = 1 - price_impact
            
            # Spread stability score
            stability_score = spread_stability.get("score", 0.5)
            
            # Weighted combination
            liquidity_score = (
                spread_score * 0.4 +
                volume_score * 0.3 +
                impact_score * 0.2 +
                stability_score * 0.1
            )
            
            return max(0, min(liquidity_score, 1.0))
            
        except Exception as e:
            return 0.5
    
    def _classify_liquidity(self, score: float) -> str:
        """Classify liquidity level"""
        try:
            if score > 0.8:
                return "very_high"
            elif score > 0.6:
                return "high"
            elif score > 0.4:
                return "medium"
            elif score > 0.2:
                return "low"
            else:
                return "very_low"
                
        except Exception as e:
            return "medium"
    
    def _analyze_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price momentum"""
        try:
            if len(data) < 10:
                return {"strength": 0.0, "direction": "neutral", "acceleration": 0.0}
            
            close_prices = data["close"].values
            
            # Short-term momentum (5 periods)
            short_momentum = (close_prices[-1] - close_prices[-5]) / close_prices[-5] if len(close_prices) >= 5 else 0
            
            # Medium-term momentum (10 periods)
            medium_momentum = (close_prices[-1] - close_prices[-10]) / close_prices[-10] if len(close_prices) >= 10 else 0
            
            # Long-term momentum (20 periods)
            long_momentum = (close_prices[-1] - close_prices[-20]) / close_prices[-20] if len(close_prices) >= 20 else 0
            
            # Calculate momentum strength
            momentum_strength = abs(short_momentum + medium_momentum + long_momentum) / 3
            
            # Determine direction
            avg_momentum = (short_momentum + medium_momentum + long_momentum) / 3
            if avg_momentum > 0.001:
                direction = "bullish"
            elif avg_momentum < -0.001:
                direction = "bearish"
            else:
                direction = "neutral"
            
            # Calculate acceleration (change in momentum)
            acceleration = self._calculate_momentum_acceleration(close_prices)
            
            return {
                "strength": momentum_strength,
                "direction": direction,
                "acceleration": acceleration,
                "components": {
                    "short_term": short_momentum,
                    "medium_term": medium_momentum,
                    "long_term": long_momentum
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing momentum: {e}")
            return {"strength": 0.0, "direction": "neutral", "acceleration": 0.0}
    
    def _calculate_momentum_acceleration(self, prices: np.ndarray) -> float:
        """Calculate momentum acceleration"""
        try:
            if len(prices) < 15:
                return 0.0
            
            # Calculate momentum at two different points
            recent_momentum = (prices[-1] - prices[-5]) / prices[-5]
            previous_momentum = (prices[-6] - prices[-10]) / prices[-10]
            
            # Acceleration is change in momentum
            acceleration = recent_momentum - previous_momentum
            
            return acceleration
            
        except Exception as e:
            return 0.0
    
    def _analyze_price_range(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price range characteristics"""
        try:
            if len(data) < 10:
                return {"expansion": False, "compression": False, "breakout_potential": 0.0}
            
            # Calculate recent range
            recent_highs = data["high"].values[-10:]
            recent_lows = data["low"].values[-10:]
            recent_range = np.max(recent_highs) - np.min(recent_lows)
            
            # Calculate historical range
            if len(data) >= 30:
                historical_highs = data["high"].values[-30:-10]
                historical_lows = data["low"].values[-30:-10]
                historical_range = np.max(historical_highs) - np.min(historical_lows)
            else:
                historical_range = recent_range
            
            # Range analysis
            range_ratio = recent_range / historical_range if historical_range > 0 else 1.0
            
            expansion = range_ratio > 1.2
            compression = range_ratio < 0.8
            
            # Breakout potential based on compression
            if compression:
                breakout_potential = min((1.2 - range_ratio) / 0.4, 1.0)
            else:
                breakout_potential = 0.0
            
            return {
                "expansion": expansion,
                "compression": compression,
                "breakout_potential": breakout_potential,
                "range_ratio": range_ratio,
                "recent_range": recent_range,
                "historical_range": historical_range
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing price range: {e}")
            return {"expansion": False, "compression": False, "breakout_potential": 0.0}
    
    def _analyze_market_correlation(self, symbol: str) -> Dict[str, Any]:
        """Analyze market correlation factors"""
        try:
            # This would ideally analyze correlation with other instruments
            # For now, return basic correlation info
            
            correlation_factors = {
                "XAUUSD": ["DXY", "US10Y", "VIX"],
                "BTCUSD": ["NASDAQ", "Risk_Sentiment"],
                "EURUSD": ["DXY", "EUR_Interest_Rates"],
                "GBPUSD": ["DXY", "GBP_Interest_Rates"],
                "USDJPY": ["US10Y", "Risk_Sentiment"]
            }
            
            factors = correlation_factors.get(symbol, ["DXY", "Risk_Sentiment"])
            
            return {
                "primary_factors": factors,
                "risk_on_off": self._determine_risk_sentiment(),
                "correlation_strength": 0.5  # Would calculate actual correlation
            }
            
        except Exception as e:
            return {"primary_factors": [], "risk_on_off": "neutral"}
    
    def _determine_risk_sentiment(self) -> str:
        """Determine overall market risk sentiment"""
        try:
            # This would analyze VIX, bond yields, etc.
            # For now, return neutral
            return "neutral"
            
        except Exception as e:
            return "neutral"
    
    def _determine_overall_condition(self, volatility: Dict[str, Any], trend: Dict[str, Any], 
                                   session: Dict[str, Any], liquidity: Dict[str, Any], 
                                   momentum: Dict[str, Any]) -> str:
        """Determine overall market condition"""
        try:
            # Score different aspects
            vol_score = self._score_volatility_condition(volatility)
            trend_score = self._score_trend_condition(trend)
            session_score = self._score_session_condition(session)
            liquidity_score = liquidity.get("score", 0.5)
            momentum_score = momentum.get("strength", 0.0)
            
            # Weighted overall score
            overall_score = (
                vol_score * 0.25 +
                trend_score * 0.25 +
                session_score * 0.2 +
                liquidity_score * 0.15 +
                momentum_score * 0.15
            )
            
            # Classify overall condition
            if overall_score > 0.8:
                return "excellent"
            elif overall_score > 0.6:
                return "good"
            elif overall_score > 0.4:
                return "moderate"
            elif overall_score > 0.2:
                return "poor"
            else:
                return "very_poor"
                
        except Exception as e:
            return "moderate"
    
    def _score_volatility_condition(self, volatility: Dict[str, Any]) -> float:
        """Score volatility condition for trading"""
        try:
            level = volatility.get("level", "normal")
            
            # Moderate volatility is best for most strategies
            if level == "normal":
                return 0.8
            elif level in ["low", "high"]:
                return 0.6
            elif level in ["very_low", "very_high"]:
                return 0.3
            else:
                return 0.5
                
        except Exception as e:
            return 0.5
    
    def _score_trend_condition(self, trend: Dict[str, Any]) -> float:
        """Score trend condition for trading"""
        try:
            strength = trend.get("strength", 0.0)
            quality = trend.get("quality", "weak")
            
            # Strong trends are good for trend-following
            if quality in ["strong", "very_strong"]:
                return 0.8
            elif quality == "moderate":
                return 0.6
            else:
                return 0.4
                
        except Exception as e:
            return 0.5
    
    def _score_session_condition(self, session: Dict[str, Any]) -> float:
        """Score session condition for trading"""
        try:
            liquidity_level = session.get("liquidity_level", "low")
            market_open = session.get("market_open", False)
            
            if not market_open:
                return 0.1
            
            if liquidity_level == "very_high":
                return 0.9
            elif liquidity_level == "high":
                return 0.7
            elif liquidity_level == "medium":
                return 0.5
            else:
                return 0.3
                
        except Exception as e:
            return 0.5
    
    def _get_trading_recommendation(self, volatility: Dict[str, Any], trend: Dict[str, Any], 
                                  session: Dict[str, Any]) -> Dict[str, Any]:
        """Get trading recommendation based on market conditions"""
        try:
            recommendations = []
            
            # Volatility-based recommendations
            vol_level = volatility.get("level", "normal")
            if vol_level == "very_low":
                recommendations.append("Consider range trading strategies")
            elif vol_level == "very_high":
                recommendations.append("Use smaller position sizes")
                recommendations.append("Widen stop losses")
            elif vol_level == "normal":
                recommendations.append("Good conditions for most strategies")
            
            # Trend-based recommendations
            trend_quality = trend.get("quality", "weak")
            trend_direction = trend.get("direction", "neutral")
            
            if trend_quality in ["strong", "very_strong"]:
                recommendations.append(f"Strong {trend_direction} trend - consider trend-following")
            elif trend_quality == "weak":
                recommendations.append("Weak trend - consider mean reversion")
            
            # Session-based recommendations
            if not session.get("market_open", False):
                recommendations.append("Markets closed - avoid trading")
            elif session.get("peak_hours", False):
                recommendations.append("Peak liquidity hours - good for scalping")
            elif session.get("liquidity_level") == "low":
                recommendations.append("Low liquidity - be cautious with large positions")
            
            return {
                "recommendations": recommendations,
                "overall_sentiment": "favorable" if len([r for r in recommendations if "good" in r.lower()]) > 0 else "cautious",
                "suggested_strategies": self._suggest_strategies(volatility, trend, session)
            }
            
        except Exception as e:
            return {"recommendations": ["Monitor market conditions"], "overall_sentiment": "neutral"}
    
    def _suggest_strategies(self, volatility: Dict[str, Any], trend: Dict[str, Any], 
                          session: Dict[str, Any]) -> List[str]:
        """Suggest suitable trading strategies"""
        try:
            strategies = []
            
            # Based on volatility
            vol_level = volatility.get("level", "normal")
            if vol_level in ["low", "very_low"]:
                strategies.extend(["range_trading", "mean_reversion"])
            elif vol_level in ["high", "very_high"]:
                strategies.extend(["breakout", "momentum"])
            else:
                strategies.extend(["scalping", "swing_trading"])
            
            # Based on trend
            trend_quality = trend.get("quality", "weak")
            if trend_quality in ["strong", "very_strong"]:
                strategies.extend(["trend_following", "momentum"])
            else:
                strategies.extend(["contrarian", "mean_reversion"])
            
            # Based on session
            if session.get("peak_hours", False):
                strategies.extend(["scalping", "hft"])
            elif session.get("liquidity_level") == "low":
                strategies = [s for s in strategies if s not in ["scalping", "hft"]]
            
            return list(set(strategies))  # Remove duplicates
            
        except Exception as e:
            return ["conservative"]
    
    def _calculate_volatility_percentile(self, current_vol: float, data: pd.DataFrame) -> float:
        """Calculate volatility percentile"""
        try:
            if len(data) < 50:
                return 0.5
            
            # Calculate historical volatility
            window = 20
            historical_vols = []
            
            for i in range(window, len(data)):
                segment = data.iloc[i-window:i]
                vol = self._calculate_segment_volatility(segment)
                historical_vols.append(vol)
            
            if not historical_vols:
                return 0.5
            
            # Calculate percentile
            percentile = (sum(1 for v in historical_vols if v < current_vol) / len(historical_vols))
            return percentile
            
        except Exception as e:
            return 0.5
    
    def _detect_volatility_regime(self, data: pd.DataFrame) -> str:
        """Detect volatility regime (expansion/contraction)"""
        try:
            if len(data) < 40:
                return "unknown"
            
            # Calculate volatility for different periods
            recent_vol = []
            historical_vol = []
            
            # Recent volatility (last 20 periods)
            for i in range(len(data)-20, len(data)):
                if i >= 10:
                    segment = data.iloc[i-10:i]
                    vol = self._calculate_segment_volatility(segment)
                    recent_vol.append(vol)
            
            # Historical volatility (20-40 periods ago)
            for i in range(len(data)-40, len(data)-20):
                if i >= 10:
                    segment = data.iloc[i-10:i]
                    vol = self._calculate_segment_volatility(segment)
                    historical_vol.append(vol)
            
            if recent_vol and historical_vol:
                recent_avg = np.mean(recent_vol)
                historical_avg = np.mean(historical_vol)
                
                ratio = recent_avg / historical_avg if historical_avg > 0 else 1.0
                
                if ratio > 1.3:
                    return "expansion"
                elif ratio < 0.7:
                    return "contraction"
                else:
                    return "stable"
            
            return "unknown"
            
        except Exception as e:
            return "unknown"
    
    def _store_condition_history(self, symbol: str, condition: Dict[str, Any]):
        """Store market condition in history"""
        try:
            if symbol not in self.condition_history:
                self.condition_history[symbol] = []
            
            # Store simplified condition
            simplified_condition = {
                "timestamp": condition["timestamp"],
                "overall_condition": condition["overall_condition"],
                "volatility_level": condition["volatility"]["level"],
                "trend_direction": condition["trend"]["direction"],
                "trend_strength": condition["trend"]["quality"],
                "liquidity_level": condition["liquidity"]["level"],
                "market_open": condition["session"]["market_open"]
            }
            
            self.condition_history[symbol].append(simplified_condition)
            
            # Keep only recent history (last 1000 records)
            if len(self.condition_history[symbol]) > 1000:
                self.condition_history[symbol] = self.condition_history[symbol][-1000:]
                
        except Exception as e:
            self.logger.error(f"Error storing condition history: {e}")
    
    def get_current_volatility(self, symbol: str) -> float:
        """Get current volatility for a symbol"""
        try:
            return self.current_volatility.get(symbol, 1.0)
        except:
            return 1.0
    
    def _get_default_conditions(self) -> Dict[str, Any]:
        """Get default market conditions when analysis fails"""
        return {
            "timestamp": datetime.now(),
            "symbol": "UNKNOWN",
            "overall_condition": "moderate",
            "volatility": {"current": 1.0, "level": "normal", "trend": "stable"},
            "trend": {"strength": 0.0, "direction": "neutral", "quality": "weak"},
            "session": {"current_sessions": [], "liquidity_level": "medium", "market_open": True},
            "liquidity": {"score": 0.5, "level": "medium"},
            "momentum": {"strength": 0.0, "direction": "neutral", "acceleration": 0.0},
            "range": {"expansion": False, "compression": False, "breakout_potential": 0.0},
            "correlation": {"primary_factors": [], "risk_on_off": "neutral"},
            "trading_recommendation": {
                "recommendations": ["Monitor market conditions"],
                "overall_sentiment": "cautious",
                "suggested_strategies": ["conservative"]
            }
        }
