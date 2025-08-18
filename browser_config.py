#!/usr/bin/env python3
"""
Browser Configuration Module for TradeBot Sentinel
Optimized for headless cloud deployment with robust Chrome/Chromium setup
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserConfigError(Exception):
    """Custom exception for browser configuration errors"""
    pass

class CloudBrowserConfig:
    """
    Advanced browser configuration for cloud deployment
    Handles Chrome/Chromium setup with cloud-optimized settings
    """
    
    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright: Optional[Playwright] = None
        
        # Cloud environment detection
        self.is_cloud = self._detect_cloud_environment()
        self.chrome_path = self._find_chrome_executable()
        
        logger.info(f"Browser config initialized - Cloud: {self.is_cloud}, Headless: {self.headless}")
    
    def _detect_cloud_environment(self) -> bool:
        """
        Detect if running in a cloud environment
        """
        cloud_indicators = [
            'AWS_EXECUTION_ENV',
            'GOOGLE_CLOUD_PROJECT', 
            'AZURE_CLIENT_ID',
            'KUBERNETES_SERVICE_HOST',
            'DOCKER_CONTAINER',
            'HEROKU_APP_NAME'
        ]
        
        # Check environment variables
        for indicator in cloud_indicators:
            if os.getenv(indicator):
                logger.info(f"Cloud environment detected: {indicator}")
                return True
        
        # Check for containerization
        if os.path.exists('/.dockerenv'):
            logger.info("Docker container detected")
            return True
            
        # Check for common cloud metadata endpoints
        try:
            import requests
            # AWS metadata
            try:
                response = requests.get('http://169.254.169.254/latest/meta-data/', timeout=1)
                if response.status_code == 200:
                    logger.info("AWS cloud environment detected")
                    return True
            except:
                pass
                
            # GCP metadata
            try:
                response = requests.get('http://metadata.google.internal/computeMetadata/v1/', 
                                      headers={'Metadata-Flavor': 'Google'}, timeout=1)
                if response.status_code == 200:
                    logger.info("GCP cloud environment detected")
                    return True
            except:
                pass
        except ImportError:
            pass
            
        return False
    
    def _find_chrome_executable(self) -> Optional[str]:
        """
        Find Chrome/Chromium executable path
        """
        # Environment variable override
        chrome_path = os.getenv('CHROME_EXECUTABLE_PATH')
        if chrome_path and os.path.exists(chrome_path):
            logger.info(f"Using Chrome from environment: {chrome_path}")
            return chrome_path
        
        # Common Chrome/Chromium paths
        possible_paths = [
            # Linux paths (cloud environments)
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/opt/google/chrome/chrome',
            '/snap/bin/chromium',
            
            # Windows paths
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            
            # macOS paths
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found Chrome executable: {path}")
                return path
        
        # Try to find via which/where command
        try:
            if sys.platform.startswith('win'):
                result = subprocess.run(['where', 'chrome'], capture_output=True, text=True)
            else:
                result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split('\n')[0]
                logger.info(f"Found Chrome via command: {path}")
                return path
        except Exception as e:
            logger.warning(f"Error finding Chrome via command: {e}")
        
        logger.warning("Chrome executable not found")
        return None
    
    def get_browser_args(self) -> List[str]:
        """
        Get optimized browser arguments for cloud deployment
        """
        base_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-back-forward-cache',
            '--disable-ipc-flooding-protection',
            '--no-first-run',
            '--no-default-browser-check',
            '--no-pings',
            '--password-store=basic',
            '--use-mock-keychain',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--mute-audio',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-sync'
        ]
        
        # Cloud-specific optimizations
        if self.is_cloud:
            cloud_args = [
                '--memory-pressure-off',
                '--max_old_space_size=4096',
                '--disable-background-networking',
                '--disable-client-side-phishing-detection',
                '--disable-component-update',
                '--disable-domain-reliability',
                '--disable-features=TranslateUI',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--metrics-recording-only',
                '--safebrowsing-disable-auto-update',
                '--enable-automation',
                '--disable-blink-features=AutomationControlled'
            ]
            base_args.extend(cloud_args)
        
        # Memory optimization for limited resources
        memory_args = [
            '--memory-pressure-off',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees'
        ]
        base_args.extend(memory_args)
        
        # Display configuration for headless
        if self.headless:
            display_args = [
                '--headless=new',
                '--hide-scrollbars',
                '--disable-logging',
                '--disable-gpu-logging',
                '--silent'
            ]
            base_args.extend(display_args)
        
        # Window size for consistent rendering
        base_args.extend([
            '--window-size=1920,1080',
            '--viewport-size=1920,1080'
        ])
        
        return base_args
    
    def get_context_options(self) -> Dict:
        """
        Get browser context options
        """
        options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation', 'notifications'],
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'ignore_https_errors': True,
            'java_script_enabled': True,
            'bypass_csp': True
        }
        
        # Cloud-specific context options
        if self.is_cloud:
            options.update({
                'offline': False,
                'device_scale_factor': 1,
                'is_mobile': False,
                'has_touch': False
            })
        
        return options
    
    async def launch_browser(self) -> Browser:
        """
        Launch browser with optimized settings
        """
        try:
            self.playwright = sync_playwright().start()
            
            launch_options = {
                'headless': self.headless,
                'args': self.get_browser_args(),
                'ignore_default_args': ['--enable-automation'],
                'slow_mo': 100 if self.debug else 0,
                'timeout': 60000,  # 60 seconds
                'handle_sigint': False,
                'handle_sigterm': False,
                'handle_sighup': False
            }
            
            # Use custom Chrome path if available
            if self.chrome_path:
                launch_options['executable_path'] = self.chrome_path
            
            # Launch browser
            logger.info("Launching browser with optimized settings...")
            self.browser = self.playwright.chromium.launch(**launch_options)
            
            # Create context with optimized settings
            context_options = self.get_context_options()
            self.context = self.browser.new_context(**context_options)
            
            # Add stealth configurations
            await self._add_stealth_configurations()
            
            logger.info("Browser launched successfully")
            return self.browser
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            await self.cleanup()
            raise BrowserConfigError(f"Browser launch failed: {e}")
    
    async def _add_stealth_configurations(self):
        """
        Add stealth configurations to avoid detection
        """
        if not self.context:
            return
            
        # Override navigator properties
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        window.chrome = {
            runtime: {},
        };
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' }),
            }),
        });
        """
        
        self.context.add_init_script(stealth_script)
        logger.info("Stealth configurations added")
    
    def create_page(self) -> Page:
        """
        Create a new page with optimized settings
        """
        if not self.context:
            raise BrowserConfigError("Browser context not available")
        
        page = self.context.new_page()
        
        # Set timeouts
        page.set_default_timeout(30000)  # 30 seconds
        page.set_default_navigation_timeout(60000)  # 60 seconds
        
        # Block unnecessary resources for performance
        page.route('**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2}', lambda route: route.abort())
        page.route('**/analytics.js', lambda route: route.abort())
        page.route('**/gtag.js', lambda route: route.abort())
        page.route('**/facebook.net/**', lambda route: route.abort())
        page.route('**/google-analytics.com/**', lambda route: route.abort())
        
        logger.info("New page created with optimizations")
        return page
    
    async def cleanup(self):
        """
        Clean up browser resources
        """
        try:
            if self.context:
                await self.context.close()
                self.context = None
                logger.info("Browser context closed")
            
            if self.browser:
                await self.browser.close()
                self.browser = None
                logger.info("Browser closed")
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                logger.info("Playwright stopped")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def health_check(self) -> Dict[str, Union[bool, str]]:
        """
        Perform browser health check
        """
        health = {
            'chrome_available': bool(self.chrome_path),
            'chrome_path': self.chrome_path or 'Not found',
            'cloud_environment': self.is_cloud,
            'headless_mode': self.headless,
            'browser_active': bool(self.browser and not self.browser.is_closed()),
            'context_active': bool(self.context and not self.context.closed)
        }
        
        # Test Chrome executable
        if self.chrome_path:
            try:
                result = subprocess.run([self.chrome_path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                health['chrome_version'] = result.stdout.strip() if result.returncode == 0 else 'Unknown'
                health['chrome_executable'] = result.returncode == 0
            except Exception as e:
                health['chrome_executable'] = False
                health['chrome_error'] = str(e)
        
        return health

# Convenience functions
def create_cloud_browser(headless: bool = True, debug: bool = False) -> CloudBrowserConfig:
    """
    Create a cloud-optimized browser configuration
    """
    return CloudBrowserConfig(headless=headless, debug=debug)

def install_browser_dependencies():
    """
    Install browser dependencies for cloud deployment
    """
    logger.info("Installing browser dependencies...")
    
    try:
        # Install Playwright browsers
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        subprocess.run([sys.executable, '-m', 'playwright', 'install-deps', 'chromium'], check=True)
        logger.info("Playwright dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Playwright dependencies: {e}")
        raise BrowserConfigError(f"Dependency installation failed: {e}")

if __name__ == '__main__':
    # Test browser configuration
    import asyncio
    
    async def test_browser():
        config = create_cloud_browser(headless=True, debug=True)
        
        # Health check
        health = config.health_check()
        print("Browser Health Check:")
        for key, value in health.items():
            print(f"  {key}: {value}")
        
        try:
            # Launch browser
            browser = await config.launch_browser()
            page = config.create_page()
            
            # Test navigation
            await page.goto('https://httpbin.org/user-agent')
            content = await page.content()
            print(f"\nTest page loaded: {len(content)} characters")
            
            # Take screenshot
            await page.screenshot(path='browser_test.png')
            print("Screenshot saved: browser_test.png")
            
        except Exception as e:
            print(f"Browser test failed: {e}")
        finally:
            await config.cleanup()
    
    # Run test
    asyncio.run(test_browser())