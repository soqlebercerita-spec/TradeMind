
"""
Scalping strategy for AuraTrade Bot
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import Logger

class ScalpingStrategy:
    """Scalping strategy implementation"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.enabled = True
        self.name = "Scalping"
        
        # Strategy parameters
        self.min_confidence = 70.0
        self.scalp_target = 8.0  # pips
        self.stop_loss = 5.0  # pips
        self.bb_period = 20
        self.bb_std = 2.0
        
    def analyze_signal(self, symbol: str, data: pd.DataFrame, current_price: tuple, 
                      market_condition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze scalping signals"""
        try:
            if len(data) < 25:
                return None
            
            # Calculate Bollinger Bands
            bb_middle = data['close'].rolling(self.bb_period).mean()
            bb_std = data['close'].rolling(self.bb_period).std()
            bb_upper = bb_middle + (bb_std * self.bb_std)
            bb_lower = bb_middle - (bb_std * self.bb_std)
            
            # Calculate RSI
            rsi = self._calculate_rsi(data['close'], 14)
            
            # Calculate MACD
            macd_data = self._calculate_macd(data['close'])
            
            bid, ask = current_price
            current = (bid + ask) / 2
            
            signal = None
            confidence = 0
            
            # Oversold bounce signal
            if (current <= bb_lower.iloc[-1] and 
                rsi.iloc[-1] < 30 and
                macd_data['histogram'].iloc[-1] > macd_data['histogram'].iloc[-2]):
                
                signal = 'buy'
                confidence = 75.0
                
                # Additional confirmations
                if data['close'].iloc[-1] > data['low'].iloc[-1]:  # Not at session low
                    confidence += 10
                if market_condition.get('condition') == 'ranging':
                    confidence += 5
                    
            # Overbought fade signal
            elif (current >= bb_upper.iloc[-1] and 
                  rsi.iloc[-1] > 70 and
                  macd_data['histogram'].iloc[-1] < macd_data['histogram'].iloc[-2]):
                
                signal = 'sell'
                confidence = 75.0
                
                # Additional confirmations
                if data['close'].iloc[-1] < data['high'].iloc[-1]:  # Not at session high
                    confidence += 10
                if market_condition.get('condition') == 'ranging':
                    confidence += 5
            
            if signal and confidence >= self.min_confidence:
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'entry_price': current,
                    'stop_loss_pips': self.stop_loss,
                    'take_profit_pips': self.scalp_target,
                    'risk_percent': 0.8,
                    'strategy': self.name,
                    'timeframe': 'M5'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in scalping strategy analysis: {e}")
            return None
    
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception:
            return pd.Series()
    
    def _calculate_macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD"""
        try:
            exp1 = series.ewm(span=fast).mean()
            exp2 = series.ewm(span=slow).mean()
            
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
            
        except Exception:
            return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}
