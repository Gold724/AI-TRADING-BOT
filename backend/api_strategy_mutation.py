import os
import sys
import json
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

# Add the strategies directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategies"))

# Import the StrategyMutator
from strategies.strategy_mutation import StrategyMutator

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "strategy_mutation.log")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("STRATEGY_MUTATION")

# Create Blueprint
strategy_mutation_bp = Blueprint('strategy_mutation', __name__)

# Initialize the StrategyMutator
mutator = StrategyMutator()

@strategy_mutation_bp.route("/api/strategy", methods=["GET", "POST"])
def manage_strategy():
    """Get or update the current strategy."""
    if request.method == "GET":
        try:
            strategy_data = mutator.get_current_strategy()
            return jsonify(strategy_data), 200
        except Exception as e:
            logger.error(f"Error getting current strategy: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    elif request.method == "POST":
        try:
            data = request.get_json()
            if not data or "strategy" not in data:
                return jsonify({"status": "error", "message": "Strategy name is required"}), 400
            
            description = data.get("description", "Strategy updated via API")
            history_entry = mutator.update_strategy(data, description)
            
            return jsonify({
                "status": "success",
                "message": f"Strategy updated to {data['strategy']}",
                "version": history_entry["version"],
                "updated_at": history_entry["updated_at"]
            }), 200
        except Exception as e:
            logger.error(f"Error updating strategy: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

@strategy_mutation_bp.route("/api/strategy/history", methods=["GET"])
def get_strategy_history():
    """Get the strategy mutation history."""
    try:
        limit = request.args.get("limit", 10, type=int)
        history = mutator.get_strategy_history(limit)
        return jsonify({
            "status": "success",
            "history": history,
            "count": len(history)
        }), 200
    except Exception as e:
        logger.error(f"Error getting strategy history: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@strategy_mutation_bp.route("/api/strategy/available", methods=["GET"])
def get_available_strategies():
    """Get list of available strategy modules."""
    try:
        strategies = mutator.get_available_strategies()
        return jsonify({
            "status": "success",
            "strategies": strategies,
            "count": len(strategies)
        }), 200
    except Exception as e:
        logger.error(f"Error getting available strategies: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@strategy_mutation_bp.route("/api/strategy/mutate", methods=["POST"])
def mutate_strategy():
    """Mutate the current strategy with new parameters."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Get current strategy as base
        current_strategy = mutator.get_current_strategy()
        
        # Update with new parameters
        for key, value in data.items():
            if key == "parameters" and isinstance(value, dict):
                # Update nested parameters
                if "parameters" not in current_strategy:
                    current_strategy["parameters"] = {}
                for param_key, param_value in value.items():
                    current_strategy["parameters"][param_key] = param_value
            elif key != "parameters":
                # Update top-level fields
                current_strategy[key] = value
        
        # Save the updated strategy
        description = data.get("description", "Strategy mutated via API")
        history_entry = mutator.update_strategy(current_strategy, description)
        
        return jsonify({
            "status": "success",
            "message": f"Strategy mutated successfully",
            "version": history_entry["version"],
            "updated_at": history_entry["updated_at"],
            "strategy": current_strategy
        }), 200
    except Exception as e:
        logger.error(f"Error mutating strategy: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@strategy_mutation_bp.route("/api/strategy/prompt", methods=["POST"])
def mutate_strategy_from_prompt():
    """Mutate the current strategy using a natural language prompt."""
    try:
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"status": "error", "message": "Prompt is required"}), 400
        
        prompt = data["prompt"]
        description = data.get("description", f"Strategy mutated via prompt: {prompt[:50]}...")
        
        # Get current strategy
        current_strategy = mutator.get_current_strategy()
        
        # This is a placeholder - in a real implementation, this would call an AI service
        # For now, just log the request and return the current strategy unchanged
        logger.info(f"Strategy mutation requested via prompt: {prompt[:100]}...")
        
        # In a real implementation, this would process the prompt with an AI service
        # and update the strategy based on the AI response
        # For now, we'll just return a message indicating this is a placeholder
        
        return jsonify({
            "status": "success",
            "message": "Strategy prompt received. AI-based mutation is not yet implemented.",
            "prompt": prompt,
            "strategy": current_strategy
        }), 200
    except Exception as e:
        logger.error(f"Error processing strategy prompt: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500