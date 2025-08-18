#!/usr/bin/env python3
"""
Adaptive TradeBot Sentinel - AI-Powered Self-Learning Automation

This enhanced version uses:
1. Computer Vision (OpenCV) for visual element detection
2. AI-powered selector discovery and learning
3. Dynamic adaptation to UI changes
4. Self-updating selector database
5. Screenshot-based fallback mechanisms

No more manual selector updates needed!
"""

import asyncio
import json
import os
import cv2
import numpy as np
from datetime import datetime
from playwright.async_api import async_playwright, Page
from typing import Optional, Dict, Any, List, Tuple
import base64
from pathlib import Path

class AdaptiveTradeBotSentinel:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
        # AI Learning Database
        self.selector_db_path = "adaptive_selectors.json"
        self.selector_db = self.load_selector_database()
        
        # Computer Vision Templates
        self.template_dir = Path("cv_templates")
        self.template_dir.mkdir(exist_ok=True)
        
        # Learning parameters
        self.confidence_threshold = 0.8
        self.learning_enabled = True
        
    def load_selector_database(self) -> Dict:
        """Load or create adaptive selector database"""
        if os.path.exists(self.selector_db_path):
            with open(self.selector_db_path, 'r') as f:
                return json.load(f)
        return {
            "time_sync_warning": {
                "modal_selectors": [],
                "close_selectors": [],
                "success_rate": {},
                "last_updated": None
            },
            "login_elements": {
                "username_selectors": [],
                "password_selectors": [],
                "submit_selectors": [],
                "success_rate": {},
                "last_updated": None
            },
            "trading_elements": {
                "order_tab_selectors": [],
                "amount_selectors": [],
                "submit_selectors": [],
                "success_rate": {},
                "last_updated": None
            }
        }
    
    def save_selector_database(self):
        """Save updated selector database"""
        with open(self.selector_db_path, 'w') as f:
            json.dump(self.selector_db, f, indent=2)
    
    async def setup_browser(self):
        """Setup browser with enhanced debugging capabilities"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--enable-automation'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await self.context.new_page()
        
        # Enable console logging for AI learning
        self.page.on('console', self.log_console_message)
        
        print("[AI-SENTINEL] Adaptive browser setup complete")
    
    async def log_console_message(self, msg):
        """Log console messages for learning"""
        if self.learning_enabled:
            print(f"[CONSOLE-LEARN] {msg.text}")
    
    async def take_screenshot_for_cv(self, filename: str = None) -> str:
        """Take screenshot for computer vision analysis"""
        if not filename:
            filename = f"cv_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        screenshot_path = self.template_dir / filename
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    
    def detect_elements_by_template(self, screenshot_path: str, template_name: str) -> List[Tuple[int, int]]:
        """Use OpenCV template matching to find UI elements"""
        template_path = self.template_dir / f"{template_name}.png"
        
        if not template_path.exists():
            print(f"[CV-WARNING] Template {template_name} not found")
            return []
        
        # Load images
        screenshot = cv2.imread(screenshot_path)
        template = cv2.imread(str(template_path))
        
        if screenshot is None or template is None:
            return []
        
        # Template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= self.confidence_threshold)
        
        # Return center coordinates of matches
        matches = []
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + template.shape[1] // 2
            center_y = pt[1] + template.shape[0] // 2
            matches.append((center_x, center_y))
        
        return matches
    
    async def ai_discover_selectors(self, element_type: str, context_keywords: List[str]) -> List[str]:
        """AI-powered selector discovery using DOM analysis"""
        print(f"[AI-DISCOVERY] Discovering selectors for {element_type}")
        
        # Get all elements with potential relevance
        discovered_selectors = []
        
        # Analyze by text content
        for keyword in context_keywords:
            selectors = await self.page.evaluate(f"""
                () => {{
                    const elements = Array.from(document.querySelectorAll('*'));
                    const matches = [];
                    
                    elements.forEach(el => {{
                        const text = el.textContent?.toLowerCase() || '';
                        const placeholder = el.placeholder?.toLowerCase() || '';
                        const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
                        const className = el.className || '';
                        const id = el.id || '';
                        
                        if (text.includes('{keyword.lower()}') || 
                            placeholder.includes('{keyword.lower()}') ||
                            ariaLabel.includes('{keyword.lower()}') ||
                            className.toLowerCase().includes('{keyword.lower()}') ||
                            id.toLowerCase().includes('{keyword.lower()}')) {{
                            
                            // Generate multiple selector strategies
                            const selectors = [];
                            
                            // ID selector
                            if (el.id) selectors.push(`#${{el.id}}`);
                            
                            // Class selector
                            if (el.className) {{
                                const classes = el.className.split(' ').filter(c => c.length > 0);
                                if (classes.length > 0) {{
                                    selectors.push(`.${{classes.join('.')}}}`);
                                }}
                            }}
                            
                            // Attribute selectors
                            if (el.placeholder) selectors.push(`[placeholder="${{el.placeholder}}"]`);
                            if (el.getAttribute('aria-label')) selectors.push(`[aria-label="${{el.getAttribute('aria-label')}}"]`);
                            
                            // Text-based selectors
                            if (el.textContent && el.textContent.trim()) {{
                                selectors.push(`${{el.tagName.toLowerCase()}}:has-text("${{el.textContent.trim()}}")`);
                            }}
                            
                            // CSS path
                            let path = [];
                            let current = el;
                            while (current && current !== document.body) {{
                                let selector = current.tagName.toLowerCase();
                                if (current.id) {{
                                    selector += `#${{current.id}}`;
                                    path.unshift(selector);
                                    break;
                                }} else if (current.className) {{
                                    const classes = current.className.split(' ').filter(c => c.length > 0);
                                    if (classes.length > 0) {{
                                        selector += `.${{classes[0]}}`;
                                    }}
                                }}
                                path.unshift(selector);
                                current = current.parentElement;
                            }}
                            if (path.length > 0) selectors.push(path.join(' > '));
                            
                            matches.push(...selectors);
                        }}
                    }});
                    
                    return [...new Set(matches)];
                }}
            """)
            
            discovered_selectors.extend(selectors)
        
        # Remove duplicates and return
        unique_selectors = list(set(discovered_selectors))
        print(f"[AI-DISCOVERY] Found {len(unique_selectors)} potential selectors")
        
        return unique_selectors
    
    async def test_selector_effectiveness(self, selectors: List[str], action_type: str = "click") -> Dict[str, float]:
        """Test and rate selector effectiveness"""
        effectiveness_scores = {}
        
        for selector in selectors:
            try:
                # Test if selector finds elements
                elements = await self.page.query_selector_all(selector)
                if not elements:
                    effectiveness_scores[selector] = 0.0
                    continue
                
                # Test if elements are interactable
                score = 0.5  # Base score for finding elements
                
                for element in elements[:3]:  # Test up to 3 elements
                    try:
                        # Check visibility
                        is_visible = await element.is_visible()
                        if is_visible:
                            score += 0.2
                        
                        # Check if enabled
                        is_enabled = await element.is_enabled()
                        if is_enabled:
                            score += 0.2
                        
                        # Check bounding box
                        bbox = await element.bounding_box()
                        if bbox and bbox['width'] > 0 and bbox['height'] > 0:
                            score += 0.1
                        
                    except Exception:
                        continue
                
                effectiveness_scores[selector] = min(score, 1.0)
                
            except Exception as e:
                effectiveness_scores[selector] = 0.0
        
        return effectiveness_scores
    
    async def adaptive_handle_time_sync_warning(self) -> bool:
        """AI-powered adaptive time sync warning handling"""
        print("[AI-ADAPTIVE] Handling time sync warning with AI")
        
        # Take screenshot for CV analysis
        screenshot_path = await self.take_screenshot_for_cv("time_sync_analysis.png")
        
        # Try existing selectors first
        existing_selectors = self.selector_db["time_sync_warning"]["modal_selectors"]
        
        modal_found = False
        for selector in existing_selectors:
            try:
                modal = await self.page.wait_for_selector(selector, timeout=2000)
                if modal:
                    modal_found = True
                    break
            except Exception:
                continue
        
        # If no existing selectors work, use AI discovery
        if not modal_found:
            print("[AI-LEARNING] Discovering new time sync warning selectors")
            
            # AI discovery for modal
            modal_keywords = ["time sync", "warning", "clock", "synchronized", "modal", "dialog"]
            new_modal_selectors = await self.ai_discover_selectors("time_sync_modal", modal_keywords)
            
            # Test effectiveness
            modal_scores = await self.test_selector_effectiveness(new_modal_selectors)
            
            # Add effective selectors to database
            for selector, score in modal_scores.items():
                if score > 0.5 and selector not in existing_selectors:
                    self.selector_db["time_sync_warning"]["modal_selectors"].append(selector)
                    self.selector_db["time_sync_warning"]["success_rate"][selector] = score
            
            # Try new selectors
            for selector in self.selector_db["time_sync_warning"]["modal_selectors"]:
                try:
                    modal = await self.page.wait_for_selector(selector, timeout=2000)
                    if modal:
                        modal_found = True
                        break
                except Exception:
                    continue
        
        if not modal_found:
            # Fallback to computer vision
            print("[CV-FALLBACK] Using computer vision for modal detection")
            modal_matches = self.detect_elements_by_template(screenshot_path, "time_sync_modal")
            if modal_matches:
                modal_found = True
        
        if modal_found:
            # Now find close button using AI
            return await self.adaptive_close_modal()
        
        return False
    
    async def adaptive_close_modal(self) -> bool:
        """AI-powered modal closing"""
        print("[AI-ADAPTIVE] Finding close button with AI")
        
        # Try existing close selectors
        existing_close_selectors = self.selector_db["time_sync_warning"]["close_selectors"]
        
        for selector in existing_close_selectors:
            try:
                await self.page.click(selector)
                print(f"[SUCCESS] Modal closed with existing selector: {selector}")
                return True
            except Exception:
                continue
        
        # AI discovery for close buttons
        close_keywords = ["close", "dismiss", "ok", "continue", "got it", "×", "cancel"]
        new_close_selectors = await self.ai_discover_selectors("close_button", close_keywords)
        
        # Test effectiveness
        close_scores = await self.test_selector_effectiveness(new_close_selectors, "click")
        
        # Try new selectors
        for selector, score in sorted(close_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.3:  # Lower threshold for close buttons
                try:
                    await self.page.click(selector)
                    print(f"[AI-SUCCESS] Modal closed with new selector: {selector}")
                    
                    # Add to database
                    if selector not in existing_close_selectors:
                        self.selector_db["time_sync_warning"]["close_selectors"].append(selector)
                        self.selector_db["time_sync_warning"]["success_rate"][selector] = score
                        self.save_selector_database()
                    
                    return True
                except Exception:
                    continue
        
        # Final fallback - Escape key
        try:
            await self.page.keyboard.press('Escape')
            print("[FALLBACK] Modal closed with Escape key")
            return True
        except Exception:
            pass
        
        return False
    
    async def adaptive_login(self, username: str, password: str) -> bool:
        """AI-powered adaptive login"""
        print("[AI-ADAPTIVE] Starting adaptive login process")
        
        # Navigate to login page
        await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
        
        # Handle time sync warning
        await self.adaptive_handle_time_sync_warning()
        
        # Take screenshot for analysis
        screenshot_path = await self.take_screenshot_for_cv("login_analysis.png")
        
        # AI-powered username field detection
        username_success = await self.adaptive_fill_field("username", username, 
            ["username", "email", "user", "login", "account"])
        
        if not username_success:
            print("[AI-ERROR] Could not find username field")
            return False
        
        # AI-powered password field detection
        password_success = await self.adaptive_fill_field("password", password,
            ["password", "pass", "pwd", "secret"])
        
        if not password_success:
            print("[AI-ERROR] Could not find password field")
            return False
        
        # AI-powered submit button detection
        submit_success = await self.adaptive_submit_form()
        
        if submit_success:
            # Handle post-login time sync warning
            await asyncio.sleep(2)
            await self.adaptive_handle_time_sync_warning()
            return True
        
        return False
    
    async def adaptive_fill_field(self, field_type: str, value: str, keywords: List[str]) -> bool:
        """AI-powered form field filling"""
        print(f"[AI-ADAPTIVE] Filling {field_type} field")
        
        # Try existing selectors
        existing_selectors = self.selector_db["login_elements"].get(f"{field_type}_selectors", [])
        
        for selector in existing_selectors:
            try:
                await self.page.fill(selector, value)
                print(f"[SUCCESS] {field_type} filled with existing selector")
                return True
            except Exception:
                continue
        
        # AI discovery
        new_selectors = await self.ai_discover_selectors(f"{field_type}_field", keywords)
        
        # Test and try new selectors
        field_scores = await self.test_selector_effectiveness(new_selectors)
        
        for selector, score in sorted(field_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.4:
                try:
                    await self.page.fill(selector, value)
                    print(f"[AI-SUCCESS] {field_type} filled with new selector: {selector}")
                    
                    # Add to database
                    if selector not in existing_selectors:
                        self.selector_db["login_elements"][f"{field_type}_selectors"].append(selector)
                        self.save_selector_database()
                    
                    return True
                except Exception:
                    continue
        
        return False
    
    async def adaptive_submit_form(self) -> bool:
        """AI-powered form submission"""
        print("[AI-ADAPTIVE] Submitting login form")
        
        # Try existing submit selectors
        existing_selectors = self.selector_db["login_elements"].get("submit_selectors", [])
        
        for selector in existing_selectors:
            try:
                await self.page.click(selector)
                print(f"[SUCCESS] Form submitted with existing selector")
                return True
            except Exception:
                continue
        
        # AI discovery for submit buttons
        submit_keywords = ["login", "sign in", "submit", "enter", "go", "continue"]
        new_selectors = await self.ai_discover_selectors("submit_button", submit_keywords)
        
        # Test and try new selectors
        submit_scores = await self.test_selector_effectiveness(new_selectors)
        
        for selector, score in sorted(submit_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.4:
                try:
                    await self.page.click(selector)
                    print(f"[AI-SUCCESS] Form submitted with new selector: {selector}")
                    
                    # Add to database
                    if selector not in existing_selectors:
                        self.selector_db["login_elements"]["submit_selectors"].append(selector)
                        self.save_selector_database()
                    
                    return True
                except Exception:
                    continue
        
        # Fallback - try Enter key
        try:
            await self.page.keyboard.press('Enter')
            print("[FALLBACK] Form submitted with Enter key")
            return True
        except Exception:
            pass
        
        return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        # Save final selector database
        self.save_selector_database()
        print("[AI-SENTINEL] Cleanup complete, selectors saved")

# Example usage
async def main():
    # Initialize adaptive bot
    bot = AdaptiveTradeBotSentinel(headless=False)
    
    try:
        await bot.setup_browser()
        
        # Get credentials
        username = os.getenv('BULENOX_USERNAME')
        password = os.getenv('BULENOX_PASSWORD')
        
        if not username or not password:
            print("[ERROR] Please set BULENOX_USERNAME and BULENOX_PASSWORD environment variables")
            return
        
        # Adaptive login
        login_success = await bot.adaptive_login(username, password)
        
        if login_success:
            print("[AI-SUCCESS] Adaptive login completed successfully!")
            print(f"[AI-INFO] Learned selectors saved to {bot.selector_db_path}")
        else:
            print("[AI-ERROR] Adaptive login failed")
        
        # Keep browser open for inspection
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"[AI-ERROR] {e}")
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())