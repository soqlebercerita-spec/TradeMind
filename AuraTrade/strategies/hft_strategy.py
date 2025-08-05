
"""
High Frequency Trading (HFT) Strategy for AuraTrade Bot
Ultra-fast execution based on tick data and micro-movements
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from utils.logger import Logger

class HFTStrategy:
    """High Frequency Trading strategy implementation"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.name = "HFT_Strategy"
        self.enabled = True
        
        # HFT Parameters
        self.min_spread = 0.5  # pips
        self.max_spread = 2.0  # pips
        self.profit_target = 0.8  # pips
        self.stop_loss = 1.5  # pips
        self.min_volatility = 0.3
        self.max_volatility = 2.0
        
        # Execution settings
        self.max_positions = 3
        self.max_trades_per_minute = 5
        self.trade_count_minute = 0
        self.last_minute_reset = datetime.now().minute
        
    def analyze_signal(self, symbol: str, data: pd.DataFrame, 
                      current_price: tuple, market_condition: Dict) -> Optional[Dict[str, Any]]:
        """Analyze HFT signals based on micro-movements"""
        try:
            if not self.enabled or len(data) < 20:
                return None
            
            # Reset trade counter if new minute
            current_minute = datetime.now().minute
            if current_minute != self.last_minute_reset:
                self.trade_count_minute = 0
                self.last_minute_reset = current_minute
            
            # Check rate limiting
            if self.trade_count_minute >= self.max_trades_per_minute:
                return None
            
            bid, ask = current_price
            spread = ask - bid
            
            # Spread filter
            if not (self.min_spread <= spread * 10000 <= self.max_spread):
                return None
            
            # Volatility filter
            atr = data['atr'].iloc[-1] if 'atr' in data.columns else 0
            if not (self.min_volatility <= atr * 10000 <= self.max_volatility):
                return None
            
            # Ultra-short term momentum
            price_changes = data['close'].diff().tail(5)
            momentum = price_changes.sum()
            
            # Micro trend detection
            ema_5 = data['close'].ewm(span=5).mean()
            ema_10 = data['close'].ewm(span=10).mean()
            
            micro_trend = ema_5.iloc[-1] - ema_10.iloc[-1]
            
            # Signal generation
            signal = None
            confidence = 0.0
            
            # Bullish HFT signal
            if momentum > 0 and micro_trend > 0 and data['close'].iloc[-1] > ema_5.iloc[-1]:
                signal = 'buy'
                confidence = min(abs(momentum) * 1000 + abs(micro_trend) * 1000, 100)
            
            # Bearish HFT signal
            elif momentum < 0 and micro_trend < 0 and data['close'].iloc[-1] < ema_5.iloc[-1]:
                signal = 'sell'
                confidence = min(abs(momentum) * 1000 + abs(micro_trend) * 1000, 100)
            
            if signal and confidence > 60:
                self.trade_count_minute += 1
                
                return {
                    'strategy': self.name,
                    'signal': signal,
                    'confidence': confidence,
                    'entry_price': ask if signal == 'buy' else bid,
                    'stop_loss_pips': self.stop_loss,
                    'take_profit_pips': self.profit_target,
                    'risk_percent': 0.5,  # Low risk for HFT
                    'timeframe': 'M1',
                    'reason': f'HFT {signal.upper()} - Momentum: {momentum:.5f}, Micro-trend: {micro_trend:.5f}'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in HFT strategy analysis: {e}")
            return None
    
    def should_close_position(self, position: Dict, current_data: pd.DataFrame) -> bool:
        """Check if HFT position should be closed early"""
        try:
            # Quick profit taking for HFT
            if position.get('profit', 0) > 5:  # $5 profit
                return True
            
            # Time-based exit (HFT positions should be short)
            entry_time = position.get('time_opened')
            if entry_time:
                time_diff = datetime.now() - datetime.fromtimestamp(entry_time)
                if time_diff.total_seconds() > 300:  # 5 minutes max
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking HFT position close: {e}")
            return False
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information and parameters"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'type': 'HFT',
            'timeframe': 'M1',
            'parameters': {
                'min_spread': self.min_spread,
                'max_spread': self.max_spread,
                'profit_target': self.profit_target,
                'stop_loss': self.stop_loss,
                'max_positions': self.max_positions,
                'max_trades_per_minute': self.max_trades_per_minute
            }
        }
