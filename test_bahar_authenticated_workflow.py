#!/usr/bin/env python3
"""
Test the complete Bahar workflow: Login -> Project Search with maintained session.
This test ensures the project search uses the authenticated session.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Import the Bahar skills
from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.skills.search_bahar_projects import search_bahar_projects
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_authenticated_workflow():
    """
    Test the complete workflow maintaining the same browser session.
    """
    print("🚀 Starting Authenticated Bahar Workflow...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = os.getenv("BAHAR_URL", "https://bahr.sa")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return
    
    browser_manager = None
    
    try:
        # Step 1: Initialize browser (ONCE)
        print("🌐 Step 1: Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        # Step 2: Authenticate using ESSO
        print("🔐 Step 2: Authenticating with ESSO...")
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url=bahar_url,
            wait_time=3.0
        )
        
        print(f"📝 Login result: {login_result}")
        
        if "Success" not in login_result:
            print("❌ Authentication failed, cannot proceed")
            return
            
        print("✅ Authentication successful!")
        
        # Step 3: Get current page info
        page = await browser_manager.get_current_page()
        print(f"📍 Current URL after login: {page.url}")
        
        # Check authentication status
        cookies = await page.context.cookies()
        access_token_found = any(cookie.get("name") == "access_token" for cookie in cookies)
        print(f"🍪 Access token in session: {'✅ Yes' if access_token_found else '❌ No'}")
        
        # Step 4: Search for projects (SAME SESSION)
        print("\n🔍 Step 3: Searching for projects in authenticated session...")
        
        search_scenarios = [
            {
                "name": "Recent Projects",
                "query": "",
                "sort_by": "publishDate_DESC",
                "max_results": 5
            },
            {
                "name": "Web Development", 
                "query": "web development",
                "max_results": 3
            },
            {
                "name": "Mobile Apps",
                "query": "mobile app",
                "max_results": 3
            }
        ]
        
        for i, scenario in enumerate(search_scenarios, 1):
            print(f"\n📋 Search {i}: {scenario['name']}")
            
            try:
                # Use the SAME browser session for search
                search_result = await search_bahar_projects(
                    search_query=scenario.get("query", ""),
                    sort_by=scenario.get("sort_by", "publishDate_DESC"),
                    max_results=scenario.get("max_results", 5)
                )
                
                # Parse results
                result_data = json.loads(search_result)
                
                if "error" in result_data:
                    print(f"   ❌ Search failed: {result_data['error']}")
                else:
                    projects = result_data.get("projects", [])
                    print(f"   ✅ Found {len(projects)} projects")
                    
                    # Show project details
                    for j, project in enumerate(projects[:2], 1):  # Show first 2
                        print(f"   🎯 Project {j}:")
                        print(f"      📝 Title: {project.get('title', 'N/A')}")
                        print(f"      💰 Budget: {project.get('budget', 'N/A')}")
                        if project.get('description'):
                            desc = project['description'][:80] + "..." if len(project['description']) > 80 else project['description']
                            print(f"      📄 Description: {desc}")
                        if project.get('url'):
                            print(f"      🔗 URL: {project['url']}")
                        print()
                
                # Brief pause between searches
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Search failed: {str(e)}")
        
        # Step 5: Show final session status
        print(f"\n📍 Final URL: {page.url}")
        print("✅ Authenticated workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during authenticated workflow: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.stop_playwright()
            except:
                pass

async def test_session_persistence():
    """
    Test to verify that the authenticated session persists between operations.
    """
    print("🧪 Testing Session Persistence...")
    
    load_dotenv()
    bahar_username = os.getenv("BAHAR_USERNAME") 
    bahar_password = os.getenv("BAHAR_PASSWORD")
    
    if not bahar_username or not bahar_password:
        print("❌ Credentials not found")
        return
    
    try:
        # Initialize and authenticate
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        print("🔐 Authenticating...")
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url="https://bahr.sa"
        )
        
        if "Success" in login_result:
            print("✅ Login successful")
            
            # Test multiple searches in same session
            print("\n🔄 Testing multiple searches in same session...")
            
            for i in range(3):
                print(f"\n🔍 Search attempt {i+1}/3")
                
                page = await browser_manager.get_current_page()
                print(f"   📍 Current URL: {page.url}")
                
                # Check cookies
                cookies = await page.context.cookies()
                token_found = any(c.get("name") == "access_token" for c in cookies)
                print(f"   🍪 Token present: {'✅' if token_found else '❌'}")
                
                # Perform search
                search_result = await search_bahar_projects(
                    search_query="",
                    max_results=1
                )
                
                result_data = json.loads(search_result)
                if "error" in result_data:
                    print(f"   ❌ Search {i+1} failed: {result_data['error']}")
                else:
                    projects = result_data.get("projects", [])
                    print(f"   ✅ Search {i+1} found {len(projects)} projects")
                
                await asyncio.sleep(1)
        
        await browser_manager.stop_playwright()
        
    except Exception as e:
        print(f"❌ Session persistence test failed: {str(e)}")

if __name__ == "__main__":
    print("🎯 Bahar Authenticated Workflow Test")
    print("=" * 50)
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("Choose test:")
    print("1. Full authenticated workflow (Login + Multiple Project Searches)")
    print("2. Session persistence test")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("🔑 Running full authenticated workflow...")
        asyncio.run(test_authenticated_workflow())
    elif choice == "2":
        print("🔑 Running session persistence test...")
        asyncio.run(test_session_persistence())
    else:
        print("❌ Invalid choice, running full workflow...")
        asyncio.run(test_authenticated_workflow())
    
    print("\n✨ Test completed!")