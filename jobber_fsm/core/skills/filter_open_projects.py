import asyncio
import inspect
import json
import traceback
from typing import Dict, List, Optional

from playwright.async_api import Page
from typing_extensions import Annotated

from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
from jobber_fsm.core.skills.click_using_selector import click
from jobber_fsm.utils.logger import logger


async def filter_open_projects(
    max_projects: Annotated[
        int,
        "Maximum number of open projects to process",
    ] = 10,
    scroll_to_last_open: Annotated[
        bool,
        "Whether to scroll to the last open project and stop at closed ones",
    ] = True,
) -> Annotated[str, "JSON string containing filtered open projects"]:
    """
    Filter projects to show only open ones and scroll to the last open project.
    
    This function:
    1. Identifies project status indicators (open/closed)
    2. Filters to show only open projects
    3. Scrolls through projects until it finds the last open one
    4. Stops when it encounters closed projects
    
    Args:
        max_projects: Maximum number of open projects to process
        scroll_to_last_open: Whether to scroll to last open project
    
    Returns:
        JSON string with filtered open projects
    """
    logger.info(f"Filtering open projects (max: {max_projects}, scroll_to_last: {scroll_to_last_open})")
    
    # Get the active browser page (should already be authenticated)
    browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
    page = await browser_manager.get_current_page()
    
    if page is None:
        raise ValueError("No active page found. Please ensure browser is initialized and authenticated.")
    
    function_name = inspect.currentframe().f_code.co_name  # type: ignore
    
    try:
        await browser_manager.take_screenshots(f"{function_name}_start", page)
        
        # Step 1: Apply status filter to show only open projects
        logger.info("Applying status filter to show only open projects")
        filter_result = await apply_status_filter(page)
        
        if not filter_result["success"]:
            logger.warning(f"Status filter failed: {filter_result['message']}")
        
        # Step 2: Scroll and collect open projects
        logger.info("Scrolling through projects to find open ones")
        open_projects = await scroll_and_collect_open_projects(page, max_projects, scroll_to_last_open)
        
        # Step 3: Return results
        result = {
            "total_open_found": len(open_projects),
            "max_projects_requested": max_projects,
            "scroll_to_last_open": scroll_to_last_open,
            "filter_applied": filter_result["success"],
            "open_projects": open_projects
        }
        
        await browser_manager.take_screenshots(f"{function_name}_success", page)
        logger.info(f"Found {len(open_projects)} open projects")
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Error filtering open projects: {str(e)}")
        traceback.print_exc()
        await browser_manager.take_screenshots(f"{function_name}_error", page)
        return json.dumps({
            "error": f"Failed to filter open projects: {str(e)}",
            "open_projects": []
        }, ensure_ascii=False)


async def apply_status_filter(page: Page) -> Dict[str, any]:
    """
    Apply status filter to show only open projects.
    
    Args:
        page: The Playwright page instance
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info("Looking for status filter options")
        
        # Common selectors for status filters
        status_filter_selectors = [
            "select[name='status']", "select[name='state']",
            ".status-filter", ".state-filter", ".project-status-filter",
            "[data-testid='status-filter']", ".filter-status",
            "button:contains('Status')", "button:contains('حالة')",  # Arabic
            ".filter-dropdown", ".filter-select"
        ]
        
        # Common selectors for "Open" status option
        open_status_selectors = [
            "option[value='open']", "option[value='active']",
            "option:contains('Open')", "option:contains('Active')",
            "option:contains('مفتوح')", "option:contains('نشط')",  # Arabic
            "button:contains('Open')", "button:contains('Active')",
            ".status-open", ".status-active"
        ]
        
        # Try to find and apply status filter
        for filter_selector in status_filter_selectors:
            try:
                filter_element = await page.query_selector(filter_selector)
                if filter_element:
                    logger.info(f"Found status filter: {filter_selector}")
                    
                    # Click on the filter to open options
                    await click(filter_selector, 1.0)
                    await asyncio.sleep(1)
                    
                    # Try to select "Open" status
                    for open_selector in open_status_selectors:
                        try:
                            open_element = await page.query_selector(open_selector)
                            if open_element:
                                await click(open_selector, 1.0)
                                await asyncio.sleep(2)  # Wait for filter to apply
                                
                                logger.info(f"Applied 'Open' status filter using: {open_selector}")
                                return {"success": True, "message": f"Applied open status filter: {open_selector}"}
                        except:
                            continue
                    
                    # If no specific "Open" option found, try clicking the first option
                    try:
                        first_option = await page.query_selector(f"{filter_selector} option:first-child")
                        if first_option:
                            await click(f"{filter_selector} option:first-child", 1.0)
                            await asyncio.sleep(2)
                            return {"success": True, "message": "Applied first status filter option"}
                    except:
                        pass
                    
                    break
            except:
                continue
        
        # If no filter found, try to find any filter buttons
        filter_button_selectors = [
            "button:contains('Filter')", "button:contains('تصفية')",  # Arabic
            ".filter-button", "[data-testid='filter']", ".filter-btn"
        ]
        
        for button_selector in filter_button_selectors:
            try:
                button = await page.query_selector(button_selector)
                if button:
                    await click(button_selector, 1.0)
                    await asyncio.sleep(1)
                    
                    # Look for open status in the opened filter panel
                    for open_selector in open_status_selectors:
                        try:
                            open_element = await page.query_selector(open_selector)
                            if open_element:
                                await click(open_selector, 1.0)
                                await asyncio.sleep(2)
                                return {"success": True, "message": f"Applied open filter via button: {button_selector}"}
                        except:
                            continue
            except:
                continue
        
        return {"success": False, "message": "Could not find or apply status filter"}
        
    except Exception as e:
        logger.error(f"Error applying status filter: {str(e)}")
        return {"success": False, "message": f"Error applying status filter: {str(e)}"}


async def scroll_and_collect_open_projects(page: Page, max_projects: int, scroll_to_last_open: bool) -> List[Dict[str, any]]:
    """
    Scroll through projects and collect open ones, stopping at closed projects.
    
    Args:
        page: The Playwright page instance
        max_projects: Maximum number of projects to collect
        scroll_to_last_open: Whether to scroll to last open project
    
    Returns:
        List of open project dictionaries
    """
    try:
        open_projects = []
        last_open_project = None
        consecutive_closed_count = 0
        max_consecutive_closed = 3  # Stop after 3 consecutive closed projects
        
        # Common selectors for project containers
        project_selectors = [
            ".project-card", ".project-item", ".job-card", ".listing-item",
            "[data-testid='project-card']", ".card", ".project",
            ".project-listing", ".project-container", ".project-row",
            ".project-grid-item", ".project-list-item", "article",
            ".content-item", ".listing-item", ".item"
        ]
        
        # Common selectors for status indicators
        status_selectors = [
            ".status", ".project-status", ".job-status", ".state",
            "[data-testid='status']", ".status-indicator", ".status-badge",
            ".project-state", ".job-state", ".listing-status"
        ]
        
        # Keywords indicating closed status
        closed_keywords = [
            "closed", "مغلق", "مكتمل", "منتهي", "مقفل",  # Arabic
            "completed", "finished", "ended", "terminated",
            "expired", "cancelled", "canceled", "inactive"
        ]
        
        # Keywords indicating open status
        open_keywords = [
            "open", "مفتوح", "نشط", "متاح", "مفتوح",  # Arabic
            "active", "available", "ongoing", "live",
            "accepting", "bidding", "open for bids"
        ]
        
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while len(open_projects) < max_projects and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            
            # Get current projects on page
            current_projects = []
            for selector in project_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        current_projects = elements
                        break
                except:
                    continue
            
            if not current_projects:
                logger.info("No project elements found on current page")
                break
            
            # Process each project on current page
            for project_element in current_projects:
                if len(open_projects) >= max_projects:
                    break
                
                try:
                    # Check project status
                    project_status = await check_project_status(project_element, status_selectors, closed_keywords, open_keywords)
                    
                    if project_status["is_open"]:
                        # Extract project details
                        project_details = await extract_project_basic_info(project_element)
                        if project_details:
                            project_details["status"] = "open"
                            open_projects.append(project_details)
                            last_open_project = project_details
                            consecutive_closed_count = 0
                            logger.debug(f"Found open project: {project_details.get('title', 'Unknown')}")
                    
                    elif project_status["is_closed"]:
                        consecutive_closed_count += 1
                        logger.debug(f"Found closed project: {project_status.get('status_text', 'Unknown')}")
                        
                        # If we're supposed to stop at closed projects and we've found several consecutive closed ones
                        if scroll_to_last_open and consecutive_closed_count >= max_consecutive_closed:
                            logger.info(f"Stopping at closed projects (found {consecutive_closed_count} consecutive closed)")
                            return open_projects
                    
                except Exception as e:
                    logger.debug(f"Error processing project element: {str(e)}")
                    continue
            
            # Scroll down to load more projects
            if len(open_projects) < max_projects:
                scroll_result = await scroll_page_down(page)
                if not scroll_result["success"]:
                    logger.info("Could not scroll further, reached end of page")
                    break
                
                await asyncio.sleep(2)  # Wait for new content to load
        
        logger.info(f"Finished scrolling. Found {len(open_projects)} open projects")
        return open_projects
        
    except Exception as e:
        logger.error(f"Error scrolling and collecting projects: {str(e)}")
        return []


async def check_project_status(project_element, status_selectors: List[str], closed_keywords: List[str], open_keywords: List[str]) -> Dict[str, any]:
    """
    Check if a project is open or closed based on status indicators.
    
    Args:
        project_element: The project element to check
        status_selectors: Selectors for status indicators
        closed_keywords: Keywords indicating closed status
        open_keywords: Keywords indicating open status
        
    Returns:
        Dictionary with status information
    """
    try:
        status_text = ""
        
        # Look for status indicators within the project element
        for selector in status_selectors:
            try:
                status_element = await project_element.query_selector(selector)
                if status_element:
                    status_text = await status_element.text_content()
                    if status_text:
                        status_text = status_text.strip().lower()
                        break
            except:
                continue
        
        # If no explicit status found, check the entire project text
        if not status_text:
            try:
                full_text = await project_element.text_content()
                if full_text:
                    status_text = full_text.lower()
            except:
                pass
        
        # Determine status based on keywords
        is_closed = any(keyword in status_text for keyword in closed_keywords)
        is_open = any(keyword in status_text for keyword in open_keywords)
        
        # If no explicit status found, assume open (default behavior)
        if not is_closed and not is_open:
            is_open = True
        
        return {
            "is_open": is_open,
            "is_closed": is_closed,
            "status_text": status_text
        }
        
    except Exception as e:
        logger.debug(f"Error checking project status: {str(e)}")
        return {"is_open": True, "is_closed": False, "status_text": ""}


async def extract_project_basic_info(project_element) -> Optional[Dict[str, any]]:
    """
    Extract basic information from a project element.
    
    Args:
        project_element: The project element
        
    Returns:
        Dictionary with basic project information or None
    """
    try:
        project_info = {}
        
        # Extract title
        title_selectors = [".title", ".project-title", "h1", "h2", "h3", ".heading", "[data-testid='title']"]
        for selector in title_selectors:
            try:
                title_element = await project_element.query_selector(selector)
                if title_element:
                    project_info["title"] = await title_element.text_content()
                    break
            except:
                continue
        
        # Extract budget
        budget_selectors = [".budget", ".price", ".amount", ".cost", "[data-testid='budget']"]
        for selector in budget_selectors:
            try:
                budget_element = await project_element.query_selector(selector)
                if budget_element:
                    project_info["budget"] = await budget_element.text_content()
                    break
            except:
                continue
        
        # Extract project link
        link_selectors = ["a", "[href]"]
        for selector in link_selectors:
            try:
                link_element = await project_element.query_selector(selector)
                if link_element:
                    href = await link_element.get_attribute("href")
                    if href:
                        if href.startswith("/"):
                            href = f"https://bahr.sa{href}"
                        project_info["url"] = href
                        break
            except:
                continue
        
        # Only return if we have at least a title
        if project_info.get("title"):
            return project_info
        else:
            return None
            
    except Exception as e:
        logger.debug(f"Error extracting project info: {str(e)}")
        return None


async def scroll_page_down(page: Page) -> Dict[str, any]:
    """
    Scroll the page down to load more content.
    
    Args:
        page: The Playwright page instance
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Get current scroll position
        current_position = await page.evaluate("window.pageYOffset")
        
        # Scroll down
        await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(1)
        
        # Check if we actually scrolled
        new_position = await page.evaluate("window.pageYOffset")
        
        if new_position > current_position:
            return {"success": True, "message": f"Scrolled from {current_position} to {new_position}"}
        else:
            return {"success": False, "message": "Could not scroll further"}
        
    except Exception as e:
        logger.error(f"Error scrolling page: {str(e)}")
        return {"success": False, "message": f"Error scrolling: {str(e)}"} 