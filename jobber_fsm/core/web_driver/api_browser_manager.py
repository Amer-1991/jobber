import asyncio
import json
import os
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import aiohttp
from dotenv import load_dotenv

from jobber_fsm.utils.logger import logger


class APIBrowserManager:
    """
    API-based browser manager for services like Browserbase.
    
    This manager uses API tokens to control browser sessions remotely,
    providing a more reliable and scalable alternative to local Playwright.
    """
    
    def __init__(
        self,
        api_token: str = None,
        api_base_url: str = "https://api.browserbase.com",
        headless: bool = False,
        screenshots_dir: str = "",
        take_screenshots: bool = False,
    ):
        """
        Initialize the API browser manager.
        
        Args:
            api_token: API token for the browser service
            api_base_url: Base URL for the browser service API
            headless: Whether to run in headless mode
            screenshots_dir: Directory to save screenshots
            take_screenshots: Whether to take screenshots
        """
        load_dotenv()
        
        self.api_token = api_token or os.getenv("BROWSER_API_TOKEN")
        self.api_base_url = api_base_url or os.getenv("BROWSER_API_BASE_URL", "https://api.browserbase.com")
        self.headless = headless
        self.session_id = None
        self.current_page = None
        self.is_initialized = False
        
        # Screenshot settings
        self.take_screenshots = take_screenshots
        self.screenshots_dir = screenshots_dir or "logs/screenshots"
        
        # Session management
        self.session_start_time = None
        self.last_activity = None
        
        # HTTP session
        self.http_session = None
        
        if not self.api_token:
            raise ValueError("API token is required. Set BROWSER_API_TOKEN environment variable or pass it to the constructor.")
    
    async def async_initialize(self, eval_mode: bool = False) -> bool:
        """
        Initialize the API browser session.
        
        Args:
            eval_mode: Whether to run in evaluation mode (not used for API)
            
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing API browser session...")
            
            # Create HTTP session
            self.http_session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Create new browser session
            session_data = {
                "headless": self.headless,
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions",
                json=session_data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    self.session_id = result.get("session_id")
                    self.current_page = result.get("page_id")
                    self.session_start_time = datetime.now()
                    self.last_activity = datetime.now()
                    self.is_initialized = True
                    
                    logger.info(f"API browser session initialized: {self.session_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create API browser session: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error initializing API browser: {str(e)}")
            return False
    
    async def get_current_page(self):
        """
        Get the current page object (compatibility with PlaywrightManager).
        
        Returns:
            APIPage object representing the current page
        """
        if not self.is_initialized:
            raise ValueError("Browser not initialized. Call async_initialize() first.")
        
        return APIPage(self.http_session, self.api_base_url, self.session_id, self.current_page)
    
    async def get_current_url(self) -> Optional[str]:
        """
        Get the current URL.
        
        Returns:
            Current URL or None if not available
        """
        if not self.is_initialized:
            return None
        
        try:
            async with self.http_session.get(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.current_page}/url"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("url")
                return None
        except Exception as e:
            logger.error(f"Error getting current URL: {str(e)}")
            return None
    
    async def take_screenshots(
        self,
        name: str,
        page=None,  # Compatibility parameter
        full_page: bool = True,
        include_timestamp: bool = True,
        load_state: str = "domcontentloaded",
        take_snapshot_timeout: int = 5000,
    ):
        """
        Take a screenshot of the current page.
        
        Args:
            name: Name for the screenshot
            page: Page object (compatibility parameter)
            full_page: Whether to take full page screenshot
            include_timestamp: Whether to include timestamp in filename
            load_state: Load state to wait for
            take_snapshot_timeout: Timeout for screenshot
        """
        if not self.take_screenshots or not self.is_initialized:
            return
        
        try:
            # Create screenshots directory if it doesn't exist
            os.makedirs(self.screenshots_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
            filename = f"{name}_{timestamp}.png" if timestamp else f"{name}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take screenshot via API
            screenshot_data = {
                "full_page": full_page,
                "timeout": take_snapshot_timeout
            }
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.current_page}/screenshot",
                json=screenshot_data
            ) as response:
                if response.status == 200:
                    # Save screenshot
                    with open(filepath, 'wb') as f:
                        f.write(await response.read())
                    logger.info(f"Screenshot saved: {filepath}")
                else:
                    logger.warning(f"Failed to take screenshot: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
    
    async def close(self):
        """
        Close the API browser session.
        """
        if self.is_initialized and self.session_id:
            try:
                async with self.http_session.delete(
                    f"{self.api_base_url}/sessions/{self.session_id}"
                ) as response:
                    if response.status == 200:
                        logger.info("API browser session closed successfully")
                    else:
                        logger.warning(f"Failed to close session: {response.status}")
            except Exception as e:
                logger.error(f"Error closing API browser session: {str(e)}")
        
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
        
        self.is_initialized = False
        self.session_id = None
        self.current_page = None


class APIPage:
    """
    Represents a page in the API browser session.
    Provides compatibility with Playwright Page interface.
    """
    
    def __init__(self, http_session, api_base_url: str, session_id: str, page_id: str):
        self.http_session = http_session
        self.api_base_url = api_base_url
        self.session_id = session_id
        self.page_id = page_id
    
    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000):
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: Wait condition
            timeout: Navigation timeout
        """
        try:
            navigation_data = {
                "url": url,
                "wait_until": wait_until,
                "timeout": timeout
            }
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/goto",
                json=navigation_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Navigated to: {url}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Navigation failed: {response.status} - {error_text}")
                    raise Exception(f"Navigation failed: {error_text}")
                    
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            raise
    
    async def query_selector(self, selector: str):
        """
        Find an element by selector.
        
        Args:
            selector: CSS selector
            
        Returns:
            APIElement object or None
        """
        try:
            query_data = {"selector": selector}
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/query_selector",
                json=query_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("found"):
                        return APIElement(
                            self.http_session,
                            self.api_base_url,
                            self.session_id,
                            self.page_id,
                            result.get("element_id")
                        )
                return None
                
        except Exception as e:
            logger.error(f"Error querying selector {selector}: {str(e)}")
            return None
    
    async def query_selector_all(self, selector: str):
        """
        Find all elements by selector.
        
        Args:
            selector: CSS selector
            
        Returns:
            List of APIElement objects
        """
        try:
            query_data = {"selector": selector}
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/query_selector_all",
                json=query_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    elements = []
                    for element_data in result.get("elements", []):
                        elements.append(APIElement(
                            self.http_session,
                            self.api_base_url,
                            self.session_id,
                            self.page_id,
                            element_data.get("element_id")
                        ))
                    return elements
                return []
                
        except Exception as e:
            logger.error(f"Error querying all selectors {selector}: {str(e)}")
            return []
    
    async def get_dom_content(self, content_type: str = "all_fields"):
        """
        Get DOM content from the page.
        
        Args:
            content_type: Type of content to extract
            
        Returns:
            DOM content as string
        """
        try:
            dom_data = {"content_type": content_type}
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/get_dom",
                json=dom_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("dom_content", "")
                else:
                    logger.error(f"Failed to get DOM content: {response.status}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error getting DOM content: {str(e)}")
            return ""
    
    async def wait_for_load_state(self, state: str = "domcontentloaded"):
        """
        Wait for page load state.
        
        Args:
            state: Load state to wait for
        """
        try:
            wait_data = {"state": state}
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/wait_for_load_state",
                json=wait_data
            ) as response:
                if response.status == 200:
                    logger.info(f"Page loaded: {state}")
                else:
                    logger.warning(f"Wait for load state failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error waiting for load state: {str(e)}")


class APIElement:
    """
    Represents an element in the API browser session.
    Provides compatibility with Playwright ElementHandle interface.
    """
    
    def __init__(self, http_session, api_base_url: str, session_id: str, page_id: str, element_id: str):
        self.http_session = http_session
        self.api_base_url = api_base_url
        self.session_id = session_id
        self.page_id = page_id
        self.element_id = element_id
    
    async def click(self, timeout: int = 30000):
        """
        Click the element.
        
        Args:
            timeout: Click timeout
        """
        try:
            click_data = {"timeout": timeout}
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/elements/{self.element_id}/click",
                json=click_data
            ) as response:
                if response.status == 200:
                    logger.info("Element clicked successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Click failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error clicking element: {str(e)}")
            return False
    
    async def fill(self, value: str, timeout: int = 30000):
        """
        Fill the element with text.
        
        Args:
            value: Text to fill
            timeout: Fill timeout
        """
        try:
            fill_data = {"value": value, "timeout": timeout}
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/elements/{self.element_id}/fill",
                json=fill_data
            ) as response:
                if response.status == 200:
                    logger.info(f"Element filled with: {value}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Fill failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error filling element: {str(e)}")
            return False
    
    async def get_attribute(self, name: str):
        """
        Get element attribute.
        
        Args:
            name: Attribute name
            
        Returns:
            Attribute value or None
        """
        try:
            attr_data = {"attribute": name}
            
            async with self.http_session.post(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/elements/{self.element_id}/get_attribute",
                json=attr_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("value")
                return None
                
        except Exception as e:
            logger.error(f"Error getting attribute {name}: {str(e)}")
            return None
    
    async def text_content(self):
        """
        Get element text content.
        
        Returns:
            Text content or None
        """
        try:
            async with self.http_session.get(
                f"{self.api_base_url}/sessions/{self.session_id}/pages/{self.page_id}/elements/{self.element_id}/text"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("text")
                return None
                
        except Exception as e:
            logger.error(f"Error getting text content: {str(e)}")
            return None 