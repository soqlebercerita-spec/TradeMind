"""
Credentials management for AuraTrade Bot
Secure handling of MT5 and API credentials
"""

import os
from typing import Dict, Optional
from utils.logger import Logger

class Credentials:
    """Secure credentials management"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self._mt5_credentials = {}
        self._telegram_credentials = {}
        self._api_credentials = {}
        self.load_credentials()

    def load_credentials(self):
        """Load credentials from environment variables"""
        try:
            # MT5 Credentials
            self._mt5_credentials = {
                'login': int(os.getenv('MT5_LOGIN', '0')),
                'password': os.getenv('MT5_PASSWORD', ''),
                'server': os.getenv('MT5_SERVER', ''),
                'timeout': int(os.getenv('MT5_TIMEOUT', '60000')),
                'portable': bool(os.getenv('MT5_PORTABLE', 'False').lower() == 'true')
            }

            # Telegram Credentials
            self._telegram_credentials = {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
                'enabled': bool(os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true')
            }

            # API Credentials
            self._api_credentials = {
                'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
                'fmp': os.getenv('FMP_API_KEY', ''),
                'news_api': os.getenv('NEWS_API_KEY', '')
            }

            self.logger.info("Credentials loaded successfully")

        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            self._set_default_credentials()

    def _set_default_credentials(self):
        """Set default credentials when loading fails"""
        self._mt5_credentials = {
            'login': 0,
            'password': '',
            'server': '',
            'timeout': 60000,
            'portable': False
        }

        self._telegram_credentials = {
            'bot_token': '',
            'chat_id': '',
            'enabled': False
        }

        self._api_credentials = {
            'alpha_vantage': '',
            'fmp': '',
            'news_api': ''
        }

    def get_mt5_credentials(self) -> Dict:
        """Get MT5 credentials"""
        return self._mt5_credentials.copy()

    def get_telegram_credentials(self) -> Dict:
        """Get Telegram credentials"""
        return self._telegram_credentials.copy()

    def get_api_credentials(self) -> Dict:
        """Get API credentials"""
        return self._api_credentials.copy()

    def validate_mt5_credentials(self) -> bool:
        """Validate MT5 credentials"""
        creds = self._mt5_credentials
        return bool(creds.get('login', 0) and creds.get('password') and creds.get('server'))

    def validate_telegram_credentials(self) -> bool:
        """Validate Telegram credentials"""
        creds = self._telegram_credentials
        return bool(creds.get('bot_token') and creds.get('chat_id'))

    def update_mt5_credentials(self, login: int, password: str, server: str):
        """Update MT5 credentials"""
        self._mt5_credentials.update({
            'login': login,
            'password': password,
            'server': server
        })
        self.logger.info("MT5 credentials updated")

    def update_telegram_credentials(self, bot_token: str, chat_id: str):
        """Update Telegram credentials"""
        self._telegram_credentials.update({
            'bot_token': bot_token,
            'chat_id': chat_id
        })
        self.logger.info("Telegram credentials updated")