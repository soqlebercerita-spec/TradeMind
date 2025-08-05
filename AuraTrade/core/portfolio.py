
"""
Portfolio management for AuraTrade Bot
Tracks performance, risk, and portfolio metrics
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class Portfolio:
    """Portfolio management and performance tracking"""

    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector
        
        # Portfolio metrics
        self.initial_balance = 0.0
        self.peak_balance = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.max_drawdown = 0.0
        
        # Performance tracking
        self.trade_history = []
        self.daily_performance = {}
        
        self.logger.info("Portfolio manager initialized")

    def initialize(self) -> bool:
        """Initialize portfolio with current account state"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return False
            
            self.initial_balance = account_info.get('balance', 0)
            self.peak_balance = self.initial_balance
            
            self.logger.info(f"Portfolio initialized with balance: ${self.initial_balance:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing portfolio: {e}")
            return False

    def update_performance(self) -> None:
        """Update portfolio performance metrics"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return
            
            current_balance = account_info.get('balance', 0)
            current_equity = account_info.get('equity', 0)
            
            # Update peak balance
            if current_equity > self.peak_balance:
                self.peak_balance = current_equity
            
            # Calculate drawdown
            if self.peak_balance > 0:
                current_drawdown = ((self.peak_balance - current_equity) / self.peak_balance) * 100
                if current_drawdown > self.max_drawdown:
                    self.max_drawdown = current_drawdown
            
            # Update daily performance
            today = datetime.now().date()
            if today not in self.daily_performance:
                self.daily_performance[today] = {
                    'starting_balance': current_balance,
                    'trades': 0,
                    'pnl': 0.0
                }
            
        except Exception as e:
            self.logger.error(f"Error updating performance: {e}")

    def record_trade(self, trade_result: Dict[str, Any]) -> None:
        """Record completed trade"""
        try:
            self.total_trades += 1
            profit = trade_result.get('profit', 0.0)
            
            if profit > 0:
                self.winning_trades += 1
                self.total_profit += profit
            else:
                self.losing_trades += 1
                self.total_loss += abs(profit)
            
            # Record trade details
            trade_record = {
                'timestamp': datetime.now(),
                'symbol': trade_result.get('symbol', ''),
                'type': trade_result.get('type', ''),
                'volume': trade_result.get('volume', 0),
                'profit': profit,
                'duration': trade_result.get('duration', 0)
            }
            
            self.trade_history.append(trade_record)
            
            # Update daily performance
            today = datetime.now().date()
            if today in self.daily_performance:
                self.daily_performance[today]['trades'] += 1
                self.daily_performance[today]['pnl'] += profit
            
            self.logger.info(f"Trade recorded: {profit:.2f} profit")
            
        except Exception as e:
            self.logger.error(f"Error recording trade: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            account_info = self.mt5_connector.get_account_info()
            current_balance = account_info.get('balance', 0) if account_info else 0
            
            # Calculate metrics
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            avg_win = self.total_profit / self.winning_trades if self.winning_trades > 0 else 0
            avg_loss = self.total_loss / self.losing_trades if self.losing_trades > 0 else 0
            profit_factor = self.total_profit / self.total_loss if self.total_loss > 0 else 0
            
            total_return = ((current_balance - self.initial_balance) / self.initial_balance * 100) if self.initial_balance > 0 else 0
            
            return {
                'initial_balance': self.initial_balance,
                'current_balance': current_balance,
                'total_return': total_return,
                'peak_balance': self.peak_balance,
                'max_drawdown': self.max_drawdown,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'total_profit': self.total_profit,
                'total_loss': self.total_loss,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'sharpe_ratio': self._calculate_sharpe_ratio(),
                'target_win_rate': 75.0,
                'performance_grade': self._calculate_performance_grade(win_rate)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {}

    def get_daily_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily performance for last N days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            daily_data = []
            current_date = start_date
            
            while current_date <= end_date:
                if current_date in self.daily_performance:
                    daily_data.append({
                        'date': current_date,
                        **self.daily_performance[current_date]
                    })
                else:
                    daily_data.append({
                        'date': current_date,
                        'trades': 0,
                        'pnl': 0.0
                    })
                
                current_date += timedelta(days=1)
            
            return daily_data
            
        except Exception as e:
            self.logger.error(f"Error getting daily performance: {e}")
            return []

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""
        try:
            if len(self.trade_history) < 10:
                return 0.0
            
            # Get returns from last 30 trades
            recent_trades = self.trade_history[-30:]
            returns = [trade['profit'] for trade in recent_trades]
            
            if not returns:
                return 0.0
            
            mean_return = sum(returns) / len(returns)
            std_return = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5
            
            if std_return == 0:
                return 0.0
            
            # Annualized Sharpe ratio (assuming 252 trading days)
            sharpe = (mean_return / std_return) * (252 ** 0.5)
            return sharpe
            
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    def _calculate_performance_grade(self, win_rate: float) -> str:
        """Calculate performance grade based on win rate"""
        if win_rate >= 75:
            return "A+"
        elif win_rate >= 70:
            return "A"
        elif win_rate >= 65:
            return "B+"
        elif win_rate >= 60:
            return "B"
        elif win_rate >= 55:
            return "C+"
        elif win_rate >= 50:
            return "C"
        else:
            return "D"

    def export_performance_report(self) -> str:
        """Export performance report as string"""
        try:
            summary = self.get_performance_summary()
            
            report = f"""
AuraTrade Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== ACCOUNT SUMMARY ===
Initial Balance: ${summary.get('initial_balance', 0):.2f}
Current Balance: ${summary.get('current_balance', 0):.2f}
Total Return: {summary.get('total_return', 0):.2f}%
Peak Balance: ${summary.get('peak_balance', 0):.2f}
Max Drawdown: {summary.get('max_drawdown', 0):.2f}%

=== TRADING STATISTICS ===
Total Trades: {summary.get('total_trades', 0)}
Winning Trades: {summary.get('winning_trades', 0)}
Losing Trades: {summary.get('losing_trades', 0)}
Win Rate: {summary.get('win_rate', 0):.2f}% (Target: 75%+)
Performance Grade: {summary.get('performance_grade', 'N/A')}

=== PROFIT/LOSS ===
Total Profit: ${summary.get('total_profit', 0):.2f}
Total Loss: ${summary.get('total_loss', 0):.2f}
Average Win: ${summary.get('avg_win', 0):.2f}
Average Loss: ${summary.get('avg_loss', 0):.2f}
Profit Factor: {summary.get('profit_factor', 0):.2f}

=== RISK METRICS ===
Sharpe Ratio: {summary.get('sharpe_ratio', 0):.2f}
Max Drawdown: {summary.get('max_drawdown', 0):.2f}%

=== PERFORMANCE TARGET ===
Target Win Rate: 75%+
Current Achievement: {summary.get('win_rate', 0):.2f}%
Status: {'✅ ACHIEVED' if summary.get('win_rate', 0) >= 75 else '🎯 IN PROGRESS'}
            """
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error exporting performance report: {e}")
            return "Error generating report"
