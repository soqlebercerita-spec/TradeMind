
"""
Position sizing calculator for AuraTrade Bot
Calculates optimal lot sizes based on risk percentage and account equity
"""

from typing import Dict, Optional
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger

class PositionSizing:
    """Position sizing calculator based on risk percentage"""
    
    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager):
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.logger = Logger().get_logger()
        
        # Default risk settings
        self.default_risk_percent = 1.0  # 1% risk per trade
        self.min_lot_size = 0.01
        self.max_lot_size = 10.0
        
    def calculate_lot_size(self, symbol: str, entry_price: float, stop_loss: float, 
                          risk_percent: Optional[float] = None) -> float:
        """Calculate optimal lot size based on risk percentage"""
        try:
            # Get account info
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                self.logger.error("Cannot get account info for position sizing")
                return self.min_lot_size
            
            # Use default risk if not specified
            if risk_percent is None:
                risk_percent = self.default_risk_percent
            
            # Calculate risk amount in account currency
            equity = account_info['equity']
            risk_amount = equity * (risk_percent / 100)
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"Cannot get symbol info for {symbol}")
                return self.min_lot_size
            
            # Calculate pip value and risk in pips
            pip_size = self._get_pip_size(symbol)
            risk_pips = abs(entry_price - stop_loss) / pip_size
            
            if risk_pips <= 0:
                self.logger.warning("Invalid stop loss distance")
                return self.min_lot_size
            
            # Calculate pip value per lot
            pip_value_per_lot = self._calculate_pip_value_per_lot(symbol, symbol_info)
            
            # Calculate lot size
            lot_size = risk_amount / (risk_pips * pip_value_per_lot)
            
            # Round to symbol's lot step
            lot_step = symbol_info.get('volume_step', 0.01)
            lot_size = round(lot_size / lot_step) * lot_step
            
            # Apply min/max limits
            lot_size = max(self.min_lot_size, min(lot_size, self.max_lot_size))
            
            # Final risk manager check
            if not self.risk_manager.can_open_position(symbol):
                return 0.0
            
            self.logger.info(f"Calculated lot size for {symbol}: {lot_size} (Risk: {risk_percent}%)")
            return lot_size
            
        except Exception as e:
            self.logger.error(f"Error calculating lot size: {e}")
            return self.min_lot_size
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        pip_sizes = {
            'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01,
            'USDCHF': 0.0001, 'AUDUSD': 0.0001, 'USDCAD': 0.0001,
            'NZDUSD': 0.0001, 'EURGBP': 0.0001, 'EURJPY': 0.01,
            'GBPJPY': 0.01, 'XAUUSD': 0.1, 'XAGUSD': 0.001,
            'BTCUSD': 1.0, 'US30': 1.0, 'NAS100': 1.0
        }
        return pip_sizes.get(symbol, 0.0001)
    
    def _calculate_pip_value_per_lot(self, symbol: str, symbol_info: Dict) -> float:
        """Calculate pip value per lot for symbol"""
        try:
            # Get account currency
            account_info = self.mt5_connector.get_account_info()
            account_currency = account_info.get('currency', 'USD')
            
            # Basic pip values for USD account
            if account_currency == 'USD':
                pip_values = {
                    'EURUSD': 10.0, 'GBPUSD': 10.0, 'USDJPY': 9.24,  # Approximate
                    'USDCHF': 10.26, 'AUDUSD': 10.0, 'USDCAD': 7.46,
                    'NZDUSD': 10.0, 'XAUUSD': 1.0, 'XAGUSD': 5.0
                }
                return pip_values.get(symbol, 10.0)
            
            # For other account currencies, use simplified calculation
            return 10.0
            
        except Exception as e:
            self.logger.error(f"Error calculating pip value: {e}")
            return 10.0
    
    def get_max_lot_size_for_balance(self, symbol: str, balance_percent: float = 10.0) -> float:
        """Get maximum lot size based on balance percentage"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return self.min_lot_size
            
            # Calculate max risk amount
            max_risk = account_info['equity'] * (balance_percent / 100)
            
            # Get symbol info for margin calculation
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return self.min_lot_size
            
            # Simplified margin calculation
            margin_required = symbol_info.get('margin_initial', 1000)  # Per lot
            max_lots = max_risk / margin_required
            
            return min(max_lots, self.max_lot_size)
            
        except Exception as e:
            self.logger.error(f"Error calculating max lot size: {e}")
            return self.min_lot_size
