#!/usr/bin/env python3
"""
Test to capture the dynamic milestone form behavior.
This will test how the form changes when milestoneNumber is modified.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_dynamic_milestone_form():
    """
    Test the dynamic behavior of the milestone form fields.
    """
    print("🔍 Testing Dynamic Milestone Form Behavior...")
    
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
        
        # Step 2: Navigate to the proposal submission form
        print("🔄 Step 2: Navigating to proposal submission form...")
        
        proposal_url = "https://bahr.sa/projects/recruitments/01987f02-014f-74b7-96ef-caa0578f2496/proposals/submit"
        
        await page.goto(proposal_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "proposals/submit" not in current_url:
            print("❌ Failed to navigate to proposal submission form")
            return
        
        print("✅ Successfully navigated to proposal submission form!")
        
        # Step 3: Analyze initial form state
        print("🔍 Step 3: Analyzing initial form state...")
        
        # Get initial form fields
        initial_inputs = await page.query_selector_all("input, textarea, select")
        print(f"📥 Initial form has {len(initial_inputs)} input fields")
        
        for i, input_elem in enumerate(initial_inputs):
            input_id = await input_elem.get_attribute("id")
            input_type = await input_elem.get_attribute("type")
            input_name = await input_elem.get_attribute("name")
            print(f"   📝 Field {i+1}: ID={input_id}, Type={input_type}, Name={input_name}")
        
        # Step 4: Test milestone number = 1
        print("\n🧪 Step 4: Testing milestone number = 1...")
        
        # Find and fill the milestone number field
        milestone_field = await page.query_selector("#milestoneNumber")
        if milestone_field:
            await milestone_field.fill("1")
            await asyncio.sleep(2)  # Wait for dynamic fields to appear
            
            # Count inputs after setting milestone = 1
            inputs_after_1 = await page.query_selector_all("input, textarea, select")
            print(f"📥 After milestone=1: {len(inputs_after_1)} input fields")
            
            # Look for milestone-related fields
            milestone_fields = []
            for input_elem in inputs_after_1:
                input_id = await input_elem.get_attribute("id")
                input_type = await input_elem.get_attribute("type")
                input_name = await input_elem.get_attribute("name")
                input_placeholder = await input_elem.get_attribute("placeholder")
                
                # Get label for this input
                label_text = ""
                if input_id:
                    label = await page.query_selector(f"label[for='{input_id}']")
                    if label:
                        label_text = await label.text_content()
                
                if "milestone" in str(input_id).lower() or "budget" in str(input_id).lower() or "outcome" in str(input_id).lower():
                    milestone_fields.append({
                        "id": input_id,
                        "type": input_type,
                        "name": input_name,
                        "placeholder": input_placeholder,
                        "label": label_text
                    })
            
            print(f"🎯 Found {len(milestone_fields)} milestone-related fields:")
            for field in milestone_fields:
                print(f"   📝 {field['id']}: {field['type']} - {field['label']}")
        
        # Step 5: Test milestone number = 2
        print("\n🧪 Step 5: Testing milestone number = 2...")
        
        await milestone_field.fill("2")
        await asyncio.sleep(2)  # Wait for dynamic fields to appear
        
        inputs_after_2 = await page.query_selector_all("input, textarea, select")
        print(f"📥 After milestone=2: {len(inputs_after_2)} input fields")
        
        # Look for milestone-related fields
        milestone_fields_2 = []
        for input_elem in inputs_after_2:
            input_id = await input_elem.get_attribute("id")
            input_type = await input_elem.get_attribute("type")
            input_name = await input_elem.get_attribute("name")
            input_placeholder = await input_elem.get_attribute("placeholder")
            
            # Get label for this input
            label_text = ""
            if input_id:
                label = await page.query_selector(f"label[for='{input_id}']")
                if label:
                    label_text = await label.text_content()
            
            if "milestone" in str(input_id).lower() or "budget" in str(input_id).lower() or "outcome" in str(input_id).lower():
                milestone_fields_2.append({
                    "id": input_id,
                    "type": input_type,
                    "name": input_name,
                    "placeholder": input_placeholder,
                    "label": label_text
                })
        
        print(f"🎯 Found {len(milestone_fields_2)} milestone-related fields:")
        for field in milestone_fields_2:
            print(f"   📝 {field['id']}: {field['type']} - {field['label']}")
        
        # Step 6: Test milestone number = 3
        print("\n🧪 Step 6: Testing milestone number = 3...")
        
        await milestone_field.fill("3")
        await asyncio.sleep(2)  # Wait for dynamic fields to appear
        
        inputs_after_3 = await page.query_selector_all("input, textarea, select")
        print(f"📥 After milestone=3: {len(inputs_after_3)} input fields")
        
        # Look for milestone-related fields
        milestone_fields_3 = []
        for input_elem in inputs_after_3:
            input_id = await input_elem.get_attribute("id")
            input_type = await input_elem.get_attribute("type")
            input_name = await input_elem.get_attribute("name")
            input_placeholder = await input_elem.get_attribute("placeholder")
            
            # Get label for this input
            label_text = ""
            if input_id:
                label = await page.query_selector(f"label[for='{input_id}']")
                if label:
                    label_text = await label.text_content()
            
            if "milestone" in str(input_id).lower() or "budget" in str(input_id).lower() or "outcome" in str(input_id).lower():
                milestone_fields_3.append({
                    "id": input_id,
                    "type": input_type,
                    "name": input_name,
                    "placeholder": input_placeholder,
                    "label": label_text
                })
        
        print(f"🎯 Found {len(milestone_fields_3)} milestone-related fields:")
        for field in milestone_fields_3:
            print(f"   📝 {field['id']}: {field['type']} - {field['label']}")
        
        # Step 7: Capture the complete form structure with milestones
        print("\n📄 Step 7: Capturing complete form structure with milestones...")
        
        # Get all form content after setting milestone = 3
        form_content = await page.query_selector("form")
        if form_content:
            form_html = await form_content.inner_html()
            
            # Save form HTML for analysis
            with open("milestone_form_structure.html", "w", encoding="utf-8") as f:
                f.write(form_html)
            print("💾 Milestone form HTML saved to: milestone_form_structure.html")
        
        # Step 8: Get page text content to see all labels
        print("\n📄 Step 8: Extracting page text content...")
        
        from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
        text_content = await get_dom_with_content_type("text_only")
        
        print(f"📄 Page text content length: {len(text_content)} characters")
        print("📄 Text content (looking for milestone-related text):")
        print(text_content)
        
        # Save text content for analysis
        with open("milestone_form_text.txt", "w", encoding="utf-8") as f:
            f.write(text_content)
        print("💾 Milestone form text saved to: milestone_form_text.txt")
        
        # Step 9: Summary of dynamic behavior
        print("\n📊 Step 9: Summary of dynamic milestone behavior...")
        print(f"   📏 Initial form fields: {len(initial_inputs)}")
        print(f"   📏 After milestone=1: {len(inputs_after_1)}")
        print(f"   📏 After milestone=2: {len(inputs_after_2)}")
        print(f"   📏 After milestone=3: {len(inputs_after_3)}")
        
        print("\n✅ Dynamic milestone form analysis completed!")
        print("📁 Check the saved files for detailed form structure:")
        print("   - milestone_form_structure.html")
        print("   - milestone_form_text.txt")
        
    except Exception as e:
        print(f"❌ Error during dynamic form analysis: {str(e)}")
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
    print("🎯 Dynamic Milestone Form Analysis")
    print("=" * 50)
    print("This will test how the form changes when milestoneNumber is modified:")
    print("1. Test milestone = 1 (should show 2 additional fields)")
    print("2. Test milestone = 2 (should show 4 additional fields)")
    print("3. Test milestone = 3 (should show 6 additional fields)")
    print("4. Capture all dynamic field IDs and labels")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting dynamic milestone form analysis...")
    asyncio.run(test_dynamic_milestone_form())
    
    print("\n✨ Analysis completed!") 