"""
Pattern-based trading strategy for AuraTrade Bot
Identifies and trades based on candlestick and chart patterns
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from core.mt5_connector import MT5Connector
from analysis.pattern_recognition import PatternRecognition
from analysis.technical_analysis import TechnicalAnalysis
from utils.logger import Logger

class PatternStrategy:
    """Pattern-based trading strategy implementation"""
    
    def __init__(self, mt5_connector: MT5Connector, strategy_settings: Dict[str, Any]):
        self.logger = Logger.get_logger(__name__)
        self.mt5_connector = mt5_connector
        self.settings = strategy_settings
        self.pattern_recognition = PatternRecognition()
        self.technical_analysis = TechnicalAnalysis()
        
        # Pattern strategy parameters
        self.timeframe = self.settings.get("timeframe", "M15")
        self.confirmation_timeframe = self.settings.get("confirmation_timeframe", "H1")
        self.patterns = self.settings.get("patterns", {})
        self.min_pattern_strength = self.settings.get("min_pattern_strength", 0.6)
        self.require_volume_confirmation = self.settings.get("require_volume_confirmation", True)
        
        # Pattern tracking
        self.detected_patterns = {}
        self.pattern_success_rates = {}
        self.recent_patterns = {}
        
        self.logger.info("📊 Pattern Strategy initialized")
    
    def generate_signal(self, symbol: str, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate pattern-based trading signal"""
        try:
            rates_data = analysis_data.get("rates")
            if rates_data is None or len(rates_data) < 20:
                return None
            
            # Get confirmation timeframe data
            confirmation_data = self._get_confirmation_data(symbol)
            
            # Detect candlestick patterns
            candlestick_patterns = self._detect_candlestick_patterns(rates_data)
            
            # Detect chart patterns
            chart_patterns = self._detect_chart_patterns(rates_data)
            
            # Get technical confirmation
            technical_confirmation = self._get_technical_confirmation(analysis_data)
            
            # Get volume confirmation
            volume_confirmation = self._get_volume_confirmation(rates_data)
            
            # Combine all pattern signals
            combined_signal = self._combine_pattern_signals(
                symbol,
                candlestick_patterns,
                chart_patterns,
                technical_confirmation,
                volume_confirmation,
                confirmation_data
            )
            
            if not combined_signal or combined_signal["strength"] < self.min_pattern_strength:
                return None
            
            # Calculate entry levels
            tick_data = analysis_data.get("tick", {})
            if not tick_data:
                return None
            
            signal = self._create_pattern_signal(
                symbol, combined_signal, rates_data, tick_data
            )
            
            # Store detected pattern
            self._store_pattern_detection(symbol, combined_signal)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating pattern signal for {symbol}: {e}")
            return None
    
    def _get_confirmation_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get confirmation timeframe data"""
        try:
            # Convert timeframe strings to minutes
            timeframe_map = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
            
            confirmation_minutes = timeframe_map.get(self.confirmation_timeframe, 60)
            confirmation_data = self.mt5_connector.get_rates(symbol, confirmation_minutes, 100)
            
            return confirmation_data
            
        except Exception as e:
            self.logger.error(f"Error getting confirmation data: {e}")
            return None
    
    def _detect_candlestick_patterns(self, rates_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect candlestick patterns"""
        try:
            detected_patterns = []
            
            # Check each enabled pattern
            for pattern_name, pattern_config in self.patterns.items():
                if not pattern_config.get("enabled", False):
                    continue
                
                pattern_strength = pattern_config.get("strength", 0.5)
                
                # Detect specific patterns
                if pattern_name == "hammer":
                    hammer_signals = self.pattern_recognition.detect_hammer(rates_data)
                    for signal in hammer_signals:
                        signal["pattern_name"] = "hammer"
                        signal["base_strength"] = pattern_strength
                        detected_patterns.append(signal)
                
                elif pattern_name == "doji":
                    doji_signals = self.pattern_recognition.detect_doji(rates_data)
                    for signal in doji_signals:
                        signal["pattern_name"] = "doji"
                        signal["base_strength"] = pattern_strength
                        detected_patterns.append(signal)
                
                elif pattern_name == "engulfing":
                    engulfing_signals = self.pattern_recognition.detect_engulfing(rates_data)
                    for signal in engulfing_signals:
                        signal["pattern_name"] = "engulfing"
                        signal["base_strength"] = pattern_strength
                        detected_patterns.append(signal)
                
                elif pattern_name == "pinbar":
                    pinbar_signals = self.pattern_recognition.detect_pinbar(rates_data)
                    for signal in pinbar_signals:
                        signal["pattern_name"] = "pinbar"
                        signal["base_strength"] = pattern_strength
                        detected_patterns.append(signal)
                
                elif pattern_name == "inside_bar":
                    inside_bar_signals = self.pattern_recognition.detect_inside_bar(rates_data)
                    for signal in inside_bar_signals:
                        signal["pattern_name"] = "inside_bar"
                        signal["base_strength"] = pattern_strength
                        detected_patterns.append(signal)
            
            return detected_patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting candlestick patterns: {e}")
            return []
    
    def _detect_chart_patterns(self, rates_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect chart patterns"""
        try:
            detected_patterns = []
            
            # Support and resistance levels
            support_resistance = self.pattern_recognition.detect_support_resistance(rates_data)
            if support_resistance:
                detected_patterns.extend(support_resistance)
            
            # Triangle patterns
            triangles = self.pattern_recognition.detect_triangles(rates_data)
            if triangles:
                detected_patterns.extend(triangles)
            
            # Head and shoulders
            head_shoulders = self.pattern_recognition.detect_head_shoulders(rates_data)
            if head_shoulders:
                detected_patterns.extend(head_shoulders)
            
            # Double top/bottom
            double_patterns = self.pattern_recognition.detect_double_patterns(rates_data)
            if double_patterns:
                detected_patterns.extend(double_patterns)
            
            # Trend channels
            channels = self.pattern_recognition.detect_trend_channels(rates_data)
            if channels:
                detected_patterns.extend(channels)
            
            return detected_patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting chart patterns: {e}")
            return []
    
    def _get_technical_confirmation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get technical analysis confirmation"""
        try:
            technical_signals = analysis_data.get("technical", {})
            
            confirmations = {
                "trend_alignment": 0.0,
                "momentum_confirmation": 0.0,
                "volatility_confirmation": 0.0,
                "overall_score": 0.0
            }
            
            # Trend alignment
            sma_data = technical_signals.get("sma", {})
            ema_data = technical_signals.get("ema", {})
            
            if sma_data and ema_data:
                sma_trend = sma_data.get("trend", "neutral")
                ema_trend = ema_data.get("trend", "neutral")
                
                if sma_trend == ema_trend and sma_trend != "neutral":
                    confirmations["trend_alignment"] = 0.8
                elif sma_trend != "neutral" or ema_trend != "neutral":
                    confirmations["trend_alignment"] = 0.4
            
            # Momentum confirmation
            rsi_data = technical_signals.get("rsi", {})
            macd_data = technical_signals.get("macd", {})
            
            if rsi_data and macd_data:
                rsi_signal = rsi_data.get("signal", "neutral")
                macd_signal = macd_data.get("signal", "neutral")
                
                if rsi_signal == macd_signal and rsi_signal != "neutral":
                    confirmations["momentum_confirmation"] = 0.7
                elif rsi_signal != "neutral" or macd_signal != "neutral":
                    confirmations["momentum_confirmation"] = 0.3
            
            # Volatility confirmation
            atr_data = technical_signals.get("atr", {})
            bb_data = technical_signals.get("bollinger_bands", {})
            
            if atr_data and bb_data:
                atr_trend = atr_data.get("trend", "neutral")
                bb_squeeze = bb_data.get("squeeze", False)
                
                if atr_trend == "expanding" and not bb_squeeze:
                    confirmations["volatility_confirmation"] = 0.6
                elif atr_trend == "contracting" and bb_squeeze:
                    confirmations["volatility_confirmation"] = 0.3
            
            # Calculate overall score
            confirmations["overall_score"] = (
                confirmations["trend_alignment"] * 0.4 +
                confirmations["momentum_confirmation"] * 0.4 +
                confirmations["volatility_confirmation"] * 0.2
            )
            
            return confirmations
            
        except Exception as e:
            self.logger.error(f"Error getting technical confirmation: {e}")
            return {"trend_alignment": 0.0, "momentum_confirmation": 0.0, 
                   "volatility_confirmation": 0.0, "overall_score": 0.0}
    
    def _get_volume_confirmation(self, rates_data: pd.DataFrame) -> Dict[str, Any]:
        """Get volume confirmation for patterns"""
        try:
            if "volume" not in rates_data.columns:
                return {"volume_support": 0.0, "volume_trend": "neutral"}
            
            volume = rates_data["volume"].values
            
            if len(volume) < 10:
                return {"volume_support": 0.0, "volume_trend": "neutral"}
            
            # Calculate average volume
            avg_volume = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
            recent_volume = np.mean(volume[-3:])  # Last 3 bars
            
            # Volume support calculation
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            if volume_ratio > 1.5:
                volume_support = 0.8
                volume_trend = "increasing"
            elif volume_ratio > 1.2:
                volume_support = 0.6
                volume_trend = "increasing"
            elif volume_ratio < 0.7:
                volume_support = 0.2
                volume_trend = "decreasing"
            else:
                volume_support = 0.4
                volume_trend = "neutral"
            
            return {
                "volume_support": volume_support,
                "volume_trend": volume_trend,
                "volume_ratio": volume_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Error getting volume confirmation: {e}")
            return {"volume_support": 0.0, "volume_trend": "neutral"}
    
    def _combine_pattern_signals(self, symbol: str, candlestick_patterns: List[Dict[str, Any]],
                               chart_patterns: List[Dict[str, Any]], 
                               technical_confirmation: Dict[str, Any],
                               volume_confirmation: Dict[str, Any],
                               confirmation_data: Optional[pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Combine all pattern signals into a single trading signal"""
        try:
            if not candlestick_patterns and not chart_patterns:
                return None
            
            all_patterns = candlestick_patterns + chart_patterns
            
            # Score each pattern
            scored_patterns = []
            for pattern in all_patterns:
                score = self._score_pattern(pattern, technical_confirmation, 
                                          volume_confirmation, confirmation_data)
                if score > 0:
                    pattern["final_score"] = score
                    scored_patterns.append(pattern)
            
            if not scored_patterns:
                return None
            
            # Sort by score and select best patterns
            scored_patterns.sort(key=lambda x: x["final_score"], reverse=True)
            
            # Combine top patterns
            top_patterns = scored_patterns[:3]  # Top 3 patterns
            
            # Determine overall direction
            buy_strength = sum(p["final_score"] for p in top_patterns if p.get("direction") == "BUY")
            sell_strength = sum(p["final_score"] for p in top_patterns if p.get("direction") == "SELL")
            
            if buy_strength > sell_strength and buy_strength > 0.3:
                direction = "BUY"
                strength = buy_strength
            elif sell_strength > buy_strength and sell_strength > 0.3:
                direction = "SELL"
                strength = sell_strength
            else:
                return None
            
            # Apply confirmations
            confirmation_multiplier = (
                technical_confirmation["overall_score"] * 0.6 +
                volume_confirmation["volume_support"] * 0.4
            )
            
            final_strength = min(strength * (1 + confirmation_multiplier), 1.0)
            
            # Check timeframe confirmation
            if confirmation_data is not None:
                timeframe_confirmation = self._get_timeframe_confirmation(
                    confirmation_data, direction
                )
                final_strength *= (1 + timeframe_confirmation * 0.3)
            
            return {
                "direction": direction,
                "strength": min(final_strength, 1.0),
                "patterns": top_patterns,
                "technical_confirmation": technical_confirmation,
                "volume_confirmation": volume_confirmation,
                "reasoning": self._create_pattern_reasoning(top_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error combining pattern signals: {e}")
            return None
    
    def _score_pattern(self, pattern: Dict[str, Any], technical_confirmation: Dict[str, Any],
                      volume_confirmation: Dict[str, Any], 
                      confirmation_data: Optional[pd.DataFrame]) -> float:
        """Score individual pattern based on various factors"""
        try:
            base_strength = pattern.get("base_strength", 0.5)
            pattern_quality = pattern.get("quality", 0.5)
            
            # Base score
            score = base_strength * pattern_quality
            
            # Historical success rate
            pattern_name = pattern.get("pattern_name", "unknown")
            historical_success = self.pattern_success_rates.get(pattern_name, 0.5)
            score *= (0.5 + historical_success * 0.5)
            
            # Technical confirmation bonus
            tech_score = technical_confirmation.get("overall_score", 0)
            score *= (1 + tech_score * 0.3)
            
            # Volume confirmation
            if self.require_volume_confirmation:
                volume_score = volume_confirmation.get("volume_support", 0)
                if volume_score < 0.3:
                    score *= 0.5  # Penalize weak volume
                else:
                    score *= (1 + volume_score * 0.2)
            
            # Pattern recency (prefer recent patterns)
            pattern_age = pattern.get("bars_ago", 0)
            if pattern_age > 5:
                score *= 0.8  # Reduce score for old patterns
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error scoring pattern: {e}")
            return 0.0
    
    def _get_timeframe_confirmation(self, confirmation_data: pd.DataFrame, 
                                  direction: str) -> float:
        """Get confirmation from higher timeframe"""
        try:
            if len(confirmation_data) < 10:
                return 0.0
            
            # Simple trend confirmation using closing prices
            recent_closes = confirmation_data["close"].values[-5:]
            trend_slope = np.polyfit(range(len(recent_closes)), recent_closes, 1)[0]
            
            if direction == "BUY" and trend_slope > 0:
                return 0.5  # Positive confirmation
            elif direction == "SELL" and trend_slope < 0:
                return 0.5  # Positive confirmation
            elif (direction == "BUY" and trend_slope < 0) or \
                 (direction == "SELL" and trend_slope > 0):
                return -0.3  # Negative confirmation
            
            return 0.0  # Neutral
            
        except Exception as e:
            self.logger.error(f"Error getting timeframe confirmation: {e}")
            return 0.0
    
    def _create_pattern_reasoning(self, patterns: List[Dict[str, Any]]) -> str:
        """Create human-readable reasoning for pattern signals"""
        try:
            pattern_names = [p.get("pattern_name", "unknown") for p in patterns]
            pattern_scores = [f"{p.get('pattern_name', 'unknown')}({p.get('final_score', 0):.2f})" 
                            for p in patterns]
            
            reasoning = f"Pattern combination: {', '.join(pattern_scores)}"
            
            return reasoning
            
        except Exception as e:
            self.logger.error(f"Error creating pattern reasoning: {e}")
            return "Pattern-based signal"
    
    def _create_pattern_signal(self, symbol: str, combined_signal: Dict[str, Any],
                             rates_data: pd.DataFrame, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create final pattern trading signal"""
        try:
            direction = combined_signal["direction"]
            strength = combined_signal["strength"]
            
            # Calculate entry price
            entry_price = tick_data["ask"] if direction == "BUY" else tick_data["bid"]
            
            # Calculate stop loss and take profit based on pattern
            sl_level, tp_level = self._calculate_pattern_levels(
                symbol, direction, entry_price, rates_data, combined_signal
            )
            
            # Calculate stop loss in pips
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info:
                point = symbol_info.get("point", 0.0001)
                sl_pips = abs(entry_price - sl_level) / point
            else:
                sl_pips = 20  # Default
            
            signal = {
                "direction": direction,
                "strength": strength,
                "entry_price": entry_price,
                "take_profit": tp_level,
                "stop_loss": sl_level,
                "stop_loss_pips": sl_pips,
                "strategy_type": "pattern",
                "timeframe": self.timeframe,
                "confidence": strength,
                "patterns_detected": [p.get("pattern_name") for p in combined_signal["patterns"]],
                "reasoning": combined_signal["reasoning"]
            }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error creating pattern signal: {e}")
            return None
    
    def _calculate_pattern_levels(self, symbol: str, direction: str, entry_price: float,
                                rates_data: pd.DataFrame, combined_signal: Dict[str, Any]) -> tuple:
        """Calculate stop loss and take profit levels for pattern trades"""
        try:
            # Get recent price action for level calculation
            highs = rates_data["high"].values[-20:]
            lows = rates_data["low"].values[-20:]
            
            # Calculate ATR for dynamic levels
            atr = self._calculate_simple_atr(rates_data, 14)
            
            # Base levels using ATR
            if direction == "BUY":
                # Stop loss below recent low
                recent_low = np.min(lows[-10:])
                sl_level = min(recent_low - atr * 0.5, entry_price - atr * 1.5)
                
                # Take profit using risk-reward ratio
                risk_distance = entry_price - sl_level
                tp_level = entry_price + risk_distance * 2  # 1:2 risk-reward
                
            else:  # SELL
                # Stop loss above recent high
                recent_high = np.max(highs[-10:])
                sl_level = max(recent_high + atr * 0.5, entry_price + atr * 1.5)
                
                # Take profit using risk-reward ratio
                risk_distance = sl_level - entry_price
                tp_level = entry_price - risk_distance * 2  # 1:2 risk-reward
            
            # Adjust based on pattern type
            patterns = combined_signal.get("patterns", [])
            for pattern in patterns:
                pattern_name = pattern.get("pattern_name", "")
                
                # Pattern-specific adjustments
                if pattern_name in ["hammer", "doji"]:
                    # Reversal patterns - tighter stops
                    if direction == "BUY":
                        sl_level = max(sl_level, entry_price - atr * 1.0)
                    else:
                        sl_level = min(sl_level, entry_price + atr * 1.0)
                
                elif pattern_name in ["engulfing"]:
                    # Strong reversal - wider targets
                    if direction == "BUY":
                        tp_level = entry_price + (entry_price - sl_level) * 2.5
                    else:
                        tp_level = entry_price - (sl_level - entry_price) * 2.5
            
            # Round to symbol digits
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if symbol_info:
                digits = symbol_info.get("digits", 5)
                sl_level = round(sl_level, digits)
                tp_level = round(tp_level, digits)
            
            return tp_level, sl_level
            
        except Exception as e:
            self.logger.error(f"Error calculating pattern levels: {e}")
            return 0.0, 0.0
    
    def _calculate_simple_atr(self, rates_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate simple Average True Range"""
        try:
            if len(rates_data) < period + 1:
                return 0.001  # Default value
            
            highs = rates_data["high"].values
            lows = rates_data["low"].values
            closes = rates_data["close"].values
            
            # Calculate True Range
            tr_values = []
            for i in range(1, len(rates_data)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
            
            # Calculate ATR
            if len(tr_values) >= period:
                atr = np.mean(tr_values[-period:])
            else:
                atr = np.mean(tr_values)
            
            return atr
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return 0.001
    
    def _store_pattern_detection(self, symbol: str, pattern_signal: Dict[str, Any]):
        """Store pattern detection for tracking"""
        try:
            if symbol not in self.detected_patterns:
                self.detected_patterns[symbol] = []
            
            pattern_record = {
                "timestamp": datetime.now(),
                "patterns": pattern_signal.get("patterns", []),
                "direction": pattern_signal["direction"],
                "strength": pattern_signal["strength"]
            }
            
            self.detected_patterns[symbol].append(pattern_record)
            
            # Keep only recent detections
            if len(self.detected_patterns[symbol]) > 100:
                self.detected_patterns[symbol] = self.detected_patterns[symbol][-100:]
                
        except Exception as e:
            self.logger.error(f"Error storing pattern detection: {e}")
    
    def update_pattern_success_rates(self, pattern_name: str, success: bool):
        """Update success rates for pattern types"""
        try:
            if pattern_name not in self.pattern_success_rates:
                self.pattern_success_rates[pattern_name] = {"success": 0, "total": 0}
            
            self.pattern_success_rates[pattern_name]["total"] += 1
            if success:
                self.pattern_success_rates[pattern_name]["success"] += 1
            
        except Exception as e:
            self.logger.error(f"Error updating pattern success rates: {e}")
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern strategy statistics"""
        try:
            # Calculate success rates
            success_rates = {}
            for pattern, stats in self.pattern_success_rates.items():
                if stats["total"] > 0:
                    success_rates[pattern] = stats["success"] / stats["total"] * 100
            
            # Count recent detections
            recent_detections = 0
            for symbol_patterns in self.detected_patterns.values():
                recent_detections += len([p for p in symbol_patterns 
                                        if (datetime.now() - p["timestamp"]).days < 1])
            
            return {
                "strategy": "Pattern",
                "timeframe": self.timeframe,
                "confirmation_timeframe": self.confirmation_timeframe,
                "min_pattern_strength": self.min_pattern_strength,
                "enabled_patterns": [name for name, config in self.patterns.items() 
                                   if config.get("enabled", False)],
                "pattern_success_rates": success_rates,
                "recent_detections_24h": recent_detections,
                "total_patterns_tracked": len(self.pattern_success_rates)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pattern statistics: {e}")
            return {}
