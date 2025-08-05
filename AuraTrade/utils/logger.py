"""
Logging utility for AuraTrade Bot
Provides structured logging with file and console output
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys

class Logger:
    """Centralized logging system"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self.setup_logger()

    def setup_logger(self):
        """Initialize logger with file and console handlers"""
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Create logger
        self._logger = logging.getLogger('AuraTrade')
        self._logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        self._logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # File handler with rotation
        log_file = os.path.join(logs_dir, f'auratrade_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)

        # Fix encoding issues on Windows
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            except:
                pass

        # Error file handler
        error_file = os.path.join(logs_dir, f'auratrade_errors_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)

        # Add handlers to logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        self._logger.addHandler(error_handler)

        # Log initialization
        self._logger.info("Logger initialized successfully")

    def get_logger(self):
        """Get the logger instance"""
        return self._logger

    def log_trade(self, action: str, symbol: str, volume: float, price: float, result: str):
        """Special method for logging trades"""
        trade_msg = f"TRADE - {action}: {symbol} {volume} lots @ {price} - {result}"
        self._logger.info(trade_msg)

    def log_error_with_context(self, error: Exception, context: str):
        """Log error with additional context"""
        self._logger.error(f"ERROR in {context}: {str(error)}", exc_info=True)