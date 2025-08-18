#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradeBot Sentinel - Advanced Scheduling System
Cron-like scheduling for fully autonomous operation with job management
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from threading import Thread, Event
from dotenv import load_dotenv

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class ScheduledJob:
    name: str
    command: str
    schedule: str  # cron-like format: "minute hour day month weekday"
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    max_runtime: int = 3600  # seconds
    timeout_action: str = "kill"  # "kill" or "ignore"
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 300  # seconds
    
class CronScheduler:
    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self.stop_event = Event()
        self.scheduler_thread = None
        self.active_processes: Dict[str, subprocess.Popen] = {}
        
        # Configuration
        self.config = {
            'check_interval': int(os.getenv('SCHEDULER_CHECK_INTERVAL', '60')),  # seconds
            'log_file': os.getenv('SCHEDULER_LOG_FILE', 'logs/scheduler.log'),
            'jobs_file': os.getenv('SCHEDULER_JOBS_FILE', 'logs/scheduled_jobs.json'),
            'max_concurrent_jobs': int(os.getenv('MAX_CONCURRENT_JOBS', '3')),
            'job_timeout': int(os.getenv('DEFAULT_JOB_TIMEOUT', '3600')),
        }
        
        # Ensure directories exist
        Path('logs').mkdir(exist_ok=True)
        
        # Load existing jobs
        self.load_jobs()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        self.stop()
        
    def add_job(self, job: ScheduledJob):
        """Add a scheduled job"""
        job.next_run = self._calculate_next_run(job.schedule)
        self.jobs[job.name] = job
        self.save_jobs()
        logger.info(f"✅ Job added: {job.name} - Next run: {job.next_run}")
        
    def remove_job(self, job_name: str):
        """Remove a scheduled job"""
        if job_name in self.jobs:
            del self.jobs[job_name]
            self.save_jobs()
            logger.info(f"🗑️ Job removed: {job_name}")
        else:
            logger.warning(f"Job not found: {job_name}")
            
    def enable_job(self, job_name: str):
        """Enable a job"""
        if job_name in self.jobs:
            self.jobs[job_name].enabled = True
            self.save_jobs()
            logger.info(f"✅ Job enabled: {job_name}")
            
    def disable_job(self, job_name: str):
        """Disable a job"""
        if job_name in self.jobs:
            self.jobs[job_name].enabled = False
            self.save_jobs()
            logger.info(f"⏸️ Job disabled: {job_name}")
            
    def _calculate_next_run(self, schedule: str, from_time: Optional[datetime] = None) -> datetime:
        """Calculate next run time from cron-like schedule"""
        if from_time is None:
            from_time = datetime.now()
            
        # Parse cron format: "minute hour day month weekday"
        parts = schedule.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid schedule format: {schedule}")
            
        minute, hour, day, month, weekday = parts
        
        # Start from next minute
        next_time = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Simple cron parsing (supports * and specific values)
        for _ in range(366 * 24 * 60):  # Max 1 year ahead
            if self._matches_schedule(next_time, minute, hour, day, month, weekday):
                return next_time
            next_time += timedelta(minutes=1)
            
        raise ValueError(f"Could not calculate next run for schedule: {schedule}")
        
    def _matches_schedule(self, dt: datetime, minute: str, hour: str, day: str, month: str, weekday: str) -> bool:
        """Check if datetime matches cron schedule"""
        return (
            self._matches_field(dt.minute, minute) and
            self._matches_field(dt.hour, hour) and
            self._matches_field(dt.day, day) and
            self._matches_field(dt.month, month) and
            self._matches_field(dt.weekday(), weekday)
        )
        
    def _matches_field(self, value: int, pattern: str) -> bool:
        """Check if value matches cron field pattern"""
        if pattern == '*':
            return True
            
        # Handle ranges (e.g., "1-5")
        if '-' in pattern:
            start, end = map(int, pattern.split('-'))
            return start <= value <= end
            
        # Handle lists (e.g., "1,3,5")
        if ',' in pattern:
            values = list(map(int, pattern.split(',')))
            return value in values
            
        # Handle step values (e.g., "*/5")
        if '/' in pattern:
            base, step = pattern.split('/')
            if base == '*':
                return value % int(step) == 0
            else:
                base_val = int(base)
                return value >= base_val and (value - base_val) % int(step) == 0
                
        # Exact match
        return value == int(pattern)
        
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        self.stop_event.clear()
        self.scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"🚀 Scheduler started with {len(self.jobs)} jobs")
        
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
            
        logger.info("🛑 Stopping scheduler...")
        self.running = False
        self.stop_event.set()
        
        # Kill active processes
        for job_name, process in self.active_processes.items():
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"🔪 Terminated job: {job_name}")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"💀 Killed job: {job_name}")
            except Exception as e:
                logger.error(f"Error stopping job {job_name}: {e}")
                
        self.active_processes.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            
        logger.info("✅ Scheduler stopped")
        
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running and not self.stop_event.is_set():
            try:
                current_time = datetime.now()
                
                # Check for jobs to run
                for job_name, job in self.jobs.items():
                    if not job.enabled:
                        continue
                        
                    if job.next_run and current_time >= job.next_run:
                        if len(self.active_processes) < self.config['max_concurrent_jobs']:
                            self._run_job(job)
                        else:
                            logger.warning(f"⏳ Job {job_name} delayed - max concurrent jobs reached")
                            
                # Check for completed processes
                self._check_completed_processes()
                
                # Wait before next check
                self.stop_event.wait(self.config['check_interval'])
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)  # Wait before retrying
                
    def _run_job(self, job: ScheduledJob):
        """Run a scheduled job"""
        try:
            logger.info(f"🚀 Starting job: {job.name}")
            
            # Update job stats
            job.last_run = datetime.now()
            job.run_count += 1
            job.next_run = self._calculate_next_run(job.schedule, job.last_run)
            
            # Start process
            process = subprocess.Popen(
                job.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.active_processes[job.name] = process
            self.save_jobs()
            
            logger.info(f"✅ Job started: {job.name} (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to start job {job.name}: {e}")
            job.failure_count += 1
            self.save_jobs()
            
    def _check_completed_processes(self):
        """Check for completed processes and handle results"""
        completed_jobs = []
        
        for job_name, process in self.active_processes.items():
            if process.poll() is not None:  # Process completed
                completed_jobs.append(job_name)
                
                job = self.jobs[job_name]
                return_code = process.returncode
                
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    stdout, stderr = "", "Process communication timeout"
                    
                if return_code == 0:
                    job.success_count += 1
                    job.retry_count = 0  # Reset retry count on success
                    logger.info(f"✅ Job completed successfully: {job_name}")
                else:
                    job.failure_count += 1
                    logger.error(f"❌ Job failed: {job_name} (exit code: {return_code})")
                    
                    if stderr:
                        logger.error(f"Job {job_name} stderr: {stderr[:500]}")
                        
                    # Handle retries
                    if job.retry_count < job.max_retries:
                        job.retry_count += 1
                        retry_time = datetime.now() + timedelta(seconds=job.retry_delay)
                        job.next_run = retry_time
                        logger.info(f"🔄 Job {job_name} will retry in {job.retry_delay}s (attempt {job.retry_count}/{job.max_retries})")
                        
                # Log job output
                self._log_job_output(job_name, return_code, stdout, stderr)
                
        # Remove completed processes
        for job_name in completed_jobs:
            del self.active_processes[job_name]
            
        if completed_jobs:
            self.save_jobs()
            
    def _log_job_output(self, job_name: str, return_code: int, stdout: str, stderr: str):
        """Log job output to file"""
        log_file = Path(f"logs/job_{job_name.replace(' ', '_')}.log")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Job: {job_name}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"Exit Code: {return_code}\n")
            f.write(f"{'='*50}\n")
            
            if stdout:
                f.write(f"STDOUT:\n{stdout}\n")
                
            if stderr:
                f.write(f"STDERR:\n{stderr}\n")
                
    def save_jobs(self):
        """Save jobs to file"""
        jobs_data = {}
        for name, job in self.jobs.items():
            job_dict = asdict(job)
            # Convert datetime objects to ISO strings
            if job_dict['last_run']:
                job_dict['last_run'] = job.last_run.isoformat()
            if job_dict['next_run']:
                job_dict['next_run'] = job.next_run.isoformat()
            jobs_data[name] = job_dict
            
        with open(self.config['jobs_file'], 'w') as f:
            json.dump(jobs_data, f, indent=2)
            
    def load_jobs(self):
        """Load jobs from file"""
        jobs_file = Path(self.config['jobs_file'])
        if not jobs_file.exists():
            return
            
        try:
            with open(jobs_file, 'r') as f:
                jobs_data = json.load(f)
                
            for name, job_dict in jobs_data.items():
                # Convert ISO strings back to datetime objects
                if job_dict['last_run']:
                    job_dict['last_run'] = datetime.fromisoformat(job_dict['last_run'])
                if job_dict['next_run']:
                    job_dict['next_run'] = datetime.fromisoformat(job_dict['next_run'])
                    
                self.jobs[name] = ScheduledJob(**job_dict)
                
            logger.info(f"📂 Loaded {len(self.jobs)} jobs from file")
            
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'running': self.running,
            'total_jobs': len(self.jobs),
            'enabled_jobs': sum(1 for job in self.jobs.values() if job.enabled),
            'active_processes': len(self.active_processes),
            'jobs': {
                name: {
                    'enabled': job.enabled,
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'run_count': job.run_count,
                    'success_count': job.success_count,
                    'failure_count': job.failure_count,
                    'success_rate': f"{(job.success_count / max(job.run_count, 1)) * 100:.1f}%"
                }
                for name, job in self.jobs.items()
            }
        }
        
def setup_default_jobs(scheduler: CronScheduler):
    """Setup default TradeBot Sentinel jobs"""
    
    # Main trading bot - runs every 15 minutes during market hours
    trading_job = ScheduledJob(
        name="TradeBot Main",
        command="python tradebot_sentinel_advanced_pro.py --headless",
        schedule="*/15 9-16 * * 1-5",  # Every 15 min, 9AM-4PM, Mon-Fri
        max_runtime=900,  # 15 minutes
        max_retries=2
    )
    scheduler.add_job(trading_job)
    
    # Risk monitoring - runs every 5 minutes
    risk_job = ScheduledJob(
        name="Risk Monitor",
        command="python risk_management.py --monitor",
        schedule="*/5 * * * *",  # Every 5 minutes
        max_runtime=300,  # 5 minutes
        max_retries=1
    )
    scheduler.add_job(risk_job)
    
    # Daily report - runs at 6 PM every day
    report_job = ScheduledJob(
        name="Daily Report",
        command="python generate_daily_report.py",
        schedule="0 18 * * *",  # 6 PM daily
        max_runtime=600,  # 10 minutes
        max_retries=2
    )
    scheduler.add_job(report_job)
    
    # System health check - runs every hour
    health_job = ScheduledJob(
        name="Health Check",
        command="python system_health_check.py",
        schedule="0 * * * *",  # Every hour
        max_runtime=300,  # 5 minutes
        max_retries=1
    )
    scheduler.add_job(health_job)
    
    # Log cleanup - runs daily at midnight
    cleanup_job = ScheduledJob(
        name="Log Cleanup",
        command="python cleanup_logs.py",
        schedule="0 0 * * *",  # Midnight daily
        max_runtime=600,  # 10 minutes
        max_retries=1
    )
    scheduler.add_job(cleanup_job)
    
if __name__ == "__main__":
    # Configure logging with UTF-8 encoding
    log_handlers = [
        logging.StreamHandler()
    ]

    # Add file handler with UTF-8 encoding
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = logging.FileHandler('logs/scheduler.log', encoding='utf-8')
    log_handlers.append(file_handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=log_handlers
    )
    
    # Create and start scheduler
    scheduler = CronScheduler()
    
    # Setup default jobs if none exist
    if not scheduler.jobs:
        setup_default_jobs(scheduler)
        
    try:
        scheduler.start()
        
        # Keep running until interrupted
        while scheduler.running:
            time.sleep(60)
            
            # Print status every 10 minutes
            if datetime.now().minute % 10 == 0:
                status = scheduler.get_status()
                logger.info(f"📊 Scheduler Status: {status['active_processes']} active, {status['enabled_jobs']} enabled jobs")
                
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        scheduler.stop()