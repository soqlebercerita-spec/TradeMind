
"""
Settings management for AuraTrade Bot
Handles user preferences and trading parameters
"""

import json
import os
from typing import Dict, Any, Optional
from utils.logger import Logger

class Settings:
    """Settings management for AuraTrade Bot"""
    
    def __init__(self, settings_file: str = "AuraTrade/config/settings.json"):
        self.logger = Logger().get_logger()
        self.settings_file = settings_file
        self.settings = self._load_default_settings()
        self.load_settings()
        
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default settings"""
        return {
            'trading': {
                'auto_trading_enabled': False,
                'max_positions': 10,
                'max_positions_per_symbol': 3,
                'default_volume': 0.01,
                'default_tp_pips': 40,
                'default_sl_pips': 20,
                'max_spread_pips': 3.0,
                'trading_sessions_enabled': True,
                'weekend_trading': False,
                'news_filter_enabled': True,
            },
            'risk_management': {
                'risk_per_trade': 1.0,
                'max_daily_risk': 5.0,
                'max_drawdown': 10.0,
                'emergency_stop_enabled': True,
                'margin_level_threshold': 200.0,
                'conservative_mode': True,
            },
            'strategies': {
                'scalping_enabled': True,
                'hft_enabled': True,
                'pattern_enabled': True,
                'arbitrage_enabled': False,
                'swing_enabled': False,
                'strategy_allocation': {
                    'scalping': 40,
                    'hft': 30,
                    'pattern': 30
                }
            },
            'symbols': {
                'enabled_symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'],
                'auto_detect_symbols': True,
                'major_pairs_only': True,
                'include_metals': True,
                'include_crypto': False,
            },
            'gui': {
                'theme': 'dark',
                'update_interval': 1000,
                'show_notifications': True,
                'sound_alerts': True,
                'auto_save_logs': True,
                'chart_refresh_rate': 500,
                'window_size': {'width': 1400, 'height': 900},
                'always_on_top': False,
            },
            'notifications': {
                'telegram_enabled': False,
                'email_enabled': False,
                'desktop_enabled': True,
                'sound_enabled': True,
                'notify_trades': True,
                'notify_errors': True,
                'notify_system_status': True,
            },
            'data': {
                'update_interval_ms': 100,
                'history_bars': 100,
                'cache_timeout_minutes': 60,
                'enable_data_validation': True,
                'auto_cleanup_old_data': True,
            },
            'performance': {
                'target_win_rate': 75.0,
                'target_profit_factor': 2.0,
                'max_consecutive_losses': 5,
                'daily_profit_target': 2.0,
                'monthly_profit_target': 20.0,
            }
        }
    
    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    user_settings = json.load(f)
                    self._merge_settings(user_settings)
                self.logger.info("Settings loaded successfully")
                return True
            else:
                self.logger.info("No settings file found, using defaults")
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
    
    def _merge_settings(self, user_settings: Dict[str, Any]):
        """Merge user settings with defaults"""
        def merge_dict(default: dict, user: dict):
            for key, value in user.items():
                if key in default:
                    if isinstance(default[key], dict) and isinstance(value, dict):
                        merge_dict(default[key], value)
                    else:
                        default[key] = value
                else:
                    default[key] = value
        
        merge_dict(self.settings, user_settings)
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get setting value"""
        try:
            if key is None:
                return self.settings.get(section, default)
            return self.settings.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """Set setting value"""
        try:
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section][key] = value
            return True
        except Exception as e:
            self.logger.error(f"Error setting value: {e}")
            return False
    
    def get_trading_settings(self) -> Dict[str, Any]:
        """Get trading settings"""
        return self.settings.get('trading', {})
    
    def get_risk_settings(self) -> Dict[str, Any]:
        """Get risk management settings"""
        return self.settings.get('risk_management', {})
    
    def get_strategy_settings(self) -> Dict[str, Any]:
        """Get strategy settings"""
        return self.settings.get('strategies', {})
    
    def get_gui_settings(self) -> Dict[str, Any]:
        """Get GUI settings"""
        return self.settings.get('gui', {})
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        return self.settings.get('notifications', {})
    
    def get_enabled_symbols(self) -> list:
        """Get list of enabled trading symbols"""
        return self.settings.get('symbols', {}).get('enabled_symbols', ['EURUSD'])
    
    def is_strategy_enabled(self, strategy_name: str) -> bool:
        """Check if a strategy is enabled"""
        return self.settings.get('strategies', {}).get(f'{strategy_name}_enabled', False)
    
    def update_trading_setting(self, key: str, value: Any) -> bool:
        """Update trading setting"""
        return self.set('trading', key, value)
    
    def update_risk_setting(self, key: str, value: Any) -> bool:
        """Update risk management setting"""
        return self.set('risk_management', key, value)
    
    def enable_strategy(self, strategy_name: str, enabled: bool = True) -> bool:
        """Enable/disable a strategy"""
        return self.set('strategies', f'{strategy_name}_enabled', enabled)
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        try:
            self.settings = self._load_default_settings()
            self.save_settings()
            self.logger.info("Settings reset to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting settings: {e}")
            return False
    
    def export_settings(self, file_path: str) -> bool:
        """Export settings to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.info(f"Settings exported to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Import settings from file"""
        try:
            with open(file_path, 'r') as f:
                imported_settings = json.load(f)
            self._merge_settings(imported_settings)
            self.save_settings()
            self.logger.info(f"Settings imported from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return False
    
    def get_settings_summary(self) -> str:
        """Get formatted settings summary"""
        trading = self.get_trading_settings()
        risk = self.get_risk_settings()
        strategies = self.get_strategy_settings()
        
        summary = f"""
AuraTrade Bot Settings Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Trading Settings:
  • Auto Trading: {'✅ Enabled' if trading.get('auto_trading_enabled') else '❌ Disabled'}
  • Max Positions: {trading.get('max_positions', 'N/A')}
  • Default Volume: {trading.get('default_volume', 'N/A')}
  • TP/SL: {trading.get('default_tp_pips', 'N/A')}/{trading.get('default_sl_pips', 'N/A')} pips

⚠️ Risk Management:
  • Risk per Trade: {risk.get('risk_per_trade', 'N/A')}%
  • Max Daily Risk: {risk.get('max_daily_risk', 'N/A')}%
  • Max Drawdown: {risk.get('max_drawdown', 'N/A')}%
  • Conservative Mode: {'✅ On' if risk.get('conservative_mode') else '❌ Off'}

📈 Active Strategies:
  • Scalping: {'✅' if strategies.get('scalping_enabled') else '❌'}
  • HFT: {'✅' if strategies.get('hft_enabled') else '❌'}
  • Pattern: {'✅' if strategies.get('pattern_enabled') else '❌'}
  • Arbitrage: {'✅' if strategies.get('arbitrage_enabled') else '❌'}

💱 Symbols: {', '.join(self.get_enabled_symbols())}
        """
        return summary.strip()
"""
Settings Manager for AuraTrade Bot
Runtime settings and preferences
"""

import json
import os
from typing import Dict, Any, Optional
from utils.logger import Logger

class Settings:
    """Runtime settings manager"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.settings_file = "settings.json"
        self.settings = self._load_settings()
        self.logger.info("Settings loaded")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        default_settings = {
            'gui': {
                'theme': 'dark',
                'window_width': 1400,
                'window_height': 900,
                'auto_update_interval': 1000
            },
            'trading': {
                'auto_start': False,
                'default_strategy': 'scalping',
                'default_symbol': 'EURUSD',
                'default_lot_size': 0.01
            },
            'notifications': {
                'telegram_enabled': False,
                'sound_enabled': True,
                'trade_notifications': True,
                'system_notifications': True
            },
            'advanced': {
                'debug_mode': False,
                'log_trades': True,
                'backup_enabled': True,
                'auto_save_interval': 300
            }
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults
                    self._merge_settings(default_settings, loaded_settings)
                    return default_settings
            except Exception as e:
                self.logger.error(f"Error loading settings: {e}")
        
        return default_settings
    
    def _merge_settings(self, default: Dict, loaded: Dict):
        """Recursively merge loaded settings with defaults"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
    
    def get(self, key: str, default=None):
        """Get setting value"""
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set setting value"""
        keys = key.split('.')
        settings = self.settings
        
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        settings[keys[-1]] = value
        self.save()
    
    def save(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def reset_to_defaults(self):
        """Reset settings to defaults"""
        if os.path.exists(self.settings_file):
            os.remove(self.settings_file)
        self.settings = self._load_settings()
        self.save()
        self.logger.info("Settings reset to defaults")
    
    def get_gui_settings(self) -> Dict[str, Any]:
        """Get GUI settings"""
        return self.settings.get('gui', {})
    
    def get_trading_settings(self) -> Dict[str, Any]:
        """Get trading settings"""
        return self.settings.get('trading', {})
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        return self.settings.get('notifications', {})
