
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
        
        # Performance targets for 85%+ win rate
        self.performance_targets = {
            'daily_profit_target': 2.0,      # 2% daily profit target
            'daily_loss_limit': -1.5,       # -1.5% daily loss limit (conservative)
            'weekly_profit_target': 10.0,   # 10% weekly profit target
            'monthly_profit_target': 30.0,  # 30% monthly profit target
            'max_consecutive_losses': 3,    # Stop after 3 consecutive losses
            'profit_protection': 80.0,       # Protect 80% of profits above target
            'target_win_rate': 85.0         # Target 85% win rate
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
                        for key, value in strategy_data.items():
                            if hasattr(self.strategies[strategy_name], key):
                                setattr(self.strategies[strategy_name], key, value)
            
            return True
            
        except FileNotFoundError:
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
                'performance_targets': self.performance_targets,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
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
