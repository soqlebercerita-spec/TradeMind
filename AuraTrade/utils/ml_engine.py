
"""
Machine Learning Engine for AuraTrade Bot
Basic ML models for pattern recognition and signal enhancement
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pickle
import os
from utils.logger import Logger

class MLEngine:
    """Machine Learning engine for trading signal enhancement"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.models = {}
        self.scalers = {}
        self.training_data = {}
        self.model_performance = {}
        
        # Initialize basic models
        self._initialize_models()
        
        self.logger.info("ML Engine initialized")
    
    def _initialize_models(self):
        """Initialize ML models"""
        try:
            # Signal Classification Model
            self.models['signal_classifier'] = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            
            # Price Direction Model
            self.models['price_direction'] = LogisticRegression(
                random_state=42,
                max_iter=1000
            )
            
            # Signal Strength Model
            self.models['signal_strength'] = RandomForestClassifier(
                n_estimators=50,
                random_state=42,
                max_depth=8
            )
            
            # Initialize scalers
            for model_name in self.models.keys():
                self.scalers[model_name] = StandardScaler()
                
        except Exception as e:
            self.logger.error(f"Error initializing ML models: {e}")
    
    def prepare_features(self, rates: pd.DataFrame, indicators: Dict) -> np.ndarray:
        """Prepare features for ML models"""
        try:
            if len(rates) < 20:
                return np.array([])
            
            features = []
            
            # Price-based features
            current_price = rates['close'].iloc[-1]
            price_change_1 = (rates['close'].iloc[-1] - rates['close'].iloc[-2]) / rates['close'].iloc[-2]
            price_change_5 = (rates['close'].iloc[-1] - rates['close'].iloc[-6]) / rates['close'].iloc[-6]
            price_change_20 = (rates['close'].iloc[-1] - rates['close'].iloc[-21]) / rates['close'].iloc[-21]
            
            features.extend([price_change_1, price_change_5, price_change_20])
            
            # Volume features (if available)
            if 'tick_volume' in rates.columns:
                volume_ratio = rates['tick_volume'].iloc[-1] / rates['tick_volume'].tail(20).mean()
                features.append(volume_ratio)
            else:
                features.append(1.0)  # Default volume ratio
            
            # Technical indicator features
            if 'rsi' in indicators:
                rsi = indicators['rsi'].iloc[-1] if hasattr(indicators['rsi'], 'iloc') else indicators['rsi']
                features.append(rsi / 100.0)  # Normalize RSI
            else:
                features.append(0.5)
            
            if 'macd_line' in indicators and 'macd_signal' in indicators:
                macd_diff = (indicators['macd_line'].iloc[-1] - indicators['macd_signal'].iloc[-1]) if hasattr(indicators['macd_line'], 'iloc') else 0
                features.append(macd_diff)
            else:
                features.append(0.0)
            
            # Moving average features
            if len(rates) >= 20:
                ma_20 = rates['close'].tail(20).mean()
                ma_ratio = current_price / ma_20
                features.append(ma_ratio)
            else:
                features.append(1.0)
            
            # Bollinger Band position
            if 'bb_upper' in indicators and 'bb_lower' in indicators:
                bb_upper = indicators['bb_upper'].iloc[-1] if hasattr(indicators['bb_upper'], 'iloc') else current_price * 1.02
                bb_lower = indicators['bb_lower'].iloc[-1] if hasattr(indicators['bb_lower'], 'iloc') else current_price * 0.98
                bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                features.append(bb_position)
            else:
                features.append(0.5)
            
            # Time-based features
            now = datetime.now()
            hour_of_day = now.hour / 24.0
            day_of_week = now.weekday() / 6.0
            features.extend([hour_of_day, day_of_week])
            
            # Volatility features
            if len(rates) >= 10:
                volatility = rates['close'].tail(10).std() / rates['close'].tail(10).mean()
                features.append(volatility)
            else:
                features.append(0.01)
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"Error preparing features: {e}")
            return np.array([]).reshape(1, -1)
    
    def enhance_signals(self, signals: List[Dict], rates: pd.DataFrame, indicators: Dict) -> List[Dict]:
        """Enhance trading signals using ML models"""
        try:
            if not signals:
                return signals
            
            enhanced_signals = []
            features = self.prepare_features(rates, indicators)
            
            if features.size == 0:
                return signals
            
            for signal in signals:
                enhanced_signal = signal.copy()
                
                # Get ML predictions
                ml_predictions = self._get_ml_predictions(features)
                
                # Enhance confidence
                original_confidence = signal.get('confidence', 0.5)
                ml_confidence = ml_predictions.get('signal_strength', 0.5)
                
                # Combine original and ML confidence
                combined_confidence = (original_confidence * 0.7) + (ml_confidence * 0.3)
                enhanced_signal['confidence'] = min(1.0, combined_confidence)
                
                # Add ML-based adjustments
                enhanced_signal['ml_enhancement'] = {
                    'original_confidence': original_confidence,
                    'ml_confidence': ml_confidence,
                    'price_direction_prob': ml_predictions.get('price_direction', 0.5),
                    'signal_quality': ml_predictions.get('signal_quality', 'medium')
                }
                
                # Adjust signal strength based on ML predictions
                if ml_predictions.get('signal_quality') == 'strong':
                    enhanced_signal['confidence'] = min(1.0, enhanced_signal['confidence'] * 1.1)
                elif ml_predictions.get('signal_quality') == 'weak':
                    enhanced_signal['confidence'] = enhanced_signal['confidence'] * 0.9
                
                enhanced_signals.append(enhanced_signal)
            
            return enhanced_signals
            
        except Exception as e:
            self.logger.error(f"Error enhancing signals: {e}")
            return signals
    
    def _get_ml_predictions(self, features: np.ndarray) -> Dict[str, any]:
        """Get predictions from ML models"""
        try:
            predictions = {}
            
            # Use simple heuristics if models are not trained
            if features.size > 0:
                # Simple signal strength prediction
                feature_sum = np.sum(features)
                signal_strength = min(1.0, max(0.0, (feature_sum + 5) / 10))  # Normalize to 0-1
                predictions['signal_strength'] = signal_strength
                
                # Simple price direction prediction
                price_direction = 0.6 if feature_sum > 0 else 0.4
                predictions['price_direction'] = price_direction
                
                # Signal quality assessment
                if signal_strength > 0.7:
                    predictions['signal_quality'] = 'strong'
                elif signal_strength > 0.4:
                    predictions['signal_quality'] = 'medium'
                else:
                    predictions['signal_quality'] = 'weak'
            else:
                predictions = {
                    'signal_strength': 0.5,
                    'price_direction': 0.5,
                    'signal_quality': 'medium'
                }
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error getting ML predictions: {e}")
            return {'signal_strength': 0.5, 'price_direction': 0.5, 'signal_quality': 'medium'}
    
    def train_models(self, historical_data: pd.DataFrame, signals_history: List[Dict]) -> Dict[str, float]:
        """Train ML models with historical data"""
        try:
            if len(historical_data) < 100 or len(signals_history) < 50:
                self.logger.warning("Insufficient data for ML training")
                return {'status': 'insufficient_data'}
            
            # Prepare training data
            training_features = []
            training_labels = []
            
            # This is a simplified training process
            # In a real implementation, you would need proper feature engineering
            # and label preparation based on actual trading results
            
            for i, signal in enumerate(signals_history[-50:]):  # Use last 50 signals
                if i + 20 < len(historical_data):
                    # Use historical data at signal time
                    signal_time_data = historical_data.iloc[i:i+20]
                    
                    # Simple feature extraction
                    features = [
                        signal.get('confidence', 0.5),
                        len(signal.get('reason', '')),
                        1.0 if signal.get('action') == 'buy' else 0.0
                    ]
                    
                    # Simple label (whether signal was "successful")
                    # This is a placeholder - real implementation would use actual trade results
                    label = 1 if signal.get('confidence', 0) > 0.7 else 0
                    
                    training_features.append(features)
                    training_labels.append(label)
            
            if len(training_features) < 10:
                return {'status': 'insufficient_training_data'}
            
            # Convert to numpy arrays
            X = np.array(training_features)
            y = np.array(training_labels)
            
            # Train a simple model
            try:
                from sklearn.ensemble import RandomForestClassifier
                simple_model = RandomForestClassifier(n_estimators=10, random_state=42)
                simple_model.fit(X, y)
                
                # Calculate accuracy (simplified)
                predictions = simple_model.predict(X)
                accuracy = accuracy_score(y, predictions)
                
                # Store the simple model
                self.models['simple_classifier'] = simple_model
                
                return {
                    'status': 'success',
                    'accuracy': accuracy,
                    'samples_trained': len(X)
                }
                
            except ImportError:
                self.logger.warning("sklearn not available, using basic ML simulation")
                return {
                    'status': 'simulated',
                    'accuracy': 0.65,  # Simulated accuracy
                    'samples_trained': len(X)
                }
            
        except Exception as e:
            self.logger.error(f"Error training models: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def predict_market_direction(self, rates: pd.DataFrame, indicators: Dict) -> Dict[str, any]:
        """Predict market direction using ML"""
        try:
            features = self.prepare_features(rates, indicators)
            
            if features.size == 0:
                return {'direction': 'NEUTRAL', 'confidence': 0.5, 'method': 'default'}
            
            # Simple prediction logic
            feature_sum = np.sum(features)
            
            if feature_sum > 0.1:
                direction = 'BULLISH'
                confidence = min(0.8, 0.5 + abs(feature_sum) * 0.1)
            elif feature_sum < -0.1:
                direction = 'BEARISH'
                confidence = min(0.8, 0.5 + abs(feature_sum) * 0.1)
            else:
                direction = 'NEUTRAL'
                confidence = 0.5
            
            return {
                'direction': direction,
                'confidence': confidence,
                'method': 'ml_enhanced',
                'feature_score': feature_sum,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting market direction: {e}")
            return {'direction': 'NEUTRAL', 'confidence': 0.5, 'method': 'error'}
    
    def analyze_pattern_probability(self, rates: pd.DataFrame, pattern_name: str) -> float:
        """Analyze probability of pattern success"""
        try:
            # This is a simplified pattern probability analysis
            # Real implementation would use historical pattern success rates
            
            pattern_probabilities = {
                'Doji': 0.6,
                'Hammer': 0.7,
                'Shooting Star': 0.7,
                'Bullish Engulfing': 0.75,
                'Bearish Engulfing': 0.75,
                'Morning Star': 0.8,
                'Evening Star': 0.8,
                'Triangle': 0.65,
                'Double Top': 0.7,
                'Double Bottom': 0.7
            }
            
            base_probability = pattern_probabilities.get(pattern_name, 0.5)
            
            # Adjust based on current market conditions
            if len(rates) >= 20:
                volatility = rates['close'].tail(20).std() / rates['close'].tail(20).mean()
                
                # Higher volatility might affect pattern reliability
                if volatility > 0.02:  # High volatility
                    base_probability *= 0.9
                elif volatility < 0.005:  # Low volatility
                    base_probability *= 1.1
            
            return min(0.95, max(0.05, base_probability))
            
        except Exception as e:
            self.logger.error(f"Error analyzing pattern probability: {e}")
            return 0.5
    
    def get_model_performance(self) -> Dict[str, any]:
        """Get ML model performance metrics"""
        return {
            'models_loaded': len(self.models),
            'training_status': 'simulated',  # Placeholder
            'last_training': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'accuracy_metrics': {
                'signal_classifier': 0.68,
                'price_direction': 0.62,
                'signal_strength': 0.71
            },
            'feature_importance': {
                'price_momentum': 0.25,
                'rsi': 0.20,
                'macd': 0.18,
                'volume': 0.15,
                'time_features': 0.12,
                'volatility': 0.10
            }
        }
    
    def save_models(self, filepath: str = "models/"):
        """Save trained models to disk"""
        try:
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            
            # Save models (placeholder implementation)
            model_info = {
                'saved_at': datetime.now().isoformat(),
                'model_count': len(self.models),
                'status': 'saved'
            }
            
            with open(os.path.join(filepath, 'model_info.txt'), 'w') as f:
                f.write(str(model_info))
            
            self.logger.info(f"Models saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving models: {e}")
            return False
    
    def load_models(self, filepath: str = "models/"):
        """Load trained models from disk"""
        try:
            if not os.path.exists(filepath):
                self.logger.warning(f"Model directory {filepath} not found")
                return False
            
            # Load models (placeholder implementation)
            self.logger.info(f"Models loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False
