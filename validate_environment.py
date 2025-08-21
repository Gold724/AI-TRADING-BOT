#!/usr/bin/env python3
"""
AI Trading Sentinel - Environment Variables Validation Script
TRAE-SentinelOps Production Deployment Validator

This script validates all required environment variables for production deployment.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Required environment variables for different deployment modes
REQUIRED_VARS = {
    'vps_deployment': [
        'CONTABO_VPS_IP',
        'CONTABO_VPS_USER', 
        'CONTABO_SSH_KEY_PATH'
    ],
    'github_integration': [
        'GITHUB_TOKEN',
        'GITHUB_REPO_URL'
    ],
    'trading_platform': [
        'BULENOX_USERNAME',
        'BULENOX_PASSWORD'
    ],
    'web_application': [
        'FLASK_SECRET_KEY',
        'JWT_SECRET_KEY'
    ],
    'monitoring': [
        'SLACK_WEBHOOK_URL'
    ]
}

# Optional but recommended variables
OPTIONAL_VARS = {
    'enhanced_monitoring': [
        'SMTP_SERVER',
        'SMTP_USERNAME', 
        'SMTP_PASSWORD',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ],
    'security': [
        'API_RATE_LIMIT',
        'API_CORS_ORIGINS',
        'SSL_CERT_PATH',
        'SSL_KEY_PATH'
    ],
    'trading_config': [
        'TRADING_MAX_RISK_PERCENT',
        'TRADING_STOP_LOSS_PERCENT',
        'TRADING_TAKE_PROFIT_PERCENT'
    ]
}

def check_environment_variables() -> Dict:
    """Check all environment variables and return validation results"""
    results = {
        'status': 'success',
        'missing_required': [],
        'missing_optional': [],
        'present_vars': [],
        'validation_errors': [],
        'recommendations': []
    }
    
    # Check required variables
    for category, vars_list in REQUIRED_VARS.items():
        for var in vars_list:
            value = os.getenv(var)
            if not value:
                results['missing_required'].append(f"{var} ({category})")
                results['status'] = 'failed'
            else:
                results['present_vars'].append(f"{var} ({category})")
                
                # Validate specific variables
                if var == 'CONTABO_SSH_KEY_PATH':
                    if not Path(value).exists():
                        results['validation_errors'].append(f"SSH key file not found: {value}")
                        
                elif var == 'GITHUB_TOKEN':
                    if not value.startswith('ghp_'):
                        results['validation_errors'].append("GitHub token should start with 'ghp_'")
                        
                elif var == 'CONTABO_VPS_IP':
                    # Basic IP validation
                    parts = value.split('.')
                    if len(parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
                        results['validation_errors'].append(f"Invalid IP address format: {value}")
    
    # Check optional variables
    for category, vars_list in OPTIONAL_VARS.items():
        for var in vars_list:
            value = os.getenv(var)
            if not value:
                results['missing_optional'].append(f"{var} ({category})")
            else:
                results['present_vars'].append(f"{var} ({category})")
    
    # Generate recommendations
    if results['missing_required']:
        results['recommendations'].append("Set all required environment variables before deployment")
        results['recommendations'].append("Refer to ENVIRONMENT_SETUP_GUIDE.md for detailed instructions")
    
    if results['missing_optional']:
        results['recommendations'].append("Consider setting optional variables for enhanced functionality")
    
    if results['validation_errors']:
        results['status'] = 'warning' if results['status'] == 'success' else 'failed'
        results['recommendations'].append("Fix validation errors before proceeding")
    
    return results

def check_env_file() -> Dict:
    """Check if .env file exists and is properly configured"""
    env_file = Path('.env')
    env_template = Path('.env.template')
    
    result = {
        'env_file_exists': env_file.exists(),
        'env_template_exists': env_template.exists(),
        'recommendations': []
    }
    
    if not result['env_file_exists']:
        if result['env_template_exists']:
            result['recommendations'].append("Copy .env.template to .env and configure your values")
        else:
            result['recommendations'].append("Create .env file with your environment variables")
    
    return result

def validate_deployment_readiness() -> bool:
    """Validate if system is ready for deployment"""
    env_results = check_environment_variables()
    file_results = check_env_file()
    
    print("🔍 AI Trading Sentinel - Environment Validation")
    print("=" * 50)
    
    # Print environment variables status
    print(f"\n📊 Environment Variables Status: {env_results['status'].upper()}")
    
    if env_results['present_vars']:
        print(f"\n✅ Present Variables ({len(env_results['present_vars'])}):") 
        for var in env_results['present_vars']:
            print(f"   • {var}")
    
    if env_results['missing_required']:
        print(f"\n❌ Missing Required Variables ({len(env_results['missing_required'])}):") 
        for var in env_results['missing_required']:
            print(f"   • {var}")
    
    if env_results['missing_optional']:
        print(f"\n⚠️  Missing Optional Variables ({len(env_results['missing_optional'])}):") 
        for var in env_results['missing_optional']:
            print(f"   • {var}")
    
    if env_results['validation_errors']:
        print(f"\n🚨 Validation Errors ({len(env_results['validation_errors'])}):") 
        for error in env_results['validation_errors']:
            print(f"   • {error}")
    
    # Print file status
    print(f"\n📁 Configuration Files:")
    print(f"   • .env file: {'✅ Present' if file_results['env_file_exists'] else '❌ Missing'}")
    print(f"   • .env.template: {'✅ Present' if file_results['env_template_exists'] else '❌ Missing'}")
    
    # Print recommendations
    all_recommendations = env_results['recommendations'] + file_results['recommendations']
    if all_recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(all_recommendations, 1):
            print(f"   {i}. {rec}")
    
    # Deployment readiness assessment
    is_ready = (
        env_results['status'] in ['success', 'warning'] and
        not env_results['missing_required'] and
        file_results['env_file_exists']
    )
    
    print(f"\n🎯 Deployment Readiness: {'✅ READY' if is_ready else '❌ NOT READY'}")
    
    if is_ready:
        print("\n🚀 System is ready for production deployment!")
        print("   Run: python execute_production_deployment.py")
    else:
        print("\n⚠️  Please address the issues above before deployment.")
        print("   Refer to: ENVIRONMENT_SETUP_GUIDE.md")
    
    return is_ready

def generate_env_template():
    """Generate .env.template file with all variables"""
    template_content = "# AI Trading Sentinel - Environment Variables Template\n"
    template_content += "# Copy this file to .env and configure your values\n\n"
    
    # Add required variables
    template_content += "# =============================================================================\n"
    template_content += "# REQUIRED VARIABLES (Must be set for deployment)\n"
    template_content += "# =============================================================================\n\n"
    
    for category, vars_list in REQUIRED_VARS.items():
        template_content += f"# {category.replace('_', ' ').title()}\n"
        for var in vars_list:
            template_content += f"{var}=\n"
        template_content += "\n"
    
    # Add optional variables
    template_content += "# =============================================================================\n"
    template_content += "# OPTIONAL VARIABLES (Recommended for enhanced functionality)\n"
    template_content += "# =============================================================================\n\n"
    
    for category, vars_list in OPTIONAL_VARS.items():
        template_content += f"# {category.replace('_', ' ').title()}\n"
        for var in vars_list:
            template_content += f"# {var}=\n"
        template_content += "\n"
    
    # Write template file
    with open('.env.template', 'w') as f:
        f.write(template_content)
    
    print("✅ Generated .env.template file")
    print("   Copy to .env and configure your values")

def main():
    """Main validation function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--generate-template':
        generate_env_template()
        return
    
    # Run validation
    is_ready = validate_deployment_readiness()
    
    # Save validation results
    env_results = check_environment_variables()
    file_results = check_env_file()
    
    validation_report = {
        'timestamp': str(Path().resolve()),
        'deployment_ready': is_ready,
        'environment_variables': env_results,
        'configuration_files': file_results
    }
    
    with open('environment_validation_report.json', 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    print(f"\n📄 Validation report saved: environment_validation_report.json")
    
    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)

if __name__ == '__main__':
    main()