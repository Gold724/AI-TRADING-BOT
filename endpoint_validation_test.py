#!/usr/bin/env python3
"""
TradeBot Sentinel - Endpoint Validation Test
Validates all captured trade endpoints and generates a comprehensive report
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class EndpointValidator:
    def __init__(self):
        self.curls_dir = Path("logs/curls")
        self.json_dir = Path("logs/json")
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "validated_endpoints": [],
            "trade_operations": {
                "buy_orders": [],
                "sell_orders": [],
                "position_close": [],
                "layouts": [],
                "charts": [],
                "login": []
            },
            "errors": [],
            "summary": {}
        }
    
    def extract_curl_data(self, curl_file: Path) -> Dict[str, Any]:
        """Extract data from cURL file."""
        try:
            with open(curl_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract URL
            url_match = re.search(r"curl -X (\w+) '([^']+)'", content)
            method = url_match.group(1) if url_match else "UNKNOWN"
            url = url_match.group(2) if url_match else "UNKNOWN"
            
            # Extract JSON data
            json_data = None
            json_match = re.search(r"-d '({.*})'", content, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    json_data = "INVALID_JSON"
            
            # Extract headers
            headers = {}
            header_matches = re.findall(r"-H '([^:]+): ([^']+)'", content)
            for header_name, header_value in header_matches:
                headers[header_name] = header_value
            
            return {
                "file": curl_file.name,
                "method": method,
                "url": url,
                "headers": headers,
                "json_data": json_data,
                "has_auth": "authorization" in headers,
                "content_length": len(content)
            }
        except Exception as e:
            return {
                "file": curl_file.name,
                "error": str(e),
                "method": "ERROR",
                "url": "ERROR"
            }
    
    def categorize_endpoint(self, endpoint_data: Dict[str, Any]) -> str:
        """Categorize endpoint based on URL and data."""
        url = endpoint_data.get("url", "").lower()
        json_data = endpoint_data.get("json_data", {})
        
        if "/order" in url:
            if isinstance(json_data, dict):
                position_size = json_data.get("positionSize", 0)
                if position_size > 0:
                    return "buy_orders"
                elif position_size < 0:
                    return "sell_orders"
            return "buy_orders"  # Default for order endpoint
        elif "/position/close" in url:
            return "position_close"
        elif "/layouts" in url:
            return "layouts"
        elif "/charts" in url:
            return "charts"
        elif "/login" in url or "/auth" in url:
            return "login"
        else:
            return "other"
    
    def validate_trade_data(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trade-specific data."""
        validation = {
            "valid": True,
            "issues": []
        }
        
        json_data = endpoint_data.get("json_data")
        if isinstance(json_data, dict):
            # Check required trade fields
            required_fields = ["accountId", "symbolId"]
            for field in required_fields:
                if field not in json_data:
                    validation["issues"].append(f"Missing required field: {field}")
                    validation["valid"] = False
            
            # Validate position size
            if "positionSize" in json_data:
                pos_size = json_data["positionSize"]
                if not isinstance(pos_size, (int, float)) or pos_size == 0:
                    validation["issues"].append(f"Invalid positionSize: {pos_size}")
                    validation["valid"] = False
        
        # Check authentication
        if not endpoint_data.get("has_auth"):
            validation["issues"].append("Missing authorization header")
            validation["valid"] = False
        
        return validation
    
    def validate_all_endpoints(self):
        """Validate all captured endpoints."""
        print("🔍 Starting endpoint validation...")
        
        if not self.curls_dir.exists():
            self.validation_results["errors"].append("cURLs directory not found")
            return
        
        curl_files = list(self.curls_dir.glob("*.curl")) + list(self.curls_dir.glob("*.sh"))
        self.validation_results["total_files"] = len(curl_files)
        
        print(f"📁 Found {len(curl_files)} cURL files to validate")
        
        for curl_file in curl_files:
            print(f"   Validating: {curl_file.name}")
            
            endpoint_data = self.extract_curl_data(curl_file)
            
            if "error" in endpoint_data:
                self.validation_results["errors"].append({
                    "file": curl_file.name,
                    "error": endpoint_data["error"]
                })
                continue
            
            # Categorize and validate
            category = self.categorize_endpoint(endpoint_data)
            validation = self.validate_trade_data(endpoint_data)
            
            endpoint_result = {
                **endpoint_data,
                "category": category,
                "validation": validation
            }
            
            self.validation_results["validated_endpoints"].append(endpoint_result)
            
            # Add to category
            if category in self.validation_results["trade_operations"]:
                self.validation_results["trade_operations"][category].append(endpoint_result)
    
    def generate_summary(self):
        """Generate validation summary."""
        operations = self.validation_results["trade_operations"]
        
        self.validation_results["summary"] = {
            "total_endpoints": len(self.validation_results["validated_endpoints"]),
            "buy_orders_count": len(operations["buy_orders"]),
            "sell_orders_count": len(operations["sell_orders"]),
            "position_close_count": len(operations["position_close"]),
            "layout_requests": len(operations["layouts"]),
            "chart_requests": len(operations["charts"]),
            "login_requests": len(operations["login"]),
            "valid_endpoints": len([e for e in self.validation_results["validated_endpoints"] if e["validation"]["valid"]]),
            "invalid_endpoints": len([e for e in self.validation_results["validated_endpoints"] if not e["validation"]["valid"]]),
            "total_errors": len(self.validation_results["errors"])
        }
    
    def save_report(self, format_type: str = "json"):
        """Save validation report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "json":
            report_file = f"endpoint_validation_report_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2, default=str)
            print(f"📄 JSON report saved: {report_file}")
        
        elif format_type == "markdown":
            report_file = f"endpoint_validation_report_{timestamp}.md"
            self.save_markdown_report(report_file)
            print(f"📄 Markdown report saved: {report_file}")
    
    def save_markdown_report(self, filename: str):
        """Save validation report in Markdown format."""
        summary = self.validation_results["summary"]
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# TradeBot Sentinel - Endpoint Validation Report\n\n")
            f.write(f"**Generated:** {self.validation_results['timestamp']}\n\n")
            
            # Summary
            f.write("## 📊 Summary\n\n")
            f.write(f"- **Total Endpoints:** {summary['total_endpoints']}\n")
            f.write(f"- **Valid Endpoints:** {summary['valid_endpoints']}\n")
            f.write(f"- **Invalid Endpoints:** {summary['invalid_endpoints']}\n")
            f.write(f"- **Total Errors:** {summary['total_errors']}\n\n")
            
            # Trade Operations
            f.write("## 🔄 Trade Operations\n\n")
            f.write(f"- **BUY Orders:** {summary['buy_orders_count']}\n")
            f.write(f"- **SELL Orders:** {summary['sell_orders_count']}\n")
            f.write(f"- **Position Close:** {summary['position_close_count']}\n")
            f.write(f"- **Layout Requests:** {summary['layout_requests']}\n")
            f.write(f"- **Chart Requests:** {summary['chart_requests']}\n")
            f.write(f"- **Login Requests:** {summary['login_requests']}\n\n")
            
            # Detailed Endpoints
            f.write("## 📋 Detailed Endpoint Analysis\n\n")
            
            for category, endpoints in self.validation_results["trade_operations"].items():
                if endpoints:
                    f.write(f"### {category.replace('_', ' ').title()}\n\n")
                    for endpoint in endpoints:
                        status = "✅" if endpoint["validation"]["valid"] else "❌"
                        f.write(f"- {status} **{endpoint['method']}** `{endpoint['url']}`\n")
                        if endpoint["validation"]["issues"]:
                            for issue in endpoint["validation"]["issues"]:
                                f.write(f"  - ⚠️ {issue}\n")
                    f.write("\n")
            
            # Errors
            if self.validation_results["errors"]:
                f.write("## ❌ Errors\n\n")
                for error in self.validation_results["errors"]:
                    f.write(f"- **{error.get('file', 'Unknown')}:** {error.get('error', 'Unknown error')}\n")
                f.write("\n")
    
    def print_console_report(self):
        """Print validation report to console."""
        summary = self.validation_results["summary"]
        
        print("\n" + "="*60)
        print("🎯 TRADEBOT SENTINEL - ENDPOINT VALIDATION REPORT")
        print("="*60)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Endpoints: {summary['total_endpoints']}")
        print(f"   Valid Endpoints: {summary['valid_endpoints']} ✅")
        print(f"   Invalid Endpoints: {summary['invalid_endpoints']} ❌")
        print(f"   Total Errors: {summary['total_errors']}")
        
        print(f"\n🔄 TRADE OPERATIONS:")
        print(f"   BUY Orders: {summary['buy_orders_count']}")
        print(f"   SELL Orders: {summary['sell_orders_count']}")
        print(f"   Position Close: {summary['position_close_count']}")
        print(f"   Layout Requests: {summary['layout_requests']}")
        print(f"   Chart Requests: {summary['chart_requests']}")
        print(f"   Login Requests: {summary['login_requests']}")
        
        if self.validation_results["errors"]:
            print(f"\n❌ ERRORS:")
            for error in self.validation_results["errors"]:
                print(f"   - {error.get('file', 'Unknown')}: {error.get('error', 'Unknown error')}")
        
        print("\n" + "="*60)

def main():
    validator = EndpointValidator()
    validator.validate_all_endpoints()
    validator.generate_summary()
    validator.print_console_report()
    validator.save_report("json")
    validator.save_report("markdown")
    
    print("\n🎉 Validation completed successfully!")
    print("📁 Check endpoint_validation_report_*.json for detailed JSON report")
    print("📄 Check endpoint_validation_report_*.md for Markdown report")

if __name__ == "__main__":
    main()