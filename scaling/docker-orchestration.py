#!/usr/bin/env python3
"""
AI Trading Sentinel - Docker-based Multi-Account Orchestration
Provides containerized isolation for trading accounts with complete resource control,
security isolation, and scalable deployment across multiple nodes.
"""

import asyncio
import docker
import json
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

import yaml
import redis
from jinja2 import Template

# =============================================================================
# CONFIGURATION AND ENUMS
# =============================================================================

class ContainerStatus(Enum):
    """Container status enumeration"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"

class NetworkMode(Enum):
    """Network isolation modes"""
    BRIDGE = "bridge"
    HOST = "host"
    NONE = "none"
    CUSTOM = "custom"

class StorageType(Enum):
    """Storage types for containers"""
    BIND = "bind"
    VOLUME = "volume"
    TMPFS = "tmpfs"

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ContainerResources:
    """Container resource limits"""
    cpu_limit: float = 0.5  # CPU cores
    memory_limit: str = "1g"  # Memory limit (e.g., "512m", "1g")
    memory_swap: str = "2g"  # Swap limit
    memory_reservation: str = "256m"  # Memory reservation
    cpu_shares: int = 1024  # CPU shares (relative weight)
    cpu_period: int = 100000  # CPU period in microseconds
    cpu_quota: int = 50000  # CPU quota in microseconds
    blkio_weight: int = 500  # Block I/O weight (10-1000)
    device_read_bps: Dict[str, str] = field(default_factory=dict)  # Device read rate limit
    device_write_bps: Dict[str, str] = field(default_factory=dict)  # Device write rate limit
    ulimits: List[Dict[str, Any]] = field(default_factory=list)  # Process limits
    pids_limit: int = 1000  # Maximum number of processes

@dataclass
class ContainerNetwork:
    """Container network configuration"""
    mode: NetworkMode = NetworkMode.BRIDGE
    custom_network: Optional[str] = None
    port_bindings: Dict[str, str] = field(default_factory=dict)  # container_port: host_port
    expose_ports: List[str] = field(default_factory=list)
    hostname: Optional[str] = None
    dns: List[str] = field(default_factory=lambda: ["8.8.8.8", "8.8.4.4"])
    dns_search: List[str] = field(default_factory=list)
    extra_hosts: Dict[str, str] = field(default_factory=dict)
    mac_address: Optional[str] = None
    network_disabled: bool = False

@dataclass
class ContainerStorage:
    """Container storage configuration"""
    volumes: Dict[str, Dict[str, str]] = field(default_factory=dict)  # host_path: {"bind": container_path, "mode": "rw"}
    tmpfs: Dict[str, str] = field(default_factory=dict)  # mount_point: options
    working_dir: str = "/app"
    user: Optional[str] = None
    group_add: List[str] = field(default_factory=list)
    read_only: bool = False
    security_opt: List[str] = field(default_factory=list)
    cap_add: List[str] = field(default_factory=list)
    cap_drop: List[str] = field(default_factory=lambda: ["ALL"])
    privileged: bool = False

@dataclass
class ContainerConfig:
    """Complete container configuration"""
    account_id: str
    image: str = "trading-sentinel:latest"
    name: Optional[str] = None
    command: Optional[List[str]] = None
    environment: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    resources: ContainerResources = field(default_factory=ContainerResources)
    network: ContainerNetwork = field(default_factory=ContainerNetwork)
    storage: ContainerStorage = field(default_factory=ContainerStorage)
    restart_policy: Dict[str, Any] = field(default_factory=lambda: {"Name": "unless-stopped", "MaximumRetryCount": 3})
    health_check: Optional[Dict[str, Any]] = None
    logging: Dict[str, Any] = field(default_factory=lambda: {"Type": "json-file", "Config": {"max-size": "10m", "max-file": "3"}})
    auto_remove: bool = False
    detach: bool = True
    stdin_open: bool = False
    tty: bool = False

@dataclass
class ContainerMetrics:
    """Container runtime metrics"""
    account_id: str
    container_id: str
    status: ContainerStatus
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    memory_limit_mb: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    block_read_bytes: int = 0
    block_write_bytes: int = 0
    pids: int = 0
    uptime_seconds: int = 0
    restart_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

# =============================================================================
# DOCKER IMAGE BUILDER
# =============================================================================

class DockerImageBuilder:
    """Builds optimized Docker images for trading accounts"""
    
    def __init__(self, docker_client: docker.DockerClient):
        self.docker_client = docker_client
        self.logger = logging.getLogger(__name__)
    
    def build_base_image(self, tag: str = "trading-sentinel-base:latest") -> bool:
        """Build base trading sentinel image"""
        try:
            dockerfile_content = self._generate_base_dockerfile()
            
            # Create temporary build context
            with tempfile.TemporaryDirectory() as build_dir:
                dockerfile_path = Path(build_dir) / "Dockerfile"
                dockerfile_path.write_text(dockerfile_content)
                
                # Copy application files
                self._copy_application_files(build_dir)
                
                # Build image
                self.logger.info(f"Building base image: {tag}")
                image, build_logs = self.docker_client.images.build(
                    path=build_dir,
                    tag=tag,
                    rm=True,
                    forcerm=True,
                    pull=True,
                    nocache=False
                )
                
                # Log build output
                for log in build_logs:
                    if 'stream' in log:
                        self.logger.debug(log['stream'].strip())
                
                self.logger.info(f"Base image built successfully: {image.id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error building base image: {e}")
            return False
    
    def build_account_image(self, account_id: str, base_tag: str = "trading-sentinel-base:latest", 
                          custom_config: Optional[Dict[str, Any]] = None) -> bool:
        """Build account-specific image"""
        try:
            tag = f"trading-sentinel-{account_id}:latest"
            dockerfile_content = self._generate_account_dockerfile(base_tag, account_id, custom_config)
            
            with tempfile.TemporaryDirectory() as build_dir:
                dockerfile_path = Path(build_dir) / "Dockerfile"
                dockerfile_path.write_text(dockerfile_content)
                
                # Copy account-specific files
                self._copy_account_files(build_dir, account_id, custom_config)
                
                # Build image
                self.logger.info(f"Building account image: {tag}")
                image, build_logs = self.docker_client.images.build(
                    path=build_dir,
                    tag=tag,
                    rm=True,
                    forcerm=True
                )
                
                self.logger.info(f"Account image built successfully: {image.id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error building account image for {account_id}: {e}")
            return False
    
    def _generate_base_dockerfile(self) -> str:
        """Generate base Dockerfile"""
        return """
# AI Trading Sentinel - Base Image
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Playwright
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create non-root user
RUN groupadd -r trading && useradd -r -g trading -d /app -s /bin/bash trading

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Set ownership
RUN chown -R trading:trading /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/cache /app/config \
    && chown -R trading:trading /app/logs /app/data /app/cache /app/config

# Switch to non-root user
USER trading

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Default command
CMD ["python", "main.py"]
"""
    
    def _generate_account_dockerfile(self, base_tag: str, account_id: str, 
                                   custom_config: Optional[Dict[str, Any]] = None) -> str:
        """Generate account-specific Dockerfile"""
        template = Template("""
# AI Trading Sentinel - Account Specific Image
FROM {{ base_tag }}

# Account-specific environment variables
ENV ACCOUNT_ID={{ account_id }}
ENV ACCOUNT_NAME="{{ account_name }}"
ENV BROKER="{{ broker }}"
ENV STRATEGY="{{ strategy }}"

# Copy account-specific configuration
COPY config/ /app/config/
COPY scripts/ /app/scripts/

# Set account-specific permissions
USER root
RUN chown -R trading:trading /app/config /app/scripts
USER trading

# Account-specific health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from health_check import check_account_health; check_account_health('{{ account_id }}')"

# Account-specific startup command
CMD ["python", "main.py", "--account-id", "{{ account_id }}"]
""")
        
        config = custom_config or {}
        return template.render(
            base_tag=base_tag,
            account_id=account_id,
            account_name=config.get('account_name', f'Account {account_id}'),
            broker=config.get('broker', 'default'),
            strategy=config.get('strategy', 'default')
        )
    
    def _copy_application_files(self, build_dir: str):
        """Copy application files to build directory"""
        try:
            # Copy main application files
            app_files = [
                'main.py',
                'requirements.txt',
                'config/',
                'src/',
                'strategies/',
                'utils/'
            ]
            
            for file_path in app_files:
                src = Path(file_path)
                if src.exists():
                    dst = Path(build_dir) / file_path
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        
        except Exception as e:
            self.logger.error(f"Error copying application files: {e}")
    
    def _copy_account_files(self, build_dir: str, account_id: str, custom_config: Optional[Dict[str, Any]]):
        """Copy account-specific files to build directory"""
        try:
            # Create config directory
            config_dir = Path(build_dir) / "config"
            config_dir.mkdir(exist_ok=True)
            
            # Create account configuration
            account_config = {
                'account_id': account_id,
                'timestamp': datetime.utcnow().isoformat(),
                **(custom_config or {})
            }
            
            config_file = config_dir / "account.json"
            config_file.write_text(json.dumps(account_config, indent=2))
            
            # Create scripts directory
            scripts_dir = Path(build_dir) / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            
            # Create startup script
            startup_script = scripts_dir / "startup.sh"
            startup_script.write_text(f"""
#!/bin/bash
set -e

echo "Starting trading account: {account_id}"
echo "Configuration loaded from: /app/config/account.json"

# Initialize account-specific setup
python -c "from setup import initialize_account; initialize_account('{account_id}')"

# Start the trading application
exec "$@"
""")
            startup_script.chmod(0o755)
            
        except Exception as e:
            self.logger.error(f"Error copying account files: {e}")

# =============================================================================
# CONTAINER MANAGER
# =============================================================================

class ContainerManager:
    """Manages individual Docker containers for trading accounts"""
    
    def __init__(self, docker_client: docker.DockerClient, redis_client: redis.Redis):
        self.docker_client = docker_client
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        self.containers: Dict[str, docker.models.containers.Container] = {}
    
    def create_container(self, config: ContainerConfig) -> bool:
        """Create a new container"""
        try:
            container_name = config.name or f"trading-{config.account_id}"
            
            # Check if container already exists
            try:
                existing = self.docker_client.containers.get(container_name)
                if existing:
                    self.logger.warning(f"Container {container_name} already exists")
                    return False
            except docker.errors.NotFound:
                pass
            
            # Prepare container configuration
            container_config = self._prepare_container_config(config)
            
            # Create container
            self.logger.info(f"Creating container: {container_name}")
            container = self.docker_client.containers.create(
                image=config.image,
                name=container_name,
                **container_config
            )
            
            self.containers[config.account_id] = container
            
            # Store container metadata
            self._store_container_metadata(config.account_id, container, config)
            
            self.logger.info(f"Container created successfully: {container.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating container for {config.account_id}: {e}")
            return False
    
    def start_container(self, account_id: str) -> bool:
        """Start a container"""
        try:
            container = self._get_container(account_id)
            if not container:
                return False
            
            if container.status == 'running':
                self.logger.warning(f"Container for {account_id} is already running")
                return True
            
            self.logger.info(f"Starting container for account: {account_id}")
            container.start()
            
            # Wait for container to be ready
            self._wait_for_container_ready(container)
            
            self.logger.info(f"Container started successfully: {container.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting container for {account_id}: {e}")
            return False
    
    def stop_container(self, account_id: str, timeout: int = 30) -> bool:
        """Stop a container"""
        try:
            container = self._get_container(account_id)
            if not container:
                return False
            
            if container.status != 'running':
                self.logger.warning(f"Container for {account_id} is not running")
                return True
            
            self.logger.info(f"Stopping container for account: {account_id}")
            container.stop(timeout=timeout)
            
            self.logger.info(f"Container stopped successfully: {container.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping container for {account_id}: {e}")
            return False
    
    def restart_container(self, account_id: str, timeout: int = 30) -> bool:
        """Restart a container"""
        try:
            container = self._get_container(account_id)
            if not container:
                return False
            
            self.logger.info(f"Restarting container for account: {account_id}")
            container.restart(timeout=timeout)
            
            # Wait for container to be ready
            self._wait_for_container_ready(container)
            
            self.logger.info(f"Container restarted successfully: {container.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting container for {account_id}: {e}")
            return False
    
    def pause_container(self, account_id: str) -> bool:
        """Pause a container"""
        try:
            container = self._get_container(account_id)
            if not container:
                return False
            
            if container.status != 'running':
                self.logger.warning(f"Container for {account_id} is not running")
                return False
            
            self.logger.info(f"Pausing container for account: {account_id}")
            container.pause()
            
            self.logger.info(f"Container paused successfully: {container.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing container for {account_id}: {e}")
            return False
    
    def unpause_container(self, account_id: str) -> bool:
        """Unpause a container"""
        try:
            container = self._get_container(account_id)
            if not container:
                return False
            
            if container.status != 'paused':
                self.logger.warning(f"Container for {account_id} is not paused")
                return False
            
            self.logger.info(f"Unpausing container for account: {account_id}")
            container.unpause()
            
            self.logger.info(f"Container unpaused successfully: {container.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unpausing container for {account_id}: {e}")
            return False
    
    def remove_container(self, account_id: str, force: bool = False) -> bool:
        """Remove a container"""
        try:
            container = self._get_container(account_id)
            if not container:
                return True
            
            # Stop container if running
            if container.status == 'running':
                self.stop_container(account_id)
            
            self.logger.info(f"Removing container for account: {account_id}")
            container.remove(force=force)
            
            # Remove from tracking
            if account_id in self.containers:
                del self.containers[account_id]
            
            # Remove metadata
            self._remove_container_metadata(account_id)
            
            self.logger.info(f"Container removed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing container for {account_id}: {e}")
            return False
    
    def get_container_metrics(self, account_id: str) -> Optional[ContainerMetrics]:
        """Get container metrics"""
        try:
            container = self._get_container(account_id)
            if not container:
                return None
            
            # Refresh container info
            container.reload()
            
            # Get container stats
            stats = container.stats(stream=False)
            
            # Calculate metrics
            metrics = self._calculate_metrics(account_id, container, stats)
            
            # Store metrics in Redis
            self._store_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting metrics for {account_id}: {e}")
            return None
    
    def get_container_logs(self, account_id: str, tail: int = 100) -> Optional[str]:
        """Get container logs"""
        try:
            container = self._get_container(account_id)
            if not container:
                return None
            
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting logs for {account_id}: {e}")
            return None
    
    def execute_command(self, account_id: str, command: List[str]) -> Optional[str]:
        """Execute command in container"""
        try:
            container = self._get_container(account_id)
            if not container:
                return None
            
            if container.status != 'running':
                self.logger.warning(f"Container for {account_id} is not running")
                return None
            
            result = container.exec_run(command)
            return result.output.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error executing command in {account_id}: {e}")
            return None
    
    def _get_container(self, account_id: str) -> Optional[docker.models.containers.Container]:
        """Get container by account ID"""
        try:
            if account_id in self.containers:
                container = self.containers[account_id]
                container.reload()
                return container
            
            # Try to find by name
            container_name = f"trading-{account_id}"
            try:
                container = self.docker_client.containers.get(container_name)
                self.containers[account_id] = container
                return container
            except docker.errors.NotFound:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting container for {account_id}: {e}")
            return None
    
    def _prepare_container_config(self, config: ContainerConfig) -> Dict[str, Any]:
        """Prepare Docker container configuration"""
        container_config = {
            'detach': config.detach,
            'stdin_open': config.stdin_open,
            'tty': config.tty,
            'environment': config.environment,
            'labels': {
                'ai.trading.sentinel.account_id': config.account_id,
                'ai.trading.sentinel.created': datetime.utcnow().isoformat(),
                **config.labels
            },
            'restart_policy': config.restart_policy,
            'auto_remove': config.auto_remove,
            'working_dir': config.storage.working_dir,
            'user': config.storage.user,
            'group_add': config.storage.group_add,
            'read_only': config.storage.read_only,
            'security_opt': config.storage.security_opt,
            'cap_add': config.storage.cap_add,
            'cap_drop': config.storage.cap_drop,
            'privileged': config.storage.privileged,
            'logging': config.logging,
        }
        
        # Add command if specified
        if config.command:
            container_config['command'] = config.command
        
        # Add resource limits
        container_config.update(self._prepare_resource_config(config.resources))
        
        # Add network configuration
        container_config.update(self._prepare_network_config(config.network))
        
        # Add storage configuration
        container_config.update(self._prepare_storage_config(config.storage))
        
        # Add health check
        if config.health_check:
            container_config['healthcheck'] = config.health_check
        
        return container_config
    
    def _prepare_resource_config(self, resources: ContainerResources) -> Dict[str, Any]:
        """Prepare resource configuration"""
        config = {
            'mem_limit': resources.memory_limit,
            'memswap_limit': resources.memory_swap,
            'mem_reservation': resources.memory_reservation,
            'cpu_shares': resources.cpu_shares,
            'cpu_period': resources.cpu_period,
            'cpu_quota': resources.cpu_quota,
            'blkio_weight': resources.blkio_weight,
            'pids_limit': resources.pids_limit,
        }
        
        # Add CPU limit
        if resources.cpu_limit:
            config['nano_cpus'] = int(resources.cpu_limit * 1e9)
        
        # Add device limits
        if resources.device_read_bps:
            config['device_read_bps'] = [{'Path': path, 'Rate': rate} 
                                       for path, rate in resources.device_read_bps.items()]
        
        if resources.device_write_bps:
            config['device_write_bps'] = [{'Path': path, 'Rate': rate} 
                                        for path, rate in resources.device_write_bps.items()]
        
        # Add ulimits
        if resources.ulimits:
            config['ulimits'] = resources.ulimits
        
        return config
    
    def _prepare_network_config(self, network: ContainerNetwork) -> Dict[str, Any]:
        """Prepare network configuration"""
        config = {
            'network_disabled': network.network_disabled,
            'dns': network.dns,
            'dns_search': network.dns_search,
            'extra_hosts': network.extra_hosts,
        }
        
        # Add network mode
        if network.mode == NetworkMode.HOST:
            config['network_mode'] = 'host'
        elif network.mode == NetworkMode.NONE:
            config['network_mode'] = 'none'
        elif network.mode == NetworkMode.CUSTOM and network.custom_network:
            config['network'] = network.custom_network
        
        # Add port bindings
        if network.port_bindings:
            config['ports'] = network.port_bindings
        
        # Add hostname
        if network.hostname:
            config['hostname'] = network.hostname
        
        # Add MAC address
        if network.mac_address:
            config['mac_address'] = network.mac_address
        
        return config
    
    def _prepare_storage_config(self, storage: ContainerStorage) -> Dict[str, Any]:
        """Prepare storage configuration"""
        config = {}
        
        # Add volumes
        if storage.volumes:
            config['volumes'] = storage.volumes
        
        # Add tmpfs
        if storage.tmpfs:
            config['tmpfs'] = storage.tmpfs
        
        return config
    
    def _wait_for_container_ready(self, container: docker.models.containers.Container, timeout: int = 60):
        """Wait for container to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            container.reload()
            
            if container.status == 'running':
                # Check health if health check is configured
                if hasattr(container.attrs['Config'], 'Healthcheck'):
                    health = container.attrs.get('State', {}).get('Health', {})
                    if health.get('Status') == 'healthy':
                        return
                else:
                    return
            
            time.sleep(1)
        
        raise TimeoutError(f"Container {container.id} did not become ready within {timeout} seconds")
    
    def _calculate_metrics(self, account_id: str, container: docker.models.containers.Container, 
                         stats: Dict[str, Any]) -> ContainerMetrics:
        """Calculate container metrics from stats"""
        # CPU usage calculation
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        
        cpu_usage_percent = 0.0
        if system_delta > 0:
            cpu_usage_percent = (cpu_delta / system_delta) * \
                              len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
        
        # Memory usage
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        memory_usage_mb = memory_usage / (1024 * 1024)
        memory_limit_mb = memory_limit / (1024 * 1024)
        
        # Network I/O
        networks = stats.get('networks', {})
        network_rx_bytes = sum(net['rx_bytes'] for net in networks.values())
        network_tx_bytes = sum(net['tx_bytes'] for net in networks.values())
        
        # Block I/O
        blkio_stats = stats.get('blkio_stats', {})
        block_read_bytes = sum(item['value'] for item in blkio_stats.get('io_service_bytes_recursive', []) 
                              if item['op'] == 'Read')
        block_write_bytes = sum(item['value'] for item in blkio_stats.get('io_service_bytes_recursive', []) 
                               if item['op'] == 'Write')
        
        # Process count
        pids = stats.get('pids_stats', {}).get('current', 0)
        
        # Uptime
        started_at = container.attrs['State']['StartedAt']
        start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        uptime_seconds = int((datetime.utcnow().replace(tzinfo=start_time.tzinfo) - start_time).total_seconds())
        
        # Restart count
        restart_count = container.attrs['RestartCount']
        
        return ContainerMetrics(
            account_id=account_id,
            container_id=container.id,
            status=ContainerStatus(container.status),
            cpu_usage_percent=cpu_usage_percent,
            memory_usage_mb=memory_usage_mb,
            memory_limit_mb=memory_limit_mb,
            network_rx_bytes=network_rx_bytes,
            network_tx_bytes=network_tx_bytes,
            block_read_bytes=block_read_bytes,
            block_write_bytes=block_write_bytes,
            pids=pids,
            uptime_seconds=uptime_seconds,
            restart_count=restart_count
        )
    
    def _store_container_metadata(self, account_id: str, container: docker.models.containers.Container, 
                                config: ContainerConfig):
        """Store container metadata in Redis"""
        try:
            metadata = {
                'account_id': account_id,
                'container_id': container.id,
                'container_name': container.name,
                'image': config.image,
                'created_at': datetime.utcnow().isoformat(),
                'config': {
                    'resources': config.resources.__dict__,
                    'network': config.network.__dict__,
                    'storage': config.storage.__dict__,
                }
            }
            
            self.redis_client.hset(
                'container_metadata',
                account_id,
                json.dumps(metadata)
            )
            
        except Exception as e:
            self.logger.error(f"Error storing container metadata: {e}")
    
    def _remove_container_metadata(self, account_id: str):
        """Remove container metadata from Redis"""
        try:
            self.redis_client.hdel('container_metadata', account_id)
        except Exception as e:
            self.logger.error(f"Error removing container metadata: {e}")
    
    def _store_metrics(self, metrics: ContainerMetrics):
        """Store container metrics in Redis"""
        try:
            metrics_data = {
                'account_id': metrics.account_id,
                'container_id': metrics.container_id,
                'status': metrics.status.value,
                'cpu_usage_percent': metrics.cpu_usage_percent,
                'memory_usage_mb': metrics.memory_usage_mb,
                'memory_limit_mb': metrics.memory_limit_mb,
                'network_rx_bytes': metrics.network_rx_bytes,
                'network_tx_bytes': metrics.network_tx_bytes,
                'block_read_bytes': metrics.block_read_bytes,
                'block_write_bytes': metrics.block_write_bytes,
                'pids': metrics.pids,
                'uptime_seconds': metrics.uptime_seconds,
                'restart_count': metrics.restart_count,
                'last_updated': metrics.last_updated.isoformat(),
            }
            
            # Store current metrics
            self.redis_client.hset(
                'container_metrics',
                metrics.account_id,
                json.dumps(metrics_data)
            )
            
            # Store historical metrics
            self.redis_client.lpush(
                f'container_metrics_history:{metrics.account_id}',
                json.dumps(metrics_data)
            )
            
            # Keep only last 1000 entries
            self.redis_client.ltrim(f'container_metrics_history:{metrics.account_id}', 0, 999)
            
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")

# =============================================================================
# DOCKER ORCHESTRATOR
# =============================================================================

class DockerOrchestrator:
    """Main orchestrator for Docker-based multi-account trading"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise
        
        # Initialize Redis client
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        
        # Initialize components
        self.image_builder = DockerImageBuilder(self.docker_client)
        self.container_manager = ContainerManager(self.docker_client, self.redis_client)
        
        # State
        self._running = False
        self._monitor_thread = None
    
    def start(self):
        """Start the Docker orchestrator"""
        try:
            self.logger.info("Starting Docker Orchestrator")
            self._running = True
            
            # Build base image if not exists
            self._ensure_base_image()
            
            # Start monitoring
            import threading
            self._monitor_thread = threading.Thread(target=self._monitor_containers, daemon=True)
            self._monitor_thread.start()
            
            self.logger.info("Docker Orchestrator started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting orchestrator: {e}")
            raise
    
    def stop(self):
        """Stop the Docker orchestrator"""
        try:
            self.logger.info("Stopping Docker Orchestrator")
            self._running = False
            
            # Stop monitoring
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=30)
            
            # Stop all containers
            self._stop_all_containers()
            
            self.logger.info("Docker Orchestrator stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping orchestrator: {e}")
    
    def deploy_account(self, account_id: str, config: ContainerConfig) -> bool:
        """Deploy a new trading account"""
        try:
            self.logger.info(f"Deploying account: {account_id}")
            
            # Build account-specific image
            if not self.image_builder.build_account_image(account_id):
                return False
            
            # Update image in config
            config.image = f"trading-sentinel-{account_id}:latest"
            
            # Create and start container
            if not self.container_manager.create_container(config):
                return False
            
            if not self.container_manager.start_container(account_id):
                return False
            
            self.logger.info(f"Account {account_id} deployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deploying account {account_id}: {e}")
            return False
    
    def undeploy_account(self, account_id: str) -> bool:
        """Undeploy a trading account"""
        try:
            self.logger.info(f"Undeploying account: {account_id}")
            
            # Remove container
            if not self.container_manager.remove_container(account_id, force=True):
                return False
            
            # Remove account image
            try:
                image_tag = f"trading-sentinel-{account_id}:latest"
                self.docker_client.images.remove(image_tag, force=True)
            except docker.errors.ImageNotFound:
                pass
            
            self.logger.info(f"Account {account_id} undeployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error undeploying account {account_id}: {e}")
            return False
    
    def scale_account(self, account_id: str, replicas: int) -> bool:
        """Scale an account to multiple replicas"""
        try:
            self.logger.info(f"Scaling account {account_id} to {replicas} replicas")
            
            # Get current containers for this account
            current_containers = self._get_account_containers(account_id)
            current_count = len(current_containers)
            
            if replicas > current_count:
                # Scale up
                for i in range(current_count, replicas):
                    replica_id = f"{account_id}-replica-{i}"
                    # Create replica configuration
                    # Implementation depends on specific requirements
                    pass
            elif replicas < current_count:
                # Scale down
                containers_to_remove = current_containers[replicas:]
                for container in containers_to_remove:
                    container.stop()
                    container.remove()
            
            self.logger.info(f"Account {account_id} scaled to {replicas} replicas")
            return True
            
        except Exception as e:
            self.logger.error(f"Error scaling account {account_id}: {e}")
            return False
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        try:
            # Get all trading containers
            containers = self.docker_client.containers.list(
                all=True,
                filters={'label': 'ai.trading.sentinel.account_id'}
            )
            
            account_status = {}
            for container in containers:
                account_id = container.labels.get('ai.trading.sentinel.account_id')
                if account_id:
                    metrics = self.container_manager.get_container_metrics(account_id)
                    account_status[account_id] = {
                        'container_id': container.id,
                        'status': container.status,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'created': container.attrs['Created'],
                        'metrics': metrics.__dict__ if metrics else None
                    }
            
            # System resources
            system_info = self.docker_client.info()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'docker_info': {
                    'version': system_info['ServerVersion'],
                    'containers_running': system_info['ContainersRunning'],
                    'containers_paused': system_info['ContainersPaused'],
                    'containers_stopped': system_info['ContainersStopped'],
                    'images': system_info['Images'],
                    'memory_total': system_info['MemTotal'],
                    'cpus': system_info['NCPU']
                },
                'accounts': account_status,
                'total_accounts': len(account_status),
                'active_accounts': len([s for s in account_status.values() if s['status'] == 'running'])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting orchestrator status: {e}")
            return {}
    
    def _ensure_base_image(self):
        """Ensure base image exists"""
        try:
            # Check if base image exists
            try:
                self.docker_client.images.get('trading-sentinel-base:latest')
                self.logger.info("Base image already exists")
                return
            except docker.errors.ImageNotFound:
                pass
            
            # Build base image
            self.logger.info("Building base image...")
            if not self.image_builder.build_base_image():
                raise Exception("Failed to build base image")
                
        except Exception as e:
            self.logger.error(f"Error ensuring base image: {e}")
            raise
    
    def _get_account_containers(self, account_id: str) -> List[docker.models.containers.Container]:
        """Get all containers for an account"""
        try:
            return self.docker_client.containers.list(
                all=True,
                filters={
                    'label': f'ai.trading.sentinel.account_id={account_id}'
                }
            )
        except Exception as e:
            self.logger.error(f"Error getting containers for {account_id}: {e}")
            return []
    
    def _stop_all_containers(self):
        """Stop all trading containers"""
        try:
            containers = self.docker_client.containers.list(
                filters={'label': 'ai.trading.sentinel.account_id'}
            )
            
            for container in containers:
                try:
                    container.stop(timeout=30)
                    self.logger.info(f"Stopped container: {container.id}")
                except Exception as e:
                    self.logger.error(f"Error stopping container {container.id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error stopping all containers: {e}")
    
    def _monitor_containers(self):
        """Monitor all containers"""
        while self._running:
            try:
                # Get all trading containers
                containers = self.docker_client.containers.list(
                    all=True,
                    filters={'label': 'ai.trading.sentinel.account_id'}
                )
                
                for container in containers:
                    account_id = container.labels.get('ai.trading.sentinel.account_id')
                    if account_id:
                        # Collect metrics
                        self.container_manager.get_container_metrics(account_id)
                        
                        # Check health
                        if container.status == 'exited':
                            self.logger.warning(f"Container for {account_id} has exited")
                            # Implement restart logic if needed
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in container monitoring: {e}")
                time.sleep(10)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function for testing Docker orchestration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create orchestrator
    orchestrator = DockerOrchestrator()
    
    try:
        # Start orchestrator
        orchestrator.start()
        
        # Example: Deploy test account
        test_config = ContainerConfig(
            account_id="test_docker_account",
            environment={
                'ACCOUNT_ID': 'test_docker_account',
                'BROKER': 'test_broker',
                'STRATEGY': 'scalping',
                'LOG_LEVEL': 'INFO'
            },
            resources=ContainerResources(
                cpu_limit=0.5,
                memory_limit="512m",
                memory_reservation="256m"
            ),
            network=ContainerNetwork(
                port_bindings={'8000': '8001'}
            )
        )
        
        # Deploy account
        if orchestrator.deploy_account("test_docker_account", test_config):
            print("Test account deployed successfully")
        
        # Monitor
        print("Docker Orchestrator running. Press Ctrl+C to stop.")
        
        while True:
            status = orchestrator.get_orchestrator_status()
            print(f"\nOrchestrator Status: {status['active_accounts']}/{status['total_accounts']} accounts active")
            
            for account_id, account_info in status['accounts'].items():
                print(f"  {account_id}: {account_info['status']}")
                if account_info['metrics']:
                    metrics = account_info['metrics']
                    print(f"    CPU: {metrics['cpu_usage_percent']:.1f}%, Memory: {metrics['memory_usage_mb']:.1f}MB")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    main()