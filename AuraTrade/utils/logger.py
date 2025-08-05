
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
