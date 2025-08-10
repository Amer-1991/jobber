#!/usr/bin/env python3
"""
Test to find the correct selectors for project cards on the projects page.
"""

import asyncio
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def find_project_selectors():
    """
    Find the correct selectors for project cards on the projects page.
    """
    print("🔍 Finding Project Card Selectors...")
    
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
        await asyncio.sleep(5)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "projects" not in current_url:
            print("❌ Failed to navigate to projects page")
            return
        
        print("✅ Successfully navigated to projects page!")
        
        # Step 3: Try different selectors
        print("🔍 Step 3: Trying different selectors...")
        
        selectors_to_try = [
            "[data-testid='project-card']",
            ".project-card",
            ".project-listing",
            ".مشروع",
            "article",
            "[role='article']",
            ".card",
            ".project",
            "div[class*='project']",
            "div[class*='card']",
            "a[href*='/projects/']",
            "a[href*='/recruitments/']"
        ]
        
        for selector in selectors_to_try:
            elements = await page.query_selector_all(selector)
            print(f"   Selector '{selector}': {len(elements)} elements found")
            
            if len(elements) > 0:
                print(f"   ✅ Found {len(elements)} elements with selector '{selector}'")
                
                # Try to get some info from the first element
                if len(elements) > 0:
                    first_element = elements[0]
                    try:
                        # Get text content
                        text = await first_element.text_content()
                        if text:
                            print(f"   📝 First element text (first 100 chars): {text[:100]}...")
                        
                        # Get tag name
                        tag_name = await first_element.evaluate("el => el.tagName.toLowerCase()")
                        print(f"   🏷️ Tag name: {tag_name}")
                        
                        # Get class
                        class_name = await first_element.get_attribute("class")
                        if class_name:
                            print(f"   🎨 Class: {class_name}")
                        
                        # Get href if it's a link
                        href = await first_element.get_attribute("href")
                        if href:
                            print(f"   🔗 Href: {href}")
                        
                    except Exception as e:
                        print(f"   ❌ Error getting element info: {str(e)}")
        
        # Step 4: Look for any clickable elements that might be project links
        print("\n🔍 Step 4: Looking for project links...")
        
        # Find all links
        all_links = await page.query_selector_all("a")
        project_links = []
        
        for link in all_links:
            try:
                href = await link.get_attribute("href")
                if href and ("/projects/" in href or "/recruitments/" in href):
                    text = await link.text_content()
                    project_links.append({
                        "href": href,
                        "text": text[:50] if text else "No text"
                    })
            except:
                pass
        
        print(f"   Found {len(project_links)} project links:")
        for i, link in enumerate(project_links[:5]):  # Show first 5
            print(f"      {i+1}. {link['text']} -> {link['href']}")
        
        # Step 5: Get page text to understand structure
        print("\n🔍 Step 5: Analyzing page structure...")
        
        from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
        text_content = await get_dom_with_content_type("text_only")
        
        # Look for project-related text
        lines = text_content.split('\n')
        project_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and any(keyword in line.lower() for keyword in ["project", "مشروع", "tracking", "marketing", "design"]):
                project_lines.append(line)
        
        print(f"   Found {len(project_lines)} potential project lines:")
        for i, line in enumerate(project_lines[:5]):  # Show first 5
            print(f"      {i+1}. {line}")
        
        # Step 6: Save page HTML for analysis
        print("\n💾 Step 6: Saving page HTML for analysis...")
        
        html_content = await page.content()
        with open("projects_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("✅ Page HTML saved to: projects_page.html")
        
        print("\n✅ Selector analysis completed!")
        
    except Exception as e:
        print(f"❌ Error during selector analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.stop_playwright()
            except:
                pass

if __name__ == "__main__":
    print("🎯 Find Project Card Selectors")
    print("=" * 50)
    print("This will find the correct selectors for project cards on the projects page.")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting selector analysis...")
    asyncio.run(find_project_selectors())
    
    print("\n✨ Analysis completed!") 