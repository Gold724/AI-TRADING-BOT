#!/usr/bin/env python3
"""
Advanced Anti-Detection System for TradeBot Sentinel
Comprehensive bot detection evasion and stealth measures
"""

import asyncio
import json
import logging
import random
import time
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import base64
import string
from urllib.parse import urlparse
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('anti_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DetectionRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class StealthMode(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    PARANOID = "paranoid"

@dataclass
class BrowserFingerprint:
    user_agent: str
    screen_resolution: Tuple[int, int]
    timezone: str
    language: str
    platform: str
    webgl_vendor: str
    webgl_renderer: str
    canvas_fingerprint: str
    audio_fingerprint: str
    fonts: List[str]
    plugins: List[str]

@dataclass
class DetectionMetrics:
    timestamp: str
    risk_level: DetectionRisk
    detection_score: float
    triggered_rules: List[str]
    mitigation_actions: List[str]
    success_rate: float
    metadata: Dict[str, Any]

class AdvancedAntiDetection:
    def __init__(self, stealth_mode: StealthMode = StealthMode.STANDARD):
        self.stealth_mode = stealth_mode
        self.current_fingerprint = None
        self.detection_history = []
        self.mitigation_strategies = {}
        self.behavioral_patterns = {}
        
        # Detection rules and thresholds
        self.detection_rules = {
            'request_frequency': {'threshold': 10, 'window': 60},  # requests per minute
            'identical_requests': {'threshold': 3, 'window': 300},  # identical requests in 5 min
            'user_agent_consistency': {'threshold': 0.8},
            'timing_patterns': {'variance_threshold': 0.1},
            'header_anomalies': {'max_score': 5},
            'behavioral_score': {'threshold': 0.7}
        }
        
        # User agent pools for rotation
        self.user_agent_pools = {
            'chrome': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ],
            'firefox': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
            ],
            'safari': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15'
            ]
        }
        
        # Screen resolutions for fingerprinting
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
            (1280, 720), (1600, 900), (2560, 1440), (3840, 2160)
        ]
        
        # Common fonts for fingerprinting
        self.common_fonts = [
            'Arial', 'Helvetica', 'Times New Roman', 'Courier New',
            'Verdana', 'Georgia', 'Palatino', 'Garamond',
            'Bookman', 'Comic Sans MS', 'Trebuchet MS', 'Arial Black'
        ]
        
        # Timezone options
        self.timezones = [
            'America/New_York', 'America/Los_Angeles', 'Europe/London',
            'Europe/Berlin', 'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney'
        ]
        
    async def initialize(self) -> None:
        """Initialize the anti-detection system"""
        try:
            await self.generate_initial_fingerprint()
            await self.setup_mitigation_strategies()
            logger.info(f"Advanced Anti-Detection initialized in {self.stealth_mode.value} mode")
        except Exception as e:
            logger.error(f"Failed to initialize anti-detection system: {e}")
            raise
    
    async def generate_initial_fingerprint(self) -> BrowserFingerprint:
        """Generate initial browser fingerprint"""
        try:
            # Select browser type based on stealth mode
            browser_weights = {
                StealthMode.MINIMAL: {'chrome': 0.7, 'firefox': 0.2, 'safari': 0.1},
                StealthMode.STANDARD: {'chrome': 0.6, 'firefox': 0.3, 'safari': 0.1},
                StealthMode.AGGRESSIVE: {'chrome': 0.5, 'firefox': 0.4, 'safari': 0.1},
                StealthMode.PARANOID: {'chrome': 0.4, 'firefox': 0.4, 'safari': 0.2}
            }
            
            weights = browser_weights[self.stealth_mode]
            browser_type = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
            
            fingerprint = BrowserFingerprint(
                user_agent=random.choice(self.user_agent_pools[browser_type]),
                screen_resolution=random.choice(self.screen_resolutions),
                timezone=random.choice(self.timezones),
                language=random.choice(['en-US', 'en-GB', 'en-CA', 'de-DE', 'fr-FR']),
                platform=self.extract_platform_from_ua(browser_type),
                webgl_vendor=await self.generate_webgl_vendor(),
                webgl_renderer=await self.generate_webgl_renderer(),
                canvas_fingerprint=await self.generate_canvas_fingerprint(),
                audio_fingerprint=await self.generate_audio_fingerprint(),
                fonts=random.sample(self.common_fonts, random.randint(8, 12)),
                plugins=await self.generate_plugin_list(browser_type)
            )
            
            self.current_fingerprint = fingerprint
            logger.info(f"Generated {browser_type} fingerprint")
            return fingerprint
            
        except Exception as e:
            logger.error(f"Error generating fingerprint: {e}")
            raise
    
    def extract_platform_from_ua(self, browser_type: str) -> str:
        """Extract platform from user agent"""
        if 'Windows' in self.current_fingerprint.user_agent if self.current_fingerprint else True:
            return 'Win32'
        elif 'Macintosh' in self.current_fingerprint.user_agent if self.current_fingerprint else False:
            return 'MacIntel'
        else:
            return 'Linux x86_64'
    
    async def generate_webgl_vendor(self) -> str:
        """Generate WebGL vendor string"""
        vendors = [
            'Google Inc. (NVIDIA)',
            'Google Inc. (Intel)',
            'Google Inc. (AMD)',
            'Mozilla (NVIDIA)',
            'Mozilla (Intel)',
            'WebKit (Apple)'
        ]
        return random.choice(vendors)
    
    async def generate_webgl_renderer(self) -> str:
        """Generate WebGL renderer string"""
        renderers = [
            'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'Apple GPU',
            'Intel Iris Pro OpenGL Engine',
            'NVIDIA GeForce GTX 1080 OpenGL Engine'
        ]
        return random.choice(renderers)
    
    async def generate_canvas_fingerprint(self) -> str:
        """Generate canvas fingerprint"""
        # Simulate canvas rendering variations
        base_string = "Canvas fingerprint test 123"
        variations = [
            base_string + str(random.randint(1000, 9999)),
            base_string + chr(random.randint(65, 90)),
            base_string + f"{random.random():.6f}"
        ]
        
        selected = random.choice(variations)
        return hashlib.md5(selected.encode()).hexdigest()[:16]
    
    async def generate_audio_fingerprint(self) -> str:
        """Generate audio context fingerprint"""
        # Simulate audio context variations
        audio_data = f"audio_{random.randint(100000, 999999)}_{time.time()}"
        return hashlib.sha256(audio_data.encode()).hexdigest()[:20]
    
    async def generate_plugin_list(self, browser_type: str) -> List[str]:
        """Generate realistic plugin list"""
        base_plugins = {
            'chrome': [
                'Chrome PDF Plugin',
                'Chrome PDF Viewer',
                'Native Client'
            ],
            'firefox': [
                'OpenH264 Video Codec',
                'Widevine Content Decryption Module'
            ],
            'safari': [
                'WebKit built-in PDF',
                'QuickTime Plugin'
            ]
        }
        
        common_plugins = [
            'Adobe Flash Player',
            'Java Deployment Toolkit',
            'Microsoft Silverlight',
            'VLC Web Plugin'
        ]
        
        plugins = base_plugins.get(browser_type, [])
        
        # Add some common plugins randomly
        num_additional = random.randint(0, 3)
        plugins.extend(random.sample(common_plugins, min(num_additional, len(common_plugins))))
        
        return plugins
    
    async def setup_mitigation_strategies(self) -> None:
        """Setup mitigation strategies for different detection scenarios"""
        self.mitigation_strategies = {
            'high_request_frequency': [
                self.implement_request_delays,
                self.rotate_fingerprint,
                self.add_random_delays
            ],
            'identical_requests': [
                self.add_request_variations,
                self.rotate_headers,
                self.change_request_order
            ],
            'user_agent_inconsistency': [
                self.fix_user_agent_consistency,
                self.regenerate_fingerprint
            ],
            'suspicious_timing': [
                self.randomize_timing_patterns,
                self.implement_human_delays
            ],
            'header_anomalies': [
                self.normalize_headers,
                self.add_realistic_headers
            ],
            'behavioral_anomalies': [
                self.simulate_human_behavior,
                self.add_mouse_movements,
                self.implement_scroll_patterns
            ]
        }
    
    async def analyze_detection_risk(self, request_data: Dict[str, Any]) -> DetectionMetrics:
        """Analyze detection risk for a request"""
        try:
            timestamp = datetime.now().isoformat()
            detection_score = 0.0
            triggered_rules = []
            
            # Check request frequency
            freq_score = await self.check_request_frequency(request_data)
            if freq_score > self.detection_rules['request_frequency']['threshold']:
                detection_score += 0.3
                triggered_rules.append('high_request_frequency')
            
            # Check for identical requests
            identical_score = await self.check_identical_requests(request_data)
            if identical_score > self.detection_rules['identical_requests']['threshold']:
                detection_score += 0.25
                triggered_rules.append('identical_requests')
            
            # Check user agent consistency
            ua_score = await self.check_user_agent_consistency(request_data)
            if ua_score < self.detection_rules['user_agent_consistency']['threshold']:
                detection_score += 0.2
                triggered_rules.append('user_agent_inconsistency')
            
            # Check timing patterns
            timing_score = await self.check_timing_patterns(request_data)
            if timing_score > self.detection_rules['timing_patterns']['variance_threshold']:
                detection_score += 0.15
                triggered_rules.append('suspicious_timing')
            
            # Check header anomalies
            header_score = await self.check_header_anomalies(request_data)
            if header_score > self.detection_rules['header_anomalies']['max_score']:
                detection_score += 0.1
                triggered_rules.append('header_anomalies')
            
            # Determine risk level
            if detection_score >= 0.8:
                risk_level = DetectionRisk.CRITICAL
            elif detection_score >= 0.6:
                risk_level = DetectionRisk.HIGH
            elif detection_score >= 0.4:
                risk_level = DetectionRisk.MEDIUM
            else:
                risk_level = DetectionRisk.LOW
            
            # Calculate success rate based on history
            success_rate = await self.calculate_success_rate()
            
            metrics = DetectionMetrics(
                timestamp=timestamp,
                risk_level=risk_level,
                detection_score=detection_score,
                triggered_rules=triggered_rules,
                mitigation_actions=[],
                success_rate=success_rate,
                metadata={
                    'stealth_mode': self.stealth_mode.value,
                    'fingerprint_age': self.get_fingerprint_age()
                }
            )
            
            # Store metrics
            self.detection_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing detection risk: {e}")
            return DetectionMetrics(
                timestamp=datetime.now().isoformat(),
                risk_level=DetectionRisk.HIGH,
                detection_score=1.0,
                triggered_rules=['analysis_error'],
                mitigation_actions=[],
                success_rate=0.0,
                metadata={'error': str(e)}
            )
    
    async def check_request_frequency(self, request_data: Dict[str, Any]) -> float:
        """Check request frequency for bot-like behavior"""
        try:
            # Get recent requests from history
            current_time = time.time()
            window = self.detection_rules['request_frequency']['window']
            
            recent_requests = [
                req for req in self.detection_history
                if current_time - time.mktime(time.strptime(req.timestamp[:19], '%Y-%m-%dT%H:%M:%S')) < window
            ]
            
            return len(recent_requests)
            
        except Exception as e:
            logger.error(f"Error checking request frequency: {e}")
            return 0.0
    
    async def check_identical_requests(self, request_data: Dict[str, Any]) -> float:
        """Check for identical requests that might indicate bot behavior"""
        try:
            # Create hash of current request
            request_hash = hashlib.md5(
                json.dumps(request_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Count identical requests in recent history
            current_time = time.time()
            window = self.detection_rules['identical_requests']['window']
            
            identical_count = 0
            for metrics in self.detection_history:
                if current_time - time.mktime(time.strptime(metrics.timestamp[:19], '%Y-%m-%dT%H:%M:%S')) < window:
                    if metrics.metadata.get('request_hash') == request_hash:
                        identical_count += 1
            
            return identical_count
            
        except Exception as e:
            logger.error(f"Error checking identical requests: {e}")
            return 0.0
    
    async def check_user_agent_consistency(self, request_data: Dict[str, Any]) -> float:
        """Check user agent consistency"""
        try:
            current_ua = request_data.get('headers', {}).get('user-agent', '')
            if not current_ua:
                return 0.0
            
            if not self.current_fingerprint:
                return 1.0
            
            # Check if current UA matches fingerprint
            if current_ua == self.current_fingerprint.user_agent:
                return 1.0
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error checking user agent consistency: {e}")
            return 0.5
    
    async def check_timing_patterns(self, request_data: Dict[str, Any]) -> float:
        """Check for suspicious timing patterns"""
        try:
            if len(self.detection_history) < 3:
                return 0.0
            
            # Get recent request timestamps
            recent_times = []
            for metrics in self.detection_history[-10:]:
                timestamp = datetime.fromisoformat(metrics.timestamp)
                recent_times.append(timestamp.timestamp())
            
            if len(recent_times) < 3:
                return 0.0
            
            # Calculate intervals between requests
            intervals = []
            for i in range(1, len(recent_times)):
                intervals.append(recent_times[i] - recent_times[i-1])
            
            # Calculate variance in intervals
            if len(intervals) < 2:
                return 0.0
            
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            
            # Normalize variance (low variance = suspicious)
            normalized_variance = variance / (mean_interval ** 2) if mean_interval > 0 else 1.0
            
            return 1.0 - min(1.0, normalized_variance * 10)  # Invert so low variance = high score
            
        except Exception as e:
            logger.error(f"Error checking timing patterns: {e}")
            return 0.0
    
    async def check_header_anomalies(self, request_data: Dict[str, Any]) -> float:
        """Check for header anomalies"""
        try:
            headers = request_data.get('headers', {})
            anomaly_score = 0.0
            
            # Check for missing common headers
            expected_headers = ['user-agent', 'accept', 'accept-language', 'accept-encoding']
            for header in expected_headers:
                if header not in [h.lower() for h in headers.keys()]:
                    anomaly_score += 1.0
            
            # Check for suspicious header values
            user_agent = headers.get('user-agent', '').lower()
            if 'bot' in user_agent or 'crawler' in user_agent or 'spider' in user_agent:
                anomaly_score += 2.0
            
            # Check for automation indicators
            automation_indicators = ['selenium', 'webdriver', 'phantomjs', 'headless']
            for indicator in automation_indicators:
                if any(indicator in str(value).lower() for value in headers.values()):
                    anomaly_score += 1.5
            
            return anomaly_score
            
        except Exception as e:
            logger.error(f"Error checking header anomalies: {e}")
            return 0.0
    
    async def calculate_success_rate(self) -> float:
        """Calculate success rate based on recent history"""
        try:
            if len(self.detection_history) < 5:
                return 1.0
            
            recent_metrics = self.detection_history[-20:]
            successful_requests = sum(
                1 for m in recent_metrics 
                if m.risk_level in [DetectionRisk.LOW, DetectionRisk.MEDIUM]
            )
            
            return successful_requests / len(recent_metrics)
            
        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return 0.5
    
    def get_fingerprint_age(self) -> float:
        """Get age of current fingerprint in hours"""
        if not self.current_fingerprint:
            return 0.0
        
        # Assuming fingerprint was created when system initialized
        # In a real implementation, you'd track creation time
        return 1.0  # Placeholder
    
    async def apply_mitigations(self, metrics: DetectionMetrics) -> List[str]:
        """Apply mitigation strategies based on detection metrics"""
        try:
            applied_mitigations = []
            
            for rule in metrics.triggered_rules:
                if rule in self.mitigation_strategies:
                    strategies = self.mitigation_strategies[rule]
                    
                    # Apply strategies based on stealth mode
                    num_strategies = {
                        StealthMode.MINIMAL: 1,
                        StealthMode.STANDARD: 2,
                        StealthMode.AGGRESSIVE: 3,
                        StealthMode.PARANOID: len(strategies)
                    }.get(self.stealth_mode, 2)
                    
                    selected_strategies = strategies[:num_strategies]
                    
                    for strategy in selected_strategies:
                        try:
                            await strategy()
                            applied_mitigations.append(strategy.__name__)
                        except Exception as e:
                            logger.error(f"Error applying mitigation {strategy.__name__}: {e}")
            
            # Update metrics with applied mitigations
            metrics.mitigation_actions = applied_mitigations
            
            return applied_mitigations
            
        except Exception as e:
            logger.error(f"Error applying mitigations: {e}")
            return []
    
    # Mitigation strategy implementations
    async def implement_request_delays(self) -> None:
        """Implement delays between requests"""
        delay = random.uniform(1.0, 5.0)
        await asyncio.sleep(delay)
        logger.debug(f"Applied request delay: {delay:.2f}s")
    
    async def rotate_fingerprint(self) -> None:
        """Rotate browser fingerprint"""
        await self.generate_initial_fingerprint()
        logger.debug("Rotated browser fingerprint")
    
    async def add_random_delays(self) -> None:
        """Add random delays to simulate human behavior"""
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)
        logger.debug(f"Added random delay: {delay:.2f}s")
    
    async def add_request_variations(self) -> None:
        """Add variations to requests"""
        # This would modify request parameters slightly
        logger.debug("Added request variations")
    
    async def rotate_headers(self) -> None:
        """Rotate request headers"""
        # This would change non-essential headers
        logger.debug("Rotated headers")
    
    async def change_request_order(self) -> None:
        """Change order of request parameters"""
        # This would reorder JSON keys or form parameters
        logger.debug("Changed request order")
    
    async def fix_user_agent_consistency(self) -> None:
        """Fix user agent consistency issues"""
        if self.current_fingerprint:
            # Ensure all requests use the same user agent
            logger.debug("Fixed user agent consistency")
    
    async def regenerate_fingerprint(self) -> None:
        """Regenerate browser fingerprint"""
        await self.generate_initial_fingerprint()
        logger.debug("Regenerated fingerprint")
    
    async def randomize_timing_patterns(self) -> None:
        """Randomize timing patterns"""
        # Add variable delays to break timing patterns
        delay = random.uniform(0.1, 3.0)
        await asyncio.sleep(delay)
        logger.debug(f"Randomized timing: {delay:.2f}s")
    
    async def implement_human_delays(self) -> None:
        """Implement human-like delays"""
        # Simulate human reading/thinking time
        delay = random.uniform(2.0, 8.0)
        await asyncio.sleep(delay)
        logger.debug(f"Applied human delay: {delay:.2f}s")
    
    async def normalize_headers(self) -> None:
        """Normalize request headers"""
        # This would ensure headers look normal
        logger.debug("Normalized headers")
    
    async def add_realistic_headers(self) -> None:
        """Add realistic headers"""
        # This would add missing common headers
        logger.debug("Added realistic headers")
    
    async def simulate_human_behavior(self) -> None:
        """Simulate human behavior patterns"""
        # This would add mouse movements, scrolling, etc.
        logger.debug("Simulated human behavior")
    
    async def add_mouse_movements(self) -> None:
        """Add mouse movement simulation"""
        # This would simulate mouse movements
        logger.debug("Added mouse movements")
    
    async def implement_scroll_patterns(self) -> None:
        """Implement scroll patterns"""
        # This would simulate scrolling behavior
        logger.debug("Implemented scroll patterns")
    
    async def get_stealth_headers(self) -> Dict[str, str]:
        """Get stealth headers for requests"""
        try:
            if not self.current_fingerprint:
                await self.generate_initial_fingerprint()
            
            headers = {
                'User-Agent': self.current_fingerprint.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': f"{self.current_fingerprint.language},en;q=0.5",
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            # Add random headers based on stealth mode
            if self.stealth_mode in [StealthMode.AGGRESSIVE, StealthMode.PARANOID]:
                additional_headers = {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': 'https://example.com',
                    'Referer': 'https://example.com/'
                }
                headers.update(additional_headers)
            
            return headers
            
        except Exception as e:
            logger.error(f"Error getting stealth headers: {e}")
            return {}
    
    async def get_browser_scripts(self) -> List[str]:
        """Get JavaScript scripts for browser stealth"""
        try:
            scripts = []
            
            # Basic stealth script
            basic_stealth = """
            // Override webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [{}],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            """
            scripts.append(basic_stealth)
            
            if self.stealth_mode in [StealthMode.AGGRESSIVE, StealthMode.PARANOID]:
                # Advanced stealth script
                advanced_stealth = f"""
                // Override screen properties
                Object.defineProperty(screen, 'width', {{
                    get: () => {self.current_fingerprint.screen_resolution[0] if self.current_fingerprint else 1920},
                }});
                Object.defineProperty(screen, 'height', {{
                    get: () => {self.current_fingerprint.screen_resolution[1] if self.current_fingerprint else 1080},
                }});
                
                // Override timezone
                Date.prototype.getTimezoneOffset = function() {{
                    return -300; // EST timezone offset
                }};
                
                // Override canvas fingerprinting
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {{
                    const context = this.getContext('2d');
                    if (context) {{
                        context.fillStyle = 'rgba(255, 255, 255, 0.01)';
                        context.fillRect(0, 0, 1, 1);
                    }}
                    return originalToDataURL.apply(this, arguments);
                }};
                """
                scripts.append(advanced_stealth)
            
            return scripts
            
        except Exception as e:
            logger.error(f"Error getting browser scripts: {e}")
            return []
    
    async def get_detection_report(self) -> Dict[str, Any]:
        """Get comprehensive detection report"""
        try:
            if not self.detection_history:
                return {'no_data': True}
            
            recent_metrics = self.detection_history[-20:]
            
            # Calculate statistics
            avg_detection_score = sum(m.detection_score for m in recent_metrics) / len(recent_metrics)
            risk_distribution = {}
            for risk in DetectionRisk:
                risk_distribution[risk.value] = sum(1 for m in recent_metrics if m.risk_level == risk)
            
            most_common_rules = {}
            for metrics in recent_metrics:
                for rule in metrics.triggered_rules:
                    most_common_rules[rule] = most_common_rules.get(rule, 0) + 1
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'stealth_mode': self.stealth_mode.value,
                'current_fingerprint': asdict(self.current_fingerprint) if self.current_fingerprint else None,
                'statistics': {
                    'total_requests': len(self.detection_history),
                    'recent_requests': len(recent_metrics),
                    'avg_detection_score': avg_detection_score,
                    'success_rate': await self.calculate_success_rate(),
                    'risk_distribution': risk_distribution
                },
                'most_triggered_rules': sorted(
                    most_common_rules.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                'recommendations': await self.generate_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating detection report: {e}")
            return {'error': str(e)}
    
    async def generate_recommendations(self) -> List[str]:
        """Generate recommendations for improving stealth"""
        try:
            recommendations = []
            
            if not self.detection_history:
                return ['No detection history available']
            
            recent_metrics = self.detection_history[-10:]
            
            # Check success rate
            success_rate = await self.calculate_success_rate()
            if success_rate < 0.7:
                recommendations.append('Consider upgrading to more aggressive stealth mode')
            
            # Check most common triggered rules
            rule_counts = {}
            for metrics in recent_metrics:
                for rule in metrics.triggered_rules:
                    rule_counts[rule] = rule_counts.get(rule, 0) + 1
            
            if 'high_request_frequency' in rule_counts and rule_counts['high_request_frequency'] > 3:
                recommendations.append('Implement longer delays between requests')
            
            if 'identical_requests' in rule_counts and rule_counts['identical_requests'] > 2:
                recommendations.append('Add more variation to request parameters')
            
            if 'suspicious_timing' in rule_counts:
                recommendations.append('Randomize timing patterns more effectively')
            
            # Check fingerprint age
            fingerprint_age = self.get_fingerprint_age()
            if fingerprint_age > 24:  # hours
                recommendations.append('Consider rotating browser fingerprint')
            
            if not recommendations:
                recommendations.append('Current stealth configuration appears effective')
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ['Error generating recommendations']
    
    async def cleanup_history(self) -> None:
        """Clean up old detection history"""
        try:
            # Keep only last 100 entries
            if len(self.detection_history) > 100:
                self.detection_history = self.detection_history[-100:]
            
            logger.debug("Cleaned up detection history")
            
        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")

async def main():
    """Main function for standalone testing"""
    anti_detection = AdvancedAntiDetection(StealthMode.STANDARD)
    
    try:
        await anti_detection.initialize()
        
        # Test detection analysis
        test_request = {
            'url': 'https://api.trading.com/orders',
            'method': 'POST',
            'headers': {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'content-type': 'application/json'
            },
            'payload': '{"symbol": "BTCUSD", "side": "buy"}'
        }
        
        metrics = await anti_detection.analyze_detection_risk(test_request)
        print(f"Detection risk: {metrics.risk_level.value} (score: {metrics.detection_score:.2f})")
        
        # Apply mitigations if needed
        if metrics.risk_level in [DetectionRisk.HIGH, DetectionRisk.CRITICAL]:
            mitigations = await anti_detection.apply_mitigations(metrics)
            print(f"Applied mitigations: {mitigations}")
        
        # Get detection report
        report = await anti_detection.get_detection_report()
        print(json.dumps(report, indent=2))
        
    except KeyboardInterrupt:
        logger.info("Anti-detection testing interrupted by user")
    except Exception as e:
        logger.error(f"Error in anti-detection testing: {e}")

if __name__ == "__main__":
    asyncio.run(main())