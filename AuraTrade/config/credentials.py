"""
Secure credentials management for AuraTrade Bot
"""

class Credentials:
    """Secure credentials management"""

    def __init__(self):
        # MetaTrader 5 Configuration
        self.MT5 = {
            'login': 12345678,  # Replace with your MT5 login
            'password': 'your_password',  # Replace with your MT5 password
            'server': 'YourBroker-Demo',  # Replace with your broker server
            'path': None,  # Auto-detect MT5 path
            'timeout': 10000,
            'portable': False
        }

        # Telegram Bot Configuration
        self.TELEGRAM = {
            'bot_token': '',  # Get from @BotFather
            'chat_id': '',  # Your Telegram chat ID
            'notifications_enabled': False  # Set to True when configured
        }

        # Database Configuration (Optional)
        self.DATABASE = {
            'type': 'sqlite',
            'host': 'localhost',
            'port': 5432,
            'name': 'auratrade.db',
            'user': '',
            'password': ''
        }

        # API Keys (Optional)
        self.API_KEYS = {
            'financial_data': '',
            'news_api': '',
            'economic_calendar': ''
        }

    def validate_credentials(self):
        """Validate credential configuration"""
        validation = {
            'mt5_configured': bool(self.MT5.get('login') and self.MT5.get('password') and self.MT5.get('server')),
            'telegram_configured': bool(self.TELEGRAM.get('bot_token') and self.TELEGRAM.get('chat_id')),
            'database_configured': bool(self.DATABASE.get('name'))
        }
        return validation

    @property
    def MT5_LOGIN(self):
        return self.MT5.get('login')

    @property
    def MT5_PASSWORD(self):
        return self.MT5.get('password')

    @property
    def MT5_SERVER(self):
        return self.MT5.get('server')