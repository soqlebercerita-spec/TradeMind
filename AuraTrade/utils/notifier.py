
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
