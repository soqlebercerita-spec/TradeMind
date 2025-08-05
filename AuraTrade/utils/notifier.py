"""
Telegram notification system for AuraTrade Bot
"""

import requests
import json
from datetime import datetime
from typing import Optional
from config.credentials import Credentials
from utils.logger import Logger

class TelegramNotifier:
    """Telegram notification system"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.credentials = Credentials()
        self.bot_token = self.credentials.TELEGRAM.get('bot_token')
        self.chat_id = self.credentials.TELEGRAM.get('chat_id')
        self.enabled = self.credentials.TELEGRAM.get('notifications_enabled', False)

        if self.enabled and (not self.bot_token or not self.chat_id):
            self.logger.warning("Telegram credentials not configured properly")
            self.enabled = False

    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send message to Telegram"""
        if not self.enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                self.logger.debug("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False

    def notify_trade_opened(self, symbol: str, action: str, volume: float, 
                           price: float, tp: float, sl: float) -> bool:
        """Notify when trade is opened"""
        message = (
            f"<b>TRADE OPENED</b>\n\n"
            f"Symbol: {symbol}\n"
            f"Action: {action}\n"
            f"Volume: {volume}\n"
            f"Price: {price}\n"
            f"TP: {tp}\n"
            f"SL: {sl}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)

    def notify_trade_closed(self, symbol: str, action: str, volume: float, 
                           close_price: float, profit: float) -> bool:
        """Notify when trade is closed"""
        status = "PROFIT" if profit > 0 else "LOSS"
        message = (
            f"<b>TRADE CLOSED - {status}</b>\n\n"
            f"Symbol: {symbol}\n"
            f"Action: {action}\n"
            f"Volume: {volume}\n"
            f"Close Price: {close_price}\n"
            f"P&L: ${profit:.2f}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)

    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status notification"""
        message = (
            f"<b>AURATRADE STATUS</b>\n\n"
            f"Status: {status.upper()}\n"
            f"Details: {details}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)

    def send_trade_alert(self, direction: str, symbol: str, volume: float, 
                        entry: float, sl: float, tp: float, strategy: str) -> bool:
        """Send trade alert"""
        message = (
            f"<b>TRADE ALERT</b>\n\n"
            f"Direction: {direction}\n"
            f"Symbol: {symbol}\n"
            f"Volume: {volume}\n"
            f"Entry: {entry}\n"
            f"Stop Loss: {sl}\n"
            f"Take Profit: {tp}\n"
            f"Strategy: {strategy}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)

    def test_connection(self) -> bool:
        """Test Telegram connection"""
        if not self.enabled:
            self.logger.info("Telegram notifications disabled")
            return False

        test_message = "AuraTrade Bot - Connection Test"
        result = self.send_message(test_message)

        if result:
            self.logger.info("Telegram connection test successful")
        else:
            self.logger.error("Telegram connection test failed")

        return result