"""
Position Sizing System for AuraTrade Bot
Advanced position sizing with multiple algorithms
"""

import math
import numpy as np
from typing import Dict, Optional, Any
from enum import Enum
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class SizingMethod(Enum):
    FIXED = "fixed"
    PERCENT_RISK = "percent_risk"
    KELLY = "kelly"
    VOLATILITY = "volatility"
    MARTINGALE = "martingale"
    ANTI_MARTINGALE = "anti_martingale"

class PositionSizing:
    """Advanced position sizing calculator"""

    def __init__(self, mt5_connector: MT5Connector):
        self.mt5 = mt5_connector
        self.logger = Logger().get_logger()

        # Default settings
        self.method = SizingMethod.PERCENT_RISK
        self.default_risk_percent = 1.0
        self.min_lot_size = 0.01
        self.max_lot_size = 10.0
        self.kelly_lookback = 50
        self.volatility_period = 20

        self.logger.info("PositionSizing initialized")

    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: float, method: SizingMethod = None,
                              risk_percent: float = None) -> float:
        """Calculate optimal position size"""
        try:
            if method is None:
                method = self.method

            if risk_percent is None:
                risk_percent = self.default_risk_percent

            if method == SizingMethod.FIXED:
                return self._fixed_sizing(symbol)
            elif method == SizingMethod.PERCENT_RISK:
                return self._percent_risk_sizing(symbol, entry_price, stop_loss, risk_percent)
            elif method == SizingMethod.KELLY:
                return self._kelly_sizing(symbol, entry_price, stop_loss)
            elif method == SizingMethod.VOLATILITY:
                return self._volatility_sizing(symbol, risk_percent)
            elif method == SizingMethod.MARTINGALE:
                return self._martingale_sizing(symbol, risk_percent)
            elif method == SizingMethod.ANTI_MARTINGALE:
                return self._anti_martingale_sizing(symbol, risk_percent)
            else:
                return self._percent_risk_sizing(symbol, entry_price, stop_loss, risk_percent)

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return self.min_lot_size

    def _fixed_sizing(self, symbol: str) -> float:
        """Fixed lot size"""
        return 0.01

    def _percent_risk_sizing(self, symbol: str, entry_price: float, 
                           stop_loss: float, risk_percent: float) -> float:
        """Position sizing based on percent risk"""
        try:
            account_info = self.mt5.get_account_info()
            if not account_info:
                return self.min_lot_size

            balance = account_info['balance']
            risk_amount = balance * (risk_percent / 100)

            # Calculate risk per unit
            risk_per_pip = abs(entry_price - stop_loss)
            if risk_per_pip <= 0:
                return self.min_lot_size

            # Get symbol info
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return self.min_lot_size

            # Calculate pip value
            pip_value = self._calculate_pip_value(symbol, 1.0)
            if pip_value <= 0:
                return self.min_lot_size

            # Convert price difference to pips
            digits = symbol_info['digits']
            point = symbol_info['point']

            if digits == 5 or digits == 3:
                pips = risk_per_pip / (point * 10)
            else:
                pips = risk_per_pip / point

            # Calculate lot size
            lot_size = risk_amount / (pips * pip_value)

            return self._normalize_lot_size(symbol, lot_size)

        except Exception as e:
            self.logger.error(f"Error in percent risk sizing: {e}")
            return self.min_lot_size

    def _kelly_sizing(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        """Kelly criterion position sizing"""
        try:
            # Get recent trade history to calculate win rate and avg win/loss
            history = self.mt5.get_order_history(days=30)

            if len(history) < 10:  # Not enough data
                return self._percent_risk_sizing(symbol, entry_price, stop_loss, 1.0)

            wins = [trade for trade in history if trade.get('profit', 0) > 0]
            losses = [trade for trade in history if trade.get('profit', 0) < 0]

            if not wins or not losses:
                return self._percent_risk_sizing(symbol, entry_price, stop_loss, 1.0)

            win_rate = len(wins) / len(history)
            avg_win = np.mean([trade['profit'] for trade in wins])
            avg_loss = abs(np.mean([trade['profit'] for trade in losses]))

            if avg_loss <= 0:
                return self.min_lot_size

            # Kelly formula: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate

            kelly_fraction = (b * p - q) / b

            # Apply Kelly fraction (limited to max 25% for safety)
            kelly_fraction = max(0, min(0.25, kelly_fraction))

            # Convert to lot size
            account_info = self.mt5.get_account_info()
            if not account_info:
                return self.min_lot_size

            balance = account_info['balance']
            risk_amount = balance * kelly_fraction

            # Calculate lot size based on stop loss
            risk_pips = abs(entry_price - stop_loss)
            pip_value = self._calculate_pip_value(symbol, 1.0)

            if risk_pips > 0 and pip_value > 0:
                symbol_info = self.mt5.get_symbol_info(symbol)
                if symbol_info:
                    digits = symbol_info['digits']
                    point = symbol_info['point']

                    if digits == 5 or digits == 3:
                        pips = risk_pips / (point * 10)
                    else:
                        pips = risk_pips / point

                    lot_size = risk_amount / (pips * pip_value)
                    return self._normalize_lot_size(symbol, lot_size)

            return self.min_lot_size

        except Exception as e:
            self.logger.error(f"Error in Kelly sizing: {e}")
            return self.min_lot_size

    def _volatility_sizing(self, symbol: str, risk_percent: float) -> float:
        """Volatility-based position sizing"""
        try:
            # Get historical data
            rates = self.mt5.get_rates(symbol, 'H1', self.volatility_period * 24)
            if rates is None or len(rates) < self.volatility_period:
                return self._percent_risk_sizing(symbol, 0, 0, risk_percent)

            # Calculate volatility (ATR)
            high_low = rates['high'] - rates['low']
            high_close = abs(rates['high'] - rates['close'].shift(1))
            low_close = abs(rates['low'] - rates['close'].shift(1))

            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=self.volatility_period).mean().iloc[-1]

            if np.isnan(atr) or atr <= 0:
                return self.min_lot_size

            # Adjust position size based on volatility
            # Higher volatility = smaller position
            base_volatility = 0.001  # Base volatility assumption
            volatility_ratio = base_volatility / atr

            # Calculate base position size
            account_info = self.mt5.get_account_info()
            if not account_info:
                return self.min_lot_size

            balance = account_info['balance']
            base_risk = balance * (risk_percent / 100)

            # Adjust for volatility
            adjusted_lot_size = (base_risk * volatility_ratio) / 1000  # Simplified calculation

            return self._normalize_lot_size(symbol, adjusted_lot_size)

        except Exception as e:
            self.logger.error(f"Error in volatility sizing: {e}")
            return self.min_lot_size

    def _martingale_sizing(self, symbol: str, risk_percent: float) -> float:
        """Martingale position sizing (increase after losses)"""
        try:
            # Get recent trades
            history = self.mt5.get_order_history(days=7)

            if not history:
                return self._percent_risk_sizing(symbol, 0, 0, risk_percent)

            # Count consecutive losses
            consecutive_losses = 0
            for trade in reversed(history):  # Most recent first
                if trade.get('profit', 0) < 0:
                    consecutive_losses += 1
                else:
                    break

            # Increase size based on consecutive losses (limited for safety)
            multiplier = min(2 ** consecutive_losses, 4)  # Max 4x
            base_size = self._percent_risk_sizing(symbol, 0, 0, risk_percent)

            return self._normalize_lot_size(symbol, base_size * multiplier)

        except Exception as e:
            self.logger.error(f"Error in Martingale sizing: {e}")
            return self.min_lot_size

    def _anti_martingale_sizing(self, symbol: str, risk_percent: float) -> float:
        """Anti-Martingale position sizing (increase after wins)"""
        try:
            # Get recent trades
            history = self.mt5.get_order_history(days=7)

            if not history:
                return self._percent_risk_sizing(symbol, 0, 0, risk_percent)

            # Count consecutive wins
            consecutive_wins = 0
            for trade in reversed(history):  # Most recent first
                if trade.get('profit', 0) > 0:
                    consecutive_wins += 1
                else:
                    break

            # Increase size based on consecutive wins (limited for safety)
            multiplier = min(1 + (consecutive_wins * 0.2), 2)  # Max 2x
            base_size = self._percent_risk_sizing(symbol, 0, 0, risk_percent)

            return self._normalize_lot_size(symbol, base_size * multiplier)

        except Exception as e:
            self.logger.error(f"Error in Anti-Martingale sizing: {e}")
            return self.min_lot_size

    def _calculate_pip_value(self, symbol: str, volume: float) -> float:
        """Calculate pip value"""
        try:
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0

            contract_size = symbol_info['trade_contract_size']
            point = symbol_info['point']
            digits = symbol_info['digits']

            # Calculate pip size
            if digits == 5 or digits == 3:
                pip_size = point * 10
            else:
                pip_size = point

            # Calculate pip value
            pip_value = volume * contract_size * pip_size

            return pip_value

        except Exception as e:
            self.logger.error(f"Error calculating pip value: {e}")
            return 0.0

    def _normalize_lot_size(self, symbol: str, lot_size: float) -> float:
        """Normalize lot size to symbol requirements"""
        try:
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return self.min_lot_size

            min_lot = symbol_info['volume_min']
            max_lot = symbol_info['volume_max']
            lot_step = symbol_info['volume_step']

            # Ensure within bounds
            lot_size = max(min_lot, min(max_lot, lot_size))
            lot_size = max(self.min_lot_size, min(self.max_lot_size, lot_size))

            # Round to lot step
            if lot_step > 0:
                lot_size = round(lot_size / lot_step) * lot_step

            return round(lot_size, 2)

        except Exception as e:
            self.logger.error(f"Error normalizing lot size: {e}")
            return self.min_lot_size

    def get_sizing_recommendation(self, symbol: str, strategy: str = "balanced") -> Dict[str, Any]:
        """Get position sizing recommendations"""
        try:
            recommendations = {}

            # Get symbol info
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return recommendations

            current_price = (symbol_info['bid'] + symbol_info['ask']) / 2

            # Different strategies
            if strategy == "conservative":
                methods = [SizingMethod.FIXED, SizingMethod.PERCENT_RISK]
                risk_percents = [0.5, 1.0]
            elif strategy == "aggressive":
                methods = [SizingMethod.KELLY, SizingMethod.VOLATILITY, SizingMethod.ANTI_MARTINGALE]
                risk_percents = [2.0, 3.0]
            else:  # balanced
                methods = [SizingMethod.PERCENT_RISK, SizingMethod.VOLATILITY]
                risk_percents = [1.0, 1.5]

            # Calculate recommendations
            for method in methods:
                for risk_pct in risk_percents:
                    key = f"{method.value}_{risk_pct}%"

                    # Use reasonable stop loss for calculation
                    stop_loss = current_price * 0.98 if method != SizingMethod.FIXED else 0

                    lot_size = self.calculate_position_size(
                        symbol, current_price, stop_loss, method, risk_pct
                    )

                    recommendations[key] = {
                        'method': method.value,
                        'risk_percent': risk_pct,
                        'lot_size': lot_size,
                        'risk_amount': self._calculate_risk_amount(symbol, lot_size, current_price, stop_loss)
                    }

            return recommendations

        except Exception as e:
            self.logger.error(f"Error getting sizing recommendations: {e}")
            return {}

    def _calculate_risk_amount(self, symbol: str, lot_size: float, 
                              entry_price: float, stop_loss: float) -> float:
        """Calculate risk amount in account currency"""
        try:
            if stop_loss <= 0:
                return 0.0

            price_diff = abs(entry_price - stop_loss)
            pip_value = self._calculate_pip_value(symbol, lot_size)

            symbol_info = self.mt5.get_symbol_info(symbol)
            if symbol_info:
                digits = symbol_info['digits']
                point = symbol_info['point']

                if digits == 5 or digits == 3:
                    pips = price_diff / (point * 10)
                else:
                    pips = price_diff / point

                return pips * pip_value

            return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating risk amount: {e}")
            return 0.0