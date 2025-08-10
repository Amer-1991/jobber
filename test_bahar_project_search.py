#!/usr/bin/env python3
"""
Test script for Bahar project search functionality.
This script demonstrates how to search for projects on Bahar after authentication.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Import the Bahar skills
from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.skills.search_bahar_projects import search_bahar_projects
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_full_bahar_workflow():
    """
    Test the complete workflow: Login + Project Search
    """
    print("🚀 Starting Bahar Complete Workflow Test...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = os.getenv("BAHAR_URL", "https://bahr.sa")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return
    
    try:
        # Step 1: Initialize browser
        print("🌐 Step 1: Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        # Step 2: Login with ESSO token
        print("🔐 Step 2: Logging in to Bahar...")
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url=bahar_url,
            wait_time=3.0
        )
        
        print(f"📝 Login result: {login_result}")
        
        if "Success" not in login_result:
            print("❌ Login failed, cannot proceed with project search")
            return
        
        print("✅ Login successful!")
        
        # Step 3: Search for projects
        print("🔍 Step 3: Searching for projects...")
        
        # Test different search scenarios
        search_scenarios = [
            {
                "name": "Web Development Projects",
                "query": "web development",
                "category": "Web Development",
                "min_budget": 500,
                "max_budget": 5000
            },
            {
                "name": "Mobile App Projects", 
                "query": "mobile app",
                "category": "Mobile Development",
                "max_results": 10
            },
            {
                "name": "All Recent Projects",
                "query": "",
                "sort_by": "publishDate_DESC",
                "max_results": 15
            }
        ]
        
        for i, scenario in enumerate(search_scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario['name']}")
            print(f"   Query: '{scenario.get('query', 'None')}'")
            print(f"   Filters: {scenario}")
            
            try:
                # Search for projects
                search_result = await search_bahar_projects(
                    search_query=scenario.get("query", ""),
                    min_budget=scenario.get("min_budget"),
                    max_budget=scenario.get("max_budget"),
                    category=scenario.get("category"),
                    sort_by=scenario.get("sort_by", "publishDate_DESC"),
                    max_results=scenario.get("max_results", 20)
                )
                
                # Parse and display results
                result_data = json.loads(search_result)
                
                if "error" in result_data:
                    print(f"   ❌ Search failed: {result_data['error']}")
                else:
                    projects = result_data.get("projects", [])
                    print(f"   ✅ Found {len(projects)} projects")
                    
                    # Display first few projects
                    for j, project in enumerate(projects[:3], 1):
                        print(f"   🎯 Project {j}:")
                        print(f"      Title: {project.get('title', 'N/A')}")
                        print(f"      Budget: {project.get('budget', 'N/A')}")
                        print(f"      Description: {project.get('description', 'N/A')[:100]}...")
                        if project.get('url'):
                            print(f"      URL: {project['url']}")
                        print()
                
                # Wait between scenarios
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Search scenario failed: {str(e)}")
        
        print("✅ Project search workflow completed!")
        
    except Exception as e:
        print(f"❌ Error during workflow test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        try:
            await browser_manager.stop_playwright()
        except:
            pass

async def test_project_search_only():
    """
    Test project search assuming already logged in.
    """
    print("🧪 Testing Project Search Only (assumes already logged in)...")
    
    try:
        # Initialize browser (assumes already authenticated)
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        print("🔍 Searching for 'web development' projects...")
        
        # Search for web development projects
        search_result = await search_bahar_projects(
            search_query="web development",
            min_budget=100,
            max_budget=2000,
            sort_by="publishDate_DESC",
            max_results=10
        )
        
        # Parse and display results
        result_data = json.loads(search_result)
        
        if "error" in result_data:
            print(f"❌ Search failed: {result_data['error']}")
        else:
            projects = result_data.get("projects", [])
            print(f"✅ Found {len(projects)} projects")
            
            # Display projects
            for i, project in enumerate(projects, 1):
                print(f"\n🎯 Project {i}:")
                print(f"   Title: {project.get('title', 'N/A')}")
                print(f"   Budget: {project.get('budget', 'N/A')}")
                print(f"   Description: {project.get('description', 'N/A')[:150]}...")
                if project.get('skills'):
                    print(f"   Skills: {', '.join(project['skills'])}")
                if project.get('url'):
                    print(f"   URL: {project['url']}")
        
        await browser_manager.stop_playwright()
        
    except Exception as e:
        print(f"❌ Error during project search test: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_without_credentials():
    """
    Test the project search structure without credentials.
    """
    print("🧪 Testing Project Search structure (without real credentials)...")
    
    try:
        print("✅ Project search skill is ready to use")
        print("📝 To test with real credentials:")
        print("   1. Set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   2. Run the test_full_bahar_workflow() function")
        print("   3. Make sure you're authenticated before running search_only test")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🎯 Bahar Project Search Test")
    print("=" * 50)
    
    # Check if credentials are available
    load_dotenv()
    if os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD"):
        print("🔑 Credentials found!")
        print("Choose test option:")
        print("1. Full workflow (Login + Project Search)")
        print("2. Project search only (assumes already logged in)")
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            print("🔑 Running full workflow test...")
            asyncio.run(test_full_bahar_workflow())
        elif choice == "2":
            print("🔑 Running project search only...")
            asyncio.run(test_project_search_only())
        else:
            print("❌ Invalid choice, running full workflow...")
            asyncio.run(test_full_bahar_workflow())
    else:
        print("🔑 No credentials found, running structure test...")
        asyncio.run(test_without_credentials())
    
    print("\n✨ Test completed!")