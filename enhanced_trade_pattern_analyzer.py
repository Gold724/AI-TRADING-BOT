#!/usr/bin/env python3
"""
Enhanced Trade Pattern Analyzer for TradeBot Sentinel
Advanced ML-based pattern recognition and trade prediction
"""

import asyncio
import json
import logging
import sqlite3
import time
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
from urllib.parse import urlparse, parse_qs
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trade_pattern_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatternType(Enum):
    URL_PATTERN = "url_pattern"
    PAYLOAD_PATTERN = "payload_pattern"
    HEADER_PATTERN = "header_pattern"
    TIMING_PATTERN = "timing_pattern"
    SEQUENCE_PATTERN = "sequence_pattern"

class ConfidenceLevel(Enum):
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9

@dataclass
class TradePattern:
    id: str
    pattern_type: PatternType
    pattern_data: Dict[str, Any]
    confidence_score: float
    success_rate: float
    occurrence_count: int
    last_seen: str
    created_at: str
    metadata: Dict[str, Any]

@dataclass
class TradeSignal:
    timestamp: str
    url: str
    method: str
    payload: str
    headers: Dict[str, str]
    confidence_score: float
    matched_patterns: List[str]
    prediction: str
    metadata: Dict[str, Any]

@dataclass
class PatternAnalysis:
    total_patterns: int
    high_confidence_patterns: int
    success_rate: float
    most_common_patterns: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]
    recommendations: List[str]

class EnhancedTradePatternAnalyzer:
    def __init__(self, db_path: str = "trade_patterns.db"):
        self.db_path = db_path
        self.db_connection = None
        self.patterns = {}
        self.trade_signals = []
        self.learning_enabled = True
        
        # Pattern recognition thresholds
        self.thresholds = {
            'min_occurrences': 3,
            'min_confidence': 0.5,
            'pattern_similarity': 0.8,
            'time_window_minutes': 30
        }
        
        # Trade-related keywords and patterns
        self.trade_keywords = {
            'symbols': ['symbol', 'ticker', 'asset', 'pair', 'instrument'],
            'actions': ['buy', 'sell', 'order', 'trade', 'execute', 'place'],
            'amounts': ['amount', 'quantity', 'size', 'volume', 'lots'],
            'prices': ['price', 'rate', 'value', 'cost', 'limit', 'stop'],
            'types': ['market', 'limit', 'stop', 'trailing', 'bracket']
        }
        
        # URL patterns that commonly indicate trading
        self.trade_url_patterns = [
            r'/api/v\d+/trade',
            r'/trading/order',
            r'/execute',
            r'/place.*order',
            r'/buy|/sell',
            r'/position',
            r'/portfolio/action'
        ]
        
    async def initialize(self) -> None:
        """Initialize the pattern analyzer"""
        try:
            await self.init_database()
            await self.load_existing_patterns()
            logger.info("Enhanced Trade Pattern Analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pattern analyzer: {e}")
            raise
    
    async def init_database(self) -> None:
        """Initialize SQLite database for pattern storage"""
        try:
            self.db_connection = sqlite3.connect(self.db_path)
            cursor = self.db_connection.cursor()
            
            # Trade patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_patterns (
                    id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence_score REAL,
                    success_rate REAL,
                    occurrence_count INTEGER,
                    last_seen TEXT,
                    created_at TEXT,
                    metadata TEXT
                )
            ''')
            
            # Trade signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    url TEXT NOT NULL,
                    method TEXT,
                    payload TEXT,
                    headers TEXT,
                    confidence_score REAL,
                    matched_patterns TEXT,
                    prediction TEXT,
                    metadata TEXT
                )
            ''')
            
            # Pattern performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pattern_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT,
                    timestamp TEXT,
                    prediction_correct BOOLEAN,
                    confidence_score REAL,
                    actual_outcome TEXT,
                    metadata TEXT
                )
            ''')
            
            # Learning data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_hash TEXT UNIQUE,
                    url TEXT,
                    method TEXT,
                    payload TEXT,
                    headers TEXT,
                    timestamp TEXT,
                    is_trade BOOLEAN,
                    confidence_score REAL,
                    features TEXT
                )
            ''')
            
            self.db_connection.commit()
            logger.info("Pattern analyzer database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def load_existing_patterns(self) -> None:
        """Load existing patterns from database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('SELECT * FROM trade_patterns')
            
            for row in cursor.fetchall():
                pattern = TradePattern(
                    id=row[0],
                    pattern_type=PatternType(row[1]),
                    pattern_data=json.loads(row[2]),
                    confidence_score=row[3],
                    success_rate=row[4],
                    occurrence_count=row[5],
                    last_seen=row[6],
                    created_at=row[7],
                    metadata=json.loads(row[8]) if row[8] else {}
                )
                self.patterns[pattern.id] = pattern
            
            logger.info(f"Loaded {len(self.patterns)} existing patterns")
            
        except Exception as e:
            logger.error(f"Error loading existing patterns: {e}")
    
    async def analyze_request(self, url: str, method: str, payload: str, headers: Dict[str, str]) -> TradeSignal:
        """Analyze a request and determine if it's trade-related"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Extract features from the request
            features = await self.extract_features(url, method, payload, headers)
            
            # Calculate confidence score
            confidence_score = await self.calculate_confidence(features)
            
            # Find matching patterns
            matched_patterns = await self.find_matching_patterns(features)
            
            # Make prediction
            prediction = await self.make_prediction(confidence_score, matched_patterns)
            
            # Create trade signal
            signal = TradeSignal(
                timestamp=timestamp,
                url=url,
                method=method,
                payload=payload[:1000],  # Truncate for storage
                headers=headers,
                confidence_score=confidence_score,
                matched_patterns=[p.id for p in matched_patterns],
                prediction=prediction,
                metadata={
                    'features': features,
                    'pattern_count': len(matched_patterns)
                }
            )
            
            # Store signal
            await self.store_trade_signal(signal)
            
            # Learn from this request if enabled
            if self.learning_enabled:
                await self.learn_from_request(url, method, payload, headers, features, confidence_score)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing request: {e}")
            return None
    
    async def extract_features(self, url: str, method: str, payload: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract features from a request for pattern analysis"""
        try:
            features = {
                'url_features': await self.extract_url_features(url),
                'payload_features': await self.extract_payload_features(payload),
                'header_features': await self.extract_header_features(headers),
                'method': method.upper(),
                'timestamp_features': await self.extract_timestamp_features()
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    async def extract_url_features(self, url: str) -> Dict[str, Any]:
        """Extract features from URL"""
        try:
            parsed = urlparse(url)
            
            features = {
                'domain': parsed.netloc,
                'path': parsed.path,
                'path_segments': parsed.path.split('/'),
                'query_params': parse_qs(parsed.query),
                'has_trade_keywords': any(keyword in url.lower() for keywords in self.trade_keywords.values() for keyword in keywords),
                'matches_trade_patterns': any(re.search(pattern, url, re.IGNORECASE) for pattern in self.trade_url_patterns),
                'path_depth': len([seg for seg in parsed.path.split('/') if seg]),
                'has_api_indicator': '/api/' in url.lower() or '/v' in url.lower(),
                'has_numeric_id': bool(re.search(r'/\d+', parsed.path))
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting URL features: {e}")
            return {}
    
    async def extract_payload_features(self, payload: str) -> Dict[str, Any]:
        """Extract features from request payload"""
        try:
            if not payload:
                return {'empty': True}
            
            features = {
                'empty': False,
                'length': len(payload),
                'is_json': False,
                'is_form_data': False,
                'trade_keyword_count': 0,
                'numeric_values': [],
                'field_names': []
            }
            
            # Try to parse as JSON
            try:
                json_data = json.loads(payload)
                features['is_json'] = True
                features['field_names'] = list(json_data.keys()) if isinstance(json_data, dict) else []
                
                # Count trade-related keywords
                payload_lower = json.dumps(json_data).lower()
                for category, keywords in self.trade_keywords.items():
                    for keyword in keywords:
                        features['trade_keyword_count'] += payload_lower.count(keyword)
                
                # Extract numeric values
                features['numeric_values'] = self.extract_numeric_values(json.dumps(json_data))
                
            except json.JSONDecodeError:
                # Check if it's form data
                if '=' in payload and ('&' in payload or len(payload.split('=')) == 2):
                    features['is_form_data'] = True
                    form_data = parse_qs(payload)
                    features['field_names'] = list(form_data.keys())
                
                # Count trade keywords in raw payload
                payload_lower = payload.lower()
                for category, keywords in self.trade_keywords.items():
                    for keyword in keywords:
                        features['trade_keyword_count'] += payload_lower.count(keyword)
                
                features['numeric_values'] = self.extract_numeric_values(payload)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting payload features: {e}")
            return {'empty': True}
    
    async def extract_header_features(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract features from request headers"""
        try:
            features = {
                'content_type': headers.get('content-type', '').lower(),
                'has_auth': any(key.lower() in ['authorization', 'x-auth-token', 'x-api-key'] for key in headers.keys()),
                'has_csrf': any('csrf' in key.lower() for key in headers.keys()),
                'user_agent': headers.get('user-agent', ''),
                'custom_headers': [key for key in headers.keys() if key.lower().startswith('x-')],
                'header_count': len(headers)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting header features: {e}")
            return {}
    
    async def extract_timestamp_features(self) -> Dict[str, Any]:
        """Extract timestamp-based features"""
        try:
            now = datetime.now()
            
            features = {
                'hour': now.hour,
                'day_of_week': now.weekday(),
                'is_business_hours': 9 <= now.hour <= 17,
                'is_weekend': now.weekday() >= 5
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting timestamp features: {e}")
            return {}
    
    def extract_numeric_values(self, text: str) -> List[float]:
        """Extract numeric values from text"""
        try:
            # Find all numeric values (including decimals)
            numeric_pattern = r'\b\d+(?:\.\d+)?\b'
            matches = re.findall(numeric_pattern, text)
            return [float(match) for match in matches]
        except:
            return []
    
    async def calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence score for trade detection"""
        try:
            confidence = 0.0
            
            # URL-based confidence
            url_features = features.get('url_features', {})
            if url_features.get('has_trade_keywords', False):
                confidence += 0.3
            if url_features.get('matches_trade_patterns', False):
                confidence += 0.4
            if url_features.get('has_api_indicator', False):
                confidence += 0.1
            
            # Payload-based confidence
            payload_features = features.get('payload_features', {})
            if not payload_features.get('empty', True):
                trade_keyword_count = payload_features.get('trade_keyword_count', 0)
                if trade_keyword_count > 0:
                    confidence += min(0.3, trade_keyword_count * 0.1)
                
                if payload_features.get('is_json', False):
                    confidence += 0.1
                
                # Check for numeric values (potential prices/amounts)
                numeric_values = payload_features.get('numeric_values', [])
                if numeric_values:
                    confidence += 0.1
            
            # Header-based confidence
            header_features = features.get('header_features', {})
            if header_features.get('has_auth', False):
                confidence += 0.1
            
            # Method-based confidence
            if features.get('method') == 'POST':
                confidence += 0.1
            
            # Normalize confidence to 0-1 range
            confidence = min(1.0, confidence)
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    async def find_matching_patterns(self, features: Dict[str, Any]) -> List[TradePattern]:
        """Find patterns that match the current request features"""
        try:
            matching_patterns = []
            
            for pattern in self.patterns.values():
                similarity = await self.calculate_pattern_similarity(pattern, features)
                if similarity >= self.thresholds['pattern_similarity']:
                    matching_patterns.append(pattern)
            
            # Sort by confidence score
            matching_patterns.sort(key=lambda p: p.confidence_score, reverse=True)
            
            return matching_patterns
            
        except Exception as e:
            logger.error(f"Error finding matching patterns: {e}")
            return []
    
    async def calculate_pattern_similarity(self, pattern: TradePattern, features: Dict[str, Any]) -> float:
        """Calculate similarity between a pattern and current features"""
        try:
            pattern_data = pattern.pattern_data
            similarity = 0.0
            total_weight = 0.0
            
            # Compare URL features
            if 'url_features' in pattern_data and 'url_features' in features:
                url_sim = self.compare_dict_features(pattern_data['url_features'], features['url_features'])
                similarity += url_sim * 0.4
                total_weight += 0.4
            
            # Compare payload features
            if 'payload_features' in pattern_data and 'payload_features' in features:
                payload_sim = self.compare_dict_features(pattern_data['payload_features'], features['payload_features'])
                similarity += payload_sim * 0.3
                total_weight += 0.3
            
            # Compare header features
            if 'header_features' in pattern_data and 'header_features' in features:
                header_sim = self.compare_dict_features(pattern_data['header_features'], features['header_features'])
                similarity += header_sim * 0.2
                total_weight += 0.2
            
            # Compare method
            if pattern_data.get('method') == features.get('method'):
                similarity += 0.1
                total_weight += 0.1
            
            return similarity / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating pattern similarity: {e}")
            return 0.0
    
    def compare_dict_features(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> float:
        """Compare two feature dictionaries"""
        try:
            if not dict1 or not dict2:
                return 0.0
            
            common_keys = set(dict1.keys()) & set(dict2.keys())
            if not common_keys:
                return 0.0
            
            matches = 0
            for key in common_keys:
                if dict1[key] == dict2[key]:
                    matches += 1
                elif isinstance(dict1[key], (int, float)) and isinstance(dict2[key], (int, float)):
                    # For numeric values, consider close values as matches
                    if abs(dict1[key] - dict2[key]) / max(abs(dict1[key]), abs(dict2[key]), 1) < 0.1:
                        matches += 0.5
            
            return matches / len(common_keys)
            
        except Exception as e:
            logger.error(f"Error comparing dict features: {e}")
            return 0.0
    
    async def make_prediction(self, confidence_score: float, matched_patterns: List[TradePattern]) -> str:
        """Make a prediction about whether this is a trade request"""
        try:
            if confidence_score >= 0.8:
                return "VERY_LIKELY_TRADE"
            elif confidence_score >= 0.6:
                return "LIKELY_TRADE"
            elif confidence_score >= 0.4:
                return "POSSIBLE_TRADE"
            elif confidence_score >= 0.2:
                return "UNLIKELY_TRADE"
            else:
                return "NOT_TRADE"
                
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return "UNKNOWN"
    
    async def store_trade_signal(self, signal: TradeSignal) -> None:
        """Store trade signal in database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO trade_signals 
                (timestamp, url, method, payload, headers, confidence_score, matched_patterns, prediction, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.timestamp,
                signal.url,
                signal.method,
                signal.payload,
                json.dumps(signal.headers),
                signal.confidence_score,
                json.dumps(signal.matched_patterns),
                signal.prediction,
                json.dumps(signal.metadata)
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing trade signal: {e}")
    
    async def learn_from_request(self, url: str, method: str, payload: str, headers: Dict[str, str], 
                                features: Dict[str, Any], confidence_score: float) -> None:
        """Learn from a request to improve pattern recognition"""
        try:
            # Create a hash for the request
            request_hash = hashlib.md5(f"{url}{method}{payload}".encode()).hexdigest()
            
            # Determine if this is likely a trade based on confidence
            is_trade = confidence_score >= self.thresholds['min_confidence']
            
            # Store learning data
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learning_data 
                (request_hash, url, method, payload, headers, timestamp, is_trade, confidence_score, features)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_hash,
                url,
                method,
                payload[:1000],  # Truncate
                json.dumps(headers),
                datetime.now().isoformat(),
                is_trade,
                confidence_score,
                json.dumps(features)
            ))
            self.db_connection.commit()
            
            # Update or create patterns
            if is_trade:
                await self.update_patterns(features, confidence_score)
            
        except Exception as e:
            logger.error(f"Error learning from request: {e}")
    
    async def update_patterns(self, features: Dict[str, Any], confidence_score: float) -> None:
        """Update existing patterns or create new ones"""
        try:
            # Create pattern ID based on features
            pattern_id = hashlib.md5(json.dumps(features, sort_keys=True).encode()).hexdigest()[:16]
            
            if pattern_id in self.patterns:
                # Update existing pattern
                pattern = self.patterns[pattern_id]
                pattern.occurrence_count += 1
                pattern.last_seen = datetime.now().isoformat()
                pattern.confidence_score = (pattern.confidence_score + confidence_score) / 2
                
            else:
                # Create new pattern
                pattern = TradePattern(
                    id=pattern_id,
                    pattern_type=PatternType.URL_PATTERN,  # Default type
                    pattern_data=features,
                    confidence_score=confidence_score,
                    success_rate=1.0,  # Initial success rate
                    occurrence_count=1,
                    last_seen=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat(),
                    metadata={}
                )
                self.patterns[pattern_id] = pattern
            
            # Store pattern in database
            await self.store_pattern(pattern)
            
        except Exception as e:
            logger.error(f"Error updating patterns: {e}")
    
    async def store_pattern(self, pattern: TradePattern) -> None:
        """Store pattern in database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO trade_patterns 
                (id, pattern_type, pattern_data, confidence_score, success_rate, occurrence_count, last_seen, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.id,
                pattern.pattern_type.value,
                json.dumps(pattern.pattern_data),
                pattern.confidence_score,
                pattern.success_rate,
                pattern.occurrence_count,
                pattern.last_seen,
                pattern.created_at,
                json.dumps(pattern.metadata)
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing pattern: {e}")
    
    async def analyze_patterns(self) -> PatternAnalysis:
        """Analyze current patterns and provide insights"""
        try:
            total_patterns = len(self.patterns)
            high_confidence_patterns = sum(1 for p in self.patterns.values() if p.confidence_score >= 0.7)
            
            if total_patterns > 0:
                avg_success_rate = sum(p.success_rate for p in self.patterns.values()) / total_patterns
            else:
                avg_success_rate = 0.0
            
            # Find most common patterns
            most_common = sorted(
                self.patterns.values(),
                key=lambda p: p.occurrence_count,
                reverse=True
            )[:5]
            
            most_common_data = [
                {
                    'id': p.id,
                    'confidence': p.confidence_score,
                    'occurrences': p.occurrence_count,
                    'success_rate': p.success_rate
                } for p in most_common
            ]
            
            # Trend analysis
            trend_analysis = await self.analyze_trends()
            
            # Generate recommendations
            recommendations = await self.generate_recommendations()
            
            analysis = PatternAnalysis(
                total_patterns=total_patterns,
                high_confidence_patterns=high_confidence_patterns,
                success_rate=avg_success_rate,
                most_common_patterns=most_common_data,
                trend_analysis=trend_analysis,
                recommendations=recommendations
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return PatternAnalysis(
                total_patterns=0,
                high_confidence_patterns=0,
                success_rate=0.0,
                most_common_patterns=[],
                trend_analysis={},
                recommendations=[]
            )
    
    async def analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends in trade patterns"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get recent signals
            cursor.execute('''
                SELECT confidence_score, prediction, timestamp
                FROM trade_signals 
                WHERE timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
            ''')
            
            recent_signals = cursor.fetchall()
            
            if not recent_signals:
                return {'no_data': True}
            
            # Calculate trends
            avg_confidence = sum(s[0] for s in recent_signals) / len(recent_signals)
            
            prediction_counts = Counter(s[1] for s in recent_signals)
            
            # Time-based analysis
            hourly_counts = defaultdict(int)
            for signal in recent_signals:
                hour = datetime.fromisoformat(signal[2]).hour
                hourly_counts[hour] += 1
            
            trends = {
                'avg_confidence_24h': avg_confidence,
                'total_signals_24h': len(recent_signals),
                'prediction_distribution': dict(prediction_counts),
                'peak_hours': sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3],
                'trend_direction': 'increasing' if avg_confidence > 0.5 else 'stable'
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {}
    
    async def generate_recommendations(self) -> List[str]:
        """Generate recommendations for improving pattern detection"""
        try:
            recommendations = []
            
            # Check pattern count
            if len(self.patterns) < 10:
                recommendations.append("Collect more trading data to improve pattern recognition")
            
            # Check confidence distribution
            high_conf_patterns = sum(1 for p in self.patterns.values() if p.confidence_score >= 0.7)
            if high_conf_patterns / max(len(self.patterns), 1) < 0.3:
                recommendations.append("Consider adjusting confidence thresholds or feature extraction")
            
            # Check pattern diversity
            pattern_types = set(p.pattern_type for p in self.patterns.values())
            if len(pattern_types) < 3:
                recommendations.append("Expand pattern types to include timing and sequence patterns")
            
            # Check recent activity
            recent_patterns = [p for p in self.patterns.values() 
                             if datetime.fromisoformat(p.last_seen) > datetime.now() - timedelta(hours=24)]
            if len(recent_patterns) == 0:
                recommendations.append("No recent trading activity detected - verify system is capturing requests")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    async def optimize_thresholds(self) -> None:
        """Optimize detection thresholds based on performance data"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get performance data
            cursor.execute('''
                SELECT confidence_score, prediction_correct
                FROM pattern_performance 
                WHERE timestamp > datetime('now', '-7 days')
            ''')
            
            performance_data = cursor.fetchall()
            
            if len(performance_data) < 10:
                logger.info("Insufficient performance data for threshold optimization")
                return
            
            # Find optimal threshold
            best_threshold = 0.5
            best_accuracy = 0.0
            
            for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
                correct_predictions = 0
                total_predictions = 0
                
                for conf_score, is_correct in performance_data:
                    if conf_score >= threshold:
                        total_predictions += 1
                        if is_correct:
                            correct_predictions += 1
                
                if total_predictions > 0:
                    accuracy = correct_predictions / total_predictions
                    if accuracy > best_accuracy:
                        best_accuracy = accuracy
                        best_threshold = threshold
            
            # Update threshold if improvement is significant
            if best_accuracy > 0.8 and abs(best_threshold - self.thresholds['min_confidence']) > 0.1:
                self.thresholds['min_confidence'] = best_threshold
                logger.info(f"Optimized confidence threshold to {best_threshold} (accuracy: {best_accuracy:.2f})")
            
        except Exception as e:
            logger.error(f"Error optimizing thresholds: {e}")
    
    async def cleanup_old_data(self) -> None:
        """Clean up old data to maintain performance"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            cursor = self.db_connection.cursor()
            
            # Clean old signals
            cursor.execute('DELETE FROM trade_signals WHERE timestamp < ?', (cutoff_date,))
            
            # Clean old learning data
            cursor.execute('DELETE FROM learning_data WHERE timestamp < ?', (cutoff_date,))
            
            # Clean old performance data
            cursor.execute('DELETE FROM pattern_performance WHERE timestamp < ?', (cutoff_date,))
            
            # Remove patterns with low occurrence and old last_seen
            old_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute('''
                DELETE FROM trade_patterns 
                WHERE occurrence_count < ? AND last_seen < ?
            ''', (self.thresholds['min_occurrences'], old_cutoff))
            
            self.db_connection.commit()
            
            # Reload patterns
            await self.load_existing_patterns()
            
            logger.info("Old pattern data cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def get_analysis_report(self) -> Dict[str, Any]:
        """Get comprehensive analysis report"""
        try:
            analysis = await self.analyze_patterns()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'pattern_analysis': asdict(analysis),
                'system_status': {
                    'learning_enabled': self.learning_enabled,
                    'total_patterns': len(self.patterns),
                    'database_connected': self.db_connection is not None
                },
                'thresholds': self.thresholds
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating analysis report: {e}")
            return {'error': str(e)}
    
    async def close(self) -> None:
        """Close the pattern analyzer"""
        if self.db_connection:
            self.db_connection.close()
        logger.info("Enhanced Trade Pattern Analyzer closed")

async def main():
    """Main function for standalone testing"""
    analyzer = EnhancedTradePatternAnalyzer()
    
    try:
        await analyzer.initialize()
        
        # Test with sample request
        sample_signal = await analyzer.analyze_request(
            url="https://api.trading.com/v1/orders",
            method="POST",
            payload='{"symbol": "BTCUSD", "side": "buy", "amount": 0.1, "price": 50000}',
            headers={"Content-Type": "application/json", "Authorization": "Bearer token"}
        )
        
        print(f"Sample analysis: {sample_signal.prediction} (confidence: {sample_signal.confidence_score:.2f})")
        
        # Get analysis report
        report = await analyzer.get_analysis_report()
        print(json.dumps(report, indent=2))
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main())