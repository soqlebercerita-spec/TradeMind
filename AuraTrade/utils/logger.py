
"""
Logging utility for AuraTrade Bot
"""

import os
import logging
from datetime import datetime
from typing import Optional

class Logger:
    """Enhanced logging system for trading bot"""
    
    def __init__(self, name: str, log_dir: Optional[str] = None):
        self.name = name
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', 'logs')
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler for all logs
        log_file = os.path.join(self.log_dir, f"{name.lower()}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Daily rotating file handler for trading logs
        if 'trading' in name.lower() or 'engine' in name.lower():
            daily_log = os.path.join(self.log_dir, f"trading_{datetime.now().strftime('%Y%m%d')}.log")
            daily_handler = logging.FileHandler(daily_log)
            daily_handler.setLevel(logging.INFO)
            daily_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(daily_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def trade(self, action: str, symbol: str, volume: float, price: float, 
              tp: float = 0, sl: float = 0, comment: str = ""):
        """Log trading action"""
        message = f"TRADE | {action} | {symbol} | Vol:{volume} | Price:{price}"
        if tp > 0:
            message += f" | TP:{tp}"
        if sl > 0:
            message += f" | SL:{sl}"
        if comment:
            message += f" | {comment}"
        
        self.logger.info(message)
    
    def performance(self, metric: str, value: float, unit: str = ""):
        """Log performance metrics"""
        message = f"PERFORMANCE | {metric}: {value}{unit}"
        self.logger.info(message)
    
    def system(self, component: str, status: str, details: str = ""):
        """Log system status"""
        message = f"SYSTEM | {component}: {status}"
        if details:
            message += f" | {details}"
        self.logger.info(message)
"""
Logging utility for AuraTrade Bot
Provides structured logging with file and console output
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

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
"""
Advanced logging system for AuraTrade Bot
Implements multiple log levels and file rotation
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class Logger:
    """Professional logging system for AuraTrade"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        os.makedirs('AuraTrade/logs', exist_ok=True)
        
        # Create logger
        self._logger = logging.getLogger('AuraTrade')
        self._logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handlers
        info_handler = RotatingFileHandler(
            'AuraTrade/logs/auratrade.log', 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        info_handler.setLevel(logging.INFO)
        
        error_handler = RotatingFileHandler(
            'AuraTrade/logs/errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        
        trade_handler = RotatingFileHandler(
            'AuraTrade/logs/trades.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        trade_handler.setLevel(logging.INFO)
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Apply formatters
        console_handler.setFormatter(console_formatter)
        info_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        trade_handler.setFormatter(detailed_formatter)
        
        # Add handlers
        self._logger.addHandler(console_handler)
        self._logger.addHandler(info_handler)
        self._logger.addHandler(error_handler)
        
        # Add trade logger
        self.trade_logger = logging.getLogger('AuraTrade.Trades')
        self.trade_logger.addHandler(trade_handler)
    
    def get_logger(self):
        """Get main logger instance"""
        return self._logger
    
    def get_trade_logger(self):
        """Get trade-specific logger"""
        return self.trade_logger
    
    def log_trade(self, action, symbol, volume, price, sl=None, tp=None, profit=None):
        """Log trading activity"""
        trade_info = f"{action} | {symbol} | Vol: {volume} | Price: {price}"
        if sl:
            trade_info += f" | SL: {sl}"
        if tp:
            trade_info += f" | TP: {tp}"
        if profit is not None:
            trade_info += f" | P&L: ${profit:.2f}"
        
        self.trade_logger.info(trade_info)
