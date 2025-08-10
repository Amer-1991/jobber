#!/usr/bin/env python3
"""
Test to navigate to Bahar projects page and extract projects.
This will navigate to https://bahr.sa/projects and extract recent projects.
"""

import asyncio
import json
from jobber_fsm.core.skills.search_bahar_projects import search_bahar_projects
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_navigate_and_extract():
    """
    Navigate to Bahar projects page and extract projects.
    """
    print("🚀 Navigating to Bahar projects page and extracting projects...")
    
    try:
        # Get the current browser session
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        print(f"📍 Starting URL: {page.url}")
        
        # Navigate to Bahar projects page
        print("🔄 Navigating to https://bahr.sa/projects...")
        await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)  # Wait for page to load
        
        print(f"📍 Current URL: {page.url}")
        
        # Check if navigation was successful
        if "projects" not in page.url:
            print("❌ Failed to navigate to projects page")
            return
        
        print("✅ Successfully navigated to projects page!")
        
        # Extract projects from the page
        print("🔍 Extracting projects from the page...")
        search_result = await search_bahar_projects(
            search_query="",  # No search query, just extract all recent projects
            max_results=10
        )
        
        # Parse and display results
        result_data = json.loads(search_result)
        
        if "error" in result_data:
            print(f"❌ Extraction failed: {result_data['error']}")
        else:
            projects = result_data.get("projects", [])
            print(f"✅ Found {len(projects)} projects on the page")
            
            if projects:
                print("\n📋 Recent Projects Found:")
                for i, project in enumerate(projects, 1):
                    print(f"\n🎯 Project {i}:")
                    print(f"   📝 Title: {project.get('title', 'N/A')}")
                    print(f"   💰 Budget: {project.get('budget', 'N/A')}")
                    if project.get('description'):
                        desc = project['description'][:120] + "..." if len(project['description']) > 120 else project['description']
                        print(f"   📄 Description: {desc}")
                    if project.get('url'):
                        print(f"   🔗 URL: {project['url']}")
                    if project.get('skills'):
                        print(f"   🛠️ Skills: {', '.join(project['skills'])}")
                    if project.get('deadline'):
                        print(f"   ⏰ Deadline: {project['deadline']}")
            else:
                print("❌ No projects found. The page might be loading or have a different structure.")
                
                # Show page info for debugging
                title = await page.title()
                print(f"📄 Page title: {title}")
                
                # Get some page content for analysis
                from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
                text_content = await get_dom_with_content_type("text_only")
                
                print(f"📄 Page content length: {len(text_content)} characters")
                print("📄 First 300 characters:")
                print(text_content[:300])
        
        await browser_manager.stop_playwright()
        
    except Exception as e:
        print(f"❌ Error during navigation and extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎯 Navigate and Extract Projects Test")
    print("=" * 50)
    print("This will navigate to https://bahr.sa/projects and extract recent projects.")
    
    asyncio.run(test_navigate_and_extract())
    
    print("\n✨ Test completed!") 