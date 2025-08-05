
"""
Credentials and API keys for AuraTrade Bot
Store all sensitive information here
"""

import os
from typing import Dict, Any

class Credentials:
    """Centralized credentials management"""
    
    def __init__(self):
        # MetaTrader 5 Connection
        self.MT5 = {
            'login': int(os.getenv('MT5_LOGIN', '12345678')),
            'password': os.getenv('MT5_PASSWORD', 'your_password'),
            'server': os.getenv('MT5_SERVER', 'YourBroker-Demo'),
            'path': os.getenv('MT5_PATH', r'C:\Program Files\MetaTrader 5\terminal64.exe'),
            'timeout': 60000,
            'retry_attempts': 3,
            'retry_delay': 5
        }
        
        # Telegram Bot Configuration
        self.TELEGRAM = {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'notifications_enabled': os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        }
        
        # News API Keys (for sentiment analysis)
        self.NEWS_API = {
            'newsapi_key': os.getenv('NEWSAPI_KEY', ''),
            'alpha_vantage_key': os.getenv('ALPHAVANTAGE_KEY', ''),
            'finnhub_key': os.getenv('FINNHUB_KEY', '')
        }
        
        # Database Configuration (if needed)
        self.DATABASE = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'name': os.getenv('DB_NAME', 'auratrade'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        
        # Webhook URLs (for external integrations)
        self.WEBHOOKS = {
            'discord_webhook': os.getenv('DISCORD_WEBHOOK', ''),
            'slack_webhook': os.getenv('SLACK_WEBHOOK', '')
        }
    
    def validate_credentials(self) -> Dict[str, bool]:
        """Validate that required credentials are present"""
        validation = {
            'mt5_configured': bool(self.MT5['login'] and self.MT5['password'] and self.MT5['server']),
            'telegram_configured': bool(self.TELEGRAM['bot_token'] and self.TELEGRAM['chat_id']) if self.TELEGRAM['notifications_enabled'] else True,
            'path_exists': os.path.exists(self.MT5['path']) if self.MT5['path'] else False
        }
        
        return validation
    
    def get_mt5_config(self) -> Dict[str, Any]:
        """Get MT5 configuration"""
        return self.MT5.copy()
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram configuration"""
        return self.TELEGRAM.copy()
