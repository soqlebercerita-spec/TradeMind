"""
Main configuration file for AuraTrade Bot
Contains all system-wide settings and parameters
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from utils.logger import Logger

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class for AuraTrade Bot"""

    def __init__(self):
        # Trading configuration
        self.TRADING_CONFIG = {
            'DEFAULT_TIMEFRAME': 'M1',
            'MAX_POSITIONS': 10,
            'MAX_POSITIONS_PER_SYMBOL': 3,
            'DEFAULT_VOLUME': 0.01,
            'MIN_VOLUME': 0.01,
            'MAX_VOLUME': 1.0,
            'VOLUME_STEP': 0.01,
            'DEFAULT_TP_PIPS': 40,
            'DEFAULT_SL_PIPS': 20,
            'MAX_SPREAD_PIPS': 3.0,
            'ORDER_TIMEOUT': 30,
            'MAX_SLIPPAGE': 2,
        }

        # Risk management configuration
        self.RISK_CONFIG = {
            'MAX_RISK_PER_TRADE': 1.0,      # 1% per trade
            'MAX_DAILY_RISK': 5.0,          # 5% daily limit
            'MAX_DRAWDOWN': 10.0,           # 10% max drawdown
            'MIN_MARGIN_LEVEL': 200.0,      # 200% minimum margin
            'EMERGENCY_STOP_DRAWDOWN': 15.0, # 15% emergency stop
            'RISK_MANAGEMENT_ENABLED': True,
            'CONSERVATIVE_MODE': True,
        }

        # Strategy configuration
        self.STRATEGY_CONFIG = {
            'SCALPING_ENABLED': True,
            'HFT_ENABLED': True,
            'PATTERN_ENABLED': True,
            'SCALPING_TP_PIPS': 8,
            'SCALPING_SL_PIPS': 12,
            'HFT_TP_PIPS': 3,
            'HFT_SL_PIPS': 5,
            'PATTERN_TP_PIPS': 25,
            'PATTERN_SL_PIPS': 15,
            'MIN_CONFIDENCE': 0.65,
            'STRATEGY_TIMEOUT': 300,  # 5 minutes
        }

        # Data management configuration
        self.DATA_CONFIG = {
            'UPDATE_INTERVAL': 0.1,         # 100ms
            'HISTORY_BARS': 100,
            'TICK_HISTORY_SIZE': 1000,
            'CACHE_TIMEOUT': 60,            # 1 minute
            'DATA_CLEANUP_HOURS': 24,
            'ENABLE_DATA_VALIDATION': True,
        }

        # GUI configuration
        self.GUI_CONFIG = {
            'UPDATE_INTERVAL': 1000,        # 1 second
            'WINDOW_WIDTH': 1400,
            'WINDOW_HEIGHT': 900,
            'MIN_WIDTH': 1200,
            'MIN_HEIGHT': 800,
            'THEME': 'dark',
            'ENABLE_NOTIFICATIONS': True,
            'AUTO_SAVE_LOGS': True,
            'LOG_MAX_LINES': 1000,
        }

        # Logging configuration
        self.LOGGING_CONFIG = {
            'LEVEL': 'INFO',
            'FILE_LOGGING': True,
            'CONSOLE_LOGGING': True,
            'LOG_ROTATION': True,
            'MAX_LOG_SIZE_MB': 10,
            'BACKUP_COUNT': 5,
            'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'DATE_FORMAT': '%Y-%m-%d %H:%M:%S',
        }

        # Notification configuration
        self.NOTIFICATION_CONFIG = {
            'TELEGRAM_ENABLED': False,
            'EMAIL_ENABLED': False,
            'SOUND_ENABLED': True,
            'TRADE_NOTIFICATIONS': True,
            'SYSTEM_NOTIFICATIONS': True,
            'ERROR_NOTIFICATIONS': True,
            'PERFORMANCE_NOTIFICATIONS': True,
        }

        # Database/File paths
        self.PATHS = {
            'LOGS_DIR': 'AuraTrade/logs',
            'DATA_DIR': 'AuraTrade/data',
            'CONFIG_DIR': 'AuraTrade/config',
            'EXPORTS_DIR': 'AuraTrade/exports',
            'BACKUP_DIR': 'AuraTrade/backups',
        }

        # Trading sessions
        self.TRADING_SESSIONS = {
            'ASIAN': {'start': 0, 'end': 9},
            'LONDON': {'start': 8, 'end': 16},
            'NEW_YORK': {'start': 13, 'end': 22},
            'AVOID_HOURS': [0, 1, 2, 22, 23],
            'WEEKEND_TRADING': False,
        }

        # Symbol configurations
        self.SYMBOLS_CONFIG = {
            'MAJOR_PAIRS': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'],
            'MINOR_PAIRS': ['EURJPY', 'EURGBP', 'GBPJPY', 'AUDJPY'],
            'EXOTIC_PAIRS': ['EURTRY', 'USDMXN', 'USDZAR'],
            'METALS': ['XAUUSD', 'XAGUSD'],
            'CRYPTO': ['BTCUSD', 'ETHUSD'],
            'DEFAULT_SYMBOLS': ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'],
            'AUTO_DETECT_SYMBOLS': True,
        }

        # Performance targets
        self.PERFORMANCE_TARGETS = {
            'TARGET_WIN_RATE': 75.0,
            'TARGET_PROFIT_FACTOR': 2.0,
            'TARGET_SHARPE_RATIO': 1.5,
            'MAX_CONSECUTIVE_LOSSES': 5,
            'DAILY_PROFIT_TARGET': 2.0,  # 2% daily target
            'MONTHLY_PROFIT_TARGET': 20.0,  # 20% monthly target
        }

        # Create directories if they don't exist
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories"""
        for path in self.PATHS.values():
            os.makedirs(path, exist_ok=True)

    def get_config(self, section: str) -> Dict[str, Any]:
        """Get configuration section"""
        sections = {
            'trading': self.TRADING_CONFIG,
            'risk': self.RISK_CONFIG,
            'strategy': self.STRATEGY_CONFIG,
            'data': self.DATA_CONFIG,
            'gui': self.GUI_CONFIG,
            'logging': self.LOGGING_CONFIG,
            'notification': self.NOTIFICATION_CONFIG,
            'paths': self.PATHS,
            'sessions': self.TRADING_SESSIONS,
            'symbols': self.SYMBOLS_CONFIG,
            'performance': self.PERFORMANCE_TARGETS,
        }

        return sections.get(section, {})

    def update_config(self, section: str, key: str, value: Any):
        """Update configuration value"""
        sections = {
            'trading': self.TRADING_CONFIG,
            'risk': self.RISK_CONFIG,
            'strategy': self.STRATEGY_CONFIG,
            'data': self.DATA_CONFIG,
            'gui': self.GUI_CONFIG,
            'logging': self.LOGGING_CONFIG,
            'notification': self.NOTIFICATION_CONFIG,
            'sessions': self.TRADING_SESSIONS,
            'symbols': self.SYMBOLS_CONFIG,
            'performance': self.PERFORMANCE_TARGETS,
        }

        if section in sections and key in sections[section]:
            sections[section][key] = value
            return True
        return False

    def get_symbol_config(self, symbol: str) -> Dict[str, Any]:
        """Get symbol-specific configuration"""
        # Default configuration for all symbols
        symbol_config = {
            'enabled': True,
            'max_positions': 2,
            'max_spread': 3.0,
            'min_volume': 0.01,
            'max_volume': 1.0,
            'scalping_enabled': True,
            'hft_enabled': True,
            'pattern_enabled': True,
        }

        # Symbol-specific overrides
        overrides = {
            'EURUSD': {'max_spread': 2.0, 'hft_enabled': True},
            'GBPUSD': {'max_spread': 2.5, 'hft_enabled': True},
            'USDJPY': {'max_spread': 2.0, 'hft_enabled': True},
            'XAUUSD': {'max_spread': 5.0, 'max_volume': 0.5, 'hft_enabled': False},
            'BTCUSD': {'max_spread': 10.0, 'max_volume': 0.1, 'scalping_enabled': False},
        }

        if symbol in overrides:
            symbol_config.update(overrides[symbol])

        return symbol_config

    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed based on time/session"""
        from datetime import datetime

        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        # Check weekend trading
        if weekday == 6 and not self.TRADING_SESSIONS['WEEKEND_TRADING']:  # Sunday
            return False

        # Check avoid hours
        if hour in self.TRADING_SESSIONS['AVOID_HOURS']:
            return False

        # Check Friday close
        if weekday == 4 and hour >= 21:  # Friday after 9 PM
            return False

        return True

    def get_active_session(self) -> str:
        """Get current active trading session"""
        from datetime import datetime

        hour = datetime.now().hour

        for session, times in self.TRADING_SESSIONS.items():
            if isinstance(times, dict) and 'start' in times and 'end' in times:
                if times['start'] <= hour <= times['end']:
                    return session

        return 'CLOSED'

    def export_config(self, file_path: str = None):
        """Export configuration to file"""
        import json

        if file_path is None:
            file_path = os.path.join(self.PATHS['CONFIG_DIR'], 'exported_config.json')

        config_data = {
            'trading': self.TRADING_CONFIG,
            'risk': self.RISK_CONFIG,
            'strategy': self.STRATEGY_CONFIG,
            'data': self.DATA_CONFIG,
            'gui': self.GUI_CONFIG,
            'logging': self.LOGGING_CONFIG,
            'notification': self.NOTIFICATION_CONFIG,
            'sessions': self.TRADING_SESSIONS,
            'symbols': self.SYMBOLS_CONFIG,
            'performance': self.PERFORMANCE_TARGETS,
        }

        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=4)

    def import_config(self, file_path: str):
        """Import configuration from file"""
        import json

        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)

            # Update configurations
            for section, data in config_data.items():
                if hasattr(self, f"{section.upper()}_CONFIG"):
                    setattr(self, f"{section.upper()}_CONFIG", data)
                elif section.upper() in ['TRADING_SESSIONS', 'SYMBOLS_CONFIG', 'PERFORMANCE_TARGETS']:
                    setattr(self, section.upper(), data)

            return True
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False