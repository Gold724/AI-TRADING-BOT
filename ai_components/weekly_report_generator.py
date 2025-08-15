#!/usr/bin/env python
# Weekly Report Generator - Generates performance reports and sends via Slack/Email

import json
import logging
import os
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, List, Optional

# Import local modules
try:
    from ai_components.sentinel_decider_llm import SentinelDeciderLLM
    from ai_components.dynamic_risk_engine import DynamicRiskEngine
    from ai_components.strategy_evolution import StrategyEvolution
except ImportError:
    # For local testing
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ai_components.sentinel_decider_llm import SentinelDeciderLLM
    from ai_components.dynamic_risk_engine import DynamicRiskEngine
    from ai_components.strategy_evolution import StrategyEvolution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("weekly_report_generator")

# Constants
CONFIG_FILE = os.path.join("config", "report_config.json")
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
NEWS_HISTORY_FILE = os.path.join("data", "news_history.json")

class WeeklyReportGenerator:
    """Generates weekly performance reports and distributes them via Slack and Email"""
    
    def __init__(self, 
                 config_file: str = CONFIG_FILE,
                 trade_history_file: str = TRADE_HISTORY_FILE,
                 news_history_file: str = NEWS_HISTORY_FILE):
        """Initialize the weekly report generator
        
        Args:
            config_file (str): Path to the report configuration file
            trade_history_file (str): Path to the trade history file
            news_history_file (str): Path to the news history file
        """
        self.config_file = config_file
        self.trade_history_file = trade_history_file
        self.news_history_file = news_history_file
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        os.makedirs(os.path.dirname(trade_history_file), exist_ok=True)
        os.makedirs(os.path.dirname(news_history_file), exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize components
        self.sentinel = SentinelDeciderLLM()
        self.risk_engine = DynamicRiskEngine()
        self.strategy_evolution = StrategyEvolution()
        
        logger.info("Weekly Report Generator initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load the report configuration
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    "report": {
                        "enabled": True,
                        "frequency": "weekly",  # weekly, daily, monthly
                        "day_of_week": 1,       # 0=Monday, 6=Sunday
                        "hour": 8,              # Hour of the day (24-hour format)
                        "include_sections": [
                            "performance_summary",
                            "strategy_evolution",
                            "risk_adjustments",
                            "news_impact",
                            "recommendations"
                        ]
                    },
                    "slack": {
                        "enabled": True,
                        "webhook_url": "",
                        "channel": "#trading-reports",
                        "username": "TRAE-Bot",
                        "icon_emoji": ":chart_with_upwards_trend:"
                    },
                    "email": {
                        "enabled": False,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "username": "",
                        "password": "",
                        "from_email": "",
                        "to_emails": [],
                        "subject_prefix": "[TRAE] Weekly Trading Report: "
                    }
                }
                
                # Save default configuration
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def load_trade_history(self) -> List[Dict[str, Any]]:
        """Load trade history
        
        Returns:
            List[Dict[str, Any]]: List of historical trades
        """
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return []
    
    def load_news_history(self) -> List[Dict[str, Any]]:
        """Load news history
        
        Returns:
            List[Dict[str, Any]]: List of historical news items
        """
        try:
            if os.path.exists(self.news_history_file):
                with open(self.news_history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading news history: {e}")
            return []
    
    def should_generate_report(self) -> bool:
        """Check if a report should be generated based on the current time and configuration
        
        Returns:
            bool: True if a report should be generated, False otherwise
        """
        if not self.config.get("report", {}).get("enabled", False):
            return False
        
        frequency = self.config.get("report", {}).get("frequency", "weekly")
        now = datetime.now()
        
        if frequency == "daily":
            # Check if it's the configured hour
            hour = self.config.get("report", {}).get("hour", 8)
            return now.hour == hour
        
        elif frequency == "weekly":
            # Check if it's the configured day of the week and hour
            day_of_week = self.config.get("report", {}).get("day_of_week", 1)  # Default to Monday
            hour = self.config.get("report", {}).get("hour", 8)
            return now.weekday() == day_of_week and now.hour == hour
        
        elif frequency == "monthly":
            # Check if it's the first day of the month and the configured hour
            hour = self.config.get("report", {}).get("hour", 8)
            return now.day == 1 and now.hour == hour
        
        return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report
        
        Returns:
            Dict[str, Any]: Report data
        """
        try:
            # Determine report period
            frequency = self.config.get("report", {}).get("frequency", "weekly")
            now = datetime.now()
            
            if frequency == "daily":
                start_date = now - timedelta(days=1)
                period_name = "Daily"
            elif frequency == "weekly":
                start_date = now - timedelta(days=7)
                period_name = "Weekly"
            elif frequency == "monthly":
                start_date = now - timedelta(days=30)
                period_name = "Monthly"
            else:
                start_date = now - timedelta(days=7)  # Default to weekly
                period_name = "Weekly"
            
            # Load data
            trade_history = self.load_trade_history()
            news_history = self.load_news_history()
            
            # Filter data for the report period
            period_trades = []
            for trade in trade_history:
                if "timestamp" in trade:
                    try:
                        trade_date = datetime.fromisoformat(trade["timestamp"])
                        if trade_date >= start_date:
                            period_trades.append(trade)
                    except (ValueError, TypeError):
                        pass
            
            period_news = []
            for news in news_history:
                if "timestamp" in news:
                    try:
                        news_date = datetime.fromisoformat(news["timestamp"])
                        if news_date >= start_date:
                            period_news.append(news)
                    except (ValueError, TypeError):
                        pass
            
            # Generate report sections
            include_sections = self.config.get("report", {}).get("include_sections", [])
            report_data = {
                "timestamp": now.isoformat(),
                "period": {
                    "name": period_name,
                    "start_date": start_date.isoformat(),
                    "end_date": now.isoformat()
                },
                "sections": {}
            }
            
            # Generate each enabled section
            if "performance_summary" in include_sections:
                report_data["sections"]["performance_summary"] = self.generate_performance_summary(period_trades)
            
            if "strategy_evolution" in include_sections:
                report_data["sections"]["strategy_evolution"] = self.generate_strategy_evolution_summary()
            
            if "risk_adjustments" in include_sections:
                report_data["sections"]["risk_adjustments"] = self.generate_risk_adjustments_summary()
            
            if "news_impact" in include_sections:
                report_data["sections"]["news_impact"] = self.generate_news_impact_summary(period_news, period_trades)
            
            if "recommendations" in include_sections:
                report_data["sections"]["recommendations"] = self.generate_recommendations(report_data)
            
            return report_data
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def generate_performance_summary(self, period_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of trading performance
        
        Args:
            period_trades (List[Dict[str, Any]]): Trades during the report period
            
        Returns:
            Dict[str, Any]: Performance summary
        """
        # Calculate basic metrics
        total_trades = len(period_trades)
        winning_trades = sum(1 for trade in period_trades if trade.get("win", False))
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate profit metrics
        total_profit = sum(trade.get("profit", 0) for trade in period_trades)
        total_loss = sum(abs(trade.get("profit", 0)) for trade in period_trades if trade.get("profit", 0) < 0)
        
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')
        
        # Calculate drawdown
        balance_curve = []
        running_balance = 0
        for trade in period_trades:
            running_balance += trade.get("profit", 0)
            balance_curve.append(running_balance)
        
        max_drawdown = 0
        peak = 0
        
        for balance in balance_curve:
            if balance > peak:
                peak = balance
            else:
                drawdown = (peak - balance) / peak * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
        
        # Group trades by strategy
        strategy_performance = {}
        for trade in period_trades:
            strategy = trade.get("strategy", "unknown")
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_profit": 0
                }
            
            strategy_performance[strategy]["total_trades"] += 1
            if trade.get("win", False):
                strategy_performance[strategy]["winning_trades"] += 1
            strategy_performance[strategy]["total_profit"] += trade.get("profit", 0)
        
        # Calculate win rates for each strategy
        for strategy, stats in strategy_performance.items():
            stats["win_rate"] = (stats["winning_trades"] / stats["total_trades"] * 100) if stats["total_trades"] > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "total_profit": total_profit,
            "strategy_performance": strategy_performance
        }
    
    def generate_strategy_evolution_summary(self) -> Dict[str, Any]:
        """Generate a summary of strategy evolution
        
        Returns:
            Dict[str, Any]: Strategy evolution summary
        """
        # Get evolution report from the strategy evolution system
        evolution_report = self.strategy_evolution.generate_evolution_report()
        
        # Extract relevant information for the summary
        summary = {
            "active_strategies": 0,
            "active_variants": 0,
            "active_tests": len(evolution_report.get("active_tests", [])),
            "recent_promotions": evolution_report.get("recent_promotions", []),
            "recent_retirements": evolution_report.get("recent_retirements", []),
            "top_strategies": [],
            "recommendations": evolution_report.get("recommendations", [])
        }
        
        # Count active strategies and variants
        strategies = evolution_report.get("strategies", {})
        for strategy, data in strategies.items():
            summary["active_strategies"] += 1
            summary["active_variants"] += len([v for v in data.get("variants", []) 
                                            if v.get("status") not in ["discarded", "retired"]])
        
        # Identify top performing strategies
        top_strategies = []
        for strategy, data in strategies.items():
            metrics = data.get("metrics", {})
            if metrics.get("win_rate", 0) > 0 and metrics.get("total_trades", 0) > 0:
                top_strategies.append({
                    "name": strategy,
                    "win_rate": metrics.get("win_rate", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                    "total_trades": metrics.get("total_trades", 0)
                })
        
        # Sort by win rate and take top 5
        top_strategies.sort(key=lambda x: x["win_rate"], reverse=True)
        summary["top_strategies"] = top_strategies[:5]
        
        return summary
    
    def generate_risk_adjustments_summary(self) -> Dict[str, Any]:
        """Generate a summary of risk adjustments
        
        Returns:
            Dict[str, Any]: Risk adjustments summary
        """
        # Get risk report from the dynamic risk engine
        risk_report = self.risk_engine.generate_risk_report()
        
        # Extract relevant information for the summary
        summary = {
            "current_risk_level": risk_report.get("current_risk_level", "medium"),
            "risk_trend": risk_report.get("risk_trend", "stable"),
            "risk_factors": risk_report.get("risk_factors", {}),
            "recent_adjustments": risk_report.get("recent_adjustments", []),
            "recommendations": risk_report.get("recommendations", [])
        }
        
        return summary
    
    def generate_news_impact_summary(self, period_news: List[Dict[str, Any]], 
                                   period_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of news impact on trading
        
        Args:
            period_news (List[Dict[str, Any]]): News items during the report period
            period_trades (List[Dict[str, Any]]): Trades during the report period
            
        Returns:
            Dict[str, Any]: News impact summary
        """
        # Group news by impact level
        news_by_impact = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for news in period_news:
            impact = news.get("impact", "low")
            if impact in news_by_impact:
                news_by_impact[impact].append(news)
        
        # Identify trades potentially affected by high-impact news
        affected_trades = []
        for trade in period_trades:
            trade_date = datetime.fromisoformat(trade.get("timestamp", datetime.now().isoformat()))
            
            # Check if any high-impact news was published within 24 hours of the trade
            for news in news_by_impact["high"]:
                news_date = datetime.fromisoformat(news.get("timestamp", datetime.now().isoformat()))
                time_diff = abs((trade_date - news_date).total_seconds() / 3600)  # Hours
                
                if time_diff <= 24:  # Within 24 hours
                    affected_trades.append({
                        "trade": trade,
                        "news": news,
                        "time_diff_hours": time_diff
                    })
        
        # Generate summary
        summary = {
            "total_news_items": len(period_news),
            "high_impact_news": len(news_by_impact["high"]),
            "medium_impact_news": len(news_by_impact["medium"]),
            "low_impact_news": len(news_by_impact["low"]),
            "trades_affected_by_news": len(affected_trades),
            "top_news_items": news_by_impact["high"][:5],  # Top 5 high-impact news
            "news_trade_correlations": affected_trades[:5]  # Top 5 affected trades
        }
        
        return summary
    
    def generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on the report data
        
        Args:
            report_data (Dict[str, Any]): Report data
            
        Returns:
            List[str]: Recommendations
        """
        recommendations = []
        
        # Get recommendations from each section
        if "strategy_evolution" in report_data["sections"]:
            evolution_recs = report_data["sections"]["strategy_evolution"].get("recommendations", [])
            recommendations.extend(evolution_recs)
        
        if "risk_adjustments" in report_data["sections"]:
            risk_recs = report_data["sections"]["risk_adjustments"].get("recommendations", [])
            recommendations.extend(risk_recs)
        
        # Add performance-based recommendations
        if "performance_summary" in report_data["sections"]:
            performance = report_data["sections"]["performance_summary"]
            
            # Check win rate
            win_rate = performance.get("win_rate", 0)
            if win_rate < 40:
                recommendations.append("Overall win rate is below 40%. Consider reviewing and optimizing all active strategies.")
            elif win_rate > 60:
                recommendations.append("Overall win rate is above 60%. Consider increasing position sizes or risk parameters.")
            
            # Check drawdown
            max_drawdown = performance.get("max_drawdown", 0)
            if max_drawdown > 15:
                recommendations.append(f"Maximum drawdown of {max_drawdown:.2f}% exceeds 15%. Consider reducing risk parameters.")
            
            # Check strategy performance
            strategy_performance = performance.get("strategy_performance", {})
            for strategy, stats in strategy_performance.items():
                if stats["total_trades"] >= 10:  # Only consider strategies with sufficient trades
                    if stats["win_rate"] < 35:
                        recommendations.append(f"Strategy '{strategy}' has a low win rate of {stats['win_rate']:.2f}%. Consider optimization or retirement.")
                    elif stats["win_rate"] > 65:
                        recommendations.append(f"Strategy '{strategy}' has a high win rate of {stats['win_rate']:.2f}%. Consider creating variants to explore improvements.")
        
        # Add news-based recommendations
        if "news_impact" in report_data["sections"]:
            news_impact = report_data["sections"]["news_impact"]
            
            if news_impact.get("high_impact_news", 0) > 3:
                recommendations.append("Multiple high-impact news events occurred during this period. Consider adjusting risk parameters during high-volatility periods.")
            
            if news_impact.get("trades_affected_by_news", 0) > 5:
                recommendations.append("Several trades were potentially affected by news events. Consider enhancing news-based filtering in the trading strategy.")
        
        # Deduplicate recommendations
        unique_recommendations = []
        for rec in recommendations:
            if rec not in unique_recommendations:
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def format_report_for_slack(self, report_data: Dict[str, Any]) -> str:
        """Format the report for Slack
        
        Args:
            report_data (Dict[str, Any]): Report data
            
        Returns:
            str: Formatted report for Slack
        """
        period = report_data["period"]
        sections = report_data["sections"]
        
        # Format header
        header = f"*{period['name']} Trading Report: {datetime.fromisoformat(period['start_date']).strftime('%Y-%m-%d')} to {datetime.fromisoformat(period['end_date']).strftime('%Y-%m-%d')}*\n\n"
        
        # Format performance summary
        performance = ""
        if "performance_summary" in sections:
            perf = sections["performance_summary"]
            performance = "*Performance Summary*\n"
            performance += f"• Total Trades: {perf['total_trades']}\n"
            performance += f"• Win Rate: {perf['win_rate']:.2f}%\n"
            performance += f"• Profit Factor: {perf['profit_factor']:.2f}\n"
            performance += f"• Max Drawdown: {perf['max_drawdown']:.2f}%\n"
            performance += f"• Total Profit: {perf['total_profit']:.2f}\n\n"
            
            # Add top strategies
            if perf.get("strategy_performance"):
                performance += "*Top Strategies*\n"
                sorted_strategies = sorted(perf["strategy_performance"].items(), 
                                         key=lambda x: x[1]["win_rate"], reverse=True)[:3]
                
                for strategy, stats in sorted_strategies:
                    performance += f"• {strategy}: {stats['win_rate']:.2f}% win rate, {stats['total_profit']:.2f} profit\n"
                
                performance += "\n"
        
        # Format strategy evolution
        evolution = ""
        if "strategy_evolution" in sections:
            evo = sections["strategy_evolution"]
            evolution = "*Strategy Evolution*\n"
            evolution += f"• Active Strategies: {evo['active_strategies']}\n"
            evolution += f"• Active Variants: {evo['active_variants']}\n"
            evolution += f"• Active A/B Tests: {evo['active_tests']}\n\n"
            
            # Add recent promotions
            if evo.get("recent_promotions"):
                evolution += "*Recent Promotions*\n"
                for promotion in evo["recent_promotions"][:3]:
                    evolution += f"• {promotion['variant']} promoted to replace {promotion['strategy']}\n"
                evolution += "\n"
        
        # Format risk adjustments
        risk = ""
        if "risk_adjustments" in sections:
            risk_data = sections["risk_adjustments"]
            risk = "*Risk Adjustments*\n"
            risk += f"• Current Risk Level: {risk_data['current_risk_level'].capitalize()}\n"
            risk += f"• Risk Trend: {risk_data['risk_trend'].capitalize()}\n\n"
            
            # Add recent adjustments
            if risk_data.get("recent_adjustments"):
                risk += "*Recent Adjustments*\n"
                for adjustment in risk_data["recent_adjustments"][:3]:
                    risk += f"• {adjustment['parameter']}: {adjustment['old_value']} → {adjustment['new_value']}\n"
                risk += "\n"
        
        # Format news impact
        news = ""
        if "news_impact" in sections:
            news_data = sections["news_impact"]
            news = "*News Impact*\n"
            news += f"• High Impact News: {news_data['high_impact_news']}\n"
            news += f"• Trades Affected by News: {news_data['trades_affected_by_news']}\n\n"
            
            # Add top news items
            if news_data.get("top_news_items"):
                news += "*Top News Items*\n"
                for news_item in news_data["top_news_items"][:3]:
                    news += f"• {news_item.get('title', 'Untitled')}: {news_item.get('summary', 'No summary')}\n"
                news += "\n"
        
        # Format recommendations
        recommendations = ""
        if "recommendations" in sections:
            recs = sections["recommendations"]
            recommendations = "*Recommendations*\n"
            for i, rec in enumerate(recs[:5], 1):
                recommendations += f"{i}. {rec}\n"
            recommendations += "\n"
        
        # Combine all sections
        report = header + performance + evolution + risk + news + recommendations
        
        return report
    
    def format_report_for_email(self, report_data: Dict[str, Any]) -> str:
        """Format the report for email (HTML)
        
        Args:
            report_data (Dict[str, Any]): Report data
            
        Returns:
            str: Formatted report for email (HTML)
        """
        period = report_data["period"]
        sections = report_data["sections"]
        
        # Format header
        header = f"<h1>{period['name']} Trading Report</h1>"
        header += f"<p><strong>Period:</strong> {datetime.fromisoformat(period['start_date']).strftime('%Y-%m-%d')} to {datetime.fromisoformat(period['end_date']).strftime('%Y-%m-%d')}</p>"
        
        # Format performance summary
        performance = ""
        if "performance_summary" in sections:
            perf = sections["performance_summary"]
            performance = "<h2>Performance Summary</h2>"
            performance += "<table border='1' cellpadding='5' cellspacing='0'>"
            performance += "<tr><td>Total Trades</td><td>{}</td></tr>".format(perf['total_trades'])
            performance += "<tr><td>Win Rate</td><td>{:.2f}%</td></tr>".format(perf['win_rate'])
            performance += "<tr><td>Profit Factor</td><td>{:.2f}</td></tr>".format(perf['profit_factor'])
            performance += "<tr><td>Max Drawdown</td><td>{:.2f}%</td></tr>".format(perf['max_drawdown'])
            performance += "<tr><td>Total Profit</td><td>{:.2f}</td></tr>".format(perf['total_profit'])
            performance += "</table>"
            
            # Add top strategies
            if perf.get("strategy_performance"):
                performance += "<h3>Top Strategies</h3>"
                performance += "<table border='1' cellpadding='5' cellspacing='0'>"
                performance += "<tr><th>Strategy</th><th>Win Rate</th><th>Total Trades</th><th>Total Profit</th></tr>"
                
                sorted_strategies = sorted(perf["strategy_performance"].items(), 
                                         key=lambda x: x[1]["win_rate"], reverse=True)[:5]
                
                for strategy, stats in sorted_strategies:
                    performance += "<tr>"
                    performance += f"<td>{strategy}</td>"
                    performance += f"<td>{stats['win_rate']:.2f}%</td>"
                    performance += f"<td>{stats['total_trades']}</td>"
                    performance += f"<td>{stats['total_profit']:.2f}</td>"
                    performance += "</tr>"
                
                performance += "</table>"
        
        # Format strategy evolution
        evolution = ""
        if "strategy_evolution" in sections:
            evo = sections["strategy_evolution"]
            evolution = "<h2>Strategy Evolution</h2>"
            evolution += "<table border='1' cellpadding='5' cellspacing='0'>"
            evolution += "<tr><td>Active Strategies</td><td>{}</td></tr>".format(evo['active_strategies'])
            evolution += "<tr><td>Active Variants</td><td>{}</td></tr>".format(evo['active_variants'])
            evolution += "<tr><td>Active A/B Tests</td><td>{}</td></tr>".format(evo['active_tests'])
            evolution += "</table>"
            
            # Add recent promotions
            if evo.get("recent_promotions"):
                evolution += "<h3>Recent Promotions</h3>"
                evolution += "<ul>"
                for promotion in evo["recent_promotions"][:5]:
                    evolution += f"<li>{promotion['variant']} promoted to replace {promotion['strategy']}</li>"
                evolution += "</ul>"
            
            # Add recent retirements
            if evo.get("recent_retirements"):
                evolution += "<h3>Recent Retirements</h3>"
                evolution += "<ul>"
                for retirement in evo["recent_retirements"][:5]:
                    evolution += f"<li>Strategy {retirement['strategy']} retired</li>"
                evolution += "</ul>"
        
        # Format risk adjustments
        risk = ""
        if "risk_adjustments" in sections:
            risk_data = sections["risk_adjustments"]
            risk = "<h2>Risk Adjustments</h2>"
            risk += "<p><strong>Current Risk Level:</strong> {}</p>".format(risk_data['current_risk_level'].capitalize())
            risk += "<p><strong>Risk Trend:</strong> {}</p>".format(risk_data['risk_trend'].capitalize())
            
            # Add risk factors
            if risk_data.get("risk_factors"):
                risk += "<h3>Risk Factors</h3>"
                risk += "<table border='1' cellpadding='5' cellspacing='0'>"
                risk += "<tr><th>Factor</th><th>Value</th><th>Impact</th></tr>"
                
                for factor, data in risk_data["risk_factors"].items():
                    risk += "<tr>"
                    risk += f"<td>{factor}</td>"
                    risk += f"<td>{data.get('value', 'N/A')}</td>"
                    risk += f"<td>{data.get('impact', 'N/A')}</td>"
                    risk += "</tr>"
                
                risk += "</table>"
            
            # Add recent adjustments
            if risk_data.get("recent_adjustments"):
                risk += "<h3>Recent Adjustments</h3>"
                risk += "<table border='1' cellpadding='5' cellspacing='0'>"
                risk += "<tr><th>Parameter</th><th>Old Value</th><th>New Value</th><th>Date</th></tr>"
                
                for adjustment in risk_data["recent_adjustments"][:5]:
                    risk += "<tr>"
                    risk += f"<td>{adjustment['parameter']}</td>"
                    risk += f"<td>{adjustment['old_value']}</td>"
                    risk += f"<td>{adjustment['new_value']}</td>"
                    risk += f"<td>{adjustment.get('date', 'N/A')}</td>"
                    risk += "</tr>"
                
                risk += "</table>"
        
        # Format news impact
        news = ""
        if "news_impact" in sections:
            news_data = sections["news_impact"]
            news = "<h2>News Impact</h2>"
            news += "<table border='1' cellpadding='5' cellspacing='0'>"
            news += "<tr><td>Total News Items</td><td>{}</td></tr>".format(news_data['total_news_items'])
            news += "<tr><td>High Impact News</td><td>{}</td></tr>".format(news_data['high_impact_news'])
            news += "<tr><td>Medium Impact News</td><td>{}</td></tr>".format(news_data['medium_impact_news'])
            news += "<tr><td>Low Impact News</td><td>{}</td></tr>".format(news_data['low_impact_news'])
            news += "<tr><td>Trades Affected by News</td><td>{}</td></tr>".format(news_data['trades_affected_by_news'])
            news += "</table>"
            
            # Add top news items
            if news_data.get("top_news_items"):
                news += "<h3>Top News Items</h3>"
                news += "<table border='1' cellpadding='5' cellspacing='0'>"
                news += "<tr><th>Title</th><th>Summary</th><th>Impact</th></tr>"
                
                for news_item in news_data["top_news_items"][:5]:
                    news += "<tr>"
                    news += f"<td>{news_item.get('title', 'Untitled')}</td>"
                    news += f"<td>{news_item.get('summary', 'No summary')}</td>"
                    news += f"<td>{news_item.get('impact', 'low').capitalize()}</td>"
                    news += "</tr>"
                
                news += "</table>"
        
        # Format recommendations
        recommendations = ""
        if "recommendations" in sections:
            recs = sections["recommendations"]
            recommendations = "<h2>Recommendations</h2>"
            recommendations += "<ol>"
            for rec in recs:
                recommendations += f"<li>{rec}</li>"
            recommendations += "</ol>"
        
        # Combine all sections
        report = f"""<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th {{ background-color: #f2f2f2; text-align: left; }}
        h1, h2, h3 {{ color: #333366; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        {header}
        {performance}
        {evolution}
        {risk}
        {news}
        {recommendations}
        <p>Generated by TRAE AI Trading Bot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""
        
        return report
    
    def send_report_to_slack(self, report_data: Dict[str, Any]) -> bool:
        """Send the report to Slack
        
        Args:
            report_data (Dict[str, Any]): Report data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.config.get("slack", {}).get("enabled", False):
                logger.info("Slack notifications are disabled")
                return False
            
            webhook_url = self.config.get("slack", {}).get("webhook_url", "")
            if not webhook_url:
                logger.error("Slack webhook URL is not configured")
                return False
            
            # Format report for Slack
            report_text = self.format_report_for_slack(report_data)
            
            # Prepare payload
            payload = {
                "text": report_text,
                "channel": self.config.get("slack", {}).get("channel", "#trading-reports"),
                "username": self.config.get("slack", {}).get("username", "TRAE-Bot"),
                "icon_emoji": self.config.get("slack", {}).get("icon_emoji", ":chart_with_upwards_trend:")
            }
            
            # Send to Slack
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                logger.info("Report sent to Slack successfully")
                return True
            else:
                logger.error(f"Failed to send report to Slack: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending report to Slack: {e}")
            return False
    
    def send_report_to_email(self, report_data: Dict[str, Any]) -> bool:
        """Send the report via email
        
        Args:
            report_data (Dict[str, Any]): Report data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.config.get("email", {}).get("enabled", False):
                logger.info("Email notifications are disabled")
                return False
            
            # Get email configuration
            email_config = self.config.get("email", {})
            smtp_server = email_config.get("smtp_server", "")
            smtp_port = email_config.get("smtp_port", 587)
            username = email_config.get("username", "")
            password = email_config.get("password", "")
            from_email = email_config.get("from_email", "")
            to_emails = email_config.get("to_emails", [])
            subject_prefix = email_config.get("subject_prefix", "[TRAE] Weekly Trading Report: ")
            
            if not smtp_server or not username or not password or not from_email or not to_emails:
                logger.error("Email configuration is incomplete")
                return False
            
            # Format report for email
            report_html = self.format_report_for_email(report_data)
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"{subject_prefix}{datetime.now().strftime('%Y-%m-%d')}"
            
            # Attach HTML report
            msg.attach(MIMEText(report_html, "html"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logger.info(f"Report sent via email to {len(to_emails)} recipients")
            return True
        except Exception as e:
            logger.error(f"Error sending report via email: {e}")
            return False
    
    def distribute_report(self, report_data: Dict[str, Any]) -> Dict[str, bool]:
        """Distribute the report via configured channels
        
        Args:
            report_data (Dict[str, Any]): Report data
            
        Returns:
            Dict[str, bool]: Distribution results
        """
        results = {}
        
        # Send to Slack
        if self.config.get("slack", {}).get("enabled", False):
            results["slack"] = self.send_report_to_slack(report_data)
        
        # Send via email
        if self.config.get("email", {}).get("enabled", False):
            results["email"] = self.send_report_to_email(report_data)
        
        return results
    
    def run(self) -> Optional[Dict[str, Any]]:
        """Run the report generator
        
        Returns:
            Optional[Dict[str, Any]]: Report data if generated, None otherwise
        """
        try:
            # Check if a report should be generated
            if not self.should_generate_report():
                logger.info("No report scheduled for this time")
                return None
            
            # Generate report
            logger.info("Generating report...")
            report_data = self.generate_report()
            
            # Distribute report
            logger.info("Distributing report...")
            distribution_results = self.distribute_report(report_data)
            
            # Log results
            for channel, success in distribution_results.items():
                if success:
                    logger.info(f"Report successfully sent via {channel}")
                else:
                    logger.error(f"Failed to send report via {channel}")
            
            return report_data
        except Exception as e:
            logger.error(f"Error running report generator: {e}")
            return None


# For testing
if __name__ == "__main__":
    # Create report generator
    report_generator = WeeklyReportGenerator()
    
    # Generate report
    report_data = report_generator.generate_report()
    
    # Print report data
    print("\nReport Data:")
    print(json.dumps(report_data, indent=4))
    
    # Format for Slack
    slack_report = report_generator.format_report_for_slack(report_data)
    
    print("\nSlack Report:")
    print(slack_report)
    
    # Distribute report
    distribution_results = report_generator.distribute_report(report_data)
    
    print("\nDistribution Results:")
    for channel, success in distribution_results.items():
        print(f"{channel}: {'Success' if success else 'Failed'}")