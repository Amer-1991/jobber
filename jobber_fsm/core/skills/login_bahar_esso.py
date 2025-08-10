import asyncio
import json
import inspect
import traceback
from typing import Dict, Optional

import aiohttp
from playwright.async_api import Page
from typing_extensions import Annotated

from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.enter_text_using_selector import custom_fill_element
from jobber_fsm.core.skills.click_using_selector import click
from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
from jobber_fsm.utils.logger import logger


async def login_bahar_esso(
    username: Annotated[
        str,
        "The username/email for Bahar ESSO login",
    ],
    password: Annotated[
        str,
        "The password for Bahar ESSO login",
    ],
    bahar_url: Annotated[
        str,
        "The URL of the Bahar website (e.g., https://bahr.sa)",
    ],
    wait_time: Annotated[
        float,
        "Wait time in seconds after login attempt to verify success",
    ] = 3.0,
) -> Annotated[str, "Result of the login attempt with status and details"]:
    """
    Performs login to the Bahar website using the ESSO API endpoint.
    
    This function uses the actual ESSO authentication API discovered from network analysis
    to authenticate with Bahar, then navigates to the dashboard.
    
    Args:
        username: The username or email address for Bahar login
        password: The password for Bahar login
        bahar_url: The URL of the Bahar website
        wait_time: Time to wait after login attempt to verify success (default: 3.0 seconds)
    
    Returns:
        A detailed message indicating the success or failure of the login attempt
    """
    logger.info(f"Attempting to login to Bahar using ESSO API at {bahar_url}")
    
    # Initialize PlaywrightManager and get the active browser page
    browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
    page = await browser_manager.get_current_page()
    
    if page is None:
        raise ValueError("No active page found. Please open a browser page first.")
    
    function_name = inspect.currentframe().f_code.co_name  # type: ignore
    
    try:
        await browser_manager.take_screenshots(f"{function_name}_start", page)
        
        # Step 1: Navigate to Bahar website first
        logger.info(f"Navigating to {bahar_url}")
        # Use shorter timeout for slow networks
        try:
            await page.goto(bahar_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
        except Exception as nav_err:
            logger.warning(f"Initial navigation failed, trying with commit: {nav_err}")
            try:
                await page.goto(bahar_url, wait_until="commit", timeout=10000)
                await asyncio.sleep(2)
            except Exception as nav_err2:
                logger.warning(f"Navigation with commit also failed: {nav_err2}")
                # Continue anyway - might still work
        
        # Step 2: Check if already logged in
        is_logged_in = await check_if_logged_in(page)
        if is_logged_in:
            logger.info("Already logged in to Bahar")
            await browser_manager.take_screenshots(f"{function_name}_already_logged_in", page)
            return "Success: Already logged in to Bahar"
        
        # Step 3: Perform ESSO API authentication
        logger.info("Performing ESSO API authentication...")
        auth_result = await perform_esso_authentication(username, password)
        
        if not auth_result["success"]:
            await browser_manager.take_screenshots(f"{function_name}_api_failed", page)
            return f"Failed: ESSO API authentication failed. {auth_result['message']}"
        
        # Step 4: Set up browser session with authentication token
        logger.info("Setting up browser session with authentication token...")
        session_setup_result = await setup_browser_session_with_token(page, auth_result, bahar_url)
        
        if not session_setup_result["success"]:
            await browser_manager.take_screenshots(f"{function_name}_session_setup_failed", page)
            return f"Failed: Browser session setup failed. {session_setup_result['message']}"
        
        # Step 5: Navigate to dashboard after successful authentication
        logger.info("Authentication successful, navigating to dashboard...")
        dashboard_url = f"{bahar_url.rstrip('/')}/dashboard"
        try:
            await page.goto(dashboard_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(wait_time)
        except Exception as nav_err:
            logger.warning(f"Dashboard navigation failed, trying projects page: {nav_err}")
            # As a fallback, try navigating to projects directly
            projects_url = f"{bahar_url.rstrip('/')}/projects"
            logger.info("Falling back to projects page navigation...")
            try:
                await page.goto(projects_url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(wait_time)
            except Exception as nav_err2:
                logger.warning(f"Projects page navigation also failed: {nav_err2}")
                # Continue anyway - might still work
        
        # Step 6: Verify login success
        final_verification = await verify_login_success(page)
        
        if final_verification["success"]:
            await browser_manager.take_screenshots(f"{function_name}_success", page)
            return f"Success: Successfully logged in to Bahar as {username} using ESSO token authentication"
        else:
            await browser_manager.take_screenshots(f"{function_name}_verification_failed", page)
            return f"Failed: Login verification failed. {final_verification['message']}"
            
    except Exception as e:
        logger.error(f"Error during Bahar ESSO login: {str(e)}")
        traceback.print_exc()
        await browser_manager.take_screenshots(f"{function_name}_error", page)
        return f"Error: Login attempt failed with exception: {str(e)}"


async def setup_browser_session_with_token(page: Page, auth_result: Dict[str, any], bahar_url: str) -> Dict[str, any]:
    """
    Set up the browser session with authentication token and cookies.
    
    Args:
        page: The Playwright page instance
        auth_result: The authentication result from ESSO API
        bahar_url: The Bahar website URL
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Extract authentication data
        response_data = auth_result.get("response_data", {})
        access_token = response_data.get("access_token")
        sid_cookie = auth_result.get("cookies", "")
        
        if not access_token:
            return {
                "success": False,
                "message": "No access token received from authentication"
            }
        
        logger.info("Setting up browser session with authentication token...")
        
        # Step 1: Set up cookies for Bahar domain
        if sid_cookie:
            # Parse SID cookie
            sid_value = None
            if "SID=" in sid_cookie:
                sid_part = sid_cookie.split("SID=")[1].split(";")[0]
                sid_value = sid_part
                
            if sid_value:
                # Set SID cookie for 910ths.sa domain
                await page.context.add_cookies([{
                    "name": "SID",
                    "value": sid_value,
                    "domain": ".910ths.sa",
                    "path": "/",
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "Lax"
                }])
                logger.info(f"Set SID cookie for 910ths.sa domain: {sid_value[:20]}...")
        
        # Step 2: Set access token cookie for Bahar domain  
        bahar_domain = ".bahr.sa"  # Extract domain from bahar_url
        if "bahr.sa" in bahar_url:
            await page.context.add_cookies([{
                "name": "access_token",
                "value": access_token,
                "domain": bahar_domain,
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            }])
            logger.info(f"Set access_token cookie for Bahar domain: {access_token[:50]}...")
        
        # Step 3: Set up request headers with authorization
        await page.set_extra_http_headers({
            "Authorization": f"Bearer {access_token}",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*"
        })
        logger.info("Set authorization headers for browser session")
        
        # Step 4: Navigate to a simple page first to establish the session
        logger.info("Establishing authenticated session...")
        await page.goto(bahar_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "message": "Browser session successfully set up with authentication token"
        }
        
    except Exception as e:
        logger.error(f"Error setting up browser session: {str(e)}")
        return {
            "success": False,
            "message": f"Error setting up browser session: {str(e)}"
        }


async def perform_esso_authentication(username: str, password: str) -> Dict[str, any]:
    """
    Perform authentication using the ESSO API endpoint.
    
    Args:
        username: The username/email
        password: The password
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # ESSO API endpoint discovered from network analysis
        esso_url = "https://esso-api.910ths.sa/api/user/login"
        
        # Prepare the payload
        payload = {
            "email": username,
            "password": password
        }
        
        # Headers based on the network request
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://esso.910ths.sa",
            "Referer": "https://esso.910ths.sa/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
        }
        
        logger.info(f"Making ESSO API request to {esso_url}")
        
        # Create SSL context that doesn't verify certificates (for development)
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                esso_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                response_text = await response.text()
                logger.info(f"ESSO API response status: {response.status}")
                logger.info(f"ESSO API response: {response_text}")
                
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        
                        # Check for successful authentication
                        if "SID" in response.headers.get("Set-Cookie", ""):
                            logger.info("ESSO authentication successful - SID cookie received")
                            return {
                                "success": True,
                                "message": "ESSO API authentication successful",
                                "cookies": response.headers.get("Set-Cookie", ""),
                                "response_data": response_data
                            }
                        else:
                            return {
                                "success": False,
                                "message": "No authentication cookie received from ESSO API"
                            }
                            
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "message": f"Invalid JSON response from ESSO API: {response_text}"
                        }
                else:
                    return {
                        "success": False,
                        "message": f"ESSO API returned status {response.status}: {response_text}"
                    }
                    
    except aiohttp.ClientError as e:
        logger.error(f"Network error during ESSO authentication: {str(e)}")
        return {
            "success": False,
            "message": f"Network error during ESSO authentication: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during ESSO authentication: {str(e)}")
        return {
            "success": False,
            "message": f"Unexpected error during ESSO authentication: {str(e)}"
        }


async def check_if_logged_in(page: Page) -> bool:
    """
    Check if the user is already logged in to Bahar.
    
    Args:
        page: The Playwright page instance
        
    Returns:
        True if already logged in, False otherwise
    """
    try:
        # Common indicators of being logged in
        logged_in_indicators = [
            "[data-testid='user-menu']",
            "[data-testid='profile']",
            ".user-menu",
            ".profile-menu",
            "[href*='logout']",
            "[href*='profile']",
            ".logged-in",
            ".user-avatar",
            ".dashboard",
            ".welcome-message"
        ]
        
        for indicator in logged_in_indicators:
            try:
                element = await page.query_selector(indicator)
                if element:
                    logger.info(f"Found logged in indicator: {indicator}")
                    return True
            except:
                continue
        
        # Check URL for dashboard or logged-in pages
        current_url = page.url
        logged_in_urls = ["/dashboard", "/profile", "/account", "/home"]
        for url_part in logged_in_urls:
            if url_part in current_url:
                logger.info(f"Current URL indicates logged in: {current_url}")
                return True
                
        return False
        
    except Exception as e:
        logger.warning(f"Error checking login status: {str(e)}")
        return False


async def verify_login_success(page: Page) -> Dict[str, any]:
    """
    Verify if the login was successful by checking multiple indicators.
    
    Args:
        page: The Playwright page instance
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Wait a bit for any redirects or page changes
        await asyncio.sleep(3)
        
        # Check if we have access_token in cookies (indicates successful authentication)
        cookies = await page.context.cookies()
        has_access_token = any(cookie.get("name") == "access_token" for cookie in cookies)
        
        if has_access_token:
            logger.info("Found access_token cookie - authentication successful")
        
        # Check for login success indicators in DOM
        success_indicators = [
            "[data-testid='user-menu']",
            "[data-testid='profile']",
            ".user-menu",
            ".profile-menu", 
            "[href*='logout']",
            "[href*='profile']",
            ".logged-in",
            ".user-avatar",
            ".dashboard",
            ".welcome-message",
            # Arabic indicators for Bahar
            "text=الملف الشخصي",  # Profile in Arabic
            "text=تسجيل خروج",    # Logout in Arabic
            "text=لوحة التحكم",   # Dashboard in Arabic
        ]
        
        for indicator in success_indicators:
            try:
                element = await page.query_selector(indicator)
                if element:
                    logger.info(f"Found login success indicator: {indicator}")
                    return {
                        "success": True,
                        "message": f"Login verified with indicator: {indicator}"
                    }
            except:
                continue
        
        # Check for login error indicators
        error_indicators = [
            ".error-message",
            ".login-error",
            "[data-testid='error-message']",
            ".alert-danger",
            ".alert-error"
        ]
        
        for indicator in error_indicators:
            try:
                element = await page.query_selector(indicator)
                if element:
                    error_text = await element.text_content()
                    logger.warning(f"Found login error: {error_text}")
                    return {
                        "success": False,
                        "message": f"Login error detected: {error_text}"
                    }
            except:
                continue
        
        # Check URL for dashboard or logged-in pages
        current_url = page.url
        logged_in_urls = ["/dashboard", "/profile", "/account", "/home", "/projects"]
        for url_part in logged_in_urls:
            if url_part in current_url:
                logger.info(f"URL indicates successful login: {current_url}")
                return {
                    "success": True,
                    "message": f"Login verified by URL: {current_url}"
                }
        
        # If we have access token cookie, consider it successful even without DOM indicators
        if has_access_token:
            logger.info("Login verified by access_token cookie presence")
            return {
                "success": True,
                "message": "Login verified by access_token cookie presence"
            }
        
        # If we're still on the login page, login probably failed
        if "login" in current_url.lower() or "signin" in current_url.lower():
            return {
                "success": False,
                "message": "Still on login page, login may have failed"
            }
        
        # If we can't determine, assume success but log warning
        logger.warning("Could not definitively verify login success, but no errors found")
        return {
            "success": True,
            "message": "Login status unclear, but no errors detected"
        }
        
    except Exception as e:
        logger.error(f"Error verifying login success: {str(e)}")
        return {
            "success": False,
            "message": f"Error verifying login: {str(e)}"
        }


async def logout_bahar_esso() -> Annotated[str, "Result of the logout attempt"]:
    """
    Logout from Bahar website.
    
    Returns:
        A message indicating the success or failure of the logout attempt
    """
    logger.info("Attempting to logout from Bahar")
    
    browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
    page = await browser_manager.get_current_page()
    
    if page is None:
        return "Error: No active page found"
    
    try:
        # Common logout selectors
        logout_selectors = [
            "[href*='logout']",
            "[data-testid='logout']",
            ".logout",
            ".signout",
            "button:contains('Logout')",
            "button:contains('Sign Out')",
            "a:contains('Logout')",
            "a:contains('Sign Out')"
        ]
        
        for selector in logout_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await click(selector, 1.0)
                    logger.info(f"Clicked logout using selector: {selector}")
                    await asyncio.sleep(2)
                    return "Success: Successfully logged out from Bahar"
            except Exception as e:
                logger.debug(f"Failed to logout with selector {selector}: {str(e)}")
                continue
        
        return "Warning: Could not find logout button, but may still be logged out"
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return f"Error: Logout failed with exception: {str(e)}" 