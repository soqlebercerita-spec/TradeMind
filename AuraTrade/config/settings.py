
"""
Settings Module for AuraTrade Bot
User-configurable settings and preferences
"""

import os
import json
from typing import Dict, Any, List
from utils.logger import Logger

class Settings:
    """User settings and preferences manager"""
    
    def __init__(self, settings_file: str = "AuraTrade/config/user_settings.json"):
        self.logger = Logger().get_logger()
        self.settings_file = settings_file
        self.settings = self._load_default_settings()
        self.load_settings()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default settings"""
        return {
            'trading': {
                'default_symbol': 'EURUSD',
                'default_lot_size': 0.01,
                'max_open_trades': 10,
                'scalping_tp_pips': 8,
                'scalping_sl_pips': 12,
                'general_tp_pips': 40,
                'general_sl_pips': 20,
                'tp_type': 'pips',  # 'pips', 'price', 'percent'
                'sl_type': 'pips',  # 'pips', 'price', 'percent'
                'auto_close_profit_percent': 10.0,
                'max_daily_loss_percent': 5.0,
                'max_drawdown_percent': 5.0,
            },
            'strategies': {
                'active_strategy': 'scalping',
                'scalping_enabled': True,
                'intraday_enabled': True,
                'arbitrage_enabled': True,
                'hft_enabled': True,
            },
            'gui': {
                'theme': 'dark',
                'auto_refresh_interval': 1000,
                'show_notifications': True,
                'save_window_position': True,
                'window_width': 1400,
                'window_height': 900,
            },
            'notifications': {
                'telegram_enabled': False,
                'telegram_token': '',
                'telegram_chat_id': '',
                'notify_on_start': True,
                'notify_on_trade': True,
                'notify_on_stop': True,
                'notify_on_error': True,
            },
            'logging': {
                'log_level': 'INFO',
                'export_trades_csv': True,
                'daily_summary': True,
                'separate_buy_sell_files': True,
            }
        }
    
    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._merge_settings(self.settings, loaded_settings)
                self.logger.info("Settings loaded successfully")
                return True
            else:
                self.save_settings()  # Create default settings file
                return True
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Save settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.info("Settings saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False
    
    def _merge_settings(self, defaults: Dict, loaded: Dict):
        """Recursively merge loaded settings with defaults"""
        for key, value in loaded.items():
            if key in defaults:
                if isinstance(value, dict) and isinstance(defaults[key], dict):
                    self._merge_settings(defaults[key], value)
                else:
                    defaults[key] = value
    
    def get(self, section: str, key: str = None) -> Any:
        """Get setting value"""
        if key is None:
            return self.settings.get(section, {})
        return self.settings.get(section, {}).get(key)
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """Set setting value"""
        try:
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section][key] = value
            return self.save_settings()
        except Exception as e:
            self.logger.error(f"Error setting {section}.{key}: {e}")
            return False
    
    def get_trading_settings(self) -> Dict[str, Any]:
        """Get all trading settings"""
        return self.settings.get('trading', {})
    
    def get_strategy_settings(self) -> Dict[str, Any]:
        """Get all strategy settings"""
        return self.settings.get('strategies', {})
    
    def get_gui_settings(self) -> Dict[str, Any]:
        """Get all GUI settings"""
        return self.settings.get('gui', {})
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get all notification settings"""
        return self.settings.get('notifications', {})
    
    def calculate_tp_sl_values(self, symbol: str, action: str, current_price: float, 
                              tp_value: float, sl_value: float, tp_type: str, sl_type: str, 
                              lot_size: float = 0.01) -> Dict[str, Any]:
        """Calculate TP/SL values in different formats"""
        try:
            # Mock symbol info for calculation
            point = 0.00001 if 'JPY' not in symbol else 0.001
            if 'XAU' in symbol or 'XAG' in symbol:
                point = 0.01
            
            pip_value = 10 * lot_size if 'JPY' not in symbol else lot_size
            if 'XAU' in symbol:
                pip_value = lot_size
            
            result = {
                'tp_price': 0.0,
                'sl_price': 0.0,
                'tp_pips': 0.0,
                'sl_pips': 0.0,
                'tp_profit_usd': 0.0,
                'sl_loss_usd': 0.0,
                'tp_profit_percent': 0.0,
                'sl_loss_percent': 0.0
            }
            
            # Calculate TP
            if tp_type == 'pips':
                tp_pips = tp_value
                if action.lower() == 'buy':
                    tp_price = current_price + (tp_pips * point)
                else:
                    tp_price = current_price - (tp_pips * point)
            elif tp_type == 'price':
                tp_price = tp_value
                tp_pips = abs(tp_price - current_price) / point
            else:  # percent
                profit_amount = (tp_value / 100) * 10000  # Assuming $10,000 balance
                tp_pips = profit_amount / pip_value
                if action.lower() == 'buy':
                    tp_price = current_price + (tp_pips * point)
                else:
                    tp_price = current_price - (tp_pips * point)
            
            # Calculate SL
            if sl_type == 'pips':
                sl_pips = sl_value
                if action.lower() == 'buy':
                    sl_price = current_price - (sl_pips * point)
                else:
                    sl_price = current_price + (sl_pips * point)
            elif sl_type == 'price':
                sl_price = sl_value
                sl_pips = abs(current_price - sl_price) / point
            else:  # percent
                loss_amount = (sl_value / 100) * 10000  # Assuming $10,000 balance
                sl_pips = loss_amount / pip_value
                if action.lower() == 'buy':
                    sl_price = current_price - (sl_pips * point)
                else:
                    sl_price = current_price + (sl_pips * point)
            
            # Calculate profit/loss in USD and percent
            result.update({
                'tp_price': tp_price,
                'sl_price': sl_price,
                'tp_pips': tp_pips,
                'sl_pips': sl_pips,
                'tp_profit_usd': tp_pips * pip_value,
                'sl_loss_usd': sl_pips * pip_value,
                'tp_profit_percent': (tp_pips * pip_value) / 10000 * 100,
                'sl_loss_percent': (sl_pips * pip_value) / 10000 * 100
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating TP/SL values: {e}")
            return result
