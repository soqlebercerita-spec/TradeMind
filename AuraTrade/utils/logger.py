
"""
UTF-8 compatible logging system for AuraTrade Bot
Handles Windows Unicode issues and provides structured logging
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
import codecs

class Logger:
    """UTF-8 compatible logger with Windows support"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with UTF-8 support"""
        try:
            # Create logs directory
            log_dir = Path("AuraTrade/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure root logger
            self._logger = logging.getLogger('AuraTrade')
            self._logger.setLevel(logging.DEBUG)
            
            # Clear any existing handlers
            self._logger.handlers.clear()
            
            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            simple_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%H:%M:%S'
            )
            
            # File handler with UTF-8 encoding
            log_file = log_dir / f"auratrade_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(
                log_file, 
                mode='a', 
                encoding='utf-8',
                delay=True
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            
            # Rotating file handler for error logs
            error_log_file = log_dir / "auratrade_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            
            # Console handler with UTF-8 support
            if sys.platform.startswith('win'):
                # Windows UTF-8 console setup
                try:
                    # Try to set console to UTF-8
                    import subprocess
                    subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
                except:
                    pass
                
                # Use custom stream handler for Windows
                console_handler = logging.StreamHandler(sys.stdout)
            else:
                # Unix/Linux
                console_handler = logging.StreamHandler(sys.stdout)
            
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            
            # Add handlers to logger
            self._logger.addHandler(file_handler)
            self._logger.addHandler(error_handler)
            self._logger.addHandler(console_handler)
            
            # Test logging
            self._logger.info("AuraTrade Logger initialized successfully ✅")
            self._logger.info(f"Log file: {log_file}")
            self._logger.info(f"Error log: {error_log_file}")
            
        except Exception as e:
            # Fallback to basic logging if setup fails
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s | %(levelname)s | %(message)s'
            )
            self._logger = logging.getLogger('AuraTrade')
            self._logger.error(f"Failed to setup advanced logger: {e}")
    
    def get_logger(self):
        """Get the configured logger instance"""
        return self._logger
    
    def log_trade_event(self, event_type: str, symbol: str, action: str, 
                       volume: float, price: float, profit: float = 0):
        """Log trading events with structured format"""
        try:
            message = f"TRADE_{event_type.upper()} | {symbol} | {action} | Vol:{volume:.2f} | Price:{price:.5f}"
            if profit != 0:
                profit_emoji = "📈" if profit > 0 else "📉"
                message += f" | P&L:{profit:+.2f} {profit_emoji}"
            
            self._logger.info(message)
            
        except Exception as e:
            self._logger.error(f"Error logging trade event: {e}")
    
    def log_system_event(self, event_type: str, message: str, level: str = "INFO"):
        """Log system events"""
        try:
            formatted_message = f"SYSTEM_{event_type.upper()} | {message}"
            
            if level.upper() == "ERROR":
                self._logger.error(formatted_message)
            elif level.upper() == "WARNING":
                self._logger.warning(formatted_message)
            elif level.upper() == "DEBUG":
                self._logger.debug(formatted_message)
            else:
                self._logger.info(formatted_message)
                
        except Exception as e:
            self._logger.error(f"Error logging system event: {e}")
    
    def log_performance_metrics(self, metrics: dict):
        """Log performance metrics"""
        try:
            message = "PERFORMANCE | "
            message += f"Trades:{metrics.get('trades', 0)} | "
            message += f"WinRate:{metrics.get('win_rate', 0):.1f}% | "
            message += f"P&L:${metrics.get('pnl', 0):+.2f} | "
            message += f"Balance:${metrics.get('balance', 0):.2f}"
            
            self._logger.info(message)
            
        except Exception as e:
            self._logger.error(f"Error logging performance metrics: {e}")
    
    def log_risk_alert(self, alert_type: str, current_value: float, limit: float, symbol: str = ""):
        """Log risk management alerts"""
        try:
            risk_emoji = "⚠️" if alert_type == "WARNING" else "🚨"
            message = f"RISK_{alert_type.upper()} {risk_emoji} | "
            
            if symbol:
                message += f"{symbol} | "
            
            message += f"Current:{current_value:.2f} | Limit:{limit:.2f}"
            
            if alert_type.upper() == "CRITICAL":
                self._logger.error(message)
            else:
                self._logger.warning(message)
                
        except Exception as e:
            self._logger.error(f"Error logging risk alert: {e}")
    
    def log_connection_event(self, broker: str, event: str, details: str = ""):
        """Log connection events"""
        try:
            status_emoji = {
                'CONNECTED': '🟢',
                'DISCONNECTED': '🔴',
                'RECONNECTING': '🟡',
                'ERROR': '❌'
            }
            
            emoji = status_emoji.get(event.upper(), '📡')
            message = f"CONNECTION {emoji} | {broker} | {event.upper()}"
            
            if details:
                message += f" | {details}"
            
            if event.upper() in ['ERROR', 'DISCONNECTED']:
                self._logger.error(message)
            elif event.upper() == 'RECONNECTING':
                self._logger.warning(message)
            else:
                self._logger.info(message)
                
        except Exception as e:
            self._logger.error(f"Error logging connection event: {e}")
    
    def setup_strategy_logger(self, strategy_name: str):
        """Setup dedicated logger for a strategy"""
        try:
            strategy_logger = logging.getLogger(f'AuraTrade.{strategy_name}')
            strategy_logger.setLevel(logging.DEBUG)
            
            # Strategy-specific log file
            log_dir = Path("AuraTrade/logs")
            strategy_log_file = log_dir / f"strategy_{strategy_name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
            
            strategy_handler = logging.FileHandler(
                strategy_log_file,
                mode='a',
                encoding='utf-8'
            )
            
            strategy_formatter = logging.Formatter(
                f'%(asctime)s | {strategy_name.upper()} | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            strategy_handler.setFormatter(strategy_formatter)
            strategy_logger.addHandler(strategy_handler)
            
            return strategy_logger
            
        except Exception as e:
            self._logger.error(f"Error setting up strategy logger for {strategy_name}: {e}")
            return self._logger
    
    def get_log_stats(self):
        """Get logging statistics"""
        try:
            log_dir = Path("AuraTrade/logs")
            
            if not log_dir.exists():
                return {"error": "Log directory not found"}
            
            log_files = list(log_dir.glob("*.log"))
            total_size = sum(f.stat().st_size for f in log_files)
            
            return {
                "log_files": len(log_files),
                "total_size_mb": total_size / 1024 / 1024,
                "log_directory": str(log_dir)
            }
            
        except Exception as e:
            self._logger.error(f"Error getting log stats: {e}")
            return {"error": str(e)}
    
    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Clean up old log files"""
        try:
            log_dir = Path("AuraTrade/logs")
            if not log_dir.exists():
                return
            
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                self._logger.info(f"Cleaned up {deleted_count} old log files")
                
        except Exception as e:
            self._logger.error(f"Error cleaning up logs: {e}")

# Global logger instance
_logger_instance = Logger()

def get_logger():
    """Get global logger instance"""
    return _logger_instance.get_logger()
