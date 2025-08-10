#!/usr/bin/env python3
"""
Test to find the next available project after submitting an offer.
"""

import asyncio
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def find_next_project():
    """
    Find the next available project after submitting an offer.
    """
    print("🔍 Finding Next Available Project...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return
    
    browser_manager = None
    
    try:
        # Step 1: Initialize browser and login
        print("🌐 Step 1: Initializing browser and logging in...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        # Login
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url="https://bahr.sa",
            wait_time=3.0
        )
        
        if "Success" not in login_result:
            print("❌ Login failed, cannot proceed")
            return
        
        print("✅ Login successful!")
        
        # Step 2: Navigate to projects page
        print("🔄 Step 2: Navigating to projects page...")
        
        await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "projects" not in current_url:
            print("❌ Failed to navigate to projects page")
            return
        
        print("✅ Successfully navigated to projects page!")
        
        # Step 3: Find available projects with pagination
        print("🔍 Step 3: Finding available projects...")
        
        # Wait for projects to load
        await asyncio.sleep(5)
        
        page_number = 1
        max_pages = 10  # Limit to avoid infinite loop
        
        while page_number <= max_pages:
            print(f"\n📄 Processing Page {page_number}...")
            
            # Get project links for current page
            project_links = await page.query_selector_all("a[href*='/projects/'], a[href*='/recruitments/']")
            print(f"   📥 Found {len(project_links)} project links on page {page_number}")
            
            if not project_links:
                print(f"   ❌ No projects found on page {page_number}")
                break
            
            # Check each project on this page
            for i, link in enumerate(project_links):
                try:
                    print(f"\n📋 Checking Project {i+1} on page {page_number}...")
                    
                    # Get project URL
                    project_url = await link.get_attribute("href")
                    if project_url and not project_url.startswith("http"):
                        project_url = f"https://bahr.sa{project_url}"
                    
                    print(f"   🔗 URL: {project_url}")
                    
                    # Get project title from the link text
                    title = await link.text_content()
                    title = title.strip() if title else f"Project {i+1}"
                    
                    # Clean up the title (remove extra text)
                    if "منشور في:" in title:
                        title = title.split("منشور في:")[0].strip()
                    if "بالمشروع" in title:
                        title = title.replace("بالمشروع", "").strip()
                    
                    # If title is still empty, try to get it from the page after navigation
                    if not title or title == f"Project {i+1}":
                        # Navigate to get the title
                        await page.goto(project_url, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(2)
                        
                        # Try to get title from the page
                        title_element = await page.query_selector("h1, h2, h3")
                        if title_element:
                            title = await title_element.text_content()
                            title = title.strip() if title else f"Project {i+1}"
                        
                        # Go back to projects list
                        await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(2)
                    
                    print(f"   🎯 Title: {title}")
                    
                    if not project_url:
                        print("   ⚠️ No project URL found, skipping...")
                        continue
                    
                    # Step 5: Navigate to project details
                    print("   🔄 Navigating to project details...")
                    
                    await page.goto(project_url, wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(3)
                    
                    # Step 6: Check project status and if we can submit an offer
                    print("   🔍 Checking project status...")
                    
                    # First check if project is closed
                    project_status = await check_project_status_and_availability(page)
                    
                    if project_status["is_closed"]:
                        print(f"   🚫 Project is CLOSED - stopping search")
                        print(f"   📊 Status: {project_status['status']}")
                        return None  # Stop searching when we find a closed project
                    
                    if project_status["can_submit"]:
                        print(f"   ✅ CAN SUBMIT OFFER!")
                        print(f"   📍 Submit URL: {project_status['submit_url']}")
                        
                        # Get more project details
                        project_details = await extract_project_details(page)
                        
                        print(f"   📊 Project Details:")
                        print(f"      - Category: {project_details.get('category', 'N/A')}")
                        print(f"      - Budget: {project_details.get('budget', 'N/A')}")
                        print(f"      - Deadline: {project_details.get('deadline', 'N/A')}")
                        print(f"      - Status: {project_details.get('status', 'N/A')}")
                        
                        print(f"\n🎯 FOUND NEXT AVAILABLE PROJECT!")
                        print(f"   Title: {title}")
                        print(f"   URL: {project_url}")
                        print(f"   Submit URL: {project_status['submit_url']}")
                        print(f"   Page: {page_number}")
                        
                        return {
                            "title": title,
                            "url": project_url,
                            "submit_url": project_status['submit_url'],
                            "details": project_details,
                            "page_number": page_number
                        }
                    else:
                        print(f"   ❌ Cannot submit offer: {project_status['reason']}")
                    
                    # Go back to projects list
                    print("   🔄 Going back to projects list...")
                    await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"   ❌ Error checking project {i+1}: {str(e)}")
                    continue
            
            # After checking all projects on current page, try to go to next page
            print(f"   📄 Finished page {page_number}, checking for next page...")
            
            # Look for next page button
            next_page_button = await page.query_selector("button[aria-label*='next'], button[aria-label*='التالي'], a[aria-label*='next'], a[aria-label*='التالي']")
            
            if next_page_button:
                # Check if button is disabled
                is_disabled = await next_page_button.get_attribute("disabled")
                if not is_disabled:
                    print(f"   ➡️ Going to next page...")
                    await next_page_button.click()
                    await asyncio.sleep(3)
                    page_number += 1
                else:
                    print(f"   🛑 Next page button is disabled - reached last page")
                    break
            else:
                print(f"   🛑 No next page button found - reached last page")
                break
        
        print(f"\n❌ No available projects found after checking {page_number} pages")
        return None
        
    except Exception as e:
        print(f"❌ Error during project search: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.stop_playwright()
            except:
                pass

async def check_project_status_and_availability(page):
    """
    Check if project is closed and if we can submit an offer.
    """
    try:
        # First check if project is closed
        closed_indicators = [
            "مغلق",  # Closed in Arabic
            "closed",
            "انتهى التقديم",  # Submission ended
            "submission ended",
            "الموعد النهائي انقضى",  # Deadline passed
            "deadline passed"
        ]
        
        # Get page text to check for closed indicators
        from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
        text_content = await get_dom_with_content_type("text_only")
        
        is_closed = any(indicator in text_content for indicator in closed_indicators)
        
        if is_closed:
            return {
                "is_closed": True,
                "can_submit": False,
                "status": "Project is closed",
                "reason": "Project is closed for submissions",
                "submit_url": None
            }
        
        # Check if we can submit an offer
        submit_link = await page.query_selector("a:has-text('تقديم العرض')")
        
        if submit_link:
            link_href = await submit_link.get_attribute("href")
            return {
                "is_closed": False,
                "can_submit": True,
                "status": "Can submit offer",
                "reason": "Submit link available",
                "submit_url": link_href
            }
        else:
            # Check if we already submitted
            my_offer_dropdown = await page.query_selector("button:has-text('عرضي')")
            if my_offer_dropdown:
                return {
                    "is_closed": False,
                    "can_submit": False,
                    "status": "Already submitted",
                    "reason": "Offer already submitted",
                    "submit_url": None
                }
            else:
                return {
                    "is_closed": False,
                    "can_submit": False,
                    "status": "Cannot submit",
                    "reason": "No submit link or offer dropdown found",
                    "submit_url": None
                }
    
    except Exception as e:
        return {
            "is_closed": False,
            "can_submit": False,
            "status": f"Error: {str(e)}",
            "reason": "Error checking project status",
            "submit_url": None
        }

async def extract_project_details(page):
    """
    Extract basic project details from the page.
    """
    try:
        details = {}
        
        # Get category
        category_element = await page.query_selector(".category, [data-testid='category']")
        if category_element:
            details['category'] = await category_element.text_content()
        
        # Get budget
        budget_element = await page.query_selector(".budget, [data-testid='budget']")
        if budget_element:
            details['budget'] = await budget_element.text_content()
        
        # Get deadline
        deadline_element = await page.query_selector(".deadline, [data-testid='deadline']")
        if deadline_element:
            details['deadline'] = await deadline_element.text_content()
        
        # Get status
        status_element = await page.query_selector(".status, [data-testid='status']")
        if status_element:
            details['status'] = await status_element.text_content()
        
        return details
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("🎯 Find Next Available Project")
    print("=" * 50)
    print("This will find the next available project after submitting an offer.")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting project search...")
    result = asyncio.run(find_next_project())
    
    if result:
        print(f"\n✅ Found next project: {result['title']}")
        print(f"   Page: {result['page_number']}")
    else:
        print("\n❌ No available projects found")
    
    print("\n✨ Search completed!") 