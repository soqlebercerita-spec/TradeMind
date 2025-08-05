"""
Strategy and risk-specific settings for AuraTrade Bot
These settings can be modified during runtime through the GUI
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class StrategySettings:
    """Individual strategy configuration"""
    enabled: bool = True
    weight: float = 1.0
    max_positions: int = 5
    min_signal_strength: float = 0.6
    timeframes: List[str] = None
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = ['M15', 'H1']
        if self.symbols is None:
            self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']

@dataclass
class RiskSettings:
    """Risk management configuration"""
    max_risk_per_trade: float = 1.0
    max_daily_risk: float = 5.0
    max_total_exposure: float = 10.0
    max_correlation: float = 0.8
    position_sizing_method: str = 'risk_based'
    kelly_fraction: float = 0.25
    trailing_stop: bool = True
    trailing_distance: float = 0.5
    
@dataclass
class NotificationSettings:
    """Notification preferences"""
    telegram_enabled: bool = True
    trade_opened: bool = True
    trade_closed: bool = True
    profit_target_hit: bool = True
    stop_loss_hit: bool = True
    high_drawdown: bool = True
    system_errors: bool = True
    daily_summary: bool = True

class Settings:
    """Main settings manager for the trading bot"""
    
    def __init__(self, config_file: str = 'settings.json'):
        self.config_file = config_file
        
        # Default strategy settings
        self.strategies = {
            'hft': StrategySettings(
                enabled=True,
                weight=0.3,
                max_positions=3,
                min_signal_strength=0.8,
                timeframes=['M1'],
                symbols=['EURUSD', 'GBPUSD', 'USDJPY']
            ),
            'scalping': StrategySettings(
                enabled=True,
                weight=0.4,
                max_positions=5,
                min_signal_strength=0.7,
                timeframes=['M1', 'M5'],
                symbols=['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD']
            ),
            'arbitrage': StrategySettings(
                enabled=False,
                weight=0.2,
                max_positions=2,
                min_signal_strength=0.9,
                timeframes=['M1'],
                symbols=['EURUSD', 'GBPUSD']
            ),
            'pattern': StrategySettings(
                enabled=True,
                weight=0.5,
                max_positions=4,
                min_signal_strength=0.6,
                timeframes=['M15', 'M30'],
                symbols=['EURUSD', 'GBPUSD', 'XAUUSD', 'USDJPY']
            )
        }
        
        # Risk management settings
        self.risk = RiskSettings()
        
        # Notification settings
        self.notifications = NotificationSettings()
        
        # Trading session settings
        self.trading_sessions = {
            'asian': {
                'enabled': True,
                'start_hour': 0,
                'end_hour': 8,
                'aggressive_mode': False
            },
            'european': {
                'enabled': True,
                'start_hour': 8,
                'end_hour': 16,
                'aggressive_mode': True
            },
            'american': {
                'enabled': True,
                'start_hour': 16,
                'end_hour': 24,
                'aggressive_mode': True
            }
        }
        
        # Market condition adaptations
        self.market_conditions = {
            'high_volatility': {
                'reduce_position_size': True,
                'increase_stop_distance': True,
                'disable_hft': True,
                'volatility_threshold': 2.0
            },
            'low_volatility': {
                'increase_position_size': False,
                'enable_scalping': True,
                'volatility_threshold': 0.5
            },
            'trending_market': {
                'favor_trend_strategies': True,
                'reduce_mean_reversion': True,
                'trend_strength_threshold': 0.7
            },
            'ranging_market': {
                'favor_mean_reversion': True,
                'reduce_trend_following': True,
                'range_detection_period': 100
            }
        }
        
        # Performance targets
        self.performance_targets = {
            'daily_profit_target': 2.0,      # 2% daily profit target
            'daily_loss_limit': -3.0,       # -3% daily loss limit
            'weekly_profit_target': 10.0,   # 10% weekly profit target
            'monthly_profit_target': 30.0,  # 30% monthly profit target
            'max_consecutive_losses': 5,    # Stop after 5 consecutive losses
            'profit_protection': 50.0       # Protect 50% of profits above target
        }
        
        # Load settings from file if exists
        self.load_settings()
    
    def load_settings(self) -> bool:
        """Load settings from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Load strategy settings
            if 'strategies' in data:
                for strategy_name, strategy_data in data['strategies'].items():
                    if strategy_name in self.strategies:
                        # Update existing strategy settings
                        for key, value in strategy_data.items():
                            if hasattr(self.strategies[strategy_name], key):
                                setattr(self.strategies[strategy_name], key, value)
            
            # Load risk settings
            if 'risk' in data:
                for key, value in data['risk'].items():
                    if hasattr(self.risk, key):
                        setattr(self.risk, key, value)
            
            # Load notification settings
            if 'notifications' in data:
                for key, value in data['notifications'].items():
                    if hasattr(self.notifications, key):
                        setattr(self.notifications, key, value)
            
            # Load other settings
            if 'trading_sessions' in data:
                self.trading_sessions.update(data['trading_sessions'])
            
            if 'market_conditions' in data:
                self.market_conditions.update(data['market_conditions'])
            
            if 'performance_targets' in data:
                self.performance_targets.update(data['performance_targets'])
            
            return True
            
        except FileNotFoundError:
            # Create default settings file
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error loading settings: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Save current settings to JSON file"""
        try:
            data = {
                'strategies': {
                    name: asdict(strategy) for name, strategy in self.strategies.items()
                },
                'risk': asdict(self.risk),
                'notifications': asdict(self.notifications),
                'trading_sessions': self.trading_sessions,
                'market_conditions': self.market_conditions,
                'performance_targets': self.performance_targets,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def update_strategy_setting(self, strategy: str, setting: str, value: Any) -> bool:
        """Update individual strategy setting"""
        try:
            if strategy in self.strategies and hasattr(self.strategies[strategy], setting):
                setattr(self.strategies[strategy], setting, value)
                self.save_settings()
                return True
            return False
        except Exception:
            return False
    
    def update_risk_setting(self, setting: str, value: Any) -> bool:
        """Update individual risk setting"""
        try:
            if hasattr(self.risk, setting):
                setattr(self.risk, setting, value)
                self.save_settings()
                return True
            return False
        except Exception:
            return False
    
    def get_active_strategies(self) -> List[str]:
        """Get list of enabled strategies"""
        return [name for name, strategy in self.strategies.items() if strategy.enabled]
    
    def get_strategy_symbols(self, strategy: str) -> List[str]:
        """Get symbols for specific strategy"""
        if strategy in self.strategies:
            return self.strategies[strategy].symbols
        return []
    
    def get_strategy_timeframes(self, strategy: str) -> List[str]:
        """Get timeframes for specific strategy"""
        if strategy in self.strategies:
            return self.strategies[strategy].timeframes
        return []
    
    def is_trading_session_active(self) -> bool:
        """Check if any trading session is currently active"""
        current_hour = datetime.now().hour
        
        for session_name, session_config in self.trading_sessions.items():
            if not session_config['enabled']:
                continue
            
            start_hour = session_config['start_hour']
            end_hour = session_config['end_hour']
            
            if start_hour <= current_hour < end_hour:
                return True
        
        return False
    
    def get_current_trading_session(self) -> str:
        """Get name of current active trading session"""
        current_hour = datetime.now().hour
        
        for session_name, session_config in self.trading_sessions.items():
            if not session_config['enabled']:
                continue
            
            start_hour = session_config['start_hour']
            end_hour = session_config['end_hour']
            
            if start_hour <= current_hour < end_hour:
                return session_name
        
        return 'none'
    
    def should_use_aggressive_mode(self) -> bool:
        """Check if current session should use aggressive trading mode"""
        current_session = self.get_current_trading_session()
        if current_session != 'none':
            return self.trading_sessions[current_session].get('aggressive_mode', False)
        return False
