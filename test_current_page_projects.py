#!/usr/bin/env python3
"""
Test to extract projects from the current Bahar projects page.
This assumes you're already on https://bahr.sa/projects
"""

import asyncio
import json
from jobber_fsm.core.skills.search_bahar_projects import search_bahar_projects
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_current_page_extraction():
    """
    Extract projects from the current page without navigation.
    """
    print("🔍 Extracting projects from current Bahar projects page...")
    
    try:
        # Get the current browser session
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        print(f"📍 Current URL: {page.url}")
        
        # Check if we're on the projects page
        if "projects" not in page.url:
            print("⚠️ Not on projects page. Please navigate to https://bahr.sa/projects first.")
            return
        
        print("✅ On projects page, extracting projects...")
        
        # Extract projects from current page
        search_result = await search_bahar_projects(
            search_query="",  # No search query, just extract all
            max_results=10
        )
        
        # Parse and display results
        result_data = json.loads(search_result)
        
        if "error" in result_data:
            print(f"❌ Extraction failed: {result_data['error']}")
        else:
            projects = result_data.get("projects", [])
            print(f"✅ Found {len(projects)} projects on current page")
            
            if projects:
                print("\n📋 Projects found:")
                for i, project in enumerate(projects, 1):
                    print(f"\n🎯 Project {i}:")
                    print(f"   📝 Title: {project.get('title', 'N/A')}")
                    print(f"   💰 Budget: {project.get('budget', 'N/A')}")
                    if project.get('description'):
                        desc = project['description'][:100] + "..." if len(project['description']) > 100 else project['description']
                        print(f"   📄 Description: {desc}")
                    if project.get('url'):
                        print(f"   🔗 URL: {project['url']}")
                    if project.get('skills'):
                        print(f"   🛠️ Skills: {', '.join(project['skills'])}")
            else:
                print("❌ No projects found. The page might be loading or have a different structure.")
                
                # Show page info for debugging
                title = await page.title()
                print(f"📄 Page title: {title}")
                
                # Get some page content for analysis
                from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
                text_content = await get_dom_with_content_type("text_only")
                
                print(f"📄 Page content length: {len(text_content)} characters")
                print("📄 First 500 characters:")
                print(text_content[:500])
        
        await browser_manager.stop_playwright()
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎯 Current Page Project Extraction Test")
    print("=" * 50)
    print("Make sure you're on https://bahr.sa/projects before running this test.")
    
    asyncio.run(test_current_page_extraction())
    
    print("\n✨ Test completed!") 