"""
Portfolio Management for AuraTrade Bot
Position tracking, risk management, and performance analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from core.mt5_connector import MT5Connector
from utils.logger import Logger

class Portfolio:
    """Portfolio management and tracking"""

    def __init__(self, mt5_connector: MT5Connector):
        self.logger = Logger().get_logger()
        self.mt5_connector = mt5_connector

        # Portfolio tracking
        self.positions = {}
        self.closed_trades = []
        self.daily_stats = {}
        self.portfolio_history = []

        # Performance metrics
        self.initial_balance = 0.0
        self.current_balance = 0.0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.max_drawdown = 0.0
        self.max_equity = 0.0

        self.logger.info("Portfolio manager initialized")

    def update_portfolio(self):
        """Update portfolio with current positions and account info"""
        try:
            # Get current account info
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return

            self.current_balance = account_info.get('balance', 0.0)
            current_equity = account_info.get('equity', 0.0)

            # Set initial balance if not set
            if self.initial_balance == 0.0:
                self.initial_balance = self.current_balance

            # Update max equity for drawdown calculation
            if current_equity > self.max_equity:
                self.max_equity = current_equity

            # Calculate drawdown
            if self.max_equity > 0:
                current_drawdown = (self.max_equity - current_equity) / self.max_equity * 100
                if current_drawdown > self.max_drawdown:
                    self.max_drawdown = current_drawdown

            # Get current positions
            positions = self.mt5_connector.get_positions()
            self.positions = {pos['ticket']: pos for pos in positions}

            # Update portfolio history
            self.portfolio_history.append({
                'timestamp': datetime.now(),
                'balance': self.current_balance,
                'equity': current_equity,
                'margin': account_info.get('margin', 0.0),
                'free_margin': account_info.get('margin_free', 0.0),
                'margin_level': account_info.get('margin_level', 0.0),
                'positions_count': len(positions),
                'unrealized_pnl': sum(pos['profit'] for pos in positions)
            })

            # Keep only last 1000 records
            if len(self.portfolio_history) > 1000:
                self.portfolio_history = self.portfolio_history[-1000:]

        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")

    def add_closed_trade(self, trade_info: Dict):
        """Add closed trade to history"""
        try:
            trade_data = {
                'ticket': trade_info.get('ticket'),
                'symbol': trade_info.get('symbol'),
                'type': trade_info.get('type'),
                'volume': trade_info.get('volume'),
                'open_price': trade_info.get('price_open'),
                'close_price': trade_info.get('price_close'),
                'open_time': trade_info.get('time_open'),
                'close_time': trade_info.get('time_close'),
                'profit': trade_info.get('profit', 0.0),
                'commission': trade_info.get('commission', 0.0),
                'swap': trade_info.get('swap', 0.0),
                'comment': trade_info.get('comment', '')
            }

            self.closed_trades.append(trade_data)

            # Update win/loss counters
            profit = trade_data['profit']
            if profit > 0:
                self.win_count += 1
                self.total_profit += profit
            else:
                self.loss_count += 1
                self.total_loss += abs(profit)

            # Keep only last 1000 trades
            if len(self.closed_trades) > 1000:
                self.closed_trades = self.closed_trades[-1000:]

        except Exception as e:
            self.logger.error(f"Error adding closed trade: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            total_trades = self.win_count + self.loss_count
            win_rate = (self.win_count / total_trades * 100) if total_trades > 0 else 0.0

            # Profit factor
            profit_factor = (self.total_profit / self.total_loss) if self.total_loss > 0 else float('inf')

            # Return on Investment
            roi = ((self.current_balance - self.initial_balance) / self.initial_balance * 100) if self.initial_balance > 0 else 0.0

            # Average trade metrics
            avg_win = self.total_profit / self.win_count if self.win_count > 0 else 0.0
            avg_loss = self.total_loss / self.loss_count if self.loss_count > 0 else 0.0

            # Sharpe-like ratio (simplified)
            if len(self.portfolio_history) > 1:
                returns = []
                for i in range(1, len(self.portfolio_history)):
                    prev_equity = self.portfolio_history[i-1]['equity']
                    curr_equity = self.portfolio_history[i]['equity']
                    if prev_equity > 0:
                        returns.append((curr_equity - prev_equity) / prev_equity)

                if returns:
                    avg_return = np.mean(returns)
                    std_return = np.std(returns)
                    sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0

            return {
                'total_trades': total_trades,
                'winning_trades': self.win_count,
                'losing_trades': self.loss_count,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_profit': self.total_profit,
                'total_loss': self.total_loss,
                'net_profit': self.total_profit - self.total_loss,
                'roi': roi,
                'max_drawdown': self.max_drawdown,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'sharpe_ratio': sharpe_ratio,
                'current_balance': self.current_balance,
                'initial_balance': self.initial_balance
            }

        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get today's trading statistics"""
        try:
            today = datetime.now().date()

            # Filter today's trades
            today_trades = [
                trade for trade in self.closed_trades
                if datetime.fromtimestamp(trade.get('close_time', 0)).date() == today
            ]

            if not today_trades:
                return {
                    'trades_today': 0,
                    'profit_today': 0.0,
                    'win_rate_today': 0.0,
                    'best_trade': 0.0,
                    'worst_trade': 0.0
                }

            profits = [trade['profit'] for trade in today_trades]
            wins_today = len([p for p in profits if p > 0])

            return {
                'trades_today': len(today_trades),
                'profit_today': sum(profits),
                'win_rate_today': (wins_today / len(today_trades) * 100) if today_trades else 0.0,
                'best_trade': max(profits) if profits else 0.0,
                'worst_trade': min(profits) if profits else 0.0
            }

        except Exception as e:
            self.logger.error(f"Error calculating daily stats: {e}")
            return {}

    def get_symbol_performance(self) -> Dict[str, Dict]:
        """Get performance breakdown by symbol"""
        try:
            symbol_stats = {}

            for trade in self.closed_trades:
                symbol = trade.get('symbol', 'UNKNOWN')
                profit = trade.get('profit', 0.0)

                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'total_profit': 0.0,
                        'total_loss': 0.0,
                        'net_profit': 0.0
                    }

                stats = symbol_stats[symbol]
                stats['trades'] += 1

                if profit > 0:
                    stats['wins'] += 1
                    stats['total_profit'] += profit
                else:
                    stats['losses'] += 1
                    stats['total_loss'] += abs(profit)

                stats['net_profit'] = stats['total_profit'] - stats['total_loss']

            # Calculate win rates
            for symbol, stats in symbol_stats.items():
                if stats['trades'] > 0:
                    stats['win_rate'] = (stats['wins'] / stats['trades']) * 100
                else:
                    stats['win_rate'] = 0.0

            return symbol_stats

        except Exception as e:
            self.logger.error(f"Error calculating symbol performance: {e}")
            return {}

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Calculate risk-related metrics"""
        try:
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return {}

            balance = account_info.get('balance', 0.0)
            equity = account_info.get('equity', 0.0)
            margin = account_info.get('margin', 0.0)
            free_margin = account_info.get('margin_free', 0.0)
            margin_level = account_info.get('margin_level', 0.0)

            # Risk per trade (assuming 1% risk)
            risk_per_trade = balance * 0.01

            # Position sizing based on current margin
            max_positions = int(free_margin / (balance * 0.02)) if balance > 0 else 0

            return {
                'account_balance': balance,
                'account_equity': equity,
                'used_margin': margin,
                'free_margin': free_margin,
                'margin_level': margin_level,
                'max_drawdown': self.max_drawdown,
                'risk_per_trade': risk_per_trade,
                'max_recommended_positions': max_positions,
                'equity_to_balance_ratio': (equity / balance * 100) if balance > 0 else 0.0
            }

        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}

    def export_portfolio_data(self) -> Dict[str, Any]:
        """Export comprehensive portfolio data"""
        return {
            'performance_metrics': self.get_performance_metrics(),
            'daily_stats': self.get_daily_stats(),
            'symbol_performance': self.get_symbol_performance(),
            'risk_metrics': self.get_risk_metrics(),
            'current_positions': self.positions,
            'recent_trades': self.closed_trades[-50:],  # Last 50 trades
            'portfolio_history': self.portfolio_history[-100:],  # Last 100 records
            'export_timestamp': datetime.now().isoformat()
        }