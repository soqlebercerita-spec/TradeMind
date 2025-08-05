
"""
Secure credentials management for AuraTrade Bot
"""

import os
from typing import Dict, Any
from utils.logger import Logger

class Credentials:
    """Secure credentials management"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        
        # MT5 Credentials - CONFIGURE THESE FOR YOUR ACCOUNT
        self.MT5_LOGIN = int(os.getenv('MT5_LOGIN', '0'))  # Your MT5 account number
        self.MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')  # Your MT5 password
        self.MT5_SERVER = os.getenv('MT5_SERVER', '')      # Your MT5 server
        
        # Telegram Bot Credentials (Optional)
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Validate on initialization
        self.validate_credentials()
    
    def validate_credentials(self) -> Dict[str, Any]:
        """Validate all credentials"""
        validation_result = {
            'mt5_configured': False,
            'telegram_configured': False,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check MT5 credentials
            if self.MT5_LOGIN and self.MT5_LOGIN != 0:
                if self.MT5_PASSWORD:
                    if self.MT5_SERVER:
                        validation_result['mt5_configured'] = True
                        self.logger.info("MT5 credentials configured")
                    else:
                        validation_result['errors'].append("MT5_SERVER not configured")
                else:
                    validation_result['errors'].append("MT5_PASSWORD not configured")
            else:
                validation_result['errors'].append("MT5_LOGIN not configured")
            
            # Check Telegram credentials (optional)
            if self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID:
                validation_result['telegram_configured'] = True
                self.logger.info("Telegram credentials configured")
            else:
                validation_result['warnings'].append("Telegram credentials not configured - notifications disabled")
            
            # Log results
            if validation_result['errors']:
                for error in validation_result['errors']:
                    self.logger.error(f"Credential error: {error}")
            
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    self.logger.warning(f"Credential warning: {warning}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating credentials: {e}")
            validation_result['errors'].append(f"Validation error: {e}")
            return validation_result
    
    def get_mt5_credentials(self) -> Dict[str, Any]:
        """Get MT5 credentials"""
        return {
            'login': self.MT5_LOGIN,
            'password': self.MT5_PASSWORD,
            'server': self.MT5_SERVER
        }
    
    def get_telegram_credentials(self) -> Dict[str, str]:
        """Get Telegram credentials"""
        return {
            'bot_token': self.TELEGRAM_BOT_TOKEN,
            'chat_id': self.TELEGRAM_CHAT_ID
        }
    
    def is_mt5_configured(self) -> bool:
        """Check if MT5 is properly configured"""
        return bool(self.MT5_LOGIN and self.MT5_PASSWORD and self.MT5_SERVER)
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)
