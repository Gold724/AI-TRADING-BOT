#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Request Interceptor for TradeBot Sentinel

This module provides network request interception capabilities to capture
trade execution requests from the Bulenox trading platform.

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import re
from typing import Optional, Dict, Any, List, Callable
from playwright.async_api import Page, Request, Response
from urllib.parse import urlparse, parse_qs
import time
from pathlib import Path

class RequestInterceptor:
    """Handles network request interception for trade execution detection."""
    
    def __init__(self, page: Page, logger: Optional[logging.Logger] = None):
        """Initialize the request interceptor.
        
        Args:
            page: Playwright page instance
            logger: Optional logger instance
        """
        self.page = page
        self.logger = logger or logging.getLogger(__name__)
        self.intercepted_requests = []
        self.trade_requests = []
        self.is_intercepting = False
        
        # Keywords that indicate trade execution requests
        self.trade_keywords = [
            'symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell',
            'quantity', 'side', 'instrument', 'execute', 'position',
            'market', 'limit', 'stop', 'orderType', 'orderSide',
            'tradingPair', 'volume', 'leverage', 'margin'
        ]
        
        # URL patterns that might indicate trading endpoints
        self.trade_url_patterns = [
            r'/api/.*trade.*',
            r'/api/.*order.*',
            r'/api/.*position.*',
            r'/api/.*execute.*',
            r'/trading/.*',
            r'/order/.*',
            r'/v\d+/.*trade.*',
            r'/v\d+/.*order.*'
        ]
        
        # HTTP methods to monitor
        self.monitored_methods = ['POST', 'PUT', 'PATCH']
        
    async def start_interception(self) -> None:
        """Start intercepting network requests."""
        if self.is_intercepting:
            self.logger.warning("Request interception already active")
            return
        
        self.logger.info("Starting network request interception...")
        
        # Set up request and response handlers
        self.page.on('request', self._handle_request)
        self.page.on('response', self._handle_response)
        
        self.is_intercepting = True
        self.logger.info("Network request interception started")
    
    async def stop_interception(self) -> None:
        """Stop intercepting network requests."""
        if not self.is_intercepting:
            self.logger.warning("Request interception not active")
            return
        
        self.logger.info("Stopping network request interception...")
        
        # Remove event handlers
        self.page.remove_listener('request', self._handle_request)
        self.page.remove_listener('response', self._handle_response)
        
        self.is_intercepting = False
        self.logger.info("Network request interception stopped")
    
    async def _handle_request(self, request: Request) -> None:
        """Handle intercepted requests.
        
        Args:
            request: Intercepted request object
        """
        try:
            # Log all POST requests
            if request.method in self.monitored_methods:
                self.logger.debug(f"Intercepted {request.method} request: {request.url}")
                
                # Store request details
                request_data = {
                    'timestamp': time.time(),
                    'method': request.method,
                    'url': request.url,
                    'headers': dict(request.headers),
                    'post_data': None,
                    'is_trade_request': False
                }
                
                # Get POST data if available
                try:
                    post_data = request.post_data
                    if post_data:
                        request_data['post_data'] = post_data
                        
                        # Check if this might be a trade request
                        if self._is_trade_request(request.url, post_data, dict(request.headers)):
                            request_data['is_trade_request'] = True
                            self.trade_requests.append(request_data)
                            self.logger.info(f"🎯 TRADE REQUEST DETECTED: {request.method} {request.url}")
                            
                            # Save trade request immediately
                            await self._save_trade_request(request_data)
                            
                except Exception as e:
                    self.logger.debug(f"Could not get POST data: {e}")
                
                self.intercepted_requests.append(request_data)
        
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
    
    async def _handle_response(self, response: Response) -> None:
        """Handle intercepted responses.
        
        Args:
            response: Intercepted response object
        """
        try:
            # Log responses to potential trade requests
            if response.request.method in self.monitored_methods:
                self.logger.debug(f"Response {response.status} for {response.request.method} {response.url}")
                
                # If this was a trade request, log the response
                if any(req['url'] == response.url and req['is_trade_request'] 
                      for req in self.trade_requests):
                    try:
                        response_text = await response.text()
                        self.logger.info(f"Trade request response ({response.status}): {response_text[:200]}...")
                    except Exception as e:
                        self.logger.debug(f"Could not get response text: {e}")
        
        except Exception as e:
            self.logger.error(f"Error handling response: {e}")
    
    def _is_trade_request(self, url: str, post_data: str, headers: Dict[str, str]) -> bool:
        """Determine if a request is likely a trade execution request.
        
        Args:
            url: Request URL
            post_data: POST data as string
            headers: Request headers
            
        Returns:
            True if likely a trade request, False otherwise
        """
        try:
            # Check URL patterns
            for pattern in self.trade_url_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    self.logger.debug(f"Trade URL pattern matched: {pattern}")
                    return True
            
            # Check POST data for trade keywords
            if post_data:
                post_data_lower = post_data.lower()
                
                # Try to parse as JSON
                try:
                    json_data = json.loads(post_data)
                    json_str = json.dumps(json_data).lower()
                    
                    # Check for trade keywords in JSON
                    keyword_count = sum(1 for keyword in self.trade_keywords 
                                      if keyword in json_str)
                    
                    if keyword_count >= 2:  # At least 2 trade keywords
                        self.logger.debug(f"Trade keywords found in JSON: {keyword_count}")
                        return True
                        
                except json.JSONDecodeError:
                    # Not JSON, check as plain text
                    keyword_count = sum(1 for keyword in self.trade_keywords 
                                      if keyword in post_data_lower)
                    
                    if keyword_count >= 2:
                        self.logger.debug(f"Trade keywords found in POST data: {keyword_count}")
                        return True
            
            # Check headers for trading-related content types or custom headers
            content_type = headers.get('content-type', '').lower()
            if 'application/json' in content_type and post_data:
                # Additional JSON analysis
                try:
                    json_data = json.loads(post_data)
                    # Look for common trading fields
                    trading_fields = ['symbol', 'amount', 'price', 'side', 'orderType']
                    if any(field in json_data for field in trading_fields):
                        self.logger.debug("Trading fields found in JSON data")
                        return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error analyzing trade request: {e}")
            return False
    
    async def _save_trade_request(self, request_data: Dict[str, Any]) -> None:
        """Save trade request to file for analysis.
        
        Args:
            request_data: Request data dictionary
        """
        try:
            timestamp = int(request_data['timestamp'])
            filename = f"trade_request_{timestamp}.json"
            
            # Save detailed request data
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, indent=2, default=str)
            
            self.logger.info(f"Trade request saved to: {filename}")
            
            # Also generate cURL command immediately
            await self._generate_curl_command(request_data)
            
        except Exception as e:
            self.logger.error(f"Error saving trade request: {e}")
    
    async def _generate_curl_command(self, request_data: Dict[str, Any]) -> None:
        """Generate cURL command for the trade request.
        
        Args:
            request_data: Request data dictionary
        """
        try:
            url = request_data['url']
            method = request_data['method']
            headers = request_data['headers']
            post_data = request_data['post_data']
            
            # Build cURL command
            curl_parts = ['curl']
            
            # Add method
            if method != 'GET':
                curl_parts.append(f'-X {method}')
            
            # Add headers
            for header_name, header_value in headers.items():
                # Skip some headers that curl adds automatically
                if header_name.lower() not in ['content-length', 'host']:
                    curl_parts.append(f'-H "{header_name}: {header_value}"')
            
            # Add POST data
            if post_data:
                # Escape quotes in data
                escaped_data = post_data.replace('"', '\\"')
                curl_parts.append(f'-d "{escaped_data}"')
            
            # Add URL
            curl_parts.append(f'"{url}"')
            
            # Join command
            curl_command = ' \\
  '.join(curl_parts)
            
            # Save to trade.sh file
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write('#!/bin/bash\n')
                f.write('# Generated cURL command for trade execution\n')
                f.write(f'# Timestamp: {time.ctime(request_data["timestamp"])}\n')
                f.write('\n')
                f.write(curl_command)
                f.write('\n')
            
            self.logger.info("cURL command saved to trade.sh")
            
        except Exception as e:
            self.logger.error(f"Error generating cURL command: {e}")
    
    def get_trade_requests(self) -> List[Dict[str, Any]]:
        """Get all detected trade requests.
        
        Returns:
            List of trade request data dictionaries
        """
        return self.trade_requests.copy()
    
    def get_all_requests(self) -> List[Dict[str, Any]]:
        """Get all intercepted requests.
        
        Returns:
            List of all request data dictionaries
        """
        return self.intercepted_requests.copy()
    
    def clear_requests(self) -> None:
        """Clear all stored requests."""
        self.intercepted_requests.clear()
        self.trade_requests.clear()
        self.logger.info("Cleared all stored requests")
    
    async def wait_for_trade_request(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Wait for a trade request to be detected.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Trade request data if detected, None if timeout
        """
        self.logger.info(f"Waiting for trade request (timeout: {timeout}s)...")
        
        start_time = time.time()
        initial_count = len(self.trade_requests)
        
        while time.time() - start_time < timeout:
            if len(self.trade_requests) > initial_count:
                latest_request = self.trade_requests[-1]
                self.logger.info("Trade request detected!")
                return latest_request
            
            await asyncio.sleep(0.5)
        
        self.logger.warning("Timeout waiting for trade request")
        return None
    
    def export_requests_to_file(self, filename: str = None) -> str:
        """Export all requests to a JSON file.
        
        Args:
            filename: Optional filename
            
        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = int(time.time())
            filename = f"intercepted_requests_{timestamp}.json"
        
        try:
            export_data = {
                'timestamp': time.time(),
                'total_requests': len(self.intercepted_requests),
                'trade_requests': len(self.trade_requests),
                'requests': self.intercepted_requests
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Requests exported to: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting requests: {e}")
            return ""

async def setup_request_interception(page: Page, logger: Optional[logging.Logger] = None) -> RequestInterceptor:
    """Convenience function to set up request interception.
    
    Args:
        page: Playwright page instance
        logger: Optional logger instance
        
    Returns:
        Configured RequestInterceptor instance
    """
    interceptor = RequestInterceptor(page, logger)
    await interceptor.start_interception()
    return interceptor

if __name__ == "__main__":
    # Test the request interceptor module
    print("Request interceptor module loaded successfully!")
    print("To test request interception, run the main tradebot_sentinel.py script.")