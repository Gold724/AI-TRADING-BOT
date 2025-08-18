#!/usr/bin/env python3
"""
TradeBot Sentinel Test Script
Quick test to verify the automation is working properly
"""

import asyncio
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

async def test_imports():
    """Test if all required modules can be imported"""
    console.print("[bold blue]Testing imports...[/bold blue]")
    
    try:
        from playwright.async_api import async_playwright
        console.print("✅ Playwright imported successfully")
    except ImportError as e:
        console.print(f"❌ Playwright import failed: {e}")
        return False
    
    try:
        import curlconverter
        console.print("✅ curlconverter imported successfully")
    except ImportError as e:
        console.print(f"❌ curlconverter import failed: {e}")
        return False
    
    try:
        import requests
        console.print("✅ requests imported successfully")
    except ImportError as e:
        console.print(f"❌ requests import failed: {e}")
        return False
    
    return True

async def test_playwright_browser():
    """Test if Playwright can launch a browser"""
    console.print("[bold blue]Testing Playwright browser launch...[/bold blue]")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://httpbin.org/get")
            title = await page.title()
            await browser.close()
            
            console.print(f"✅ Browser launched successfully, page title: {title}")
            return True
            
    except Exception as e:
        console.print(f"❌ Browser test failed: {e}")
        return False

def test_environment():
    """Test environment setup"""
    console.print("[bold blue]Testing environment setup...[/bold blue]")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        console.print("✅ .env file found")
    else:
        console.print("⚠️  .env file not found (optional)")
    
    # Check if tradebot_sentinel.py exists
    main_script = Path("tradebot_sentinel.py")
    if main_script.exists():
        console.print("✅ tradebot_sentinel.py found")
    else:
        console.print("❌ tradebot_sentinel.py not found")
        return False
    
    return True

def test_curlconverter():
    """Test curlconverter functionality"""
    console.print("[bold blue]Testing curlconverter...[/bold blue]")
    
    try:
        import curlconverter
        
        # Test cURL command conversion using CurlConverter class
        test_curl = "curl -X POST https://httpbin.org/post -H 'Content-Type: application/json' -d '{\"test\": \"data\"}'"
        
        # Just test that we can create a converter instance
        converter = curlconverter.CurlConverter(test_curl)
        
        # Verify the converter has the curl command stored
        if hasattr(converter, 'curl_command') and converter.curl_command:
            console.print("✅ curlconverter working correctly")
            return True
        else:
            console.print("❌ curlconverter instance creation failed")
            return False
            
    except Exception as e:
        console.print(f"❌ curlconverter test failed: {e}")
        return False

async def main():
    """Run all tests"""
    console.print(Panel.fit(
        Text("TradeBot Sentinel - System Test", justify="center"),
        style="bold green"
    ))
    
    tests = [
        ("Environment Setup", test_environment),
        ("Module Imports", test_imports),
        ("curlconverter", test_curlconverter),
        ("Playwright Browser", test_playwright_browser),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n[bold yellow]Running {test_name} test...[/bold yellow]")
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
            
        results.append((test_name, result))
    
    # Summary
    console.print("\n" + "="*50)
    console.print("[bold blue]Test Summary:[/bold blue]")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        console.print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    console.print(f"\n[bold]Results: {passed}/{len(results)} tests passed[/bold]")
    
    if passed == len(results):
        console.print("\n[bold green]🎉 All tests passed! TradeBot Sentinel is ready to use.[/bold green]")
    else:
        console.print("\n[bold red]⚠️  Some tests failed. Please check the setup.[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())