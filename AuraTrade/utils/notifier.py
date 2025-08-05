
"""
Telegram notification system for AuraTrade Bot
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from config.credentials import Credentials
from utils.logger import Logger

class Notifier:
    """Telegram notification manager"""
    
    def __init__(self):
        self.credentials = Credentials()
        self.logger = Logger("Notifier")
        self.bot_token = self.credentials.TELEGRAM_BOT_TOKEN
        self.chat_id = self.credentials.TELEGRAM_CHAT_ID
        self.enabled = self.credentials.is_telegram_configured()
        
        if not self.enabled:
            self.logger.warning("⚠️ Telegram notifications disabled - credentials not configured")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram"""
        if not self.enabled:
            self.logger.debug(f"Notification (disabled): {message}")
            return False
        
        try:
            # Run async function in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._send_async(message, parse_mode))
            loop.close()
            return result
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    async def _send_async(self, message: str, parse_mode: str) -> bool:
        """Send message asynchronously"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.debug("✅ Notification sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Telegram API error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Async notification error: {e}")
            return False
    
    def notify_trade_opened(self, symbol: str, action: str, volume: float, 
                           price: float, tp: float, sl: float) -> bool:
        """Notify when trade is opened"""
        message = f"""
🚀 <b>TRADE OPENED</b>
📊 Symbol: {symbol}
📈 Action: {action}
💰 Volume: {volume}
💵 Price: {price}
🎯 TP: {tp}
🛑 SL: {sl}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        return self.send_message(message.strip())
    
    def notify_trade_closed(self, symbol: str, action: str, volume: float, 
                           open_price: float, close_price: float, profit: float) -> bool:
        """Notify when trade is closed"""
        profit_emoji = "💚" if profit > 0 else "❤️"
        message = f"""
{profit_emoji} <b>TRADE CLOSED</b>
📊 Symbol: {symbol}
📈 Action: {action}
💰 Volume: {volume}
🔓 Open: {open_price}
🔒 Close: {close_price}
💵 Profit: ${profit:.2f}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        return self.send_message(message.strip())
    
    def notify_stop_loss_hit(self, symbol: str, loss: float) -> bool:
        """Notify when stop loss is hit"""
        message = f"""
🚨 <b>STOP LOSS HIT</b>
📊 Symbol: {symbol}
💸 Loss: ${loss:.2f}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        return self.send_message(message.strip())
    
    def notify_take_profit_hit(self, symbol: str, profit: float) -> bool:
        """Notify when take profit is hit"""
        message = f"""
🎯 <b>TAKE PROFIT HIT</b>
📊 Symbol: {symbol}
💰 Profit: ${profit:.2f}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        return self.send_message(message.strip())
    
    def notify_high_drawdown(self, current_dd: float, max_dd: float) -> bool:
        """Notify when drawdown is high"""
        message = f"""
⚠️ <b>HIGH DRAWDOWN ALERT</b>
📉 Current DD: {current_dd:.2f}%
🚨 Max DD: {max_dd:.2f}%
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        return self.send_message(message.strip())
    
    def notify_system_error(self, component: str, error: str) -> bool:
        """Notify system errors"""
        message = f"""
🚨 <b>SYSTEM ERROR</b>
🔧 Component: {component}
❌ Error: {error}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        return self.send_message(message.strip())
    
    def notify_daily_summary(self, trades: int, profit: float, dd: float, equity: float) -> bool:
        """Send daily trading summary"""
        profit_emoji = "💚" if profit > 0 else "❤️" if profit < 0 else "💙"
        
        message = f"""
📊 <b>DAILY SUMMARY</b>
🔢 Trades: {trades}
{profit_emoji} P&L: ${profit:.2f}
📉 Max DD: {dd:.2f}%
💰 Equity: ${equity:.2f}
📅 Date: {datetime.now().strftime('%Y-%m-%d')}
        """
        return self.send_message(message.strip())
    
    def notify_strategy_signal(self, strategy: str, symbol: str, signal: str, 
                              confidence: float) -> bool:
        """Notify strategy signals"""
        message = f"""
📡 <b>STRATEGY SIGNAL</b>
🧠 Strategy: {strategy}
📊 Symbol: {symbol}
📈 Signal: {signal}
🎯 Confidence: {confidence:.1%}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        return self.send_message(message.strip())
"""
Telegram notification system for AuraTrade Bot
Sends alerts and updates via Telegram Bot API
"""

import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from config.credentials import Credentials
from utils.logger import Logger

class TelegramNotifier:
    """Telegram bot for sending notifications"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.credentials = Credentials()
        
        # Get Telegram credentials
        self.bot_token = self.credentials.TELEGRAM['bot_token']
        self.chat_id = self.credentials.TELEGRAM['chat_id']
        
        # API URL
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Notification settings
        self.enabled = self.credentials.TELEGRAM['notifications_enabled']
        self.max_retries = 3
        
        if self.enabled and self.bot_token and self.chat_id:
            self.logger.info("Telegram notifier initialized successfully")
        else:
            self.logger.warning("Telegram notifier disabled or not configured")
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send a message to Telegram"""
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"{self.api_url}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        return True
                    else:
                        self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                        
                except requests.RequestException as e:
                    self.logger.error(f"Request error (attempt {attempt + 1}): {e}")
                    
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(1)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Exception sending Telegram message: {e}")
            return False
    
    def send_trade_alert(self, action: str, symbol: str, volume: float, 
                        price: float, sl: float, tp: float, strategy: str) -> bool:
        """Send trade execution alert"""
        emoji = "🟢" if action.upper() == "BUY" else "🔴"
        
        message = (
            f"{emoji} <b>TRADE EXECUTED</b>\n\n"
            f"<b>Action:</b> {action.upper()}\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Volume:</b> {volume} lots\n"
            f"<b>Price:</b> {price}\n"
            f"<b>Stop Loss:</b> {sl}\n"
            f"<b>Take Profit:</b> {tp}\n"
            f"<b>Strategy:</b> {strategy}\n"
            f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return self.send_message(message)
    
    def send_position_closed(self, symbol: str, profit: float, reason: str) -> bool:
        """Send position closed alert"""
        emoji = "💰" if profit > 0 else "💸"
        
        message = (
            f"{emoji} <b>POSITION CLOSED</b>\n\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Profit/Loss:</b> ${profit:.2f}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return self.send_message(message)
    
    def send_risk_alert(self, alert_type: str, details: Dict[str, Any]) -> bool:
        """Send risk management alert"""
        message = (
            f"⚠️ <b>RISK ALERT</b>\n\n"
            f"<b>Type:</b> {alert_type}\n"
        )
        
        for key, value in details.items():
            message += f"<b>{key.replace('_', ' ').title()}:</b> {value}\n"
        
        message += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(message)
    
    def send_emergency_stop(self, reason: str, positions_closed: int) -> bool:
        """Send emergency stop alert"""
        message = (
            f"🚨 <b>EMERGENCY STOP TRIGGERED</b>\n\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Positions Closed:</b> {positions_closed}\n"
            f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"All trading has been stopped!"
        )
        
        return self.send_message(message)
    
    def send_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """Send daily trading summary"""
        profit_emoji = "📈" if summary.get('total_profit', 0) > 0 else "📉"
        
        message = (
            f"{profit_emoji} <b>DAILY SUMMARY</b>\n\n"
            f"<b>Total Trades:</b> {summary.get('total_trades', 0)}\n"
            f"<b>Winning Trades:</b> {summary.get('winning_trades', 0)}\n"
            f"<b>Losing Trades:</b> {summary.get('losing_trades', 0)}\n"
            f"<b>Win Rate:</b> {summary.get('win_rate', 0):.1f}%\n"
            f"<b>Total Profit:</b> ${summary.get('total_profit', 0):.2f}\n"
            f"<b>Max Drawdown:</b> {summary.get('max_drawdown', 0):.2f}%\n"
            f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        return self.send_message(message)
    
    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status update"""
        status_emoji = {
            'starting': '🟡',
            'running': '🟢',
            'stopped': '🔴',
            'error': '❌',
            'warning': '⚠️'
        }
        
        emoji = status_emoji.get(status.lower(), '📊')
        
        message = (
            f"{emoji} <b>SYSTEM STATUS</b>\n\n"
            f"<b>Status:</b> {status.upper()}\n"
        )
        
        if details:
            message += f"<b>Details:</b> {details}\n"
        
        message += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            if not self.enabled:
                return False
            
            test_message = f"🤖 AuraTrade Bot Test Message\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            result = self.send_message(test_message)
            
            if result:
                self.logger.info("Telegram connection test successful")
            else:
                self.logger.error("Telegram connection test failed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Exception testing Telegram connection: {e}")
            return False
