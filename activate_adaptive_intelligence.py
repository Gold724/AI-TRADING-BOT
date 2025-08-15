#!/usr/bin/env python
# Activate Adaptive Intelligence System for TRAE AI Trading Bot

import argparse
import logging
import os
import sys
from datetime import datetime

# Import AI components
from ai_components.sentinel_decider_llm import SentinelDeciderLLM
from ai_components.dynamic_risk_engine import DynamicRiskEngine
from ai_components.strategy_evolution import StrategyEvolution
from ai_components.weekly_report_generator import WeeklyReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("activate_adaptive_intelligence")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Activate TRAE Adaptive Intelligence System")
    parser.add_argument(
        "--mode",
        choices=["initialize", "evaluate", "report", "full"],
        default="full",
        help="Operation mode: initialize (setup only), evaluate (run analysis), report (generate reports), full (all steps)"
    )
    parser.add_argument(
        "--force-report",
        action="store_true",
        help="Force report generation regardless of schedule"
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Directory containing configuration files"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing data files"
    )
    return parser.parse_args()

def initialize_components(args):
    """Initialize all AI components"""
    logger.info("Initializing Adaptive Intelligence components...")
    
    # Ensure directories exist
    os.makedirs(args.config_dir, exist_ok=True)
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Initialize components
    sentinel = SentinelDeciderLLM(
        os.path.join(args.config_dir, "sentinel_decider_config.json")
    )
    risk_engine = DynamicRiskEngine(
        os.path.join(args.data_dir, "trade_history.json"),
        os.path.join(args.config_dir, "risk_config.json"),
        os.path.join(args.data_dir, "risk_history.json")
    )
    strategy_evolution = StrategyEvolution(
        os.path.join(args.data_dir, "strategy_history.json"),
        os.path.join(args.config_dir, "strategy_config.json"),
        os.path.join(args.data_dir, "strategy_variants.json")
    )
    report_generator = WeeklyReportGenerator(
        os.path.join(args.config_dir, "report_config.json")
    )
    
    logger.info("All components initialized successfully")
    return sentinel, risk_engine, strategy_evolution, report_generator

def run_evaluation(sentinel, risk_engine, strategy_evolution):
    """Run the evaluation cycle for all strategies"""
    logger.info("Running strategy evaluation cycle...")
    
    # Get all active strategies
    strategies = strategy_evolution.get_active_strategies()
    logger.info(f"Found {len(strategies)} active strategies")
    
    for strategy_name in strategies:
        logger.info(f"Evaluating strategy: {strategy_name}")
        
        # 1. Validate strategy using Sentinel Decider
        validation_result = sentinel.validate_strategy(
            strategy_name=strategy_name,
            technical_indicators={},  # Would be populated with actual data
            market_psychology={},     # Would be populated with actual data
            news_data=[],             # Would be populated with actual data
            recent_trades=[]          # Would be populated with actual data
        )
        
        # 2. Update risk parameters
        risk_params = risk_engine.calculate_dynamic_risk(
            strategy_name=strategy_name,
            market_volatility=0.0,    # Would be calculated from actual data
            recent_trades=[]          # Would be populated with actual data
        )
        
        # 3. Evolve strategy if needed
        evolution_result = strategy_evolution.evaluate_strategy(
            strategy_name=strategy_name,
            performance_metrics={},   # Would be populated with actual data
            market_conditions={}      # Would be populated with actual data
        )
        
        logger.info(f"Strategy {strategy_name} evaluation complete")
        logger.info(f"Confidence: {validation_result.get('weighted_confidence', 0):.2f}")
        logger.info(f"Risk adjustment: {risk_params.get('position_size_percent', 0):.2f}%")
        logger.info(f"Evolution decision: {evolution_result.get('decision', 'no_change')}")
    
    logger.info("Evaluation cycle complete")

def generate_reports(report_generator, force=False):
    """Generate performance reports"""
    logger.info("Checking if reports need to be generated...")
    
    # Check if report should be generated based on schedule
    if report_generator.should_generate_report() or force:
        logger.info("Generating weekly performance report")
        report_generator.generate_and_send_reports()
        logger.info("Reports generated and sent successfully")
    else:
        logger.info("No reports scheduled for generation at this time")

def main():
    """Main function to activate the Adaptive Intelligence System"""
    args = parse_arguments()
    
    logger.info("=== TRAE Adaptive Intelligence System ===")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Config directory: {args.config_dir}")
    logger.info(f"Data directory: {args.data_dir}")
    
    # Initialize components
    sentinel, risk_engine, strategy_evolution, report_generator = initialize_components(args)
    
    # Execute based on mode
    if args.mode in ["evaluate", "full"]:
        run_evaluation(sentinel, risk_engine, strategy_evolution)
    
    if args.mode in ["report", "full"]:
        generate_reports(report_generator, args.force_report)
    
    logger.info("Adaptive Intelligence System execution complete")

if __name__ == "__main__":
    main()