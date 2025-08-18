#!/usr/bin/env python3
"""
🤖 TradeBot Sentinel - Deployment Readiness Verification

This script verifies that all deployment requirements are met
and provides a comprehensive readiness report.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def check_deployment_package():
    """Verify deployment package completeness"""
    print("🔍 Checking deployment package...")
    
    deploy_dir = Path("deployment_package")
    required_files = {
        ".env": "Environment configuration with Bulenox credentials",
        "setup_vps.sh": "VPS setup and dependency installation script",
        "tradebot-sentinel.service": "Systemd service configuration",
        "DEPLOYMENT_INSTRUCTIONS.md": "Complete deployment guide",
        "quick_deploy.sh": "Automated deployment script"
    }
    
    results = {}
    all_present = True
    
    for filename, description in required_files.items():
        file_path = deploy_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size
            results[filename] = {
                "status": "✅ PRESENT",
                "size": f"{size:,} bytes",
                "description": description
            }
            print(f"  ✅ {filename} ({size:,} bytes)")
        else:
            results[filename] = {
                "status": "❌ MISSING",
                "size": "0 bytes",
                "description": description
            }
            print(f"  ❌ {filename} - MISSING")
            all_present = False
    
    return all_present, results

def check_env_configuration():
    """Verify .env file contains required Bulenox credentials"""
    print("\n🔧 Checking environment configuration...")
    
    env_file = Path("deployment_package/.env")
    if not env_file.exists():
        print("  ❌ .env file not found")
        return False, {}
    
    required_vars = {
        "BULENOX_USERNAME": "BX64883",
        "BULENOX_PASSWORD": "XujhMzFf6K",
        "BROKER_USERNAME": "BX64883",
        "BROKER_PASSWORD": "XujhMzFf6K",
        "HEADLESS": "true",
        "AUTOMATION_HEADLESS": "true",
        "INTERCEPT_TRADE_REQUESTS": "true",
        "SAVE_CURL_COMMANDS": "true",
        "AUTO_CONVERT_TO_PYTHON": "true"
    }
    
    env_content = env_file.read_text(encoding='utf-8')
    results = {}
    all_configured = True
    
    for var, expected_value in required_vars.items():
        if f"{var}={expected_value}" in env_content:
            results[var] = {"status": "✅ CONFIGURED", "value": expected_value}
            print(f"  ✅ {var}={expected_value}")
        else:
            results[var] = {"status": "❌ MISSING/INCORRECT", "value": "Not found"}
            print(f"  ❌ {var} - Missing or incorrect")
            all_configured = False
    
    return all_configured, results

def check_project_structure():
    """Verify main project files are present"""
    print("\n📁 Checking project structure...")
    
    required_files = {
        "main.py": "Main application entry point",
        "requirements.txt": "Python dependencies",
        "trade_request_full.py": "Generated Python trading implementation",
        "login_bulenox.py": "Bulenox login automation",
        "README.md": "Project documentation"
    }
    
    results = {}
    all_present = True
    
    for filename, description in required_files.items():
        file_path = Path(filename)
        if file_path.exists():
            size = file_path.stat().st_size
            results[filename] = {
                "status": "✅ PRESENT",
                "size": f"{size:,} bytes",
                "description": description
            }
            print(f"  ✅ {filename} ({size:,} bytes)")
        else:
            results[filename] = {
                "status": "❌ MISSING",
                "size": "0 bytes",
                "description": description
            }
            print(f"  ❌ {filename} - MISSING")
            all_present = False
    
    return all_present, results

def check_log_directories():
    """Verify log directories exist locally"""
    print("\n📋 Checking log directories...")
    
    required_dirs = {
        "logs": "Main log directory",
        "logs/curls": "cURL command storage",
        "logs/json": "JSON request/response logs",
        "logs/screenshots": "Error screenshots"
    }
    
    results = {}
    all_present = True
    
    for dirname, description in required_dirs.items():
        dir_path = Path(dirname)
        if dir_path.exists() and dir_path.is_dir():
            file_count = len(list(dir_path.glob("*")))
            results[dirname] = {
                "status": "✅ EXISTS",
                "files": f"{file_count} files",
                "description": description
            }
            print(f"  ✅ {dirname}/ ({file_count} files)")
        else:
            results[dirname] = {
                "status": "❌ MISSING",
                "files": "0 files",
                "description": description
            }
            print(f"  ❌ {dirname}/ - MISSING")
            all_present = False
    
    return all_present, results

def check_captured_endpoints():
    """Check if trade endpoints have been captured"""
    print("\n🎯 Checking captured trade endpoints...")
    
    curls_dir = Path("logs/curls")
    if not curls_dir.exists():
        print("  ❌ No curls directory found")
        return False, {}
    
    curl_files = list(curls_dir.glob("*.curl")) + list(curls_dir.glob("*.sh"))
    
    if not curl_files:
        print("  ⚠️ No captured endpoints found")
        return False, {"captured_files": 0, "status": "No endpoints captured yet"}
    
    # Count different types of endpoints
    trade_files = [f for f in curl_files if any(keyword in f.name.lower() for keyword in ['trade', 'order', 'position'])]
    
    results = {
        "total_files": len(curl_files),
        "trade_files": len(trade_files),
        "status": "✅ ENDPOINTS CAPTURED" if trade_files else "⚠️ NO TRADE ENDPOINTS"
    }
    
    print(f"  📊 Total captured files: {len(curl_files)}")
    print(f"  🎯 Trade-related files: {len(trade_files)}")
    
    return len(trade_files) > 0, results

def generate_readiness_report():
    """Generate comprehensive readiness report"""
    print("\n" + "="*60)
    print("🤖 TradeBot Sentinel - Deployment Readiness Report")
    print("="*60)
    
    # Run all checks
    package_ok, package_results = check_deployment_package()
    env_ok, env_results = check_env_configuration()
    project_ok, project_results = check_project_structure()
    logs_ok, logs_results = check_log_directories()
    endpoints_ok, endpoints_results = check_captured_endpoints()
    
    # Calculate overall readiness
    critical_checks = [package_ok, env_ok, project_ok]
    optional_checks = [logs_ok, endpoints_ok]
    
    overall_ready = all(critical_checks)
    
    # Create comprehensive report
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "✅ READY FOR DEPLOYMENT" if overall_ready else "❌ NOT READY",
        "critical_checks": {
            "deployment_package": package_ok,
            "environment_config": env_ok,
            "project_structure": project_ok
        },
        "optional_checks": {
            "log_directories": logs_ok,
            "captured_endpoints": endpoints_ok
        },
        "detailed_results": {
            "deployment_package": package_results,
            "environment_config": env_results,
            "project_structure": project_results,
            "log_directories": logs_results,
            "captured_endpoints": endpoints_results
        },
        "deployment_instructions": {
            "quick_deploy": "cd deployment_package && ./quick_deploy.sh YOUR_VPS_IP",
            "manual_deploy": "Follow instructions in deployment_package/DEPLOYMENT_INSTRUCTIONS.md",
            "file_transfer": "Upload ai-trading-sentinel/ to VPS and run setup_vps.sh"
        },
        "next_steps": [
            "Choose deployment method (quick/manual/file transfer)",
            "Transfer files to Contabo VPS",
            "Run setup_vps.sh on VPS",
            "Copy .env file to VPS project directory",
            "Install and start systemd service",
            "Monitor logs for successful automation"
        ]
    }
    
    # Save report
    report_file = f"deployment_readiness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n📊 READINESS SUMMARY:")
    print(f"  Overall Status: {report['overall_status']}")
    print(f"  Deployment Package: {'✅ READY' if package_ok else '❌ ISSUES'}")
    print(f"  Environment Config: {'✅ READY' if env_ok else '❌ ISSUES'}")
    print(f"  Project Structure: {'✅ READY' if project_ok else '❌ ISSUES'}")
    print(f"  Log Directories: {'✅ READY' if logs_ok else '⚠️ MISSING'}")
    print(f"  Captured Endpoints: {'✅ READY' if endpoints_ok else '⚠️ NONE'}")
    
    print("\n🎯 DEPLOYMENT READINESS:")
    if overall_ready:
        print("  ✅ READY FOR CONTABO VPS DEPLOYMENT")
        print("  ✅ Bulenox credentials configured (BX64883)")
        print("  ✅ Headless Chrome settings enabled")
        print("  ✅ All deployment files prepared")
        print("\n🚀 NEXT STEPS:")
        print("  1. Choose deployment method:")
        print("     - Quick: cd deployment_package && ./quick_deploy.sh YOUR_VPS_IP")
        print("     - Manual: Follow DEPLOYMENT_INSTRUCTIONS.md")
        print("  2. Execute deployment to your Contabo VPS")
        print("  3. Start TradeBot Sentinel service")
        print("  4. Monitor automation logs")
    else:
        print("  ❌ NOT READY - Issues found")
        print("  🔧 Fix the issues above before deployment")
    
    print(f"\n📄 Detailed report saved: {report_file}")
    
    return overall_ready, report

def main():
    """Main verification function"""
    print("🤖 TradeBot Sentinel - Deployment Readiness Verification")
    print("Starting comprehensive readiness check...\n")
    
    ready, report = generate_readiness_report()
    
    if ready:
        print("\n🎉 DEPLOYMENT READY!")
        print("Your TradeBot Sentinel system is ready for Contabo VPS deployment.")
        return 0
    else:
        print("\n⚠️ DEPLOYMENT NOT READY")
        print("Please address the issues identified above.")
        return 1

if __name__ == "__main__":
    exit(main())