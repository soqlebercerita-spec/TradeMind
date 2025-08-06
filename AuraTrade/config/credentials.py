
"""
Credentials management for AuraTrade Bot
Handles MT5 login credentials and API keys securely
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from utils.logger import Logger

# Load environment variables
load_dotenv()

class Credentials:
    """Secure credentials management for AuraTrade Bot"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self._load_credentials()
        
    def _load_credentials(self):
        """Load credentials from environment variables"""
        try:
            # MT5 Credentials
            self.mt5_login = os.getenv('MT5_LOGIN')
            self.mt5_password = os.getenv('MT5_PASSWORD') 
            self.mt5_server = os.getenv('MT5_SERVER')
            
            # Telegram Credentials
            self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            # Email Credentials (optional)
            self.email_address = os.getenv('EMAIL_ADDRESS')
            self.email_password = os.getenv('EMAIL_PASSWORD')
            self.email_smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
            self.email_smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
            
            # API Keys (optional)
            self.webhook_url = os.getenv('WEBHOOK_URL')
            self.discord_webhook = os.getenv('DISCORD_WEBHOOK')
            
            self.logger.info("Credentials loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            
    def get_mt5_credentials(self) -> Dict[str, Any]:
        """Get MT5 login credentials"""
        return {
            'login': self.mt5_login,
            'password': self.mt5_password,
            'server': self.mt5_server
        }
    
    def get_telegram_credentials(self) -> Dict[str, str]:
        """Get Telegram bot credentials"""
        return {
            'bot_token': self.telegram_bot_token,
            'chat_id': self.telegram_chat_id
        }
    
    def get_email_credentials(self) -> Dict[str, Any]:
        """Get email credentials"""
        return {
            'address': self.email_address,
            'password': self.email_password,
            'smtp_server': self.email_smtp_server,
            'smtp_port': self.email_smtp_port
        }
    
    def is_mt5_configured(self) -> bool:
        """Check if MT5 credentials are configured"""
        return all([
            self.mt5_login,
            self.mt5_password, 
            self.mt5_server
        ])
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is configured"""
        return all([
            self.telegram_bot_token,
            self.telegram_chat_id
        ])
    
    def is_email_configured(self) -> bool:
        """Check if email is configured"""
        return all([
            self.email_address,
            self.email_password
        ])
    
    def validate_credentials(self) -> Dict[str, bool]:
        """Validate all credentials"""
        return {
            'mt5': self.is_mt5_configured(),
            'telegram': self.is_telegram_configured(),
            'email': self.is_email_configured()
        }
    
    def update_mt5_credentials(self, login: str, password: str, server: str):
        """Update MT5 credentials"""
        self.mt5_login = login
        self.mt5_password = password
        self.mt5_server = server
        self.logger.info("MT5 credentials updated")
    
    def update_telegram_credentials(self, bot_token: str, chat_id: str):
        """Update Telegram credentials"""
        self.telegram_bot_token = bot_token
        self.telegram_chat_id = chat_id
        self.logger.info("Telegram credentials updated")
    
    def get_credential_status(self) -> str:
        """Get formatted credential status"""
        validation = self.validate_credentials()
        status_parts = []
        
        if validation['mt5']:
            status_parts.append("✅ MT5 Ready")
        else:
            status_parts.append("❌ MT5 Not Configured")
            
        if validation['telegram']:
            status_parts.append("✅ Telegram Ready")
        else:
            status_parts.append("❌ Telegram Not Configured")
            
        if validation['email']:
            status_parts.append("✅ Email Ready")
        else:
            status_parts.append("❌ Email Not Configured")
            
        return " | ".join(status_parts)
