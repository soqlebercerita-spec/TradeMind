
"""
Credentials configuration for AuraTrade Bot
Store all sensitive information and API keys here
"""

class Credentials:
    """Centralized credentials management"""
    
    def __init__(self):
        # MetaTrader 5 Credentials
        self.MT5 = {
            'login': 12345678,  # Replace with your MT5 account number
            'password': 'your_password',  # Replace with your MT5 password
            'server': 'MetaQuotes-Demo',  # Replace with your broker's server
            'timeout': 60000,
            'portable': False
        }
        
        # Telegram Bot Configuration
        self.TELEGRAM = {
            'bot_token': 'your_telegram_bot_token',  # Get from @BotFather
            'chat_id': 'your_chat_id',  # Your Telegram chat ID
            'notifications_enabled': False  # Set to True when configured
        }
        
        # Database Configuration (Optional)
        self.DATABASE = {
            'host': 'localhost',
            'port': 5432,
            'database': 'auratrade',
            'username': 'postgres',
            'password': 'your_db_password',
            'enabled': False
        }
        
        # API Keys for external services
        self.API_KEYS = {
            'news_api': 'your_news_api_key',
            'economic_calendar': 'your_calendar_api_key'
        }
    
    def validate_credentials(self) -> dict:
        """Validate all credentials"""
        validation = {
            'mt5_configured': bool(self.MT5['login'] and self.MT5['password'] and self.MT5['server']),
            'telegram_configured': bool(self.TELEGRAM['bot_token'] and self.TELEGRAM['chat_id']),
            'database_configured': self.DATABASE['enabled'] and bool(self.DATABASE['host']),
            'apis_configured': bool(self.API_KEYS.get('news_api'))
        }
        
        return validation
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return (self.TELEGRAM['notifications_enabled'] and 
                bool(self.TELEGRAM['bot_token']) and 
                bool(self.TELEGRAM['chat_id']))
    
    def get_mt5_credentials(self) -> dict:
        """Get MT5 credentials"""
        return self.MT5.copy()
    
    def get_telegram_config(self) -> dict:
        """Get Telegram configuration"""
        return self.TELEGRAM.copy()
    
    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        """Get Telegram bot token"""
        return self.TELEGRAM.get('bot_token', '')
    
    @property
    def TELEGRAM_CHAT_ID(self) -> str:
        """Get Telegram chat ID"""
        return self.TELEGRAM.get('chat_id', '')
