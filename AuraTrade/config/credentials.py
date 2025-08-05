
"""
Credentials management for AuraTrade Bot
Secure handling of sensitive information
"""

import os
from typing import Dict, Any, Optional
from utils.logger import Logger

class Credentials:
    """Secure credentials management"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self._load_credentials()
        
    def _load_credentials(self):
        """Load credentials from environment variables or defaults"""
        # MT5 Credentials
        self.mt5_login = int(os.getenv('MT5_LOGIN', '0'))
        self.mt5_password = os.getenv('MT5_PASSWORD', '')
        self.mt5_server = os.getenv('MT5_SERVER', 'Demo-Server')
        self.mt5_path = os.getenv('MT5_PATH', 'C:\\Program Files\\MetaTrader 5\\terminal64.exe')
        
        # Telegram Credentials
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # API Keys
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY', '')
        self.news_api_key = os.getenv('NEWS_API_KEY', '')
        
        self.logger.info("Credentials loaded from environment")
        
    def get_mt5_credentials(self) -> Dict[str, Any]:
        """Get MT5 connection credentials"""
        return {
            'login': self.mt5_login,
            'password': self.mt5_password,
            'server': self.mt5_server,
            'path': self.mt5_path
        }
        
    def get_telegram_credentials(self) -> Dict[str, str]:
        """Get Telegram bot credentials"""
        return {
            'token': self.telegram_token,
            'chat_id': self.telegram_chat_id
        }
        
    def validate_credentials(self) -> Dict[str, bool]:
        """Validate all credentials"""
        validation = {
            'mt5_configured': bool(self.mt5_login and self.mt5_password and self.mt5_server),
            'telegram_configured': bool(self.telegram_token and self.telegram_chat_id),
            'api_keys_configured': bool(self.alpha_vantage_key or self.news_api_key)
        }
        
        if not validation['mt5_configured']:
            self.logger.warning("MT5 credentials not configured - using mock mode")
            
        if not validation['telegram_configured']:
            self.logger.warning("Telegram credentials not configured - notifications disabled")
            
        return validation
        
    def is_demo_mode(self) -> bool:
        """Check if running in demo/mock mode"""
        return self.mt5_login == 0 or 'demo' in self.mt5_server.lower()
