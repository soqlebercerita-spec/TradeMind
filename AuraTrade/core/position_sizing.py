"""
Position sizing calculations for AuraTrade Bot
"""

from typing import Optional
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger

class PositionSizing:
    """Position sizing calculation system"""

    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager):
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.logger = Logger().get_logger()

        # Default sizing parameters
        self.default_risk_percent = 1.0  # 1% per trade
        self.min_lot_size = 0.01
        self.max_lot_size = 10.0

    def calculate_lot_size(self, symbol: str, entry_price: float, stop_loss: float,
                          risk_percent: float = None) -> float:
        """Calculate optimal lot size based on risk percentage"""
        try:
            if risk_percent is None:
                risk_percent = self.default_risk_percent

            # Get account information
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                self.logger.error("Cannot get account info for position sizing")
                return self.min_lot_size

            balance = account_info.get('balance', 0)
            if balance <= 0:
                return self.min_lot_size

            # Calculate risk amount in account currency
            risk_amount = balance * (risk_percent / 100.0)

            # Calculate risk in pips
            pip_size = self._get_pip_size(symbol)
            risk_pips = abs(entry_price - stop_loss) / pip_size

            if risk_pips <= 0:
                return self.min_lot_size

            # Calculate pip value
            pip_value = self._get_pip_value(symbol, balance)

            # Calculate lot size
            lot_size = risk_amount / (risk_pips * pip_value)

            # Apply limits
            lot_size = max(self.min_lot_size, min(lot_size, self.max_lot_size))

            # Round to appropriate decimal places
            lot_size = round(lot_size, 2)

            self.logger.debug(f"Calculated lot size for {symbol}: {lot_size}")

            return lot_size

        except Exception as e:
            self.logger.error(f"Error calculating lot size: {e}")
            return self.min_lot_size

    def calculate_position_value(self, symbol: str, lot_size: float) -> float:
        """Calculate position value in account currency"""
        try:
            # Get current price
            current_price = self.mt5_connector.get_current_price(symbol)
            if not current_price:
                return 0.0

            bid, ask = current_price
            price = (bid + ask) / 2

            # Standard lot size is 100,000 for most forex pairs
            contract_size = 100000
            if 'JPY' in symbol:
                contract_size = 100000
            elif 'XAU' in symbol:  # Gold
                contract_size = 100
            elif 'BTC' in symbol:  # Bitcoin
                contract_size = 1

            position_value = lot_size * contract_size * price

            return position_value

        except Exception as e:
            self.logger.error(f"Error calculating position value: {e}")
            return 0.0

    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        pip_sizes = {
            'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01,
            'USDCHF': 0.0001, 'AUDUSD': 0.0001, 'USDCAD': 0.0001,
            'NZDUSD': 0.0001, 'EURGBP': 0.0001, 'EURJPY': 0.01,
            'GBPJPY': 0.01, 'CHFJPY': 0.01, 'AUDJPY': 0.01,
            'XAUUSD': 0.1, 'XAGUSD': 0.001, 'BTCUSD': 1.0
        }
        return pip_sizes.get(symbol, 0.0001)

    def _get_pip_value(self, symbol: str, balance: float) -> float:
        """Get pip value in account currency"""
        try:
            # Simplified pip value calculation
            # In practice, this should consider account currency
            pip_values = {
                'EURUSD': 10.0, 'GBPUSD': 10.0, 'USDJPY': 10.0,
                'USDCHF': 10.0, 'AUDUSD': 10.0, 'USDCAD': 10.0,
                'NZDUSD': 10.0, 'EURGBP': 10.0, 'EURJPY': 10.0,
                'GBPJPY': 10.0, 'CHFJPY': 10.0, 'AUDJPY': 10.0,
                'XAUUSD': 1.0, 'XAGUSD': 5.0, 'BTCUSD': 0.1
            }
            return pip_values.get(symbol, 10.0)

        except Exception as e:
            self.logger.error(f"Error getting pip value: {e}")
            return 10.0

    def calculate_margin_required(self, symbol: str, lot_size: float) -> float:
        """Calculate margin required for position"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0

            # Get margin rate (leverage)
            margin_rate = symbol_info.get('margin_rate', 0.01)  # Default 1:100 leverage

            position_value = self.calculate_position_value(symbol, lot_size)
            margin_required = position_value * margin_rate

            return margin_required

        except Exception as e:
            self.logger.error(f"Error calculating margin: {e}")
            return 0.0

    def get_max_lot_size_for_symbol(self, symbol: str) -> float:
        """Get maximum allowed lot size for symbol"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return self.min_lot_size

            # Calculate based on available margin
            free_margin = account_info.get('margin_free', 0)
            margin_per_lot = self.calculate_margin_required(symbol, 1.0)

            if margin_per_lot > 0:
                max_lots = free_margin / margin_per_lot
                max_lots = min(max_lots, self.max_lot_size)
                return max(self.min_lot_size, max_lots)

            return self.min_lot_size

        except Exception as e:
            self.logger.error(f"Error calculating max lot size: {e}")
            return self.min_lot_size