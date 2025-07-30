# O.R.I.G.I.N. Cloud Prime - JavaScript-Enhanced Selenium Integration
# Provides advanced JavaScript-based solutions for Selenium automation challenges

import time
import logging
import json
from typing import Dict, Any, Optional, Union, List, Callable
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
    JavascriptException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/js_selenium.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("js_selenium")

class JSSeleniumHelper:
    """Provides JavaScript-enhanced solutions for Selenium automation challenges"""
    
    def __init__(self, driver: WebDriver):
        """Initialize the helper with a WebDriver instance
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self._setup_js_helpers()
        logger.info("JavaScript-Enhanced Selenium Helper initialized")
    
    def _setup_js_helpers(self) -> None:
        """Inject helper JavaScript functions into the page"""
        try:
            # Inject utility functions that will be available in the page context
            self.driver.execute_script("""
            window.__seleniumHelpers = {
                // Store state for tracking page readiness
                state: {
                    pageReady: false,
                    ajaxRequests: 0,
                    lastActivity: Date.now()
                },
                
                // Track AJAX requests
                trackAjax: function() {
                    const originalXHR = window.XMLHttpRequest;
                    window.XMLHttpRequest = function() {
                        const xhr = new originalXHR();
                        const originalOpen = xhr.open;
                        const originalSend = xhr.send;
                        
                        xhr.open = function() {
                            window.__seleniumHelpers.state.lastActivity = Date.now();
                            return originalOpen.apply(this, arguments);
                        };
                        
                        xhr.send = function() {
                            window.__seleniumHelpers.state.ajaxRequests++;
                            window.__seleniumHelpers.state.lastActivity = Date.now();
                            
                            xhr.addEventListener('loadend', function() {
                                window.__seleniumHelpers.state.ajaxRequests--;
                                window.__seleniumHelpers.state.lastActivity = Date.now();
                            });
                            
                            return originalSend.apply(this, arguments);
                        };
                        
                        return xhr;
                    };
                },
                
                // Track fetch requests
                trackFetch: function() {
                    const originalFetch = window.fetch;
                    window.fetch = function() {
                        window.__seleniumHelpers.state.ajaxRequests++;
                        window.__seleniumHelpers.state.lastActivity = Date.now();
                        
                        return originalFetch.apply(this, arguments)
                            .then(function(response) {
                                window.__seleniumHelpers.state.ajaxRequests--;
                                window.__seleniumHelpers.state.lastActivity = Date.now();
                                return response;
                            })
                            .catch(function(error) {
                                window.__seleniumHelpers.state.ajaxRequests--;
                                window.__seleniumHelpers.state.lastActivity = Date.now();
                                throw error;
                            });
                    };
                },
                
                // Check if page is truly ready (DOM + AJAX)
                isPageReady: function() {
                    return document.readyState === 'complete' && 
                           window.__seleniumHelpers.state.ajaxRequests === 0 &&
                           (Date.now() - window.__seleniumHelpers.state.lastActivity) > 500;
                },
                
                // Patch navigator.webdriver to avoid bot detection
                patchNavigatorWebdriver: function() {
                    if (navigator.webdriver === true) {
                        Object.defineProperty(navigator, 'webdriver', {
                            get: function() { return undefined; }
                        });
                    }
                },
                
                // Click an element using JavaScript
                clickElement: function(element) {
                    if (element) {
                        // Scroll element into view first
                        element.scrollIntoView({behavior: 'instant', block: 'center'});
                        
                        // Try multiple click methods
                        try {
                            // Method 1: Standard click
                            element.click();
                        } catch (e) {
                            try {
                                // Method 2: MouseEvent
                                const evt = new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                });
                                element.dispatchEvent(evt);
                            } catch (e2) {
                                // Method 3: Direct function call for buttons
                                if (typeof element.onclick === 'function') {
                                    element.onclick();
                                }
                            }
                        }
                        return true;
                    }
                    return false;
                },
                
                // Set value on input element and trigger events
                setInputValue: function(element, value) {
                    if (element) {
                        // Focus the element
                        element.focus();
                        
                        // Set the value
                        element.value = value;
                        
                        // Trigger events
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        return true;
                    }
                    return false;
                },
                
                // Find element by XPath
                findElementByXPath: function(xpath) {
                    return document.evaluate(
                        xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                    ).singleNodeValue;
                },
                
                // Find elements by text content
                findElementsByText: function(text, tag = '*', exactMatch = false) {
                    const elements = Array.from(document.getElementsByTagName(tag));
                    return elements.filter(el => {
                        const content = el.textContent.trim();
                        return exactMatch ? content === text : content.includes(text);
                    });
                },
                
                // Get computed visibility of element
                isElementVisible: function(element) {
                    if (!element) return false;
                    
                    const style = window.getComputedStyle(element);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' && 
                           style.opacity !== '0' &&
                           element.offsetWidth > 0 &&
                           element.offsetHeight > 0;
                },
                
                // Wait for element to be visible and enabled
                waitForElement: function(selector, timeoutMs) {
                    return new Promise((resolve, reject) => {
                        const startTime = Date.now();
                        const checkElement = () => {
                            const element = document.querySelector(selector);
                            if (element && this.isElementVisible(element)) {
                                resolve(element);
                                return;
                            }
                            
                            if (Date.now() - startTime > timeoutMs) {
                                reject(new Error(`Element ${selector} not found or visible within ${timeoutMs}ms`));
                                return;
                            }
                            
                            setTimeout(checkElement, 100);
                        };
                        
                        checkElement();
                    });
                },
                
                // Extract data from the page
                extractPageData: function() {
                    // This is a placeholder that can be customized per broker
                    const data = {
                        url: window.location.href,
                        title: document.title,
                        // Add broker-specific data extraction here
                    };
                    
                    // Example: Extract account balance if available
                    if (window.accountBalance !== undefined) {
                        data.accountBalance = window.accountBalance;
                    }
                    
                    return data;
                }
            };
            
            // Initialize trackers
            window.__seleniumHelpers.trackAjax();
            window.__seleniumHelpers.trackFetch();
            window.__seleniumHelpers.patchNavigatorWebdriver();
            
            // Set page ready flag when DOM is fully loaded
            if (document.readyState === 'complete') {
                window.__seleniumHelpers.state.pageReady = true;
            } else {
                window.addEventListener('load', function() {
                    window.__seleniumHelpers.state.pageReady = true;
                });
            }
            
            return 'JS Helpers initialized';
            """)
            logger.info("Injected JavaScript helpers into page")
        except Exception as e:
            logger.error(f"Failed to inject JavaScript helpers: {str(e)}")
    
    def wait_for_page_ready(self, timeout: int = 30) -> bool:
        """Wait for the page to be fully loaded and all AJAX requests to complete
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if page is ready, False if timeout occurred
        """
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                is_ready = self.driver.execute_script("return window.__seleniumHelpers.isPageReady();")
                if is_ready:
                    logger.info(f"Page ready after {time.time() - start_time:.1f} seconds")
                    return True
                time.sleep(0.5)
            
            logger.warning(f"Timeout waiting for page to be ready after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"Error waiting for page ready: {str(e)}")
            return False
    
    def js_click(self, element: WebElement) -> bool:
        """Click an element using JavaScript
        
        Args:
            element: The WebElement to click
            
        Returns:
            True if click was successful, False otherwise
        """
        try:
            result = self.driver.execute_script(
                "return window.__seleniumHelpers.clickElement(arguments[0]);", 
                element
            )
            if result:
                logger.info(f"JavaScript click successful on {element}")
            else:
                logger.warning(f"JavaScript click failed on {element}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error during JavaScript click: {str(e)}")
            return False
    
    def js_set_value(self, element: WebElement, value: str) -> bool:
        """Set value on input element using JavaScript
        
        Args:
            element: The WebElement to set value on
            value: The value to set
            
        Returns:
            True if setting value was successful, False otherwise
        """
        try:
            result = self.driver.execute_script(
                "return window.__seleniumHelpers.setInputValue(arguments[0], arguments[1]);", 
                element, value
            )
            if result:
                logger.info(f"JavaScript set value '{value}' successful on {element}")
            else:
                logger.warning(f"JavaScript set value '{value}' failed on {element}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error during JavaScript set value: {str(e)}")
            return False
    
    def find_element_by_text(self, text: str, tag: str = '*', exact_match: bool = False) -> Optional[WebElement]:
        """Find an element by its text content using JavaScript
        
        Args:
            text: The text to search for
            tag: The HTML tag to limit the search to (default: '*' for all tags)
            exact_match: Whether to require an exact text match
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            elements = self.driver.execute_script(
                "return window.__seleniumHelpers.findElementsByText(arguments[0], arguments[1], arguments[2]);", 
                text, tag, exact_match
            )
            if elements and len(elements) > 0:
                logger.info(f"Found element with text '{text}'")
                return elements[0]
            else:
                logger.warning(f"No element found with text '{text}'")
                return None
        except Exception as e:
            logger.error(f"Error finding element by text: {str(e)}")
            return None
    
    def is_element_visible(self, element: WebElement) -> bool:
        """Check if an element is visible using JavaScript
        
        Args:
            element: The WebElement to check
            
        Returns:
            True if element is visible, False otherwise
        """
        try:
            return bool(self.driver.execute_script(
                "return window.__seleniumHelpers.isElementVisible(arguments[0]);", 
                element
            ))
        except Exception as e:
            logger.error(f"Error checking element visibility: {str(e)}")
            return False
    
    def extract_page_data(self) -> Dict[str, Any]:
        """Extract data from the page using JavaScript
        
        Returns:
            Dictionary of extracted data
        """
        try:
            data = self.driver.execute_script("return window.__seleniumHelpers.extractPageData();")
            logger.info(f"Extracted page data: {json.dumps(data, indent=2)}")
            return data
        except Exception as e:
            logger.error(f"Error extracting page data: {str(e)}")
            return {}
    
    def patch_navigator_webdriver(self) -> bool:
        """Patch navigator.webdriver to avoid bot detection
        
        Returns:
            True if patch was successful, False otherwise
        """
        try:
            self.driver.execute_script("window.__seleniumHelpers.patchNavigatorWebdriver();")
            logger.info("Patched navigator.webdriver")
            return True
        except Exception as e:
            logger.error(f"Error patching navigator.webdriver: {str(e)}")
            return False
    
    def safe_click(self, element: WebElement, timeout: int = 10) -> bool:
        """Attempt to click an element safely, falling back to JavaScript if needed
        
        Args:
            element: The WebElement to click
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if click was successful, False otherwise
        """
        try:
            # First try regular Selenium click
            element.click()
            logger.info(f"Regular click successful on {element}")
            return True
        except (ElementNotInteractableException, ElementClickInterceptedException) as e:
            logger.warning(f"Regular click failed, trying JavaScript click: {str(e)}")
            return self.js_click(element)
        except Exception as e:
            logger.error(f"Error during safe click: {str(e)}")
            return False
    
    def safe_send_keys(self, element: WebElement, value: str) -> bool:
        """Attempt to send keys to an element safely, falling back to JavaScript if needed
        
        Args:
            element: The WebElement to send keys to
            value: The value to send
            
        Returns:
            True if sending keys was successful, False otherwise
        """
        try:
            # First try regular Selenium send_keys
            element.clear()
            element.send_keys(value)
            logger.info(f"Regular send_keys successful on {element}")
            return True
        except (ElementNotInteractableException, ElementClickInterceptedException) as e:
            logger.warning(f"Regular send_keys failed, trying JavaScript: {str(e)}")
            return self.js_set_value(element, value)
        except Exception as e:
            logger.error(f"Error during safe send_keys: {str(e)}")
            return False
    
    def wait_for_element(self, by: By, value: str, timeout: int = 30, visible: bool = True) -> Optional[WebElement]:
        """Wait for an element to be present and optionally visible
        
        Args:
            by: The locator strategy to use
            value: The locator value
            timeout: Maximum time to wait in seconds
            visible: Whether to wait for visibility as well
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            if visible:
                element = wait.until(EC.visibility_of_element_located((by, value)))
            else:
                element = wait.until(EC.presence_of_element_located((by, value)))
            
            logger.info(f"Element found: {by}={value}")
            return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for element: {str(e)}")
            return None
    
    def execute_async_js(self, script: str, *args) -> Any:
        """Execute asynchronous JavaScript
        
        Args:
            script: The JavaScript to execute
            *args: Arguments to pass to the script
            
        Returns:
            Result of the script execution
        """
        try:
            # Ensure script uses the 'callback' argument as the last parameter
            # Example: "var callback = arguments[arguments.length - 1]; setTimeout(function() { callback('done'); }, 1000);"
            result = self.driver.execute_async_script(script, *args)
            logger.info(f"Async JavaScript executed successfully")
            return result
        except JavascriptException as e:
            logger.error(f"JavaScript error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error executing async JavaScript: {str(e)}")
            return None
    
    def wait_for_js_condition(self, condition: str, timeout: int = 30, poll_frequency: float = 0.5) -> bool:
        """Wait for a JavaScript condition to be true
        
        Args:
            condition: JavaScript condition that should return true/false
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check the condition in seconds
            
        Returns:
            True if condition became true, False if timeout occurred
        """
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                result = self.driver.execute_script(f"return Boolean({condition});")
                if result:
                    logger.info(f"JavaScript condition '{condition}' is true")
                    return True
                time.sleep(poll_frequency)
            
            logger.warning(f"Timeout waiting for JavaScript condition '{condition}'")
            return False
        except Exception as e:
            logger.error(f"Error waiting for JavaScript condition: {str(e)}")
            return False
    
    def create_custom_js_extractor(self, extraction_script: str) -> Callable[[], Any]:
        """Create a custom JavaScript data extractor function
        
        Args:
            extraction_script: JavaScript that extracts and returns data
            
        Returns:
            Function that when called executes the script and returns the result
        """
        def extractor() -> Any:
            try:
                return self.driver.execute_script(extraction_script)
            except Exception as e:
                logger.error(f"Error in custom JS extractor: {str(e)}")
                return None
        
        return extractor
    
    def inject_custom_js(self, script: str) -> bool:
        """Inject custom JavaScript into the page
        
        Args:
            script: JavaScript to inject
            
        Returns:
            True if injection was successful, False otherwise
        """
        try:
            self.driver.execute_script(script)
            logger.info("Custom JavaScript injected successfully")
            return True
        except Exception as e:
            logger.error(f"Error injecting custom JavaScript: {str(e)}")
            return False

# Example usage
def create_js_helper(driver: WebDriver) -> JSSeleniumHelper:
    """Create a JavaScript Selenium Helper instance
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        JSSeleniumHelper instance
    """
    helper = JSSeleniumHelper(driver)
    
    # Patch navigator.webdriver to avoid bot detection
    helper.patch_navigator_webdriver()
    
    # Wait for page to be fully loaded
    helper.wait_for_page_ready()
    
    return helper