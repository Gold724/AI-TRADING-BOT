#!/usr/bin/env python3
"""
TradeBot Sentinel - Universal Cloud Deployment Script

This script automates deployment to multiple cloud providers:
- AWS EC2
- Google Cloud Platform
- DigitalOcean
- Contabo VPS
- Vast.ai

Usage:
    python3 deploy_cloud.py --provider aws --instance-type t3.medium
    python3 deploy_cloud.py --provider gcp --machine-type e2-medium
    python3 deploy_cloud.py --provider digitalocean --size s-2vcpu-4gb
    python3 deploy_cloud.py --provider contabo --plan vps-s
    python3 deploy_cloud.py --provider vast --gpu-type rtx3080
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CloudDeploy')

class CloudDeployer:
    """Universal cloud deployment manager"""
    
    def __init__(self, provider, config):
        self.provider = provider
        self.config = config
        self.deployment_id = f"tradebot-{int(time.time())}"
        
    def validate_credentials(self):
        """Validate cloud provider credentials"""
        logger.info(f"Validating {self.provider} credentials...")
        
        if self.provider == 'aws':
            return self._validate_aws_credentials()
        elif self.provider == 'gcp':
            return self._validate_gcp_credentials()
        elif self.provider == 'digitalocean':
            return self._validate_do_credentials()
        elif self.provider == 'contabo':
            return self._validate_contabo_credentials()
        elif self.provider == 'vast':
            return self._validate_vast_credentials()
        else:
            logger.error(f"Unsupported provider: {self.provider}")
            return False
    
    def _validate_aws_credentials(self):
        """Validate AWS credentials"""
        try:
            result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                                  capture_output=True, text=True, check=True)
            logger.info("AWS credentials validated successfully")
            return True
        except subprocess.CalledProcessError:
            logger.error("AWS credentials validation failed")
            return False
    
    def _validate_gcp_credentials(self):
        """Validate GCP credentials"""
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], 
                                  capture_output=True, text=True, check=True)
            logger.info("GCP credentials validated successfully")
            return True
        except subprocess.CalledProcessError:
            logger.error("GCP credentials validation failed")
            return False
    
    def _validate_do_credentials(self):
        """Validate DigitalOcean credentials"""
        token = os.getenv('DO_API_TOKEN')
        if not token:
            logger.error("DO_API_TOKEN not found in environment")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get('https://api.digitalocean.com/v2/account', headers=headers)
            response.raise_for_status()
            logger.info("DigitalOcean credentials validated successfully")
            return True
        except requests.RequestException:
            logger.error("DigitalOcean credentials validation failed")
            return False
    
    def _validate_contabo_credentials(self):
        """Validate Contabo credentials"""
        # Contabo uses SSH key authentication
        ssh_key = os.getenv('CONTABO_SSH_KEY')
        if not ssh_key or not os.path.exists(ssh_key):
            logger.error("CONTABO_SSH_KEY not found or invalid")
            return False
        
        logger.info("Contabo SSH key validated successfully")
        return True
    
    def _validate_vast_credentials(self):
        """Validate Vast.ai credentials"""
        api_key = os.getenv('VAST_API_KEY')
        if not api_key:
            logger.error("VAST_API_KEY not found in environment")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get('https://console.vast.ai/api/v0/users/current/', headers=headers)
            response.raise_for_status()
            logger.info("Vast.ai credentials validated successfully")
            return True
        except requests.RequestException:
            logger.error("Vast.ai credentials validation failed")
            return False
    
    def create_instance(self):
        """Create cloud instance"""
        logger.info(f"Creating {self.provider} instance...")
        
        if self.provider == 'aws':
            return self._create_aws_instance()
        elif self.provider == 'gcp':
            return self._create_gcp_instance()
        elif self.provider == 'digitalocean':
            return self._create_do_instance()
        elif self.provider == 'contabo':
            return self._create_contabo_instance()
        elif self.provider == 'vast':
            return self._create_vast_instance()
    
    def _create_aws_instance(self):
        """Create AWS EC2 instance"""
        try:
            # Create security group
            sg_result = subprocess.run([
                'aws', 'ec2', 'create-security-group',
                '--group-name', f'tradebot-sg-{self.deployment_id}',
                '--description', 'TradeBot Sentinel Security Group'
            ], capture_output=True, text=True, check=True)
            
            sg_id = json.loads(sg_result.stdout)['GroupId']
            
            # Add security group rules
            subprocess.run([
                'aws', 'ec2', 'authorize-security-group-ingress',
                '--group-id', sg_id,
                '--protocol', 'tcp',
                '--port', '22',
                '--cidr', '0.0.0.0/0'
            ], check=True)
            
            subprocess.run([
                'aws', 'ec2', 'authorize-security-group-ingress',
                '--group-id', sg_id,
                '--protocol', 'tcp',
                '--port', '5000',
                '--cidr', '0.0.0.0/0'
            ], check=True)
            
            # Launch instance
            instance_result = subprocess.run([
                'aws', 'ec2', 'run-instances',
                '--image-id', 'ami-0c02fb55956c7d316',  # Ubuntu 22.04
                '--instance-type', self.config.get('instance_type', 't3.medium'),
                '--key-name', os.getenv('AWS_KEY_PAIR'),
                '--security-group-ids', sg_id,
                '--tag-specifications', f'ResourceType=instance,Tags=[{{Key=Name,Value=tradebot-sentinel-{self.deployment_id}}}]'
            ], capture_output=True, text=True, check=True)
            
            instance_data = json.loads(instance_result.stdout)
            instance_id = instance_data['Instances'][0]['InstanceId']
            
            logger.info(f"AWS instance created: {instance_id}")
            
            # Wait for instance to be running
            logger.info("Waiting for instance to be running...")
            subprocess.run([
                'aws', 'ec2', 'wait', 'instance-running',
                '--instance-ids', instance_id
            ], check=True)
            
            # Get public IP
            ip_result = subprocess.run([
                'aws', 'ec2', 'describe-instances',
                '--instance-ids', instance_id,
                '--query', 'Reservations[0].Instances[0].PublicIpAddress',
                '--output', 'text'
            ], capture_output=True, text=True, check=True)
            
            public_ip = ip_result.stdout.strip()
            logger.info(f"Instance public IP: {public_ip}")
            
            return {
                'instance_id': instance_id,
                'public_ip': public_ip,
                'ssh_user': 'ubuntu',
                'ssh_key': os.getenv('AWS_SSH_KEY_PATH')
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AWS instance creation failed: {e}")
            return None
    
    def _create_gcp_instance(self):
        """Create GCP Compute Engine instance"""
        try:
            # Create firewall rules
            subprocess.run([
                'gcloud', 'compute', 'firewall-rules', 'create', f'tradebot-firewall-{self.deployment_id}',
                '--allow', 'tcp:22,tcp:5000,tcp:80,tcp:443',
                '--source-ranges', '0.0.0.0/0',
                '--description', 'TradeBot Sentinel firewall rules'
            ], check=True)
            
            # Create instance
            subprocess.run([
                'gcloud', 'compute', 'instances', 'create', f'tradebot-sentinel-{self.deployment_id}',
                '--zone', self.config.get('zone', 'us-central1-a'),
                '--machine-type', self.config.get('machine_type', 'e2-medium'),
                '--image-family', 'ubuntu-2204-lts',
                '--image-project', 'ubuntu-os-cloud',
                '--boot-disk-size', '20GB',
                '--tags', 'tradebot-sentinel'
            ], check=True)
            
            # Get external IP
            ip_result = subprocess.run([
                'gcloud', 'compute', 'instances', 'describe', f'tradebot-sentinel-{self.deployment_id}',
                '--zone', self.config.get('zone', 'us-central1-a'),
                '--format', 'get(networkInterfaces[0].accessConfigs[0].natIP)'
            ], capture_output=True, text=True, check=True)
            
            public_ip = ip_result.stdout.strip()
            logger.info(f"GCP instance created with IP: {public_ip}")
            
            return {
                'instance_id': f'tradebot-sentinel-{self.deployment_id}',
                'public_ip': public_ip,
                'ssh_user': 'ubuntu',
                'ssh_key': os.getenv('GCP_SSH_KEY_PATH')
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"GCP instance creation failed: {e}")
            return None
    
    def _create_do_instance(self):
        """Create DigitalOcean droplet"""
        token = os.getenv('DO_API_TOKEN')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get SSH key ID
        ssh_keys_response = requests.get('https://api.digitalocean.com/v2/account/keys', headers=headers)
        ssh_keys = ssh_keys_response.json()['ssh_keys']
        ssh_key_id = ssh_keys[0]['id'] if ssh_keys else None
        
        droplet_data = {
            'name': f'tradebot-sentinel-{self.deployment_id}',
            'region': self.config.get('region', 'nyc1'),
            'size': self.config.get('size', 's-2vcpu-4gb'),
            'image': 'ubuntu-22-04-x64',
            'ssh_keys': [ssh_key_id] if ssh_key_id else [],
            'monitoring': True,
            'tags': ['tradebot-sentinel']
        }
        
        try:
            response = requests.post('https://api.digitalocean.com/v2/droplets', 
                                   headers=headers, json=droplet_data)
            response.raise_for_status()
            
            droplet = response.json()['droplet']
            droplet_id = droplet['id']
            
            logger.info(f"DigitalOcean droplet created: {droplet_id}")
            
            # Wait for droplet to be active
            logger.info("Waiting for droplet to be active...")
            while True:
                status_response = requests.get(f'https://api.digitalocean.com/v2/droplets/{droplet_id}', 
                                             headers=headers)
                droplet_status = status_response.json()['droplet']
                
                if droplet_status['status'] == 'active':
                    public_ip = droplet_status['networks']['v4'][0]['ip_address']
                    logger.info(f"Droplet is active with IP: {public_ip}")
                    break
                
                time.sleep(10)
            
            return {
                'instance_id': str(droplet_id),
                'public_ip': public_ip,
                'ssh_user': 'root',
                'ssh_key': os.getenv('DO_SSH_KEY_PATH')
            }
            
        except requests.RequestException as e:
            logger.error(f"DigitalOcean droplet creation failed: {e}")
            return None
    
    def _create_contabo_instance(self):
        """Create Contabo VPS instance (manual setup required)"""
        logger.info("Contabo VPS creation requires manual setup through their control panel")
        logger.info("Please create a VPS instance and provide the IP address")
        
        public_ip = input("Enter your Contabo VPS IP address: ")
        
        return {
            'instance_id': 'contabo-manual',
            'public_ip': public_ip,
            'ssh_user': 'root',
            'ssh_key': os.getenv('CONTABO_SSH_KEY')
        }
    
    def _create_vast_instance(self):
        """Create Vast.ai instance"""
        api_key = os.getenv('VAST_API_KEY')
        headers = {'Authorization': f'Bearer {api_key}'}
        
        # Search for available instances
        search_params = {
            'verified': True,
            'external': False,
            'rentable': True,
            'gpu_name': self.config.get('gpu_type', 'RTX 3080'),
            'order': 'score-'
        }
        
        try:
            search_response = requests.get('https://console.vast.ai/api/v0/bundles/', 
                                         headers=headers, params=search_params)
            search_response.raise_for_status()
            
            offers = search_response.json()['offers']
            if not offers:
                logger.error("No available Vast.ai instances found")
                return None
            
            # Select the best offer
            best_offer = offers[0]
            
            # Create instance
            create_data = {
                'client_id': 'me',
                'image': 'pytorch/pytorch:latest',
                'args': [],
                'env': {},
                'price': best_offer['min_bid'],
                'disk': 10,
                'label': f'tradebot-sentinel-{self.deployment_id}'
            }
            
            create_response = requests.put(f'https://console.vast.ai/api/v0/asks/{best_offer["id"]}/', 
                                         headers=headers, json=create_data)
            create_response.raise_for_status()
            
            instance_data = create_response.json()
            instance_id = instance_data['new_contract']
            
            logger.info(f"Vast.ai instance created: {instance_id}")
            
            # Wait for instance to be running
            logger.info("Waiting for instance to be running...")
            while True:
                status_response = requests.get(f'https://console.vast.ai/api/v0/instances/{instance_id}/', 
                                             headers=headers)
                instance_status = status_response.json()['instances'][0]
                
                if instance_status['actual_status'] == 'running':
                    public_ip = instance_status['public_ipaddr']
                    ssh_port = instance_status['ssh_port']
                    logger.info(f"Instance is running with IP: {public_ip}:{ssh_port}")
                    break
                
                time.sleep(15)
            
            return {
                'instance_id': str(instance_id),
                'public_ip': public_ip,
                'ssh_user': 'root',
                'ssh_port': ssh_port,
                'ssh_key': os.getenv('VAST_SSH_KEY_PATH')
            }
            
        except requests.RequestException as e:
            logger.error(f"Vast.ai instance creation failed: {e}")
            return None
    
    def deploy_application(self, instance_info):
        """Deploy TradeBot Sentinel to the instance"""
        logger.info("Deploying TradeBot Sentinel...")
        
        # Wait for SSH to be available
        self._wait_for_ssh(instance_info)
        
        # Use existing deployment script
        deploy_script = './trae_deploy.sh'
        if not os.path.exists(deploy_script):
            logger.error(f"Deployment script not found: {deploy_script}")
            return False
        
        try:
            cmd = [
                deploy_script,
                '--vps-ip', instance_info['public_ip'],
                '--vps-user', instance_info['ssh_user'],
                '--ssh-key', instance_info['ssh_key']
            ]
            
            if 'ssh_port' in instance_info:
                cmd.extend(['--ssh-port', str(instance_info['ssh_port'])])
            
            subprocess.run(cmd, check=True)
            logger.info("Deployment completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def _wait_for_ssh(self, instance_info, timeout=300):
        """Wait for SSH to be available"""
        logger.info("Waiting for SSH to be available...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ssh_cmd = [
                    'ssh', '-o', 'ConnectTimeout=5',
                    '-o', 'StrictHostKeyChecking=no',
                    '-i', instance_info['ssh_key'],
                    f"{instance_info['ssh_user']}@{instance_info['public_ip']}",
                    'echo "SSH is ready"'
                ]
                
                if 'ssh_port' in instance_info:
                    ssh_cmd.extend(['-p', str(instance_info['ssh_port'])])
                
                subprocess.run(ssh_cmd, check=True, capture_output=True)
                logger.info("SSH is now available")
                return True
                
            except subprocess.CalledProcessError:
                time.sleep(10)
        
        logger.error("SSH connection timeout")
        return False
    
    def save_deployment_info(self, instance_info):
        """Save deployment information"""
        deployment_info = {
            'provider': self.provider,
            'deployment_id': self.deployment_id,
            'timestamp': datetime.now().isoformat(),
            'instance_info': instance_info,
            'config': self.config
        }
        
        with open(f'deployment_{self.deployment_id}.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info(f"Deployment info saved to deployment_{self.deployment_id}.json")

def main():
    parser = argparse.ArgumentParser(description='Deploy TradeBot Sentinel to cloud providers')
    parser.add_argument('--provider', required=True, 
                       choices=['aws', 'gcp', 'digitalocean', 'contabo', 'vast'],
                       help='Cloud provider')
    parser.add_argument('--instance-type', help='AWS instance type')
    parser.add_argument('--machine-type', help='GCP machine type')
    parser.add_argument('--size', help='DigitalOcean droplet size')
    parser.add_argument('--plan', help='Contabo VPS plan')
    parser.add_argument('--gpu-type', help='Vast.ai GPU type')
    parser.add_argument('--region', help='Cloud region/zone')
    parser.add_argument('--zone', help='GCP zone')
    parser.add_argument('--dry-run', action='store_true', help='Validate configuration only')
    
    args = parser.parse_args()
    
    # Build configuration
    config = {}
    if args.instance_type:
        config['instance_type'] = args.instance_type
    if args.machine_type:
        config['machine_type'] = args.machine_type
    if args.size:
        config['size'] = args.size
    if args.plan:
        config['plan'] = args.plan
    if args.gpu_type:
        config['gpu_type'] = args.gpu_type
    if args.region:
        config['region'] = args.region
    if args.zone:
        config['zone'] = args.zone
    
    # Create deployer
    deployer = CloudDeployer(args.provider, config)
    
    # Validate credentials
    if not deployer.validate_credentials():
        logger.error("Credential validation failed")
        sys.exit(1)
    
    if args.dry_run:
        logger.info("Dry run completed successfully")
        sys.exit(0)
    
    # Create instance
    instance_info = deployer.create_instance()
    if not instance_info:
        logger.error("Instance creation failed")
        sys.exit(1)
    
    # Deploy application
    if deployer.deploy_application(instance_info):
        deployer.save_deployment_info(instance_info)
        logger.info("\n" + "="*50)
        logger.info("DEPLOYMENT SUCCESSFUL!")
        logger.info(f"Provider: {args.provider}")
        logger.info(f"Instance ID: {instance_info['instance_id']}")
        logger.info(f"Public IP: {instance_info['public_ip']}")
        logger.info(f"SSH User: {instance_info['ssh_user']}")
        logger.info(f"TradeBot URL: http://{instance_info['public_ip']}:5000")
        logger.info("="*50)
    else:
        logger.error("Deployment failed")
        sys.exit(1)

if __name__ == '__main__':
    main()