#!/usr/bin/env python3
"""
Simple test to check if we can access Bahar projects page and extract content.
This assumes the user is already logged in via browser.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.search_bahar_projects import search_bahar_projects
from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_current_page_content():
    """
    Test what's on the current page and try to extract projects.
    """
    print("🧪 Testing Current Page Content...")
    
    try:
        # Initialize browser (assumes already running)
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        print(f"📍 Current URL: {page.url}")
        
        # Check if we're on a projects page
        if "project" in page.url.lower():
            print("✅ Already on a projects page!")
        else:
            print("🔄 Navigating to projects page...")
            try:
                await page.goto("https://bahr.sa/projects", wait_until="networkidle", timeout=10000)
                print(f"📍 New URL: {page.url}")
            except Exception as e:
                print(f"⚠️ Navigation failed: {str(e)}")
                print("🔄 Trying alternative navigation...")
                # Try clicking on projects link instead
                try:
                    # Look for projects link
                    projects_selectors = [
                        "a[href*='project']",
                        "text=مشاريع",  # Projects in Arabic
                        "text=Projects",
                        ".projects-link",
                        "[data-testid='projects']"
                    ]
                    
                    for selector in projects_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                await element.click()
                                await asyncio.sleep(3)
                                print(f"📍 Clicked on projects, new URL: {page.url}")
                                break
                        except:
                            continue
                except Exception as e2:
                    print(f"⚠️ Alternative navigation also failed: {str(e2)}")
        
        # Get page content to analyze
        print("\n🔍 Analyzing page content...")
        dom_content = await get_dom_with_content_type("text_only")
        
        # Show some content
        content_lines = dom_content.split('\n')[:20]  # First 20 lines
        for i, line in enumerate(content_lines, 1):
            if line.strip():
                print(f"   {i:2d}: {line.strip()[:100]}")
        
        print(f"\n📄 Total content length: {len(dom_content)} characters")
        
        # Try to extract projects from current page
        print("\n🎯 Attempting to extract projects from current page...")
        search_result = await search_bahar_projects(
            search_query="",
            max_results=5
        )
        
        result_data = json.loads(search_result)
        
        if "error" in result_data:
            print(f"❌ Project extraction failed: {result_data['error']}")
        else:
            projects = result_data.get("projects", [])
            print(f"✅ Extracted {len(projects)} potential projects")
            
            for i, project in enumerate(projects, 1):
                print(f"\n🎯 Potential Project {i}:")
                print(f"   Title: {project.get('title', 'N/A')}")
                print(f"   Description: {project.get('description', 'N/A')[:100]}...")
                print(f"   Budget: {project.get('budget', 'N/A')}")
                print(f"   URL: {project.get('url', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_manual_navigation():
    """
    Test manual step-by-step navigation to projects.
    """
    print("🧪 Testing Manual Navigation to Projects...")
    
    try:
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        print(f"📍 Starting URL: {page.url}")
        
        # Step 1: Go to main Bahar page
        print("🔄 Step 1: Going to main Bahar page...")
        await page.goto("https://bahr.sa", wait_until="networkidle", timeout=15000)
        print(f"📍 After main page: {page.url}")
        await asyncio.sleep(2)
        
        # Step 2: Look for projects navigation
        print("🔍 Step 2: Looking for projects navigation...")
        dom_content = await get_dom_with_content_type("all_fields")
        
        # Try to click on projects
        projects_clicked = False
        projects_selectors = [
            "text=المشاريع",  # Projects in Arabic
            "text=مشاريع", 
            "text=Projects",
            "a[href*='project']",
            ".projects",
            "[data-testid='projects']",
            "nav a:has-text('مشاريع')",
            "nav a:has-text('Projects')"
        ]
        
        for selector in projects_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"✅ Found projects link with selector: {selector}")
                    await element.click()
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    print(f"📍 After clicking projects: {page.url}")
                    projects_clicked = True
                    break
            except Exception as e:
                print(f"⚠️ Failed with selector {selector}: {str(e)}")
                continue
        
        if not projects_clicked:
            print("❌ Could not find projects navigation link")
            # Try direct URL as fallback
            print("🔄 Trying direct URL navigation...")
            await page.goto("https://bahr.sa/projects", wait_until="networkidle")
        
        # Step 3: Analyze final page
        print("\n🔍 Step 3: Analyzing final page...")
        print(f"📍 Final URL: {page.url}")
        
        # Get page title
        title = await page.title()
        print(f"📄 Page title: {title}")
        
        # Check for project-related content
        text_content = await get_dom_with_content_type("text_only")
        
        # Look for project indicators
        project_keywords = ["مشروع", "project", "عمل", "work", "خدمة", "service"]
        found_keywords = []
        
        for keyword in project_keywords:
            if keyword in text_content.lower():
                count = text_content.lower().count(keyword)
                found_keywords.append(f"{keyword}: {count}")
        
        print(f"🔍 Project keywords found: {', '.join(found_keywords)}")
        
        # Show page structure
        dom_structure = await get_dom_with_content_type("all_fields")
        print(f"📄 Page has {len(dom_structure)} DOM elements")
        
    except Exception as e:
        print(f"❌ Error during manual navigation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎯 Simple Bahar Project Search Test")
    print("=" * 50)
    
    print("Choose test option:")
    print("1. Test current page content")
    print("2. Test manual navigation to projects")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("🔑 Testing current page content...")
        asyncio.run(test_current_page_content())
    elif choice == "2":
        print("🔑 Testing manual navigation...")
        asyncio.run(test_manual_navigation())
    else:
        print("❌ Invalid choice, testing current page...")
        asyncio.run(test_current_page_content())
    
    print("\n✨ Test completed!")