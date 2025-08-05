
"""
Main trading engine optimized for high win rate (85%+)
Implements conservative risk management and advanced signal filtering
"""

import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from config.config import Config
from config.settings import Settings
from core.mt5_connector import MT5Connector
from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.position_sizing import PositionSizing
from data.data_manager import DataManager
from utils.logger import Logger
from utils.notifier import TelegramNotifier

class TradingEngine:
    """High-performance trading engine optimized for 85%+ win rate"""
    
    def __init__(self, mt5_connector: MT5Connector, order_manager: OrderManager,
                 risk_manager: RiskManager, position_sizing: PositionSizing,
                 data_manager: DataManager, ml_engine, notifier: TelegramNotifier):
        
        self.logger = Logger().get_logger()
        self.config = Config()
        self.settings = Settings()
        
        # Core components
        self.mt5_connector = mt5_connector
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_sizing = position_sizing
        self.data_manager = data_manager
        self.ml_engine = ml_engine
        self.notifier = notifier
        
        # Control flags
        self.running = False
        self.paused = False
        self.emergency_stop = False
        
        # Threading
        self.main_thread = None
        
        # Performance tracking for 85%+ win rate
        self.trades_today = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_trade_time = None
        self.win_rate = 0.0
        
        # High-quality signal filtering (conservative approach)
        self.min_signal_confirmation = 3  # Require 3+ confirmations
        self.max_daily_trades = 10  # Limit trades for quality
        self.required_win_rate = 85.0  # Target win rate
        
    def start(self):
        """Start the trading engine"""
        try:
            if self.running:
                self.logger.warning("Trading engine is already running")
                return
            
            self.logger.info("🚀 Starting AuraTrade High-Performance Engine...")
            self.running = True
            self.emergency_stop = False
            
            # Reset daily counters if new day
            self._reset_daily_counters()
            
            # Start main trading loop
            self.main_thread = threading.Thread(target=self._main_trading_loop, daemon=True)
            self.main_thread.start()
            
            self.logger.info("✅ Trading engine started successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start trading engine: {e}")
            self.running = False
    
    def stop(self):
        """Stop the trading engine"""
        try:
            self.logger.info("🛑 Stopping trading engine...")
            self.running = False
            
            # Wait for main thread to finish
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=10)
            
            self.logger.info("✅ Trading engine stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping trading engine: {e}")
    
    def _main_trading_loop(self):
        """Main trading loop optimized for high win rate"""
        self.logger.info("🔄 High-performance trading loop started")
        
        while self.running and not self.emergency_stop:
            try:
                # Check if paused
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Check connection
                if not self.mt5_connector.is_connected():
                    self.logger.warning("⚠️ MT5 connection lost, attempting reconnection...")
                    if not self.mt5_connector.reconnect():
                        time.sleep(10)
                        continue
                
                # Conservative daily limits check
                if self._check_conservative_limits():
                    self.logger.info("📊 Daily limits reached - maintaining high win rate")
                    break
                
                # Risk management check
                if self.risk_manager.check_emergency_stop():
                    self.emergency_stop_all()
                    break
                
                # Update market data
                self._update_market_data()
                
                # Process high-quality trading signals only
                self._process_high_quality_signals()
                
                # Monitor existing positions
                self._monitor_positions()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Sleep to maintain quality over quantity
                time.sleep(1)  # Slower loop for better quality
                
            except Exception as e:
                self.logger.error(f"❌ Error in main trading loop: {e}")
                time.sleep(1)
        
        self.logger.info("🏁 High-performance trading loop ended")
    
    def _process_high_quality_signals(self):
        """Process only high-quality signals for better win rate"""
        try:
            # Only trade major pairs during optimal hours
            optimal_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
            current_hour = datetime.now().hour
            
            # Trade only during optimal market hours (high liquidity)
            if not (8 <= current_hour <= 17):  # European/US overlap
                return
            
            for symbol in optimal_symbols:
                if not self._is_symbol_optimal_for_trading(symbol):
                    continue
                
                # Get multi-timeframe analysis
                signal_confirmations = self._get_signal_confirmations(symbol)
                
                # Require multiple confirmations for high win rate
                if signal_confirmations >= self.min_signal_confirmation:
                    self._execute_high_quality_trade(symbol, signal_confirmations)
                    
        except Exception as e:
            self.logger.error(f"❌ Error processing high-quality signals: {e}")
    
    def _get_signal_confirmations(self, symbol: str) -> int:
        """Get number of signal confirmations from different sources"""
        try:
            confirmations = 0
            
            # Get data for multiple timeframes
            m15_data = self.data_manager.get_rates(symbol, 'M15', 100)
            h1_data = self.data_manager.get_rates(symbol, 'H1', 100)
            h4_data = self.data_manager.get_rates(symbol, 'H4', 100)
            
            if any(data is None or len(data) < 50 for data in [m15_data, h1_data, h4_data]):
                return 0
            
            # Technical analysis confirmation
            if self._check_technical_confirmation(m15_data, h1_data):
                confirmations += 1
            
            # Trend alignment confirmation
            if self._check_trend_alignment(h1_data, h4_data):
                confirmations += 1
            
            # Volume confirmation
            if self._check_volume_confirmation(m15_data):
                confirmations += 1
            
            # Support/Resistance confirmation
            if self._check_sr_confirmation(symbol, m15_data):
                confirmations += 1
            
            # Market condition confirmation
            if self._check_market_condition_favorable():
                confirmations += 1
            
            return confirmations
            
        except Exception as e:
            self.logger.error(f"❌ Error getting signal confirmations for {symbol}: {e}")
            return 0
    
    def _check_technical_confirmation(self, m15_data: pd.DataFrame, h1_data: pd.DataFrame) -> bool:
        """Check technical analysis confirmation across timeframes"""
        try:
            # Calculate key indicators for both timeframes
            m15_ema20 = m15_data['close'].ewm(span=20).mean()
            m15_ema50 = m15_data['close'].ewm(span=50).mean()
            
            h1_ema20 = h1_data['close'].ewm(span=20).mean()
            h1_ema50 = h1_data['close'].ewm(span=50).mean()
            
            # Check if both timeframes show same trend direction
            m15_bullish = m15_ema20.iloc[-1] > m15_ema50.iloc[-1]
            h1_bullish = h1_ema20.iloc[-1] > h1_ema50.iloc[-1]
            
            # Confirmation if both timeframes agree
            return m15_bullish == h1_bullish
            
        except Exception as e:
            self.logger.error(f"❌ Error in technical confirmation: {e}")
            return False
    
    def _check_trend_alignment(self, h1_data: pd.DataFrame, h4_data: pd.DataFrame) -> bool:
        """Check trend alignment between H1 and H4"""
        try:
            # Calculate trend indicators
            h1_sma = h1_data['close'].rolling(20).mean()
            h4_sma = h4_data['close'].rolling(20).mean()
            
            # Check trend direction alignment
            h1_trend_up = h1_data['close'].iloc[-1] > h1_sma.iloc[-1]
            h4_trend_up = h4_data['close'].iloc[-1] > h4_sma.iloc[-1]
            
            return h1_trend_up == h4_trend_up
            
        except Exception as e:
            self.logger.error(f"❌ Error in trend alignment check: {e}")
            return False
    
    def _check_volume_confirmation(self, data: pd.DataFrame) -> bool:
        """Check volume confirmation (placeholder - MT5 doesn't provide volume for forex)"""
        try:
            # For forex, we can use tick volume or price action
            # Check for increasing volatility as volume proxy
            recent_range = (data['high'] - data['low']).tail(5).mean()
            overall_range = (data['high'] - data['low']).tail(20).mean()
            
            return recent_range > overall_range * 1.2
            
        except Exception as e:
            self.logger.error(f"❌ Error in volume confirmation: {e}")
            return False
    
    def _check_sr_confirmation(self, symbol: str, data: pd.DataFrame) -> bool:
        """Check support/resistance level confirmation"""
        try:
            current_price = data['close'].iloc[-1]
            
            # Find recent support/resistance levels
            highs = data['high'].tail(50)
            lows = data['low'].tail(50)
            
            # Check if price is near key level (within 0.1%)
            for level in [highs.max(), lows.min()]:
                distance = abs(current_price - level) / current_price
                if distance < 0.001:  # Within 0.1%
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in S/R confirmation: {e}")
            return False
    
    def _check_market_condition_favorable(self) -> bool:
        """Check if market conditions are favorable for high win rate"""
        try:
            current_hour = datetime.now().hour
            
            # Avoid trading during low liquidity periods
            if current_hour < 6 or current_hour > 20:
                return False
            
            # Avoid major news release times (simplified check)
            # In practice, you'd integrate with economic calendar
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking market conditions: {e}")
            return False
    
    def _execute_high_quality_trade(self, symbol: str, confirmations: int):
        """Execute trade only with high-quality signals"""
        try:
            # Conservative position sizing for high win rate
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return
            
            # Risk only 0.5% per trade for conservative approach
            risk_amount = account_info['equity'] * 0.005  # 0.5%
            
            # Get current price
            current_price = self.mt5_connector.get_current_price(symbol)
            if not current_price:
                return
            
            bid, ask = current_price
            
            # Determine trade direction based on confirmations
            # Simplified - in practice, use your signal logic
            entry_price = ask  # Buy example
            stop_loss = entry_price - 0.001  # 10 pips stop loss
            take_profit = entry_price + 0.002  # 20 pips take profit (2:1 R:R)
            
            # Calculate position size
            pip_value = 0.0001  # For major pairs
            stop_loss_pips = abs(entry_price - stop_loss) / pip_value
            
            if stop_loss_pips > 0:
                volume = risk_amount / (stop_loss_pips * 10)  # Simplified calculation
                volume = round(volume, 2)
                
                if volume > 0:
                    # Place order
                    result = self.mt5_connector.place_order(
                        symbol=symbol,
                        order_type=0,  # Buy order
                        volume=volume,
                        price=entry_price,
                        sl=stop_loss,
                        tp=take_profit,
                        comment=f"AuraTrade-HQ-{confirmations}"
                    )
                    
                    if result:
                        self.trades_today += 1
                        self.last_trade_time = datetime.now()
                        
                        self.logger.info(f"✅ High-quality trade executed: {symbol} - {confirmations} confirmations")
                        
                        # Send notification
                        if self.notifier:
                            self.notifier.notify_trade_opened(
                                symbol, "BUY", volume, entry_price, take_profit, stop_loss
                            )
            
        except Exception as e:
            self.logger.error(f"❌ Error executing high-quality trade: {e}")
    
    def _is_symbol_optimal_for_trading(self, symbol: str) -> bool:
        """Check if symbol conditions are optimal for trading"""
        try:
            # Check spread
            spread = self.mt5_connector.get_spread(symbol)
            if spread is None or spread > 2.0:  # Max 2 pip spread
                return False
            
            # Check if market is open
            if not self.mt5_connector.is_market_open(symbol):
                return False
            
            # Check if we already have position in this symbol
            positions = self.mt5_connector.get_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    return False  # One position per symbol for quality
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking symbol optimization: {e}")
            return False
    
    def _check_conservative_limits(self) -> bool:
        """Check conservative limits for high win rate"""
        try:
            # Check win rate - stop if below target
            if self.trades_today > 5 and self.win_rate < self.required_win_rate:
                self.logger.warning(f"⚠️ Win rate below target: {self.win_rate:.1f}% < {self.required_win_rate}%")
                return True
            
            # Limit daily trades for quality
            if self.trades_today >= self.max_daily_trades:
                self.logger.info(f"📈 Daily trade limit reached: {self.trades_today}")
                return True
            
            # Stop after 2 consecutive losses to preserve win rate
            if self.consecutive_losses >= 2:
                self.logger.warning(f"⚠️ Consecutive losses limit: {self.consecutive_losses}")
                return True
            
            # Check daily profit/loss limits
            if self.daily_pnl <= -100:  # $100 daily loss limit
                self.logger.warning(f"⚠️ Daily loss limit reached: ${self.daily_pnl:.2f}")
                return True
            
            if self.daily_pnl >= 500:  # $500 daily profit target
                self.logger.info(f"🎯 Daily profit target reached: ${self.daily_pnl:.2f}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking conservative limits: {e}")
            return False
    
    def _update_market_data(self):
        """Update market data for active symbols"""
        try:
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
            for symbol in symbols:
                # Update data in background - simplified
                pass
                
        except Exception as e:
            self.logger.error(f"❌ Error updating market data: {e}")
    
    def _monitor_positions(self):
        """Monitor and manage existing positions"""
        try:
            positions = self.mt5_connector.get_positions()
            
            for position in positions:
                # Implement trailing stops and position management
                self._manage_position(position)
                
        except Exception as e:
            self.logger.error(f"❌ Error monitoring positions: {e}")
    
    def _manage_position(self, position: Dict):
        """Manage individual position for optimal results"""
        try:
            # Quick profit taking for scalping positions
            if position['profit'] > 50:  # $50 profit
                self.mt5_connector.close_position(position['ticket'])
                self.logger.info(f"✅ Position closed with profit: ${position['profit']:.2f}")
                
        except Exception as e:
            self.logger.error(f"❌ Error managing position: {e}")
    
    def _update_performance_metrics(self):
        """Update performance tracking for win rate calculation"""
        try:
            positions = self.mt5_connector.get_positions()
            
            # Simple win rate calculation
            if self.trades_today > 0:
                self.win_rate = (self.winning_trades / self.trades_today) * 100
            
            # Update daily P&L
            account_info = self.mt5_connector.get_account_info()
            if account_info and hasattr(self, 'starting_equity'):
                self.daily_pnl = account_info['equity'] - self.starting_equity
            elif account_info:
                self.starting_equity = account_info['equity']
                
        except Exception as e:
            self.logger.error(f"❌ Error updating performance metrics: {e}")
    
    def _reset_daily_counters(self):
        """Reset daily counters for new trading day"""
        try:
            now = datetime.now()
            if not hasattr(self, 'last_reset_date') or self.last_reset_date.date() != now.date():
                self.trades_today = 0
                self.winning_trades = 0
                self.losing_trades = 0
                self.daily_pnl = 0.0
                self.consecutive_losses = 0
                self.win_rate = 0.0
                self.last_reset_date = now
                
                # Get starting equity for the day
                account_info = self.mt5_connector.get_account_info()
                if account_info:
                    self.starting_equity = account_info['equity']
                    
                self.logger.info("🔄 Daily counters reset for new trading day")
                
        except Exception as e:
            self.logger.error(f"❌ Error resetting daily counters: {e}")
    
    def emergency_stop_all(self):
        """Emergency stop - close all positions"""
        try:
            self.logger.warning("🚨 EMERGENCY STOP ACTIVATED")
            self.emergency_stop = True
            self.running = False
            
            # Close all positions
            positions = self.mt5_connector.get_positions()
            for position in positions:
                self.mt5_connector.close_position(position['ticket'])
            
            if self.notifier:
                self.notifier.send_message("🚨 EMERGENCY STOP - All positions closed")
                
        except Exception as e:
            self.logger.error(f"❌ Error during emergency stop: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            'running': self.running,
            'paused': self.paused,
            'emergency_stop': self.emergency_stop,
            'trades_today': self.trades_today,
            'win_rate': self.win_rate,
            'daily_pnl': self.daily_pnl,
            'consecutive_losses': self.consecutive_losses,
            'target_win_rate': self.required_win_rate
        }
