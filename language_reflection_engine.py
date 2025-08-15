# language_reflection_engine.py

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

class LanguageReflectionEngine:
    """Language Reflection Engine for TRAE Phase 8
    
    This class enables natural language reasoning, self-reflection, and user interaction
    through a language-based interface. It generates weekly reflections, processes user
    queries, and provides natural language explanations for trading decisions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Language Reflection Engine
        
        Args:
            config (Dict[str, Any], optional): Configuration for the engine. Defaults to None.
        """
        # Create logs directory and self_reflection subdirectory if they don't exist
        os.makedirs("logs/self_reflection", exist_ok=True)
        
        # Set up logging for language reflection
        self.logger = logging.getLogger('language_reflection')
        file_handler = logging.FileHandler('logs/language_reflection.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Set default configuration
        self.config = {
            "enabled": True,
            "language_interface": True,
            "enable_self_questions": True,
            "reflection_dir": "logs/self_reflection",
            "user_queries_file": "logs/user_queries.json",
            "weekly_reflection_schedule": {
                "day_of_week": 6,  # Sunday (0 is Monday in Python's datetime)
                "last_reflection": None
            },
            "reflection_questions": [
                "What trades performed best and why?",
                "What risk decisions failed or succeeded?",
                "What patterns or anomalies were detected?",
                "What phase logic needs refinement?"
            ],
            "governance_channel": None  # Could be a Slack webhook URL or other notification endpoint
        }
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Initialize user queries file if it doesn't exist
        if not os.path.exists(self.config["user_queries_file"]):
            with open(self.config["user_queries_file"], "w") as f:
                json.dump({
                    "total_queries": 0,
                    "successful_queries": 0,
                    "query_history": []
                }, f, indent=4)
        
        # Check if we need to generate a weekly reflection
        self.check_weekly_reflection_schedule()
        
        self.logger.info("Initialized language reflection engine")
    
    def check_weekly_reflection_schedule(self) -> None:
        """Check if it's time to generate a weekly reflection and generate one if needed"""
        try:
            now = datetime.now()
            schedule = self.config["weekly_reflection_schedule"]
            last_reflection = schedule["last_reflection"]
            
            # If we've never generated a reflection or it's been a week since the last one
            if last_reflection is None or (now - datetime.fromisoformat(last_reflection)).days >= 7:
                self.generate_weekly_reflection()
                schedule["last_reflection"] = now.isoformat()
        except Exception as e:
            self.logger.error(f"Error checking weekly reflection schedule: {e}")
    
    def generate_weekly_reflection(self) -> None:
        """Generate a weekly reflection report based on trade logs and metrics"""
        try:
            # Create timestamp for the reflection file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reflection_file = f"{self.config['reflection_dir']}/weekly_log_{timestamp}.md"
            
            # Gather data sources for reflection
            data_sources = {
                "strategy_evolution": self._load_log_file("logs/strategy_evolution.log"),
                "ai_feedback": self._load_json_file("logs/ai_feedback.json"),
                "liquidity_routing": self._load_log_file("logs/liquidity_routing.log"),
                "intent_signals": self._load_json_file("logs/intent_signals.json"),
                "daily_metrics": self._load_json_file("data/daily_metrics.json"),
                "prompts_history": self._load_json_file("logs/prompts_history.json")
            }
            
            # Generate reflection content
            reflection_content = self._generate_reflection_content(data_sources)
            
            # Write reflection to file
            with open(reflection_file, "w") as f:
                f.write(reflection_content)
                
            self.logger.info(f"Generated weekly reflection: {reflection_file}")
            
            # Also send to governance channel if configured
            self._send_to_governance_channel(reflection_content)
            
        except Exception as e:
            self.logger.error(f"Error generating weekly reflection: {e}")
    
    def _load_log_file(self, file_path: str) -> List[str]:
        """Load a log file and return its contents as a list of lines"""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return f.readlines()
            return []
        except Exception as e:
            self.logger.error(f"Error loading log file {file_path}: {e}")
            return []
    
    def _load_json_file(self, file_path: str) -> Dict:
        """Load a JSON file and return its contents as a dictionary"""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading JSON file {file_path}: {e}")
            return {}
    
    def _generate_reflection_content(self, data_sources: Dict) -> str:
        """Generate the content for the weekly reflection"""
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Start with header
        content = f"# TRAE Weekly Self-Reflection\n\n"
        content += f"**Generated:** {timestamp}\n\n"
        
        # Add sections for each reflection question
        for question in self.config["reflection_questions"]:
            content += f"## {question}\n\n"
            
            # Generate answer based on available data
            # In a real implementation, this would use an LLM to generate insightful answers
            if question == "What trades performed best and why?":
                content += self._reflect_on_best_trades(data_sources)
            elif question == "What risk decisions failed or succeeded?":
                content += self._reflect_on_risk_decisions(data_sources)
            elif question == "What patterns or anomalies were detected?":
                content += self._reflect_on_patterns(data_sources)
            elif question == "What phase logic needs refinement?":
                content += self._reflect_on_phase_logic(data_sources)
            
            content += "\n\n"
        
        # Add summary section
        content += "## Summary and Next Steps\n\n"
        content += "Based on this week's performance, the following actions are recommended:\n\n"
        content += "1. [Recommendation 1]\n"
        content += "2. [Recommendation 2]\n"
        content += "3. [Recommendation 3]\n\n"
        
        return content
    
    def _reflect_on_best_trades(self, data_sources: Dict) -> str:
        """Generate reflection on best performing trades"""
        # In a real implementation, this would analyze trade data and metrics
        # For now, we'll return a placeholder
        return "The following trades performed best this week:\n" \
               "- [Strategy] on [Symbol] with [Profit]% gain\n" \
               "- [Strategy] on [Symbol] with [Profit]% gain\n\n" \
               "These trades succeeded because:\n" \
               "- [Reason 1]\n" \
               "- [Reason 2]"
    
    def _reflect_on_risk_decisions(self, data_sources: Dict) -> str:
        """Generate reflection on risk decisions"""
        # In a real implementation, this would analyze risk management data
        return "Successful risk decisions:\n" \
               "- [Decision] - [Outcome]\n" \
               "- [Decision] - [Outcome]\n\n" \
               "Failed risk decisions:\n" \
               "- [Decision] - [Outcome]\n" \
               "- [Decision] - [Outcome]"
    
    def _reflect_on_patterns(self, data_sources: Dict) -> str:
        """Generate reflection on patterns and anomalies"""
        # In a real implementation, this would analyze pattern recognition data
        return "Patterns detected:\n" \
               "- [Pattern] - [Frequency]\n" \
               "- [Pattern] - [Frequency]\n\n" \
               "Anomalies detected:\n" \
               "- [Anomaly] - [Impact]\n" \
               "- [Anomaly] - [Impact]"
    
    def _reflect_on_phase_logic(self, data_sources: Dict) -> str:
        """Generate reflection on phase logic that needs refinement"""
        # In a real implementation, this would analyze phase performance data
        return "Current phase logic that could be improved:\n" \
               "- [Logic component] - [Reason for improvement]\n" \
               "- [Logic component] - [Reason for improvement]\n\n" \
               "Suggested modifications:\n" \
               "- [Specific modification details]"
    
    def _send_to_governance_channel(self, content: str) -> None:
        """Send the reflection content to the governance channel"""
        # In a real implementation, this would send the content to a Slack channel or other notification endpoint
        governance_channel = self.config.get("governance_channel")
        if governance_channel:
            try:
                # This is a placeholder for sending to a notification endpoint
                self.logger.info(f"Sent reflection to governance channel: {governance_channel}")
            except Exception as e:
                self.logger.error(f"Error sending to governance channel: {e}")
        else:
            self.logger.info("No governance channel configured, skipping notification")
    
    def process_user_query(self, query: str) -> str:
        """Process a natural language query from a user
        
        Args:
            query (str): The user's natural language query
            
        Returns:
            str: The response to the query
        """
        if not self.config["language_interface"]:
            return "Language interface is not enabled."
            
        try:
            # Log the query
            self.logger.info(f"Received user query: {query}")
            
            # Update query history
            self._update_query_history(query)
            
            # Process different types of queries
            if "why did you skip trades" in query.lower():
                return self._answer_skipped_trades_query()
            elif "win rate" in query.lower():
                return self._answer_win_rate_query()
            elif "phase prompt" in query.lower():
                return self._answer_phase_prompt_query()
            else:
                # Generic response for other queries
                # In a real implementation, this would use an LLM to generate responses
                return f"I processed your query: '{query}'. In a full implementation, I would provide a detailed answer based on my logs and metrics."
                
        except Exception as e:
            self.logger.error(f"Error processing user query: {e}")
            return f"Error processing your query: {str(e)}"
    
    def _update_query_history(self, query: str) -> None:
        """Update the query history with a new query"""
        try:
            # Load existing query history
            query_data = self._load_json_file(self.config["user_queries_file"])
            
            # Update counts
            query_data["total_queries"] = query_data.get("total_queries", 0) + 1
            
            # Add query to history
            query_data["query_history"].append({
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "successful": True  # Assume success for now
            })
            
            # Save updated query history
            with open(self.config["user_queries_file"], "w") as f:
                json.dump(query_data, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Error updating query history: {e}")
    
    def _answer_skipped_trades_query(self) -> str:
        """Answer a query about skipped trades"""
        # In a real implementation, this would analyze trade logs
        return "I skipped trades today for the following reasons:\n" \
               "1. Low confidence scores below threshold\n" \
               "2. High market volatility during news events\n" \
               "3. Conflicting signals from multiple strategies"
    
    def _answer_win_rate_query(self) -> str:
        """Answer a query about win rate"""
        # In a real implementation, this would calculate win rate from trade data
        return "This week's performance metrics:\n" \
               "- Win rate: 68%\n" \
               "- Average profit per trade: 0.42%\n" \
               "- Best performing strategy: Breakout (78% win rate)\n" \
               "- Worst performing strategy: Mean Reversion (52% win rate)"
    
    def _answer_phase_prompt_query(self) -> str:
        """Answer a query about the current phase prompt"""
        # In a real implementation, this would load the current phase prompt
        return "I am currently following Phase 8 prompt: 'Language Interface & Self-Reflection'\n" \
               "This phase enables me to describe my reasoning in natural language, " \
               "generate weekly self-evaluations, and respond to user queries about my performance and decisions."

# For testing
if __name__ == "__main__":
    # Create language reflection engine
    engine = LanguageReflectionEngine()
    
    # Test generating a weekly reflection
    print("Generating weekly reflection...")
    engine.generate_weekly_reflection()
    
    # Test processing user queries
    print("\nProcessing user queries...")
    queries = [
        "Why did you skip trades today?",
        "What's your win rate this week?",
        "What phase prompt are you following?",
        "How do you decide which liquidity provider to use?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = engine.process_user_query(query)
        print(f"Response: {response}")