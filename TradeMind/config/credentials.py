"""
Credentials and sensitive configuration data for AuraTrade Bot
All sensitive data should be loaded from environment variables
"""

import os
from typing import Dict, Optional

class Credentials:
    """Manages all credentials and sensitive configuration"""
    
    def __init__(self):
        # MetaTrader 5 credentials
        self.MT5_LOGIN = int(os.getenv('MT5_LOGIN', '0'))
        self.MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
        self.MT5_SERVER = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
        self.MT5_PATH = os.getenv('MT5_PATH', 'C:\\Program Files\\MetaTrader 5\\terminal64.exe')
        
        # Telegram bot credentials
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # API Keys for external data sources
        self.ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self.NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
        self.TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
        
        # Database credentials (if using external database)
        self.DATABASE_URL = os.getenv('DATABASE_URL', '')
        self.REDIS_URL = os.getenv('REDIS_URL', '')
        
        # Webhook and API endpoints
        self.WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')
        self.API_SECRET_KEY = os.getenv('API_SECRET_KEY', '')
        
        # Encryption keys for local data storage
        self.ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
    
    def validate_credentials(self) -> Dict[str, bool]:
        """Validate that all required credentials are present"""
        validation = {
            'mt5_login': self.MT5_LOGIN > 0,
            'mt5_password': bool(self.MT5_PASSWORD),
            'mt5_server': bool(self.MT5_SERVER),
            'telegram_bot_token': bool(self.TELEGRAM_BOT_TOKEN),
            'telegram_chat_id': bool(self.TELEGRAM_CHAT_ID)
        }
        
        return validation
    
    def get_missing_credentials(self) -> list:
        """Get list of missing required credentials"""
        validation = self.validate_credentials()
        missing = [key for key, valid in validation.items() if not valid]
        return missing
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram notifications are properly configured"""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)
    
    def is_mt5_configured(self) -> bool:
        """Check if MT5 connection is properly configured"""
        return bool(self.MT5_LOGIN > 0 and self.MT5_PASSWORD and self.MT5_SERVER)
    
    def get_mt5_credentials(self) -> Dict[str, any]:
        """Get MT5 connection credentials"""
        return {
            'login': self.MT5_LOGIN,
            'password': self.MT5_PASSWORD,
            'server': self.MT5_SERVER,
            'path': self.MT5_PATH
        }
    
    def get_telegram_credentials(self) -> Dict[str, str]:
        """Get Telegram bot credentials"""
        return {
            'bot_token': self.TELEGRAM_BOT_TOKEN,
            'chat_id': self.TELEGRAM_CHAT_ID
        }
    
    def get_external_api_keys(self) -> Dict[str, str]:
        """Get external API keys for data sources"""
        return {
            'alpha_vantage': self.ALPHA_VANTAGE_API_KEY,
            'newsapi': self.NEWSAPI_KEY,
            'twitter': self.TWITTER_BEARER_TOKEN
        }
    
    @staticmethod
    def create_env_template() -> str:
        """Create environment variable template for easy setup"""
        template = """
# AuraTrade Bot Environment Variables
# Copy this to .env file and fill in your credentials

# MetaTrader 5 Connection
MT5_LOGIN=your_mt5_login_number
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server
MT5_PATH=C:\\Program Files\\MetaTrader 5\\terminal64.exe

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# External Data APIs (Optional)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
NEWSAPI_KEY=your_newsapi_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Database (Optional)
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url

# Security (Optional)
WEBHOOK_SECRET=your_webhook_secret
API_SECRET_KEY=your_api_secret_key
ENCRYPTION_KEY=your_encryption_key
"""
        return template.strip()
