
"""
High Frequency Trading strategy for AuraTrade Bot
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import Logger

class HFTStrategy:
    """High Frequency Trading strategy"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.enabled = True
        self.name = "HFT"
        
        # Strategy parameters
        self.min_confidence = 75.0
        self.max_spread = 2.0
        self.scalp_target = 5.0  # pips
        self.stop_loss = 3.0  # pips
        self.risk_reward = 1.67  # 5:3 ratio
        
    def analyze_signal(self, symbol: str, data: pd.DataFrame, current_price: tuple, 
                      market_condition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze HFT signals"""
        try:
            if len(data) < 20:
                return None
            
            # Check market conditions
            if market_condition.get('volatility') == 'low':
                return None
            
            # Calculate indicators
            ema_5 = data['close'].ewm(span=5).mean()
            ema_10 = data['close'].ewm(span=10).mean()
            rsi = self._calculate_rsi(data['close'], 7)
            
            bid, ask = current_price
            current = (bid + ask) / 2
            
            # Signal logic
            signal = None
            confidence = 0
            
            # Bullish signal
            if (ema_5.iloc[-1] > ema_10.iloc[-1] and 
                ema_5.iloc[-2] <= ema_10.iloc[-2] and
                rsi.iloc[-1] > 30 and rsi.iloc[-1] < 70 and
                current > ema_5.iloc[-1]):
                
                signal = 'buy'
                confidence = 80.0
                
                # Additional confirmations
                if data['close'].iloc[-1] > data['open'].iloc[-1]:  # Green candle
                    confidence += 5
                if market_condition.get('trend') == 'up':
                    confidence += 10
                    
            # Bearish signal
            elif (ema_5.iloc[-1] < ema_10.iloc[-1] and 
                  ema_5.iloc[-2] >= ema_10.iloc[-2] and
                  rsi.iloc[-1] < 70 and rsi.iloc[-1] > 30 and
                  current < ema_5.iloc[-1]):
                
                signal = 'sell'
                confidence = 80.0
                
                # Additional confirmations
                if data['close'].iloc[-1] < data['open'].iloc[-1]:  # Red candle
                    confidence += 5
                if market_condition.get('trend') == 'down':
                    confidence += 10
            
            if signal and confidence >= self.min_confidence:
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'entry_price': current,
                    'stop_loss_pips': self.stop_loss,
                    'take_profit_pips': self.scalp_target,
                    'risk_percent': 0.5,
                    'strategy': self.name,
                    'timeframe': 'M1'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in HFT strategy analysis: {e}")
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
