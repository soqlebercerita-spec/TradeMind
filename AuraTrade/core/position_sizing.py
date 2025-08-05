"""
Position sizing and risk calculation for AuraTrade Bot
Implements percentage-based TP/SL instead of pip-based
"""

from typing import Optional, Tuple
from core.mt5_connector import MT5Connector
from core.risk_manager import RiskManager
from utils.logger import Logger

class PositionSizing:
    """Professional position sizing with percentage-based risk"""

    def __init__(self, mt5_connector: MT5Connector, risk_manager: RiskManager):
        self.mt5_connector = mt5_connector
        self.risk_manager = risk_manager
        self.logger = Logger().get_logger()

    def calculate_lot_size(self, symbol: str, entry_price: float, 
                          stop_loss: float, risk_percent: float = 1.0) -> float:
        """Calculate optimal lot size based on percentage risk"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0

            balance = account_info['balance']
            risk_amount = balance * (risk_percent / 100)

            # Calculate pip value
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0

            pip_size = 0.0001 if 'JPY' not in symbol else 0.01
            stop_loss_pips = abs(entry_price - stop_loss) / pip_size

            if stop_loss_pips == 0:
                return 0.0

            # Calculate lot size
            pip_value = 10  # $10 per pip for 1 lot in major pairs
            lot_size = risk_amount / (stop_loss_pips * pip_value)

            # Apply limits
            min_lot = symbol_info.get('volume_min', 0.01)
            max_lot = symbol_info.get('volume_max', 100.0)
            lot_step = symbol_info.get('volume_step', 0.01)

            # Round to lot step
            lot_size = round(lot_size / lot_step) * lot_step
            lot_size = max(min_lot, min(lot_size, max_lot))

            return lot_size

        except Exception as e:
            self.logger.error(f"Error calculating lot size: {e}")
            return 0.0

    def calculate_percentage_based_levels(self, symbol: str, entry_price: float, 
                                        direction: str, risk_percent: float = 1.0, 
                                        reward_ratio: float = 2.0) -> Tuple[float, float]:
        """Calculate TP/SL levels based on account balance percentage"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0, 0.0

            balance = account_info['balance']

            # Calculate risk amount in dollars
            risk_amount = balance * (risk_percent / 100)
            reward_amount = risk_amount * reward_ratio

            # Get symbol info for proper calculation
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0, 0.0

            # Calculate contract size and pip value
            contract_size = symbol_info.get('trade_contract_size', 100000)
            pip_size = 0.0001 if 'JPY' not in symbol else 0.01

            # Standard lot size for calculation
            standard_lot = 1.0
            pip_value = (pip_size * contract_size * standard_lot) / entry_price

            # Calculate required pips for risk/reward amounts
            risk_pips = risk_amount / pip_value
            reward_pips = reward_amount / pip_value

            # Calculate actual TP/SL prices
            if direction.lower() == 'buy':
                stop_loss = entry_price - (risk_pips * pip_size)
                take_profit = entry_price + (reward_pips * pip_size)
            else:  # sell
                stop_loss = entry_price + (risk_pips * pip_size)
                take_profit = entry_price - (reward_pips * pip_size)

            # Round to symbol digits
            digits = symbol_info.get('digits', 5)
            stop_loss = round(stop_loss, digits)
            take_profit = round(take_profit, digits)

            self.logger.info(f"Calculated levels for {symbol}: SL={stop_loss}, TP={take_profit}")

            return stop_loss, take_profit

        except Exception as e:
            self.logger.error(f"Error calculating percentage-based levels: {e}")
            return 0.0, 0.0

    def get_position_risk_percentage(self, symbol: str, volume: float, 
                                   entry_price: float, stop_loss: float) -> float:
        """Calculate actual risk percentage for a position"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0

            balance = account_info['balance']

            # Calculate pip difference
            pip_size = 0.0001 if 'JPY' not in symbol else 0.01
            pip_difference = abs(entry_price - stop_loss) / pip_size

            # Calculate monetary risk
            pip_value = 10 * volume  # $10 per pip per lot
            risk_amount = pip_difference * pip_value

            # Calculate percentage
            risk_percentage = (risk_amount / balance) * 100

            return risk_percentage

        except Exception as e:
            self.logger.error(f"Error calculating position risk percentage: {e}")
            return 0.0

    def validate_position_size(self, symbol: str, volume: float) -> bool:
        """Validate if position size is within limits"""
        try:
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return False

            min_lot = symbol_info.get('volume_min', 0.01)
            max_lot = symbol_info.get('volume_max', 100.0)
            lot_step = symbol_info.get('volume_step', 0.01)

            # Check minimum and maximum
            if volume < min_lot or volume > max_lot:
                return False

            # Check lot step compliance
            if (volume / lot_step) != int(volume / lot_step):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating position size: {e}")
            return False

    def get_max_position_size(self, symbol: str, risk_percent: float = 1.0) -> float:
        """Get maximum position size based on risk percentage"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return 0.0

            balance = account_info['balance']
            margin = account_info.get('margin', 0)
            free_margin = account_info.get('margin_free', balance)

            # Calculate maximum risk amount
            max_risk_amount = balance * (risk_percent / 100)

            # Consider available margin
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0

            # Get current price for margin calculation
            current_price = self.mt5_connector.get_current_price(symbol)
            if not current_price:
                return 0.0

            bid_price = current_price[0]

            # Calculate margin requirement per lot
            contract_size = symbol_info.get('trade_contract_size', 100000)
            margin_required = (contract_size * bid_price) / 100  # Assuming 1:100 leverage

            # Maximum lots based on margin
            max_lots_by_margin = free_margin / margin_required * 0.8  # 80% safety margin

            # Maximum lots based on risk
            # Assuming 50 pip stop loss for calculation
            pip_value = 10  # $10 per pip per lot
            assumed_stop_pips = 50
            max_lots_by_risk = max_risk_amount / (assumed_stop_pips * pip_value)

            # Take the smaller of the two
            max_lots = min(max_lots_by_margin, max_lots_by_risk)

            # Apply symbol limits
            max_symbol_lot = symbol_info.get('volume_max', 100.0)
            max_lots = min(max_lots, max_symbol_lot)

            # Round to lot step
            lot_step = symbol_info.get('volume_step', 0.01)
            max_lots = int(max_lots / lot_step) * lot_step

            return max(0.01, max_lots)  # Minimum 0.01 lot

        except Exception as e:
            self.logger.error(f"Error calculating max position size: {e}")
            return 0.01