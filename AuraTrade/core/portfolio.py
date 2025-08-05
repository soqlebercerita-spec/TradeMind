
"""
Portfolio management for AuraTrade Bot
Tracks performance, risk, and portfolio metrics
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class PortfolioManager:
    """Advanced portfolio tracking and analysis"""

    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5 = mt5_connector
        
        # Performance tracking
        self.trade_history = []
        self.daily_stats = {}
        self.monthly_stats = {}
        
        # Risk metrics
        self.max_drawdown = 0.0
        self.current_drawdown = 0.0
        self.peak_balance = 0.0
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.gross_profit = 0.0
        self.gross_loss = 0.0
        
        self.logger.info("PortfolioManager initialized")

    def update_portfolio(self):
        """Update portfolio metrics"""
        try:
            # Get current account info
            account = self.mt5.get_account_info()
            if not account:
                return
            
            current_balance = account.get('balance', 0)
            current_equity = account.get('equity', 0)
            
            # Update peak balance
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance
            
            # Calculate drawdown
            if self.peak_balance > 0:
                self.current_drawdown = (self.peak_balance - current_balance) / self.peak_balance
                if self.current_drawdown > self.max_drawdown:
                    self.max_drawdown = self.current_drawdown
            
            # Update daily stats
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.daily_stats:
                self.daily_stats[today] = {
                    'start_balance': current_balance,
                    'trades': 0,
                    'profit': 0.0,
                    'wins': 0,
                    'losses': 0
                }
            
            # Get positions for current profit calculation
            positions = self.mt5.get_positions()
            unrealized_pnl = sum(pos['profit'] for pos in positions)
            
            return {
                'balance': current_balance,
                'equity': current_equity,
                'unrealized_pnl': unrealized_pnl,
                'current_drawdown': self.current_drawdown,
                'max_drawdown': self.max_drawdown,
                'peak_balance': self.peak_balance
            }
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")
            return {}

    def record_trade(self, trade_data: Dict[str, Any]):
        """Record completed trade"""
        try:
            self.trade_history.append({
                'timestamp': datetime.now(),
                'symbol': trade_data.get('symbol', ''),
                'type': trade_data.get('type', ''),
                'volume': trade_data.get('volume', 0),
                'entry_price': trade_data.get('entry_price', 0),
                'exit_price': trade_data.get('exit_price', 0),
                'profit': trade_data.get('profit', 0),
                'duration': trade_data.get('duration', 0),
                'strategy': trade_data.get('strategy', '')
            })
            
            # Update statistics
            self.total_trades += 1
            profit = trade_data.get('profit', 0)
            
            if profit > 0:
                self.winning_trades += 1
                self.gross_profit += profit
            else:
                self.losing_trades += 1
                self.gross_loss += abs(profit)
            
            self.total_profit += profit
            
            # Update daily stats
            today = datetime.now().strftime('%Y-%m-%d')
            if today in self.daily_stats:
                self.daily_stats[today]['trades'] += 1
                self.daily_stats[today]['profit'] += profit
                if profit > 0:
                    self.daily_stats[today]['wins'] += 1
                else:
                    self.daily_stats[today]['losses'] += 1
            
            self.logger.info(f"Trade recorded: {trade_data.get('symbol', '')} P&L: {profit:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error recording trade: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            # Calculate win rate
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            # Calculate profit factor
            profit_factor = (self.gross_profit / abs(self.gross_loss)) if self.gross_loss != 0 else 0
            
            # Calculate average win/loss
            avg_win = (self.gross_profit / self.winning_trades) if self.winning_trades > 0 else 0
            avg_loss = (abs(self.gross_loss) / self.losing_trades) if self.losing_trades > 0 else 0
            
            # Calculate risk-reward ratio
            risk_reward_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0
            
            # Get recent performance (last 30 trades)
            recent_trades = self.trade_history[-30:] if len(self.trade_history) >= 30 else self.trade_history
            recent_wins = sum(1 for trade in recent_trades if trade['profit'] > 0)
            recent_win_rate = (recent_wins / len(recent_trades) * 100) if recent_trades else 0
            
            return {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'total_profit': self.total_profit,
                'gross_profit': self.gross_profit,
                'gross_loss': self.gross_loss,
                'profit_factor': profit_factor,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'risk_reward_ratio': risk_reward_ratio,
                'max_drawdown': self.max_drawdown,
                'current_drawdown': self.current_drawdown,
                'recent_win_rate': recent_win_rate,
                'peak_balance': self.peak_balance
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}

    def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """Get daily performance summary"""
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            if date not in self.daily_stats:
                return {}
            
            stats = self.daily_stats[date]
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            
            return {
                'date': date,
                'trades': stats['trades'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': win_rate,
                'profit': stats['profit'],
                'start_balance': stats['start_balance']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting daily summary: {e}")
            return {}

    def get_symbol_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by symbol"""
        try:
            symbol_stats = {}
            
            for trade in self.trade_history:
                symbol = trade['symbol']
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'profit': 0.0
                    }
                
                symbol_stats[symbol]['trades'] += 1
                symbol_stats[symbol]['profit'] += trade['profit']
                
                if trade['profit'] > 0:
                    symbol_stats[symbol]['wins'] += 1
                else:
                    symbol_stats[symbol]['losses'] += 1
            
            # Calculate win rates
            for symbol in symbol_stats:
                stats = symbol_stats[symbol]
                stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            
            return symbol_stats
            
        except Exception as e:
            self.logger.error(f"Error getting symbol performance: {e}")
            return {}

    def get_strategy_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by strategy"""
        try:
            strategy_stats = {}
            
            for trade in self.trade_history:
                strategy = trade.get('strategy', 'Unknown')
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        'trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'profit': 0.0
                    }
                
                strategy_stats[strategy]['trades'] += 1
                strategy_stats[strategy]['profit'] += trade['profit']
                
                if trade['profit'] > 0:
                    strategy_stats[strategy]['wins'] += 1
                else:
                    strategy_stats[strategy]['losses'] += 1
            
            # Calculate win rates
            for strategy in strategy_stats:
                stats = strategy_stats[strategy]
                stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            
            return strategy_stats
            
        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {e}")
            return {}

    def export_trade_history(self, filename: str = None) -> str:
        """Export trade history to CSV"""
        try:
            if filename is None:
                filename = f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            if not self.trade_history:
                return "No trade history to export"
            
            df = pd.DataFrame(self.trade_history)
            df.to_csv(filename, index=False)
            
            self.logger.info(f"Trade history exported to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting trade history: {e}")
            return f"Export failed: {e}"

    def reset_statistics(self):
        """Reset all statistics (use with caution)"""
        try:
            self.trade_history = []
            self.daily_stats = {}
            self.monthly_stats = {}
            self.total_trades = 0
            self.winning_trades = 0
            self.losing_trades = 0
            self.total_profit = 0.0
            self.gross_profit = 0.0
            self.gross_loss = 0.0
            self.max_drawdown = 0.0
            self.current_drawdown = 0.0
            self.peak_balance = 0.0
            
            self.logger.info("Portfolio statistics reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting statistics: {e}")
