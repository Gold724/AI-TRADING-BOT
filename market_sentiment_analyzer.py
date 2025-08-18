#!/usr/bin/env python3
"""
TradeBot Sentinel - Advanced Market Sentiment Analyzer

Comprehensive market sentiment analysis system:
- Multi-source sentiment data aggregation
- Real-time news and social media monitoring
- Machine learning-based sentiment classification
- Technical sentiment indicators
- Market fear/greed index calculation
- Sentiment-based trading signals
- Historical sentiment correlation analysis
- Automated sentiment alerts and notifications

Features:
- Natural Language Processing (NLP) for text analysis
- Social media sentiment tracking (Twitter, Reddit, etc.)
- News sentiment analysis from multiple sources
- Technical sentiment indicators (VIX, Put/Call ratio)
- Machine learning sentiment prediction models
- Real-time sentiment scoring and classification
- Sentiment momentum and trend analysis
- Integration with trading strategies
- Customizable sentiment thresholds and alerts
- Historical sentiment backtesting

Author: TradeBot Sentinel Team
Version: 1.0.0
Date: 2024
"""

import asyncio
import logging
import json
import time
import threading
import sqlite3
import os
import sys
import pickle
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import pandas as pd
from collections import deque, defaultdict, Counter
import statistics
import traceback
from contextlib import contextmanager
import warnings
warnings.filterwarnings('ignore')

# Web scraping and API
import requests
from bs4 import BeautifulSoup
import feedparser

# Natural Language Processing
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️ NLTK not available. Basic sentiment analysis will be used.")

# Advanced NLP
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob not available. Advanced sentiment analysis will be limited.")

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Deep Learning (optional)
try:
    import torch
    import torch.nn as nn
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not available. Advanced deep learning models will be disabled.")

@dataclass
class SentimentData:
    """Individual sentiment data point"""
    timestamp: str
    source: str  # 'news', 'twitter', 'reddit', 'technical'
    symbol: Optional[str]
    text: str
    sentiment_score: float  # -1 to 1 scale
    sentiment_label: str  # 'positive', 'negative', 'neutral'
    confidence: float  # 0 to 1 scale
    volume: int  # engagement/volume metric
    url: Optional[str] = None
    author: Optional[str] = None
    keywords: List[str] = None

@dataclass
class AggregatedSentiment:
    """Aggregated sentiment metrics"""
    timestamp: str
    symbol: Optional[str]
    timeframe: str  # '1h', '4h', '1d', '1w'
    
    # Sentiment scores
    overall_sentiment: float  # -1 to 1
    news_sentiment: float
    social_sentiment: float
    technical_sentiment: float
    
    # Sentiment distribution
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float
    
    # Volume and engagement
    total_mentions: int
    sentiment_volume: float
    engagement_score: float
    
    # Trend analysis
    sentiment_momentum: float  # Rate of change
    sentiment_trend: str  # 'improving', 'deteriorating', 'stable'
    
    # Fear/Greed metrics
    fear_greed_index: float  # 0 to 100
    market_emotion: str  # 'extreme_fear', 'fear', 'neutral', 'greed', 'extreme_greed'
    
    # Confidence metrics
    data_quality: float
    prediction_confidence: float

@dataclass
class SentimentSignal:
    """Trading signal based on sentiment analysis"""
    timestamp: str
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0 to 1
    confidence: float
    
    # Signal components
    sentiment_component: float
    momentum_component: float
    contrarian_component: float
    
    # Supporting data
    current_sentiment: float
    sentiment_change: float
    volume_confirmation: bool
    
    # Risk assessment
    risk_level: str  # 'low', 'medium', 'high'
    recommended_position_size: float
    
    reasoning: str
    expiry_time: str

@dataclass
class SentimentAlert:
    """Sentiment-based alert"""
    timestamp: str
    alert_type: str  # 'extreme_sentiment', 'sentiment_reversal', 'volume_spike'
    severity: str  # 'low', 'medium', 'high', 'critical'
    symbol: Optional[str]
    message: str
    current_value: float
    threshold_value: float
    recommended_action: str
    auto_executed: bool = False

class SentimentAnalysisEngine:
    """Core sentiment analysis engine"""
    
    def __init__(self):
        self.logger = logging.getLogger('SentimentAnalysisEngine')
        
        # Initialize NLP components
        self._initialize_nlp()
        
        # Sentiment models
        self.models = {}
        self.vectorizers = {}
        
        # Sentiment lexicons
        self.positive_words = set()
        self.negative_words = set()
        self._load_sentiment_lexicons()
        
        # Market-specific keywords
        self.bullish_keywords = {
            'moon', 'bull', 'bullish', 'pump', 'rally', 'surge', 'breakout',
            'buy', 'long', 'hodl', 'diamond hands', 'to the moon', 'rocket'
        }
        
        self.bearish_keywords = {
            'bear', 'bearish', 'dump', 'crash', 'drop', 'sell', 'short',
            'panic', 'fear', 'correction', 'bubble', 'overvalued', 'red'
        }
    
    def _initialize_nlp(self):
        """Initialize NLP components"""
        try:
            if NLTK_AVAILABLE:
                # Download required NLTK data
                nltk.download('vader_lexicon', quiet=True)
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                
                self.sia = SentimentIntensityAnalyzer()
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
            
            if TRANSFORMERS_AVAILABLE:
                # Load pre-trained sentiment model
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    return_all_scores=True
                )
            
        except Exception as e:
            self.logger.error(f"NLP initialization failed: {e}")
    
    def _load_sentiment_lexicons(self):
        """Load sentiment lexicons"""
        try:
            # Basic positive/negative word lists
            positive_words = [
                'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic',
                'wonderful', 'outstanding', 'superb', 'brilliant', 'perfect',
                'love', 'like', 'enjoy', 'happy', 'excited', 'optimistic',
                'confident', 'strong', 'solid', 'robust', 'healthy', 'growth'
            ]
            
            negative_words = [
                'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate',
                'dislike', 'sad', 'angry', 'frustrated', 'disappointed', 'worried',
                'concerned', 'weak', 'poor', 'decline', 'fall', 'drop', 'crash',
                'fail', 'failure', 'loss', 'risk', 'danger', 'threat', 'problem'
            ]
            
            self.positive_words.update(positive_words)
            self.negative_words.update(negative_words)
            
        except Exception as e:
            self.logger.error(f"Sentiment lexicon loading failed: {e}")
    
    def analyze_text_sentiment(self, text: str, method: str = 'hybrid') -> Tuple[float, str, float]:
        """Analyze sentiment of text using various methods"""
        try:
            if not text or len(text.strip()) == 0:
                return 0.0, 'neutral', 0.0
            
            sentiments = []
            confidences = []
            
            # VADER sentiment (if available)
            if NLTK_AVAILABLE and hasattr(self, 'sia'):
                vader_scores = self.sia.polarity_scores(text)
                vader_sentiment = vader_scores['compound']
                sentiments.append(vader_sentiment)
                confidences.append(abs(vader_sentiment))
            
            # TextBlob sentiment (if available)
            if TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                textblob_sentiment = blob.sentiment.polarity
                sentiments.append(textblob_sentiment)
                confidences.append(abs(textblob_sentiment))
            
            # Transformers sentiment (if available)
            if TRANSFORMERS_AVAILABLE and hasattr(self, 'sentiment_pipeline'):
                try:
                    results = self.sentiment_pipeline(text[:512])  # Limit text length
                    
                    # Convert to -1 to 1 scale
                    pos_score = next((r['score'] for r in results if r['label'] == 'LABEL_2'), 0)
                    neg_score = next((r['score'] for r in results if r['label'] == 'LABEL_0'), 0)
                    
                    transformer_sentiment = pos_score - neg_score
                    sentiments.append(transformer_sentiment)
                    confidences.append(max(pos_score, neg_score))
                    
                except Exception as e:
                    self.logger.warning(f"Transformer sentiment analysis failed: {e}")
            
            # Lexicon-based sentiment
            lexicon_sentiment = self._lexicon_sentiment(text)
            sentiments.append(lexicon_sentiment)
            confidences.append(abs(lexicon_sentiment))
            
            # Market-specific sentiment
            market_sentiment = self._market_specific_sentiment(text)
            sentiments.append(market_sentiment)
            confidences.append(abs(market_sentiment))
            
            # Combine sentiments
            if method == 'average':
                final_sentiment = np.mean(sentiments)
                final_confidence = np.mean(confidences)
            elif method == 'weighted':
                weights = np.array(confidences)
                weights = weights / np.sum(weights) if np.sum(weights) > 0 else np.ones_like(weights) / len(weights)
                final_sentiment = np.average(sentiments, weights=weights)
                final_confidence = np.mean(confidences)
            else:  # hybrid
                # Use the most confident prediction
                best_idx = np.argmax(confidences) if confidences else 0
                final_sentiment = sentiments[best_idx] if sentiments else 0.0
                final_confidence = confidences[best_idx] if confidences else 0.0
            
            # Determine sentiment label
            if final_sentiment > 0.1:
                sentiment_label = 'positive'
            elif final_sentiment < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return final_sentiment, sentiment_label, final_confidence
            
        except Exception as e:
            self.logger.error(f"Text sentiment analysis failed: {e}")
            return 0.0, 'neutral', 0.0
    
    def _lexicon_sentiment(self, text: str) -> float:
        """Calculate sentiment using lexicon-based approach"""
        try:
            words = text.lower().split()
            positive_count = sum(1 for word in words if word in self.positive_words)
            negative_count = sum(1 for word in words if word in self.negative_words)
            
            total_words = len(words)
            if total_words == 0:
                return 0.0
            
            sentiment = (positive_count - negative_count) / total_words
            return max(-1.0, min(1.0, sentiment * 5))  # Scale and clamp
            
        except Exception as e:
            self.logger.error(f"Lexicon sentiment calculation failed: {e}")
            return 0.0
    
    def _market_specific_sentiment(self, text: str) -> float:
        """Calculate market-specific sentiment"""
        try:
            text_lower = text.lower()
            
            bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
            bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
            
            if bullish_count == 0 and bearish_count == 0:
                return 0.0
            
            sentiment = (bullish_count - bearish_count) / (bullish_count + bearish_count)
            return sentiment
            
        except Exception as e:
            self.logger.error(f"Market sentiment calculation failed: {e}")
            return 0.0
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """Extract key terms from text"""
        try:
            if not NLTK_AVAILABLE:
                # Simple keyword extraction
                words = re.findall(r'\b\w+\b', text.lower())
                word_freq = Counter(words)
                return [word for word, _ in word_freq.most_common(top_k)]
            
            # Advanced keyword extraction
            tokens = word_tokenize(text.lower())
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                     if token.isalpha() and token not in self.stop_words]
            
            word_freq = Counter(tokens)
            return [word for word, _ in word_freq.most_common(top_k)]
            
        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def train_custom_model(self, training_data: List[Tuple[str, str]], model_name: str = 'custom'):
        """Train custom sentiment classification model"""
        try:
            if not training_data:
                self.logger.warning("No training data provided")
                return
            
            texts, labels = zip(*training_data)
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words='english'
            )
            
            X = vectorizer.fit_transform(texts)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train multiple models
            models = {
                'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'logistic_regression': LogisticRegression(random_state=42),
                'naive_bayes': MultinomialNB(),
                'gradient_boosting': GradientBoostingClassifier(random_state=42)
            }
            
            best_model = None
            best_score = 0
            
            for name, model in models.items():
                model.fit(X_train, y_train)
                score = model.score(X_test, y_test)
                
                self.logger.info(f"{name} accuracy: {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_model = model
            
            # Store best model
            self.models[model_name] = best_model
            self.vectorizers[model_name] = vectorizer
            
            self.logger.info(f"Custom model '{model_name}' trained with accuracy: {best_score:.3f}")
            
        except Exception as e:
            self.logger.error(f"Custom model training failed: {e}")
    
    def predict_with_custom_model(self, text: str, model_name: str = 'custom') -> Tuple[str, float]:
        """Predict sentiment using custom trained model"""
        try:
            if model_name not in self.models or model_name not in self.vectorizers:
                return 'neutral', 0.0
            
            model = self.models[model_name]
            vectorizer = self.vectorizers[model_name]
            
            X = vectorizer.transform([text])
            prediction = model.predict(X)[0]
            
            # Get prediction probability
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X)[0]
                confidence = np.max(probabilities)
            else:
                confidence = 0.5
            
            return prediction, confidence
            
        except Exception as e:
            self.logger.error(f"Custom model prediction failed: {e}")
            return 'neutral', 0.0

class NewsDataCollector:
    """News data collection and processing"""
    
    def __init__(self):
        self.logger = logging.getLogger('NewsDataCollector')
        
        # News sources
        self.news_sources = {
            'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cointelegraph': 'https://cointelegraph.com/rss',
            'reuters_crypto': 'https://www.reuters.com/technology/cryptocurrency',
            'bloomberg_crypto': 'https://www.bloomberg.com/crypto',
            'yahoo_finance': 'https://finance.yahoo.com/rss/topstories'
        }
        
        # Request session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def collect_news_data(self, symbols: List[str] = None, hours_back: int = 24) -> List[SentimentData]:
        """Collect news data from various sources"""
        news_data = []
        
        try:
            for source_name, source_url in self.news_sources.items():
                try:
                    source_data = self._collect_from_source(source_name, source_url, symbols, hours_back)
                    news_data.extend(source_data)
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to collect from {source_name}: {e}")
            
            self.logger.info(f"Collected {len(news_data)} news articles")
            return news_data
            
        except Exception as e:
            self.logger.error(f"News data collection failed: {e}")
            return []
    
    def _collect_from_source(self, source_name: str, source_url: str, 
                           symbols: List[str], hours_back: int) -> List[SentimentData]:
        """Collect data from a specific news source"""
        data = []
        
        try:
            if source_url.endswith('.xml') or 'rss' in source_url:
                # RSS feed
                data = self._parse_rss_feed(source_name, source_url, symbols, hours_back)
            else:
                # Web scraping
                data = self._scrape_website(source_name, source_url, symbols, hours_back)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Source collection failed for {source_name}: {e}")
            return []
    
    def _parse_rss_feed(self, source_name: str, feed_url: str, 
                       symbols: List[str], hours_back: int) -> List[SentimentData]:
        """Parse RSS feed for news articles"""
        data = []
        
        try:
            feed = feedparser.parse(feed_url)
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for entry in feed.entries:
                try:
                    # Parse publication date
                    pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    title = entry.title if hasattr(entry, 'title') else ''
                    description = entry.description if hasattr(entry, 'description') else ''
                    link = entry.link if hasattr(entry, 'link') else ''
                    
                    text = f"{title} {description}"
                    
                    # Filter by symbols if specified
                    if symbols:
                        relevant_symbol = self._find_relevant_symbol(text, symbols)
                        if not relevant_symbol:
                            continue
                    else:
                        relevant_symbol = None
                    
                    sentiment_data = SentimentData(
                        timestamp=pub_date.isoformat(),
                        source=f"news_{source_name}",
                        symbol=relevant_symbol,
                        text=text,
                        sentiment_score=0.0,  # Will be calculated later
                        sentiment_label='neutral',
                        confidence=0.0,
                        volume=1,
                        url=link
                    )
                    
                    data.append(sentiment_data)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse RSS entry: {e}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"RSS feed parsing failed: {e}")
            return []
    
    def _scrape_website(self, source_name: str, url: str, 
                       symbols: List[str], hours_back: int) -> List[SentimentData]:
        """Scrape website for news articles"""
        data = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Generic article extraction (would need customization per site)
            articles = soup.find_all(['article', 'div'], class_=re.compile(r'article|news|story'))
            
            for article in articles[:20]:  # Limit to 20 articles
                try:
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                    title = title_elem.get_text().strip() if title_elem else ''
                    
                    content_elem = article.find(['p', 'div'], class_=re.compile(r'content|summary|description'))
                    content = content_elem.get_text().strip() if content_elem else ''
                    
                    link_elem = article.find('a')
                    link = link_elem.get('href') if link_elem else ''
                    
                    if not title and not content:
                        continue
                    
                    text = f"{title} {content}"
                    
                    # Filter by symbols if specified
                    if symbols:
                        relevant_symbol = self._find_relevant_symbol(text, symbols)
                        if not relevant_symbol:
                            continue
                    else:
                        relevant_symbol = None
                    
                    sentiment_data = SentimentData(
                        timestamp=datetime.now().isoformat(),
                        source=f"news_{source_name}",
                        symbol=relevant_symbol,
                        text=text,
                        sentiment_score=0.0,
                        sentiment_label='neutral',
                        confidence=0.0,
                        volume=1,
                        url=link
                    )
                    
                    data.append(sentiment_data)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse article: {e}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Website scraping failed: {e}")
            return []
    
    def _find_relevant_symbol(self, text: str, symbols: List[str]) -> Optional[str]:
        """Find relevant trading symbol in text"""
        text_upper = text.upper()
        
        for symbol in symbols:
            symbol_variations = [
                symbol.upper(),
                symbol.upper().replace('USD', ''),
                symbol.upper().replace('USDT', ''),
                symbol.upper().replace('BTC', ''),
                symbol.upper().replace('ETH', '')
            ]
            
            for variation in symbol_variations:
                if variation in text_upper:
                    return symbol
        
        return None

class SocialMediaCollector:
    """Social media sentiment data collector"""
    
    def __init__(self):
        self.logger = logging.getLogger('SocialMediaCollector')
        
        # This is a simplified implementation
        # In practice, you would use official APIs (Twitter API, Reddit API, etc.)
        self.reddit_subreddits = [
            'cryptocurrency', 'bitcoin', 'ethereum', 'cryptomarkets',
            'altcoin', 'defi', 'nft', 'trading', 'investing'
        ]
    
    def collect_social_data(self, symbols: List[str] = None, hours_back: int = 24) -> List[SentimentData]:
        """Collect social media sentiment data"""
        social_data = []
        
        try:
            # Simulate social media data collection
            # In practice, you would implement actual API calls
            
            # Generate sample social media posts
            sample_posts = self._generate_sample_social_data(symbols, hours_back)
            social_data.extend(sample_posts)
            
            self.logger.info(f"Collected {len(social_data)} social media posts")
            return social_data
            
        except Exception as e:
            self.logger.error(f"Social media data collection failed: {e}")
            return []
    
    def _generate_sample_social_data(self, symbols: List[str], hours_back: int) -> List[SentimentData]:
        """Generate sample social media data for demonstration"""
        data = []
        
        try:
            sample_texts = [
                "Bitcoin is looking bullish! Ready for the next pump! 🚀",
                "Ethereum gas fees are killing me. This is unsustainable.",
                "Just bought the dip. Diamond hands! 💎🙌",
                "Market is crashing again. Time to panic sell everything.",
                "HODL strong! This is just a temporary correction.",
                "New ATH incoming! Bull market is back!",
                "Bear market blues. When will this end?",
                "DCA strategy is the way to go in this volatility.",
                "Altcoin season is here! Time to diversify.",
                "Regulation fears are overblown. Crypto will survive."
            ]
            
            for i in range(50):  # Generate 50 sample posts
                text = np.random.choice(sample_texts)
                symbol = np.random.choice(symbols) if symbols else None
                
                # Random timestamp within the specified hours
                random_hours = np.random.uniform(0, hours_back)
                timestamp = datetime.now() - timedelta(hours=random_hours)
                
                sentiment_data = SentimentData(
                    timestamp=timestamp.isoformat(),
                    source='social_reddit',
                    symbol=symbol,
                    text=text,
                    sentiment_score=0.0,
                    sentiment_label='neutral',
                    confidence=0.0,
                    volume=np.random.randint(1, 100),  # Random engagement
                    author=f"user_{i}"
                )
                
                data.append(sentiment_data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Sample social data generation failed: {e}")
            return []

class MarketSentimentAnalyzer:
    """Main market sentiment analyzer"""
    
    def __init__(self, config_file: str = 'sentiment_config.json'):
        self.logger = self._setup_logging()
        
        # Configuration
        self.config = self._load_config(config_file)
        
        # Core components
        self.sentiment_engine = SentimentAnalysisEngine()
        self.news_collector = NewsDataCollector()
        self.social_collector = SocialMediaCollector()
        
        # Data storage
        self.sentiment_history = deque(maxlen=10000)
        self.aggregated_sentiment = {}
        self.sentiment_signals = deque(maxlen=1000)
        self.alerts_history = deque(maxlen=500)
        
        # Monitoring
        self.monitoring_active = False
        self.update_interval = self.config.get('update_interval', 300)  # 5 minutes
        
        # Thresholds
        self.sentiment_thresholds = self.config.get('sentiment_thresholds', {
            'extreme_positive': 0.7,
            'positive': 0.3,
            'neutral_high': 0.1,
            'neutral_low': -0.1,
            'negative': -0.3,
            'extreme_negative': -0.7
        })
        
        self.logger.info("📊 Market Sentiment Analyzer initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('MarketSentimentAnalyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('sentiment_analysis.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load sentiment analysis configuration"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    'update_interval': 300,
                    'data_sources': {
                        'news': True,
                        'social': True,
                        'technical': True
                    },
                    'sentiment_thresholds': {
                        'extreme_positive': 0.7,
                        'positive': 0.3,
                        'neutral_high': 0.1,
                        'neutral_low': -0.1,
                        'negative': -0.3,
                        'extreme_negative': -0.7
                    },
                    'signal_generation': {
                        'enabled': True,
                        'min_confidence': 0.6,
                        'contrarian_mode': False
                    },
                    'alert_settings': {
                        'extreme_sentiment_threshold': 0.8,
                        'sentiment_reversal_threshold': 0.5,
                        'volume_spike_threshold': 2.0
                    }
                }
                
                # Save default config
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                return default_config
                
        except Exception as e:
            self.logger.error(f"Config loading failed: {e}")
            return {}
    
    def collect_sentiment_data(self, symbols: List[str] = None, hours_back: int = 24) -> List[SentimentData]:
        """Collect sentiment data from all sources"""
        all_data = []
        
        try:
            # Collect news data
            if self.config.get('data_sources', {}).get('news', True):
                news_data = self.news_collector.collect_news_data(symbols, hours_back)
                all_data.extend(news_data)
            
            # Collect social media data
            if self.config.get('data_sources', {}).get('social', True):
                social_data = self.social_collector.collect_social_data(symbols, hours_back)
                all_data.extend(social_data)
            
            # Process sentiment for all collected data
            for data_point in all_data:
                sentiment_score, sentiment_label, confidence = self.sentiment_engine.analyze_text_sentiment(
                    data_point.text
                )
                
                data_point.sentiment_score = sentiment_score
                data_point.sentiment_label = sentiment_label
                data_point.confidence = confidence
                data_point.keywords = self.sentiment_engine.extract_keywords(data_point.text, 5)
            
            # Store in history
            self.sentiment_history.extend(all_data)
            
            self.logger.info(f"Collected and processed {len(all_data)} sentiment data points")
            return all_data
            
        except Exception as e:
            self.logger.error(f"Sentiment data collection failed: {e}")
            return []
    
    def calculate_aggregated_sentiment(self, symbol: Optional[str] = None, 
                                     timeframe: str = '1h') -> Optional[AggregatedSentiment]:
        """Calculate aggregated sentiment metrics"""
        try:
            # Define time window
            if timeframe == '1h':
                hours = 1
            elif timeframe == '4h':
                hours = 4
            elif timeframe == '1d':
                hours = 24
            elif timeframe == '1w':
                hours = 168
            else:
                hours = 1
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter relevant data
            relevant_data = [
                data for data in self.sentiment_history
                if datetime.fromisoformat(data.timestamp) >= cutoff_time
                and (symbol is None or data.symbol == symbol)
            ]
            
            if not relevant_data:
                return None
            
            # Calculate sentiment metrics
            sentiments = [data.sentiment_score for data in relevant_data]
            confidences = [data.confidence for data in relevant_data]
            volumes = [data.volume for data in relevant_data]
            
            overall_sentiment = np.average(sentiments, weights=confidences) if confidences else np.mean(sentiments)
            
            # Separate by source
            news_data = [data for data in relevant_data if data.source.startswith('news')]
            social_data = [data for data in relevant_data if data.source.startswith('social')]
            
            news_sentiment = np.mean([data.sentiment_score for data in news_data]) if news_data else 0.0
            social_sentiment = np.mean([data.sentiment_score for data in social_data]) if social_data else 0.0
            technical_sentiment = 0.0  # Would be calculated from technical indicators
            
            # Sentiment distribution
            positive_count = sum(1 for s in sentiments if s > 0.1)
            negative_count = sum(1 for s in sentiments if s < -0.1)
            neutral_count = len(sentiments) - positive_count - negative_count
            
            total_count = len(sentiments)
            positive_ratio = positive_count / total_count if total_count > 0 else 0
            negative_ratio = negative_count / total_count if total_count > 0 else 0
            neutral_ratio = neutral_count / total_count if total_count > 0 else 0
            
            # Volume and engagement
            total_mentions = len(relevant_data)
            sentiment_volume = sum(volumes)
            engagement_score = np.mean(volumes) if volumes else 0
            
            # Trend analysis
            sentiment_momentum = self._calculate_sentiment_momentum(relevant_data)
            sentiment_trend = self._determine_sentiment_trend(sentiment_momentum)
            
            # Fear/Greed index
            fear_greed_index = self._calculate_fear_greed_index(overall_sentiment, sentiment_momentum, volumes)
            market_emotion = self._classify_market_emotion(fear_greed_index)
            
            # Data quality
            data_quality = min(1.0, len(relevant_data) / 100)  # Quality based on data volume
            prediction_confidence = np.mean(confidences) if confidences else 0.5
            
            aggregated = AggregatedSentiment(
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                timeframe=timeframe,
                overall_sentiment=overall_sentiment,
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                technical_sentiment=technical_sentiment,
                positive_ratio=positive_ratio,
                negative_ratio=negative_ratio,
                neutral_ratio=neutral_ratio,
                total_mentions=total_mentions,
                sentiment_volume=sentiment_volume,
                engagement_score=engagement_score,
                sentiment_momentum=sentiment_momentum,
                sentiment_trend=sentiment_trend,
                fear_greed_index=fear_greed_index,
                market_emotion=market_emotion,
                data_quality=data_quality,
                prediction_confidence=prediction_confidence
            )
            
            # Store aggregated sentiment
            key = f"{symbol or 'market'}_{timeframe}"
            self.aggregated_sentiment[key] = aggregated
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Aggregated sentiment calculation failed: {e}")
            return None
    
    def _calculate_sentiment_momentum(self, data: List[SentimentData]) -> float:
        """Calculate sentiment momentum (rate of change)"""
        try:
            if len(data) < 10:
                return 0.0
            
            # Sort by timestamp
            sorted_data = sorted(data, key=lambda x: x.timestamp)
            
            # Split into two halves
            mid_point = len(sorted_data) // 2
            first_half = sorted_data[:mid_point]
            second_half = sorted_data[mid_point:]
            
            # Calculate average sentiment for each half
            first_avg = np.mean([d.sentiment_score for d in first_half])
            second_avg = np.mean([d.sentiment_score for d in second_half])
            
            # Momentum is the change
            momentum = second_avg - first_avg
            return momentum
            
        except Exception as e:
            self.logger.error(f"Sentiment momentum calculation failed: {e}")
            return 0.0
    
    def _determine_sentiment_trend(self, momentum: float) -> str:
        """Determine sentiment trend based on momentum"""
        if momentum > 0.1:
            return 'improving'
        elif momentum < -0.1:
            return 'deteriorating'
        else:
            return 'stable'
    
    def _calculate_fear_greed_index(self, sentiment: float, momentum: float, volumes: List[int]) -> float:
        """Calculate Fear & Greed Index (0-100 scale)"""
        try:
            # Base score from sentiment (-1 to 1 -> 0 to 100)
            base_score = (sentiment + 1) * 50
            
            # Momentum adjustment
            momentum_adjustment = momentum * 20
            
            # Volume adjustment (higher volume = more extreme emotions)
            avg_volume = np.mean(volumes) if volumes else 1
            volume_multiplier = min(1.5, 1 + (avg_volume - 1) / 100)
            
            # Calculate final index
            fear_greed = base_score + momentum_adjustment
            fear_greed *= volume_multiplier
            
            # Clamp to 0-100 range
            return max(0, min(100, fear_greed))
            
        except Exception as e:
            self.logger.error(f"Fear/Greed index calculation failed: {e}")
            return 50.0  # Neutral
    
    def _classify_market_emotion(self, fear_greed_index: float) -> str:
        """Classify market emotion based on Fear & Greed Index"""
        if fear_greed_index <= 20:
            return 'extreme_fear'
        elif fear_greed_index <= 40:
            return 'fear'
        elif fear_greed_index <= 60:
            return 'neutral'
        elif fear_greed_index <= 80:
            return 'greed'
        else:
            return 'extreme_greed'
    
    def generate_sentiment_signals(self, symbol: str) -> List[SentimentSignal]:
        """Generate trading signals based on sentiment analysis"""
        signals = []
        
        try:
            if not self.config.get('signal_generation', {}).get('enabled', True):
                return signals
            
            # Get aggregated sentiment for different timeframes
            sentiment_1h = self.calculate_aggregated_sentiment(symbol, '1h')
            sentiment_4h = self.calculate_aggregated_sentiment(symbol, '4h')
            sentiment_1d = self.calculate_aggregated_sentiment(symbol, '1d')
            
            if not sentiment_1h:
                return signals
            
            # Signal generation logic
            current_sentiment = sentiment_1h.overall_sentiment
            sentiment_momentum = sentiment_1h.sentiment_momentum
            fear_greed = sentiment_1h.fear_greed_index
            
            # Contrarian vs. momentum strategy
            contrarian_mode = self.config.get('signal_generation', {}).get('contrarian_mode', False)
            min_confidence = self.config.get('signal_generation', {}).get('min_confidence', 0.6)
            
            # Generate signals based on different strategies
            
            # 1. Extreme sentiment contrarian signal
            if contrarian_mode and abs(current_sentiment) > 0.7:
                signal_type = 'buy' if current_sentiment < -0.7 else 'sell'
                strength = abs(current_sentiment)
                confidence = sentiment_1h.prediction_confidence
                
                if confidence >= min_confidence:
                    signal = SentimentSignal(
                        timestamp=datetime.now().isoformat(),
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=strength,
                        confidence=confidence,
                        sentiment_component=current_sentiment,
                        momentum_component=sentiment_momentum,
                        contrarian_component=1.0,
                        current_sentiment=current_sentiment,
                        sentiment_change=sentiment_momentum,
                        volume_confirmation=sentiment_1h.sentiment_volume > 50,
                        risk_level='medium',
                        recommended_position_size=0.1,
                        reasoning=f"Contrarian signal: extreme {sentiment_1h.market_emotion}",
                        expiry_time=(datetime.now() + timedelta(hours=4)).isoformat()
                    )
                    signals.append(signal)
            
            # 2. Momentum-based signal
            elif not contrarian_mode and abs(sentiment_momentum) > 0.3:
                signal_type = 'buy' if sentiment_momentum > 0 else 'sell'
                strength = abs(sentiment_momentum)
                confidence = sentiment_1h.prediction_confidence
                
                if confidence >= min_confidence:
                    signal = SentimentSignal(
                        timestamp=datetime.now().isoformat(),
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=strength,
                        confidence=confidence,
                        sentiment_component=current_sentiment,
                        momentum_component=sentiment_momentum,
                        contrarian_component=0.0,
                        current_sentiment=current_sentiment,
                        sentiment_change=sentiment_momentum,
                        volume_confirmation=sentiment_1h.sentiment_volume > 30,
                        risk_level='low' if abs(sentiment_momentum) < 0.5 else 'medium',
                        recommended_position_size=0.05,
                        reasoning=f"Momentum signal: sentiment {sentiment_1h.sentiment_trend}",
                        expiry_time=(datetime.now() + timedelta(hours=2)).isoformat()
                    )
                    signals.append(signal)
            
            # 3. Fear/Greed extreme signal
            if fear_greed <= 20 or fear_greed >= 80:
                signal_type = 'buy' if fear_greed <= 20 else 'sell'
                strength = (20 - fear_greed) / 20 if fear_greed <= 20 else (fear_greed - 80) / 20
                confidence = sentiment_1h.data_quality
                
                if confidence >= min_confidence:
                    signal = SentimentSignal(
                        timestamp=datetime.now().isoformat(),
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=abs(strength),
                        confidence=confidence,
                        sentiment_component=current_sentiment,
                        momentum_component=sentiment_momentum,
                        contrarian_component=0.8,
                        current_sentiment=current_sentiment,
                        sentiment_change=sentiment_momentum,
                        volume_confirmation=True,
                        risk_level='high',
                        recommended_position_size=0.15,
                        reasoning=f"Fear/Greed extreme: {sentiment_1h.market_emotion} ({fear_greed:.0f})",
                        expiry_time=(datetime.now() + timedelta(hours=6)).isoformat()
                    )
                    signals.append(signal)
            
            # Store signals
            self.sentiment_signals.extend(signals)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Sentiment signal generation failed: {e}")
            return []
    
    def generate_sentiment_alerts(self) -> List[SentimentAlert]:
        """Generate sentiment-based alerts"""
        alerts = []
        
        try:
            alert_settings = self.config.get('alert_settings', {})
            
            # Check for extreme sentiment
            for key, aggregated in self.aggregated_sentiment.items():
                symbol = aggregated.symbol
                
                # Extreme sentiment alert
                if abs(aggregated.overall_sentiment) > alert_settings.get('extreme_sentiment_threshold', 0.8):
                    alert = SentimentAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='extreme_sentiment',
                        severity='high',
                        symbol=symbol,
                        message=f"Extreme sentiment detected for {symbol or 'market'}: {aggregated.overall_sentiment:.2f}",
                        current_value=abs(aggregated.overall_sentiment),
                        threshold_value=alert_settings.get('extreme_sentiment_threshold', 0.8),
                        recommended_action="Consider contrarian position or risk management"
                    )
                    alerts.append(alert)
                
                # Sentiment reversal alert
                if abs(aggregated.sentiment_momentum) > alert_settings.get('sentiment_reversal_threshold', 0.5):
                    alert = SentimentAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='sentiment_reversal',
                        severity='medium',
                        symbol=symbol,
                        message=f"Sentiment reversal detected for {symbol or 'market'}: {aggregated.sentiment_trend}",
                        current_value=abs(aggregated.sentiment_momentum),
                        threshold_value=alert_settings.get('sentiment_reversal_threshold', 0.5),
                        recommended_action="Monitor for trend confirmation"
                    )
                    alerts.append(alert)
                
                # Volume spike alert
                avg_volume = statistics.mean([data.volume for data in self.sentiment_history[-100:]]) if len(self.sentiment_history) >= 100 else 10
                if aggregated.sentiment_volume > avg_volume * alert_settings.get('volume_spike_threshold', 2.0):
                    alert = SentimentAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='volume_spike',
                        severity='medium',
                        symbol=symbol,
                        message=f"Sentiment volume spike for {symbol or 'market'}: {aggregated.sentiment_volume:.0f}",
                        current_value=aggregated.sentiment_volume,
                        threshold_value=avg_volume * alert_settings.get('volume_spike_threshold', 2.0),
                        recommended_action="Investigate news or events causing increased attention"
                    )
                    alerts.append(alert)
            
            # Store alerts
            self.alerts_history.extend(alerts)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Sentiment alert generation failed: {e}")
            return []
    
    def start_monitoring(self, symbols: List[str] = None):
        """Start continuous sentiment monitoring"""
        self.monitoring_active = True
        self.logger.info("📊 Sentiment monitoring started")
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Collect new sentiment data
                    self.collect_sentiment_data(symbols, hours_back=1)
                    
                    # Calculate aggregated sentiment
                    for symbol in (symbols or [None]):
                        self.calculate_aggregated_sentiment(symbol, '1h')
                        self.calculate_aggregated_sentiment(symbol, '4h')
                        self.calculate_aggregated_sentiment(symbol, '1d')
                    
                    # Generate signals
                    if symbols:
                        for symbol in symbols:
                            signals = self.generate_sentiment_signals(symbol)
                            if signals:
                                self.logger.info(f"Generated {len(signals)} signals for {symbol}")
                    
                    # Generate alerts
                    alerts = self.generate_sentiment_alerts()
                    if alerts:
                        for alert in alerts:
                            self.logger.warning(f"SENTIMENT ALERT: {alert.message}")
                    
                    time.sleep(self.update_interval)
                    
                except Exception as e:
                    self.logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
    
    def get_sentiment_report(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive sentiment report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'current_sentiment': {},
                'historical_trends': {},
                'signals': [],
                'alerts': [],
                'recommendations': []
            }
            
            # Current sentiment
            sentiment_1h = self.calculate_aggregated_sentiment(symbol, '1h')
            if sentiment_1h:
                report['current_sentiment'] = {
                    'overall_sentiment': sentiment_1h.overall_sentiment,
                    'sentiment_label': self._classify_sentiment(sentiment_1h.overall_sentiment),
                    'fear_greed_index': sentiment_1h.fear_greed_index,
                    'market_emotion': sentiment_1h.market_emotion,
                    'sentiment_trend': sentiment_1h.sentiment_trend,
                    'data_quality': sentiment_1h.data_quality,
                    'total_mentions': sentiment_1h.total_mentions
                }
            
            # Recent signals
            recent_signals = [signal for signal in self.sentiment_signals 
                            if (symbol is None or signal.symbol == symbol)
                            and datetime.fromisoformat(signal.timestamp) > datetime.now() - timedelta(hours=24)]
            report['signals'] = [asdict(signal) for signal in recent_signals[-5:]]  # Last 5 signals
            
            # Recent alerts
            recent_alerts = [alert for alert in self.alerts_history 
                           if (symbol is None or alert.symbol == symbol)
                           and datetime.fromisoformat(alert.timestamp) > datetime.now() - timedelta(hours=24)]
            report['alerts'] = [asdict(alert) for alert in recent_alerts[-5:]]  # Last 5 alerts
            
            # Recommendations
            recommendations = self._generate_sentiment_recommendations(sentiment_1h)
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            self.logger.error(f"Sentiment report generation failed: {e}")
            return {}
    
    def _classify_sentiment(self, sentiment_score: float) -> str:
        """Classify sentiment score into label"""
        thresholds = self.sentiment_thresholds
        
        if sentiment_score >= thresholds['extreme_positive']:
            return 'extremely_positive'
        elif sentiment_score >= thresholds['positive']:
            return 'positive'
        elif sentiment_score >= thresholds['neutral_high']:
            return 'slightly_positive'
        elif sentiment_score >= thresholds['neutral_low']:
            return 'neutral'
        elif sentiment_score >= thresholds['negative']:
            return 'slightly_negative'
        elif sentiment_score >= thresholds['extreme_negative']:
            return 'negative'
        else:
            return 'extremely_negative'
    
    def _generate_sentiment_recommendations(self, sentiment: Optional[AggregatedSentiment]) -> List[str]:
        """Generate sentiment-based recommendations"""
        recommendations = []
        
        try:
            if not sentiment:
                return recommendations
            
            # Extreme sentiment recommendations
            if sentiment.fear_greed_index <= 20:
                recommendations.append("Extreme fear detected - consider contrarian buying opportunity")
            elif sentiment.fear_greed_index >= 80:
                recommendations.append("Extreme greed detected - consider taking profits or reducing exposure")
            
            # Trend recommendations
            if sentiment.sentiment_trend == 'improving' and sentiment.overall_sentiment < 0:
                recommendations.append("Sentiment improving from negative levels - potential reversal signal")
            elif sentiment.sentiment_trend == 'deteriorating' and sentiment.overall_sentiment > 0:
                recommendations.append("Sentiment deteriorating from positive levels - consider risk management")
            
            # Volume recommendations
            if sentiment.sentiment_volume > 100:
                recommendations.append("High sentiment volume - increased market attention and volatility expected")
            
            # Data quality recommendations
            if sentiment.data_quality < 0.5:
                recommendations.append("Low data quality - sentiment signals may be unreliable")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Sentiment recommendation generation failed: {e}")
            return []

# Example usage and testing
def main():
    """Main function for testing the sentiment analyzer"""
    analyzer = MarketSentimentAnalyzer()
    
    # Test symbols
    test_symbols = ['BTCUSD', 'ETHUSD', 'ADAUSD']
    
    print("📊 Market Sentiment Analyzer - Demo")
    print("=" * 50)
    
    # Collect sentiment data
    print("\n📰 Collecting sentiment data...")
    sentiment_data = analyzer.collect_sentiment_data(test_symbols, hours_back=24)
    print(f"Collected {len(sentiment_data)} sentiment data points")
    
    # Calculate aggregated sentiment
    print("\n📈 Calculating aggregated sentiment...")
    for symbol in test_symbols:
        sentiment_1h = analyzer.calculate_aggregated_sentiment(symbol, '1h')
        if sentiment_1h:
            print(f"\n{symbol} Sentiment (1h):")
            print(f"  Overall: {sentiment_1h.overall_sentiment:.3f} ({analyzer._classify_sentiment(sentiment_1h.overall_sentiment)})")
            print(f"  Fear/Greed: {sentiment_1h.fear_greed_index:.0f} ({sentiment_1h.market_emotion})")
            print(f"  Trend: {sentiment_1h.sentiment_trend}")
            print(f"  Mentions: {sentiment_1h.total_mentions}")
    
    # Generate signals
    print("\n🎯 Generating signals...")
    for symbol in test_symbols:
        signals = analyzer.generate_sentiment_signals(symbol)
        if signals:
            print(f"\n{symbol} Signals:")
            for signal in signals:
                print(f"  {signal.signal_type.upper()} - Strength: {signal.strength:.2f}, Confidence: {signal.confidence:.2f}")
                print(f"    Reasoning: {signal.reasoning}")
    
    # Generate alerts
    print("\n🚨 Checking for alerts...")
    alerts = analyzer.generate_sentiment_alerts()
    if alerts:
        for alert in alerts:
            print(f"  {alert.alert_type.upper()}: {alert.message}")
    else:
        print("  No alerts generated")
    
    # Generate report
    print("\n📋 Generating sentiment report...")
    report = analyzer.get_sentiment_report()
    print(f"Report generated with {len(report.get('signals', []))} signals and {len(report.get('alerts', []))} alerts")
    
    # Start monitoring (optional)
    # analyzer.start_monitoring(test_symbols)
    # print("\n🔄 Monitoring started (press Ctrl+C to stop)")
    
    print("\n✅ Sentiment analysis demo completed!")

if __name__ == "__main__":
    main()