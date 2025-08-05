"""
Arbitrage Strategy for AuraTrade Bot
Statistical arbitrage and correlation trading
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from analysis.technical_analysis import TechnicalAnalysis
from utils.logger import Logger

class ArbitrageStrategy:
    """Statistical arbitrage strategy with correlation analysis"""

    def __init__(self):
        self.logger = Logger().get_logger()
        self.technical_analysis = TechnicalAnalysis()

        # Strategy parameters
        self.name = "Arbitrage Strategy"
        self.timeframe = 'M15'
        self.correlation_threshold = 0.7
        self.spread_threshold = 2.0  # Z-score threshold
        self.min_correlation_period = 50

        # Currency pairs for correlation analysis
        self.major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
        self.correlation_pairs = [
            ('EURUSD', 'GBPUSD'),
            ('EURUSD', 'USDCHF'),
            ('GBPUSD', 'USDCHF')
        ]

        # Correlation cache
        self.correlation_cache = {}
        self.spread_cache = {}

        self.logger.info("ArbitrageStrategy initialized")

    def generate_signal(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Generate arbitrage signal based on correlation analysis"""
        try:
            # Use M15 data for arbitrage analysis
            if 'M15' not in data or data['M15'].empty:
                return {'action': 'HOLD', 'confidence': 0, 'reason': 'No M15 data'}

            df = data['M15'].copy()

            if len(df) < self.min_correlation_period:
                return {'action': 'HOLD', 'confidence': 0, 'reason': 'Insufficient data for correlation'}

            # Find best correlation pair for the symbol
            correlation_signal = self._analyze_correlations(symbol, data)

            # Analyze spread mean reversion
            spread_signal = self._analyze_spread_reversion(symbol, data)

            # Combine signals
            final_signal = self._combine_arbitrage_signals(correlation_signal, spread_signal)

            if final_signal and final_signal['action'] != 'HOLD':
                self.logger.info(f"Arbitrage signal: {symbol} {final_signal['action']} (confidence: {final_signal['confidence']:.2f})")

            return final_signal

        except Exception as e:
            self.logger.error(f"Error generating arbitrage signal for {symbol}: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reason': f'Error: {str(e)}'}

    def _analyze_correlations(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Analyze correlation-based opportunities"""
        try:
            if symbol not in self.major_pairs:
                return None

            # Find correlation pairs for this symbol
            relevant_pairs = [pair for pair in self.correlation_pairs if symbol in pair]

            best_signal = None
            best_confidence = 0

            for pair in relevant_pairs:
                other_symbol = pair[1] if pair[0] == symbol else pair[0]

                # Check if we have data for both symbols
                if other_symbol not in [s for s in data.keys() if 'M15' in data and not data['M15'].empty]:
                    continue

                # Calculate correlation and spread
                correlation_data = self._calculate_pair_correlation(symbol, other_symbol, data)

                if correlation_data and correlation_data['correlation'] > self.correlation_threshold:
                    # Analyze spread for mean reversion opportunity
                    spread_signal = self._analyze_pair_spread(symbol, other_symbol, correlation_data)

                    if spread_signal and spread_signal['confidence'] > best_confidence:
                        best_signal = spread_signal
                        best_confidence = spread_signal['confidence']

            return best_signal

        except Exception as e:
            self.logger.error(f"Error analyzing correlations: {e}")
            return None

    def _calculate_pair_correlation(self, symbol1: str, symbol2: str, data: Dict) -> Optional[Dict[str, Any]]:
        """Calculate correlation between two currency pairs"""
        try:
            # This is a simplified version - in real implementation,
            # you would need data for multiple symbols
            df1 = data.get('M15')
            if df1 is None or df1.empty:
                return None

            # For demonstration, we'll use different timeframes as proxy for different symbols
            df2 = data.get('M5')  # Proxy for second symbol
            if df2 is None or df2.empty:
                return None

            # Align data lengths
            min_length = min(len(df1), len(df2))
            if min_length < self.min_correlation_period:
                return None

            # Calculate returns
            returns1 = df1['close'].tail(min_length).pct_change().dropna()
            returns2 = df2['close'].tail(min_length).pct_change().dropna()

            # Align series
            min_length = min(len(returns1), len(returns2))
            returns1 = returns1.tail(min_length)
            returns2 = returns2.tail(min_length)

            # Calculate correlation
            correlation = returns1.corr(returns2)

            # Calculate spread (price ratio)
            price1 = df1['close'].tail(min_length)
            price2 = df2['close'].tail(min_length)
            spread = price1 / price2

            # Calculate spread statistics
            spread_mean = spread.mean()
            spread_std = spread.std()
            current_spread = spread.iloc[-1]
            z_score = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0

            return {
                'correlation': abs(correlation),
                'spread': current_spread,
                'spread_mean': spread_mean,
                'spread_std': spread_std,
                'z_score': z_score,
                'symbol1': symbol1,
                'symbol2': symbol2
            }

        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return None

    def _analyze_pair_spread(self, symbol1: str, symbol2: str, correlation_data: Dict) -> Optional[Dict[str, Any]]:
        """Analyze spread for mean reversion opportunity"""
        try:
            z_score = correlation_data['z_score']
            correlation = correlation_data['correlation']

            # Check for significant deviation
            if abs(z_score) < self.spread_threshold:
                return None

            # Determine trade direction
            if z_score > self.spread_threshold:
                # Spread is high - sell symbol1, buy symbol2
                # Since we can only trade one symbol, sell symbol1
                action = 'SELL'
                confidence = min(0.9, (abs(z_score) / 3.0) * correlation)
                reason = f'Spread high (z={z_score:.2f}), correlation={correlation:.2f}'
            elif z_score < -self.spread_threshold:
                # Spread is low - buy symbol1, sell symbol2
                action = 'BUY'
                confidence = min(0.9, (abs(z_score) / 3.0) * correlation)
                reason = f'Spread low (z={z_score:.2f}), correlation={correlation:.2f}'
            else:
                return None

            return {
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'z_score': z_score,
                'correlation': correlation,
                'strategy': self.name
            }

        except Exception as e:
            self.logger.error(f"Error analyzing pair spread: {e}")
            return None

    def _analyze_spread_reversion(self, symbol: str, data: Dict) -> Optional[Dict[str, Any]]:
        """Analyze single-symbol mean reversion"""
        try:
            df = data['M15'].copy()

            # Calculate Bollinger Bands for mean reversion
            bb_data = self.technical_analysis.calculate_bollinger_bands(df['close'], 20, 2)

            current_price = df['close'].iloc[-1]
            bb_upper = bb_data['upper'].iloc[-1]
            bb_lower = bb_data['lower'].iloc[-1]
            bb_middle = bb_data['middle'].iloc[-1]

            # Calculate position relative to bands
            if bb_upper > bb_lower:
                position = (current_price - bb_lower) / (bb_upper - bb_lower)
            else:
                return None

            # Check for extreme positions
            if position > 0.9:  # Near upper band
                return {
                    'action': 'SELL',
                    'confidence': min(0.8, position * 0.8),
                    'reason': f'Mean reversion sell (position: {position:.2f})',
                    'strategy': self.name
                }
            elif position < 0.1:  # Near lower band
                return {
                    'action': 'BUY',
                    'confidence': min(0.8, (1 - position) * 0.8),
                    'reason': f'Mean reversion buy (position: {position:.2f})',
                    'strategy': self.name
                }

            return None

        except Exception as e:
            self.logger.error(f"Error analyzing spread reversion: {e}")
            return None

    def _combine_arbitrage_signals(self, correlation_signal: Optional[Dict], 
                                 spread_signal: Optional[Dict]) -> Dict[str, Any]:
        """Combine different arbitrage signals"""
        try:
            signals = [s for s in [correlation_signal, spread_signal] if s is not None]

            if not signals:
                return {'action': 'HOLD', 'confidence': 0, 'reason': 'No arbitrage opportunities'}

            # If only one signal, return it
            if len(signals) == 1:
                return signals[0]

            # Combine multiple signals
            buy_signals = [s for s in signals if s['action'] == 'BUY']
            sell_signals = [s for s in signals if s['action'] == 'SELL']

            if len(buy_signals) > len(sell_signals):
                # More buy signals
                avg_confidence = sum(s['confidence'] for s in buy_signals) / len(buy_signals)
                return {
                    'action': 'BUY',
                    'confidence': avg_confidence,
                    'reason': f'Combined arbitrage buy ({len(buy_signals)} signals)',
                    'strategy': self.name
                }
            elif len(sell_signals) > len(buy_signals):
                # More sell signals
                avg_confidence = sum(s['confidence'] for s in sell_signals) / len(sell_signals)
                return {
                    'action': 'SELL',
                    'confidence': avg_confidence,
                    'reason': f'Combined arbitrage sell ({len(sell_signals)} signals)',
                    'strategy': self.name
                }
            else:
                # Conflicting signals
                return {'action': 'HOLD', 'confidence': 0, 'reason': 'Conflicting arbitrage signals'}

        except Exception as e:
            self.logger.error(f"Error combining arbitrage signals: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reason': f'Combination error: {str(e)}'}

    def get_correlation_status(self) -> Dict[str, Any]:
        """Get current correlation status"""
        try:
            status = {}

            for pair in self.correlation_pairs:
                pair_key = f"{pair[0]}_{pair[1]}"
                if pair_key in self.correlation_cache:
                    status[pair_key] = self.correlation_cache[pair_key]

            return status

        except Exception as e:
            self.logger.error(f"Error getting correlation status: {e}")
            return {}

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Statistical Arbitrage',
            'timeframe': self.timeframe,
            'risk_level': 'Low-Medium',
            'hold_duration': '15min - 4hrs',
            'description': 'Statistical arbitrage based on correlation and mean reversion',
            'pairs_monitored': len(self.correlation_pairs)
        }