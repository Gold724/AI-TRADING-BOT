#!/usr/bin/env python3
"""
Trae AI Trading Sentinel - Performance Optimization Script

This script analyzes and optimizes the trading bot for production performance,
focusing on latency reduction, memory efficiency, and execution speed.

Usage:
    python optimize_performance.py [--profile] [--optimize] [--report]
    
Options:
    --profile: Run performance profiling
    --optimize: Apply optimization recommendations
    --report: Generate performance report
"""

import asyncio
import cProfile
import gc
import json
import logging
import os
import psutil
import pstats
import sys
import time
import threading
import tracemalloc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import io

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger
from src.config.settings import Settings

class PerformanceOptimizer:
    """Performance optimization and profiling for the trading bot."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = setup_logger('performance_optimizer', level=logging.DEBUG if verbose else logging.INFO)
        self.settings = Settings()
        
        # Performance metrics
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'response_times': [],
            'trade_latency': [],
            'gc_stats': [],
            'thread_count': [],
            'io_stats': []
        }
        
        # Optimization recommendations
        self.recommendations = []
        
        # Profiling data
        self.profiler = None
        self.memory_tracer = None
        
    def start_profiling(self):
        """Start performance profiling."""
        self.logger.info("Starting performance profiling...")
        
        # Start CPU profiling
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        
        # Start memory tracing
        tracemalloc.start()
        self.memory_tracer = tracemalloc.take_snapshot()
        
        # Start metrics collection
        self._start_metrics_collection()
        
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop profiling and return results."""
        self.logger.info("Stopping performance profiling...")
        
        results = {}
        
        # Stop CPU profiling
        if self.profiler:
            self.profiler.disable()
            
            # Get CPU profile stats
            s = io.StringIO()
            ps = pstats.Stats(self.profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            results['cpu_profile'] = s.getvalue()
            
        # Stop memory tracing
        if tracemalloc.is_tracing():
            current_snapshot = tracemalloc.take_snapshot()
            top_stats = current_snapshot.compare_to(self.memory_tracer, 'lineno')
            
            memory_stats = []
            for stat in top_stats[:10]:  # Top 10 memory consumers
                memory_stats.append({
                    'file': stat.traceback.format()[-1] if stat.traceback.format() else 'unknown',
                    'size_diff': stat.size_diff,
                    'count_diff': stat.count_diff
                })
                
            results['memory_profile'] = memory_stats
            tracemalloc.stop()
            
        # Stop metrics collection
        self._stop_metrics_collection()
        
        results['metrics'] = self.metrics
        return results
        
    def _start_metrics_collection(self):
        """Start collecting system metrics."""
        self.collecting_metrics = True
        self.metrics_thread = threading.Thread(target=self._collect_metrics)
        self.metrics_thread.daemon = True
        self.metrics_thread.start()
        
    def _stop_metrics_collection(self):
        """Stop collecting metrics."""
        self.collecting_metrics = False
        if hasattr(self, 'metrics_thread'):
            self.metrics_thread.join(timeout=5)
            
    def _collect_metrics(self):
        """Collect system metrics continuously."""
        process = psutil.Process()
        
        while getattr(self, 'collecting_metrics', False):
            try:
                # CPU usage
                cpu_percent = process.cpu_percent()
                self.metrics['cpu_usage'].append({
                    'timestamp': time.time(),
                    'value': cpu_percent
                })
                
                # Memory usage
                memory_info = process.memory_info()
                self.metrics['memory_usage'].append({
                    'timestamp': time.time(),
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'percent': process.memory_percent()
                })
                
                # Thread count
                self.metrics['thread_count'].append({
                    'timestamp': time.time(),
                    'value': process.num_threads()
                })
                
                # I/O stats
                try:
                    io_counters = process.io_counters()
                    self.metrics['io_stats'].append({
                        'timestamp': time.time(),
                        'read_bytes': io_counters.read_bytes,
                        'write_bytes': io_counters.write_bytes,
                        'read_count': io_counters.read_count,
                        'write_count': io_counters.write_count
                    })
                except (AttributeError, psutil.AccessDenied):
                    pass
                    
                # Garbage collection stats
                gc_stats = gc.get_stats()
                self.metrics['gc_stats'].append({
                    'timestamp': time.time(),
                    'collections': [gen['collections'] for gen in gc_stats],
                    'collected': [gen['collected'] for gen in gc_stats],
                    'uncollectable': [gen['uncollectable'] for gen in gc_stats]
                })
                
                time.sleep(1)  # Collect every second
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                
    def analyze_performance(self, profile_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze performance data and generate recommendations."""
        recommendations = []
        
        # Analyze CPU usage
        cpu_data = self.metrics.get('cpu_usage', [])
        if cpu_data:
            avg_cpu = sum(m['value'] for m in cpu_data) / len(cpu_data)
            max_cpu = max(m['value'] for m in cpu_data)
            
            if avg_cpu > 70:
                recommendations.append({
                    'category': 'CPU',
                    'severity': 'high',
                    'issue': f'High average CPU usage: {avg_cpu:.1f}%',
                    'recommendation': 'Consider optimizing CPU-intensive operations, use async/await patterns, or implement caching'
                })
                
            if max_cpu > 95:
                recommendations.append({
                    'category': 'CPU',
                    'severity': 'critical',
                    'issue': f'CPU spikes detected: {max_cpu:.1f}%',
                    'recommendation': 'Identify and optimize blocking operations, consider rate limiting'
                })
                
        # Analyze memory usage
        memory_data = self.metrics.get('memory_usage', [])
        if memory_data:
            avg_memory = sum(m['percent'] for m in memory_data) / len(memory_data)
            max_memory = max(m['percent'] for m in memory_data)
            
            # Check for memory growth
            if len(memory_data) > 10:
                start_memory = memory_data[0]['percent']
                end_memory = memory_data[-1]['percent']
                growth = end_memory - start_memory
                
                if growth > 10:  # More than 10% growth
                    recommendations.append({
                        'category': 'Memory',
                        'severity': 'high',
                        'issue': f'Memory growth detected: {growth:.1f}%',
                        'recommendation': 'Check for memory leaks, implement proper cleanup, use weak references'
                    })
                    
            if avg_memory > 80:
                recommendations.append({
                    'category': 'Memory',
                    'severity': 'high',
                    'issue': f'High memory usage: {avg_memory:.1f}%',
                    'recommendation': 'Optimize data structures, implement memory pooling, reduce object creation'
                })
                
        # Analyze garbage collection
        gc_data = self.metrics.get('gc_stats', [])
        if len(gc_data) > 1:
            start_gc = gc_data[0]
            end_gc = gc_data[-1]
            
            for gen in range(len(start_gc['collections'])):
                collections_diff = end_gc['collections'][gen] - start_gc['collections'][gen]
                if collections_diff > 100:  # Frequent GC
                    recommendations.append({
                        'category': 'GC',
                        'severity': 'medium',
                        'issue': f'Frequent garbage collection in generation {gen}: {collections_diff} collections',
                        'recommendation': 'Reduce object allocation, use object pooling, optimize data structures'
                    })
                    
        # Analyze thread count
        thread_data = self.metrics.get('thread_count', [])
        if thread_data:
            avg_threads = sum(m['value'] for m in thread_data) / len(thread_data)
            max_threads = max(m['value'] for m in thread_data)
            
            if max_threads > 50:
                recommendations.append({
                    'category': 'Threading',
                    'severity': 'medium',
                    'issue': f'High thread count: {max_threads}',
                    'recommendation': 'Use thread pools, async/await patterns, or reduce concurrent operations'
                })
                
        # Analyze CPU profile
        if 'cpu_profile' in profile_results:
            # Parse CPU profile for hot spots
            profile_lines = profile_results['cpu_profile'].split('\n')
            for line in profile_lines[5:15]:  # Skip headers, check top functions
                if 'cumtime' in line and any(keyword in line for keyword in ['sleep', 'wait', 'lock']):
                    recommendations.append({
                        'category': 'CPU',
                        'severity': 'medium',
                        'issue': 'Blocking operations detected in hot path',
                        'recommendation': 'Replace blocking calls with async alternatives or move to background threads'
                    })
                    break
                    
        # Analyze memory profile
        if 'memory_profile' in profile_results:
            for stat in profile_results['memory_profile']:
                if stat['size_diff'] > 1024 * 1024:  # More than 1MB growth
                    recommendations.append({
                        'category': 'Memory',
                        'severity': 'medium',
                        'issue': f'Large memory allocation detected: {stat['size_diff'] / 1024 / 1024:.1f}MB',
                        'recommendation': f'Optimize memory usage in: {stat['file']}'
                    })
                    
        return recommendations
        
    def apply_optimizations(self) -> List[str]:
        """Apply performance optimizations."""
        applied = []
        
        try:
            # Optimize garbage collection
            gc.set_threshold(700, 10, 10)  # More aggressive GC
            applied.append("Optimized garbage collection thresholds")
            
            # Set process priority (if possible)
            try:
                process = psutil.Process()
                if hasattr(psutil, 'HIGH_PRIORITY_CLASS'):
                    process.nice(psutil.HIGH_PRIORITY_CLASS)
                else:
                    process.nice(-5)  # Higher priority on Unix
                applied.append("Increased process priority")
            except (psutil.AccessDenied, AttributeError):
                pass
                
            # Optimize Python settings
            sys.setswitchinterval(0.001)  # Reduce thread switching overhead
            applied.append("Optimized thread switching interval")
            
            # Enable optimizations in environment
            os.environ['PYTHONOPTIMIZE'] = '2'
            os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
            applied.append("Enabled Python optimizations")
            
        except Exception as e:
            self.logger.error(f"Error applying optimizations: {e}")
            
        return applied
        
    def benchmark_operations(self) -> Dict[str, float]:
        """Benchmark critical operations."""
        benchmarks = {}
        
        # Benchmark API response time
        try:
            import requests
            start_time = time.time()
            response = requests.get('http://localhost:5000/health', timeout=5)
            benchmarks['api_response_time'] = time.time() - start_time
        except Exception:
            benchmarks['api_response_time'] = float('inf')
            
        # Benchmark data processing
        start_time = time.time()
        data = list(range(10000))
        processed = [x * 2 for x in data if x % 2 == 0]
        benchmarks['data_processing_time'] = time.time() - start_time
        
        # Benchmark JSON serialization
        test_data = {'trades': [{'id': i, 'price': i * 1.5, 'volume': i * 10} for i in range(1000)]}
        start_time = time.time()
        json_str = json.dumps(test_data)
        json.loads(json_str)
        benchmarks['json_serialization_time'] = time.time() - start_time
        
        # Benchmark file I/O
        test_file = Path('/tmp/benchmark_test.txt')
        start_time = time.time()
        with open(test_file, 'w') as f:
            f.write('test data' * 1000)
        with open(test_file, 'r') as f:
            f.read()
        test_file.unlink()
        benchmarks['file_io_time'] = time.time() - start_time
        
        return benchmarks
        
    def generate_optimization_config(self) -> Dict[str, Any]:
        """Generate optimized configuration."""
        config = {
            'system': {
                'gc_thresholds': [700, 10, 10],
                'thread_switch_interval': 0.001,
                'process_priority': 'high'
            },
            'application': {
                'max_workers': min(32, (os.cpu_count() or 1) + 4),
                'connection_pool_size': 20,
                'request_timeout': 5.0,
                'retry_attempts': 3,
                'cache_size': 1000,
                'batch_size': 100
            },
            'trading': {
                'max_concurrent_trades': 5,
                'order_timeout': 10.0,
                'price_update_interval': 0.1,
                'risk_check_interval': 1.0
            },
            'monitoring': {
                'metrics_interval': 5.0,
                'log_level': 'INFO',
                'max_log_size': '100MB',
                'backup_count': 5
            }
        }
        
        return config
        
    def save_performance_report(self, profile_results: Dict[str, Any], 
                              recommendations: List[Dict[str, Any]],
                              benchmarks: Dict[str, float],
                              filename: str = None) -> Path:
        """Save comprehensive performance report."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_report_{timestamp}.json'
            
        report_path = Path('reports') / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate summary statistics
        summary = self._calculate_summary_stats()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'benchmarks': benchmarks,
            'recommendations': recommendations,
            'profile_results': profile_results,
            'metrics': self.metrics,
            'system_info': {
                'cpu_count': os.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'python_version': sys.version,
                'platform': sys.platform
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        self.logger.info(f"Performance report saved to: {report_path}")
        return report_path
        
    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """Calculate summary statistics from metrics."""
        summary = {}
        
        # CPU statistics
        cpu_data = [m['value'] for m in self.metrics.get('cpu_usage', [])]
        if cpu_data:
            summary['cpu'] = {
                'avg': sum(cpu_data) / len(cpu_data),
                'max': max(cpu_data),
                'min': min(cpu_data)
            }
            
        # Memory statistics
        memory_data = [m['percent'] for m in self.metrics.get('memory_usage', [])]
        if memory_data:
            summary['memory'] = {
                'avg': sum(memory_data) / len(memory_data),
                'max': max(memory_data),
                'min': min(memory_data)
            }
            
        # Thread statistics
        thread_data = [m['value'] for m in self.metrics.get('thread_count', [])]
        if thread_data:
            summary['threads'] = {
                'avg': sum(thread_data) / len(thread_data),
                'max': max(thread_data),
                'min': min(thread_data)
            }
            
        return summary
        
    def print_performance_summary(self, recommendations: List[Dict[str, Any]], 
                                benchmarks: Dict[str, float]):
        """Print performance summary."""
        print("\n" + "="*70)
        print("TRAE AI TRADING SENTINEL - PERFORMANCE ANALYSIS")
        print("="*70)
        
        # Print benchmarks
        print("\nBENCHMARKS:")
        print("-" * 30)
        for operation, time_taken in benchmarks.items():
            if time_taken == float('inf'):
                print(f"{operation}: FAILED")
            else:
                print(f"{operation}: {time_taken*1000:.2f}ms")
                
        # Print recommendations by severity
        print("\nRECOMMENDATIONS:")
        print("-" * 30)
        
        severity_order = ['critical', 'high', 'medium', 'low']
        for severity in severity_order:
            severity_recs = [r for r in recommendations if r['severity'] == severity]
            if severity_recs:
                print(f"\n{severity.upper()} PRIORITY:")
                for rec in severity_recs:
                    print(f"  • [{rec['category']}] {rec['issue']}")
                    print(f"    → {rec['recommendation']}")
                    
        # Print summary stats
        summary = self._calculate_summary_stats()
        if summary:
            print("\nSYSTEM PERFORMANCE:")
            print("-" * 30)
            
            if 'cpu' in summary:
                cpu = summary['cpu']
                print(f"CPU Usage: Avg {cpu['avg']:.1f}%, Max {cpu['max']:.1f}%")
                
            if 'memory' in summary:
                memory = summary['memory']
                print(f"Memory Usage: Avg {memory['avg']:.1f}%, Max {memory['max']:.1f}%")
                
            if 'threads' in summary:
                threads = summary['threads']
                print(f"Thread Count: Avg {threads['avg']:.1f}, Max {threads['max']}")
                
        print("\n" + "="*70)
        
def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance optimization for Trae AI Trading Sentinel')
    parser.add_argument('--profile', action='store_true', help='Run performance profiling')
    parser.add_argument('--optimize', action='store_true', help='Apply optimization recommendations')
    parser.add_argument('--report', help='Generate performance report')
    parser.add_argument('--duration', type=int, default=60, help='Profiling duration in seconds')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    optimizer = PerformanceOptimizer(verbose=args.verbose)
    
    if args.optimize:
        print("Applying performance optimizations...")
        applied = optimizer.apply_optimizations()
        for optimization in applied:
            print(f"✅ {optimization}")
            
    if args.profile:
        print(f"Starting performance profiling for {args.duration} seconds...")
        
        optimizer.start_profiling()
        
        # Let the system run for the specified duration
        time.sleep(args.duration)
        
        profile_results = optimizer.stop_profiling()
        
        # Analyze results
        recommendations = optimizer.analyze_performance(profile_results)
        benchmarks = optimizer.benchmark_operations()
        
        # Print summary
        optimizer.print_performance_summary(recommendations, benchmarks)
        
        # Save report
        if args.report or True:  # Always save report
            report_path = optimizer.save_performance_report(
                profile_results, recommendations, benchmarks, args.report
            )
            print(f"\nDetailed report saved to: {report_path}")
            
        # Generate optimized config
        config = optimizer.generate_optimization_config()
        config_path = Path('config') / 'optimized_settings.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"Optimized configuration saved to: {config_path}")
        
    else:
        # Just run benchmarks
        benchmarks = optimizer.benchmark_operations()
        optimizer.print_performance_summary([], benchmarks)
        
if __name__ == '__main__':
    main()