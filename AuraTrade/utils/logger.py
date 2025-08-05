
"""
Logging utility for AuraTrade Bot
Fixed for Windows Unicode compatibility
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

class Logger:
    """Centralized logging system with Unicode support"""

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
        """Initialize logger with Unicode-safe handlers"""
        # Create logs directory
        logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Create logger
        self._logger = logging.getLogger('AuraTrade')
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()

        # Create formatters (Unicode-safe)
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler with UTF-8 encoding
        log_file = os.path.join(logs_dir, f'auratrade_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Set encoding for console
        if hasattr(console_handler.stream, 'reconfigure'):
            try:
                console_handler.stream.reconfigure(encoding='utf-8')
            except Exception:
                pass

        # Error file handler
        error_file = os.path.join(logs_dir, f'auratrade_errors_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)

        # Add handlers
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        self._logger.addHandler(error_handler)

        # Log initialization (no emoji to avoid Unicode issues)
        self._logger.info("Logger initialized successfully")

    def get_logger(self):
        """Get the logger instance"""
        return self._logger

    def log_trade(self, action: str, symbol: str, volume: float, price: float, result: str):
        """Log trade actions"""
        trade_msg = f"TRADE - {action}: {symbol} {volume} lots @ {price} - {result}"
        self._logger.info(trade_msg)

    def log_error_with_context(self, error: Exception, context: str):
        """Log error with context"""
        self._logger.error(f"ERROR in {context}: {str(error)}", exc_info=True)

    def safe_log(self, level: str, message: str):
        """Unicode-safe logging method"""
        try:
            # Remove or replace problematic Unicode characters
            safe_message = str(message).encode('ascii', 'ignore').decode('ascii')
            getattr(self._logger, level.lower())(safe_message)
        except Exception as e:
            self._logger.error(f"Logging error: {e}")
