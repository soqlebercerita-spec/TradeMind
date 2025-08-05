
"""
Portfolio Management Module for AuraTrade Bot
Track and manage trading portfolio performance
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from utils.logger import Logger, log_info, log_error, log_trade

class Portfolio:
    """Portfolio management and performance tracking"""
    
    def __init__(self, mt5_connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Portfolio state
        self.positions = {}
        self.trade_history = []
        self.daily_stats = {}
        self.performance_metrics = {}
        
        # Performance tracking
        self.starting_balance = 0
        self.peak_balance = 0
        self.current_drawdown = 0
        self.max_drawdown = 0
        
        self._initialize_portfolio()
        
    def _initialize_portfolio(self):
        """Initialize portfolio with current account state"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                self.starting_balance = account_info.get('balance', 0)
                self.peak_balance = self.starting_balance
                
            log_info("Portfolio", f"Initialized with balance: ${self.starting_balance:.2f}")
            
        except Exception as e:
            log_error("Portfolio", "Error initializing portfolio", e)
    
    def update_positions(self):
        """Update current positions from MT5"""
        try:
            positions = self.mt5_connector.get_positions()
            self.positions = {}
            
            for pos in positions:
                symbol = pos.get('symbol')
                self.positions[symbol] = {
                    'ticket': pos.get('ticket'),
                    'symbol': symbol,
                    'volume': pos.get('volume'),
                    'type': 'BUY' if pos.get('type') == 0 else 'SELL',
                    'open_price': pos.get('price_open'),
                    'current_price': pos.get('price_current'),
                    'profit': pos.get('profit'),
                    'swap': pos.get('swap'),
                    'commission': pos.get('commission'),
                    'open_time': pos.get('time'),
                    'sl': pos.get('sl'),
                    'tp': pos.get('tp')
                }
            
            return self.positions
            
        except Exception as e:
            log_error("Portfolio", "Error updating positions", e)
            return {}
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        try:
            account_info = self.mt5_connector.get_account_info()
            positions = self.update_positions()
            
            current_balance = account_info.get('balance', 0)
            current_equity = account_info.get('equity', 0)
            current_margin = account_info.get('margin', 0)
            free_margin = account_info.get('free_margin', 0)
            
            # Calculate performance metrics
            total_profit_loss = current_balance - self.starting_balance
            profit_loss_percent = (total_profit_loss / self.starting_balance * 100) if self.starting_balance > 0 else 0
            
            # Update drawdown
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance
                self.current_drawdown = 0
            else:
                self.current_drawdown = (self.peak_balance - current_balance) / self.peak_balance * 100
                self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
            
            # Position summary
            open_positions = len(positions)
            total_position_profit = sum(pos.get('profit', 0) for pos in positions.values())
            
            # Risk metrics
            margin_level = (current_equity / current_margin * 100) if current_margin > 0 else 0
            
            summary = {
                'timestamp': datetime.now(),
                'account': {
                    'balance': current_balance,
                    'equity': current_equity,
                    'margin': current_margin,
                    'free_margin': free_margin,
                    'margin_level': margin_level
                },
                'performance': {
                    'starting_balance': self.starting_balance,
                    'total_pnl': total_profit_loss,
                    'pnl_percent': profit_loss_percent,
                    'current_drawdown': self.current_drawdown,
                    'max_drawdown': self.max_drawdown,
                    'peak_balance': self.peak_balance
                },
                'positions': {
                    'open_count': open_positions,
                    'total_profit': total_position_profit,
                    'symbols': list(positions.keys())
                },
                'risk': {
                    'margin_usage': (current_margin / current_equity * 100) if current_equity > 0 else 0,
                    'free_margin_percent': (free_margin / current_equity * 100) if current_equity > 0 else 0
                }
            }
            
            return summary
            
        except Exception as e:
            log_error("Portfolio", "Error getting portfolio summary", e)
            return {}
    
    def record_trade(self, trade_info: Dict[str, Any]):
        """Record completed trade for performance analysis"""
        try:
            trade_record = {
                'timestamp': datetime.now(),
                'ticket': trade_info.get('ticket'),
                'symbol': trade_info.get('symbol'),
                'type': trade_info.get('type'),
                'volume': trade_info.get('volume'),
                'open_price': trade_info.get('open_price'),
                'close_price': trade_info.get('close_price'),
                'profit': trade_info.get('profit'),
                'commission': trade_info.get('commission'),
                'swap': trade_info.get('swap'),
                'duration': trade_info.get('duration', 0),
                'strategy': trade_info.get('strategy', 'Unknown')
            }
            
            self.trade_history.append(trade_record)
            
            # Log the trade
            profit_loss = trade_record.get('profit', 0)
            symbol = trade_record.get('symbol')
            trade_type = trade_record.get('type')
            volume = trade_record.get('volume')
            
            log_trade(
                f"{trade_type} CLOSED",
                symbol,
                f"Volume: {volume}, P&L: ${profit_loss:.2f}"
            )
            
            # Update daily statistics
            self._update_daily_stats(trade_record)
            
        except Exception as e:
            log_error("Portfolio", "Error recording trade", e)
    
    def _update_daily_stats(self, trade_record: Dict[str, Any]):
        """Update daily trading statistics"""
        try:
            today = datetime.now().date()
            
            if today not in self.daily_stats:
                self.daily_stats[today] = {
                    'trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_profit': 0,
                    'gross_profit': 0,
                    'gross_loss': 0,
                    'volume_traded': 0
                }
            
            stats = self.daily_stats[today]
            profit = trade_record.get('profit', 0)
            volume = trade_record.get('volume', 0)
            
            stats['trades'] += 1
            stats['total_profit'] += profit
            stats['volume_traded'] += volume
            
            if profit > 0:
                stats['winning_trades'] += 1
                stats['gross_profit'] += profit
            else:
                stats['losing_trades'] += 1
                stats['gross_loss'] += abs(profit)
            
        except Exception as e:
            log_error("Portfolio", "Error updating daily stats", e)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            if not self.trade_history:
                return {}
            
            # Basic metrics
            total_trades = len(self.trade_history)
            winning_trades = sum(1 for trade in self.trade_history if trade.get('profit', 0) > 0)
            losing_trades = total_trades - winning_trades
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Profit metrics
            profits = [trade.get('profit', 0) for trade in self.trade_history]
            total_profit = sum(profits)
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            
            winning_profits = [p for p in profits if p > 0]
            losing_profits = [p for p in profits if p < 0]
            
            avg_win = sum(winning_profits) / len(winning_profits) if winning_profits else 0
            avg_loss = sum(losing_profits) / len(losing_profits) if losing_profits else 0
            
            profit_factor = (sum(winning_profits) / abs(sum(losing_profits))) if losing_profits else float('inf')
            
            # Risk metrics
            sharpe_ratio = self._calculate_sharpe_ratio(profits)
            
            # Trading frequency
            first_trade = min(trade['timestamp'] for trade in self.trade_history)
            days_trading = (datetime.now() - first_trade).days or 1
            trades_per_day = total_trades / days_trading
            
            metrics = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'avg_profit_per_trade': avg_profit,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'current_drawdown': self.current_drawdown,
                'trades_per_day': trades_per_day,
                'days_trading': days_trading
            }
            
            return metrics
            
        except Exception as e:
            log_error("Portfolio", "Error calculating performance metrics", e)
            return {}
    
    def _calculate_sharpe_ratio(self, profits: List[float]) -> float:
        """Calculate Sharpe ratio for performance evaluation"""
        try:
            if len(profits) < 2:
                return 0
            
            # Calculate returns
            returns = pd.Series(profits)
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Sharpe ratio (assuming risk-free rate of 0)
            sharpe = mean_return / std_return if std_return != 0 else 0
            
            return sharpe
            
        except Exception as e:
            log_error("Portfolio", "Error calculating Sharpe ratio", e)
            return 0
    
    def get_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get daily trading report"""
        try:
            target_date = (date or datetime.now()).date()
            
            if target_date not in self.daily_stats:
                return {
                    'date': target_date,
                    'trades': 0,
                    'profit': 0,
                    'win_rate': 0
                }
            
            stats = self.daily_stats[target_date]
            
            win_rate = (stats['winning_trades'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            
            report = {
                'date': target_date,
                'trades': stats['trades'],
                'winning_trades': stats['winning_trades'],
                'losing_trades': stats['losing_trades'],
                'win_rate': win_rate,
                'total_profit': stats['total_profit'],
                'gross_profit': stats['gross_profit'],
                'gross_loss': stats['gross_loss'],
                'volume_traded': stats['volume_traded'],
                'avg_profit_per_trade': stats['total_profit'] / stats['trades'] if stats['trades'] > 0 else 0
            }
            
            return report
            
        except Exception as e:
            log_error("Portfolio", f"Error getting daily report for {target_date}", e)
            return {}
    
    def reset_performance_tracking(self):
        """Reset performance tracking (for new trading period)"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                self.starting_balance = account_info.get('balance', 0)
                self.peak_balance = self.starting_balance
            
            self.current_drawdown = 0
            self.max_drawdown = 0
            self.trade_history = []
            self.daily_stats = {}
            
            log_info("Portfolio", "Performance tracking reset")
            
        except Exception as e:
            log_error("Portfolio", "Error resetting performance tracking", e)
