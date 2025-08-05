
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
"""
Runtime settings manager for AuraTrade Bot
Dynamic configuration that can be changed during runtime
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class Settings:
    """Runtime settings manager with persistence"""
    
    def __init__(self):
        self.settings_file = "AuraTrade/config/runtime_settings.json"
        self.settings = self._load_default_settings()
        self.load_settings()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default runtime settings"""
        return {
            'last_updated': datetime.now().isoformat(),
            'trading': {
                'auto_start': True,
                'current_mode': 'live',  # live, demo, paper
                'pause_trading': False,
                'emergency_stop': False
            },
            'risk': {
                'current_risk_per_trade': 1.0,
                'dynamic_risk_adjustment': True,
                'consecutive_losses_count': 0,
                'daily_trades_count': 0,
                'daily_pnl': 0.0
            },
            'strategies': {
                'active_strategies': ['hft', 'scalping', 'pattern'],
                'strategy_weights': {
                    'hft': 0.3,
                    'scalping': 0.4,
                    'pattern': 0.3
                }
            },
            'ml': {
                'predictions_enabled': False,
                'model_last_updated': None,
                'prediction_accuracy': 0.0
            },
            'session': {
                'session_start': None,
                'total_trades': 0,
                'winning_trades': 0,
                'current_win_rate': 0.0,
                'best_win_rate': 0.0,
                'total_profit': 0.0
            },
            'alerts': {
                'high_drawdown_alert': True,
                'low_win_rate_alert': True,
                'connection_loss_alert': True,
                'daily_summary_enabled': True
            }
        }
    
    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                return True
            return False
        except Exception as e:
            print(f"Error loading settings: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            self.settings['last_updated'] = datetime.now().isoformat()
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get setting value using dot notation (e.g., 'trading.auto_start')"""
        try:
            keys = key_path.split('.')
            value = self.settings
            
            for key in keys:
                value = value[key]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Set setting value using dot notation"""
        try:
            keys = key_path.split('.')
            current = self.settings
            
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = value
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error setting value: {e}")
            return False
    
    def is_trading_paused(self) -> bool:
        """Check if trading is paused"""
        return self.get('trading.pause_trading', False)
    
    def is_emergency_stop(self) -> bool:
        """Check if emergency stop is active"""
        return self.get('trading.emergency_stop', False)
    
    def get_current_risk(self) -> float:
        """Get current risk per trade"""
        return self.get('risk.current_risk_per_trade', 1.0)
    
    def get_active_strategies(self) -> list:
        """Get list of active strategies"""
        return self.get('strategies.active_strategies', [])
    
    def update_daily_stats(self, trades_count: int, pnl: float, win_rate: float):
        """Update daily trading statistics"""
        self.set('risk.daily_trades_count', trades_count)
        self.set('risk.daily_pnl', pnl)
        self.set('session.current_win_rate', win_rate)
        
        # Update best win rate
        best_rate = self.get('session.best_win_rate', 0.0)
        if win_rate > best_rate:
            self.set('session.best_win_rate', win_rate)
    
    def reset_daily_counters(self):
        """Reset daily counters for new trading day"""
        self.set('risk.daily_trades_count', 0)
        self.set('risk.daily_pnl', 0.0)
        self.set('risk.consecutive_losses_count', 0)
        self.set('session.session_start', datetime.now().isoformat())
    
    def increment_consecutive_losses(self):
        """Increment consecutive losses counter"""
        current = self.get('risk.consecutive_losses_count', 0)
        self.set('risk.consecutive_losses_count', current + 1)
    
    def reset_consecutive_losses(self):
        """Reset consecutive losses counter"""
        self.set('risk.consecutive_losses_count', 0)
    
    def adjust_risk_dynamically(self, win_rate: float):
        """Dynamically adjust risk based on performance"""
        if not self.get('risk.dynamic_risk_adjustment', True):
            return
        
        base_risk = 1.0
        
        if win_rate >= 90:
            # Excellent performance - slightly increase risk
            adjusted_risk = base_risk * 1.2
        elif win_rate >= 80:
            # Good performance - normal risk
            adjusted_risk = base_risk
        elif win_rate >= 70:
            # Acceptable performance - slightly reduce risk
            adjusted_risk = base_risk * 0.8
        else:
            # Poor performance - significantly reduce risk
            adjusted_risk = base_risk * 0.5
        
        # Cap the risk adjustment
        adjusted_risk = max(0.5, min(adjusted_risk, 2.0))
        self.set('risk.current_risk_per_trade', adjusted_risk)
    
    def get_strategy_weight(self, strategy_name: str) -> float:
        """Get weight for specific strategy"""
        weights = self.get('strategies.strategy_weights', {})
        return weights.get(strategy_name, 0.0)
    
    def pause_trading(self):
        """Pause trading"""
        self.set('trading.pause_trading', True)
    
    def resume_trading(self):
        """Resume trading"""
        self.set('trading.pause_trading', False)
    
    def emergency_stop(self):
        """Activate emergency stop"""
        self.set('trading.emergency_stop', True)
        self.set('trading.pause_trading', True)
    
    def reset_emergency_stop(self):
        """Reset emergency stop"""
        self.set('trading.emergency_stop', False)
    
    def export_settings(self, filename: Optional[str] = None) -> str:
        """Export settings to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AuraTrade/exports/settings_backup_{timestamp}.json"
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w') as f:
                json.dump(self.settings, f, indent=2, default=str)
            
            return filename
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return ""
    
    def import_settings(self, filename: str) -> bool:
        """Import settings from file"""
        try:
            with open(filename, 'r') as f:
                imported_settings = json.load(f)
            
            self.settings.update(imported_settings)
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False
