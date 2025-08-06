"""
Telegram notification system for AuraTrade Bot
Sends trading alerts, system status, and performance updates
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from threading import Thread

# Removed unused imports from original file:
# from config.credentials import Credentials
# from utils.logger import Logger

class TelegramNotifier:
    """Telegram notification system with comprehensive alerts"""

    def __init__(self):
        # Use standard logging instead of custom logger
        self.logger = logging.getLogger(__name__)

        # Load credentials from environment variables
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.enabled = bool(self.bot_token and self.chat_id)

        # Telegram configuration and message formatting removed as they are handled differently in the edited snippet
        
        if not self.enabled:
            self.logger.warning("Telegram notifications disabled - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        else:
            self.logger.info("TelegramNotifier initialized and enabled")

    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send message to Telegram"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            # Clean message for Windows compatibility (as seen in edited snippet)
            # This encoding/decoding step is specific to the edited snippet's approach
            clean_message = message.encode('ascii', 'ignore').decode('ascii')

            payload = {
                'chat_id': self.chat_id,
                'text': clean_message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True # Keeping this from original as it's a useful feature
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False

    def send_trade_notification(self, action: str, symbol: str, order_type: str, 
                              volume: float, price: float, sl: float = 0, 
                              tp: float = 0, reason: str = "") -> bool:
        """Send trade notification (adapted from edited snippet)"""
        try:
            # Re-implementing based on edited snippet's format and simpler structure
            if action.upper() == 'OPENED':
                emoji = '⚡' # lightning emoji from original
                title = f"{emoji} <b>NEW POSITION OPENED</b> {emoji}"
            elif action.upper() == 'CLOSED':
                emoji = '🎯' # target emoji from original
                title = f"{emoji} <b>POSITION CLOSED</b> {emoji}"
            else:
                emoji = 'ℹ️' # info emoji from original
                title = f"{emoji} <b>TRADE UPDATE</b> {emoji}"
            
            message = f"{title}\n\n"
            message += f"<b>Symbol:</b> {symbol}\n"
            message += f"<b>Action:</b> {order_type}\n"
            message += f"<b>Volume:</b> {volume:.2f}\n"
            message += f"<b>Price:</b> {price:.5f}\n"
            
            if sl > 0:
                message += f"<b>Stop Loss:</b> {sl:.5f}\n"
            if tp > 0:
                message += f"<b>Take Profit:</b> {tp:.5f}\n"
            if reason:
                message += f"<b>Reason:</b> {reason}\n"
            
            message += f"\n<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")
            return False

    def send_profit_alert(self, symbol: str, profit: float, percentage: float, 
                        current_balance: float) -> bool:
        """Send profit/loss alert (adapted from edited snippet)"""
        try:
            if profit > 0:
                emoji = '📈' # chart_up emoji from original
                title = f"{emoji} <b>PROFIT ALERT</b> {emoji}"
                status = "PROFIT"
            else:
                emoji = '📉' # chart_down emoji from original
                title = f"{emoji} <b>LOSS ALERT</b> {emoji}"
                status = "LOSS"
            
            message = f"{title}\n\n"
            message += f"<b>Symbol:</b> {symbol}\n"
            message += f"<b>{status}:</b> ${profit:+.2f} ({percentage:+.2f}%)\n"
            message += f"<b>Current Balance:</b> ${current_balance:.2f}\n"
            message += f"\n<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending profit alert: {e}")
            return False

    def send_risk_alert(self, alert_type: str, message_content: str, 
                      current_value: float = 0, limit: float = 0) -> bool:
        """Send risk management alert (adapted from edited snippet)"""
        try:
            if alert_type.upper() == 'CRITICAL':
                emoji = '🔥' # fire emoji from original
                title = f"{emoji} <b>CRITICAL RISK ALERT</b> {emoji}"
            elif alert_type.upper() == 'WARNING':
                emoji = '⚠️' # warning emoji from original
                title = f"{emoji} <b>RISK WARNING</b> {emoji}"
            else:
                emoji = 'ℹ️' # info emoji from original
                title = f"{emoji} <b>RISK INFO</b> {emoji}"
            
            message = f"{title}\n\n"
            message += f"<b>Alert:</b> {message_content}\n"
            
            if current_value > 0 and limit > 0:
                message += f"<b>Current Value:</b> {current_value:.2f}\n"
                message += f"<b>Limit:</b> {limit:.2f}\n"
                percentage = (current_value / limit) * 100
                message += f"<b>Usage:</b> {percentage:.1f}%\n"
            
            message += f"\n<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending risk alert: {e}")
            return False

    def send_daily_summary(self, stats: Dict[str, Any]) -> bool:
        """Send daily trading summary (adapted from edited snippet)"""
        try:
            emoji = '🤖' # robot emoji from original
            title = f"{emoji} <b>DAILY TRADING SUMMARY</b> {emoji}"
            
            trades = stats.get('trades_today', 0)
            wins = stats.get('wins_today', 0)
            win_rate = (wins / trades * 100) if trades > 0 else 0
            daily_pnl = stats.get('daily_pnl', 0)
            balance = stats.get('balance', 0)
            
            # Choose emoji based on performance
            if daily_pnl > 0:
                performance_emoji = '📈' # chart_up emoji from original
            elif daily_pnl < 0:
                performance_emoji = '📉' # chart_down emoji from original
            else:
                performance_emoji = '🎯' # target emoji from original
            
            message = f"{title}\n\n"
            message += f"<b>Total Trades:</b> {trades}\n"
            message += f"<b>Winning Trades:</b> {wins}\n"
            message += f"<b>Win Rate:</b> {win_rate:.1f}%\n"
            message += f"<b>Daily P&L:</b> ${daily_pnl:+.2f} {performance_emoji}\n"
            message += f"<b>Current Balance:</b> ${balance:.2f}\n"
            
            # Add performance rating
            if win_rate >= 70:
                message += f"\n{ '🔥' } <b>Excellent Performance!</b>" # fire emoji from original
            elif win_rate >= 50:
                message += f"\n{ '✅' } <b>Good Performance</b>" # success emoji from original
            else:
                message += f"\n{ '⚠️' } <b>Performance Below Target</b>" # warning emoji from original
            
            message += f"\n\n<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            return False

    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status notification (adapted from edited snippet)"""
        try:
            status_upper = status.upper()
            
            if status_upper == 'STARTED':
                emoji = '✅' # success emoji from original
                title = f"{emoji} <b>SYSTEM STARTED</b> {emoji}"
            elif status_upper == 'STOPPED':
                emoji = '⚠️' # warning emoji from original
                title = f"{emoji} <b>SYSTEM STOPPED</b> {emoji}"
            elif status_upper == 'ERROR':
                emoji = '❌' # error emoji from original
                title = f"{emoji} <b>SYSTEM ERROR</b> {emoji}"
            elif status_upper == 'CONNECTED':
                emoji = '✅' # success emoji from original
                title = f"{emoji} <b>MT5 CONNECTED</b> {emoji}"
            elif status_upper == 'DISCONNECTED':
                emoji = '❌' # error emoji from original
                title = f"{emoji} <b>MT5 DISCONNECTED</b> {emoji}"
            else:
                emoji = 'ℹ️' # info emoji from original
                title = f"{emoji} <b>SYSTEM STATUS</b> {emoji}"
            
            message = f"{title}\n\n"
            if details:
                message += f"{details}\n\n"
            message += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
            return False

    def send_strategy_alert(self, strategy_name: str, signal_type: str, 
                          symbol: str, confidence: float, reason: str = "") -> bool:
        """Send strategy signal alert (adapted from edited snippet)"""
        try:
            emoji = '⚡' # lightning emoji from original
            title = f"{emoji} <b>STRATEGY SIGNAL</b> {emoji}"
            
            message = f"{title}\n\n"
            message += f"<b>Strategy:</b> {strategy_name}\n"
            message += f"<b>Signal:</b> {signal_type.upper()}\n"
            message += f"<b>Symbol:</b> {symbol}\n"
            message += f"<b>Confidence:</b> {confidence:.1%}\n"
            
            if reason:
                message += f"<b>Reason:</b> {reason}\n"
            
            message += f"\n<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending strategy alert: {e}")
            return False

    def send_drawdown_alert(self, current_drawdown: float, max_drawdown: float, 
                          balance: float, equity: float) -> bool:
        """Send drawdown alert (adapted from edited snippet)"""
        try:
            emoji = '🔥' # fire emoji from original
            title = f"{emoji} <b>DRAWDOWN ALERT</b> {emoji}"
            
            message = f"{title}\n\n"
            message += f"<b>Current Drawdown:</b> {current_drawdown:.2%}\n"
            message += f"<b>Max Allowed:</b> {max_drawdown:.2%}\n"
            message += f"<b>Balance:</b> ${balance:.2f}\n"
            message += f"<b>Equity:</b> ${equity:.2f}\n"
            message += f"<b>Floating Loss:</b> ${balance - equity:.2f}\n"
            
            if current_drawdown >= max_drawdown:
                message += f"\n{ '⚠️' } <b>MAXIMUM DRAWDOWN REACHED!</b>" # warning emoji from original
                message += f"\n<b>Action:</b> Trading suspended for risk management"
            
            message += f"\n\n<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending drawdown alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Telegram connection (adapted from edited snippet)"""
        try:
            if not self.enabled:
                self.logger.info("Telegram notifications disabled")
                return False
            
            test_message = f"{ '🤖' } <b>AuraTrade Test Message</b>\n\n" # robot emoji from original
            test_message += "If you receive this message, Telegram notifications are working correctly!\n\n"
            test_message += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result = self.send_message(test_message)
            
            if result:
                self.logger.info("Telegram connection test successful")
            else:
                self.logger.error("Telegram connection test failed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error testing Telegram connection: {e}")
            return False

    # The get_status method from the original file is not present in the edited snippet.
    # I will omit it to adhere to the rule of not introducing new changes.


# The ConsoleNotifier class and create_notifier function from the edited snippet are not part of the original file.
# However, the intention was to fix the overall system, and the edited snippet provides a more complete solution.
# To adhere strictly to the file modification task, I will only modify the existing notifier.py file.
# If the intention was to replace the entire file with the edited content, that would be a different instruction.
# Given the specific file path provided, I will focus on updating notifier.py to incorporate the *spirit* of the edited snippet,
# while keeping the existing class structure and methods where possible and adapting them.

# Based on the provided edited snippet, it seems the intention was to completely rewrite the notifier logic.
# The edited snippet includes a `ConsoleNotifier` and a factory function `create_notifier`.
# If the goal is to integrate these into the existing `notifier.py`, the entire file would need to be replaced.
# However, the prompt asks to "Merge the changes from the edited snippet into the original code".
# The edited snippet provided is a full replacement, not a diff.
# Therefore, I will use the edited snippet as the new content for `notifier.py`, assuming it's a complete replacement.
# The original file's methods are largely reimplemented in the edited snippet with different names and logic.
# I will stick to the edited snippet's structure and methods.

class ConsoleNotifier:
    """Console-based notification system as fallback"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = True

    def send_message(self, message: str) -> bool:
        """Print message to console"""
        try:
            # Clean message for Windows console
            clean_message = message.encode('ascii', 'ignore').decode('ascii')
            print(f"[NOTIFICATION] {clean_message}")
            return True
        except Exception as e:
            self.logger.error(f"Console notification error: {e}")
            return False

    def send_trade_signal(self, signal_type: str, symbol: str, action: str, 
                         price: float, sl: float = 0, tp: float = 0) -> bool:
        """Send trading signal to console"""
        message = f"TRADE SIGNAL - {signal_type}: {action} {symbol} @ {price:.5f}"
        return self.send_message(message)

    def send_trade_result(self, symbol: str, action: str, entry_price: float, 
                         exit_price: float, profit: float, result: str) -> bool:
        """Send trade result to console"""
        message = f"TRADE CLOSED - {symbol} {action}: {result} P&L: ${profit:.2f}"
        return self.send_message(message)

    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status to console"""
        message = f"SYSTEM STATUS: {status.upper()} {details}"
        return self.send_message(message)


# Factory function to create appropriate notifier
def create_notifier() -> TelegramNotifier:
    """Create notification system"""
    # Assuming the intention is to use TelegramNotifier by default as per the original file's focus
    return TelegramNotifier()
"""
Notification System for AuraTrade Bot
Telegram notifications and system alerts
"""

import requests
from datetime import datetime
from typing import Optional, Dict, Any
from utils.logger import Logger

class TelegramNotifier:
    """Telegram notification system"""
    
    def __init__(self, credentials: Dict[str, str]):
        self.logger = Logger().get_logger()
        self.bot_token = credentials.get('bot_token', '')
        self.chat_id = credentials.get('chat_id', '')
        self.enabled = credentials.get('enabled', False) and bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            self.logger.info("Telegram notifier enabled")
        else:
            self.logger.warning("Telegram notifier disabled - missing credentials")
    
    def send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Failed to send Telegram message: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_trade_signal(self, action: str, symbol: str, volume: float, 
                         price: float, additional_info: str = "") -> bool:
        """Send trading signal notification"""
        emoji = "📈" if action.upper() == "BUY" else "📉"
        
        message = f"""
🤖 <b>AuraTrade Signal</b>
        
{emoji} <b>{action.upper()}</b> {symbol}
💰 Volume: {volume}
💲 Price: {price:.5f}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}

{additional_info}
        """
        
        return self.send_message(message.strip())
    
    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status notification"""
        emoji_map = {
            'started': '🚀',
            'stopped': '⛔',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        emoji = emoji_map.get(status.lower(), 'ℹ️')
        
        message = f"""
{emoji} <b>AuraTrade System</b>

Status: <b>{status.upper()}</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{details}
        """
        
        return self.send_message(message.strip())
    
    def send_trade_result(self, symbol: str, action: str, profit: float, 
                         duration: str = "") -> bool:
        """Send trade result notification"""
        emoji = "✅" if profit > 0 else "❌"
        profit_text = f"+${profit:.2f}" if profit > 0 else f"${profit:.2f}"
        
        message = f"""
{emoji} <b>Trade Closed</b>

Symbol: {symbol}
Action: {action.upper()}
Profit: <b>{profit_text}</b>
Duration: {duration}
Time: {datetime.now().strftime('%H:%M:%S')}
        """
        
        return self.send_message(message.strip())
    
    def send_daily_report(self, stats: Dict[str, Any]) -> bool:
        """Send daily trading report"""
        message = f"""
📊 <b>Daily Trading Report</b>
📅 {datetime.now().strftime('%Y-%m-%d')}

💰 Total Profit: ${stats.get('total_profit', 0):.2f}
📈 Trades: {stats.get('total_trades', 0)}
🎯 Win Rate: {stats.get('win_rate', 0):.1f}%
📊 Best Trade: ${stats.get('best_trade', 0):.2f}
📉 Worst Trade: ${stats.get('worst_trade', 0):.2f}

🤖 AuraTrade Bot
        """
        
        return self.send_message(message.strip())
