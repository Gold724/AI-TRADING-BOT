#!/usr/bin/env python3
"""
TradeBot Sentinel Pro - Continuous Improvement Module
Detects UI changes, updates selectors, and captures session snapshots
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import base64
from collections import defaultdict, deque
import cv2
import numpy as np
from playwright.async_api import Page, Browser, ElementHandle
import difflib
import re
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_improvement.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """Type of UI change detected"""
    SELECTOR_INVALID = "selector_invalid"
    ELEMENT_MOVED = "element_moved"
    ELEMENT_REMOVED = "element_removed"
    NEW_ELEMENT = "new_element"
    LAYOUT_CHANGE = "layout_change"
    CONTENT_CHANGE = "content_change"
    STYLE_CHANGE = "style_change"

class SelectorType(Enum):
    """Type of selector"""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ROLE = "role"
    TESTID = "testid"

@dataclass
class UIElement:
    """UI element information"""
    selector: str
    selector_type: SelectorType
    tag_name: str
    text_content: str
    attributes: Dict[str, str]
    position: Dict[str, float]  # x, y, width, height
    parent_selector: Optional[str]
    children_count: int
    screenshot_hash: Optional[str] = None
    last_seen: str = ""
    confidence_score: float = 1.0

@dataclass
class UIChange:
    """UI change detection result"""
    id: str
    timestamp: str
    change_type: ChangeType
    element_selector: str
    old_element: Optional[UIElement]
    new_element: Optional[UIElement]
    confidence: float
    description: str
    suggested_fix: Optional[str]
    page_url: str
    screenshot_before: Optional[str]
    screenshot_after: Optional[str]
    auto_fixed: bool = False

@dataclass
class SelectorCandidate:
    """Candidate selector for element"""
    selector: str
    selector_type: SelectorType
    confidence: float
    stability_score: float
    uniqueness_score: float
    description: str

@dataclass
class SessionSnapshot:
    """Session snapshot for replay"""
    id: str
    timestamp: str
    page_url: str
    page_title: str
    dom_structure: str
    screenshot: str
    network_requests: List[Dict[str, Any]]
    user_actions: List[Dict[str, Any]]
    console_logs: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    metadata: Dict[str, Any]

class ElementTracker:
    """Tracks UI elements and their changes"""
    
    def __init__(self):
        self.tracked_elements: Dict[str, UIElement] = {}
        self.element_history: Dict[str, List[UIElement]] = defaultdict(list)
        self.selector_patterns: Dict[str, List[str]] = defaultdict(list)
        self.confidence_threshold = 0.7
        
    async def track_element(self, page: Page, selector: str, selector_type: SelectorType) -> Optional[UIElement]:
        """Track a UI element"""
        try:
            element = await page.query_selector(selector)
            if not element:
                return None
            
            # Get element information
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            text_content = await element.text_content() or ""
            attributes = await element.evaluate('el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))')
            bounding_box = await element.bounding_box()
            
            position = {
                'x': bounding_box['x'] if bounding_box else 0,
                'y': bounding_box['y'] if bounding_box else 0,
                'width': bounding_box['width'] if bounding_box else 0,
                'height': bounding_box['height'] if bounding_box else 0
            }
            
            # Get parent selector
            parent_selector = None
            try:
                parent = await element.evaluate('el => el.parentElement')
                if parent:
                    parent_selector = await self.generate_selector(page, parent)
            except:
                pass
            
            # Count children
            children_count = await element.evaluate('el => el.children.length')
            
            # Take element screenshot
            screenshot_hash = None
            try:
                screenshot = await element.screenshot()
                screenshot_hash = hashlib.md5(screenshot).hexdigest()
            except:
                pass
            
            ui_element = UIElement(
                selector=selector,
                selector_type=selector_type,
                tag_name=tag_name,
                text_content=text_content,
                attributes=attributes,
                position=position,
                parent_selector=parent_selector,
                children_count=children_count,
                screenshot_hash=screenshot_hash,
                last_seen=datetime.now().isoformat()
            )
            
            # Store in tracking
            element_key = f"{selector}_{selector_type.value}"
            self.tracked_elements[element_key] = ui_element
            self.element_history[element_key].append(ui_element)
            
            # Keep only recent history
            if len(self.element_history[element_key]) > 10:
                self.element_history[element_key] = self.element_history[element_key][-10:]
            
            return ui_element
            
        except Exception as e:
            logger.error(f"Error tracking element {selector}: {e}")
            return None
    
    async def generate_selector(self, page: Page, element: ElementHandle) -> str:
        """Generate a robust selector for an element"""
        try:
            # Try different selector strategies
            selectors = []
            
            # ID selector
            element_id = await element.get_attribute('id')
            if element_id:
                selectors.append(f"#{element_id}")
            
            # Class selector
            class_name = await element.get_attribute('class')
            if class_name:
                classes = class_name.strip().split()
                if classes:
                    selectors.append(f".{'.'.join(classes)}")
            
            # Data attributes
            data_testid = await element.get_attribute('data-testid')
            if data_testid:
                selectors.append(f"[data-testid='{data_testid}']")
            
            # Name attribute
            name = await element.get_attribute('name')
            if name:
                selectors.append(f"[name='{name}']")
            
            # Text-based selector
            text = await element.text_content()
            if text and len(text.strip()) > 0 and len(text.strip()) < 50:
                selectors.append(f"text={text.strip()}")
            
            # XPath selector
            xpath = await element.evaluate('el => { const getXPath = (element) => { if (element.id) return `//*[@id="${element.id}"]`; if (element === document.body) return "/html/body"; let ix = 0; const siblings = element.parentNode ? element.parentNode.childNodes : []; for (let i = 0; i < siblings.length; i++) { const sibling = siblings[i]; if (sibling === element) return getXPath(element.parentNode) + "/" + element.tagName.toLowerCase() + "[" + (ix + 1) + "]"; if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++; } }; return getXPath(el); }')
            if xpath:
                selectors.append(xpath)
            
            # Return the first valid selector
            for selector in selectors:
                try:
                    test_element = await page.query_selector(selector)
                    if test_element:
                        return selector
                except:
                    continue
            
            # Fallback to tag name
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            return tag_name
            
        except Exception as e:
            logger.error(f"Error generating selector: {e}")
            return "unknown"
    
    def detect_changes(self, current_elements: Dict[str, UIElement]) -> List[UIChange]:
        """Detect changes in tracked elements"""
        changes = []
        current_time = datetime.now().isoformat()
        
        # Check for missing elements
        for element_key, old_element in self.tracked_elements.items():
            if element_key not in current_elements:
                change = UIChange(
                    id=f"change_{hashlib.md5(f'{element_key}_{current_time}'.encode()).hexdigest()[:8]}",
                    timestamp=current_time,
                    change_type=ChangeType.ELEMENT_REMOVED,
                    element_selector=old_element.selector,
                    old_element=old_element,
                    new_element=None,
                    confidence=0.9,
                    description=f"Element {old_element.selector} was removed or selector is invalid",
                    suggested_fix=self.suggest_alternative_selector(old_element),
                    page_url="",
                    screenshot_before=None,
                    screenshot_after=None
                )
                changes.append(change)
        
        # Check for changed elements
        for element_key, new_element in current_elements.items():
            if element_key in self.tracked_elements:
                old_element = self.tracked_elements[element_key]
                change_detected = self.compare_elements(old_element, new_element)
                
                if change_detected:
                    change_type = self.determine_change_type(old_element, new_element)
                    change = UIChange(
                        id=f"change_{hashlib.md5(f'{element_key}_{current_time}'.encode()).hexdigest()[:8]}",
                        timestamp=current_time,
                        change_type=change_type,
                        element_selector=new_element.selector,
                        old_element=old_element,
                        new_element=new_element,
                        confidence=self.calculate_change_confidence(old_element, new_element),
                        description=self.describe_change(old_element, new_element, change_type),
                        suggested_fix=self.suggest_fix(old_element, new_element, change_type),
                        page_url="",
                        screenshot_before=None,
                        screenshot_after=None
                    )
                    changes.append(change)
        
        # Check for new elements
        for element_key, new_element in current_elements.items():
            if element_key not in self.tracked_elements:
                change = UIChange(
                    id=f"change_{hashlib.md5(f'{element_key}_{current_time}'.encode()).hexdigest()[:8]}",
                    timestamp=current_time,
                    change_type=ChangeType.NEW_ELEMENT,
                    element_selector=new_element.selector,
                    old_element=None,
                    new_element=new_element,
                    confidence=0.8,
                    description=f"New element detected: {new_element.selector}",
                    suggested_fix=None,
                    page_url="",
                    screenshot_before=None,
                    screenshot_after=None
                )
                changes.append(change)
        
        return changes
    
    def compare_elements(self, old: UIElement, new: UIElement) -> bool:
        """Compare two UI elements for changes"""
        # Check position changes
        position_threshold = 10  # pixels
        if (abs(old.position['x'] - new.position['x']) > position_threshold or
            abs(old.position['y'] - new.position['y']) > position_threshold):
            return True
        
        # Check text content changes
        if old.text_content != new.text_content:
            return True
        
        # Check attribute changes
        if old.attributes != new.attributes:
            return True
        
        # Check screenshot hash changes
        if old.screenshot_hash and new.screenshot_hash:
            if old.screenshot_hash != new.screenshot_hash:
                return True
        
        return False
    
    def determine_change_type(self, old: UIElement, new: UIElement) -> ChangeType:
        """Determine the type of change between elements"""
        position_threshold = 10
        
        if (abs(old.position['x'] - new.position['x']) > position_threshold or
            abs(old.position['y'] - new.position['y']) > position_threshold):
            return ChangeType.ELEMENT_MOVED
        
        if old.text_content != new.text_content:
            return ChangeType.CONTENT_CHANGE
        
        if old.attributes != new.attributes:
            return ChangeType.STYLE_CHANGE
        
        return ChangeType.LAYOUT_CHANGE
    
    def calculate_change_confidence(self, old: UIElement, new: UIElement) -> float:
        """Calculate confidence score for detected change"""
        confidence = 0.5
        
        # Position change confidence
        position_diff = abs(old.position['x'] - new.position['x']) + abs(old.position['y'] - new.position['y'])
        if position_diff > 50:
            confidence += 0.3
        elif position_diff > 10:
            confidence += 0.2
        
        # Content change confidence
        if old.text_content != new.text_content:
            confidence += 0.2
        
        # Attribute change confidence
        if old.attributes != new.attributes:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def describe_change(self, old: UIElement, new: UIElement, change_type: ChangeType) -> str:
        """Generate description for detected change"""
        if change_type == ChangeType.ELEMENT_MOVED:
            return f"Element moved from ({old.position['x']}, {old.position['y']}) to ({new.position['x']}, {new.position['y']})"
        elif change_type == ChangeType.CONTENT_CHANGE:
            return f"Text content changed from '{old.text_content}' to '{new.text_content}'"
        elif change_type == ChangeType.STYLE_CHANGE:
            return "Element attributes or styling changed"
        else:
            return "Layout or structural change detected"
    
    def suggest_fix(self, old: UIElement, new: UIElement, change_type: ChangeType) -> Optional[str]:
        """Suggest fix for detected change"""
        if change_type == ChangeType.ELEMENT_MOVED:
            return f"Update selector to use more stable positioning or parent-relative selector"
        elif change_type == ChangeType.CONTENT_CHANGE:
            return f"Consider using partial text match or attribute-based selector"
        elif change_type == ChangeType.STYLE_CHANGE:
            return f"Update selector to be less dependent on styling attributes"
        else:
            return "Review and update selector strategy"
    
    def suggest_alternative_selector(self, element: UIElement) -> Optional[str]:
        """Suggest alternative selector for missing element"""
        suggestions = []
        
        # Try parent-based selector
        if element.parent_selector:
            suggestions.append(f"{element.parent_selector} {element.tag_name}")
        
        # Try attribute-based selectors
        for attr, value in element.attributes.items():
            if attr in ['class', 'id', 'name', 'data-testid']:
                suggestions.append(f"[{attr}='{value}']")
        
        # Try text-based selector
        if element.text_content:
            suggestions.append(f"text={element.text_content}")
        
        return " OR ".join(suggestions) if suggestions else None

class SelectorOptimizer:
    """Optimizes and generates robust selectors"""
    
    def __init__(self):
        self.selector_performance: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.selector_stability: Dict[str, float] = defaultdict(float)
        
    async def generate_robust_selectors(self, page: Page, element: ElementHandle) -> List[SelectorCandidate]:
        """Generate multiple robust selector candidates"""
        candidates = []
        
        try:
            # ID-based selector (highest priority)
            element_id = await element.get_attribute('id')
            if element_id and self.is_stable_id(element_id):
                candidates.append(SelectorCandidate(
                    selector=f"#{element_id}",
                    selector_type=SelectorType.CSS,
                    confidence=0.95,
                    stability_score=0.9,
                    uniqueness_score=1.0,
                    description="ID-based selector (most stable)"
                ))
            
            # Data-testid selector
            testid = await element.get_attribute('data-testid')
            if testid:
                candidates.append(SelectorCandidate(
                    selector=f"[data-testid='{testid}']",
                    selector_type=SelectorType.TESTID,
                    confidence=0.9,
                    stability_score=0.85,
                    uniqueness_score=0.95,
                    description="Test ID selector (very stable)"
                ))
            
            # Role-based selector
            role = await element.get_attribute('role')
            if role:
                candidates.append(SelectorCandidate(
                    selector=f"[role='{role}']",
                    selector_type=SelectorType.ROLE,
                    confidence=0.8,
                    stability_score=0.8,
                    uniqueness_score=0.7,
                    description="Role-based selector (semantic)"
                ))
            
            # Name attribute selector
            name = await element.get_attribute('name')
            if name:
                candidates.append(SelectorCandidate(
                    selector=f"[name='{name}']",
                    selector_type=SelectorType.CSS,
                    confidence=0.85,
                    stability_score=0.8,
                    uniqueness_score=0.8,
                    description="Name attribute selector"
                ))
            
            # Class-based selector (with filtering)
            class_name = await element.get_attribute('class')
            if class_name:
                classes = class_name.strip().split()
                stable_classes = [cls for cls in classes if self.is_stable_class(cls)]
                if stable_classes:
                    candidates.append(SelectorCandidate(
                        selector=f".{'.'.join(stable_classes)}",
                        selector_type=SelectorType.CSS,
                        confidence=0.7,
                        stability_score=0.6,
                        uniqueness_score=0.6,
                        description="Stable class-based selector"
                    ))
            
            # Text-based selector
            text = await element.text_content()
            if text and len(text.strip()) > 0 and len(text.strip()) < 50:
                candidates.append(SelectorCandidate(
                    selector=f"text={text.strip()}",
                    selector_type=SelectorType.TEXT,
                    confidence=0.75,
                    stability_score=0.5,
                    uniqueness_score=0.8,
                    description="Text content selector"
                ))
            
            # Partial text selector
            if text and len(text.strip()) > 10:
                partial_text = text.strip()[:20]
                candidates.append(SelectorCandidate(
                    selector=f"text*={partial_text}",
                    selector_type=SelectorType.TEXT,
                    confidence=0.65,
                    stability_score=0.4,
                    uniqueness_score=0.7,
                    description="Partial text selector"
                ))
            
            # Structural selector (parent-child relationship)
            parent = await element.evaluate('el => el.parentElement')
            if parent:
                parent_tag = await element.evaluate('el => el.parentElement.tagName.toLowerCase()')
                tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                candidates.append(SelectorCandidate(
                    selector=f"{parent_tag} > {tag_name}",
                    selector_type=SelectorType.CSS,
                    confidence=0.6,
                    stability_score=0.7,
                    uniqueness_score=0.5,
                    description="Parent-child structural selector"
                ))
            
            # XPath selector
            xpath = await self.generate_xpath(element)
            if xpath:
                candidates.append(SelectorCandidate(
                    selector=xpath,
                    selector_type=SelectorType.XPATH,
                    confidence=0.8,
                    stability_score=0.6,
                    uniqueness_score=0.9,
                    description="XPath selector"
                ))
            
            # Sort candidates by overall score
            for candidate in candidates:
                candidate.confidence = self.calculate_overall_score(candidate)
            
            candidates.sort(key=lambda x: x.confidence, reverse=True)
            
            return candidates[:5]  # Return top 5 candidates
            
        except Exception as e:
            logger.error(f"Error generating robust selectors: {e}")
            return []
    
    def is_stable_id(self, element_id: str) -> bool:
        """Check if ID is likely to be stable"""
        # Avoid dynamically generated IDs
        unstable_patterns = [
            r'\d{10,}',  # Long numbers (timestamps)
            r'[a-f0-9]{8,}',  # Hash-like strings
            r'temp_\w+',  # Temporary IDs
            r'auto_\w+',  # Auto-generated IDs
            r'\w+_\d{6,}'  # IDs with long numbers
        ]
        
        for pattern in unstable_patterns:
            if re.search(pattern, element_id, re.IGNORECASE):
                return False
        
        return True
    
    def is_stable_class(self, class_name: str) -> bool:
        """Check if class name is likely to be stable"""
        # Avoid utility classes and dynamic classes
        unstable_patterns = [
            r'^css-[a-z0-9]+$',  # CSS-in-JS classes
            r'^[a-z]+-[0-9]+$',  # Numbered utility classes
            r'^\w{6,}$',  # Long random strings
            r'active|selected|hover|focus',  # State classes
            r'\d{4,}'  # Long numbers
        ]
        
        for pattern in unstable_patterns:
            if re.search(pattern, class_name, re.IGNORECASE):
                return False
        
        return True
    
    async def generate_xpath(self, element: ElementHandle) -> str:
        """Generate XPath for element"""
        try:
            xpath = await element.evaluate('''
                el => {
                    const getXPath = (element) => {
                        if (element.id) {
                            return `//*[@id="${element.id}"]`;
                        }
                        if (element === document.body) {
                            return "/html/body";
                        }
                        let ix = 0;
                        const siblings = element.parentNode ? element.parentNode.childNodes : [];
                        for (let i = 0; i < siblings.length; i++) {
                            const sibling = siblings[i];
                            if (sibling === element) {
                                return getXPath(element.parentNode) + "/" + element.tagName.toLowerCase() + "[" + (ix + 1) + "]";
                            }
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                                ix++;
                            }
                        }
                    };
                    return getXPath(el);
                }
            ''')
            return xpath
        except:
            return ""
    
    def calculate_overall_score(self, candidate: SelectorCandidate) -> float:
        """Calculate overall score for selector candidate"""
        # Weighted scoring
        weights = {
            'confidence': 0.4,
            'stability': 0.35,
            'uniqueness': 0.25
        }
        
        score = (candidate.confidence * weights['confidence'] +
                candidate.stability_score * weights['stability'] +
                candidate.uniqueness_score * weights['uniqueness'])
        
        return score
    
    def update_selector_performance(self, selector: str, success: bool, response_time: float):
        """Update selector performance metrics"""
        if selector not in self.selector_performance:
            self.selector_performance[selector] = {
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'total_attempts': 0,
                'successful_attempts': 0
            }
        
        metrics = self.selector_performance[selector]
        metrics['total_attempts'] += 1
        
        if success:
            metrics['successful_attempts'] += 1
        
        metrics['success_rate'] = metrics['successful_attempts'] / metrics['total_attempts']
        
        # Update average response time
        current_avg = metrics['avg_response_time']
        total_attempts = metrics['total_attempts']
        metrics['avg_response_time'] = ((current_avg * (total_attempts - 1)) + response_time) / total_attempts

class SessionRecorder:
    """Records session snapshots for replay and debugging"""
    
    def __init__(self, max_snapshots: int = 50):
        self.max_snapshots = max_snapshots
        self.snapshots: deque = deque(maxlen=max_snapshots)
        self.recording = False
        self.current_session_id = None
        
    async def start_recording(self, session_id: str):
        """Start recording session"""
        self.current_session_id = session_id
        self.recording = True
        logger.info(f"Started recording session {session_id}")
    
    def stop_recording(self):
        """Stop recording session"""
        self.recording = False
        logger.info(f"Stopped recording session {self.current_session_id}")
    
    async def capture_snapshot(self, page: Page, action_type: str = "auto", 
                              action_data: Dict[str, Any] = None) -> Optional[SessionSnapshot]:
        """Capture a session snapshot"""
        if not self.recording:
            return None
        
        try:
            timestamp = datetime.now().isoformat()
            
            # Capture page information
            page_url = page.url
            page_title = await page.title()
            
            # Capture DOM structure
            dom_structure = await page.evaluate('() => document.documentElement.outerHTML')
            
            # Capture screenshot
            screenshot = await page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Capture performance metrics
            performance_metrics = await page.evaluate('''
                () => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    return {
                        loadTime: perf ? perf.loadEventEnd - perf.loadEventStart : 0,
                        domContentLoaded: perf ? perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart : 0,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                    };
                }
            ''')
            
            snapshot = SessionSnapshot(
                id=f"snapshot_{self.current_session_id}_{timestamp.replace(':', '-')}",
                timestamp=timestamp,
                page_url=page_url,
                page_title=page_title,
                dom_structure=dom_structure,
                screenshot=screenshot_b64,
                network_requests=[],  # Would be populated by network listener
                user_actions=[{
                    'type': action_type,
                    'timestamp': timestamp,
                    'data': action_data or {}
                }],
                console_logs=[],  # Would be populated by console listener
                performance_metrics=performance_metrics,
                metadata={
                    'session_id': self.current_session_id,
                    'user_agent': await page.evaluate('() => navigator.userAgent'),
                    'viewport': await page.viewport_size()
                }
            )
            
            self.snapshots.append(snapshot)
            logger.debug(f"Captured snapshot {snapshot.id}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
            return None
    
    def get_snapshots(self, limit: int = 10) -> List[SessionSnapshot]:
        """Get recent snapshots"""
        return list(self.snapshots)[-limit:]
    
    async def save_snapshot(self, snapshot: SessionSnapshot, output_dir: Path):
        """Save snapshot to disk"""
        try:
            snapshot_dir = output_dir / "snapshots" / snapshot.id
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Save metadata
            metadata = asdict(snapshot)
            metadata.pop('dom_structure')  # Save separately
            metadata.pop('screenshot')     # Save separately
            
            with open(snapshot_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Save DOM structure
            with open(snapshot_dir / "dom.html", 'w', encoding='utf-8') as f:
                f.write(snapshot.dom_structure)
            
            # Save screenshot
            screenshot_data = base64.b64decode(snapshot.screenshot)
            with open(snapshot_dir / "screenshot.png", 'wb') as f:
                f.write(screenshot_data)
            
            logger.info(f"Snapshot {snapshot.id} saved to {snapshot_dir}")
            
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")

class ContinuousImprovement:
    """Main continuous improvement system"""
    
    def __init__(self, config_path: str = "automation/config/continuous_improvement.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.db_path = Path("logs/continuous_improvement.db")
        
        # Initialize components
        self.element_tracker = ElementTracker()
        self.selector_optimizer = SelectorOptimizer()
        self.session_recorder = SessionRecorder(self.config.get('max_snapshots', 50))
        
        # Initialize database
        self.init_database()
        
        # Tracking state
        self.monitored_selectors: Set[str] = set()
        self.change_history: List[UIChange] = []
        self.auto_fix_enabled = self.config.get('auto_fix_enabled', True)
        
        logger.info("ContinuousImprovement system initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load continuous improvement configuration"""
        default_config = {
            "monitoring": {
                "enabled": True,
                "check_interval": 30,  # seconds
                "confidence_threshold": 0.7,
                "auto_fix_enabled": True,
                "max_snapshots": 50
            },
            "selectors": {
                "critical_selectors": [
                    "#username",
                    "#password",
                    "[data-testid='login-button']",
                    ".trade-button",
                    "[name='amount']",
                    "[name='symbol']"
                ],
                "fallback_strategies": [
                    "id",
                    "data-testid",
                    "name",
                    "class",
                    "text",
                    "xpath"
                ]
            },
            "snapshots": {
                "enabled": True,
                "capture_on_error": True,
                "capture_on_change": True,
                "retention_days": 7,
                "max_size_mb": 100
            },
            "notifications": {
                "enabled": True,
                "channels": ["log", "file"],
                "critical_changes_only": False
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Deep merge with default config
                    self._deep_merge(default_config, config)
                    logger.info(f"Continuous improvement configuration loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading continuous improvement config: {e}, using defaults")
        else:
            # Create default config file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Default continuous improvement configuration created at {self.config_path}")
        
        return default_config
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def init_database(self):
        """Initialize continuous improvement database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ui_changes (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        change_type TEXT NOT NULL,
                        element_selector TEXT NOT NULL,
                        old_element TEXT,
                        new_element TEXT,
                        confidence REAL NOT NULL,
                        description TEXT NOT NULL,
                        suggested_fix TEXT,
                        page_url TEXT NOT NULL,
                        screenshot_before TEXT,
                        screenshot_after TEXT,
                        auto_fixed BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS selector_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        selector TEXT NOT NULL,
                        selector_type TEXT NOT NULL,
                        success_rate REAL NOT NULL,
                        avg_response_time REAL NOT NULL,
                        total_attempts INTEGER NOT NULL,
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_snapshots (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        page_url TEXT NOT NULL,
                        page_title TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Continuous improvement database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing continuous improvement database: {e}")
    
    async def monitor_page(self, page: Page, session_id: str = None) -> List[UIChange]:
        """Monitor page for UI changes"""
        try:
            if session_id:
                await self.session_recorder.start_recording(session_id)
            
            # Capture initial snapshot
            if self.config.get('snapshots', {}).get('enabled', True):
                await self.session_recorder.capture_snapshot(page, "page_load")
            
            # Track critical selectors
            current_elements = {}
            critical_selectors = self.config.get('selectors', {}).get('critical_selectors', [])
            
            for selector in critical_selectors:
                try:
                    element = await self.element_tracker.track_element(page, selector, SelectorType.CSS)
                    if element:
                        element_key = f"{selector}_css"
                        current_elements[element_key] = element
                        self.monitored_selectors.add(selector)
                except Exception as e:
                    logger.warning(f"Could not track selector {selector}: {e}")
            
            # Detect changes
            changes = self.element_tracker.detect_changes(current_elements)
            
            # Process changes
            for change in changes:
                await self.process_change(change, page)
            
            # Store changes in database
            if changes:
                await self.store_changes(changes)
            
            return changes
            
        except Exception as e:
            logger.error(f"Error monitoring page: {e}")
            return []
    
    async def process_change(self, change: UIChange, page: Page):
        """Process detected UI change"""
        try:
            logger.info(f"Processing change: {change.description}")
            
            # Capture screenshots if enabled
            if self.config.get('snapshots', {}).get('capture_on_change', True):
                await self.session_recorder.capture_snapshot(page, "ui_change", {
                    'change_id': change.id,
                    'change_type': change.change_type.value,
                    'selector': change.element_selector
                })
            
            # Attempt auto-fix if enabled
            if (self.auto_fix_enabled and 
                change.change_type in [ChangeType.SELECTOR_INVALID, ChangeType.ELEMENT_REMOVED]):
                
                success = await self.attempt_auto_fix(change, page)
                if success:
                    change.auto_fixed = True
                    logger.info(f"Auto-fixed change {change.id}")
            
            # Add to change history
            self.change_history.append(change)
            
            # Keep only recent changes
            if len(self.change_history) > 100:
                self.change_history = self.change_history[-100:]
            
        except Exception as e:
            logger.error(f"Error processing change {change.id}: {e}")
    
    async def attempt_auto_fix(self, change: UIChange, page: Page) -> bool:
        """Attempt to automatically fix selector issues"""
        try:
            if not change.old_element:
                return False
            
            # Generate alternative selectors
            candidates = await self.selector_optimizer.generate_robust_selectors(page, None)
            
            # Test each candidate
            for candidate in candidates:
                try:
                    element = await page.query_selector(candidate.selector)
                    if element:
                        # Verify it's the same element by comparing attributes
                        if await self.verify_element_match(element, change.old_element):
                            logger.info(f"Found working alternative selector: {candidate.selector}")
                            # Here you would update your selector configuration
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error in auto-fix attempt: {e}")
            return False
    
    async def verify_element_match(self, element: ElementHandle, old_element: UIElement) -> bool:
        """Verify if element matches the old element"""
        try:
            # Compare tag name
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            if tag_name != old_element.tag_name:
                return False
            
            # Compare text content (if available)
            text_content = await element.text_content() or ""
            if old_element.text_content and text_content != old_element.text_content:
                # Allow partial match for dynamic content
                if old_element.text_content not in text_content and text_content not in old_element.text_content:
                    return False
            
            # Compare key attributes
            attributes = await element.evaluate('el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))')
            key_attrs = ['id', 'name', 'data-testid', 'role']
            
            for attr in key_attrs:
                if attr in old_element.attributes and attr in attributes:
                    if old_element.attributes[attr] != attributes[attr]:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying element match: {e}")
            return False
    
    async def store_changes(self, changes: List[UIChange]):
        """Store UI changes in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for change in changes:
                    conn.execute("""
                        INSERT INTO ui_changes (
                            id, timestamp, change_type, element_selector, old_element,
                            new_element, confidence, description, suggested_fix,
                            page_url, screenshot_before, screenshot_after, auto_fixed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        change.id,
                        change.timestamp,
                        change.change_type.value,
                        change.element_selector,
                        json.dumps(asdict(change.old_element)) if change.old_element else None,
                        json.dumps(asdict(change.new_element)) if change.new_element else None,
                        change.confidence,
                        change.description,
                        change.suggested_fix,
                        change.page_url,
                        change.screenshot_before,
                        change.screenshot_after,
                        change.auto_fixed
                    ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing changes: {e}")
    
    def get_recent_changes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent UI changes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM ui_changes 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                changes = []
                for row in cursor.fetchall():
                    changes.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'change_type': row[2],
                        'element_selector': row[3],
                        'confidence': row[5],
                        'description': row[6],
                        'suggested_fix': row[7],
                        'page_url': row[8],
                        'auto_fixed': row[11]
                    })
                
                return changes
                
        except Exception as e:
            logger.error(f"Error getting recent changes: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get continuous improvement system status"""
        return {
            'monitoring_enabled': self.config.get('monitoring', {}).get('enabled', False),
            'auto_fix_enabled': self.auto_fix_enabled,
            'monitored_selectors': len(self.monitored_selectors),
            'recent_changes': len(self.change_history),
            'snapshots_captured': len(self.session_recorder.snapshots),
            'recording_active': self.session_recorder.recording
        }