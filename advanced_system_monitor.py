#!/usr/bin/env python3
"""
Advanced System Monitor for TradeBot Sentinel
Provides comprehensive monitoring, alerting, and performance analytics
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import psutil
import aiofiles
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_system_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class SystemMetrics:
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_processes: int
    system_load: float

@dataclass
class ComponentHealth:
    name: str
    status: ComponentStatus
    last_check: str
    response_time: float
    error_count: int
    success_rate: float
    metadata: Dict[str, Any]

@dataclass
class Alert:
    id: str
    level: AlertLevel
    component: str
    message: str
    timestamp: str
    resolved: bool = False
    resolution_time: Optional[str] = None

class AdvancedSystemMonitor:
    def __init__(self, db_path: str = "system_monitor.db", check_interval: int = 30):
        self.db_path = db_path
        self.check_interval = check_interval
        self.db_connection = None
        self.monitoring_active = False
        self.components = {}
        self.alerts = []
        self.performance_history = []
        
        # Thresholds for alerts
        self.thresholds = {
            'cpu_usage': {'warning': 70, 'critical': 85},
            'memory_usage': {'warning': 80, 'critical': 90},
            'disk_usage': {'warning': 85, 'critical': 95},
            'response_time': {'warning': 5.0, 'critical': 10.0},
            'error_rate': {'warning': 0.05, 'critical': 0.10}
        }
        
    async def initialize(self) -> None:
        """Initialize the monitoring system"""
        try:
            await self.init_database()
            await self.register_components()
            logger.info("Advanced System Monitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize system monitor: {e}")
            raise
    
    async def init_database(self) -> None:
        """Initialize SQLite database for monitoring data"""
        try:
            self.db_connection = sqlite3.connect(self.db_path)
            cursor = self.db_connection.cursor()
            
            # System metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_io TEXT,
                    active_processes INTEGER,
                    system_load REAL
                )
            ''')
            
            # Component health table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS component_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_check TEXT NOT NULL,
                    response_time REAL,
                    error_count INTEGER,
                    success_rate REAL,
                    metadata TEXT
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_time TEXT
                )
            ''')
            
            # Performance analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    component TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    timestamp TEXT
                )
            ''')
            
            self.db_connection.commit()
            logger.info("Database initialized for system monitoring")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def register_components(self) -> None:
        """Register system components for monitoring"""
        self.components = {
            'tradebot_sentinel': {
                'type': 'automation',
                'health_check': self.check_tradebot_health,
                'critical': True
            },
            'database': {
                'type': 'storage',
                'health_check': self.check_database_health,
                'critical': True
            },
            'network_interception': {
                'type': 'network',
                'health_check': self.check_network_health,
                'critical': True
            },
            'session_manager': {
                'type': 'session',
                'health_check': self.check_session_health,
                'critical': False
            },
            'file_system': {
                'type': 'storage',
                'health_check': self.check_filesystem_health,
                'critical': False
            }
        }
        
        logger.info(f"Registered {len(self.components)} components for monitoring")
    
    async def start_monitoring(self) -> None:
        """Start the monitoring loop"""
        self.monitoring_active = True
        logger.info("🔍 Starting advanced system monitoring...")
        
        try:
            while self.monitoring_active:
                # Collect system metrics
                await self.collect_system_metrics()
                
                # Check component health
                await self.check_all_components()
                
                # Process alerts
                await self.process_alerts()
                
                # Generate performance analytics
                await self.generate_analytics()
                
                # Cleanup old data
                await self.cleanup_old_data()
                
                await asyncio.sleep(self.check_interval)
                
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
        finally:
            self.monitoring_active = False
            logger.info("System monitoring stopped")
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Active processes
            active_processes = len(psutil.pids())
            
            # System load
            try:
                system_load = psutil.getloadavg()[0]  # 1-minute load average
            except AttributeError:
                system_load = cpu_usage / 100  # Fallback for Windows
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_processes=active_processes,
                system_load=system_load
            )
            
            # Store in database
            await self.store_system_metrics(metrics)
            
            # Check for threshold violations
            await self.check_metric_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    async def store_system_metrics(self, metrics: SystemMetrics) -> None:
        """Store system metrics in database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO system_metrics 
                (timestamp, cpu_usage, memory_usage, disk_usage, network_io, active_processes, system_load)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp,
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.disk_usage,
                json.dumps(metrics.network_io),
                metrics.active_processes,
                metrics.system_load
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")
    
    async def check_metric_thresholds(self, metrics: SystemMetrics) -> None:
        """Check if metrics exceed defined thresholds"""
        try:
            # CPU usage check
            if metrics.cpu_usage > self.thresholds['cpu_usage']['critical']:
                await self.create_alert(
                    AlertLevel.CRITICAL,
                    'system',
                    f"Critical CPU usage: {metrics.cpu_usage:.1f}%"
                )
            elif metrics.cpu_usage > self.thresholds['cpu_usage']['warning']:
                await self.create_alert(
                    AlertLevel.WARNING,
                    'system',
                    f"High CPU usage: {metrics.cpu_usage:.1f}%"
                )
            
            # Memory usage check
            if metrics.memory_usage > self.thresholds['memory_usage']['critical']:
                await self.create_alert(
                    AlertLevel.CRITICAL,
                    'system',
                    f"Critical memory usage: {metrics.memory_usage:.1f}%"
                )
            elif metrics.memory_usage > self.thresholds['memory_usage']['warning']:
                await self.create_alert(
                    AlertLevel.WARNING,
                    'system',
                    f"High memory usage: {metrics.memory_usage:.1f}%"
                )
            
            # Disk usage check
            if metrics.disk_usage > self.thresholds['disk_usage']['critical']:
                await self.create_alert(
                    AlertLevel.CRITICAL,
                    'system',
                    f"Critical disk usage: {metrics.disk_usage:.1f}%"
                )
            elif metrics.disk_usage > self.thresholds['disk_usage']['warning']:
                await self.create_alert(
                    AlertLevel.WARNING,
                    'system',
                    f"High disk usage: {metrics.disk_usage:.1f}%"
                )
                
        except Exception as e:
            logger.error(f"Error checking metric thresholds: {e}")
    
    async def check_all_components(self) -> None:
        """Check health of all registered components"""
        for component_name, component_config in self.components.items():
            try:
                health_check = component_config['health_check']
                health = await health_check()
                
                # Store component health
                await self.store_component_health(health)
                
                # Check for component issues
                if health.status == ComponentStatus.FAILED and component_config['critical']:
                    await self.create_alert(
                        AlertLevel.CRITICAL,
                        component_name,
                        f"Critical component failure: {health.name}"
                    )
                elif health.status == ComponentStatus.DEGRADED:
                    await self.create_alert(
                        AlertLevel.WARNING,
                        component_name,
                        f"Component degraded: {health.name}"
                    )
                    
            except Exception as e:
                logger.error(f"Error checking component {component_name}: {e}")
                await self.create_alert(
                    AlertLevel.CRITICAL,
                    component_name,
                    f"Health check failed: {str(e)}"
                )
    
    async def check_tradebot_health(self) -> ComponentHealth:
        """Check TradeBot Sentinel health"""
        try:
            start_time = time.time()
            
            # Check if trade files exist and are recent
            trade_files = ['trade.sh', 'trade_request_full.py']
            files_exist = all(Path(f).exists() for f in trade_files)
            
            # Check database connectivity
            db_healthy = self.db_connection is not None
            
            response_time = time.time() - start_time
            
            if files_exist and db_healthy:
                status = ComponentStatus.HEALTHY
            elif files_exist or db_healthy:
                status = ComponentStatus.DEGRADED
            else:
                status = ComponentStatus.FAILED
            
            return ComponentHealth(
                name="tradebot_sentinel",
                status=status,
                last_check=datetime.now().isoformat(),
                response_time=response_time,
                error_count=0,
                success_rate=1.0 if status == ComponentStatus.HEALTHY else 0.5,
                metadata={'files_exist': files_exist, 'db_healthy': db_healthy}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="tradebot_sentinel",
                status=ComponentStatus.FAILED,
                last_check=datetime.now().isoformat(),
                response_time=0.0,
                error_count=1,
                success_rate=0.0,
                metadata={'error': str(e)}
            )
    
    async def check_database_health(self) -> ComponentHealth:
        """Check database health"""
        try:
            start_time = time.time()
            
            # Test database connection
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            response_time = time.time() - start_time
            
            return ComponentHealth(
                name="database",
                status=ComponentStatus.HEALTHY,
                last_check=datetime.now().isoformat(),
                response_time=response_time,
                error_count=0,
                success_rate=1.0,
                metadata={'connection': 'active'}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=ComponentStatus.FAILED,
                last_check=datetime.now().isoformat(),
                response_time=0.0,
                error_count=1,
                success_rate=0.0,
                metadata={'error': str(e)}
            )
    
    async def check_network_health(self) -> ComponentHealth:
        """Check network connectivity health"""
        try:
            start_time = time.time()
            
            # Check network interfaces
            network_stats = psutil.net_io_counters()
            interfaces_active = network_stats.bytes_sent > 0 and network_stats.bytes_recv > 0
            
            response_time = time.time() - start_time
            
            status = ComponentStatus.HEALTHY if interfaces_active else ComponentStatus.DEGRADED
            
            return ComponentHealth(
                name="network_interception",
                status=status,
                last_check=datetime.now().isoformat(),
                response_time=response_time,
                error_count=0,
                success_rate=1.0 if interfaces_active else 0.5,
                metadata={'interfaces_active': interfaces_active}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="network_interception",
                status=ComponentStatus.FAILED,
                last_check=datetime.now().isoformat(),
                response_time=0.0,
                error_count=1,
                success_rate=0.0,
                metadata={'error': str(e)}
            )
    
    async def check_session_health(self) -> ComponentHealth:
        """Check session management health"""
        try:
            start_time = time.time()
            
            # Check if session files exist
            session_files = list(Path('.').glob('session_*.json'))
            sessions_active = len(session_files) > 0
            
            response_time = time.time() - start_time
            
            status = ComponentStatus.HEALTHY if sessions_active else ComponentStatus.DEGRADED
            
            return ComponentHealth(
                name="session_manager",
                status=status,
                last_check=datetime.now().isoformat(),
                response_time=response_time,
                error_count=0,
                success_rate=1.0 if sessions_active else 0.5,
                metadata={'active_sessions': len(session_files)}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="session_manager",
                status=ComponentStatus.FAILED,
                last_check=datetime.now().isoformat(),
                response_time=0.0,
                error_count=1,
                success_rate=0.0,
                metadata={'error': str(e)}
            )
    
    async def check_filesystem_health(self) -> ComponentHealth:
        """Check filesystem health"""
        try:
            start_time = time.time()
            
            # Check disk space and write permissions
            disk_usage = psutil.disk_usage('.')
            free_space_gb = disk_usage.free / (1024**3)
            
            # Test write permissions
            test_file = Path('health_check_test.tmp')
            try:
                test_file.write_text('test')
                test_file.unlink()
                write_permissions = True
            except:
                write_permissions = False
            
            response_time = time.time() - start_time
            
            if free_space_gb > 1.0 and write_permissions:
                status = ComponentStatus.HEALTHY
            elif free_space_gb > 0.5 or write_permissions:
                status = ComponentStatus.DEGRADED
            else:
                status = ComponentStatus.FAILED
            
            return ComponentHealth(
                name="file_system",
                status=status,
                last_check=datetime.now().isoformat(),
                response_time=response_time,
                error_count=0,
                success_rate=1.0 if status == ComponentStatus.HEALTHY else 0.5,
                metadata={
                    'free_space_gb': free_space_gb,
                    'write_permissions': write_permissions
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="file_system",
                status=ComponentStatus.FAILED,
                last_check=datetime.now().isoformat(),
                response_time=0.0,
                error_count=1,
                success_rate=0.0,
                metadata={'error': str(e)}
            )
    
    async def store_component_health(self, health: ComponentHealth) -> None:
        """Store component health data"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO component_health 
                (name, status, last_check, response_time, error_count, success_rate, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                health.name,
                health.status.value,
                health.last_check,
                health.response_time,
                health.error_count,
                health.success_rate,
                json.dumps(health.metadata)
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing component health: {e}")
    
    async def create_alert(self, level: AlertLevel, component: str, message: str) -> None:
        """Create and store a new alert"""
        try:
            alert_id = f"{component}_{level.value}_{int(time.time())}"
            
            alert = Alert(
                id=alert_id,
                level=level,
                component=component,
                message=message,
                timestamp=datetime.now().isoformat()
            )
            
            # Store in database
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO alerts 
                (id, level, component, message, timestamp, resolved)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                alert.id,
                alert.level.value,
                alert.component,
                alert.message,
                alert.timestamp,
                alert.resolved
            ))
            self.db_connection.commit()
            
            # Add to active alerts
            self.alerts.append(alert)
            
            # Log alert
            log_level = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.CRITICAL: logging.CRITICAL,
                AlertLevel.EMERGENCY: logging.CRITICAL
            }.get(level, logging.INFO)
            
            logger.log(log_level, f"🚨 ALERT [{level.value.upper()}] {component}: {message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def process_alerts(self) -> None:
        """Process and manage active alerts"""
        try:
            # Auto-resolve old alerts
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            for alert in self.alerts[:]:
                alert_time = datetime.fromisoformat(alert.timestamp)
                if alert_time < cutoff_time and not alert.resolved:
                    await self.resolve_alert(alert.id)
            
            # Check for critical alert patterns
            critical_alerts = [a for a in self.alerts if a.level == AlertLevel.CRITICAL and not a.resolved]
            if len(critical_alerts) > 3:
                await self.create_alert(
                    AlertLevel.EMERGENCY,
                    'system',
                    f"Multiple critical alerts detected: {len(critical_alerts)} active"
                )
                
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
    
    async def resolve_alert(self, alert_id: str) -> None:
        """Resolve an active alert"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                UPDATE alerts 
                SET resolved = TRUE, resolution_time = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), alert_id))
            self.db_connection.commit()
            
            # Remove from active alerts
            self.alerts = [a for a in self.alerts if a.id != alert_id]
            
            logger.info(f"Alert resolved: {alert_id}")
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
    
    async def generate_analytics(self) -> None:
        """Generate performance analytics and insights"""
        try:
            # Calculate system performance trends
            cursor = self.db_connection.cursor()
            
            # Get recent metrics
            cursor.execute('''
                SELECT cpu_usage, memory_usage, disk_usage, timestamp
                FROM system_metrics 
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
            ''')
            
            recent_metrics = cursor.fetchall()
            
            if recent_metrics:
                avg_cpu = sum(m[0] for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m[1] for m in recent_metrics) / len(recent_metrics)
                avg_disk = sum(m[2] for m in recent_metrics) / len(recent_metrics)
                
                # Store analytics
                analytics_data = {
                    'avg_cpu_1h': avg_cpu,
                    'avg_memory_1h': avg_memory,
                    'avg_disk_1h': avg_disk,
                    'sample_count': len(recent_metrics)
                }
                
                cursor.execute('''
                    INSERT INTO performance_analytics 
                    (session_id, component, metric_name, metric_value, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    'system_monitor',
                    'system',
                    'hourly_averages',
                    json.dumps(analytics_data),
                    datetime.now().isoformat()
                ))
                
                self.db_connection.commit()
                
                logger.debug(f"Analytics generated: CPU={avg_cpu:.1f}%, Memory={avg_memory:.1f}%, Disk={avg_disk:.1f}%")
                
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
    
    async def cleanup_old_data(self) -> None:
        """Clean up old monitoring data"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            
            cursor = self.db_connection.cursor()
            
            # Clean old system metrics
            cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_date,))
            
            # Clean old component health records
            cursor.execute('DELETE FROM component_health WHERE last_check < ?', (cutoff_date,))
            
            # Clean resolved alerts older than 24 hours
            alert_cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            cursor.execute('DELETE FROM alerts WHERE resolved = TRUE AND resolution_time < ?', (alert_cutoff,))
            
            self.db_connection.commit()
            
            logger.debug("Old monitoring data cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status report"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get latest system metrics
            cursor.execute('''
                SELECT * FROM system_metrics 
                ORDER BY timestamp DESC LIMIT 1
            ''')
            latest_metrics = cursor.fetchone()
            
            # Get component health summary
            cursor.execute('''
                SELECT name, status, response_time, success_rate
                FROM component_health 
                WHERE last_check > datetime('now', '-5 minutes')
                GROUP BY name
                HAVING last_check = MAX(last_check)
            ''')
            component_health = cursor.fetchall()
            
            # Get active alerts
            cursor.execute('''
                SELECT level, component, message, timestamp
                FROM alerts 
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
            ''')
            active_alerts = cursor.fetchall()
            
            status_report = {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': {
                    'cpu_usage': latest_metrics[2] if latest_metrics else 0,
                    'memory_usage': latest_metrics[3] if latest_metrics else 0,
                    'disk_usage': latest_metrics[4] if latest_metrics else 0,
                    'active_processes': latest_metrics[6] if latest_metrics else 0
                },
                'component_health': [
                    {
                        'name': comp[0],
                        'status': comp[1],
                        'response_time': comp[2],
                        'success_rate': comp[3]
                    } for comp in component_health
                ],
                'active_alerts': [
                    {
                        'level': alert[0],
                        'component': alert[1],
                        'message': alert[2],
                        'timestamp': alert[3]
                    } for alert in active_alerts
                ],
                'overall_health': 'healthy' if not active_alerts else 'degraded'
            }
            
            return status_report
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    async def stop_monitoring(self) -> None:
        """Stop the monitoring system"""
        self.monitoring_active = False
        if self.db_connection:
            self.db_connection.close()
        logger.info("Advanced System Monitor stopped")

async def main():
    """Main function for standalone monitoring"""
    monitor = AdvancedSystemMonitor()
    
    try:
        await monitor.initialize()
        
        # Start monitoring in background
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # Run for demonstration (in production, this would run continuously)
        await asyncio.sleep(60)
        
        # Get status report
        status = await monitor.get_system_status()
        print(json.dumps(status, indent=2))
        
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())