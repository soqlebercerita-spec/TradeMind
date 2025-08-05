"""
Machine Learning engine for market prediction and signal generation
Implements multiple ML models for price direction and trend prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from config.config import Config
from utils.logger import Logger

class MLEngine:
    """Machine Learning engine for trading signals"""
    
    def __init__(self):
        self.logger = Logger().get_logger()
        self.config = Config()
        
        # Model storage
        self.models = {}
        self.scalers = {}
        self.feature_columns = {}
        
        # Model configurations
        self.model_configs = {
            'random_forest': {
                'class': RandomForestClassifier,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2,
                    'random_state': 42
                }
            },
            'svm': {
                'class': SVC,
                'params': {
                    'kernel': 'rbf',
                    'C': 1.0,
                    'gamma': 'scale',
                    'probability': True,
                    'random_state': 42
                }
            }
        }
        
        if XGBOOST_AVAILABLE:
            self.model_configs['xgboost'] = {
                'class': xgb.XGBClassifier,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'random_state': 42,
                    'eval_metric': 'logloss'
                }
            }
        
        # Feature engineering parameters
        self.feature_params = {
            'sma_periods': [5, 10, 20, 50],
            'ema_periods': [12, 26],
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'bb_period': 20,
            'atr_period': 14,
            'lookback_periods': [5, 10, 20]
        }
        
        # Model performance tracking
        self.model_performance = {}
        
        # Prediction cache to avoid recalculation
        self.prediction_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML models"""
        try:
            if len(df) < 100:  # Need sufficient data
                return pd.DataFrame()
            
            features_df = df.copy()
            
            # Price-based features
            features_df['returns'] = df['close'].pct_change()
            features_df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            features_df['price_change'] = (df['close'] - df['open']) / df['open']
            features_df['high_low_pct'] = (df['high'] - df['low']) / df['close']
            features_df['volume_change'] = df['tick_volume'].pct_change()
            
            # Moving averages
            for period in self.feature_params['sma_periods']:
                features_df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
                features_df[f'close_sma_{period}_ratio'] = df['close'] / features_df[f'sma_{period}']
            
            for period in self.feature_params['ema_periods']:
                features_df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
                features_df[f'close_ema_{period}_ratio'] = df['close'] / features_df[f'ema_{period}']
            
            # RSI
            rsi_period = self.feature_params['rsi_period']
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            features_df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            fast = self.feature_params['macd_fast']
            slow = self.feature_params['macd_slow']
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            features_df['macd'] = ema_fast - ema_slow
            features_df['macd_signal'] = features_df['macd'].ewm(span=9).mean()
            features_df['macd_histogram'] = features_df['macd'] - features_df['macd_signal']
            
            # Bollinger Bands
            bb_period = self.feature_params['bb_period']
            bb_sma = df['close'].rolling(window=bb_period).mean()
            bb_std = df['close'].rolling(window=bb_period).std()
            features_df['bb_upper'] = bb_sma + (bb_std * 2)
            features_df['bb_lower'] = bb_sma - (bb_std * 2)
            features_df['bb_position'] = (df['close'] - features_df['bb_lower']) / (features_df['bb_upper'] - features_df['bb_lower'])
            features_df['bb_width'] = (features_df['bb_upper'] - features_df['bb_lower']) / bb_sma
            
            # ATR
            atr_period = self.feature_params['atr_period']
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            features_df['atr'] = true_range.rolling(window=atr_period).mean()
            features_df['atr_ratio'] = features_df['atr'] / df['close']
            
            # Momentum features
            for period in self.feature_params['lookback_periods']:
                features_df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
                features_df[f'volume_momentum_{period}'] = df['tick_volume'] / df['tick_volume'].shift(period) - 1
            
            # Volatility features
            features_df['volatility_5'] = features_df['returns'].rolling(window=5).std()
            features_df['volatility_20'] = features_df['returns'].rolling(window=20).std()
            features_df['volatility_ratio'] = features_df['volatility_5'] / features_df['volatility_20']
            
            # Time-based features
            features_df['hour'] = pd.to_datetime(df.index).hour
            features_df['day_of_week'] = pd.to_datetime(df.index).dayofweek
            
            # Candlestick patterns (simplified)
            features_df['doji'] = ((np.abs(df['close'] - df['open']) / (df['high'] - df['low'])) < 0.1).astype(int)
            features_df['hammer'] = (((df['close'] - df['low']) > 2 * (df['open'] - df['close'])) & 
                                   ((df['high'] - df['close']) < (df['close'] - df['low']))).astype(int)
            
            # Remove infinite and NaN values
            features_df = features_df.replace([np.inf, -np.inf], np.nan)
            features_df = features_df.fillna(method='ffill').fillna(0)
            
            return features_df
            
        except Exception as e:
            self.logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()
    
    def create_target_variable(self, df: pd.DataFrame, lookahead: int = 5) -> pd.Series:
        """Create target variable for classification"""
        try:
            # Calculate future returns
            future_returns = df['close'].shift(-lookahead) / df['close'] - 1
            
            # Create classification target
            # 1 = Buy (positive return > threshold)
            # 0 = Hold (small return)
            # -1 = Sell (negative return < -threshold)
            
            threshold = 0.001  # 0.1% threshold
            
            target = pd.Series(0, index=df.index)
            target[future_returns > threshold] = 1
            target[future_returns < -threshold] = -1
            
            return target
            
        except Exception as e:
            self.logger.error(f"Error creating target variable: {e}")
            return pd.Series()
    
    def train_model(self, symbol: str, df: pd.DataFrame, model_type: str = 'random_forest') -> bool:
        """Train ML model for specific symbol"""
        try:
            self.logger.info(f"Training {model_type} model for {symbol}")
            
            # Prepare features
            features_df = self.prepare_features(df)
            if features_df.empty:
                self.logger.error(f"Failed to prepare features for {symbol}")
                return False
            
            # Create target
            target = self.create_target_variable(features_df)
            if target.empty:
                self.logger.error(f"Failed to create target for {symbol}")
                return False
            
            # Select feature columns (exclude OHLCV and time columns)
            exclude_cols = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            feature_cols = [col for col in features_df.columns if col not in exclude_cols]
            
            # Prepare data
            X = features_df[feature_cols].iloc[:-5]  # Remove last 5 rows (no target due to lookahead)
            y = target.iloc[:-5]
            
            # Remove rows with NaN target
            valid_indices = ~y.isna()
            X = X[valid_indices]
            y = y[valid_indices]
            
            if len(X) < 100:  # Need minimum data
                self.logger.error(f"Insufficient data for training {symbol}: {len(X)} samples")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            if model_type not in self.model_configs:
                self.logger.error(f"Unknown model type: {model_type}")
                return False
            
            model_class = self.model_configs[model_type]['class']
            model_params = self.model_configs[model_type]['params']
            
            model = model_class(**model_params)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            self.logger.info(f"Model {model_type} for {symbol}: "
                           f"Accuracy: {accuracy:.3f}, "
                           f"CV Score: {cv_mean:.3f} (+/- {cv_std * 2:.3f})")
            
            # Store model and scaler
            model_key = f"{symbol}_{model_type}"
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            self.feature_columns[model_key] = feature_cols
            
            # Store performance metrics
            self.model_performance[model_key] = {
                'accuracy': accuracy,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'training_date': datetime.now(),
                'training_samples': len(X_train)
            }
            
            # Save model to disk
            self._save_model(symbol, model_type, model, scaler, feature_cols)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model for {symbol}: {e}")
            return False
    
    def predict_direction(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Predict price direction using ensemble of models"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{len(df)}"
            if cache_key in self.prediction_cache:
                cache_time, prediction = self.prediction_cache[cache_key]
                if (datetime.now() - cache_time).seconds < self.cache_timeout:
                    return prediction
            
            # Prepare features
            features_df = self.prepare_features(df)
            if features_df.empty:
                return {'direction': 0, 'confidence': 0, 'predictions': {}}
            
            # Get latest features
            latest_features = features_df.iloc[-1:]
            
            predictions = {}
            confidences = {}
            
            # Make predictions with all available models
            for model_key in self.models.keys():
                if not model_key.startswith(symbol):
                    continue
                
                try:
                    model = self.models[model_key]
                    scaler = self.scalers[model_key]
                    feature_cols = self.feature_columns[model_key]
                    
                    # Prepare features for this model
                    X = latest_features[feature_cols]
                    X_scaled = scaler.transform(X)
                    
                    # Make prediction
                    prediction = model.predict(X_scaled)[0]
                    confidence = np.max(model.predict_proba(X_scaled))
                    
                    model_type = model_key.split('_', 1)[1]
                    predictions[model_type] = prediction
                    confidences[model_type] = confidence
                    
                except Exception as e:
                    self.logger.error(f"Error making prediction with {model_key}: {e}")
                    continue
            
            if not predictions:
                return {'direction': 0, 'confidence': 0, 'predictions': {}}
            
            # Ensemble prediction (weighted by model performance)
            weighted_prediction = 0
            total_weight = 0
            
            for model_type, prediction in predictions.items():
                model_key = f"{symbol}_{model_type}"
                if model_key in self.model_performance:
                    weight = self.model_performance[model_key]['accuracy']
                else:
                    weight = 0.5  # Default weight
                
                weighted_prediction += prediction * weight * confidences[model_type]
                total_weight += weight * confidences[model_type]
            
            if total_weight > 0:
                final_direction = weighted_prediction / total_weight
                final_confidence = min(1.0, total_weight / len(predictions))
            else:
                final_direction = 0
                final_confidence = 0
            
            # Convert to discrete direction
            if final_direction > 0.3:
                direction = 1  # Buy
            elif final_direction < -0.3:
                direction = -1  # Sell
            else:
                direction = 0  # Hold
            
            result = {
                'direction': direction,
                'confidence': final_confidence,
                'raw_prediction': final_direction,
                'predictions': predictions,
                'confidences': confidences
            }
            
            # Cache result
            self.prediction_cache[cache_key] = (datetime.now(), result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error predicting direction for {symbol}: {e}")
            return {'direction': 0, 'confidence': 0, 'predictions': {}}
    
    def retrain_models(self, symbol: str, df: pd.DataFrame) -> bool:
        """Retrain all models for a symbol"""
        try:
            self.logger.info(f"Retraining models for {symbol}")
            
            success_count = 0
            for model_type in self.config.ML_SETTINGS['models']:
                if self.train_model(symbol, df, model_type):
                    success_count += 1
            
            if success_count > 0:
                self.logger.info(f"Successfully retrained {success_count} models for {symbol}")
                return True
            else:
                self.logger.error(f"Failed to retrain any models for {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error retraining models for {symbol}: {e}")
            return False
    
    def evaluate_model_performance(self, symbol: str) -> Dict[str, Any]:
        """Evaluate current model performance"""
        try:
            performance_summary = {}
            
            for model_key in self.models.keys():
                if not model_key.startswith(symbol):
                    continue
                
                if model_key in self.model_performance:
                    perf = self.model_performance[model_key]
                    model_type = model_key.split('_', 1)[1]
                    
                    performance_summary[model_type] = {
                        'accuracy': perf['accuracy'],
                        'cv_score': perf['cv_mean'],
                        'cv_std': perf['cv_std'],
                        'age_hours': (datetime.now() - perf['training_date']).total_seconds() / 3600,
                        'training_samples': perf['training_samples']
                    }
            
            return performance_summary
            
        except Exception as e:
            self.logger.error(f"Error evaluating model performance for {symbol}: {e}")
            return {}
    
    def should_retrain(self, symbol: str) -> bool:
        """Check if models should be retrained"""
        try:
            retrain_frequency = self.config.ML_SETTINGS['model_retrain_frequency']
            
            for model_key in self.models.keys():
                if not model_key.startswith(symbol):
                    continue
                
                if model_key in self.model_performance:
                    training_date = self.model_performance[model_key]['training_date']
                    hours_since_training = (datetime.now() - training_date).total_seconds() / 3600
                    
                    if hours_since_training >= retrain_frequency:
                        return True
                    
                    # Also retrain if accuracy is too low
                    accuracy = self.model_performance[model_key]['accuracy']
                    if accuracy < 0.55:  # Less than 55% accuracy
                        self.logger.info(f"Model {model_key} accuracy too low: {accuracy:.3f}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking retrain condition for {symbol}: {e}")
            return False
    
    def _save_model(self, symbol: str, model_type: str, model, scaler, feature_cols):
        """Save model to disk"""
        try:
            models_dir = 'models'
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
            
            model_data = {
                'model': model,
                'scaler': scaler,
                'feature_columns': feature_cols,
                'symbol': symbol,
                'model_type': model_type,
                'save_date': datetime.now()
            }
            
            filename = os.path.join(models_dir, f"{symbol}_{model_type}.pkl")
            with open(filename, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.logger.info(f"Model saved: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
    
    def load_model(self, symbol: str, model_type: str) -> bool:
        """Load model from disk"""
        try:
            filename = f"models/{symbol}_{model_type}.pkl"
            
            if not os.path.exists(filename):
                return False
            
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
            
            model_key = f"{symbol}_{model_type}"
            self.models[model_key] = model_data['model']
            self.scalers[model_key] = model_data['scaler']
            self.feature_columns[model_key] = model_data['feature_columns']
            
            self.logger.info(f"Model loaded: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading model {filename}: {e}")
            return False
    
    def load_all_models(self, symbol: str):
        """Load all available models for symbol"""
        try:
            for model_type in self.model_configs.keys():
                self.load_model(symbol, model_type)
        except Exception as e:
            self.logger.error(f"Error loading models for {symbol}: {e}")
    
    def get_feature_importance(self, symbol: str, model_type: str = 'random_forest') -> Dict[str, float]:
        """Get feature importance from tree-based models"""
        try:
            model_key = f"{symbol}_{model_type}"
            
            if model_key not in self.models:
                return {}
            
            model = self.models[model_key]
            feature_cols = self.feature_columns[model_key]
            
            # Get feature importance (works for tree-based models)
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                feature_importance = dict(zip(feature_cols, importance))
                
                # Sort by importance
                sorted_importance = dict(sorted(feature_importance.items(), 
                                              key=lambda x: x[1], reverse=True))
                
                return sorted_importance
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def cleanup_old_predictions(self):
        """Clean up old cached predictions"""
        try:
            current_time = datetime.now()
            
            keys_to_remove = []
            for key, (cache_time, _) in self.prediction_cache.items():
                if (current_time - cache_time).seconds > self.cache_timeout:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.prediction_cache[key]
                
        except Exception as e:
            self.logger.error(f"Error cleaning up predictions cache: {e}")
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of all models"""
        try:
            summary = {
                'total_models': len(self.models),
                'model_types': list(set([key.split('_', 1)[1] for key in self.models.keys()])),
                'symbols': list(set([key.split('_', 1)[0] for key in self.models.keys()])),
                'performance': self.model_performance.copy(),
                'cache_size': len(self.prediction_cache),
                'xgboost_available': XGBOOST_AVAILABLE
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting model summary: {e}")
            return {}
