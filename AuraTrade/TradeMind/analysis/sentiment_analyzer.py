"""
Sentiment Analysis module for AuraTrade Bot
Analyzes news and social media sentiment for trading symbols
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from config.credentials import Credentials
from utils.logger import Logger

class SentimentAnalyzer:
    """Sentiment analysis for market-moving news and social media"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.credentials = Credentials()
        
        # Initialize sentiment analyzers
        self.vader_analyzer = None
        self.transformer_analyzer = None
        
        self._initialize_analyzers()
        
        # Sentiment cache
        self.sentiment_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # News sources configuration
        self.news_sources = {
            "news_api": {
                "enabled": self.credentials.has_news_api_credentials(),
                "url": "https://newsapi.org/v2/everything",
                "params": {
                    "apiKey": self.credentials.news_api_key,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 20
                }
            },
            "alpha_vantage": {
                "enabled": self.credentials.has_alpha_vantage_credentials(),
                "url": "https://www.alphavantage.co/query",
                "params": {
                    "function": "NEWS_SENTIMENT",
                    "apikey": self.credentials.alpha_vantage_key
                }
            }
        }
        
        # Symbol mappings for news search
        self.symbol_mappings = {
            "XAUUSD": ["gold", "precious metals", "inflation", "fed", "dollar"],
            "BTCUSD": ["bitcoin", "cryptocurrency", "crypto", "blockchain", "digital currency"],
            "EURUSD": ["euro", "european central bank", "ecb", "eurozone", "european union"],
            "GBPUSD": ["pound", "sterling", "bank of england", "boe", "brexit", "uk"],
            "USDJPY": ["yen", "bank of japan", "boj", "japan", "japanese"],
            "AUDUSD": ["australian dollar", "aud", "reserve bank australia", "rba"],
            "USDCAD": ["canadian dollar", "cad", "bank of canada", "boc", "oil"],
            "USDCHF": ["swiss franc", "chf", "swiss national bank", "snb", "switzerland"]
        }
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        self.logger.info(f"💭 Sentiment Analyzer initialized - VADER: {VADER_AVAILABLE}, Transformers: {TRANSFORMERS_AVAILABLE}")
    
    def _initialize_analyzers(self):
        """Initialize sentiment analysis models"""
        try:
            # Initialize VADER
            if VADER_AVAILABLE:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.logger.info("✅ VADER sentiment analyzer loaded")
            
            # Initialize transformer model (lightweight)
            if TRANSFORMERS_AVAILABLE:
                try:
                    self.transformer_analyzer = pipeline(
                        "sentiment-analysis",
                        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                        return_all_scores=True
                    )
                    self.logger.info("✅ Transformer sentiment analyzer loaded")
                except Exception as e:
                    self.logger.warning(f"Could not load transformer model: {e}")
                    TRANSFORMERS_AVAILABLE = False
            
        except Exception as e:
            self.logger.error(f"Error initializing sentiment analyzers: {e}")
    
    def get_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive sentiment analysis for a trading symbol"""
        try:
            # Check cache first
            cache_key = f"sentiment_{symbol}"
            if self._is_cache_valid(cache_key):
                return self.sentiment_cache[cache_key]["data"]
            
            # Gather sentiment from multiple sources
            news_sentiment = self._get_news_sentiment(symbol)
            social_sentiment = self._get_social_sentiment(symbol)
            market_sentiment = self._get_market_sentiment(symbol)
            
            # Combine sentiments
            combined_sentiment = self._combine_sentiments(
                news_sentiment, social_sentiment, market_sentiment
            )
            
            # Cache result
            self.sentiment_cache[cache_key] = {
                "data": combined_sentiment,
                "timestamp": time.time()
            }
            
            return combined_sentiment
            
        except Exception as e:
            self.logger.error(f"Error getting sentiment for {symbol}: {e}")
            return self._get_neutral_sentiment()
    
    def _get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment from financial news"""
        try:
            search_terms = self.symbol_mappings.get(symbol, [symbol])
            all_articles = []
            
            # Collect news from multiple sources
            for source_name, source_config in self.news_sources.items():
                if source_config["enabled"]:
                    articles = self._fetch_news_from_source(source_name, search_terms)
                    all_articles.extend(articles)
            
            if not all_articles:
                return {"score": 0.0, "magnitude": 0.0, "count": 0, "articles": []}
            
            # Analyze sentiment of articles
            sentiment_scores = []
            analyzed_articles = []
            
            for article in all_articles[-50:]:  # Limit to recent 50 articles
                article_sentiment = self._analyze_text_sentiment(
                    f"{article.get('title', '')} {article.get('description', '')}"
                )
                
                if article_sentiment:
                    sentiment_scores.append(article_sentiment["compound"])
                    analyzed_articles.append({
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "published": article.get("publishedAt", ""),
                        "sentiment": article_sentiment,
                        "url": article.get("url", "")
                    })
            
            if not sentiment_scores:
                return {"score": 0.0, "magnitude": 0.0, "count": 0, "articles": []}
            
            # Calculate aggregated sentiment
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            magnitude = sum(abs(score) for score in sentiment_scores) / len(sentiment_scores)
            
            return {
                "score": avg_sentiment,
                "magnitude": magnitude,
                "count": len(analyzed_articles),
                "articles": analyzed_articles[-10:],  # Return top 10 recent articles
                "distribution": self._calculate_sentiment_distribution(sentiment_scores)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting news sentiment: {e}")
            return {"score": 0.0, "magnitude": 0.0, "count": 0, "articles": []}
    
    def _fetch_news_from_source(self, source_name: str, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Fetch news from a specific source"""
        try:
            source_config = self.news_sources[source_name]
            articles = []
            
            if source_name == "news_api":
                articles = self._fetch_from_news_api(search_terms, source_config)
            elif source_name == "alpha_vantage":
                articles = self._fetch_from_alpha_vantage(search_terms, source_config)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from {source_name}: {e}")
            return []
    
    def _fetch_from_news_api(self, search_terms: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI"""
        try:
            articles = []
            
            for term in search_terms[:3]:  # Limit to 3 terms to avoid rate limits
                params = config["params"].copy()
                params["q"] = term
                params["from"] = (datetime.now() - timedelta(days=1)).isoformat()
                
                response = requests.get(config["url"], params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    articles.extend(data.get("articles", []))
                    time.sleep(0.5)  # Rate limiting
                else:
                    self.logger.warning(f"NewsAPI error: {response.status_code}")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from NewsAPI: {e}")
            return []
    
    def _fetch_from_alpha_vantage(self, search_terms: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch news from Alpha Vantage"""
        try:
            articles = []
            
            for term in search_terms[:2]:  # Alpha Vantage has stricter limits
                params = config["params"].copy()
                params["topics"] = term
                
                response = requests.get(config["url"], params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    feed = data.get("feed", [])
                    
                    # Convert Alpha Vantage format to standard format
                    for item in feed:
                        articles.append({
                            "title": item.get("title", ""),
                            "description": item.get("summary", ""),
                            "source": item.get("source", ""),
                            "publishedAt": item.get("time_published", ""),
                            "url": item.get("url", "")
                        })
                    
                    time.sleep(1)  # Rate limiting
                else:
                    self.logger.warning(f"Alpha Vantage error: {response.status_code}")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from Alpha Vantage: {e}")
            return []
    
    def _get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment from social media (Twitter, Reddit, etc.)"""
        try:
            # Note: This is a simplified implementation
            # In production, you would integrate with Twitter API, Reddit API, etc.
            
            # Simulated social sentiment based on recent market volatility
            # In reality, this would fetch and analyze social media posts
            
            # For now, return neutral sentiment
            # TODO: Implement actual social media sentiment analysis
            
            return {
                "score": 0.0,
                "magnitude": 0.0,
                "count": 0,
                "sources": ["twitter", "reddit", "stocktwits"],
                "volume": 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting social sentiment: {e}")
            return {"score": 0.0, "magnitude": 0.0, "count": 0}
    
    def _get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get market-based sentiment indicators"""
        try:
            # This would typically analyze:
            # - VIX levels (fear/greed)
            # - Put/Call ratios
            # - Market breadth indicators
            # - Insider trading activity
            
            # For now, return neutral market sentiment
            # TODO: Implement actual market sentiment indicators
            
            return {
                "score": 0.0,
                "magnitude": 0.0,
                "indicators": {
                    "vix_level": "normal",
                    "put_call_ratio": "neutral",
                    "breadth": "neutral"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market sentiment: {e}")
            return {"score": 0.0, "magnitude": 0.0}
    
    def _analyze_text_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment of text using available models"""
        try:
            if not text or len(text.strip()) < 5:
                return None
            
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Try VADER first (faster)
            if self.vader_analyzer:
                vader_scores = self.vader_analyzer.polarity_scores(cleaned_text)
                
                # If VADER confidence is high, use it
                if abs(vader_scores["compound"]) > 0.3:
                    return {
                        "compound": vader_scores["compound"],
                        "positive": vader_scores["pos"],
                        "negative": vader_scores["neg"],
                        "neutral": vader_scores["neu"],
                        "method": "vader"
                    }
            
            # Use transformer model for more nuanced analysis
            if self.transformer_analyzer:
                try:
                    # Limit text length for transformer
                    text_sample = cleaned_text[:512]
                    
                    results = self.transformer_analyzer(text_sample)
                    
                    # Convert to compound score
                    compound_score = 0.0
                    for result in results[0]:
                        if result["label"] == "LABEL_2":  # Positive
                            compound_score += result["score"]
                        elif result["label"] == "LABEL_0":  # Negative
                            compound_score -= result["score"]
                    
                    return {
                        "compound": compound_score,
                        "positive": max(r["score"] for r in results[0] if r["label"] == "LABEL_2"),
                        "negative": max(r["score"] for r in results[0] if r["label"] == "LABEL_0"),
                        "neutral": max(r["score"] for r in results[0] if r["label"] == "LABEL_1"),
                        "method": "transformer"
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Transformer analysis failed: {e}")
            
            # Fallback to VADER if available
            if self.vader_analyzer:
                vader_scores = self.vader_analyzer.polarity_scores(cleaned_text)
                return {
                    "compound": vader_scores["compound"],
                    "positive": vader_scores["pos"],
                    "negative": vader_scores["neg"],
                    "neutral": vader_scores["neu"],
                    "method": "vader"
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing text sentiment: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis"""
        try:
            # Remove URLs
            import re
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # Remove special characters but keep punctuation
            text = re.sub(r'[^\w\s\.\!\?\,\;]', '', text)
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text
    
    def _combine_sentiments(self, news_sentiment: Dict[str, Any], 
                          social_sentiment: Dict[str, Any], 
                          market_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Combine sentiments from multiple sources"""
        try:
            # Weights for different sources
            news_weight = 0.5
            social_weight = 0.3
            market_weight = 0.2
            
            # Calculate weighted sentiment score
            total_score = (
                news_sentiment.get("score", 0) * news_weight +
                social_sentiment.get("score", 0) * social_weight +
                market_sentiment.get("score", 0) * market_weight
            )
            
            # Calculate overall magnitude
            total_magnitude = (
                news_sentiment.get("magnitude", 0) * news_weight +
                social_sentiment.get("magnitude", 0) * social_weight +
                market_sentiment.get("magnitude", 0) * market_weight
            )
            
            # Determine overall sentiment
            if total_score > 0.1:
                overall_sentiment = "bullish"
            elif total_score < -0.1:
                overall_sentiment = "bearish"
            else:
                overall_sentiment = "neutral"
            
            # Calculate confidence based on magnitude and consistency
            confidence = min(total_magnitude * 2, 1.0)
            
            return {
                "overall_sentiment": overall_sentiment,
                "score": total_score,
                "magnitude": total_magnitude,
                "confidence": confidence,
                "components": {
                    "news": news_sentiment,
                    "social": social_sentiment,
                    "market": market_sentiment
                },
                "timestamp": datetime.now().isoformat(),
                "signal_strength": abs(total_score) * confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error combining sentiments: {e}")
            return self._get_neutral_sentiment()
    
    def _calculate_sentiment_distribution(self, scores: List[float]) -> Dict[str, float]:
        """Calculate distribution of sentiment scores"""
        try:
            if not scores:
                return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
            
            positive = len([s for s in scores if s > 0.1]) / len(scores)
            negative = len([s for s in scores if s < -0.1]) / len(scores)
            neutral = 1.0 - positive - negative
            
            return {
                "positive": positive,
                "negative": negative,
                "neutral": neutral
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating sentiment distribution: {e}")
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached sentiment is still valid"""
        try:
            if cache_key not in self.sentiment_cache:
                return False
            
            cache_age = time.time() - self.sentiment_cache[cache_key]["timestamp"]
            return cache_age < self.cache_duration
            
        except:
            return False
    
    def _get_neutral_sentiment(self) -> Dict[str, Any]:
        """Return neutral sentiment structure"""
        return {
            "overall_sentiment": "neutral",
            "score": 0.0,
            "magnitude": 0.0,
            "confidence": 0.0,
            "components": {
                "news": {"score": 0.0, "magnitude": 0.0, "count": 0},
                "social": {"score": 0.0, "magnitude": 0.0, "count": 0},
                "market": {"score": 0.0, "magnitude": 0.0}
            },
            "timestamp": datetime.now().isoformat(),
            "signal_strength": 0.0
        }
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """Get summary of sentiment analysis capabilities and status"""
        try:
            return {
                "analyzers": {
                    "vader": VADER_AVAILABLE,
                    "transformers": TRANSFORMERS_AVAILABLE
                },
                "news_sources": {
                    name: config["enabled"] 
                    for name, config in self.news_sources.items()
                },
                "cache_size": len(self.sentiment_cache),
                "supported_symbols": list(self.symbol_mappings.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sentiment summary: {e}")
            return {}
    
    def clear_cache(self):
        """Clear sentiment cache"""
        self.sentiment_cache.clear()
        self.logger.info("💭 Sentiment cache cleared")
    
    def analyze_custom_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment of custom text"""
        try:
            return self._analyze_text_sentiment(text)
        except Exception as e:
            self.logger.error(f"Error analyzing custom text: {e}")
            return None
