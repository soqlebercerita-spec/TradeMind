
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
        try:
            msg = msg.encode('ascii', errors='replace').decode('ascii')
        except:
            msg = repr(msg)

        return msg

class Logger:
    """Thread-safe logger with Windows compatibility"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with safe configuration"""
        # Create logs directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure main logger
        self.logger = logging.getLogger('AuraTrade')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with safe formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = SafeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with safe encoding
        log_file = os.path.join(log_dir, f'auratrade_{datetime.now().strftime("%Y%m%d")}.log')
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8', errors='replace')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = SafeFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
    def get_logger(self):
        """Get the configured logger"""
        return self.logger

# Convenience functions for easy logging
def log_info(component: str, message: str):
    """Log info message with component prefix"""
    logger = Logger().get_logger()
    logger.info(f"[{component}] {message}")

def log_error(component: str, message: str, exception: Optional[Exception] = None):
    """Log error message with component prefix"""
    logger = Logger().get_logger()
    if exception:
        logger.error(f"[{component}] {message}: {str(exception)}")
    else:
        logger.error(f"[{component}] {message}")

def log_warning(component: str, message: str):
    """Log warning message with component prefix"""
    logger = Logger().get_logger()
    logger.warning(f"[{component}] {message}")

def log_debug(component: str, message: str):
    """Log debug message with component prefix"""
    logger = Logger().get_logger()
    logger.debug(f"[{component}] {message}")

def log_trade(action: str, symbol: str, details: str):
    """Log trading activity"""
    logger = Logger().get_logger()
    logger.info(f"[TRADE] {action} {symbol} - {details}")
