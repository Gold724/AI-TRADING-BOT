#!/usr/bin/env python3
"""
AI Trading Sentinel - Production Deployment Orchestrator
TRAE-SentinelOps: Complete automation for 24/7 cloud deployment

This script orchestrates the entire production deployment process:
- Environment validation and setup
- Docker containerization
- Systemd service management
- Security hardening
- Monitoring and health checks
- CI/CD pipeline integration
"""

import os
import sys
import json
import time
import subprocess
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('DeploymentOrchestrator')

class DeploymentMode(Enum):
    DOCKER = "docker"
    SYSTEMD = "systemd"
    HYBRID = "hybrid"

class DeploymentStage(Enum):
    VALIDATION = "validation"
    PREPARATION = "preparation"
    DEPLOYMENT = "deployment"
    VERIFICATION = "verification"
    MONITORING = "monitoring"

@dataclass
class DeploymentConfig:
    mode: DeploymentMode
    environment: str
    domain: Optional[str]
    ssl_enabled: bool
    backup_enabled: bool
    monitoring_enabled: bool
    github_integration: bool
    
class DeploymentOrchestrator:
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.project_root = Path.cwd()
        self.deployment_id = f"deploy_{int(time.time())}"
        self.status = {}
        
    def run_command(self, cmd: str, check: bool = True, capture: bool = False) -> Tuple[int, str, str]:
        """Execute shell command with logging"""
        logger.info(f"Executing: {cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=capture,
                text=True
            )
            return result.returncode, result.stdout if capture else "", result.stderr if capture else ""
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd}")
            logger.error(f"Error: {e}")
            if capture:
                return e.returncode, e.stdout or "", e.stderr or ""
            return e.returncode, "", str(e)
    
    def validate_environment(self) -> bool:
        """Validate deployment environment and prerequisites"""
        logger.info("[INFO] Validating deployment environment...")
        
        checks = [
            ("Python 3.10+", self._check_python_version),
            ("Docker", self._check_docker) if self.config.mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID] else None,
            ("Systemd", self._check_systemd) if self.config.mode in [DeploymentMode.SYSTEMD, DeploymentMode.HYBRID] else None,
            ("Git", self._check_git),
            ("Environment file", self._check_env_file),
            ("Required files", self._check_required_files),
        ]
        
        all_passed = True
        for check in checks:
            if check is None:
                continue
            name, func = check
            try:
                if func():
                    logger.info(f"[OK] {name}: OK")
                else:
                    logger.error(f"[FAILED] {name}: FAILED")
                    all_passed = False
            except Exception as e:
                logger.error(f"[ERROR] {name}: ERROR - {e}")
                all_passed = False
        
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Check Python version"""
        return sys.version_info >= (3, 10)
    
    def _check_docker(self) -> bool:
        """Check Docker availability"""
        code, _, _ = self.run_command("docker --version", check=False, capture=True)
        return code == 0
    
    def _check_systemd(self) -> bool:
        """Check systemd availability"""
        return Path("/etc/systemd/system").exists()
    
    def _check_git(self) -> bool:
        """Check Git availability"""
        code, _, _ = self.run_command("git --version", check=False, capture=True)
        return code == 0
    
    def _check_env_file(self) -> bool:
        """Check environment file exists"""
        env_file = self.project_root / f".env.{self.config.environment}"
        return env_file.exists()
    
    def _check_required_files(self) -> bool:
        """Check required deployment files exist"""
        required_files = [
            "backend_main.py",
            "tradebot_sentinel_bulenox_automation.py",
            "requirements.txt",
        ]
        
        if self.config.mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
            required_files.extend([
                "docker-compose.yml",
                "Dockerfile.backend",
                "Dockerfile.bot",
                "Dockerfile.frontend",
                "Dockerfile.monitoring"
            ])
        
        if self.config.mode in [DeploymentMode.SYSTEMD, DeploymentMode.HYBRID]:
            required_files.extend([
                "aitrading-backend.service",
                "aitrading-bot.service",
                "aitrading-monitor.service"
            ])
        
        missing_files = []
        for file in required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        
        return True
    
    def prepare_deployment(self) -> bool:
        """Prepare deployment environment"""
        logger.info("🔧 Preparing deployment environment...")
        
        try:
            # Create deployment directories
            dirs = ["logs", "data", "temp", "backups", "metrics"]
            for dir_name in dirs:
                (self.project_root / dir_name).mkdir(exist_ok=True)
            
            # Install Python dependencies
            logger.info("Installing Python dependencies...")
            self.run_command("pip install -r requirements.txt")
            
            # Setup environment variables
            self._setup_environment()
            
            # Generate SSL certificates if needed
            if self.config.ssl_enabled:
                self._setup_ssl()
            
            return True
            
        except Exception as e:
            logger.error(f"Preparation failed: {e}")
            return False
    
    def _setup_environment(self):
        """Setup environment variables"""
        env_file = self.project_root / f".env.{self.config.environment}"
        if not env_file.exists():
            logger.warning(f"Environment file {env_file} not found, creating from template...")
            template_file = self.project_root / f".env.{self.config.environment}.template"
            if template_file.exists():
                env_file.write_text(template_file.read_text())
    
    def _setup_ssl(self):
        """Setup SSL certificates"""
        logger.info("Setting up SSL certificates...")
        if self.config.domain:
            # Use Let's Encrypt for production
            self.run_command(f"certbot --nginx -d {self.config.domain} --non-interactive --agree-tos")
        else:
            # Generate self-signed certificates for development
            ssl_dir = self.project_root / "ssl"
            ssl_dir.mkdir(exist_ok=True)
            self.run_command(f"openssl req -x509 -newkey rsa:4096 -keyout {ssl_dir}/key.pem -out {ssl_dir}/cert.pem -days 365 -nodes -subj '/CN=localhost'")
    
    def deploy_docker(self) -> bool:
        """Deploy using Docker Compose"""
        logger.info("🐳 Deploying with Docker Compose...")
        
        try:
            # Build and start services
            self.run_command("docker-compose down --remove-orphans")
            self.run_command("docker-compose build --no-cache")
            self.run_command("docker-compose up -d")
            
            # Wait for services to be ready
            self._wait_for_services()
            
            return True
            
        except Exception as e:
            logger.error(f"Docker deployment failed: {e}")
            return False
    
    def deploy_systemd(self) -> bool:
        """Deploy using systemd services"""
        logger.info("⚙️ Deploying with systemd services...")
        
        try:
            # Copy service files
            service_files = [
                "aitrading-backend.service",
                "aitrading-bot.service",
                "aitrading-monitor.service"
            ]
            
            for service_file in service_files:
                src = self.project_root / service_file
                dst = Path(f"/etc/systemd/system/{service_file}")
                self.run_command(f"sudo cp {src} {dst}")
            
            # Reload systemd and start services
            self.run_command("sudo systemctl daemon-reload")
            
            for service_file in service_files:
                service_name = service_file.replace(".service", "")
                self.run_command(f"sudo systemctl enable {service_name}")
                self.run_command(f"sudo systemctl start {service_name}")
            
            # Wait for services to be ready
            self._wait_for_services()
            
            return True
            
        except Exception as e:
            logger.error(f"Systemd deployment failed: {e}")
            return False
    
    def _wait_for_services(self):
        """Wait for services to be ready"""
        logger.info("Waiting for services to be ready...")
        
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Check backend health
                code, _, _ = self.run_command("curl -f http://localhost:5000/api/health", check=False, capture=True)
                if code == 0:
                    logger.info("[SUCCESS] Backend service is ready")
                    break
            except:
                pass
            
            attempt += 1
            time.sleep(10)
            logger.info(f"Waiting for services... ({attempt}/{max_attempts})")
        
        if attempt >= max_attempts:
            raise Exception("Services failed to start within timeout")
    
    def verify_deployment(self) -> bool:
        """Verify deployment health"""
        logger.info("🔍 Verifying deployment...")
        
        try:
            # Run validation script
            code, stdout, stderr = self.run_command("python validate_deployment.py", capture=True)
            
            if code == 0:
                logger.info("[SUCCESS] Deployment verification passed")
                return True
            else:
                logger.error(f"[FAILED] Deployment verification failed: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring and alerting"""
        if not self.config.monitoring_enabled:
            return True
            
        logger.info("📊 Setting up monitoring...")
        
        try:
            # Run monitoring setup
            self.run_command("python monitoring_setup.py --setup")
            
            # Setup log rotation
            self.run_command("sudo cp logrotate.conf /etc/logrotate.d/aitrading")
            
            return True
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {e}")
            return False
    
    def setup_backup(self) -> bool:
        """Setup backup system"""
        if not self.config.backup_enabled:
            return True
            
        logger.info("💾 Setting up backup system...")
        
        try:
            # Make backup script executable
            self.run_command("chmod +x backup_recovery.sh")
            
            # Setup cron job for daily backups
            cron_job = "0 2 * * * /path/to/ai-trading-sentinel/backup_recovery.sh backup\n"
            self.run_command(f"echo '{cron_job}' | crontab -")
            
            return True
            
        except Exception as e:
            logger.error(f"Backup setup failed: {e}")
            return False
    
    def deploy(self) -> bool:
        """Execute complete deployment process"""
        logger.info(f"[DEPLOY] Starting deployment {self.deployment_id}...")
        logger.info(f"Mode: {self.config.mode.value}")
        logger.info(f"Environment: {self.config.environment}")
        
        stages = [
            (DeploymentStage.VALIDATION, self.validate_environment),
            (DeploymentStage.PREPARATION, self.prepare_deployment),
        ]
        
        # Add deployment stage based on mode
        if self.config.mode == DeploymentMode.DOCKER:
            stages.append((DeploymentStage.DEPLOYMENT, self.deploy_docker))
        elif self.config.mode == DeploymentMode.SYSTEMD:
            stages.append((DeploymentStage.DEPLOYMENT, self.deploy_systemd))
        elif self.config.mode == DeploymentMode.HYBRID:
            stages.append((DeploymentStage.DEPLOYMENT, lambda: self.deploy_docker() and self.deploy_systemd()))
        
        stages.extend([
            (DeploymentStage.VERIFICATION, self.verify_deployment),
            (DeploymentStage.MONITORING, self.setup_monitoring),
        ])
        
        # Execute stages
        for stage, func in stages:
            logger.info(f"\n{'='*50}")
            logger.info(f"Stage: {stage.value.upper()}")
            logger.info(f"{'='*50}")
            
            start_time = time.time()
            success = func()
            duration = time.time() - start_time
            
            self.status[stage.value] = {
                'success': success,
                'duration': duration,
                'timestamp': time.time()
            }
            
            if success:
                logger.info(f"[SUCCESS] {stage.value} completed in {duration:.2f}s")
            else:
                logger.error(f"[FAILED] {stage.value} failed after {duration:.2f}s")
                return False
        
        # Setup backup if enabled
        if self.config.backup_enabled:
            self.setup_backup()
        
        logger.info(f"\n[SUCCESS] Deployment {self.deployment_id} completed successfully!")
        self._print_deployment_summary()
        
        return True
    
    def _print_deployment_summary(self):
        """Print deployment summary"""
        logger.info("\n" + "="*60)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("="*60)
        logger.info(f"Deployment ID: {self.deployment_id}")
        logger.info(f"Mode: {self.config.mode.value}")
        logger.info(f"Environment: {self.config.environment}")
        
        if self.config.domain:
            protocol = "https" if self.config.ssl_enabled else "http"
            logger.info(f"URL: {protocol}://{self.config.domain}")
        else:
            logger.info("URL: http://localhost:3000 (frontend)")
            logger.info("API: http://localhost:5000 (backend)")
        
        logger.info("\nServices Status:")
        for stage, info in self.status.items():
            status = "[SUCCESS]" if info['success'] else "[FAILED]"
            logger.info(f"  {stage}: {status} ({info['duration']:.2f}s)")
        
        logger.info("\nNext Steps:")
        logger.info("1. Monitor logs: tail -f logs/backend.log")
        logger.info("2. Check health: curl http://localhost:5000/api/health")
        logger.info("3. Access frontend: http://localhost:3000")
        
        if self.config.github_integration:
            logger.info("4. Setup GitHub webhook for auto-deployment")
        
        logger.info("="*60)

def main():
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Deployment Orchestrator")
    parser.add_argument("--mode", choices=["docker", "systemd", "hybrid"], default="docker", help="Deployment mode")
    parser.add_argument("--env", default="production", help="Environment (production, staging, development)")
    parser.add_argument("--domain", help="Domain name for SSL setup")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL")
    parser.add_argument("--no-backup", action="store_true", help="Disable backup setup")
    parser.add_argument("--no-monitoring", action="store_true", help="Disable monitoring setup")
    parser.add_argument("--github", action="store_true", help="Enable GitHub integration")
    
    args = parser.parse_args()
    
    config = DeploymentConfig(
        mode=DeploymentMode(args.mode),
        environment=args.env,
        domain=args.domain,
        ssl_enabled=args.ssl,
        backup_enabled=not args.no_backup,
        monitoring_enabled=not args.no_monitoring,
        github_integration=args.github
    )
    
    orchestrator = DeploymentOrchestrator(config)
    
    try:
        success = orchestrator.deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n[WARNING] Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n[ERROR] Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()