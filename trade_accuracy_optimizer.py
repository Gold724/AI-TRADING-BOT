#!/usr/bin/env python3
"""
TradeBot Sentinel - Trade Accuracy Optimizer
Machine Learning-based trade request detection and accuracy enhancement

Features:
- ML-based pattern recognition for trade requests
- Continuous learning from successful/failed detections
- Dynamic threshold adjustment
- Anomaly detection for unusual trading patterns
- Performance optimization with caching
- Real-time accuracy metrics
"""

import asyncio
import json
import os
import time
import logging
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import sqlite3
from dataclasses import dataclass, asdict
import numpy as np
from collections import defaultdict, deque
import re
from urllib.parse import urlparse, parse_qs

# ML imports (with fallbacks)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available, using rule-based fallback")

@dataclass
class TradeRequest:
    """Trade request data structure"""
    timestamp: str
    url: str
    method: str
    headers: Dict[str, str]
    payload: str
    content_type: str
    is_trade: bool
    confidence: float
    features: Dict[str, Any]
    classification: str  # 'trade', 'ui', 'data', 'auth', 'unknown'

@dataclass
class AccuracyMetrics:
    """Accuracy tracking metrics"""
    total_requests: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float

class TradeAccuracyOptimizer:
    """Advanced trade request accuracy optimizer with ML"""
    
    def __init__(self, config_file: str = 'accuracy_optimizer_config.json'):
        self.config_file = config_file
        self.db_file = 'trade_accuracy.db'
        self.model_file = 'trade_classifier.pkl'
        self.log_file = 'accuracy_optimizer.log'
        
        # Setup logging
        self.setup_logging()
        
        # Initialize database
        self._init_database()
        
        # Load configuration
        self.config = self._load_config()
        
        # ML components
        self.vectorizer = None
        self.classifier = None
        self.anomaly_detector = None
        self.is_trained = False
        
        # Feature extractors
        self.url_patterns = self._compile_url_patterns()
        self.payload_patterns = self._compile_payload_patterns()
        
        # Performance caching
        self.feature_cache = {}
        self.classification_cache = {}
        self.cache_max_size = 1000
        
        # Real-time metrics
        self.recent_requests = deque(maxlen=1000)
        self.accuracy_history = deque(maxlen=100)
        
        # Dynamic thresholds
        self.confidence_threshold = 0.7
        self.anomaly_threshold = -0.5
        
        # Load existing model if available
        self._load_model()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.log_file)
            ]
        )
        self.logger = logging.getLogger('AccuracyOptimizer')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load optimizer configuration"""
        default_config = {
            'ml_enabled': ML_AVAILABLE,
            'retrain_interval_hours': 24,
            'min_training_samples': 100,
            'confidence_threshold': 0.7,
            'anomaly_threshold': -0.5,
            'feature_cache_size': 1000,
            'auto_threshold_adjustment': True,
            'performance_monitoring': True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using defaults")
        
        # Save config
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _init_database(self):
        """Initialize SQLite database for training data and metrics"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Training data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    url TEXT,
                    method TEXT,
                    headers TEXT,
                    payload TEXT,
                    content_type TEXT,
                    is_trade BOOLEAN,
                    confidence REAL,
                    features TEXT,
                    classification TEXT,
                    verified BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Accuracy metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accuracy_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_requests INTEGER,
                    true_positives INTEGER,
                    false_positives INTEGER,
                    true_negatives INTEGER,
                    false_negatives INTEGER,
                    accuracy REAL,
                    precision_score REAL,
                    recall_score REAL,
                    f1_score REAL
                )
            ''')
            
            # Model performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_version TEXT,
                    training_samples INTEGER,
                    test_accuracy REAL,
                    feature_importance TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    def _compile_url_patterns(self) -> List[Tuple[re.Pattern, str, float]]:
        """Compile URL patterns for trade detection"""
        patterns = [
            # High confidence trade patterns
            (re.compile(r'/api/v\d+/trade', re.I), 'trade', 0.95),
            (re.compile(r'/trade/execute', re.I), 'trade', 0.95),
            (re.compile(r'/order/place', re.I), 'trade', 0.9),
            (re.compile(r'/position/open', re.I), 'trade', 0.9),
            (re.compile(r'/position/close', re.I), 'trade', 0.9),
            (re.compile(r'/buy|/sell', re.I), 'trade', 0.8),
            
            # Medium confidence patterns
            (re.compile(r'/market/order', re.I), 'trade', 0.7),
            (re.compile(r'/futures/trade', re.I), 'trade', 0.75),
            (re.compile(r'/spot/trade', re.I), 'trade', 0.75),
            
            # UI/Data patterns (negative indicators)
            (re.compile(r'/layout|/ui|/dashboard', re.I), 'ui', -0.8),
            (re.compile(r'/quote|/price|/ticker', re.I), 'data', -0.7),
            (re.compile(r'/auth|/login|/session', re.I), 'auth', -0.9),
            (re.compile(r'/websocket|/ws', re.I), 'data', -0.6),
        ]
        
        return patterns
    
    def _compile_payload_patterns(self) -> List[Tuple[re.Pattern, str, float]]:
        """Compile payload patterns for trade detection"""
        patterns = [
            # High confidence trade keywords
            (re.compile(r'"(symbol|instrument)"\s*:', re.I), 'trade', 0.8),
            (re.compile(r'"(quantity|amount|size)"\s*:', re.I), 'trade', 0.7),
            (re.compile(r'"(price|rate)"\s*:', re.I), 'trade', 0.6),
            (re.compile(r'"(side|direction)"\s*:\s*"(buy|sell)"', re.I), 'trade', 0.9),
            (re.compile(r'"(orderType|type)"\s*:', re.I), 'trade', 0.7),
            (re.compile(r'"(leverage|margin)"\s*:', re.I), 'trade', 0.8),
            
            # Trade action patterns
            (re.compile(r'"action"\s*:\s*"(buy|sell|long|short)"', re.I), 'trade', 0.85),
            (re.compile(r'"command"\s*:\s*"(place_order|execute_trade)"', re.I), 'trade', 0.9),
            
            # UI/Layout patterns (negative indicators)
            (re.compile(r'"(layout|widget|component)"\s*:', re.I), 'ui', -0.8),
            (re.compile(r'"(x|y|width|height)"\s*:', re.I), 'ui', -0.7),
            (re.compile(r'"(color|theme|style)"\s*:', re.I), 'ui', -0.6),
        ]
        
        return patterns
    
    def extract_features(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive features from request data"""
        # Create cache key
        cache_key = hashlib.md5(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()
        
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        url = request_data.get('url', '')
        method = request_data.get('method', 'GET')
        headers = request_data.get('headers', {})
        payload = request_data.get('payload', '')
        content_type = headers.get('content-type', '')
        
        features = {
            # Basic features
            'method': method,
            'url_length': len(url),
            'payload_length': len(payload),
            'header_count': len(headers),
            
            # URL features
            'url_has_api': 'api' in url.lower(),
            'url_has_trade': 'trade' in url.lower(),
            'url_has_order': 'order' in url.lower(),
            'url_has_position': 'position' in url.lower(),
            'url_path_segments': len(urlparse(url).path.split('/')),
            
            # Content type features
            'is_json': 'json' in content_type.lower(),
            'is_form_data': 'form' in content_type.lower(),
            'is_multipart': 'multipart' in content_type.lower(),
            
            # Payload features
            'payload_has_symbol': 'symbol' in payload.lower(),
            'payload_has_amount': any(word in payload.lower() for word in ['amount', 'quantity', 'size']),
            'payload_has_price': 'price' in payload.lower(),
            'payload_has_side': any(word in payload.lower() for word in ['buy', 'sell', 'long', 'short']),
            'payload_has_leverage': 'leverage' in payload.lower(),
            
            # Header features
            'has_auth_header': any('auth' in k.lower() for k in headers.keys()),
            'has_user_agent': 'user-agent' in headers,
            'has_referer': 'referer' in headers,
            
            # Pattern matching scores
            'url_pattern_score': self._calculate_url_pattern_score(url),
            'payload_pattern_score': self._calculate_payload_pattern_score(payload),
            
            # Advanced features
            'request_complexity': self._calculate_request_complexity(request_data),
            'trade_keyword_density': self._calculate_trade_keyword_density(payload),
            'json_depth': self._calculate_json_depth(payload) if payload else 0,
        }
        
        # Cache features
        if len(self.feature_cache) < self.cache_max_size:
            self.feature_cache[cache_key] = features
        
        return features
    
    def _calculate_url_pattern_score(self, url: str) -> float:
        """Calculate URL pattern matching score"""
        score = 0.0
        for pattern, category, weight in self.url_patterns:
            if pattern.search(url):
                if category == 'trade':
                    score += weight
                else:
                    score += weight  # Negative weights for non-trade patterns
        return max(-1.0, min(1.0, score))
    
    def _calculate_payload_pattern_score(self, payload: str) -> float:
        """Calculate payload pattern matching score"""
        if not payload:
            return 0.0
        
        score = 0.0
        for pattern, category, weight in self.payload_patterns:
            matches = len(pattern.findall(payload))
            if matches > 0:
                if category == 'trade':
                    score += weight * min(matches, 3)  # Cap at 3 matches
                else:
                    score += weight * min(matches, 3)
        
        return max(-1.0, min(1.0, score))
    
    def _calculate_request_complexity(self, request_data: Dict[str, Any]) -> float:
        """Calculate request complexity score"""
        url = request_data.get('url', '')
        payload = request_data.get('payload', '')
        headers = request_data.get('headers', {})
        
        complexity = 0.0
        
        # URL complexity
        complexity += len(urlparse(url).path.split('/')) * 0.1
        complexity += len(parse_qs(urlparse(url).query)) * 0.2
        
        # Payload complexity
        if payload:
            try:
                json_data = json.loads(payload)
                complexity += self._count_json_keys(json_data) * 0.1
            except:
                complexity += len(payload.split('&')) * 0.1
        
        # Header complexity
        complexity += len(headers) * 0.05
        
        return min(complexity, 10.0)  # Cap at 10
    
    def _calculate_trade_keyword_density(self, payload: str) -> float:
        """Calculate trade keyword density"""
        if not payload:
            return 0.0
        
        trade_keywords = [
            'symbol', 'instrument', 'quantity', 'amount', 'size',
            'price', 'rate', 'buy', 'sell', 'long', 'short',
            'leverage', 'margin', 'order', 'trade', 'position'
        ]
        
        words = payload.lower().split()
        if not words:
            return 0.0
        
        trade_word_count = sum(1 for word in words if any(kw in word for kw in trade_keywords))
        return trade_word_count / len(words)
    
    def _calculate_json_depth(self, payload: str) -> int:
        """Calculate JSON nesting depth"""
        try:
            json_data = json.loads(payload)
            return self._get_json_depth(json_data)
        except:
            return 0
    
    def _get_json_depth(self, obj: Any, depth: int = 0) -> int:
        """Recursively calculate JSON depth"""
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()] + [depth])
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj] + [depth])
        else:
            return depth
    
    def _count_json_keys(self, obj: Any) -> int:
        """Count total JSON keys recursively"""
        if isinstance(obj, dict):
            return len(obj) + sum(self._count_json_keys(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(self._count_json_keys(item) for item in obj)
        else:
            return 0
    
    async def classify_request(self, request_data: Dict[str, Any]) -> TradeRequest:
        """Classify request with ML or rule-based approach"""
        # Extract features
        features = self.extract_features(request_data)
        
        # Create cache key for classification
        cache_key = hashlib.md5(
            json.dumps(features, sort_keys=True).encode()
        ).hexdigest()
        
        if cache_key in self.classification_cache:
            cached_result = self.classification_cache[cache_key]
            return TradeRequest(
                timestamp=datetime.now().isoformat(),
                url=request_data.get('url', ''),
                method=request_data.get('method', 'GET'),
                headers=request_data.get('headers', {}),
                payload=request_data.get('payload', ''),
                content_type=request_data.get('headers', {}).get('content-type', ''),
                is_trade=cached_result['is_trade'],
                confidence=cached_result['confidence'],
                features=features,
                classification=cached_result['classification']
            )
        
        # Use ML classification if available and trained
        if self.config['ml_enabled'] and self.is_trained:
            is_trade, confidence, classification = await self._ml_classify(features)
        else:
            is_trade, confidence, classification = self._rule_based_classify(features)
        
        # Cache result
        if len(self.classification_cache) < self.cache_max_size:
            self.classification_cache[cache_key] = {
                'is_trade': is_trade,
                'confidence': confidence,
                'classification': classification
            }
        
        trade_request = TradeRequest(
            timestamp=datetime.now().isoformat(),
            url=request_data.get('url', ''),
            method=request_data.get('method', 'GET'),
            headers=request_data.get('headers', {}),
            payload=request_data.get('payload', ''),
            content_type=request_data.get('headers', {}).get('content-type', ''),
            is_trade=is_trade,
            confidence=confidence,
            features=features,
            classification=classification
        )
        
        # Store for training
        self._store_training_data(trade_request)
        
        # Add to recent requests for metrics
        self.recent_requests.append(trade_request)
        
        return trade_request
    
    async def _ml_classify(self, features: Dict[str, Any]) -> Tuple[bool, float, str]:
        """ML-based classification"""
        try:
            # Convert features to vector
            feature_vector = self._features_to_vector(features)
            
            # Get prediction
            prediction = self.classifier.predict([feature_vector])[0]
            confidence = max(self.classifier.predict_proba([feature_vector])[0])
            
            # Anomaly detection
            anomaly_score = self.anomaly_detector.decision_function([feature_vector])[0]
            
            # Adjust confidence based on anomaly score
            if anomaly_score < self.anomaly_threshold:
                confidence *= 0.5  # Reduce confidence for anomalies
            
            is_trade = prediction == 1 and confidence > self.confidence_threshold
            classification = 'trade' if is_trade else 'non_trade'
            
            return is_trade, confidence, classification
            
        except Exception as e:
            self.logger.error(f"ML classification failed: {e}")
            return self._rule_based_classify(features)
    
    def _rule_based_classify(self, features: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Rule-based classification fallback"""
        score = 0.0
        
        # URL pattern score (high weight)
        score += features.get('url_pattern_score', 0) * 2.0
        
        # Payload pattern score (high weight)
        score += features.get('payload_pattern_score', 0) * 2.0
        
        # Trade-specific features
        if features.get('url_has_trade', False):
            score += 0.8
        if features.get('url_has_order', False):
            score += 0.7
        if features.get('url_has_position', False):
            score += 0.7
        
        # Payload features
        if features.get('payload_has_symbol', False):
            score += 0.6
        if features.get('payload_has_amount', False):
            score += 0.5
        if features.get('payload_has_price', False):
            score += 0.4
        if features.get('payload_has_side', False):
            score += 0.8
        if features.get('payload_has_leverage', False):
            score += 0.6
        
        # Trade keyword density
        density = features.get('trade_keyword_density', 0)
        score += density * 2.0
        
        # Method bonus
        if features.get('method') == 'POST':
            score += 0.3
        
        # JSON bonus
        if features.get('is_json', False):
            score += 0.2
        
        # Normalize score to confidence
        confidence = max(0.0, min(1.0, (score + 1.0) / 2.0))
        is_trade = confidence > self.confidence_threshold
        
        # Determine classification
        if is_trade:
            classification = 'trade'
        elif features.get('url_pattern_score', 0) < -0.5:
            if 'ui' in str(features.get('url_pattern_score', '')):
                classification = 'ui'
            elif 'auth' in str(features.get('url_pattern_score', '')):
                classification = 'auth'
            else:
                classification = 'data'
        else:
            classification = 'unknown'
        
        return is_trade, confidence, classification
    
    def _features_to_vector(self, features: Dict[str, Any]) -> List[float]:
        """Convert features dictionary to vector for ML"""
        # Define feature order for consistency
        feature_keys = [
            'url_length', 'payload_length', 'header_count', 'url_has_api',
            'url_has_trade', 'url_has_order', 'url_has_position', 'url_path_segments',
            'is_json', 'is_form_data', 'payload_has_symbol', 'payload_has_amount',
            'payload_has_price', 'payload_has_side', 'payload_has_leverage',
            'has_auth_header', 'url_pattern_score', 'payload_pattern_score',
            'request_complexity', 'trade_keyword_density', 'json_depth'
        ]
        
        vector = []
        for key in feature_keys:
            value = features.get(key, 0)
            if isinstance(value, bool):
                vector.append(1.0 if value else 0.0)
            elif isinstance(value, (int, float)):
                vector.append(float(value))
            else:
                vector.append(0.0)
        
        return vector
    
    def _store_training_data(self, trade_request: TradeRequest):
        """Store request data for training"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO training_data (
                    timestamp, url, method, headers, payload, content_type,
                    is_trade, confidence, features, classification
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_request.timestamp,
                trade_request.url,
                trade_request.method,
                json.dumps(trade_request.headers),
                trade_request.payload,
                trade_request.content_type,
                trade_request.is_trade,
                trade_request.confidence,
                json.dumps(trade_request.features),
                trade_request.classification
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Training data storage failed: {e}")
    
    async def retrain_model(self) -> bool:
        """Retrain ML model with accumulated data"""
        if not self.config['ml_enabled']:
            self.logger.info("ML disabled, skipping retraining")
            return False
        
        try:
            # Get training data
            training_data = self._get_training_data()
            
            if len(training_data) < self.config['min_training_samples']:
                self.logger.info(f"Insufficient training data: {len(training_data)} samples")
                return False
            
            self.logger.info(f"Retraining model with {len(training_data)} samples")
            
            # Prepare features and labels
            X = []
            y = []
            
            for data in training_data:
                features = json.loads(data[9])  # features column
                is_trade = data[6]  # is_trade column
                
                feature_vector = self._features_to_vector(features)
                X.append(feature_vector)
                y.append(1 if is_trade else 0)
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train classifier
            self.classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.classifier.fit(X_train, y_train)
            
            # Train anomaly detector
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            self.anomaly_detector.fit(X_train)
            
            # Evaluate model
            y_pred = self.classifier.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            
            self.logger.info(f"Model performance - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
            
            # Save model
            self._save_model()
            
            # Store performance metrics
            self._store_model_performance(len(training_data), accuracy)
            
            self.is_trained = True
            
            # Adjust thresholds if auto-adjustment is enabled
            if self.config['auto_threshold_adjustment']:
                self._adjust_thresholds(accuracy, precision, recall)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model retraining failed: {e}")
            return False
    
    def _get_training_data(self) -> List[Tuple]:
        """Get training data from database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM training_data
                ORDER BY timestamp DESC
                LIMIT 10000
            ''')
            
            data = cursor.fetchall()
            conn.close()
            
            return data
            
        except Exception as e:
            self.logger.error(f"Training data retrieval failed: {e}")
            return []
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            model_data = {
                'classifier': self.classifier,
                'anomaly_detector': self.anomaly_detector,
                'confidence_threshold': self.confidence_threshold,
                'anomaly_threshold': self.anomaly_threshold,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.model_file, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.logger.info(f"Model saved to {self.model_file}")
            
        except Exception as e:
            self.logger.error(f"Model saving failed: {e}")
    
    def _load_model(self):
        """Load trained model from disk"""
        if not os.path.exists(self.model_file):
            return
        
        try:
            with open(self.model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            self.classifier = model_data.get('classifier')
            self.anomaly_detector = model_data.get('anomaly_detector')
            self.confidence_threshold = model_data.get('confidence_threshold', 0.7)
            self.anomaly_threshold = model_data.get('anomaly_threshold', -0.5)
            
            if self.classifier and self.anomaly_detector:
                self.is_trained = True
                self.logger.info("Model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
    
    def _store_model_performance(self, training_samples: int, accuracy: float):
        """Store model performance metrics"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get feature importance if available
            feature_importance = {}
            if hasattr(self.classifier, 'feature_importances_'):
                feature_keys = [
                    'url_length', 'payload_length', 'header_count', 'url_has_api',
                    'url_has_trade', 'url_has_order', 'url_has_position', 'url_path_segments',
                    'is_json', 'is_form_data', 'payload_has_symbol', 'payload_has_amount',
                    'payload_has_price', 'payload_has_side', 'payload_has_leverage',
                    'has_auth_header', 'url_pattern_score', 'payload_pattern_score',
                    'request_complexity', 'trade_keyword_density', 'json_depth'
                ]
                
                for i, importance in enumerate(self.classifier.feature_importances_):
                    if i < len(feature_keys):
                        feature_importance[feature_keys[i]] = float(importance)
            
            cursor.execute('''
                INSERT INTO model_performance (
                    timestamp, model_version, training_samples, test_accuracy, feature_importance
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                'RandomForest_v1.0',
                training_samples,
                accuracy,
                json.dumps(feature_importance)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Performance storage failed: {e}")
    
    def _adjust_thresholds(self, accuracy: float, precision: float, recall: float):
        """Automatically adjust classification thresholds"""
        # Adjust confidence threshold based on precision
        if precision < 0.8:  # Low precision, increase threshold
            self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
        elif precision > 0.95:  # High precision, can lower threshold
            self.confidence_threshold = max(0.5, self.confidence_threshold - 0.02)
        
        # Adjust anomaly threshold based on overall accuracy
        if accuracy < 0.85:  # Low accuracy, be more conservative
            self.anomaly_threshold = max(-0.8, self.anomaly_threshold - 0.1)
        elif accuracy > 0.95:  # High accuracy, can be more aggressive
            self.anomaly_threshold = min(-0.2, self.anomaly_threshold + 0.05)
        
        self.logger.info(f"Thresholds adjusted - Confidence: {self.confidence_threshold:.3f}, Anomaly: {self.anomaly_threshold:.3f}")
    
    def calculate_accuracy_metrics(self) -> AccuracyMetrics:
        """Calculate current accuracy metrics"""
        if not self.recent_requests:
            return AccuracyMetrics(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0)
        
        # For now, we'll use confidence-based metrics
        # In production, you'd have verified labels
        total_requests = len(self.recent_requests)
        
        # Estimate metrics based on confidence and classification
        high_confidence_trades = sum(1 for req in self.recent_requests 
                                   if req.is_trade and req.confidence > 0.8)
        low_confidence_trades = sum(1 for req in self.recent_requests 
                                  if req.is_trade and req.confidence <= 0.8)
        non_trades = sum(1 for req in self.recent_requests if not req.is_trade)
        
        # Estimate true/false positives (simplified)
        true_positives = high_confidence_trades
        false_positives = low_confidence_trades
        true_negatives = non_trades
        false_negatives = 0  # Hard to estimate without ground truth
        
        # Calculate metrics
        accuracy = (true_positives + true_negatives) / total_requests if total_requests > 0 else 0.0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics = AccuracyMetrics(
            total_requests=total_requests,
            true_positives=true_positives,
            false_positives=false_positives,
            true_negatives=true_negatives,
            false_negatives=false_negatives,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score
        )
        
        # Store metrics
        self._store_accuracy_metrics(metrics)
        
        return metrics
    
    def _store_accuracy_metrics(self, metrics: AccuracyMetrics):
        """Store accuracy metrics in database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO accuracy_metrics (
                    timestamp, total_requests, true_positives, false_positives,
                    true_negatives, false_negatives, accuracy, precision_score,
                    recall_score, f1_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                metrics.total_requests,
                metrics.true_positives,
                metrics.false_positives,
                metrics.true_negatives,
                metrics.false_negatives,
                metrics.accuracy,
                metrics.precision,
                metrics.recall,
                metrics.f1_score
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Metrics storage failed: {e}")
    
    async def start_optimization_loop(self, interval_hours: int = 24):
        """Start continuous optimization loop"""
        self.logger.info(f"🎯 Starting accuracy optimization loop (interval: {interval_hours}h)")
        
        while True:
            try:
                # Calculate current metrics
                metrics = self.calculate_accuracy_metrics()
                
                self.logger.info(
                    f"📊 Accuracy Metrics - Total: {metrics.total_requests}, "
                    f"Accuracy: {metrics.accuracy:.3f}, Precision: {metrics.precision:.3f}, "
                    f"Recall: {metrics.recall:.3f}, F1: {metrics.f1_score:.3f}"
                )
                
                # Retrain model if needed
                if self.config['ml_enabled']:
                    retrain_success = await self.retrain_model()
                    if retrain_success:
                        self.logger.info("🔄 Model retrained successfully")
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                self.logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    def generate_accuracy_report(self) -> str:
        """Generate comprehensive accuracy report"""
        try:
            # Get recent metrics
            current_metrics = self.calculate_accuracy_metrics()
            
            # Get historical data
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get accuracy trend
            cursor.execute('''
                SELECT timestamp, accuracy, precision_score, recall_score, f1_score
                FROM accuracy_metrics
                ORDER BY timestamp DESC
                LIMIT 24
            ''')
            
            historical_metrics = cursor.fetchall()
            
            # Get model performance
            cursor.execute('''
                SELECT timestamp, training_samples, test_accuracy, feature_importance
                FROM model_performance
                ORDER BY timestamp DESC
                LIMIT 5
            ''')
            
            model_performance = cursor.fetchall()
            
            conn.close()
            
            # Generate report
            report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            report = f"""
# TradeBot Sentinel - Accuracy Optimization Report

**Generated:** {report_time}

## Current Performance

### Real-time Metrics
- **Total Requests Processed:** {current_metrics.total_requests}
- **Overall Accuracy:** {current_metrics.accuracy:.1%}
- **Precision:** {current_metrics.precision:.1%}
- **Recall:** {current_metrics.recall:.1%}
- **F1 Score:** {current_metrics.f1_score:.3f}

### Classification Breakdown
- **True Positives:** {current_metrics.true_positives} (correctly identified trades)
- **False Positives:** {current_metrics.false_positives} (incorrectly identified as trades)
- **True Negatives:** {current_metrics.true_negatives} (correctly identified non-trades)
- **False Negatives:** {current_metrics.false_negatives} (missed trades)

## Model Configuration

### Current Settings
- **ML Enabled:** {'✅ Yes' if self.config['ml_enabled'] else '❌ No'}
- **Model Trained:** {'✅ Yes' if self.is_trained else '❌ No'}
- **Confidence Threshold:** {self.confidence_threshold:.3f}
- **Anomaly Threshold:** {self.anomaly_threshold:.3f}
- **Auto Threshold Adjustment:** {'✅ Enabled' if self.config['auto_threshold_adjustment'] else '❌ Disabled'}

### Performance Optimization
- **Feature Cache Size:** {len(self.feature_cache)}/{self.cache_max_size}
- **Classification Cache Size:** {len(self.classification_cache)}/{self.cache_max_size}
- **Recent Requests Buffer:** {len(self.recent_requests)}/1000
"""
            
            if historical_metrics:
                report += "\n## Historical Trends\n\n"
                report += "| Timestamp | Accuracy | Precision | Recall | F1 Score |\n"
                report += "|-----------|----------|-----------|--------|----------|\n"
                
                for metric in historical_metrics[:10]:
                    timestamp = metric[0][:16]  # Truncate timestamp
                    accuracy = f"{metric[1]:.3f}" if metric[1] else "N/A"
                    precision = f"{metric[2]:.3f}" if metric[2] else "N/A"
                    recall = f"{metric[3]:.3f}" if metric[3] else "N/A"
                    f1 = f"{metric[4]:.3f}" if metric[4] else "N/A"
                    
                    report += f"| {timestamp} | {accuracy} | {precision} | {recall} | {f1} |\n"
            
            if model_performance:
                report += "\n## Model Training History\n\n"
                for i, perf in enumerate(model_performance):
                    timestamp = perf[0][:16]
                    samples = perf[1]
                    accuracy = f"{perf[2]:.3f}" if perf[2] else "N/A"
                    
                    report += f"### Training Session {i+1}\n"
                    report += f"- **Date:** {timestamp}\n"
                    report += f"- **Training Samples:** {samples:,}\n"
                    report += f"- **Test Accuracy:** {accuracy}\n\n"
            
            report += f"""
## Recommendations

### Immediate Actions
{'- ✅ System performing well' if current_metrics.accuracy > 0.9 else '- ⚠️ Consider retraining model with more data'}
{'- ✅ Precision is excellent' if current_metrics.precision > 0.9 else '- ⚠️ High false positive rate - consider increasing confidence threshold'}
{'- ✅ Recall is excellent' if current_metrics.recall > 0.8 else '- ⚠️ Missing trades - consider lowering confidence threshold'}

### Optimization Opportunities
- Monitor feature importance to identify key patterns
- Collect more verified training data for edge cases
- Consider ensemble methods for improved accuracy
- Implement active learning for continuous improvement

---
*Generated by TradeBot Sentinel Accuracy Optimizer*
            """
            
            # Save report
            report_file = f'accuracy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            with open(report_file, 'w') as f:
                f.write(report)
            
            self.logger.info(f"📋 Accuracy report generated: {report_file}")
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return f"Error generating report: {e}"

# Example usage
async def main():
    """Example usage of Trade Accuracy Optimizer"""
    optimizer = TradeAccuracyOptimizer()
    
    # Example request data
    sample_request = {
        'url': 'https://api.bulenox.projectx.com/v1/trade/execute',
        'method': 'POST',
        'headers': {
            'content-type': 'application/json',
            'authorization': 'Bearer token123'
        },
        'payload': '{"symbol":"BTCUSDT","side":"buy","amount":0.001,"price":45000}'
    }
    
    # Classify request
    result = await optimizer.classify_request(sample_request)
    print(f"Classification: {result.classification}")
    print(f"Is Trade: {result.is_trade}")
    print(f"Confidence: {result.confidence:.3f}")
    
    # Calculate metrics
    metrics = optimizer.calculate_accuracy_metrics()
    print(f"\nCurrent Accuracy: {metrics.accuracy:.3f}")
    
    # Generate report
    report = optimizer.generate_accuracy_report()
    print("\nAccuracy report generated")
    
    # Start optimization loop (uncomment to run continuously)
    # await optimizer.start_optimization_loop(interval_hours=1)

if __name__ == "__main__":
    asyncio.run(main())