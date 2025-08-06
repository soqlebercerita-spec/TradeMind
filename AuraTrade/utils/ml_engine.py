"""
Machine Learning Engine for AuraTrade Bot
Advanced ML predictions and signal generation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pickle
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

from utils.logger import Logger

class MLEngine:
    """Machine Learning prediction engine"""

    def __init__(self):
        self.logger = Logger().get_logger()

        # Models
        self.direction_model = None
        self.volatility_model = None
        self.scaler = StandardScaler()

        # Model parameters
        self.lookback_period = 100
        self.prediction_horizon = 10
        self.min_confidence = 0.65

        # Feature engineering
        self.features = [
            'rsi', 'macd', 'bb_upper', 'bb_lower', 'ema_fast', 'ema_slow',
            'volume_ma', 'price_change', 'volatility', 'momentum'
        ]

        # Model paths
        self.model_dir = 'AuraTrade/data/models'
        os.makedirs(self.model_dir, exist_ok=True)

        self.logger.info("MLEngine initialized")

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML models"""
        try:
            if len(df) < 50:
                return pd.DataFrame()

            features_df = df.copy()

            # Technical indicators
            features_df['rsi'] = self._calculate_rsi(df['close'])
            features_df['macd'], features_df['macd_signal'] = self._calculate_macd(df['close'])
            features_df['bb_upper'], features_df['bb_middle'], features_df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
            features_df['ema_fast'] = df['close'].ewm(span=12).mean()
            features_df['ema_slow'] = df['close'].ewm(span=26).mean()

            # Volume indicators
            features_df['volume_ma'] = df['tick_volume'].rolling(window=20).mean()
            features_df['volume_ratio'] = df['tick_volume'] / features_df['volume_ma']

            # Price-based features
            features_df['price_change'] = df['close'].pct_change()
            features_df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
            features_df['open_close_ratio'] = (df['close'] - df['open']) / df['open']

            # Volatility
            features_df['volatility'] = features_df['price_change'].rolling(window=20).std()

            # Momentum
            features_df['momentum'] = df['close'].pct_change(periods=10)

            # Trend indicators
            features_df['trend_strength'] = (features_df['ema_fast'] - features_df['ema_slow']) / features_df['ema_slow']

            # Support/Resistance levels
            features_df['resistance_level'] = df['high'].rolling(window=20).max()
            features_df['support_level'] = df['low'].rolling(window=20).min()
            features_df['price_position'] = (df['close'] - features_df['support_level']) / (features_df['resistance_level'] - features_df['support_level'])

            # Time-based features
            features_df['hour'] = df.index.hour
            features_df['day_of_week'] = df.index.dayofweek

            # Drop NaN values
            features_df = features_df.dropna()

            return features_df

        except Exception as e:
            self.logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except:
            return pd.Series(index=prices.index, dtype=float)

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal).mean()
            return macd, macd_signal
        except:
            return pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float)

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            return upper_band, sma, lower_band
        except:
            empty_series = pd.Series(index=prices.index, dtype=float)
            return empty_series, empty_series, empty_series

    def create_labels(self, df: pd.DataFrame, horizon: int = 10) -> pd.Series:
        """Create labels for supervised learning"""
        try:
            future_prices = df['close'].shift(-horizon)
            current_prices = df['close']

            # Create direction labels (0: down, 1: up)
            price_change = (future_prices - current_prices) / current_prices
            labels = (price_change > 0.001).astype(int)  # 0.1% threshold

            return labels

        except Exception as e:
            self.logger.error(f"Error creating labels: {e}")
            return pd.Series()

    def train_models(self, df: pd.DataFrame) -> bool:
        """Train ML models"""
        try:
            self.logger.info("Training ML models...")

            # Prepare features
            features_df = self.prepare_features(df)
            if features_df.empty:
                self.logger.error("No features prepared for training")
                return False

            # Create labels
            labels = self.create_labels(features_df, self.prediction_horizon)

            # Align features and labels
            min_length = min(len(features_df), len(labels))
            features_df = features_df.iloc[:min_length]
            labels = labels.iloc[:min_length]

            # Remove NaN values
            mask = ~(features_df.isnull().any(axis=1) | labels.isnull())
            features_df = features_df[mask]
            labels = labels[mask]

            if len(features_df) < 100:
                self.logger.warning("Insufficient data for training")
                return False

            # Select features
            feature_columns = [col for col in self.features if col in features_df.columns]
            X = features_df[feature_columns].values
            y = labels.values

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )

            # Train direction model
            self.direction_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.direction_model.fit(X_train, y_train)

            # Evaluate model
            y_pred = self.direction_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            self.logger.info(f"Direction model accuracy: {accuracy:.3f}")

            # Train volatility model (predict if next period will be high volatility)
            volatility_labels = self._create_volatility_labels(features_df)
            if len(volatility_labels) > 0:
                vol_mask = ~volatility_labels.isnull()
                X_vol = X_scaled[vol_mask]
                y_vol = volatility_labels[vol_mask].values

                if len(np.unique(y_vol)) > 1:
                    X_vol_train, X_vol_test, y_vol_train, y_vol_test = train_test_split(
                        X_vol, y_vol, test_size=0.2, random_state=42
                    )

                    self.volatility_model = GradientBoostingClassifier(
                        n_estimators=50,
                        max_depth=5,
                        random_state=42
                    )
                    self.volatility_model.fit(X_vol_train, y_vol_train)

                    vol_accuracy = accuracy_score(y_vol_test, self.volatility_model.predict(X_vol_test))
                    self.logger.info(f"Volatility model accuracy: {vol_accuracy:.3f}")

            # Save models
            self._save_models()

            return True

        except Exception as e:
            self.logger.error(f"Error training models: {e}")
            return False

    def _create_volatility_labels(self, df: pd.DataFrame) -> pd.Series:
        """Create volatility labels"""
        try:
            volatility = df['volatility']
            high_vol_threshold = volatility.quantile(0.7)
            return (volatility > high_vol_threshold).astype(int)
        except:
            return pd.Series()

    def predict_direction(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Predict price direction"""
        try:
            if self.direction_model is None:
                return {'prediction': 0, 'confidence': 0.0, 'signal': 'HOLD'}

            # Prepare features
            features_df = self.prepare_features(df)
            if features_df.empty:
                return {'prediction': 0, 'confidence': 0.0, 'signal': 'HOLD'}

            # Get latest features
            latest_features = features_df.iloc[-1]
            feature_columns = [col for col in self.features if col in features_df.columns]
            X = latest_features[feature_columns].values.reshape(1, -1)

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Make prediction
            prediction = self.direction_model.predict(X_scaled)[0]
            probabilities = self.direction_model.predict_proba(X_scaled)[0]
            confidence = max(probabilities)

            # Generate signal
            if confidence >= self.min_confidence:
                signal = 'BUY' if prediction == 1 else 'SELL'
            else:
                signal = 'HOLD'

            return {
                'prediction': int(prediction),
                'confidence': float(confidence),
                'signal': signal,
                'probabilities': {
                    'down': float(probabilities[0]),
                    'up': float(probabilities[1])
                }
            }

        except Exception as e:
            self.logger.error(f"Error predicting direction: {e}")
            return {'prediction': 0, 'confidence': 0.0, 'signal': 'HOLD'}

    def predict_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Predict volatility level"""
        try:
            if self.volatility_model is None:
                return {'high_volatility': False, 'confidence': 0.0}

            # Prepare features
            features_df = self.prepare_features(df)
            if features_df.empty:
                return {'high_volatility': False, 'confidence': 0.0}

            # Get latest features
            latest_features = features_df.iloc[-1]
            feature_columns = [col for col in self.features if col in features_df.columns]
            X = latest_features[feature_columns].values.reshape(1, -1)

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Make prediction
            prediction = self.volatility_model.predict(X_scaled)[0]
            probabilities = self.volatility_model.predict_proba(X_scaled)[0]
            confidence = max(probabilities)

            return {
                'high_volatility': bool(prediction),
                'confidence': float(confidence),
                'volatility_prob': float(probabilities[1])
            }

        except Exception as e:
            self.logger.error(f"Error predicting volatility: {e}")
            return {'high_volatility': False, 'confidence': 0.0}

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from direction model"""
        try:
            if self.direction_model is None:
                return {}

            feature_columns = [col for col in self.features if col in self.direction_model.feature_names_in_]
            importances = self.direction_model.feature_importances_

            return dict(zip(feature_columns, importances))

        except Exception as e:
            self.logger.error(f"Error getting feature importance: {e}")
            return {}

    def _save_models(self):
        """Save trained models"""
        try:
            if self.direction_model is not None:
                with open(os.path.join(self.model_dir, 'direction_model.pkl'), 'wb') as f:
                    pickle.dump(self.direction_model, f)

            if self.volatility_model is not None:
                with open(os.path.join(self.model_dir, 'volatility_model.pkl'), 'wb') as f:
                    pickle.dump(self.volatility_model, f)

            with open(os.path.join(self.model_dir, 'scaler.pkl'), 'wb') as f:
                pickle.dump(self.scaler, f)

            self.logger.info("Models saved successfully")

        except Exception as e:
            self.logger.error(f"Error saving models: {e}")

    def load_models(self) -> bool:
        """Load saved models"""
        try:
            direction_model_path = os.path.join(self.model_dir, 'direction_model.pkl')
            volatility_model_path = os.path.join(self.model_dir, 'volatility_model.pkl')
            scaler_path = os.path.join(self.model_dir, 'scaler.pkl')

            if os.path.exists(direction_model_path):
                with open(direction_model_path, 'rb') as f:
                    self.direction_model = pickle.load(f)

            if os.path.exists(volatility_model_path):
                with open(volatility_model_path, 'rb') as f:
                    self.volatility_model = pickle.load(f)

            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)

            self.logger.info("Models loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False

    def retrain_with_new_data(self, df: pd.DataFrame) -> bool:
        """Retrain models with new data"""
        try:
            self.logger.info("Retraining models with new data...")
            return self.train_models(df)

        except Exception as e:
            self.logger.error(f"Error retraining models: {e}")
            return False

    def get_model_status(self) -> Dict[str, Any]:
        """Get model status information"""
        return {
            'direction_model_loaded': self.direction_model is not None,
            'volatility_model_loaded': self.volatility_model is not None,
            'scaler_loaded': hasattr(self.scaler, 'mean_'),
            'min_confidence': self.min_confidence,
            'prediction_horizon': self.prediction_horizon,
            'features_count': len(self.features)
        }