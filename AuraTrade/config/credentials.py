"""
Credentials configuration for AuraTrade Bot
Store all sensitive data here
"""

class Credentials:
    """Centralized credentials management"""

    def __init__(self):
        # MT5 Configuration (Mock for Replit)
        self.MT5_LOGIN = 12345678
        self.MT5_PASSWORD = "demo_password"
        self.MT5_SERVER = "Demo-Server"

        # Telegram Configuration
        self.TELEGRAM_ENABLED = True
        self.TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with actual token
        self.TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"     # Replace with actual chat ID

        # Trading Configuration
        self.DEMO_MODE = True  # Always True in Replit
        self.MAX_RISK_PERCENT = 2.0
        self.MAX_DAILY_LOSS = 500.0
        self.DEFAULT_LOT_SIZE = 0.01

        # API Keys (if needed)
        self.NEWS_API_KEY = ""
        self.ECONOMIC_CALENDAR_API = ""

    def validate_credentials(self) -> dict:
        """Validate all credentials"""
        validation = {
            'mt5_configured': bool(self.MT5_LOGIN and self.MT5_PASSWORD and self.MT5_SERVER),
            'telegram_configured': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),
            'demo_mode': self.DEMO_MODE,
            'errors': []
        }

        if not validation['mt5_configured']:
            validation['errors'].append("MT5 credentials incomplete")

        if self.TELEGRAM_ENABLED and not validation['telegram_configured']:
            validation['errors'].append("Telegram credentials incomplete")

        return validation

    def get_mt5_config(self) -> dict:
        """Get MT5 configuration"""
        return {
            'login': self.MT5_LOGIN,
            'password': self.MT5_PASSWORD,
            'server': self.MT5_SERVER
        }

    def get_telegram_config(self) -> dict:
        """Get Telegram configuration"""
        return {
            'enabled': self.TELEGRAM_ENABLED,
            'bot_token': self.TELEGRAM_BOT_TOKEN,
            'chat_id': self.TELEGRAM_CHAT_ID
        }