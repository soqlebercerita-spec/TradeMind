
"""
Position sizing system for AuraTrade Bot
Implements Kelly Criterion and risk-based position sizing
"""

import math
from typing import Dict, Any, Optional
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger

class PositionSizing:
    """Advanced position sizing system"""
    
    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager):
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.logger = Logger().get_logger()
        
        # Position sizing parameters
        self.kelly_fraction = 0.25  # Conservative Kelly fraction
        self.max_position_size = 10.0  # Max 10 lots per position
        self.min_position_size = 0.01  # Min 0.01 lots
        
    def calculate_position_size(self, symbol: str, risk_amount: float, 
                              entry_price: float, stop_loss: float) -> float:
        """Calculate optimal position size"""
        try:
            if not all([symbol, risk_amount, entry_price, stop_loss]):
                return 0.0
            
            # Use risk manager's calculation as base
            base_size = self.risk_manager.calculate_position_size(
                symbol, risk_amount, entry_price, stop_loss
            )
            
            # Apply Kelly Criterion adjustment
            kelly_size = self._apply_kelly_criterion(symbol, base_size)
            
            # Apply risk limits
            final_size = self._apply_risk_limits(symbol, kelly_size)
            
            return final_size
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating position size: {e}")
            return 0.0
    
    def _apply_kelly_criterion(self, symbol: str, base_size: float) -> float:
        """Apply Kelly Criterion for position sizing"""
        try:
            # Simplified Kelly - in practice, use historical win rate and avg win/loss
            win_rate = 0.85  # Target 85% win rate
            avg_win = 20.0   # Average win in pips
            avg_loss = 10.0  # Average loss in pips
            
            if win_rate > 0 and avg_loss > 0:
                # Kelly formula: f = (bp - q) / b
                # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
                b = avg_win / avg_loss
                p = win_rate
                q = 1 - win_rate
                
                kelly_fraction = (b * p - q) / b
                kelly_fraction = max(0, min(kelly_fraction, self.kelly_fraction))
                
                return base_size * kelly_fraction
            
            return base_size
            
        except Exception as e:
            self.logger.error(f"❌ Error applying Kelly criterion: {e}")
            return base_size
    
    def _apply_risk_limits(self, symbol: str, size: float) -> float:
        """Apply final risk limits to position size"""
        try:
            # Apply min/max limits
            size = max(size, self.min_position_size)
            size = min(size, self.max_position_size)
            
            # Check account-specific limits
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                # Max 5% of equity per position
                max_equity_risk = account_info['equity'] * 0.05
                max_size_by_equity = max_equity_risk / 1000  # Simplified conversion
                size = min(size, max_size_by_equity)
            
            # Round to appropriate precision
            return round(size, 2)
            
        except Exception as e:
            self.logger.error(f"❌ Error applying risk limits: {e}")
            return self.min_position_size
    
    def get_recommended_size(self, symbol: str, strategy: str = "default") -> float:
        """Get recommended position size for symbol and strategy"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return self.min_position_size
            
            # Strategy-specific sizing
            strategy_multipliers = {
                'scalping': 0.5,    # Smaller positions for scalping
                'hft': 0.3,         # Very small positions for HFT
                'pattern': 1.0,     # Normal positions for patterns
                'arbitrage': 1.5    # Larger positions for arbitrage
            }
            
            multiplier = strategy_multipliers.get(strategy, 1.0)
            
            # Base size as percentage of equity
            base_size = (account_info['equity'] * 0.01) / 1000  # 1% of equity
            recommended_size = base_size * multiplier
            
            return self._apply_risk_limits(symbol, recommended_size)
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating recommended size: {e}")
            return self.min_position_size
