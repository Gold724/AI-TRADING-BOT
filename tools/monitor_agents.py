# tools/monitor_agents.py

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_agent_performance(log_dir='logs'):
    """Load agent performance data from logs"""
    performance_file = os.path.join(log_dir, 'agent_performance.json')
    if not os.path.exists(performance_file):
        print(f"Performance file not found: {performance_file}")
        return {}
    
    with open(performance_file, 'r') as f:
        return json.load(f)

def load_vote_results(log_dir='logs'):
    """Load voting results from logs"""
    results_file = os.path.join(log_dir, 'vote_results.json')
    if not os.path.exists(results_file):
        print(f"Vote results file not found: {results_file}")
        return []
    
    with open(results_file, 'r') as f:
        return json.load(f)

def calculate_agent_stats(performance_data, vote_results):
    """Calculate statistics for each agent"""
    stats = {}
    
    # Initialize stats from performance data
    for agent_name, perf in performance_data.items():
        stats[agent_name] = {
            'correct_predictions': perf.get('correct_predictions', 0),
            'total_predictions': perf.get('total_predictions', 0),
            'accuracy': perf.get('accuracy', 0),
            'effective_weight': perf.get('effective_weight', 1.0),
            'vetoes_issued': 0,
            'vetoes_correct': 0,
            'votes_by_action': {'buy': 0, 'sell': 0, 'hold': 0},
            'confidence_history': [],
            'vote_timestamps': []
        }
    
    # Process vote results
    for result in vote_results:
        timestamp = result.get('timestamp', '')
        votes = result.get('votes', [])
        
        for vote in votes:
            agent_name = vote.get('agent', '')
            if agent_name not in stats:
                continue
                
            action = vote.get('vote', 'hold')
            confidence = vote.get('confidence', 0)
            veto = vote.get('veto', False)
            
            # Update vote counts
            stats[agent_name]['votes_by_action'][action] += 1
            stats[agent_name]['confidence_history'].append(confidence)
            stats[agent_name]['vote_timestamps'].append(timestamp)
            
            # Track vetoes
            if veto:
                stats[agent_name]['vetoes_issued'] += 1
                # Assuming a veto is correct if the final decision was 'hold'
                if result.get('final_action', '') == 'hold':
                    stats[agent_name]['vetoes_correct'] += 1
    
    # Calculate additional metrics
    for agent_name, agent_stats in stats.items():
        # Calculate veto accuracy
        if agent_stats['vetoes_issued'] > 0:
            agent_stats['veto_accuracy'] = agent_stats['vetoes_correct'] / agent_stats['vetoes_issued']
        else:
            agent_stats['veto_accuracy'] = 0
            
        # Calculate average confidence
        if agent_stats['confidence_history']:
            agent_stats['avg_confidence'] = sum(agent_stats['confidence_history']) / len(agent_stats['confidence_history'])
        else:
            agent_stats['avg_confidence'] = 0
            
        # Calculate vote distribution
        total_votes = sum(agent_stats['votes_by_action'].values())
        if total_votes > 0:
            agent_stats['vote_distribution'] = {
                action: count / total_votes 
                for action, count in agent_stats['votes_by_action'].items()
            }
        else:
            agent_stats['vote_distribution'] = {action: 0 for action in agent_stats['votes_by_action']}
    
    return stats

def plot_agent_performance(stats, output_dir='logs'):
    """Generate performance charts for agents"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot accuracy comparison
    plt.figure(figsize=(12, 6))
    agents = list(stats.keys())
    accuracies = [stats[agent]['accuracy'] for agent in agents]
    
    plt.bar(agents, accuracies)
    plt.title('Agent Prediction Accuracy')
    plt.ylabel('Accuracy (%)')
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(output_dir, 'agent_accuracy.png'))
    
    # Plot effective weights
    plt.figure(figsize=(12, 6))
    weights = [stats[agent]['effective_weight'] for agent in agents]
    
    plt.bar(agents, weights)
    plt.title('Agent Effective Weights')
    plt.ylabel('Weight')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(output_dir, 'agent_weights.png'))
    
    # Plot confidence trends over time
    plt.figure(figsize=(14, 7))
    for agent in agents:
        if stats[agent]['confidence_history'] and stats[agent]['vote_timestamps']:
            # Convert timestamps to datetime objects
            timestamps = [datetime.fromisoformat(ts) if ts else datetime.now() 
                         for ts in stats[agent]['vote_timestamps']]
            plt.plot(timestamps, stats[agent]['confidence_history'], label=agent)
    
    plt.title('Agent Confidence Trends')
    plt.xlabel('Time')
    plt.ylabel('Confidence (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'confidence_trends.png'))
    
    # Plot vote distribution
    fig, axs = plt.subplots(1, len(agents), figsize=(15, 5))
    for i, agent in enumerate(agents):
        dist = stats[agent]['vote_distribution']
        axs[i].pie([dist['buy'], dist['sell'], dist['hold']], 
                 labels=['Buy', 'Sell', 'Hold'],
                 autopct='%1.1f%%',
                 colors=['green', 'red', 'gray'])
        axs[i].set_title(agent)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'vote_distribution.png'))
    
    print(f"Performance charts saved to {output_dir}")

def generate_report(stats, output_dir='logs'):
    """Generate a text report of agent performance"""
    report_file = os.path.join(output_dir, 'agent_report.txt')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(report_file, 'w') as f:
        f.write("===== TRAE Multi-Agent System Performance Report =====\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall system stats
        f.write("SYSTEM OVERVIEW:\n")
        f.write(f"Total agents: {len(stats)}\n")
        
        # Calculate system-wide metrics
        total_correct = sum(s['correct_predictions'] for s in stats.values())
        total_predictions = sum(s['total_predictions'] for s in stats.values())
        system_accuracy = total_correct / total_predictions if total_predictions > 0 else 0
        
        f.write(f"System accuracy: {system_accuracy:.2%}\n")
        f.write(f"Total predictions: {total_predictions}\n\n")
        
        # Individual agent stats
        f.write("AGENT PERFORMANCE:\n")
        for agent_name, agent_stats in stats.items():
            f.write(f"\n--- {agent_name} ---\n")
            f.write(f"Accuracy: {agent_stats['accuracy']:.2%}\n")
            f.write(f"Effective weight: {agent_stats['effective_weight']:.2f}\n")
            f.write(f"Average confidence: {agent_stats['avg_confidence']:.2f}%\n")
            f.write(f"Total votes: {sum(agent_stats['votes_by_action'].values())}\n")
            f.write(f"Vote distribution: Buy {agent_stats['vote_distribution']['buy']:.2%}, "
                   f"Sell {agent_stats['vote_distribution']['sell']:.2%}, "
                   f"Hold {agent_stats['vote_distribution']['hold']:.2%}\n")
            
            if agent_stats['vetoes_issued'] > 0:
                f.write(f"Vetoes issued: {agent_stats['vetoes_issued']}\n")
                f.write(f"Veto accuracy: {agent_stats['veto_accuracy']:.2%}\n")
    
    print(f"Performance report saved to {report_file}")

def main():
    parser = argparse.ArgumentParser(description='Monitor TRAE multi-agent system performance')
    parser.add_argument('--log-dir', default='logs', help='Directory containing log files')
    parser.add_argument('--output-dir', default='logs/reports', help='Directory to save reports and charts')
    args = parser.parse_args()
    
    # Load data
    performance_data = load_agent_performance(args.log_dir)
    vote_results = load_vote_results(args.log_dir)
    
    if not performance_data and not vote_results:
        print("No data found. Make sure the multi-agent system has been running.")
        return
    
    # Calculate statistics
    stats = calculate_agent_stats(performance_data, vote_results)
    
    # Generate visualizations
    plot_agent_performance(stats, args.output_dir)
    
    # Generate report
    generate_report(stats, args.output_dir)
    
    print("Monitoring complete!")

if __name__ == "__main__":
    main()