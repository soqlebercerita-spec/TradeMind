
"""
Risk management system for AuraTrade Bot
Implements conservative risk controls for high win rate trading
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from core.mt5_connector import MT5Connector
from utils.logger import Logger, log_error, log_system

class RiskManager:
    """Conservative risk management for high win rate trading"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Risk parameters (conservative for 85%+ win rate)
        self.risk_params = {
            'max_risk_per_trade': 0.01,      # 1% per trade
            'max_daily_risk': 0.05,          # 5% daily
            'max_drawdown': 0.10,            # 10% max drawdown  
            'max_positions': 8,              # Max open positions
            'max_positions_per_symbol': 2,   # Max per symbol
            'margin_level_limit': 150,       # Minimum margin level %
            'correlation_limit': 0.7,        # Max correlation between positions
            'max_daily_trades': 50,          # Daily trade limit
            'max_lot_size': 1.0,             # Maximum lot size
            'news_trading_pause': 15,        # Minutes to pause around news
        }
        
        # Daily tracking
        self.daily_stats = {
            'daily_trades': 0,
            'daily_pnl': 0.0,
            'daily_risk_used': 0.0,
            'max_concurrent_positions': 0,
            'last_reset': datetime.now().date()
        }
        
        # Position tracking
        self.position_correlations = {}
        self.high_impact_news_times = []
        
        self.logger.info("Risk Manager initialized with conservative parameters")
    
    def can_open_position(self, symbol: str, volume: float, 
                         trade_type: str = "market") -> bool:
        """Check if position can be opened based on risk rules"""
        try:
            # Reset daily stats if new day
            self._check_daily_reset()
            
            # Basic checks
            if not self._check_basic_limits(symbol, volume):
                return False
            
            # Account-based checks  
            if not self._check_account_limits():
                return False
            
            # Position-based checks
            if not self._check_position_limits(symbol):
                return False
            
            # Correlation checks
            if not self._check_correlation_limits(symbol):
                return False
            
            # News-based checks
            if not self._check_news_restrictions():
                return False
            
            # Margin checks
            if not self._check_margin_requirements(symbol, volume):
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", f"Error checking position eligibility for {symbol}", e)
            return False
    
    def calculate_position_size(self, symbol: str, stop_loss_pips: float) -> float:
        """Calculate optimal position size based on risk"""
        try:
            account_info = self.mt5_connector.get_account_info()
            balance = account_info.get('balance', 0)
            
            if balance <= 0:
                return 0.0
            
            # Risk amount (1% of balance)
            risk_amount = balance * self.risk_params['max_risk_per_trade']
            
            # Get symbol info
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
            
            # Calculate pip value
            point = symbol_info.get('point', 0.00001)
            contract_size = symbol_info.get('contract_size', 100000)
            
            # Get current price for pip value calculation
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return 0.0
            
            current_price = tick['bid']
            
            # Calculate pip value per lot
            if 'JPY' in symbol:
                pip_value_per_lot = (contract_size * 0.01) / current_price
            else:
                pip_value_per_lot = contract_size * point * 10
            
            # Calculate position size
            if pip_value_per_lot > 0 and stop_loss_pips > 0:
                position_size = risk_amount / (stop_loss_pips * pip_value_per_lot)
            else:
                position_size = 0.01  # Minimum size
            
            # Apply limits
            position_size = min(position_size, self.risk_params['max_lot_size'])
            position_size = max(position_size, 0.01)  # Minimum 0.01 lots
            
            # Round to 2 decimal places
            position_size = round(position_size, 2)
            
            self.logger.info(f"Calculated position size for {symbol}: {position_size} lots (Risk: ${risk_amount:.2f})")
            return position_size
            
        except Exception as e:
            log_error("RiskManager", f"Error calculating position size for {symbol}", e)
            return 0.01  # Safe minimum
    
    def _check_basic_limits(self, symbol: str, volume: float) -> bool:
        """Check basic trading limits"""
        # Volume limits
        if volume <= 0 or volume > self.risk_params['max_lot_size']:
            self.logger.warning(f"Volume {volume} exceeds limits")
            return False
        
        # Daily trade limit
        if self.daily_stats['daily_trades'] >= self.risk_params['max_daily_trades']:
            self.logger.warning("Daily trade limit reached")
            return False
        
        # Symbol validity
        symbol_info = self.mt5_connector.get_symbol_info(symbol)
        if not symbol_info:
            self.logger.warning(f"Invalid symbol: {symbol}")
            return False
        
        return True
    
    def _check_account_limits(self) -> bool:
        """Check account-based risk limits"""
        try:
            account_info = self.mt5_connector.get_account_info()
            
            # Balance checks
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            
            if balance <= 0:
                self.logger.warning("Invalid account balance")
                return False
            
            # Drawdown check
            if balance > equity:
                drawdown = (balance - equity) / balance
                if drawdown > self.risk_params['max_drawdown']:
                    self.logger.warning(f"Max drawdown exceeded: {drawdown:.1%}")
                    return False
            
            # Daily risk check
            if self.daily_stats['daily_risk_used'] >= self.risk_params['max_daily_risk']:
                self.logger.warning("Daily risk limit reached")
                return False
            
            # Margin level check
            margin_level = account_info.get('margin_level', 1000)
            if margin_level < self.risk_params['margin_level_limit']:
                self.logger.warning(f"Insufficient margin level: {margin_level:.1f}%")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", "Error checking account limits", e)
            return False
    
    def _check_position_limits(self, symbol: str) -> bool:
        """Check position-based limits"""
        try:
            positions = self.mt5_connector.get_positions()
            
            # Total position limit
            if len(positions) >= self.risk_params['max_positions']:
                self.logger.warning("Maximum positions limit reached")
                return False
            
            # Per-symbol position limit
            symbol_positions = [p for p in positions if p['symbol'] == symbol]
            if len(symbol_positions) >= self.risk_params['max_positions_per_symbol']:
                self.logger.warning(f"Maximum positions for {symbol} reached")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", "Error checking position limits", e)
            return False
    
    def _check_correlation_limits(self, symbol: str) -> bool:
        """Check correlation limits between positions"""
        try:
            positions = self.mt5_connector.get_positions()
            
            # Get symbols of existing positions
            existing_symbols = [p['symbol'] for p in positions]
            
            # Check correlation with existing positions
            for existing_symbol in existing_symbols:
                correlation = self._get_symbol_correlation(symbol, existing_symbol)
                if correlation > self.risk_params['correlation_limit']:
                    self.logger.warning(f"High correlation between {symbol} and {existing_symbol}: {correlation:.2f}")
                    return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", "Error checking correlation limits", e)
            return True  # Allow if can't check
    
    def _check_news_restrictions(self) -> bool:
        """Check if trading is restricted due to high-impact news"""
        try:
            current_time = datetime.now()
            
            # Check if we're in a news blackout period
            for news_time in self.high_impact_news_times:
                time_diff = abs((current_time - news_time).total_seconds() / 60)
                if time_diff <= self.risk_params['news_trading_pause']:
                    self.logger.warning(f"Trading paused due to high-impact news (remaining: {self.risk_params['news_trading_pause'] - time_diff:.1f} min)")
                    return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", "Error checking news restrictions", e)
            return True  # Allow if can't check
    
    def _check_margin_requirements(self, symbol: str, volume: float) -> bool:
        """Check if sufficient margin for position"""
        try:
            account_info = self.mt5_connector.get_account_info()
            free_margin = account_info.get('free_margin', 0)
            
            # Estimate required margin
            symbol_info = self.mt5_connector.get_symbol_info(symbol)
            if not symbol_info:
                return False
            
            tick = self.mt5_connector.get_tick(symbol)
            if not tick:
                return False
            
            contract_size = symbol_info.get('contract_size', 100000)
            current_price = tick['ask']
            leverage = account_info.get('leverage', 100)
            
            required_margin = (volume * contract_size * current_price) / leverage
            
            # Require 2x margin as safety buffer
            if free_margin < required_margin * 2:
                self.logger.warning(f"Insufficient free margin for {symbol}: Required {required_margin:.2f}, Available {free_margin:.2f}")
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", "Error checking margin requirements", e)
            return False
    
    def _get_symbol_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols (simplified)"""
        # Simplified correlation mapping
        correlations = {
            ('EURUSD', 'GBPUSD'): 0.8,
            ('EURUSD', 'USDCHF'): -0.9,
            ('GBPUSD', 'USDCHF'): -0.7,
            ('AUDUSD', 'NZDUSD'): 0.9,
            ('XAUUSD', 'XAGUSD'): 0.7,
        }
        
        # Check both directions
        key1 = (symbol1, symbol2)
        key2 = (symbol2, symbol1)
        
        return correlations.get(key1, correlations.get(key2, 0.1))
    
    def _check_daily_reset(self):
        """Reset daily statistics if new day"""
        today = datetime.now().date()
        if self.daily_stats['last_reset'] != today:
            self.daily_stats = {
                'daily_trades': 0,
                'daily_pnl': 0.0,
                'daily_risk_used': 0.0,
                'max_concurrent_positions': 0,
                'last_reset': today
            }
            log_system("Daily risk statistics reset")
    
    def update_trade_metrics(self, symbol: str, volume: float, pnl: float):
        """Update metrics after trade"""
        self.daily_stats['daily_trades'] += 1
        self.daily_stats['daily_pnl'] += pnl
        
        # Update daily risk used
        account_info = self.mt5_connector.get_account_info()
        balance = account_info.get('balance', 0)
        if balance > 0:
            risk_used = abs(pnl) / balance
            self.daily_stats['daily_risk_used'] += risk_used
    
    def add_high_impact_news(self, news_time: datetime):
        """Add high-impact news time for trading restrictions"""
        self.high_impact_news_times.append(news_time)
        
        # Clean old news times (older than 1 hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.high_impact_news_times = [
            t for t in self.high_impact_news_times if t > cutoff_time
        ]
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        try:
            account_info = self.mt5_connector.get_account_info()
            positions = self.mt5_connector.get_positions()
            
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            
            # Calculate current drawdown
            drawdown = 0.0
            if balance > 0:
                drawdown = max(0, (balance - equity) / balance)
            
            return {
                'daily_trades': self.daily_stats['daily_trades'],
                'daily_pnl': self.daily_stats['daily_pnl'],
                'daily_risk_used': self.daily_stats['daily_risk_used'],
                'current_drawdown': drawdown,
                'active_positions': len(positions),
                'margin_level': account_info.get('margin_level', 0),
                'free_margin': account_info.get('free_margin', 0),
                'can_trade': self.can_open_position('EURUSD', 0.01),  # Test with EURUSD
                'risk_limits': self.risk_params,
                'news_restriction_active': len(self.high_impact_news_times) > 0
            }
            
        except Exception as e:
            log_error("RiskManager", "Error getting risk status", e)
            return {}
    
    def emergency_risk_shutdown(self) -> bool:
        """Emergency shutdown due to risk breach"""
        try:
            log_system("EMERGENCY: Risk-based shutdown initiated", "ERROR")
            
            # Close all positions
            positions = self.mt5_connector.get_positions()
            closed_count = 0
            
            for position in positions:
                result = self.mt5_connector.close_position(position['ticket'])
                if result and result.get('retcode') == 10009:
                    closed_count += 1
            
            log_system(f"Emergency shutdown: {closed_count} positions closed", "WARNING")
            return True
            
        except Exception as e:
            log_error("RiskManager", "Error during emergency shutdown", e)
            return False
    
    def is_trading_time(self) -> bool:
        """Check if current time is within trading hours"""
        try:
            current_time = datetime.now()
            
            # Avoid trading during weekends
            if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            # Avoid trading during low liquidity hours (example: 22:00-02:00 UTC)
            hour = current_time.hour
            if 22 <= hour or hour <= 2:
                return False
            
            return True
            
        except Exception as e:
            log_error("RiskManager", "Error checking trading time", e)
            return True  # Default to allow trading
