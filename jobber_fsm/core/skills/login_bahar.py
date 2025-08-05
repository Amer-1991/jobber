import asyncio
import inspect
import traceback
from typing import Dict, Optional

from playwright.async_api import Page
from typing_extensions import Annotated

from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.enter_text_using_selector import custom_fill_element
from jobber_fsm.core.skills.click_using_selector import click
from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
from jobber_fsm.utils.logger import logger


async def login_bahar(
    username: Annotated[
        str,
        "The username/email for Bahar login",
    ],
    password: Annotated[
        str,
        "The password for Bahar login",
    ],
    bahar_url: Annotated[
        str,
        "The URL of the Bahar website (e.g., https://bahar.com)",
    ],
    wait_time: Annotated[
        float,
        "Wait time in seconds after login attempt to verify success",
    ] = 3.0,
) -> Annotated[str, "Result of the login attempt with status and details"]:
    """
    Performs login to the Bahar website using provided credentials.
    
    This function navigates to the Bahar website, fills in the login form with the provided
    credentials, submits the form, and verifies if the login was successful.
    
    Args:
        username: The username or email address for Bahar login
        password: The password for Bahar login
        bahar_url: The URL of the Bahar website
        wait_time: Time to wait after login attempt to verify success (default: 3.0 seconds)
    
    Returns:
        A detailed message indicating the success or failure of the login attempt
    """
    logger.info(f"Attempting to login to Bahar at {bahar_url}")
    
    # Initialize PlaywrightManager and get the active browser page
    browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
    page = await browser_manager.get_current_page()
    
    if page is None:
        raise ValueError("No active page found. Please open a browser page first.")
    
    function_name = inspect.currentframe().f_code.co_name  # type: ignore
    
    try:
        await browser_manager.take_screenshots(f"{function_name}_start", page)
        
        # Step 1: Navigate to Bahar website
        logger.info(f"Navigating to {bahar_url}")
        await page.goto(bahar_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)  # Wait for page to fully load
        
        # Step 2: Check if already logged in
        is_logged_in = await check_if_logged_in(page)
        if is_logged_in:
            logger.info("Already logged in to Bahar")
            await browser_manager.take_screenshots(f"{function_name}_already_logged_in", page)
            return "Success: Already logged in to Bahar"
        
        # Step 3: Get DOM to identify login elements
        logger.info("Getting DOM to identify login form elements")
        dom_content = await get_dom_with_content_type("all_fields")
        
        # Step 4: Find and fill login form
        login_result = await fill_login_form(page, username, password, dom_content)
        
        # Step 5: Submit login form
        if login_result["success"]:
            submit_result = await submit_login_form(page, dom_content)
            
            # Step 6: Wait and verify login success
            await asyncio.sleep(wait_time)
            final_verification = await verify_login_success(page)
            
            if final_verification["success"]:
                await browser_manager.take_screenshots(f"{function_name}_success", page)
                return f"Success: Successfully logged in to Bahar as {username}"
            else:
                await browser_manager.take_screenshots(f"{function_name}_failed", page)
                return f"Failed: Login verification failed. {final_verification['message']}"
        else:
            await browser_manager.take_screenshots(f"{function_name}_form_fill_failed", page)
            return f"Failed: Could not fill login form. {login_result['message']}"
            
    except Exception as e:
        logger.error(f"Error during Bahar login: {str(e)}")
        traceback.print_exc()
        await browser_manager.take_screenshots(f"{function_name}_error", page)
        return f"Error: Login attempt failed with exception: {str(e)}"


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
            ".user-avatar"
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


async def fill_login_form(page: Page, username: str, password: str, dom_content: str) -> Dict[str, any]:
    """
    Fill the login form with provided credentials.
    
    Args:
        page: The Playwright page instance
        username: The username/email
        password: The password
        dom_content: The DOM content to analyze for form elements
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Common selectors for login form elements
        username_selectors = [
            "input[name='email']",
            "input[name='username']",
            "input[type='email']",
            "input[placeholder*='email']",
            "input[placeholder*='Email']",
            "input[placeholder*='username']",
            "input[placeholder*='Username']",
            "#email",
            "#username",
            "[data-testid='email-input']",
            "[data-testid='username-input']"
        ]
        
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
            "input[placeholder*='password']",
            "input[placeholder*='Password']",
            "#password",
            "[data-testid='password-input']"
        ]
        
        # Try to fill username field
        username_filled = False
        for selector in username_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await custom_fill_element(page, selector, username)
                    logger.info(f"Filled username using selector: {selector}")
                    username_filled = True
                    break
            except Exception as e:
                logger.debug(f"Failed to fill username with selector {selector}: {str(e)}")
                continue
        
        if not username_filled:
            return {
                "success": False,
                "message": "Could not find or fill username field"
            }
        
        # Try to fill password field
        password_filled = False
        for selector in password_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await custom_fill_element(page, selector, password)
                    logger.info(f"Filled password using selector: {selector}")
                    password_filled = True
                    break
            except Exception as e:
                logger.debug(f"Failed to fill password with selector {selector}: {str(e)}")
                continue
        
        if not password_filled:
            return {
                "success": False,
                "message": "Could not find or fill password field"
            }
        
        return {
            "success": True,
            "message": "Successfully filled login form"
        }
        
    except Exception as e:
        logger.error(f"Error filling login form: {str(e)}")
        return {
            "success": False,
            "message": f"Error filling login form: {str(e)}"
        }


async def submit_login_form(page: Page, dom_content: str) -> Dict[str, any]:
    """
    Submit the login form.
    
    Args:
        page: The Playwright page instance
        dom_content: The DOM content to analyze for submit button
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Common selectors for login submit buttons
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:contains('Login')",
            "button:contains('Sign In')",
            "button:contains('Log In')",
            "[data-testid='login-button']",
            "[data-testid='signin-button']",
            ".login-button",
            ".signin-button",
            "#login-button",
            "#signin-button"
        ]
        
        # Try to click submit button
        for selector in submit_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await click(selector, 1.0)
                    logger.info(f"Clicked submit button using selector: {selector}")
                    return {
                        "success": True,
                        "message": f"Successfully clicked submit button: {selector}"
                    }
            except Exception as e:
                logger.debug(f"Failed to click submit with selector {selector}: {str(e)}")
                continue
        
        # If no submit button found, try pressing Enter
        try:
            await page.keyboard.press("Enter")
            logger.info("Pressed Enter to submit form")
            return {
                "success": True,
                "message": "Pressed Enter to submit form"
            }
        except Exception as e:
            logger.warning(f"Failed to press Enter: {str(e)}")
        
        return {
            "success": False,
            "message": "Could not find or click submit button"
        }
        
    except Exception as e:
        logger.error(f"Error submitting login form: {str(e)}")
        return {
            "success": False,
            "message": f"Error submitting login form: {str(e)}"
        }


async def verify_login_success(page: Page) -> Dict[str, any]:
    """
    Verify if the login was successful.
    
    Args:
        page: The Playwright page instance
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Wait a bit for any redirects or page changes
        await asyncio.sleep(2)
        
        # Check for login success indicators
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
            ".welcome-message"
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
        logged_in_urls = ["/dashboard", "/profile", "/account", "/home"]
        for url_part in logged_in_urls:
            if url_part in current_url:
                logger.info(f"URL indicates successful login: {current_url}")
                return {
                    "success": True,
                    "message": f"Login verified by URL: {current_url}"
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


async def logout_bahar() -> Annotated[str, "Result of the logout attempt"]:
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