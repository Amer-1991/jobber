#!/usr/bin/env python3
"""
Test to analyze the proposal submission form structure and identify form fields.
This will navigate to the proposal submission page and extract form field information.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def analyze_proposal_form():
    """
    Navigate to the proposal submission form and analyze its structure.
    """
    print("🔍 Analyzing Proposal Submission Form Structure...")
    
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
        
        # Step 2: Navigate to the specific project and proposal submission form
        print("🔄 Step 2: Navigating to proposal submission form...")
        
        # From the interaction log, we know the exact URL
        proposal_url = "https://bahr.sa/projects/recruitments/01987f02-014f-74b7-96ef-caa0578f2496/proposals/submit"
        
        await page.goto(proposal_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "proposals/submit" not in current_url:
            print("❌ Failed to navigate to proposal submission form")
            return
        
        print("✅ Successfully navigated to proposal submission form!")
        
        # Step 3: Analyze form structure
        print("🔍 Step 3: Analyzing form structure...")
        
        # Get page title
        title = await page.title()
        print(f"📄 Page title: {title}")
        
        # Find all form elements
        form_elements = await page.query_selector_all("form")
        print(f"📋 Found {len(form_elements)} form(s)")
        
        # Analyze each form
        for i, form in enumerate(form_elements):
            print(f"\n📝 Form {i+1}:")
            
            # Get form attributes
            form_id = await form.get_attribute("id")
            form_class = await form.get_attribute("class")
            form_action = await form.get_attribute("action")
            form_method = await form.get_attribute("method")
            
            print(f"   🆔 ID: {form_id}")
            print(f"   🏷️ Class: {form_class}")
            print(f"   🔗 Action: {form_action}")
            print(f"   📤 Method: {form_method}")
            
            # Find all input fields in this form
            inputs = await form.query_selector_all("input, textarea, select")
            print(f"   📥 Found {len(inputs)} input fields:")
            
            for j, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute("type")
                input_name = await input_elem.get_attribute("name")
                input_id = await input_elem.get_attribute("id")
                input_placeholder = await input_elem.get_attribute("placeholder")
                input_required = await input_elem.get_attribute("required")
                input_value = await input_elem.get_attribute("value")
                
                # Get label for this input
                label_text = ""
                if input_id:
                    label = await page.query_selector(f"label[for='{input_id}']")
                    if label:
                        label_text = await label.text_content()
                
                print(f"      📝 Field {j+1}:")
                print(f"         🏷️ Type: {input_type}")
                print(f"         📛 Name: {input_name}")
                print(f"         🆔 ID: {input_id}")
                print(f"         📍 Placeholder: {input_placeholder}")
                print(f"         ⚠️ Required: {input_required}")
                print(f"         💾 Value: {input_value}")
                print(f"         🏷️ Label: {label_text}")
        
        # Step 4: Look for specific form fields mentioned in analytics
        print("\n🔍 Step 4: Looking for specific fields from analytics data...")
        
        # From the analytics data, we know there's a "duration" field
        duration_field = await page.query_selector("#duration")
        if duration_field:
            print("✅ Found 'duration' field (first field in form)")
            duration_type = await duration_field.get_attribute("type")
            duration_name = await duration_field.get_attribute("name")
            print(f"   📝 Duration field type: {duration_type}")
            print(f"   📛 Duration field name: {duration_name}")
        
        # Step 5: Get form length from analytics
        print("\n📊 Step 5: Form statistics from analytics...")
        print("   📏 Form length: 8 fields (from analytics data)")
        print("   🎯 First field ID: duration")
        print("   🎯 First field position: 1")
        
        # Step 6: Extract form content for manual analysis
        print("\n📄 Step 6: Extracting form content for analysis...")
        
        # Get the form content
        form_content = await page.query_selector("form")
        if form_content:
            form_html = await form_content.inner_html()
            print(f"📄 Form HTML length: {len(form_html)} characters")
            
            # Save form HTML for analysis
            with open("proposal_form_structure.html", "w", encoding="utf-8") as f:
                f.write(form_html)
            print("💾 Form HTML saved to: proposal_form_structure.html")
        
        # Step 7: Look for common proposal form patterns
        print("\n🔍 Step 7: Looking for common proposal form patterns...")
        
        # Common proposal form fields
        common_fields = [
            "duration", "price", "budget", "cost", "amount",
            "description", "proposal", "message", "details",
            "timeline", "deadline", "delivery", "completion",
            "experience", "portfolio", "skills", "expertise"
        ]
        
        found_fields = []
        for field_name in common_fields:
            # Try different selectors
            selectors = [
                f"#{field_name}",
                f"[name='{field_name}']",
                f"[id*='{field_name}']",
                f"[name*='{field_name}']",
                f"[placeholder*='{field_name}']"
            ]
            
            for selector in selectors:
                field = await page.query_selector(selector)
                if field:
                    field_type = await field.get_attribute("type")
                    field_name_attr = await field.get_attribute("name")
                    field_id = await field.get_attribute("id")
                    found_fields.append({
                        "name": field_name,
                        "type": field_type,
                        "name_attr": field_name_attr,
                        "id": field_id,
                        "selector": selector
                    })
                    break
        
        if found_fields:
            print("✅ Found common proposal fields:")
            for field in found_fields:
                print(f"   📝 {field['name']}: {field['type']} (ID: {field['id']}, Name: {field['name_attr']})")
        else:
            print("❌ No common proposal fields found")
        
        # Step 8: Get page text content for manual analysis
        print("\n📄 Step 8: Extracting page text content...")
        
        from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
        text_content = await get_dom_with_content_type("text_only")
        
        print(f"📄 Page text content length: {len(text_content)} characters")
        print("📄 First 1000 characters:")
        print(text_content[:1000])
        
        # Save text content for analysis
        with open("proposal_form_text.txt", "w", encoding="utf-8") as f:
            f.write(text_content)
        print("💾 Page text content saved to: proposal_form_text.txt")
        
        print("\n✅ Form analysis completed!")
        print("📁 Check the saved files for detailed form structure:")
        print("   - proposal_form_structure.html")
        print("   - proposal_form_text.txt")
        
    except Exception as e:
        print(f"❌ Error during form analysis: {str(e)}")
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
    print("🎯 Proposal Form Structure Analysis")
    print("=" * 50)
    print("This will analyze the proposal submission form to identify:")
    print("1. Form fields and their types")
    print("2. Required vs optional fields")
    print("3. Field names and IDs")
    print("4. Where to enter text and numbers")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting form structure analysis...")
    asyncio.run(analyze_proposal_form())
    
    print("\n✨ Analysis completed!") 