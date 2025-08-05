
"""
Telegram notification system for AuraTrade Bot
Sends trading alerts, system status, and performance updates
"""

import asyncio
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from config.credentials import Credentials
from utils.logger import Logger

class TelegramNotifier:
    """Telegram notification system with comprehensive alerts"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.credentials = Credentials()
        
        # Telegram configuration
        self.bot_token = getattr(self.credentials, 'TELEGRAM_BOT_TOKEN', '')
        self.chat_id = getattr(self.credentials, 'TELEGRAM_CHAT_ID', '')
        self.enabled = getattr(self.credentials, 'TELEGRAM_ENABLED', False)
        
        # API URL
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Message formatting
        self.emojis = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'money': '💰',
            'chart_up': '📈',
            'chart_down': '📉',
            'robot': '🤖',
            'bell': '🔔',
            'fire': '🔥',
            'lightning': '⚡',
            'target': '🎯'
        }
        
        if self.enabled and self.bot_token and self.chat_id:
            self.logger.info("TelegramNotifier initialized and enabled")
        else:
            self.logger.info("TelegramNotifier initialized but disabled (check credentials)")

    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send message to Telegram"""
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
        """Send trade notification"""
        try:
            if action.upper() == 'OPENED':
                emoji = self.emojis['lightning']
                title = f"{emoji} <b>NEW POSITION OPENED</b> {emoji}"
            elif action.upper() == 'CLOSED':
                emoji = self.emojis['target']
                title = f"{emoji} <b>POSITION CLOSED</b> {emoji}"
            else:
                emoji = self.emojis['info']
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
        """Send profit/loss alert"""
        try:
            if profit > 0:
                emoji = self.emojis['chart_up']
                title = f"{emoji} <b>PROFIT ALERT</b> {emoji}"
                status = "PROFIT"
            else:
                emoji = self.emojis['chart_down']
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
        """Send risk management alert"""
        try:
            if alert_type.upper() == 'CRITICAL':
                emoji = self.emojis['fire']
                title = f"{emoji} <b>CRITICAL RISK ALERT</b> {emoji}"
            elif alert_type.upper() == 'WARNING':
                emoji = self.emojis['warning']
                title = f"{emoji} <b>RISK WARNING</b> {emoji}"
            else:
                emoji = self.emojis['info']
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
        """Send daily trading summary"""
        try:
            emoji = self.emojis['robot']
            title = f"{emoji} <b>DAILY TRADING SUMMARY</b> {emoji}"
            
            trades = stats.get('trades_today', 0)
            wins = stats.get('wins_today', 0)
            win_rate = (wins / trades * 100) if trades > 0 else 0
            daily_pnl = stats.get('daily_pnl', 0)
            balance = stats.get('balance', 0)
            
            # Choose emoji based on performance
            if daily_pnl > 0:
                performance_emoji = self.emojis['chart_up']
            elif daily_pnl < 0:
                performance_emoji = self.emojis['chart_down']
            else:
                performance_emoji = self.emojis['target']
            
            message = f"{title}\n\n"
            message += f"<b>Total Trades:</b> {trades}\n"
            message += f"<b>Winning Trades:</b> {wins}\n"
            message += f"<b>Win Rate:</b> {win_rate:.1f}%\n"
            message += f"<b>Daily P&L:</b> ${daily_pnl:+.2f} {performance_emoji}\n"
            message += f"<b>Current Balance:</b> ${balance:.2f}\n"
            
            # Add performance rating
            if win_rate >= 70:
                message += f"\n{self.emojis['fire']} <b>Excellent Performance!</b>"
            elif win_rate >= 50:
                message += f"\n{self.emojis['success']} <b>Good Performance</b>"
            else:
                message += f"\n{self.emojis['warning']} <b>Performance Below Target</b>"
            
            message += f"\n\n<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            return False

    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status notification"""
        try:
            status_upper = status.upper()
            
            if status_upper == 'STARTED':
                emoji = self.emojis['success']
                title = f"{emoji} <b>SYSTEM STARTED</b> {emoji}"
            elif status_upper == 'STOPPED':
                emoji = self.emojis['warning']
                title = f"{emoji} <b>SYSTEM STOPPED</b> {emoji}"
            elif status_upper == 'ERROR':
                emoji = self.emojis['error']
                title = f"{emoji} <b>SYSTEM ERROR</b> {emoji}"
            elif status_upper == 'CONNECTED':
                emoji = self.emojis['success']
                title = f"{emoji} <b>MT5 CONNECTED</b> {emoji}"
            elif status_upper == 'DISCONNECTED':
                emoji = self.emojis['error']
                title = f"{emoji} <b>MT5 DISCONNECTED</b> {emoji}"
            else:
                emoji = self.emojis['info']
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
        """Send strategy signal alert"""
        try:
            emoji = self.emojis['lightning']
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
        """Send drawdown alert"""
        try:
            emoji = self.emojis['fire']
            title = f"{emoji} <b>DRAWDOWN ALERT</b> {emoji}"
            
            message = f"{title}\n\n"
            message += f"<b>Current Drawdown:</b> {current_drawdown:.2%}\n"
            message += f"<b>Max Allowed:</b> {max_drawdown:.2%}\n"
            message += f"<b>Balance:</b> ${balance:.2f}\n"
            message += f"<b>Equity:</b> ${equity:.2f}\n"
            message += f"<b>Floating Loss:</b> ${balance - equity:.2f}\n"
            
            if current_drawdown >= max_drawdown:
                message += f"\n{self.emojis['warning']} <b>MAXIMUM DRAWDOWN REACHED!</b>"
                message += f"\n<b>Action:</b> Trading suspended for risk management"
            
            message += f"\n\n<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending drawdown alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Telegram connection"""
        try:
            if not self.enabled:
                self.logger.info("Telegram notifications disabled")
                return False
            
            test_message = f"{self.emojis['robot']} <b>AuraTrade Test Message</b>\n\n"
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

    def get_status(self) -> Dict[str, Any]:
        """Get notifier status"""
        return {
            'enabled': self.enabled,
            'bot_token_configured': bool(self.bot_token),
            'chat_id_configured': bool(self.chat_id),
            'api_url': self.api_url if self.enabled else None
        }
