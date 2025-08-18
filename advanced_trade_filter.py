#!/usr/bin/env python3
"""
TradeBot Sentinel - Advanced Trade Request Filter
Intelligent filtering and parsing for trade execution detection

Features:
- Enhanced trade request validation
- False positive reduction
- Multi-format payload parsing
- Request classification
- Performance optimization
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import hashlib

class AdvancedTradeFilter:
    """Advanced filtering system for trade request detection"""
    
    def __init__(self):
        self.setup_logging()
        
        # Trade execution endpoints
        self.trade_endpoints = {
            'execution': [
                '/api/trade', '/trade/execute', '/orders/create',
                '/api/orders', '/trading/order', '/execute',
                '/api/positions/open', '/api/positions/close',
                '/order/submit', '/trade/place', '/api/trading/execute'
            ],
            'modification': [
                '/orders/modify', '/orders/cancel', '/orders/update',
                '/api/orders/cancel', '/trade/modify', '/positions/modify'
            ],
            'position': [
                '/positions/open', '/positions/close', '/positions/update',
                '/api/positions', '/trading/positions'
            ]
        }
        
        # Exclude these endpoints (UI/data requests)
        self.excluded_endpoints = [
            '/api/chart', '/api/quotes', '/api/market-data',
            '/api/news', '/api/notifications', '/api/user/settings',
            '/api/layout', '/api/workspace', '/api/ui',
            '/websocket', '/ws/', '/socket.io',
            '/api/heartbeat', '/api/ping', '/api/status',
            '/api/analytics', '/api/tracking', '/api/logs'
        ]
        
        # Required fields for trade validation
        self.trade_field_patterns = {
            'symbol': [r'symbol', r'instrument', r'asset', r'ticker'],
            'quantity': [r'quantity', r'amount', r'size', r'volume', r'qty'],
            'side': [r'side', r'direction', r'action', r'type'],
            'price': [r'price', r'limit', r'stop', r'level'],
            'order_type': [r'orderType', r'order_type', r'type', r'kind']
        }
        
        # Trade action keywords
        self.trade_actions = {
            'buy': ['buy', 'long', 'bid', 'purchase'],
            'sell': ['sell', 'short', 'ask', 'dispose'],
            'close': ['close', 'exit', 'liquidate'],
            'modify': ['modify', 'update', 'change', 'amend']
        }
        
        # Size thresholds
        self.max_ui_request_size = 50000  # 50KB
        self.min_trade_request_size = 50   # 50 bytes
        
        # Cache for performance
        self.request_cache = {}
        self.cache_max_size = 1000
    
    def setup_logging(self):
        """Setup logging for trade filter"""
        self.logger = logging.getLogger('TradeFilter')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def is_trade_request(self, url: str, method: str, data: Any, headers: Dict[str, str]) -> Tuple[bool, str, Dict[str, Any]]:
        """Main trade request detection logic"""
        try:
            # Quick cache check
            cache_key = self._generate_cache_key(url, method, data)
            if cache_key in self.request_cache:
                return self.request_cache[cache_key]
            
            # Step 1: Method validation
            if method.upper() not in ['POST', 'PUT', 'PATCH']:
                result = (False, 'Invalid HTTP method', {})
                self._cache_result(cache_key, result)
                return result
            
            # Step 2: URL analysis
            url_score, url_reason = self._analyze_url(url)
            if url_score < 0:
                result = (False, f'URL excluded: {url_reason}', {})
                self._cache_result(cache_key, result)
                return result
            
            # Step 3: Data size validation
            data_size = self._get_data_size(data)
            if not self._is_valid_size(data_size):
                result = (False, f'Invalid size: {data_size} bytes', {})
                self._cache_result(cache_key, result)
                return result
            
            # Step 4: Payload analysis
            payload_score, trade_data = self._analyze_payload(data)
            if payload_score < 0.5:  # Threshold for trade detection
                result = (False, f'Low payload score: {payload_score}', trade_data)
                self._cache_result(cache_key, result)
                return result
            
            # Step 5: Header analysis
            header_score = self._analyze_headers(headers)
            
            # Step 6: Final scoring
            final_score = (url_score * 0.4) + (payload_score * 0.5) + (header_score * 0.1)
            
            if final_score >= 0.7:  # High confidence threshold
                confidence = 'HIGH'
            elif final_score >= 0.5:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'
                result = (False, f'Low confidence: {final_score:.2f}', trade_data)
                self._cache_result(cache_key, result)
                return result
            
            # Success - this is likely a trade request
            result = (True, f'Trade detected (confidence: {confidence}, score: {final_score:.2f})', trade_data)
            self._cache_result(cache_key, result)
            
            self.logger.info(f"✅ Trade request detected: {url} (score: {final_score:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Trade detection error: {e}")
            return (False, f'Analysis error: {str(e)}', {})
    
    def _analyze_url(self, url: str) -> Tuple[float, str]:
        """Analyze URL for trade-related patterns"""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Check exclusions first
        for excluded in self.excluded_endpoints:
            if excluded in path:
                return (-1.0, f'Excluded endpoint: {excluded}')
        
        # Check for trade endpoints
        score = 0.0
        matched_category = None
        
        for category, endpoints in self.trade_endpoints.items():
            for endpoint in endpoints:
                if endpoint in path:
                    if category == 'execution':
                        score = 1.0
                    elif category == 'modification':
                        score = 0.8
                    elif category == 'position':
                        score = 0.9
                    matched_category = category
                    break
            if matched_category:
                break
        
        # Generic trade keywords
        if score == 0.0:
            trade_keywords = ['trade', 'order', 'position', 'execute', 'buy', 'sell']
            for keyword in trade_keywords:
                if keyword in path:
                    score = 0.6
                    matched_category = 'generic'
                    break
        
        reason = f'Matched {matched_category}' if matched_category else 'No trade patterns'
        return (score, reason)
    
    def _analyze_payload(self, data: Any) -> Tuple[float, Dict[str, Any]]:
        """Analyze request payload for trade data"""
        if not data:
            return (0.0, {})
        
        try:
            # Parse different data formats
            parsed_data = self._parse_data(data)
            if not parsed_data:
                return (0.0, {})
            
            # Extract trade-related fields
            trade_data = self._extract_trade_fields(parsed_data)
            
            # Calculate score based on found fields
            score = self._calculate_payload_score(trade_data)
            
            return (score, trade_data)
            
        except Exception as e:
            self.logger.debug(f"Payload analysis error: {e}")
            return (0.0, {})
    
    def _parse_data(self, data: Any) -> Optional[Dict[str, Any]]:
        """Parse data from various formats"""
        if isinstance(data, dict):
            return data
        
        if isinstance(data, str):
            # Try JSON parsing
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                # Try URL-encoded parsing
                try:
                    parsed = parse_qs(data)
                    return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
                except:
                    return None
        
        if isinstance(data, bytes):
            try:
                return json.loads(data.decode('utf-8'))
            except:
                return None
        
        return None
    
    def _extract_trade_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trade-related fields from parsed data"""
        trade_data = {}
        
        def search_nested(obj, path=""):
            """Recursively search nested objects"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if this key matches any trade field pattern
                    for field_type, patterns in self.trade_field_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, key, re.IGNORECASE):
                                trade_data[field_type] = {
                                    'value': value,
                                    'path': current_path,
                                    'key': key
                                }
                    
                    # Check for trade actions
                    if isinstance(value, str):
                        for action_type, actions in self.trade_actions.items():
                            if value.lower() in actions:
                                trade_data['action'] = {
                                    'value': value,
                                    'type': action_type,
                                    'path': current_path
                                }
                    
                    # Recurse into nested objects
                    if isinstance(value, (dict, list)):
                        search_nested(value, current_path)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_nested(item, f"{path}[{i}]")
        
        search_nested(data)
        return trade_data
    
    def _calculate_payload_score(self, trade_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted trade data"""
        if not trade_data:
            return 0.0
        
        # Weight different field types
        field_weights = {
            'symbol': 0.3,
            'quantity': 0.25,
            'side': 0.2,
            'action': 0.2,
            'price': 0.15,
            'order_type': 0.1
        }
        
        score = 0.0
        for field, weight in field_weights.items():
            if field in trade_data:
                score += weight
        
        # Bonus for having core trade fields
        core_fields = ['symbol', 'quantity', 'side']
        if all(field in trade_data for field in core_fields):
            score += 0.2  # Bonus for complete trade data
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _analyze_headers(self, headers: Dict[str, str]) -> float:
        """Analyze request headers for trade-related indicators"""
        score = 0.0
        
        # Check content type
        content_type = headers.get('content-type', '').lower()
        if 'application/json' in content_type:
            score += 0.3
        elif 'application/x-www-form-urlencoded' in content_type:
            score += 0.2
        
        # Check for trading-specific headers
        trading_headers = [
            'x-trading-session', 'x-order-id', 'x-trade-id',
            'x-api-key', 'authorization', 'x-csrf-token'
        ]
        
        for header in trading_headers:
            if header in [h.lower() for h in headers.keys()]:
                score += 0.1
        
        return min(score, 1.0)
    
    def _is_valid_size(self, size: int) -> bool:
        """Check if request size is within valid range for trade requests"""
        return self.min_trade_request_size <= size <= self.max_ui_request_size
    
    def _get_data_size(self, data: Any) -> int:
        """Get size of request data"""
        if data is None:
            return 0
        
        if isinstance(data, str):
            return len(data.encode('utf-8'))
        elif isinstance(data, bytes):
            return len(data)
        elif isinstance(data, dict):
            return len(json.dumps(data).encode('utf-8'))
        else:
            return len(str(data).encode('utf-8'))
    
    def _generate_cache_key(self, url: str, method: str, data: Any) -> str:
        """Generate cache key for request"""
        data_hash = hashlib.md5(str(data).encode('utf-8')).hexdigest()[:8]
        return f"{method}:{urlparse(url).path}:{data_hash}"
    
    def _cache_result(self, key: str, result: Tuple[bool, str, Dict[str, Any]]):
        """Cache analysis result"""
        if len(self.request_cache) >= self.cache_max_size:
            # Remove oldest entries
            oldest_keys = list(self.request_cache.keys())[:100]
            for old_key in oldest_keys:
                del self.request_cache[old_key]
        
        self.request_cache[key] = result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get filter statistics"""
        total_requests = len(self.request_cache)
        trade_requests = sum(1 for result in self.request_cache.values() if result[0])
        
        return {
            'total_analyzed': total_requests,
            'trade_detected': trade_requests,
            'detection_rate': (trade_requests / total_requests * 100) if total_requests > 0 else 0,
            'cache_size': len(self.request_cache)
        }
    
    def clear_cache(self):
        """Clear analysis cache"""
        self.request_cache.clear()
        self.logger.info("Analysis cache cleared")

# Example usage and testing
def test_trade_filter():
    """Test the advanced trade filter"""
    filter_system = AdvancedTradeFilter()
    
    # Test cases
    test_cases = [
        {
            'url': 'https://bulenox.projectx.com/api/trade/execute',
            'method': 'POST',
            'data': {'symbol': 'GOLD', 'quantity': 100, 'side': 'buy', 'price': 1850},
            'headers': {'content-type': 'application/json'}
        },
        {
            'url': 'https://bulenox.projectx.com/api/chart/data',
            'method': 'GET',
            'data': None,
            'headers': {}
        },
        {
            'url': 'https://bulenox.projectx.com/api/orders/create',
            'method': 'POST',
            'data': '{"instrument": "EUR/USD", "amount": 10000, "action": "sell"}',
            'headers': {'content-type': 'application/json'}
        }
    ]
    
    print("🧪 Testing Advanced Trade Filter\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"URL: {test_case['url']}")
        print(f"Method: {test_case['method']}")
        
        is_trade, reason, trade_data = filter_system.is_trade_request(
            test_case['url'],
            test_case['method'],
            test_case['data'],
            test_case['headers']
        )
        
        print(f"Result: {'✅ TRADE' if is_trade else '❌ NOT TRADE'}")
        print(f"Reason: {reason}")
        if trade_data:
            print(f"Trade Data: {trade_data}")
        print("-" * 50)
    
    # Print statistics
    stats = filter_system.get_statistics()
    print(f"\n📊 Filter Statistics:")
    print(f"Total Analyzed: {stats['total_analyzed']}")
    print(f"Trade Detected: {stats['trade_detected']}")
    print(f"Detection Rate: {stats['detection_rate']:.1f}%")

if __name__ == "__main__":
    test_trade_filter()