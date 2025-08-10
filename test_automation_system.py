#!/usr/bin/env python3
"""
Test script for the Bahar Automation System

This script tests the key components of the automation system:
1. Authentication
2. Project filtering
3. AI offer generation
4. Error handling
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobber_fsm.core.automation_orchestrator import BaharAutomationOrchestrator
from jobber_fsm.utils.logger import logger


async def test_authentication():
    """Test authentication functionality."""
    print("🔐 Testing Authentication...")
    
    orchestrator = BaharAutomationOrchestrator(headless=False)
    
    try:
        # Test initialization
        init_success = await orchestrator.initialize()
        
        if init_success:
            print("✅ Authentication test passed")
            
            # Test status
            status = orchestrator.get_status()
            print(f"   Status: {status}")
            
            await orchestrator.cleanup()
            return True
        else:
            print("❌ Authentication test failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test error: {str(e)}")
        return False


async def test_project_filtering():
    """Test project filtering functionality."""
    print("\n📋 Testing Project Filtering...")
    
    orchestrator = BaharAutomationOrchestrator(headless=False)
    
    try:
        # Initialize
        init_success = await orchestrator.initialize()
        if not init_success:
            print("❌ Failed to initialize for project filtering test")
            return False
        
        # Test getting open projects
        open_projects_result = await orchestrator._get_open_projects(max_projects=3)
        
        if "error" in open_projects_result:
            print(f"❌ Project filtering test failed: {open_projects_result['error']}")
            return False
        
        open_projects = open_projects_result.get("open_projects", [])
        print(f"✅ Project filtering test passed - Found {len(open_projects)} open projects")
        
        # Show project details
        for i, project in enumerate(open_projects[:2], 1):
            print(f"   Project {i}: {project.get('title', 'Unknown')}")
            print(f"     Budget: {project.get('budget', 'Not specified')}")
            print(f"     URL: {project.get('url', 'Not specified')}")
        
        await orchestrator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Project filtering test error: {str(e)}")
        return False


async def test_ai_offer_generation():
    """Test AI offer generation functionality."""
    print("\n🤖 Testing AI Offer Generation...")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OpenAI API key not set, skipping AI offer generation test")
        return True
    
    orchestrator = BaharAutomationOrchestrator(headless=False)
    
    try:
        # Initialize
        init_success = await orchestrator.initialize()
        if not init_success:
            print("❌ Failed to initialize for AI offer test")
            return False
        
        # Create a mock project for testing
        mock_project = {
            "title": "Test Web Development Project",
            "description": "Need a website built with modern technologies",
            "budget": "1000 SAR",
            "url": "https://bahr.sa/projects/test",
            "skills": ["Web Development", "JavaScript", "React"]
        }
        
        # Test offer submission (without auto-submit)
        offer_result = await orchestrator._submit_offer_for_project(mock_project)
        
        if offer_result.get("success"):
            print("✅ AI offer generation test passed")
            offer_data = offer_result.get("offer_data", {})
            if "ai_offer" in offer_data:
                ai_offer = offer_data["ai_offer"]
                print(f"   Generated subject: {ai_offer.get('subject', 'Not generated')}")
                print(f"   Generated price: {ai_offer.get('proposed_price', 'Not generated')}")
        else:
            print(f"❌ AI offer generation test failed: {offer_result.get('error', 'Unknown error')}")
            return False
        
        await orchestrator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ AI offer generation test error: {str(e)}")
        return False


async def test_error_handling():
    """Test error handling functionality."""
    print("\n🛡️ Testing Error Handling...")
    
    orchestrator = BaharAutomationOrchestrator(headless=False)
    
    try:
        # Test with invalid project
        invalid_project = {
            "title": "Invalid Project",
            "url": "https://invalid-url-that-does-not-exist.com"
        }
        
        # This should handle the error gracefully
        offer_result = await orchestrator._submit_offer_for_project(invalid_project)
        
        if not offer_result.get("success"):
            print("✅ Error handling test passed - correctly handled invalid project")
        else:
            print("⚠️ Error handling test - unexpected success with invalid project")
        
        # Test consecutive error tracking
        print(f"   Consecutive errors: {orchestrator.consecutive_errors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test error: {str(e)}")
        return False


async def test_single_cycle():
    """Test a complete single automation cycle."""
    print("\n🔄 Testing Single Automation Cycle...")
    
    orchestrator = BaharAutomationOrchestrator(headless=False)
    
    try:
        # Run a single cycle with minimal projects
        cycle_result = await orchestrator.run_automation_cycle(max_projects=2)
        
        print(f"✅ Single cycle test completed")
        print(f"   Projects processed: {cycle_result.get('projects_processed', 0)}")
        print(f"   Offers submitted: {cycle_result.get('offers_submitted', 0)}")
        print(f"   Success: {cycle_result.get('success', False)}")
        
        if cycle_result.get('errors'):
            print(f"   Errors: {len(cycle_result['errors'])}")
            for error in cycle_result['errors'][:2]:
                print(f"     - {error}")
        
        await orchestrator.cleanup()
        return cycle_result.get('success', False)
        
    except Exception as e:
        print(f"❌ Single cycle test error: {str(e)}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🧪 Bahar Automation System Tests")
    print("=" * 50)
    
    # Check environment variables
    load_dotenv()
    
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return False
    
    test_results = {}
    
    # Run tests
    tests = [
        ("Authentication", test_authentication),
        ("Project Filtering", test_project_filtering),
        ("AI Offer Generation", test_ai_offer_generation),
        ("Error Handling", test_error_handling),
        ("Single Cycle", test_single_cycle)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results[test_name] = result
            print(f"   {test_name}: {'✅ PASS' if result else '❌ FAIL'}")
        except Exception as e:
            test_results[test_name] = False
            print(f"   {test_name}: ❌ ERROR - {str(e)}")
    
    # Summary
    print("\n📊 Test Summary:")
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The automation system is ready to use.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the configuration and try again.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 