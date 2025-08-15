# tools/visualize_decision.py

import os
import sys
import json
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_decision(file_path):
    """Load a decision from a JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def visualize_decision(decision_data, output_dir='logs/visualizations'):
    """Create visualizations for a multi-agent decision"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract decision and votes
    decision = decision_data.get('decision', {})
    votes = decision.get('votes', [])
    
    if not votes:
        print("No votes found in the decision data")
        return
    
    # Create timestamp for output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Confidence comparison chart
    plt.figure(figsize=(12, 6))
    
    agents = [vote['agent'] for vote in votes]
    confidences = [vote['confidence'] for vote in votes]
    
    # Color bars based on vote
    colors = []
    for vote in votes:
        if vote['vote'] == 'buy':
            colors.append('green')
        elif vote['vote'] == 'sell':
            colors.append('red')
        else:  # hold
            colors.append('gray')
    
    bars = plt.bar(agents, confidences, color=colors)
    
    # Add final decision line
    plt.axhline(y=decision.get('confidence', 0), color='blue', linestyle='--', 
                label=f"Final: {decision.get('action', 'unknown')} ({decision.get('confidence', 0)}%)")
    
    plt.title('Agent Confidence Comparison')
    plt.ylabel('Confidence (%)')
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add legend for vote types
    buy_patch = mpatches.Patch(color='green', label='Buy')
    sell_patch = mpatches.Patch(color='red', label='Sell')
    hold_patch = mpatches.Patch(color='gray', label='Hold')
    plt.legend(handles=[buy_patch, sell_patch, hold_patch, plt.Line2D([0], [0], color='blue', linestyle='--', label=f"Final Decision")])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'confidence_comparison_{timestamp}.png'))
    
    # 2. Decision influence pie chart
    plt.figure(figsize=(10, 8))
    
    # Calculate influence based on confidence and weight
    influences = []
    labels = []
    colors = []
    
    for vote in votes:
        weight = vote.get('weight', 1.0)
        confidence = vote.get('confidence', 0)
        influence = weight * confidence
        influences.append(influence)
        labels.append(f"{vote['agent']} ({influence:.1f})")
        
        if vote['vote'] == 'buy':
            colors.append('lightgreen')
        elif vote['vote'] == 'sell':
            colors.append('lightcoral')
        else:  # hold
            colors.append('lightgray')
    
    plt.pie(influences, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Agent Decision Influence')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'decision_influence_{timestamp}.png'))
    
    # 3. Reasoning visualization
    plt.figure(figsize=(14, 10))
    
    # Create a text visualization of agent reasoning
    plt.axis('off')
    plt.title('Agent Reasoning Analysis')
    
    y_position = 0.95
    line_height = 0.05
    
    # Add final decision at the top
    plt.text(0.5, y_position, f"FINAL DECISION: {decision.get('action', 'unknown').upper()} ({decision.get('confidence', 0)}%)", 
             ha='center', va='center', fontsize=14, fontweight='bold', 
             bbox=dict(facecolor='lightblue', alpha=0.5))
    
    y_position -= line_height * 2
    
    # Add final reasoning
    plt.text(0.5, y_position, f"Reasoning: {decision.get('reasoning', 'No reasoning provided')}", 
             ha='center', va='center', fontsize=12, wrap=True)
    
    y_position -= line_height * 3
    
    # Add individual agent reasoning
    for i, vote in enumerate(votes):
        agent_name = vote['agent']
        vote_action = vote['vote']
        confidence = vote['confidence']
        reason = vote.get('reason', 'No reasoning provided')
        
        # Set color based on vote
        if vote_action == 'buy':
            color = 'green'
        elif vote_action == 'sell':
            color = 'red'
        else:  # hold
            color = 'gray'
        
        # Agent header
        plt.text(0.5, y_position, f"{agent_name}: {vote_action.upper()} ({confidence}%)", 
                 ha='center', va='center', fontsize=12, fontweight='bold', color=color)
        
        y_position -= line_height
        
        # Agent reasoning (with word wrap)
        plt.text(0.5, y_position, f"{reason}", 
                 ha='center', va='center', fontsize=10, wrap=True)
        
        y_position -= line_height * 2
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'reasoning_analysis_{timestamp}.png'))
    
    print(f"Visualizations saved to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Visualize TRAE multi-agent decision process')
    parser.add_argument('--decision-file', required=True, help='Path to decision JSON file')
    parser.add_argument('--output-dir', default='logs/visualizations', help='Directory to save visualizations')
    args = parser.parse_args()
    
    # Load decision data
    try:
        decision_data = load_decision(args.decision_file)
        visualize_decision(decision_data, args.output_dir)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()