
"""
Credentials configuration for AuraTrade Bot
Store all sensitive information and API keys here
"""

class Credentials:
    """Secure credentials management"""
    
    def __init__(self):
        # MetaTrader 5 Configuration (Auto-detect from installed MT5)
        self.MT5 = {
            'login': None,  # Will auto-detect
            'password': None,  # Will auto-detect
            'server': None,  # Will auto-detect
            'path': None,  # Will auto-detect
            'timeout': 10000,
            'portable': False
        }
        
        # Telegram Bot Configuration
        self.TELEGRAM = {
            'bot_token': '8365734234:AAH2uTaZPDD47Lnm3y_Tcr6aj3xGL-bVsgk',  # Get from @BotFather
            'chat_id': '5061106648',  # Your Telegram chat ID
            'notifications_enabled': True  # Set to True when configured
        }
        
        # Database Configuration (Optional)
        self.DATABASE = {
            'type': 'sqlite',  # sqlite, mysql, postgresql
            'host': 'localhost',
            'port': 5432,
            'name': 'auratrade.db',
            'user': '',
            'password': ''
        }
        
        # API Keys (Optional)
        self.API_KEYS = {
            'financial_data': '',  # Alpha Vantage, Yahoo Finance, etc.
            'news_api': '',  # News sentiment analysis
            'economic_calendar': ''  # Economic events
        }
    
    @property
    def MT5_LOGIN(self) -> int:
        """Get MT5 login (auto-detected)"""
        return self.MT5.get('login')
    
    @property
    def MT5_PASSWORD(self) -> str:
        """Get MT5 password (auto-detected)"""
        return self.MT5.get('password')
    
    @property
    def MT5_SERVER(self) -> str:
        """Get MT5 server (auto-detected)"""
        return self.MT5.get('server')
    
    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        """Get Telegram bot token"""
        return '8365734234:AAH2uTaZPDD47Lnm3y_Tcr6aj3xGL-bVsgk'
    
    @property
    def TELEGRAM_CHAT_ID(self) -> str:
        """Get Telegram chat ID"""
        return '5061106648'
    
    @property
    def TELEGRAM_ENABLED(self) -> bool:
        """Check if Telegram notifications are enabled"""
        return self.TELEGRAM.get('notifications_enabled', False)
    
    def validate_credentials(self) -> dict:
        """Validate all credentials"""
        validation = {
            'telegram': False,
            'mt5': False,
            'api_keys': False
        }
        
        # Validate Telegram
        if self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID:
            validation['telegram'] = True
        
        # MT5 will be validated during connection
        validation['mt5'] = True  # Auto-detect mode
        
        # API keys are optional
        validation['api_keys'] = True
        
        return validation
