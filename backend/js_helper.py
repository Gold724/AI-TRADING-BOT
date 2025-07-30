import os
import time
import json
import logging
from typing import Dict, List, Any, Optional, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    ElementNotInteractableException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
    JavascriptException
)

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "js_helper.log")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("JS_HELPER")

class JavaScriptHelper:
    """Helper class for JavaScript-enhanced Selenium operations."""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.stealth_enabled = False
        self.page_ready_script_injected = False
        self.state_monitor_script_injected = False
        
        # Initialize with stealth mode
        self.enable_stealth_mode()
    
    def enable_stealth_mode(self) -> bool:
        """Enable stealth mode to avoid bot detection."""
        try:
            # Patch navigator.webdriver flag
            stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Patch user agent if needed
            if (navigator.userAgent.includes('HeadlessChrome')) {
                Object.defineProperty(navigator, 'userAgent', {
                    get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                });
            }
            
            // Add missing properties that fingerprinting scripts often check
            if (!window.chrome) {
                window.chrome = {};
            }
            if (!window.chrome.runtime) {
                window.chrome.runtime = {};
            }
            
            // Add plugins array
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [{
                        0: {
                            type: 'application/pdf',
                            suffixes: 'pdf',
                            description: 'Portable Document Format',
                            enabledPlugin: true
                        },
                        name: 'PDF Viewer',
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 1
                    }];
                }
            });
            
            // Add languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Patch permissions API
            if (navigator.permissions) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = (parameters) => {
                    if (parameters.name === 'notifications') {
                        return Promise.resolve({ state: 'granted' });
                    }
                    return originalQuery(parameters);
                };
            }
            
            // Patch WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, [parameter]);
            };
            
            // Patch canvas fingerprinting
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (this.width === 0 && this.height === 0) {
                    return originalToDataURL.apply(this, [type]);
                }
                return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
            };
            
            console.log('Stealth mode enabled');
            window.__stealthModeEnabled = true;
            """
            
            self.driver.execute_script(stealth_script)
            self.stealth_enabled = True
            logger.info("Stealth mode enabled successfully")
            return True
        except Exception as e:
            logger.error(f"Error enabling stealth mode: {str(e)}")
            return False
    
    def inject_page_ready_detector(self) -> bool:
        """Inject script to detect when page is fully loaded."""
        try:
            ready_script = """
            window.__pageReady = false;
            window.__pageReadyState = 'loading';
            
            function checkPageReady() {
                // Check document readyState
                if (document.readyState === 'complete') {
                    // Check if there are any pending XHR requests
                    const pendingXHR = window.XMLHttpRequest && Array.from(performance.getEntriesByType('resource'))
                        .filter(r => r.initiatorType === 'xmlhttprequest' && !r.responseEnd);
                    
                    // Check if there are any pending fetch requests
                    const pendingFetch = window.fetch && window.__fetchRequests && window.__fetchRequests.size > 0;
                    
                    // Check if there are any pending animations or transitions
                    const pendingAnimations = document.getAnimations && document.getAnimations().some(a => a.playState === 'running');
                    
                    // Check for loading indicators
                    const loadingElements = document.querySelectorAll('.loading, .spinner, [data-loading="true"], [aria-busy="true"]');
                    
                    if (!pendingXHR && !pendingFetch && !pendingAnimations && loadingElements.length === 0) {
                        window.__pageReady = true;
                        window.__pageReadyState = 'complete';
                        return true;
                    } else {
                        window.__pageReadyState = 'interactive-loading';
                        return false;
                    }
                } else {
                    window.__pageReadyState = document.readyState;
                    return false;
                }
            }
            
            // Intercept fetch API
            if (window.fetch && !window.__fetchIntercepted) {
                window.__fetchRequests = new Set();
                const originalFetch = window.fetch;
                
                window.fetch = function() {
                    const fetchCall = {};
                    window.__fetchRequests.add(fetchCall);
                    
                    return originalFetch.apply(this, arguments)
                        .then(response => {
                            window.__fetchRequests.delete(fetchCall);
                            return response;
                        })
                        .catch(error => {
                            window.__fetchRequests.delete(fetchCall);
                            throw error;
                        });
                };
                
                window.__fetchIntercepted = true;
            }
            
            // Intercept XHR
            if (window.XMLHttpRequest && !window.__xhrIntercepted) {
                const originalOpen = XMLHttpRequest.prototype.open;
                const originalSend = XMLHttpRequest.prototype.send;
                
                XMLHttpRequest.prototype.open = function() {
                    this.__xhr_request_pending = true;
                    return originalOpen.apply(this, arguments);
                };
                
                XMLHttpRequest.prototype.send = function() {
                    this.addEventListener('loadend', function() {
                        this.__xhr_request_pending = false;
                    });
                    return originalSend.apply(this, arguments);
                };
                
                window.__xhrIntercepted = true;
            }
            
            // Check page ready state periodically
            setInterval(checkPageReady, 100);
            
            // Initial check
            checkPageReady();
            
            console.log('Page ready detector injected');
            return true;
            """
            
            self.driver.execute_script(ready_script)
            self.page_ready_script_injected = True
            logger.info("Page ready detector injected successfully")
            return True
        except Exception as e:
            logger.error(f"Error injecting page ready detector: {str(e)}")
            return False
    
    def inject_state_monitor(self) -> bool:
        """Inject script to monitor internal state of the application."""
        try:
            state_script = """
            window.__stateMonitor = {
                values: {},
                watchers: {},
                lastUpdated: {}
            };
            
            // Function to track a specific value
            window.__stateMonitor.track = function(key, selector, property) {
                try {
                    const element = document.querySelector(selector);
                    if (element) {
                        let value;
                        if (property === 'innerText') {
                            value = element.innerText;
                        } else if (property === 'innerHTML') {
                            value = element.innerHTML;
                        } else if (property === 'value') {
                            value = element.value;
                        } else if (property === 'checked') {
                            value = element.checked;
                        } else if (property === 'className') {
                            value = element.className;
                        } else if (property === 'style') {
                            value = element.style.cssText;
                        } else if (property === 'attributes') {
                            value = {};
                            for (let i = 0; i < element.attributes.length; i++) {
                                const attr = element.attributes[i];
                                value[attr.name] = attr.value;
                            }
                        } else {
                            value = element[property];
                        }
                        
                        if (this.values[key] !== value) {
                            this.values[key] = value;
                            this.lastUpdated[key] = new Date().getTime();
                            
                            // Notify watchers
                            if (this.watchers[key]) {
                                this.watchers[key].forEach(callback => {
                                    try {
                                        callback(value);
                                    } catch (e) {
                                        console.error('Error in watcher callback:', e);
                                    }
                                });
                            }
                        }
                        
                        return value;
                    }
                } catch (e) {
                    console.error('Error tracking state:', e);
                }
                return null;
            };
            
            // Function to watch for changes
            window.__stateMonitor.watch = function(key, callback) {
                if (!this.watchers[key]) {
                    this.watchers[key] = [];
                }
                this.watchers[key].push(callback);
            };
            
            // Function to get current value
            window.__stateMonitor.get = function(key) {
                return this.values[key];
            };
            
            // Function to set value manually
            window.__stateMonitor.set = function(key, value) {
                this.values[key] = value;
                this.lastUpdated[key] = new Date().getTime();
                
                // Notify watchers
                if (this.watchers[key]) {
                    this.watchers[key].forEach(callback => {
                        try {
                            callback(value);
                        } catch (e) {
                            console.error('Error in watcher callback:', e);
                        }
                    });
                }
            };
            
            // Function to get all tracked values
            window.__stateMonitor.getAll = function() {
                return this.values;
            };
            
            // Function to get last updated timestamps
            window.__stateMonitor.getLastUpdated = function() {
                return this.lastUpdated;
            };
            
            console.log('State monitor injected');
            return true;
            """
            
            self.driver.execute_script(state_script)
            self.state_monitor_script_injected = True
            logger.info("State monitor injected successfully")
            return True
        except Exception as e:
            logger.error(f"Error injecting state monitor: {str(e)}")
            return False
    
    def wait_for_page_ready(self, timeout: int = 30) -> bool:
        """Wait for page to be fully loaded and ready."""
        try:
            if not self.page_ready_script_injected:
                self.inject_page_ready_detector()
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                ready_state = self.driver.execute_script("return window.__pageReadyState || document.readyState;")
                is_ready = self.driver.execute_script("return window.__pageReady === true;")
                
                if is_ready:
                    logger.info(f"Page ready after {time.time() - start_time:.2f} seconds")
                    return True
                
                logger.debug(f"Waiting for page to be ready. Current state: {ready_state}")
                time.sleep(0.5)
            
            logger.warning(f"Timeout waiting for page to be ready after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"Error waiting for page ready: {str(e)}")
            return False
    
    def js_click(self, element_or_selector: Union[str, object]) -> bool:
        """Click an element using JavaScript."""
        try:
            if isinstance(element_or_selector, str):
                # It's a selector string
                script = f"""
                const element = document.querySelector('{element_or_selector}');
                if (element) {{
                    element.click();
                    return true;
                }}
                return false;
                """
                result = self.driver.execute_script(script)
            else:
                # It's a WebElement
                result = self.driver.execute_script("arguments[0].click();", element_or_selector)
            
            logger.info(f"JavaScript click successful on {element_or_selector}")
            return True if result is None else result
        except Exception as e:
            logger.error(f"Error performing JavaScript click: {str(e)}")
            return False
    
    def js_set_value(self, element_or_selector: Union[str, object], value: str) -> bool:
        """Set value of an input element using JavaScript."""
        try:
            if isinstance(element_or_selector, str):
                # It's a selector string
                script = f"""
                const element = document.querySelector('{element_or_selector}');
                if (element) {{
                    element.value = '{value}';
                    
                    // Trigger events
                    const inputEvent = new Event('input', {{ bubbles: true }});
                    element.dispatchEvent(inputEvent);
                    
                    const changeEvent = new Event('change', {{ bubbles: true }});
                    element.dispatchEvent(changeEvent);
                    
                    return true;
                }}
                return false;
                """
                result = self.driver.execute_script(script)
            else:
                # It's a WebElement
                result = self.driver.execute_script(
                    """arguments[0].value = arguments[1]; 
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    """, 
                    element_or_selector, value
                )
            
            logger.info(f"JavaScript set value successful on {element_or_selector}")
            return True if result is None else result
        except Exception as e:
            logger.error(f"Error performing JavaScript set value: {str(e)}")
            return False
    
    def js_get_text(self, element_or_selector: Union[str, object]) -> Optional[str]:
        """Get text content of an element using JavaScript."""
        try:
            if isinstance(element_or_selector, str):
                # It's a selector string
                script = f"""
                const element = document.querySelector('{element_or_selector}');
                if (element) {{
                    return element.textContent || element.innerText || element.value || '';
                }}
                return null;
                """
                result = self.driver.execute_script(script)
            else:
                # It's a WebElement
                result = self.driver.execute_script(
                    "return arguments[0].textContent || arguments[0].innerText || arguments[0].value || '';", 
                    element_or_selector
                )
            
            return result
        except Exception as e:
            logger.error(f"Error getting text with JavaScript: {str(e)}")
            return None
    
    def js_is_visible(self, element_or_selector: Union[str, object]) -> bool:
        """Check if an element is visible using JavaScript."""
        try:
            if isinstance(element_or_selector, str):
                # It's a selector string
                script = f"""
                const element = document.querySelector('{element_or_selector}');
                if (element) {{
                    const style = window.getComputedStyle(element);
                    return element.offsetWidth > 0 && 
                           element.offsetHeight > 0 && 
                           style.display !== 'none' && 
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0';
                }}
                return false;
                """
                result = self.driver.execute_script(script)
            else:
                # It's a WebElement
                result = self.driver.execute_script(
                    """const style = window.getComputedStyle(arguments[0]);
                    return arguments[0].offsetWidth > 0 && 
                           arguments[0].offsetHeight > 0 && 
                           style.display !== 'none' && 
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0';
                    """, 
                    element_or_selector
                )
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking visibility with JavaScript: {str(e)}")
            return False
    
    def js_wait_for_element(self, selector: str, timeout: int = 30, visible: bool = True) -> bool:
        """Wait for an element to be present and optionally visible using JavaScript."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if visible:
                    script = f"""
                    const element = document.querySelector('{selector}');
                    if (element) {{
                        const style = window.getComputedStyle(element);
                        return element.offsetWidth > 0 && 
                               element.offsetHeight > 0 && 
                               style.display !== 'none' && 
                               style.visibility !== 'hidden' &&
                               style.opacity !== '0';
                    }}
                    return false;
                    """
                else:
                    script = f"return document.querySelector('{selector}') !== null;"
                
                result = self.driver.execute_script(script)
                if result:
                    logger.info(f"Element {selector} found after {time.time() - start_time:.2f} seconds")
                    return True
                
                time.sleep(0.5)
            
            logger.warning(f"Timeout waiting for element {selector} after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"Error waiting for element with JavaScript: {str(e)}")
            return False
    
    def track_state_value(self, key: str, selector: str, property: str = 'innerText') -> Any:
        """Track a value in the state monitor."""
        try:
            if not self.state_monitor_script_injected:
                self.inject_state_monitor()
            
            script = f"return window.__stateMonitor.track('{key}', '{selector}', '{property}');"
            result = self.driver.execute_script(script)
            
            logger.info(f"Tracking state value {key} from {selector}.{property}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error tracking state value: {str(e)}")
            return None
    
    def get_state_value(self, key: str) -> Any:
        """Get a value from the state monitor."""
        try:
            if not self.state_monitor_script_injected:
                logger.warning("State monitor not injected, cannot get state value")
                return None
            
            script = f"return window.__stateMonitor.get('{key}');"
            result = self.driver.execute_script(script)
            
            return result
        except Exception as e:
            logger.error(f"Error getting state value: {str(e)}")
            return None
    
    def set_state_value(self, key: str, value: Any) -> bool:
        """Set a value in the state monitor."""
        try:
            if not self.state_monitor_script_injected:
                self.inject_state_monitor()
            
            # Convert value to JSON string for JavaScript
            if isinstance(value, (dict, list)):
                value_json = json.dumps(value)
                script = f"return window.__stateMonitor.set('{key}', JSON.parse('{value_json}'));"
            elif isinstance(value, bool):
                script = f"return window.__stateMonitor.set('{key}', {str(value).lower()});"
            elif isinstance(value, (int, float)):
                script = f"return window.__stateMonitor.set('{key}', {value});"
            elif value is None:
                script = f"return window.__stateMonitor.set('{key}', null);"
            else:
                # String value
                script = f"return window.__stateMonitor.set('{key}', '{value}');"
            
            self.driver.execute_script(script)
            logger.info(f"Set state value {key} to {value}")
            return True
        except Exception as e:
            logger.error(f"Error setting state value: {str(e)}")
            return False
    
    def get_all_state_values(self) -> Dict[str, Any]:
        """Get all values from the state monitor."""
        try:
            if not self.state_monitor_script_injected:
                logger.warning("State monitor not injected, cannot get state values")
                return {}
            
            script = "return window.__stateMonitor.getAll();"
            result = self.driver.execute_script(script)
            
            return result if result else {}
        except Exception as e:
            logger.error(f"Error getting all state values: {str(e)}")
            return {}
    
    def js_scroll_to_element(self, element_or_selector: Union[str, object]) -> bool:
        """Scroll to an element using JavaScript."""
        try:
            if isinstance(element_or_selector, str):
                # It's a selector string
                script = f"""
                const element = document.querySelector('{element_or_selector}');
                if (element) {{
                    element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    return true;
                }}
                return false;
                """
                result = self.driver.execute_script(script)
            else:
                # It's a WebElement
                result = self.driver.execute_script(
                    "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", 
                    element_or_selector
                )
            
            # Give time for smooth scrolling
            time.sleep(0.5)
            
            logger.info(f"Scrolled to element {element_or_selector}")
            return True if result is None else result
        except Exception as e:
            logger.error(f"Error scrolling to element: {str(e)}")
            return False
    
    def js_highlight_element(self, element_or_selector: Union[str, object], duration: int = 2) -> bool:
        """Highlight an element for debugging purposes."""
        try:
            if isinstance(element_or_selector, str):
                # It's a selector string
                script = f"""
                const element = document.querySelector('{element_or_selector}');
                if (element) {{
                    const originalStyle = element.getAttribute('style') || '';
                    element.setAttribute('style', originalStyle + '; border: 2px solid red; background-color: yellow; color: black;');
                    setTimeout(() => {{
                        element.setAttribute('style', originalStyle);
                    }}, {duration * 1000});
                    return true;
                }}
                return false;
                """
                result = self.driver.execute_script(script)
            else:
                # It's a WebElement
                result = self.driver.execute_script(
                    f"""const originalStyle = arguments[0].getAttribute('style') || '';
                    arguments[0].setAttribute('style', originalStyle + '; border: 2px solid red; background-color: yellow; color: black;');
                    setTimeout(() => {{
                        arguments[0].setAttribute('style', originalStyle);
                    }}, {duration * 1000});
                    """, 
                    element_or_selector
                )
            
            logger.info(f"Highlighted element {element_or_selector} for {duration} seconds")
            return True if result is None else result
        except Exception as e:
            logger.error(f"Error highlighting element: {str(e)}")
            return False
    
    def js_get_element_attributes(self, element_or_selector: Union[str, object]) -> Dict[str, str]:
        """Get all attributes of an element using JavaScript."""
        try:
            if isinstance(element_or_selector, str):
                # It's a selector string
                script = f"""
                const element = document.querySelector('{element_or_selector}');
                if (element) {{
                    const attributes = {{}};  
                    for (let i = 0; i < element.attributes.length; i++) {{
                        const attr = element.attributes[i];
                        attributes[attr.name] = attr.value;
                    }}
                    return attributes;
                }}
                return null;
                """
                result = self.driver.execute_script(script)
            else:
                # It's a WebElement
                result = self.driver.execute_script(
                    """const attributes = {};
                    for (let i = 0; i < arguments[0].attributes.length; i++) {
                        const attr = arguments[0].attributes[i];
                        attributes[attr.name] = attr.value;
                    }
                    return attributes;
                    """, 
                    element_or_selector
                )
            
            return result if result else {}
        except Exception as e:
            logger.error(f"Error getting element attributes: {str(e)}")
            return {}
    
    def js_execute_with_retry(self, script: str, max_retries: int = 3, retry_delay: float = 1.0) -> Any:
        """Execute JavaScript with retry logic."""
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                result = self.driver.execute_script(script)
                return result
            except Exception as e:
                last_error = e
                retries += 1
                logger.warning(f"JavaScript execution failed (attempt {retries}/{max_retries}): {str(e)}")
                time.sleep(retry_delay)
        
        logger.error(f"JavaScript execution failed after {max_retries} attempts: {str(last_error)}")
        raise last_error
    
    def js_wait_for_network_idle(self, timeout: int = 30, idle_time: float = 1.0) -> bool:
        """Wait for network to be idle (no pending requests)."""
        try:
            # Inject network monitoring if not already done
            self.driver.execute_script("""
            if (!window.__networkMonitor) {
                window.__networkMonitor = {
                    requests: new Set(),
                    lastRequestTime: Date.now()
                };
                
                // Intercept fetch
                if (window.fetch && !window.__fetchNetworkIntercepted) {
                    const originalFetch = window.fetch;
                    
                    window.fetch = function() {
                        const requestId = Date.now() + Math.random();
                        window.__networkMonitor.requests.add(requestId);
                        window.__networkMonitor.lastRequestTime = Date.now();
                        
                        return originalFetch.apply(this, arguments)
                            .then(response => {
                                window.__networkMonitor.requests.delete(requestId);
                                window.__networkMonitor.lastRequestTime = Date.now();
                                return response;
                            })
                            .catch(error => {
                                window.__networkMonitor.requests.delete(requestId);
                                window.__networkMonitor.lastRequestTime = Date.now();
                                throw error;
                            });
                    };
                    
                    window.__fetchNetworkIntercepted = true;
                }
                
                // Intercept XHR
                if (window.XMLHttpRequest && !window.__xhrNetworkIntercepted) {
                    const originalOpen = XMLHttpRequest.prototype.open;
                    const originalSend = XMLHttpRequest.prototype.send;
                    
                    XMLHttpRequest.prototype.open = function() {
                        this.__requestId = Date.now() + Math.random();
                        return originalOpen.apply(this, arguments);
                    };
                    
                    XMLHttpRequest.prototype.send = function() {
                        window.__networkMonitor.requests.add(this.__requestId);
                        window.__networkMonitor.lastRequestTime = Date.now();
                        
                        this.addEventListener('loadend', function() {
                            window.__networkMonitor.requests.delete(this.__requestId);
                            window.__networkMonitor.lastRequestTime = Date.now();
                        });
                        
                        return originalSend.apply(this, arguments);
                    };
                    
                    window.__xhrNetworkIntercepted = true;
                }
            }
            """)
            
            start_time = time.time()
            last_activity_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if there are any pending requests
                pending_requests = self.driver.execute_script("return window.__networkMonitor.requests.size;")
                last_request_time = self.driver.execute_script("return window.__networkMonitor.lastRequestTime;")
                
                current_time = time.time() * 1000  # Convert to milliseconds to match JavaScript time
                time_since_last_request = current_time - last_request_time
                
                if pending_requests == 0 and time_since_last_request > idle_time * 1000:
                    logger.info(f"Network idle detected after {time.time() - start_time:.2f} seconds")
                    return True
                
                # If there was activity, update the last activity time
                if last_request_time > last_activity_time * 1000:
                    last_activity_time = last_request_time / 1000  # Convert back to seconds
                
                time.sleep(0.5)
            
            logger.warning(f"Timeout waiting for network idle after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"Error waiting for network idle: {str(e)}")
            return False
    
    def js_get_console_logs(self) -> List[str]:
        """Get browser console logs using JavaScript."""
        try:
            # Inject console log capture if not already done
            self.driver.execute_script("""
            if (!window.__consoleLogs) {
                window.__consoleLogs = [];
                const originalConsoleLog = console.log;
                const originalConsoleError = console.error;
                const originalConsoleWarn = console.warn;
                const originalConsoleInfo = console.info;
                
                console.log = function() {
                    window.__consoleLogs.push({type: 'log', message: Array.from(arguments).join(' '), timestamp: new Date().toISOString()});
                    originalConsoleLog.apply(console, arguments);
                };
                
                console.error = function() {
                    window.__consoleLogs.push({type: 'error', message: Array.from(arguments).join(' '), timestamp: new Date().toISOString()});
                    originalConsoleError.apply(console, arguments);
                };
                
                console.warn = function() {
                    window.__consoleLogs.push({type: 'warn', message: Array.from(arguments).join(' '), timestamp: new Date().toISOString()});
                    originalConsoleWarn.apply(console, arguments);
                };
                
                console.info = function() {
                    window.__consoleLogs.push({type: 'info', message: Array.from(arguments).join(' '), timestamp: new Date().toISOString()});
                    originalConsoleInfo.apply(console, arguments);
                };
            }
            """)
            
            # Get the logs
            logs = self.driver.execute_script("return window.__consoleLogs;")
            
            # Format logs as strings
            formatted_logs = []
            for log in logs if logs else []:
                formatted_logs.append(f"[{log.get('timestamp', '')}] [{log.get('type', '').upper()}] {log.get('message', '')}")
            
            return formatted_logs
        except Exception as e:
            logger.error(f"Error getting console logs: {str(e)}")
            return []
    
    def js_clear_console_logs(self) -> bool:
        """Clear captured console logs."""
        try:
            self.driver.execute_script("window.__consoleLogs = [];")
            return True
        except Exception as e:
            logger.error(f"Error clearing console logs: {str(e)}")
            return False
    
    def js_get_network_requests(self) -> List[Dict[str, Any]]:
        """Get network requests using JavaScript."""
        try:
            # Inject network request capture if not already done
            self.driver.execute_script("""
            if (!window.__networkRequests) {
                window.__networkRequests = [];
                
                // Use Performance API to get existing requests
                if (window.performance && performance.getEntriesByType) {
                    const resources = performance.getEntriesByType('resource');
                    for (const resource of resources) {
                        window.__networkRequests.push({
                            url: resource.name,
                            method: 'GET',  // Performance API doesn't provide method
                            type: resource.initiatorType,
                            status: 200,  // Performance API doesn't provide status
                            duration: resource.duration,
                            startTime: resource.startTime,
                            endTime: resource.responseEnd
                        });
                    }
                }
                
                // Intercept fetch for future requests
                if (window.fetch && !window.__fetchRequestsIntercepted) {
                    const originalFetch = window.fetch;
                    
                    window.fetch = function(input, init) {
                        const url = typeof input === 'string' ? input : input.url;
                        const method = init && init.method ? init.method : 'GET';
                        const startTime = performance.now();
                        const request = {
                            url,
                            method,
                            type: 'fetch',
                            status: null,
                            duration: null,
                            startTime,
                            endTime: null
                        };
                        
                        return originalFetch.apply(this, arguments)
                            .then(response => {
                                const endTime = performance.now();
                                request.status = response.status;
                                request.duration = endTime - startTime;
                                request.endTime = endTime;
                                window.__networkRequests.push(request);
                                return response;
                            })
                            .catch(error => {
                                const endTime = performance.now();
                                request.status = 0;
                                request.error = error.toString();
                                request.duration = endTime - startTime;
                                request.endTime = endTime;
                                window.__networkRequests.push(request);
                                throw error;
                            });
                    };
                    
                    window.__fetchRequestsIntercepted = true;
                }
                
                // Intercept XHR for future requests
                if (window.XMLHttpRequest && !window.__xhrRequestsIntercepted) {
                    const originalOpen = XMLHttpRequest.prototype.open;
                    const originalSend = XMLHttpRequest.prototype.send;
                    
                    XMLHttpRequest.prototype.open = function(method, url) {
                        this.__requestMethod = method;
                        this.__requestUrl = url;
                        return originalOpen.apply(this, arguments);
                    };
                    
                    XMLHttpRequest.prototype.send = function() {
                        const startTime = performance.now();
                        this.__requestStartTime = startTime;
                        
                        this.addEventListener('loadend', function() {
                            const endTime = performance.now();
                            window.__networkRequests.push({
                                url: this.__requestUrl,
                                method: this.__requestMethod,
                                type: 'xhr',
                                status: this.status,
                                duration: endTime - startTime,
                                startTime,
                                endTime
                            });
                        });
                        
                        return originalSend.apply(this, arguments);
                    };
                    
                    window.__xhrRequestsIntercepted = true;
                }
            }
            """)
            
            # Get the network requests
            requests = self.driver.execute_script("return window.__networkRequests;")
            
            return requests if requests else []
        except Exception as e:
            logger.error(f"Error getting network requests: {str(e)}")
            return []
    
    def js_clear_network_requests(self) -> bool:
        """Clear captured network requests."""
        try:
            self.driver.execute_script("window.__networkRequests = [];")
            return True
        except Exception as e:
            logger.error(f"Error clearing network requests: {str(e)}")
            return False