# news_guard.py

from typing import Dict, Any, List
import logging
from datetime import datetime
import os
import re

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('news_guard')

class NewsGuard(BaseAgent):
    """Agent specialized in monitoring news events and their market impact"""
    
    def __init__(self, agent_id: str = "news_guard", config: Dict[str, Any] = None):
        """Initialize the news guard agent
        
        Args:
            agent_id (str, optional): Agent identifier. Defaults to "news_guard".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id, "guard", config)
        
        # Default news impact thresholds
        self.news_thresholds = {
            "high_impact": 0.8,  # 80% confidence for high impact
            "medium_impact": 0.5,  # 50% confidence for medium impact
            "low_impact": 0.3,  # 30% confidence for low impact
            "keywords": {
                "high": ["rate decision", "fed", "central bank", "inflation", "recession", "crisis", "war", "disaster"],
                "medium": ["gdp", "unemployment", "nfp", "pmi", "earnings", "forecast", "outlook"],
                "low": ["speech", "interview", "minor data", "technical issue"]
            }
        }
        
        # Override with config if provided
        if config and 'news_thresholds' in config:
            self.news_thresholds.update(config['news_thresholds'])
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate news impact and potentially veto trades during high-impact events
        
        Args:
            context (Dict[str, Any]): Trading context with market data and news info
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Default response - neutral with no veto
        proposal = {
            "action": "hold",
            "confidence": 50,
            "reason": "No significant news events detected",
            "veto": False,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if we have the required data
        if not context or 'news' not in context:
            return proposal
        
        news_items = context['news']
        if not news_items:
            return proposal
        
        # Analyze news impact
        highest_impact = 0
        impact_level = "none"
        relevant_news = []
        
        for news in news_items:
            news_title = news.get('title', '')
            news_content = news.get('content', '')
            news_time = news.get('timestamp', '')
            
            # Skip old news (more than 24 hours)
            if news_time and self._is_news_old(news_time):
                continue
            
            # Calculate impact score
            impact_score = self._calculate_news_impact(news_title, news_content)
            
            # Determine impact level
            current_impact = "none"
            if impact_score >= self.news_thresholds["high_impact"]:
                current_impact = "high"
            elif impact_score >= self.news_thresholds["medium_impact"]:
                current_impact = "medium"
            elif impact_score >= self.news_thresholds["low_impact"]:
                current_impact = "low"
            
            # Track highest impact news
            if impact_score > highest_impact:
                highest_impact = impact_score
                impact_level = current_impact
            
            # Collect relevant news
            if current_impact != "none":
                relevant_news.append(f"{current_impact.capitalize()} impact: {news_title}")
        
        # Determine action based on news impact
        if impact_level == "high":
            proposal["veto"] = True
            proposal["action"] = "hold"
            proposal["confidence"] = 100
            proposal["reason"] = f"High-impact news detected: {'; '.join(relevant_news)}"
        elif impact_level == "medium":
            proposal["action"] = "hold"
            proposal["confidence"] = 75
            proposal["reason"] = f"Medium-impact news detected: {'; '.join(relevant_news)}"
        elif impact_level == "low":
            proposal["action"] = "hold"
            proposal["confidence"] = 25
            proposal["reason"] = f"Low-impact news detected: {'; '.join(relevant_news)}"
        
        return proposal
    
    def _calculate_news_impact(self, title: str, content: str) -> float:
        """Calculate the impact score of a news item
        
        Args:
            title (str): News title
            content (str): News content
            
        Returns:
            float: Impact score between 0 and 1
        """
        if not title and not content:
            return 0
        
        # Combine title and content for analysis
        text = (title + " " + content).lower()
        
        # Count keyword matches
        high_matches = sum(1 for keyword in self.news_thresholds["keywords"]["high"] if keyword.lower() in text)
        medium_matches = sum(1 for keyword in self.news_thresholds["keywords"]["medium"] if keyword.lower() in text)
        low_matches = sum(1 for keyword in self.news_thresholds["keywords"]["low"] if keyword.lower() in text)
        
        # Calculate weighted score
        total_keywords = len(self.news_thresholds["keywords"]["high"]) + \
                         len(self.news_thresholds["keywords"]["medium"]) + \
                         len(self.news_thresholds["keywords"]["low"])
        
        weighted_score = (high_matches * 3 + medium_matches * 2 + low_matches) / (total_keywords * 3)
        
        # Boost score for title matches (they're more significant)
        title_lower = title.lower()
        title_boost = 0
        
        for keyword in self.news_thresholds["keywords"]["high"]:
            if keyword.lower() in title_lower:
                title_boost += 0.2
        
        for keyword in self.news_thresholds["keywords"]["medium"]:
            if keyword.lower() in title_lower:
                title_boost += 0.1
        
        # Cap the final score at 1.0
        return min(1.0, weighted_score + title_boost)
    
    def _is_news_old(self, news_time: str) -> bool:
        """Check if news is older than 24 hours
        
        Args:
            news_time (str): News timestamp
            
        Returns:
            bool: True if news is old, False otherwise
        """
        try:
            news_datetime = datetime.fromisoformat(news_time.replace('Z', '+00:00'))
            current_time = datetime.now().astimezone()
            time_diff = current_time - news_datetime
            
            # Return True if news is older than 24 hours
            return time_diff.total_seconds() > 86400
        except (ValueError, TypeError):
            # If we can't parse the timestamp, assume it's not old
            return False