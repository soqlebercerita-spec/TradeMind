"""
Logging utilities for AuraTrade Bot
Enhanced logging with trade tracking and system monitoring
"""

import logging
import colorlog
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Create logs directory
os.makedirs('logs', exist_ok=True)

class Logger:
    """Enhanced logger with color output and file logging"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger('AuraTrade')
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler with colors
        console_handler = colorlog.StreamHandler()
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(
            f'logs/auratrade_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Trade logger
        self.trade_logger = logging.getLogger('AuraTrade.Trades')
        trade_handler = logging.FileHandler(
            f'logs/trades_{datetime.now().strftime("%Y%m%d")}.log'
        )
        trade_handler.setFormatter(file_formatter)
        self.trade_logger.addHandler(trade_handler)
        self.trade_logger.setLevel(logging.INFO)

        self._initialized = True

    def get_logger(self):
        """Get main logger instance"""
        return self.logger

    def get_trade_logger(self):
        """Get trade logger instance"""
        return self.trade_logger

def log_trade(action: str, symbol: str, volume: float, price: float, **kwargs):
    """Log trade execution"""
    logger = Logger().get_trade_logger()
    trade_info = f"TRADE | {action.upper()} {volume} {symbol} @ {price:.5f}"

    if kwargs:
        extras = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
        trade_info += f" | {extras}"

    logger.info(trade_info)

def log_error(message: str, **kwargs):
    """Log error with context"""
    logger = Logger().get_logger()
    if kwargs:
        extras = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
        message += f" | {extras}"

    logger.error(message)

def log_system(message: str, level: str = "info"):
    """Log system events"""
    logger = Logger().get_logger()
    if level.lower() == "warning":
        logger.warning(f"SYSTEM | {message}")
    elif level.lower() == "error":
        logger.error(f"SYSTEM | {message}")
    else:
        logger.info(f"SYSTEM | {message}")
"""
Logger utility for AuraTrade Bot
Centralized logging with different levels and file output
"""

import logging
import os
from datetime import datetime
from typing import Optional

class Logger:
    """Centralized logger for AuraTrade Bot"""
    
    def __init__(self):
        self.logger = None
        self.setup_logger()
    
    def setup_logger(self):
        """Setup logger with file and console handlers"""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("AuraTrade")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        log_filename = f"logs/auratrade_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Get logger instance"""
        return self.logger

# Global logger functions
def log_trade(action: str, symbol: str, volume: float, price: float):
    """Log trade execution"""
    logger = Logger().get_logger()
    logger.info(f"TRADE: {action.upper()} {volume} {symbol} @ {price:.5f}")

def log_error(message: str):
    """Log error message"""
    logger = Logger().get_logger()
    logger.error(f"ERROR: {message}")

def log_system(message: str):
    """Log system message"""
    logger = Logger().get_logger()
    logger.info(f"SYSTEM: {message}")
