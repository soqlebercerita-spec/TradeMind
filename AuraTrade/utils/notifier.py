
"""
Notification System for AuraTrade Bot
Telegram and email notifications
"""

import asyncio
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional, Any
from datetime import datetime
import threading
import time
from utils.logger import Logger

class TelegramNotifier:
    """Telegram notification system"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.logger = Logger().get_logger()
        
        # Telegram settings
        self.bot_token = credentials.get('telegram_bot_token', '')
        self.chat_id = credentials.get('telegram_chat_id', '')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        # Rate limiting
        self.last_message_time = 0
        self.min_interval = 5  # Minimum 5 seconds between messages
        self.message_queue = []
        self.queue_thread = None
        self.queue_active = False
        
        if self.enabled:
            self.logger.info("Telegram notifier enabled")
            self._start_queue_processor()
        else:
            self.logger.warning("Telegram notifier disabled - missing credentials")
    
    def _start_queue_processor(self):
        """Start message queue processor"""
        if not self.queue_active:
            self.queue_active = True
            self.queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.queue_thread.start()
    
    def _process_queue(self):
        """Process message queue"""
        while self.queue_active:
            try:
                if self.message_queue:
                    message = self.message_queue.pop(0)
                    self._send_immediate(message)
                    time.sleep(self.min_interval)
                else:
                    time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error processing message queue: {e}")
                time.sleep(5)
    
    def send_message(self, message: str, urgent: bool = False):
        """Send message via Telegram"""
        try:
            if not self.enabled:
                return
            
            if urgent:
                self._send_immediate(message)
            else:
                self.message_queue.append(message)
                
        except Exception as e:
            self.logger.error(f"Error queuing Telegram message: {e}")
    
    def _send_immediate(self, message: str):
        """Send message immediately"""
        try:
            if not self.enabled:
                return
            
            # Rate limiting check
            current_time = time.time()
            if current_time - self.last_message_time < self.min_interval:
                time.sleep(self.min_interval - (current_time - self.last_message_time))
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            # Format message
            formatted_message = f"🤖 **AuraTrade Bot**\n\n{message}"
            
            data = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                self.logger.debug("Telegram message sent successfully")
            else:
                self.logger.error(f"Failed to send Telegram message: {response.status_code}")
            
            self.last_message_time = time.time()
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
    
    def send_trade_notification(self, action: str, symbol: str, order_type: str, 
                               volume: float, price: float, sl: float = None, 
                               tp: float = None, profit: float = None):
        """Send trade notification"""
        try:
            emoji_map = {
                'OPENED': '🟢',
                'CLOSED': '🔴',
                'MODIFIED': '🟡',
                'BUY': '📈',
                'SELL': '📉'
            }
            
            action_emoji = emoji_map.get(action, '⚡')
            type_emoji = emoji_map.get(order_type, '')
            
            message = f"{action_emoji} **TRADE {action}**\n"
            message += f"{type_emoji} **{order_type}** {symbol}\n"
            message += f"💰 Volume: {volume}\n"
            message += f"💲 Price: {price:.5f}\n"
            
            if sl:
                message += f"🛑 SL: {sl:.5f}\n"
            if tp:
                message += f"🎯 TP: {tp:.5f}\n"
            if profit is not None:
                profit_emoji = '💚' if profit > 0 else '❤️'
                message += f"{profit_emoji} Profit: ${profit:.2f}\n"
            
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")
    
    def send_system_status(self, status: str, details: str = ""):
        """Send system status notification"""
        try:
            status_emojis = {
                'started': '🚀',
                'stopped': '🛑',
                'error': '❌',
                'warning': '⚠️',
                'emergency': '🚨',
                'connected': '✅',
                'disconnected': '🔌'
            }
            
            emoji = status_emojis.get(status, 'ℹ️')
            message = f"{emoji} **SYSTEM STATUS**\n"
            message += f"Status: {status.upper()}\n"
            
            if details:
                message += f"\n{details}\n"
            
            message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.send_message(message, urgent=True)
            
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
    
    def send_performance_report(self, metrics: Dict[str, Any]):
        """Send performance report"""
        try:
            message = "📊 **PERFORMANCE REPORT**\n\n"
            
            # Key metrics
            message += f"💹 Win Rate: {metrics.get('win_rate', 0):.1f}%\n"
            message += f"💰 Net Profit: ${metrics.get('net_profit', 0):.2f}\n"
            message += f"📈 Total Trades: {metrics.get('total_trades', 0)}\n"
            message += f"🎯 Profit Factor: {metrics.get('profit_factor', 0):.2f}\n"
            
            # Risk metrics
            if 'max_drawdown' in metrics:
                message += f"📉 Max Drawdown: {metrics['max_drawdown']:.1f}%\n"
            
            # Daily stats
            if 'daily_profit' in metrics:
                profit_emoji = '💚' if metrics['daily_profit'] > 0 else '❤️'
                message += f"{profit_emoji} Today: ${metrics['daily_profit']:.2f}\n"
            
            message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending performance report: {e}")
    
    def send_risk_alert(self, risk_type: str, details: str):
        """Send risk management alert"""
        try:
            message = f"🚨 **RISK ALERT**\n\n"
            message += f"⚠️ Type: {risk_type}\n"
            message += f"📋 Details: {details}\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            self.send_message(message, urgent=True)
            
        except Exception as e:
            self.logger.error(f"Error sending risk alert: {e}")
    
    def send_market_alert(self, symbol: str, alert_type: str, message_text: str):
        """Send market analysis alert"""
        try:
            message = f"📊 **MARKET ALERT**\n\n"
            message += f"💱 Symbol: {symbol}\n"
            message += f"🔔 Type: {alert_type}\n"
            message += f"📝 {message_text}\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending market alert: {e}")
    
    def send_daily_summary(self, summary: Dict[str, Any]):
        """Send daily summary"""
        try:
            message = "📈 **DAILY SUMMARY**\n\n"
            
            # Trading stats
            message += f"📊 Trades Today: {summary.get('trades_today', 0)}\n"
            message += f"💹 Win Rate: {summary.get('win_rate_today', 0):.1f}%\n"
            
            # P&L
            profit_today = summary.get('profit_today', 0)
            profit_emoji = '💚' if profit_today > 0 else '❤️' if profit_today < 0 else '💛'
            message += f"{profit_emoji} Profit: ${profit_today:.2f}\n"
            
            # Best/Worst trades
            if 'best_trade' in summary:
                message += f"🏆 Best Trade: ${summary['best_trade']:.2f}\n"
            if 'worst_trade' in summary:
                message += f"💔 Worst Trade: ${summary['worst_trade']:.2f}\n"
            
            # Account info
            if 'account_balance' in summary:
                message += f"\n💰 Balance: ${summary['account_balance']:.2f}\n"
            if 'account_equity' in summary:
                message += f"📊 Equity: ${summary['account_equity']:.2f}\n"
            
            message += f"\n📅 {datetime.now().strftime('%Y-%m-%d')}"
            
            self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
    
    def stop(self):
        """Stop the notifier"""
        try:
            self.queue_active = False
            if self.queue_thread:
                self.queue_thread.join(timeout=5)
            self.logger.info("Telegram notifier stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping notifier: {e}")

class EmailNotifier:
    """Email notification system"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.logger = Logger().get_logger()
        
        # Email settings
        self.smtp_server = credentials.get('smtp_server', '')
        self.smtp_port = credentials.get('smtp_port', 587)
        self.email = credentials.get('email', '')
        self.password = credentials.get('email_password', '')
        self.recipient = credentials.get('recipient_email', '')
        
        self.enabled = bool(all([self.smtp_server, self.email, self.password, self.recipient]))
        
        if self.enabled:
            self.logger.info("Email notifier enabled")
        else:
            self.logger.warning("Email notifier disabled - missing credentials")
    
    def send_email(self, subject: str, message: str):
        """Send email notification"""
        try:
            if not self.enabled:
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.recipient
            msg['Subject'] = f"AuraTrade Bot - {subject}"
            
            body = f"AuraTrade Bot Notification\n\n{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            self.logger.debug("Email sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")

class NotificationManager:
    """Combined notification manager"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.telegram = TelegramNotifier(credentials)
        self.email = EmailNotifier(credentials)
        self.logger = Logger().get_logger()
        
        # Notification settings
        self.trade_notifications = True
        self.system_notifications = True
        self.performance_notifications = True
        self.risk_notifications = True
    
    def send_trade_notification(self, **kwargs):
        """Send trade notification via all enabled channels"""
        if self.trade_notifications:
            self.telegram.send_trade_notification(**kwargs)
    
    def send_system_status(self, status: str, details: str = ""):
        """Send system status via all enabled channels"""
        if self.system_notifications:
            self.telegram.send_system_status(status, details)
            if status in ['error', 'emergency']:
                self.email.send_email(f"System {status.upper()}", details)
    
    def send_performance_report(self, metrics: Dict[str, Any]):
        """Send performance report"""
        if self.performance_notifications:
            self.telegram.send_performance_report(metrics)
    
    def send_risk_alert(self, risk_type: str, details: str):
        """Send risk alert"""
        if self.risk_notifications:
            self.telegram.send_risk_alert(risk_type, details)
            self.email.send_email("Risk Alert", f"{risk_type}: {details}")
    
    def stop(self):
        """Stop all notifiers"""
        self.telegram.stop()
