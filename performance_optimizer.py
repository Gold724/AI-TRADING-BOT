#!/usr/bin/env python3
"""
TradeBot Sentinel - Advanced Performance Optimizer

Optimizes system performance through intelligent resource management,
caching strategies, connection pooling, and adaptive scaling.
Provides real-time performance monitoring and automatic optimization.

Author: TradeBot Sentinel Team
Version: 1.0.0
Date: 2024
"""

import asyncio
import logging
import json
import time
import threading
import psutil
import sqlite3
import pickle
import hashlib
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess
import os
import sys
import traceback
from contextlib import contextmanager
from collections import deque, defaultdict
import statistics
import weakref
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from functools import lru_cache, wraps
import aiohttp
import asyncio
from urllib.parse import urlparse

# Performance optimization categories
class OptimizationType(Enum):
    MEMORY_OPTIMIZATION = "memory_optimization"
    CPU_OPTIMIZATION = "cpu_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"
    DISK_IO_OPTIMIZATION = "disk_io_optimization"
    BROWSER_OPTIMIZATION = "browser_optimization"
    DATABASE_OPTIMIZATION = "database_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    CONNECTION_POOLING = "connection_pooling"
    THREAD_OPTIMIZATION = "thread_optimization"
    PROCESS_OPTIMIZATION = "process_optimization"

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: str
    metric_type: str
    value: float
    unit: str
    component: str
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationResult:
    """Result of an optimization operation"""
    optimization_type: OptimizationType
    success: bool
    improvement_percent: float
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    timestamp: str
    duration_seconds: float
    description: str

class PerformanceCache:
    """Advanced caching system with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.expiry_times: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            current_time = time.time()
            
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            # Check expiry
            if current_time > self.expiry_times.get(key, 0):
                self._remove_key(key)
                self.miss_count += 1
                return None
            
            # Update access time
            self.access_times[key] = current_time
            self.hit_count += 1
            return self.cache[key]['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self._lock:
            current_time = time.time()
            ttl = ttl or self.default_ttl
            
            # Evict if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            self.cache[key] = {'value': value, 'size': sys.getsizeof(value)}
            self.access_times[key] = current_time
            self.expiry_times[key] = current_time + ttl
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove_key(lru_key)
    
    def _remove_key(self, key: str) -> None:
        """Remove key from all data structures"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.expiry_times.pop(key, None)
    
    def clear_expired(self) -> int:
        """Clear expired entries"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, expiry in self.expiry_times.items()
                if current_time > expiry
            ]
            
            for key in expired_keys:
                self._remove_key(key)
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        total_size = sum(item['size'] for item in self.cache.values())
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'total_memory_bytes': total_size,
            'average_item_size': total_size / len(self.cache) if self.cache else 0
        }

class ConnectionPool:
    """Advanced connection pooling for HTTP requests"""
    
    def __init__(self, max_connections: int = 100, max_connections_per_host: int = 30):
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.connection_counts: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
    
    async def get_session(self, url: str) -> aiohttp.ClientSession:
        """Get or create session for URL"""
        async with self._lock:
            parsed = urlparse(url)
            host_key = f"{parsed.scheme}://{parsed.netloc}"
            
            if host_key not in self.sessions:
                connector = aiohttp.TCPConnector(
                    limit=self.max_connections,
                    limit_per_host=self.max_connections_per_host,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                
                self.sessions[host_key] = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'TradeBot-Sentinel/1.0',
                        'Connection': 'keep-alive'
                    }
                )
            
            self.connection_counts[host_key] += 1
            return self.sessions[host_key]
    
    async def close_all(self):
        """Close all sessions"""
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()
        self.connection_counts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            'active_sessions': len(self.sessions),
            'total_connections': sum(self.connection_counts.values()),
            'connections_per_host': dict(self.connection_counts)
        }

class PerformanceOptimizer:
    """Advanced performance optimization system"""
    
    def __init__(self, config_file: str = "performance_config.json"):
        self.config_file = config_file
        self.logger = self._setup_logging()
        self.config = self._load_config()
        
        # Performance tracking
        self.metrics_history: deque = deque(maxlen=10000)
        self.optimization_history: List[OptimizationResult] = []
        self.baseline_metrics: Dict[str, float] = {}
        
        # Optimization components
        self.cache = PerformanceCache(
            max_size=self.config.get('cache_max_size', 10000),
            default_ttl=self.config.get('cache_ttl', 3600)
        )
        self.connection_pool = ConnectionPool(
            max_connections=self.config.get('max_connections', 100),
            max_connections_per_host=self.config.get('max_connections_per_host', 30)
        )
        
        # Thread and process pools
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('max_threads', multiprocessing.cpu_count() * 2)
        )
        self.process_pool = ProcessPoolExecutor(
            max_workers=self.config.get('max_processes', multiprocessing.cpu_count())
        )
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.optimization_enabled = True
        
        # Database for persistence
        self.db_file = "performance_metrics.db"
        self._init_database()
        
        # Initialize baseline
        asyncio.create_task(self._establish_baseline())
        
        self.logger.info("🚀 Performance Optimizer initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('PerformanceOptimizer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('performance_optimizer.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "monitoring_interval": 30,
            "optimization_interval": 300,
            "cache_max_size": 10000,
            "cache_ttl": 3600,
            "max_connections": 100,
            "max_connections_per_host": 30,
            "max_threads": multiprocessing.cpu_count() * 2,
            "max_processes": multiprocessing.cpu_count(),
            "memory_threshold_mb": 2048,
            "cpu_threshold_percent": 80,
            "disk_threshold_percent": 85,
            "network_timeout_seconds": 30,
            "gc_threshold": 0.8,
            "auto_optimization": True,
            "aggressive_optimization": False
        }
        
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
        except Exception as e:
            self.logger.warning(f"Config load failed, using defaults: {e}")
        
        return default_config
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    component TEXT,
                    context TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    optimization_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    improvement_percent REAL,
                    before_metrics TEXT,
                    after_metrics TEXT,
                    duration_seconds REAL,
                    description TEXT
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type ON performance_metrics(metric_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimizations_timestamp ON optimizations(timestamp)")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    async def _establish_baseline(self):
        """Establish performance baseline metrics"""
        try:
            self.logger.info("📊 Establishing performance baseline")
            
            # Collect baseline metrics over a short period
            baseline_samples = []
            for _ in range(10):
                metrics = await self._collect_comprehensive_metrics()
                baseline_samples.append(metrics)
                await asyncio.sleep(1)
            
            # Calculate baseline averages
            for key in baseline_samples[0].keys():
                if isinstance(baseline_samples[0][key], (int, float)):
                    values = [sample[key] for sample in baseline_samples if key in sample]
                    self.baseline_metrics[key] = statistics.mean(values)
            
            self.logger.info(f"✅ Baseline established with {len(self.baseline_metrics)} metrics")
            
        except Exception as e:
            self.logger.error(f"Baseline establishment failed: {e}")
    
    async def _collect_comprehensive_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system and application metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Process metrics
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            process_cpu = current_process.cpu_percent()
            
            # Application-specific metrics
            cache_stats = self.cache.get_stats()
            pool_stats = self.connection_pool.get_stats()
            
            # Thread and process pool metrics
            thread_pool_active = getattr(self.thread_pool, '_threads', 0)
            process_pool_active = len(getattr(self.process_pool, '_processes', {}))
            
            # Garbage collection metrics
            gc_stats = gc.get_stats()
            gc_counts = gc.get_count()
            
            metrics = {
                # System metrics
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_usage_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                
                # Process metrics
                'process_memory_rss_mb': process_memory.rss / (1024**2),
                'process_memory_vms_mb': process_memory.vms / (1024**2),
                'process_cpu_percent': process_cpu,
                
                # Application metrics
                'cache_size': cache_stats['size'],
                'cache_hit_rate': cache_stats['hit_rate'],
                'cache_memory_mb': cache_stats['total_memory_bytes'] / (1024**2),
                'active_connections': pool_stats['total_connections'],
                'active_sessions': pool_stats['active_sessions'],
                
                # Pool metrics
                'thread_pool_active': thread_pool_active,
                'process_pool_active': process_pool_active,
                
                # GC metrics
                'gc_generation0': gc_counts[0],
                'gc_generation1': gc_counts[1],
                'gc_generation2': gc_counts[2],
                'gc_collections': sum(stat['collections'] for stat in gc_stats),
                
                # Timestamp
                'timestamp': datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {e}")
            return {}
    
    async def optimize_memory(self) -> OptimizationResult:
        """Optimize memory usage"""
        start_time = time.time()
        before_metrics = await self._collect_comprehensive_metrics()
        
        try:
            self.logger.info("🧠 Starting memory optimization")
            
            # Clear expired cache entries
            expired_cleared = self.cache.clear_expired()
            
            # Force garbage collection
            collected_objects = gc.collect()
            
            # Clear weak references
            weakref.finalize_all()
            
            # Optimize cache size if memory usage is high
            if before_metrics.get('memory_usage_percent', 0) > 85:
                current_cache_size = self.cache.max_size
                self.cache.max_size = max(1000, int(current_cache_size * 0.7))
                
                # Clear excess cache entries
                while len(self.cache.cache) > self.cache.max_size:
                    self.cache._evict_lru()
            
            await asyncio.sleep(2)  # Allow time for cleanup
            after_metrics = await self._collect_comprehensive_metrics()
            
            # Calculate improvement
            before_memory = before_metrics.get('process_memory_rss_mb', 0)
            after_memory = after_metrics.get('process_memory_rss_mb', 0)
            improvement = ((before_memory - after_memory) / before_memory * 100) if before_memory > 0 else 0
            
            result = OptimizationResult(
                optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                success=improvement > 0,
                improvement_percent=improvement,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Cleared {expired_cleared} expired cache entries, collected {collected_objects} objects"
            )
            
            self.logger.info(f"✅ Memory optimization completed: {improvement:.1f}% improvement")
            return result
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
            return OptimizationResult(
                optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                success=False,
                improvement_percent=0,
                before_metrics=before_metrics,
                after_metrics={},
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Failed: {str(e)}"
            )
    
    async def optimize_network(self) -> OptimizationResult:
        """Optimize network performance"""
        start_time = time.time()
        before_metrics = await self._collect_comprehensive_metrics()
        
        try:
            self.logger.info("🌐 Starting network optimization")
            
            # Optimize connection pool settings
            current_connections = before_metrics.get('active_connections', 0)
            
            if current_connections > self.config.get('max_connections', 100) * 0.8:
                # Reduce connection limits temporarily
                for session in self.connection_pool.sessions.values():
                    if hasattr(session, '_connector'):
                        session._connector._limit = min(50, session._connector._limit)
            
            # Clear idle connections
            for host, session in list(self.connection_pool.sessions.items()):
                if self.connection_pool.connection_counts[host] == 0:
                    await session.close()
                    del self.connection_pool.sessions[host]
                    del self.connection_pool.connection_counts[host]
            
            await asyncio.sleep(1)
            after_metrics = await self._collect_comprehensive_metrics()
            
            # Calculate improvement
            before_connections = before_metrics.get('active_connections', 0)
            after_connections = after_metrics.get('active_connections', 0)
            improvement = ((before_connections - after_connections) / before_connections * 100) if before_connections > 0 else 0
            
            result = OptimizationResult(
                optimization_type=OptimizationType.NETWORK_OPTIMIZATION,
                success=improvement > 0,
                improvement_percent=improvement,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Optimized connection pool, reduced active connections by {before_connections - after_connections}"
            )
            
            self.logger.info(f"✅ Network optimization completed: {improvement:.1f}% improvement")
            return result
            
        except Exception as e:
            self.logger.error(f"Network optimization failed: {e}")
            return OptimizationResult(
                optimization_type=OptimizationType.NETWORK_OPTIMIZATION,
                success=False,
                improvement_percent=0,
                before_metrics=before_metrics,
                after_metrics={},
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Failed: {str(e)}"
            )
    
    async def optimize_cache(self) -> OptimizationResult:
        """Optimize cache performance"""
        start_time = time.time()
        before_metrics = await self._collect_comprehensive_metrics()
        
        try:
            self.logger.info("💾 Starting cache optimization")
            
            before_hit_rate = self.cache.get_stats()['hit_rate']
            
            # Clear expired entries
            expired_cleared = self.cache.clear_expired()
            
            # Adjust cache size based on hit rate
            if before_hit_rate < 0.5 and self.cache.max_size > 1000:
                # Low hit rate, reduce cache size
                self.cache.max_size = int(self.cache.max_size * 0.8)
                while len(self.cache.cache) > self.cache.max_size:
                    self.cache._evict_lru()
            elif before_hit_rate > 0.9 and self.cache.max_size < 50000:
                # High hit rate, increase cache size
                self.cache.max_size = int(self.cache.max_size * 1.2)
            
            await asyncio.sleep(1)
            after_metrics = await self._collect_comprehensive_metrics()
            
            after_hit_rate = self.cache.get_stats()['hit_rate']
            improvement = ((after_hit_rate - before_hit_rate) / before_hit_rate * 100) if before_hit_rate > 0 else 0
            
            result = OptimizationResult(
                optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                success=improvement > 0 or expired_cleared > 0,
                improvement_percent=improvement,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Cleared {expired_cleared} expired entries, hit rate: {before_hit_rate:.2f} -> {after_hit_rate:.2f}"
            )
            
            self.logger.info(f"✅ Cache optimization completed: {improvement:.1f}% improvement")
            return result
            
        except Exception as e:
            self.logger.error(f"Cache optimization failed: {e}")
            return OptimizationResult(
                optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                success=False,
                improvement_percent=0,
                before_metrics=before_metrics,
                after_metrics={},
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Failed: {str(e)}"
            )
    
    async def optimize_threads(self) -> OptimizationResult:
        """Optimize thread pool performance"""
        start_time = time.time()
        before_metrics = await self._collect_comprehensive_metrics()
        
        try:
            self.logger.info("🧵 Starting thread optimization")
            
            # Get current thread pool stats
            current_threads = getattr(self.thread_pool, '_threads', 0)
            max_workers = self.thread_pool._max_workers
            
            # Adjust thread pool size based on CPU usage
            cpu_usage = before_metrics.get('cpu_usage_percent', 0)
            
            if cpu_usage > 90 and max_workers > 2:
                # High CPU, reduce threads
                new_max_workers = max(2, int(max_workers * 0.8))
                self.thread_pool._max_workers = new_max_workers
            elif cpu_usage < 50 and max_workers < multiprocessing.cpu_count() * 4:
                # Low CPU, can increase threads
                new_max_workers = min(multiprocessing.cpu_count() * 4, int(max_workers * 1.2))
                self.thread_pool._max_workers = new_max_workers
            
            await asyncio.sleep(1)
            after_metrics = await self._collect_comprehensive_metrics()
            
            # Calculate improvement based on CPU efficiency
            before_cpu = before_metrics.get('cpu_usage_percent', 0)
            after_cpu = after_metrics.get('cpu_usage_percent', 0)
            improvement = ((before_cpu - after_cpu) / before_cpu * 100) if before_cpu > 0 else 0
            
            result = OptimizationResult(
                optimization_type=OptimizationType.THREAD_OPTIMIZATION,
                success=abs(improvement) > 1,  # Any significant change is good
                improvement_percent=improvement,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Adjusted thread pool: {max_workers} -> {self.thread_pool._max_workers} workers"
            )
            
            self.logger.info(f"✅ Thread optimization completed: {improvement:.1f}% CPU improvement")
            return result
            
        except Exception as e:
            self.logger.error(f"Thread optimization failed: {e}")
            return OptimizationResult(
                optimization_type=OptimizationType.THREAD_OPTIMIZATION,
                success=False,
                improvement_percent=0,
                before_metrics=before_metrics,
                after_metrics={},
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                description=f"Failed: {str(e)}"
            )
    
    async def run_comprehensive_optimization(self) -> List[OptimizationResult]:
        """Run comprehensive optimization across all categories"""
        self.logger.info("🚀 Starting comprehensive performance optimization")
        
        results = []
        
        # Run optimizations in order of impact
        optimizations = [
            self.optimize_memory,
            self.optimize_cache,
            self.optimize_network,
            self.optimize_threads
        ]
        
        for optimization in optimizations:
            try:
                result = await optimization()
                results.append(result)
                
                # Save result to database
                await self._save_optimization_result(result)
                
                # Brief pause between optimizations
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Optimization {optimization.__name__} failed: {e}")
        
        # Calculate overall improvement
        successful_optimizations = [r for r in results if r.success]
        total_improvement = sum(r.improvement_percent for r in successful_optimizations)
        
        self.logger.info(f"✅ Comprehensive optimization completed: {len(successful_optimizations)}/{len(results)} successful, {total_improvement:.1f}% total improvement")
        
        return results
    
    async def _save_optimization_result(self, result: OptimizationResult):
        """Save optimization result to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO optimizations 
                (timestamp, optimization_type, success, improvement_percent, 
                 before_metrics, after_metrics, duration_seconds, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.timestamp,
                result.optimization_type.value,
                result.success,
                result.improvement_percent,
                json.dumps(result.before_metrics),
                json.dumps(result.after_metrics),
                result.duration_seconds,
                result.description
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to save optimization result: {e}")
    
    def start_monitoring(self):
        """Start continuous performance monitoring and optimization"""
        if self.monitoring_active:
            self.logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("📊 Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("⏹️ Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring and optimization loop"""
        last_optimization = time.time()
        
        while self.monitoring_active:
            try:
                # Run monitoring in async context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Collect metrics
                metrics = loop.run_until_complete(self._collect_comprehensive_metrics())
                self.metrics_history.append(metrics)
                
                # Check if optimization is needed
                current_time = time.time()
                optimization_interval = self.config.get('optimization_interval', 300)
                
                if (current_time - last_optimization > optimization_interval and 
                    self.optimization_enabled and 
                    self.config.get('auto_optimization', True)):
                    
                    # Check if optimization is warranted
                    if self._should_optimize(metrics):
                        self.logger.info("🔧 Auto-optimization triggered")
                        results = loop.run_until_complete(self.run_comprehensive_optimization())
                        last_optimization = current_time
                
                loop.close()
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
            
            time.sleep(self.config.get('monitoring_interval', 30))
    
    def _should_optimize(self, metrics: Dict[str, Any]) -> bool:
        """Determine if optimization should be triggered"""
        try:
            # Check memory usage
            if metrics.get('memory_usage_percent', 0) > self.config.get('memory_threshold_mb', 85):
                return True
            
            # Check CPU usage
            if metrics.get('cpu_usage_percent', 0) > self.config.get('cpu_threshold_percent', 80):
                return True
            
            # Check cache hit rate
            if metrics.get('cache_hit_rate', 1.0) < 0.5:
                return True
            
            # Check if performance has degraded significantly from baseline
            if self.baseline_metrics:
                memory_degradation = (metrics.get('process_memory_rss_mb', 0) - 
                                    self.baseline_metrics.get('process_memory_rss_mb', 0)) / \
                                   self.baseline_metrics.get('process_memory_rss_mb', 1)
                
                if memory_degradation > 0.5:  # 50% increase in memory usage
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Optimization check failed: {e}")
            return False
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            # Get recent metrics
            recent_metrics = list(self.metrics_history)[-10:] if self.metrics_history else []
            
            # Calculate averages
            avg_metrics = {}
            if recent_metrics:
                for key in recent_metrics[0].keys():
                    if isinstance(recent_metrics[0][key], (int, float)):
                        values = [m[key] for m in recent_metrics if key in m and isinstance(m[key], (int, float))]
                        if values:
                            avg_metrics[key] = statistics.mean(values)
            
            # Get optimization statistics
            successful_optimizations = [r for r in self.optimization_history if r.success]
            total_improvement = sum(r.improvement_percent for r in successful_optimizations)
            
            # Cache statistics
            cache_stats = self.cache.get_stats()
            
            # Connection pool statistics
            pool_stats = self.connection_pool.get_stats()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_active': self.monitoring_active,
                'optimization_enabled': self.optimization_enabled,
                
                # Current performance
                'current_metrics': avg_metrics,
                'baseline_metrics': self.baseline_metrics,
                
                # Optimization history
                'total_optimizations': len(self.optimization_history),
                'successful_optimizations': len(successful_optimizations),
                'total_improvement_percent': total_improvement,
                'average_improvement': total_improvement / len(successful_optimizations) if successful_optimizations else 0,
                
                # Component statistics
                'cache_stats': cache_stats,
                'connection_pool_stats': pool_stats,
                'thread_pool_size': self.thread_pool._max_workers,
                'process_pool_size': self.process_pool._max_workers,
                
                # System health
                'system_health': self._assess_performance_health(avg_metrics),
                'recommendations': self._generate_recommendations(avg_metrics)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Performance report generation failed: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _assess_performance_health(self, metrics: Dict[str, Any]) -> str:
        """Assess overall performance health"""
        try:
            issues = 0
            
            # Check key metrics
            if metrics.get('memory_usage_percent', 0) > 90:
                issues += 2
            elif metrics.get('memory_usage_percent', 0) > 80:
                issues += 1
            
            if metrics.get('cpu_usage_percent', 0) > 90:
                issues += 2
            elif metrics.get('cpu_usage_percent', 0) > 80:
                issues += 1
            
            if metrics.get('cache_hit_rate', 1.0) < 0.3:
                issues += 2
            elif metrics.get('cache_hit_rate', 1.0) < 0.5:
                issues += 1
            
            if issues >= 4:
                return "critical"
            elif issues >= 2:
                return "degraded"
            elif issues >= 1:
                return "warning"
            else:
                return "healthy"
                
        except Exception:
            return "unknown"
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        try:
            # Memory recommendations
            if metrics.get('memory_usage_percent', 0) > 85:
                recommendations.append("Consider increasing system memory or reducing cache size")
            
            # CPU recommendations
            if metrics.get('cpu_usage_percent', 0) > 85:
                recommendations.append("High CPU usage detected - consider reducing thread pool size")
            
            # Cache recommendations
            hit_rate = metrics.get('cache_hit_rate', 1.0)
            if hit_rate < 0.5:
                recommendations.append("Low cache hit rate - review caching strategy")
            elif hit_rate > 0.95:
                recommendations.append("Excellent cache performance - consider increasing cache size")
            
            # Connection recommendations
            if metrics.get('active_connections', 0) > 80:
                recommendations.append("High connection count - consider connection pooling optimization")
            
            if not recommendations:
                recommendations.append("Performance is optimal - no immediate actions needed")
            
        except Exception as e:
            recommendations.append(f"Unable to generate recommendations: {e}")
        
        return recommendations
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            self.logger.info("🧹 Cleaning up performance optimizer")
            
            # Stop monitoring
            self.stop_monitoring()
            
            # Close connection pool
            await self.connection_pool.close_all()
            
            # Shutdown thread pools
            self.thread_pool.shutdown(wait=True)
            self.process_pool.shutdown(wait=True)
            
            self.logger.info("✅ Performance optimizer cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

# Example usage
async def main():
    """Example usage of the Performance Optimizer"""
    optimizer = PerformanceOptimizer()
    
    try:
        # Start monitoring
        optimizer.start_monitoring()
        
        print("🚀 Performance Optimizer started")
        print("Monitoring system performance and applying optimizations...")
        
        # Let it run for a while
        await asyncio.sleep(30)
        
        # Run manual optimization
        print("\n🔧 Running manual optimization...")
        results = await optimizer.run_comprehensive_optimization()
        
        # Display results
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.optimization_type.value}: {result.improvement_percent:.1f}% improvement")
        
        # Generate report
        report = optimizer.get_performance_report()
        print(f"\n📊 System Health: {report['system_health'].upper()}")
        print(f"🎯 Cache Hit Rate: {report['cache_stats']['hit_rate']*100:.1f}%")
        print(f"🔗 Active Connections: {report['connection_pool_stats']['total_connections']}")
        
        print("\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
    finally:
        # Cleanup
        await optimizer.cleanup()
        print("\n⏹️ Performance Optimizer stopped")

if __name__ == "__main__":
    print("🤖 TradeBot Sentinel - Advanced Performance Optimizer")
    print("🚀 Intelligent resource management and performance optimization")
    print("="*70)
    
    asyncio.run(main())