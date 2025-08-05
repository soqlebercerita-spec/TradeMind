"""
Safe Windows-compatible logging system for AuraTrade Bot
Handles Unicode issues and provides structured logging
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional
import threading

class SafeFormatter(logging.Formatter):
    """Safe formatter that handles Unicode issues on Windows"""

    def format(self, record):
        # Remove emojis and special characters that cause encoding issues
        msg = super().format(record)

        # Replace problematic characters
        replacements = {
            '🚀': '[START]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '📊': '[DATA]',
            '💰': '[TRADE]',
            '🔄': '[UPDATE]',
            '📈': '[PROFIT]',
            '📉': '[LOSS]',
            '🎯': '[TARGET]',
            '⏰': '[TIME]',
            '🔍': '[SEARCH]',
            '💡': '[INFO]',
            '🛡️': '[SHIELD]',
            '🔧': '[FIX]',
            '📢': '[ALERT]'
        }

        for emoji, replacement in replacements.items():
            msg = msg.replace(emoji, replacement)

        # Ensure ASCII-safe output
        msg = msg.encode('ascii', errors='replace').decode('ascii')

        return msg

class Logger:
    """Thread-safe logger for AuraTrade Bot"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.logger = None
        self._setup_logger()

    def _setup_logger(self):
        """Setup logging configuration"""
        try:
            # Create logs directory
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)

            # Configure logger
            self.logger = logging.getLogger('AuraTrade')
            self.logger.setLevel(logging.INFO)

            # Clear existing handlers
            self.logger.handlers.clear()

            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # File handler
            log_file = os.path.join(log_dir, f'auratrade_{datetime.now().strftime("%Y%m%d")}.log')
            file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
            file_handler.setLevel(logging.DEBUG)

            # Safe formatter
            formatter = SafeFormatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

            # Prevent propagation to root logger
            self.logger.propagate = False

            self.logger.info("Logger initialized successfully")

        except Exception as e:
            print(f"Failed to setup logger: {e}")
            # Fallback to basic console logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.logger = logging.getLogger('AuraTrade')

    def get_logger(self):
        """Get the configured logger instance"""
        return self.logger

    @classmethod
    def get_instance(cls):
        """Get singleton logger instance"""
        return cls().get_logger()

# Module-level convenience functions
def get_logger(name: Optional[str] = None):
    """Get logger instance with optional name"""
    logger = Logger().get_logger()
    if name:
        return logger.getChild(name)
    return logger

def log_trade(action: str, symbol: str, volume: float, price: float, profit: float = 0.0):
    """Log trading activity"""
    logger = get_logger("TRADE")
    logger.info(f"{action.upper()} {volume} {symbol} @ {price:.5f} | P&L: ${profit:.2f}")

def log_error(component: str, message: str, exception: Exception = None):
    """Log error with component context"""
    logger = get_logger(component)
    if exception:
        logger.error(f"{message}: {str(exception)}")
    else:
        logger.error(message)

def log_system(message: str, level: str = "INFO"):
    """Log system message"""
    logger = get_logger("SYSTEM")
    if level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)