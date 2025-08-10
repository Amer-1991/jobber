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
from jobber_fsm.core.skills.enter_text_using_selector import custom_fill_element
from jobber_fsm.utils.logger import logger


async def search_bahar_projects(
    search_query: Annotated[
        str,
        "Search query for projects (e.g., 'web development', 'mobile app', 'data analysis')",
    ] = "",
    min_budget: Annotated[
        Optional[int],
        "Minimum project budget filter",
    ] = None,
    max_budget: Annotated[
        Optional[int],
        "Maximum project budget filter", 
    ] = None,
    category: Annotated[
        Optional[str],
        "Project category filter (e.g., 'Web Development', 'Mobile Development', 'Data Analysis')",
    ] = None,
    sort_by: Annotated[
        str,
        "Sort projects by: 'publishDate_DESC', 'publishDate_ASC', 'budget_DESC', 'budget_ASC'",
    ] = "publishDate_DESC",
    max_results: Annotated[
        int,
        "Maximum number of projects to return",
    ] = 20,
) -> Annotated[str, "JSON string containing list of found projects with their details"]:
    """
    Search for projects on the Bahar platform with optional filters.
    
    This function navigates to the Bahar projects page, applies search filters,
    and extracts project information including title, description, budget, and requirements.
    
    Args:
        search_query: Keywords to search for in projects
        min_budget: Minimum budget filter (optional)
        max_budget: Maximum budget filter (optional)
        category: Project category filter (optional)
        sort_by: How to sort the results
        max_results: Maximum number of projects to return
    
    Returns:
        JSON string containing list of projects with their details
    """
    logger.info(f"Searching for Bahar projects with query: '{search_query}'")
    
    # Get the active browser page (should already be authenticated)
    browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
    page = await browser_manager.get_current_page()
    
    if page is None:
        raise ValueError("No active page found. Please ensure browser is initialized and authenticated.")
    
    # Check if we have access tokens (indicates authenticated session)
    try:
        cookies = await page.context.cookies()
        has_access_token = any(cookie.get("name") == "access_token" for cookie in cookies)
        
        if not has_access_token:
            logger.warning("No access token found in browser session. User may not be authenticated.")
            # Don't fail - just proceed and let user know
        else:
            logger.info("Found access token - using authenticated session")
    except Exception as e:
        logger.warning(f"Could not check authentication status: {str(e)}")
    
    # Log current URL to help with debugging
    current_url = page.url
    logger.info(f"Starting project search from URL: {current_url}")
    
    function_name = inspect.currentframe().f_code.co_name  # type: ignore
    
    try:
        await browser_manager.take_screenshots(f"{function_name}_start", page)
        
        # Step 1: Navigate to Bahar projects page (only if not already there)
        current_url = page.url
        projects_url = "https://bahr.sa/projects"  # Use the direct projects URL
        
        if "projects" not in current_url:
            logger.info(f"Navigating to projects page: {projects_url}")
            try:
                await page.goto(projects_url, wait_until="domcontentloaded", timeout=10000)
                await asyncio.sleep(3)  # Wait for page to load
                logger.info(f"Successfully navigated to: {page.url}")
            except Exception as e:
                logger.warning(f"Navigation to projects page failed: {str(e)}")
                logger.info("Attempting to find projects navigation on current page...")
                
                # Try to find projects link instead of direct navigation
                projects_nav_result = await navigate_to_projects_via_menu(page)
                if not projects_nav_result["success"]:
                    logger.warning("Could not navigate to projects page via menu either")
        else:
            logger.info(f"Already on projects page: {current_url}")
        
        # Step 2: Apply search query if provided
        if search_query:
            search_result = await apply_search_query(page, search_query)
            if not search_result["success"]:
                logger.warning(f"Search query failed: {search_result['message']}")
        
        # Step 3: Apply filters if provided
        if min_budget or max_budget or category:
            filter_result = await apply_project_filters(page, min_budget, max_budget, category)
            if not filter_result["success"]:
                logger.warning(f"Filter application failed: {filter_result['message']}")
        
        # Step 4: Extract project information
        logger.info("Extracting project information from page...")
        projects = await extract_project_details(page, max_results)
        
        await browser_manager.take_screenshots(f"{function_name}_success", page)
        
        # Step 5: Return results as JSON
        result = {
            "search_query": search_query,
            "filters": {
                "min_budget": min_budget,
                "max_budget": max_budget,
                "category": category,
                "sort_by": sort_by
            },
            "total_found": len(projects),
            "projects": projects
        }
        
        logger.info(f"Found {len(projects)} projects")
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Error during project search: {str(e)}")
        traceback.print_exc()
        await browser_manager.take_screenshots(f"{function_name}_error", page)
        return json.dumps({
            "error": f"Project search failed: {str(e)}",
            "search_query": search_query,
            "projects": []
        }, ensure_ascii=False)


async def apply_search_query(page: Page, search_query: str) -> Dict[str, any]:
    """
    Apply search query to the projects page.
    
    Args:
        page: The Playwright page instance
        search_query: The search keywords
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info(f"Applying search query: {search_query}")
        
        # Common search input selectors
        search_selectors = [
            "input[name='search']",
            "input[placeholder*='search']",
            "input[placeholder*='Search']",
            "input[placeholder*='بحث']",  # Arabic for search
            ".search-input",
            "#search",
            "[data-testid='search-input']",
            "input[type='search']"
        ]
        
        search_applied = False
        for selector in search_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Clear existing text and enter search query
                    await element.clear()
                    await custom_fill_element(page, selector, search_query)
                    
                    # Press Enter to search
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)  # Wait for search results
                    
                    logger.info(f"Applied search query using selector: {selector}")
                    search_applied = True
                    break
            except Exception as e:
                logger.debug(f"Failed to search with selector {selector}: {str(e)}")
                continue
        
        if search_applied:
            return {"success": True, "message": f"Search query '{search_query}' applied successfully"}
        else:
            return {"success": False, "message": "Could not find search input field"}
            
    except Exception as e:
        logger.error(f"Error applying search query: {str(e)}")
        return {"success": False, "message": f"Error applying search query: {str(e)}"}


async def apply_project_filters(page: Page, min_budget: Optional[int], max_budget: Optional[int], category: Optional[str]) -> Dict[str, any]:
    """
    Apply filters to the project search results.
    
    Args:
        page: The Playwright page instance
        min_budget: Minimum budget filter
        max_budget: Maximum budget filter
        category: Category filter
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info(f"Applying filters - Budget: {min_budget}-{max_budget}, Category: {category}")
        
        filters_applied = []
        
        # Apply budget filters
        if min_budget:
            min_budget_selectors = [
                "input[name='minBudget']",
                "input[placeholder*='minimum']",
                "input[placeholder*='min']",
                ".min-budget",
                "#minBudget"
            ]
            
            for selector in min_budget_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await custom_fill_element(page, selector, str(min_budget))
                        filters_applied.append(f"min_budget: {min_budget}")
                        break
                except:
                    continue
        
        if max_budget:
            max_budget_selectors = [
                "input[name='maxBudget']",
                "input[placeholder*='maximum']",
                "input[placeholder*='max']",
                ".max-budget",
                "#maxBudget"
            ]
            
            for selector in max_budget_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await custom_fill_element(page, selector, str(max_budget))
                        filters_applied.append(f"max_budget: {max_budget}")
                        break
                except:
                    continue
        
        # Apply category filter
        if category:
            category_selectors = [
                f"option:has-text('{category}')",
                f"[data-value='{category}']",
                f"button:has-text('{category}')",
                ".category-filter",
                "select[name='category']"
            ]
            
            for selector in category_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await click(selector, 1.0)
                        filters_applied.append(f"category: {category}")
                        break
                except:
                    continue
        
        # Apply filters if any were set
        if filters_applied:
            # Look for apply/filter button
            apply_selectors = [
                "button:has-text('Apply')",
                "button:has-text('Filter')",
                "button:has-text('تطبيق')",  # Arabic for Apply
                ".apply-filters",
                ".filter-button",
                "#applyFilters"
            ]
            
            for selector in apply_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await click(selector, 1.0)
                        await asyncio.sleep(2)  # Wait for filter results
                        break
                except:
                    continue
        
        return {
            "success": True,
            "message": f"Applied filters: {', '.join(filters_applied) if filters_applied else 'No filters applied'}"
        }
        
    except Exception as e:
        logger.error(f"Error applying filters: {str(e)}")
        return {"success": False, "message": f"Error applying filters: {str(e)}"}


async def extract_project_details(page: Page, max_results: int) -> List[Dict[str, any]]:
    """
    Extract detailed information about projects from the current page.
    
    Args:
        page: The Playwright page instance
        max_results: Maximum number of projects to extract
        
    Returns:
        List of project dictionaries with details
    """
    try:
        logger.info(f"Extracting project details (max {max_results} projects)")
        
        # Get DOM content to analyze the page structure
        dom_content = await get_dom_with_content_type("all_fields")
        
        projects = []
        
        # Common project card selectors (including Arabic interface)
        project_selectors = [
            ".project-card",
            ".project-item", 
            ".job-card",
            ".listing-item",
            "[data-testid='project-card']",
            ".card",
            ".project",
            # Arabic-specific selectors
            ".مشروع",  # Project in Arabic
            ".project-listing",
            ".project-container",
            ".project-row",
            ".project-grid-item",
            ".project-list-item",
            # Generic content selectors
            "article",
            ".content-item",
            ".listing-item",
            ".item"
        ]
        
        project_elements = []
        for selector in project_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    project_elements = elements[:max_results]  # Limit results
                    logger.info(f"Found {len(elements)} project elements using selector: {selector}")
                    break
            except:
                continue
        
        # If no specific project cards found, try to extract from general content
        if not project_elements:
            logger.info("No specific project cards found, extracting from page content")
            return await extract_projects_from_content(page, max_results)
        
        # Extract details from each project element
        for i, element in enumerate(project_elements):
            if i >= max_results:
                break
                
            try:
                project = await extract_single_project_details(element, page)
                if project:
                    projects.append(project)
                    logger.debug(f"Extracted project {i+1}: {project.get('title', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Failed to extract project {i+1}: {str(e)}")
                continue
        
        return projects
        
    except Exception as e:
        logger.error(f"Error extracting project details: {str(e)}")
        return []


async def navigate_to_projects_via_menu(page: Page) -> Dict[str, any]:
    """
    Try to navigate to projects page using menu/navigation links.
    
    Args:
        page: The Playwright page instance
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info("Attempting to navigate to projects via menu links")
        
        # Common project navigation selectors
        projects_selectors = [
            "a[href*='project']",
            "text=المشاريع",  # Projects in Arabic
            "text=مشاريع",
            "text=Projects", 
            ".projects-link",
            "[data-testid='projects']",
            "nav a:has-text('مشاريع')",
            "nav a:has-text('Projects')",
            ".nav-projects",
            ".menu-projects"
        ]
        
        for selector in projects_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"Found projects link with selector: {selector}")
                    await element.click()
                    await page.wait_for_load_state("networkidle", timeout=5000)
                    await asyncio.sleep(2)
                    
                    # Check if we successfully navigated
                    new_url = page.url
                    if "project" in new_url.lower():
                        logger.info(f"Successfully navigated to projects via menu: {new_url}")
                        return {"success": True, "message": f"Navigated to projects: {new_url}"}
                    
            except Exception as e:
                logger.debug(f"Failed with selector {selector}: {str(e)}")
                continue
        
        return {"success": False, "message": "Could not find projects navigation link"}
        
    except Exception as e:
        logger.error(f"Error navigating via menu: {str(e)}")
        return {"success": False, "message": f"Error navigating via menu: {str(e)}"}


async def extract_single_project_details(element, page: Page) -> Optional[Dict[str, any]]:
    """
    Extract details from a single project element.
    
    Args:
        element: The project element
        page: The Playwright page instance
        
    Returns:
        Dictionary with project details or None if extraction fails
    """
    try:
        project = {}
        
        # Extract title
        title_selectors = [".title", ".project-title", "h1", "h2", "h3", ".heading", "[data-testid='title']"]
        for selector in title_selectors:
            try:
                title_element = await element.query_selector(selector)
                if title_element:
                    project["title"] = await title_element.text_content()
                    break
            except:
                continue
        
        # Extract description
        desc_selectors = [".description", ".project-description", ".summary", ".excerpt", "p"]
        for selector in desc_selectors:
            try:
                desc_element = await element.query_selector(selector)
                if desc_element:
                    description = await desc_element.text_content()
                    if description and len(description.strip()) > 20:  # Valid description
                        project["description"] = description.strip()
                        break
            except:
                continue
        
        # Extract budget
        budget_selectors = [".budget", ".price", ".amount", ".cost", "[data-testid='budget']"]
        for selector in budget_selectors:
            try:
                budget_element = await element.query_selector(selector)
                if budget_element:
                    budget_text = await budget_element.text_content()
                    if budget_text:
                        project["budget"] = budget_text.strip()
                        break
            except:
                continue
        
        # Extract project link
        link_selectors = ["a", "[href]"]
        for selector in link_selectors:
            try:
                link_element = await element.query_selector(selector)
                if link_element:
                    href = await link_element.get_attribute("href")
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith("/"):
                            href = f"https://bahr.sa{href}"
                        project["url"] = href
                        break
            except:
                continue
        
        # Extract deadline/timeframe
        time_selectors = [".deadline", ".timeframe", ".duration", ".time", "[data-testid='deadline']"]
        for selector in time_selectors:
            try:
                time_element = await element.query_selector(selector)
                if time_element:
                    project["deadline"] = await time_element.text_content()
                    break
            except:
                continue
        
        # Extract skills/tags
        skills_selectors = [".skills", ".tags", ".categories", ".requirements"]
        for selector in skills_selectors:
            try:
                skills_elements = await element.query_selector_all(f"{selector} span, {selector} .tag")
                if skills_elements:
                    skills = []
                    for skill_elem in skills_elements:
                        skill_text = await skill_elem.text_content()
                        if skill_text:
                            skills.append(skill_text.strip())
                    if skills:
                        project["skills"] = skills
                        break
            except:
                continue
        
        # Only return project if we have at least a title
        if project.get("title"):
            return project
        else:
            return None
            
    except Exception as e:
        logger.warning(f"Error extracting single project: {str(e)}")
        return None


async def extract_projects_from_content(page: Page, max_results: int) -> List[Dict[str, any]]:
    """
    Fallback method to extract projects from page content when specific selectors fail.
    
    Args:
        page: The Playwright page instance
        max_results: Maximum number of projects to extract
        
    Returns:
        List of project dictionaries
    """
    try:
        logger.info("Using fallback content extraction method")
        
        # Get text content and try to parse project information
        text_content = await get_dom_with_content_type("text_only")
        
        # This is a simplified extraction - in a real implementation,
        # you'd need to analyze the actual page structure
        projects = []
        
        # Try to find project-like patterns in the text (including Arabic)
        lines = text_content.split('\n')
        current_project = {}
        
        # Arabic project keywords
        arabic_keywords = ["مشروع", "عمل", "خدمة", "تطوير", "تصميم", "برمجة"]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip navigation and UI elements
            if any(skip in line.lower() for skip in ["القائمة", "menu", "navigation", "filter", "تصفية", "فرز"]):
                continue
                
            # Simple heuristics to identify project information
            if len(line) > 10 and len(line) < 200 and not current_project.get("title"):
                # Check if line contains project-related keywords
                if any(keyword in line for keyword in arabic_keywords) or "project" in line.lower():
                    current_project["title"] = line
            elif any(currency in line for currency in ["ريال", "SAR", "$", "دولار", "budget", "ميزانية"]):
                current_project["budget"] = line
            elif len(line) > 30 and not current_project.get("description"):
                current_project["description"] = line
            
            # If we have enough info, save the project
            if current_project.get("title") and len(current_project) >= 2:
                projects.append(current_project.copy())
                current_project = {}
                
                if len(projects) >= max_results:
                    break
        
        return projects
        
    except Exception as e:
        logger.error(f"Error in fallback content extraction: {str(e)}")
        return []