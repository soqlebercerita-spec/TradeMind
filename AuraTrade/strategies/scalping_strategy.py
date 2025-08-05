
"""
Scalping Strategy for AuraTrade Bot
Quick entries and exits with small profit targets
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import Logger

class ScalpingStrategy:
    """Scalping strategy implementation"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "Scalping_Strategy"
        self.enabled = True
        
        # Scalping parameters
        self.profit_target_pips = 3.0
        self.stop_loss_pips = 2.0
        self.rsi_oversold = 25
        self.rsi_overbought = 75
        self.min_atr = 0.5
        self.max_atr = 3.0
        
    def analyze_signal(self, symbol: str, data: pd.DataFrame, 
                      current_price: tuple, market_condition: Dict) -> Optional[Dict[str, Any]]:
        """Analyze scalping signals"""
        try:
            if not self.enabled or len(data) < 50:
                return None
            
            bid, ask = current_price
            latest = data.iloc[-1]
            
            # ATR filter
            atr = latest.get('atr', 0)
            if not (self.min_atr <= atr * 10000 <= self.max_atr):
                return None
            
            # RSI analysis
            rsi = latest.get('rsi', 50)
            
            # Moving average analysis
            sma_20 = latest.get('sma_20', latest['close'])
            ema_12 = latest.get('ema_12', latest['close'])
            
            # MACD analysis
            macd = latest.get('macd', 0)
            macd_signal = latest.get('macd_signal', 0)
            
            # Bollinger Bands
            bb_upper = latest.get('bb_upper', latest['close'] + 0.001)
            bb_lower = latest.get('bb_lower', latest['close'] - 0.001)
            
            signal = None
            confidence = 0.0
            
            # Bullish scalping signal
            if (rsi < self.rsi_oversold and 
                latest['close'] < bb_lower and 
                macd > macd_signal and
                latest['close'] > ema_12):
                
                signal = 'buy'
                confidence = 70 + min((self.rsi_oversold - rsi), 15)
            
            # Bearish scalping signal
            elif (rsi > self.rsi_overbought and 
                  latest['close'] > bb_upper and 
                  macd < macd_signal and
                  latest['close'] < ema_12):
                
                signal = 'sell'
                confidence = 70 + min((rsi - self.rsi_overbought), 15)
            
            # Mean reversion scalping
            elif latest['close'] < sma_20 * 0.998 and rsi < 40:
                signal = 'buy'
                confidence = 65
            elif latest['close'] > sma_20 * 1.002 and rsi > 60:
                signal = 'sell'
                confidence = 65
            
            if signal and confidence > 65:
                return {
                    'strategy': self.name,
                    'signal': signal,
                    'confidence': confidence,
                    'entry_price': ask if signal == 'buy' else bid,
                    'stop_loss_pips': self.stop_loss_pips,
                    'take_profit_pips': self.profit_target_pips,
                    'risk_percent': 1.0,
                    'timeframe': 'M5',
                    'reason': f'Scalping {signal.upper()} - RSI: {rsi:.1f}, BB position, MACD cross'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in scalping strategy analysis: {e}")
            return None
    
    def should_close_position(self, position: Dict, current_data: pd.DataFrame) -> bool:
        """Check if scalping position should be closed"""
        try:
            # Quick profit taking
            profit_usd = position.get('profit', 0)
            if profit_usd > 10:  # $10 profit
                return True
            
            # RSI reversal exit
            if len(current_data) > 0:
                latest_rsi = current_data.iloc[-1].get('rsi', 50)
                
                # Close long positions on high RSI
                if position.get('type') == 0 and latest_rsi > 75:  # Long position
                    return True
                
                # Close short positions on low RSI
                if position.get('type') == 1 and latest_rsi < 25:  # Short position
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking scalping position close: {e}")
            return False
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'type': 'Scalping',
            'timeframe': 'M5',
            'parameters': {
                'profit_target_pips': self.profit_target_pips,
                'stop_loss_pips': self.stop_loss_pips,
                'rsi_oversold': self.rsi_oversold,
                'rsi_overbought': self.rsi_overbought
            }
        }
