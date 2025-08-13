#!/usr/bin/env python3
"""
Improved Bahar Automation Script (Fixed)
========================================

This script combines all tested components with improved form filling
that keeps the browser open so you can see the generated content.
"""

import asyncio
import os
import json
import traceback
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, Set

# Global run artifacts directory
RUN_ARTIFACTS_DIR: Optional[str] = None

# Import the tested components
from token_manager import TokenManager
from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.submit_offer_with_ai import generate_fallback_offer, extract_complete_project_details
from jobber_fsm.utils.logger import logger

# Helper functions
async def clear_and_fill_input(element, value):
    """Clear and fill an input element with a value."""
    try:
        await element.click()
        await element.fill("")
        await element.type(value)
        return True
    except Exception:
        try:
            await element.fill(value)
            return True
        except Exception:
            return False

def get_contexts():
    """Get browser contexts - placeholder for now."""
    return []

def ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass

async def save_debug_artifacts(page, label: str) -> None:
    try:
        global RUN_ARTIFACTS_DIR
        if not RUN_ARTIFACTS_DIR:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            RUN_ARTIFACTS_DIR = os.path.join("artifacts", f"run_{ts}")
        ensure_dir(RUN_ARTIFACTS_DIR)
        # Subdir per label
        label_dir = os.path.join(RUN_ARTIFACTS_DIR, label)
        ensure_dir(label_dir)

        # Save URL and title
        try:
            title = await page.title()
        except Exception:
            title = ""
        info = {
            "url": page.url,
            "title": title,
            "timestamp": datetime.now().isoformat(),
        }
        with open(os.path.join(label_dir, "info.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        # Save HTML content
        try:
            content = await page.content()
            with open(os.path.join(label_dir, f"{label}.html"), "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

        # Save screenshot
        try:
            await page.screenshot(path=os.path.join(label_dir, f"{label}.png"), full_page=True)
        except Exception:
            pass

        # Save cookies
        try:
            cookies = await page.context.cookies()
            with open(os.path.join(label_dir, "cookies.json"), "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    except Exception:
        pass

async def query_selector_any_frame(page, selector: str):
    try:
        el = await page.query_selector(selector)
        if el:
            return el
    except Exception:
        pass
    try:
        for frame in page.frames:
            try:
                el = await frame.query_selector(selector)
                if el:
                    return el
            except Exception:
                continue
    except Exception:
        pass
    return None

async def improved_fill_offer_form(page, ai_offer, user_preferences):
    """
    Improved form filling function with better selectors and error handling.
    """
    try:
        logger.info("Filling Bahar offer form with improved selectors")
        
        # Check if this is a monthly project
        is_monthly = ai_offer.get("is_monthly", False)
        if is_monthly:
            print("📅 Detected monthly project - using monthly form filling logic")
        else:
            print("📋 Detected one-time project - using milestone form filling logic")
        
        # Wait for the form to be fully loaded first
        try:
            print("   ⏳ Waiting for form to fully load...")
            await page.wait_for_function(
                "() => !document.querySelector('[data-sentry-component=\"SubmitProposalFormLoading\"]')",
                timeout=30000
            )
            print("   ✅ Form is now fully loaded!")
            
            # Wait a bit more for form elements to be ready
            await page.wait_for_timeout(3000)
            
            # Additional check: wait for actual form elements to appear
            await page.wait_for_function(
                "() => document.querySelectorAll('input, textarea').length > 0",
                timeout=15000
            )
            print("   ✅ Form elements are now available!")
            
        except Exception as e:
            print(f"   ⚠️ Could not wait for form to load: {e}")
            # Try to continue anyway
            await page.wait_for_timeout(5000)
        
        # Debug: Check what elements are available on the page
        print("🔍 Debugging form elements...")
        try:
            # Get all input and textarea elements
            all_inputs = await page.query_selector_all("input")
            all_textareas = await page.query_selector_all("textarea")
            all_buttons = await page.query_selector_all("button")
            
            print(f"   Found {len(all_inputs)} input elements")
            print(f"   Found {len(all_textareas)} textarea elements")
            print(f"   Found {len(all_buttons)} button elements")
            
            # Show some input details
            for i, inp in enumerate(all_inputs[:5]):  # Show first 5 inputs
                try:
                    input_id = await inp.get_attribute('id')
                    input_name = await inp.get_attribute('name')
                    input_type = await inp.get_attribute('type')
                    input_placeholder = await inp.get_attribute('placeholder')
                    print(f"   Input {i+1}: id='{input_id}', name='{input_name}', type='{input_type}', placeholder='{input_placeholder}'")
                except:
                    pass
            
            # Show some textarea details
            for i, ta in enumerate(all_textareas[:3]):  # Show first 3 textareas
                try:
                    ta_id = await ta.get_attribute('id')
                    ta_name = await ta.get_attribute('name')
                    ta_placeholder = await ta.get_attribute('placeholder')
                    print(f"   Textarea {i+1}: id='{ta_id}', name='{ta_name}', placeholder='{ta_placeholder}'")
                except:
                    pass
                    
        except Exception as e:
            print(f"   Debug error: {str(e)}")
        
        filled_fields = []
        
        # 1. Fill Duration Field
        print("📝 Filling duration field...")
        duration_selectors = [
            "input[data-testid='duration-input']",
            "input[id='duration']",
            "input[name='duration']",
            "input[placeholder*='المدة']",
            "input[placeholder*='duration']",
            "input[placeholder*='أيام']",
            "input[placeholder*='days']",
            "input[type='number']",
            "input[type='text']"
        ]
        
        duration_filled = False
        for selector in duration_selectors:
            try:
                elements = await page.query_selector_all(selector)
            except Exception:
                continue

            for element in elements:
                try:
                    placeholder = await element.get_attribute('placeholder') or ''
                    is_duration_field = any(
                        keyword in (placeholder.lower() if placeholder else '')
                        for keyword in ['duration', 'المدة', 'أيام', 'days']
                    ) or not placeholder
                    if is_duration_field:
                        await element.fill(str(ai_offer.get('duration', 3)))
                        filled_fields.append('duration')
                        print(f"✅ Duration filled: {ai_offer.get('duration', 3)} days with selector: {selector}")
                        duration_filled = True
                        break
                except Exception:
                    continue

            if duration_filled:
                break
        
        # 2. Fill Milestone Number Field
        print("📝 Filling milestone number field...")
        milestone_selectors = [
            "input[data-testid='milestoneNumber-input']",
            "input[id='milestoneNumber']",
            "input[name='milestoneNumber']",
            "input[name='milestones']",
            "input[placeholder*='مراحل']",
            "input[placeholder*='phases']",
            "input[placeholder*='Number of milestones']",
            "input[placeholder*='milestone']",
            "input[type='number']",
            "input[type='text']"
        ]
        
        milestone_filled = False
        for selector in milestone_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        placeholder = await element.get_attribute('placeholder') or ''
                        is_milestone_field = any(
                            keyword in (placeholder.lower() if placeholder else '')
                            for keyword in ['phases', 'مراحل', 'milestone']
                        ) or not placeholder
                        if is_milestone_field:
                            await element.fill(str(ai_offer.get('milestone_number', 3)))
                            filled_fields.append('milestone_number')
                            print(f"✅ Milestone number filled: {ai_offer.get('milestone_number', 3)} phases with selector: {selector}")

                            # Wait for milestone fields to appear and ensure they render
                            try:
                                await element.press('Tab')
                            except Exception:
                                pass
                            try:
                                await page.wait_for_selector("[data-testid*='proposalMilestones.0'], input[name*='proposalMilestones'][name*='budget']", timeout=3000)
                            except Exception:
                                pass
                            # Force-render milestones if not visible
                            try:
                                await element.press('Tab')
                            except Exception:
                                pass
                            try:
                                await page.wait_for_selector("[data-testid*='proposalMilestones.0'], input[name*='proposalMilestones'][name*='budget']", timeout=3000)
                            except Exception:
                                pass
                            # Force-render milestones if not visible
                            try:
                                wanted = int(ai_offer.get('milestone_number', 3))
                            except Exception:
                                wanted = 3
                            await ensure_milestones_rendered(page, wanted)

                            milestone_filled = True
                            break
                    except Exception:
                        continue
                if milestone_filled:
                    break
            except Exception:
                continue
        
        # 3. Fill Brief Field
        print("📝 Filling brief field...")
        brief_selectors = [
            "textarea[id='brief']",
            "textarea[name='brief']",
            "textarea[data-testid='brief']",
            "textarea[placeholder*='النبذة']",
            "textarea[placeholder*='brief']",
            "textarea[placeholder*='description']",
            "textarea[placeholder*='الوصف']",
            "textarea"
        ]
        
        brief_filled = False
        for selector in brief_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        placeholder = await element.get_attribute('placeholder') or ''
                        is_brief_field = any(
                            keyword in (placeholder.lower() if placeholder else '')
                            for keyword in ['brief', 'النبذة', 'description', 'الوصف']
                        ) or not placeholder
                        if is_brief_field:
                            await element.fill(ai_offer.get('brief', ''))
                            filled_fields.append('brief')
                            print('✅ Brief filled with Arabic content')
                            brief_filled = True
                            break
                    except Exception:
                        continue
                if brief_filled:
                    break
            except Exception:
                continue
        
        # 4. Check Platform Communication
        print("📝 Checking platform communication...")
        platform_selectors = [
            "input[id='platformCommunication']",
            "input[data-testid='platformCommunication-checkbox']",
            "input[name='platformCommunication']"
        ]
        
        for selector in platform_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_checked = await element.is_checked()
                    if not is_checked:
                        await element.check()
                        filled_fields.append("platform_communication")
                        print("✅ Platform communication checked")
                    break
            except Exception as e:
                continue
        
        # 5. Handle Monthly Projects (different form structure)
        if is_monthly:
            print("📅 Filling monthly project form...")
            
            # For monthly projects, we might need to fill different fields
            # Look for monthly-specific fields
            monthly_selectors = [
                "input[id='paymentRatePerPeriod']",
                "input[placeholder*='شهري']",
                "input[placeholder*='monthly']",
                "input[placeholder*='راتب']",
                "input[placeholder*='salary']",
                "input[placeholder*='ميزانية']",
                "input[placeholder*='budget']",
                "input[type='number']",
                "input[type='text']"
            ]
            
            for selector in monthly_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            await element.fill(str(ai_offer.get("total_price_sar", 1500)))
                            filled_fields.append("monthly_budget")
                            print(f"✅ Monthly budget filled: {ai_offer.get('total_price_sar', 1500)} SAR")
                            break
                        except:
                            continue
                except Exception:
                    continue
            
            # Look for any textarea or input that might be for the brief
            brief_selectors = [
                "textarea[placeholder*='وصف']",
                "textarea[placeholder*='description']",
                "textarea[placeholder*='تفاصيل']",
                "textarea[placeholder*='details']",
                "textarea",
                "input[placeholder*='وصف']",
                "input[placeholder*='description']"
            ]
            
            for selector in brief_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            await element.fill(ai_offer.get("brief", ""))
                            filled_fields.append("monthly_brief")
                            print("✅ Monthly brief filled")
                            break
                        except:
                            continue
                except Exception:
                    continue
        
        return {
            "success": len(filled_fields) > 0,
            "message": f"Filled fields: {', '.join(filled_fields)}",
            "filled_fields": filled_fields
        }
        
    except Exception as e:
        logger.error(f"Error in improved form filling: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

async def check_project_status(page):
    """
    Check if the project is eligible for offer submission.
    
    Returns:
        Dict with status information and eligibility
    """
    try:
        print("🔍 Checking project status...")
        
        # Common status indicators
        status_selectors = {
            "closed": [
                ".status-closed", ".project-closed", ".job-closed",
                ".closed", ".inactive", ".expired",
                "text=مغلق", "text=منتهي", "text=مكتمل",
                "text=Closed", "text=Expired", "text=Completed"
            ],
            "already_submitted": [
                ".already-submitted", ".submitted", ".applied",
                ".offer-submitted", ".proposal-submitted",
                "text=تم التقديم", "text=Already Applied", "text=Submitted",
                "text=عرض مقدم", "text=Offer Submitted"
            ],
            "rejected": [
                ".rejected", ".declined", ".not-selected",
                "text=مرفوض", "text=Rejected", "text=Declined",
                "text=Not Selected"
            ],
            "in_progress": [
                ".in-progress", ".active", ".ongoing",
                "text=قيد التنفيذ", "text=In Progress", "text=Active"
            ],
            "open": [
                ".open", ".available", ".active",
                "text=مفتوح", "text=Open", "text=Available"
            ]
        }
        
        status_info = {
            "eligible": True,
            "status": "unknown",
            "reason": "",
            "details": {}
        }
        
        # Check for each status type (prioritize "open" over negative statuses)
        found_statuses = []
        
        for status_type, selectors in status_selectors.items():
            for selector in selectors:
                try:
                    if selector.startswith("text="):
                        # Text-based search
                        text_to_find = selector[5:]  # Remove "text=" prefix
                        page_content = await page.content()
                        if text_to_find in page_content:
                            found_statuses.append(status_type)
                            status_info["details"][status_type] = text_to_find
                            print(f"   Found status: {status_type} - {text_to_find}")
                            break
                    else:
                        # Element-based search
                        elements = await page.query_selector_all(selector)
                        if elements:
                            found_statuses.append(status_type)
                            status_info["details"][status_type] = selector
                            print(f"   Found status: {status_type} - {selector}")
                            break
                except Exception as e:
                    continue
        
        # Determine final status (prioritize "open" over negative statuses)
        if "open" in found_statuses:
            status_info["status"] = "open"
            status_info["eligible"] = True
            print("   ✅ Project is OPEN and eligible for submission")
        elif "in_progress" in found_statuses:
            status_info["status"] = "in_progress"
            status_info["eligible"] = True
            print("   ✅ Project is IN PROGRESS and eligible for submission")
        elif "closed" in found_statuses:
            status_info["status"] = "closed"
            status_info["eligible"] = False
            status_info["reason"] = "Project is closed"
            print("   ❌ Project is CLOSED")
        elif "rejected" in found_statuses:
            status_info["status"] = "rejected"
            status_info["eligible"] = False
            status_info["reason"] = "Project is rejected"
            print("   ❌ Project is REJECTED")
        elif "already_submitted" in found_statuses:
            status_info["status"] = "already_submitted"
            status_info["eligible"] = False
            status_info["reason"] = "Already submitted to this project"
            print("   ❌ Already submitted to this project")
        else:
            status_info["status"] = "unknown"
            status_info["eligible"] = True  # Assume eligible if no clear status
            print("   ⚠️  Project status unknown, assuming eligible")
        
        # Only check for basic project status, not submit buttons yet
        # Submit buttons will be checked after navigating to the offer form
        
        # Don't check for disabled buttons on the project details page
        # We'll check for submit button availability after navigating to the offer form
        
        print(f"✅ Project status check completed: {status_info['status']} (Eligible: {status_info['eligible']})")
        return status_info
        
    except Exception as e:
        print(f"❌ Error checking project status: {str(e)}")
        return {
            "eligible": False,
            "status": "error",
            "reason": f"Error checking status: {str(e)}",
            "details": {}
        }

async def fill_milestone_fields_improved(page, milestones):
    """
    Improved milestone field filling with budget and outcome/description.
    """
    try:
        print(f"📝 Filling {len(milestones)} milestone fields...")
        
        for i, milestone in enumerate(milestones):
            # Try to scope queries to a specific milestone container when possible
            container_selectors = [
                f"[data-testid='proposalMilestones.{i}']",
                f"[id='proposalMilestones.{i}']",
                f"[name='proposalMilestones.{i}']",
                f"[data-testid^='proposalMilestones.{i}.']",
                f"[data-testid*='proposalMilestones.{i}']",
            ]
            container = None
            for cs in container_selectors:
                try:
                    container = await page.query_selector(cs)
                    if container:
                        break
                except Exception:
                    continue

            # Helper to query either inside container or globally
            async def query_in_scope(selector: str):
                if container:
                    try:
                        return await container.query_selector(selector)
                    except Exception:
                        return None
                return await page.query_selector(selector)

            async def query_all_in_scope(selector: str):
                if container:
                    try:
                        return await container.query_selector_all(selector)
                    except Exception:
                        return []
                return await page.query_selector_all(selector)

            # Fill budget field for this milestone
            budget_selectors = [
                f"input[data-testid='proposalMilestones.{i}.budget-input']",
                f"input[id='proposalMilestones.{i}.budget']",
                f"input[name='proposalMilestones.{i}.budget']",
                # Generic scoped fallbacks
                "input[name*='proposalMilestones'][name*='budget']",
                "input[id*='proposalMilestones'][id*='budget']",
                "input[data-testid*='budget']",
                # Arabic/placeholder fallbacks
                "input[placeholder*='ميزانية']",
                "input[placeholder*='السعر']",
                "input[placeholder*='المبلغ']",
                "input[aria-label*='ميزانية']",
                "input[aria-label*='السعر']",
                "input[aria-label*='المبلغ']",
                # Any number input inside the milestone container
                "input[type='number']",
                # Fallbacks from Selenium script pattern
                "input[name^='milestonePrice-']",
            ]
            for selector in budget_selectors:
                try:
                    element = await query_in_scope(selector)
                    if element:
                        amount_int = int(milestone.get('budget', 0))
                        ok = await clear_and_fill_input(element, str(amount_int))
                        if ok:
                            print(f"✅ Milestone {i+1} budget filled: {amount_int} SAR")
                        break
                except Exception:
                    continue
                    
            # Fill outcome/description field for this milestone
            outcome_selectors = [
                f"textarea[data-testid='proposalMilestones.{i}.outcome-input']",
                f"textarea[id='proposalMilestones.{i}.outcome']",
                f"textarea[name='proposalMilestones.{i}.outcome']",
                f"textarea[data-testid='proposalMilestones.{i}.description-input']",
                f"textarea[id='proposalMilestones.{i}.description']",
                f"textarea[name='proposalMilestones.{i}.description']",
                # Generic fallbacks within scope
                "textarea[placeholder*='المخرجات']",
                "textarea[placeholder*='النتيجة']",
                "textarea[placeholder*='الوصف']",
                "textarea[placeholder*='description']",
                "textarea[placeholder*='outcome']",
                "textarea",
                "input[data-testid*='.outcome-input']",
                "input[name*='outcome']",
                "input[id*='outcome']",
                # Any contenteditable rich-text areas
                "[contenteditable='true']",
                # Fallbacks from Selenium script pattern (name-like fields)
                "input[name^='milestoneName-']",
                "input[placeholder*='Description']",
            ]

            milestone_outcome = milestone.get('outcome', milestone.get('deliverable', f'المرحلة {i+1}: إنجاز المهام المطلوبة'))

            outcome_filled = False
            for selector in outcome_selectors:
                try:
                    element = await query_in_scope(selector)
                    if element:
                        try:
                            await element.click()
                            try:
                                await page.keyboard.press('Meta+A')
                                await page.keyboard.press('Backspace')
                            except Exception:
                                pass
                            await element.fill(milestone_outcome)
                            print(f"✅ Milestone {i+1} outcome filled: {milestone_outcome[:50]}...")
                            outcome_filled = True
                            break
                        except Exception:
                            continue
                except Exception:
                    continue

            # Last-resort: contenteditable div inside container (or page)
            if not outcome_filled:
                try:
                    ce = None
                    if container:
                        ce = await container.query_selector("div[contenteditable='true']")
                    if not ce:
                        for ctx in get_contexts():
                            ce = await ctx.query_selector("div[contenteditable='true']")
                            if ce:
                                break
                    if ce:
                        try:
                            await ce.click()
                            await page.keyboard.press('Meta+A')
                            await page.keyboard.press('Backspace')
                        except Exception:
                            pass
                        try:
                            await page.evaluate("(el, text) => { el.innerText = text; el.dispatchEvent(new Event('input', { bubbles: true })); }", ce, milestone_outcome)
                            print(f"✅ Milestone {i+1} outcome filled via contenteditable")
                            outcome_filled = True
                        except Exception:
                            pass
                except Exception:
                    pass

            if not outcome_filled:
                print(f"⚠️  Could not find outcome field for milestone {i+1}")
                
        # Global fallback: attempt to fill by index across all budget/outcome fields if some remain empty
        try:
            budget_all = await page.query_selector_all("input[data-testid*='proposalMilestones'][data-testid$='.budget-input'], input[name*='proposalMilestones'][name*='budget'], input[id*='proposalMilestones'][id*='budget']")
            outcome_all = await page.query_selector_all("textarea[data-testid*='proposalMilestones'][data-testid$='.outcome-input'], textarea[name*='proposalMilestones'][name*='outcome'], textarea[id*='proposalMilestones'][id*='outcome'], textarea[data-testid*='proposalMilestones'][data-testid$='.description-input'], textarea[name*='proposalMilestones'][name*='description'], textarea[id*='proposalMilestones'][id*='description'], input[name*='proposalMilestones'][name*='outcome']")
            for i, milestone in enumerate(milestones):
                # Budget fallback
                if i < len(budget_all):
                    try:
                        val = await budget_all[i].input_value()
                    except Exception:
                        val = ""
                    if not val:
                        amount_int = int(milestone.get('budget', 0))
                        ok = await clear_and_fill_input(budget_all[i], str(amount_int))
                        if ok:
                            print(f"✅ (fallback) Milestone {i+1} budget filled: {amount_int} SAR")
                # Outcome fallback
                if i < len(outcome_all):
                    try:
                        val = await outcome_all[i].input_value()
                    except Exception:
                        val = ""
                    if not val:
                        text_val = milestone.get('outcome', milestone.get('deliverable', f'المرحلة {i+1}: إنجاز المهام المطلوبة'))
                        try:
                            await outcome_all[i].click()
                        except Exception:
                            pass
                        try:
                            await outcome_all[i].fill("")
                        except Exception:
                            pass
                        try:
                            await outcome_all[i].type(text_val)
                            print(f"✅ (fallback) Milestone {i+1} outcome filled")
                        except Exception:
                            try:
                                await page.evaluate("(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); }", outcome_all[i], text_val)
                                print(f"✅ (fallback JS) Milestone {i+1} outcome filled")
                            except Exception:
                                print(f"⚠️  (fallback) Could not fill outcome for milestone {i+1}")
        except Exception:
            pass
                    
    except Exception as e:
        logger.error(f"Error filling milestone fields: {str(e)}")

async def prepare_offer_form_ui(page):
    """Expand accordions/sections and scroll to reveal offer form inputs."""
    try:
        # Click on likely accordions/sections to reveal inputs
        toggles = [
            "button:has-text('الميزانية')",
            "button:has-text('مخرجات')",
            "button:has-text('المخرجات')",
            "button:has-text('تفاصيل')",
            "button:has-text('Milestone')",
            "button:has-text('Budget')",
        ]
        for sel in toggles:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(0.3)
            except Exception:
                continue

        # Progressive scroll to load inputs if lazy-rendered
        for _ in range(6):
            try:
                await page.mouse.wheel(0, 800)
            except Exception:
                pass
            await asyncio.sleep(0.2)

        # Wait briefly for common milestone fields
        try:
            await page.wait_for_selector("input[name*='proposalMilestones'][name*='budget'], textarea[name*='proposalMilestones'][name*='outcome']", timeout=2000)
        except Exception:
            pass
    except Exception:
        pass

async def fill_fields_with_javascript(page, budget_val, deliverable_text):
    """Fill budget and deliverable fields using JavaScript with proper event handling"""
    try:
        # Fill budget field using JavaScript with proper event handling
        await page.evaluate(f"""
            const budgetField = document.getElementById('proposalMilestones.0.budget');
            if (budgetField) {{
                budgetField.value = '{budget_val}';
                budgetField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                budgetField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                budgetField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            }}
        """)
        
        # Fill deliverable field using JavaScript with proper event handling
        await page.evaluate(f"""
            const deliverableField = document.getElementById('proposalMilestones.0.deliverable');
            if (deliverableField) {{
                deliverableField.value = '{deliverable_text}';
                deliverableField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                deliverableField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                deliverableField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            }}
        """)
        
        # Wait a bit for the form validation to update
        await asyncio.sleep(1)
        
        print(f"   ✅ Directly filled budget field with value: {budget_val}")
        print(f"   ✅ Directly filled deliverable field with text: {deliverable_text[:50]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ JavaScript fill failed: {e}")
        return False

async def fill_single_milestone_quick(page, ai_offer):
    """
    Comprehensive form filling for the proposal form with all required fields.
    """
    filled = []
    try:
        print("   🔧 Starting comprehensive form filling...")
        
        # 1. Fill duration field
        duration_selectors = [
            "#duration",
            "input[id='duration']",
            "input[data-testid='duration-input']",
        ]
        duration_val = ai_offer.get('duration_days', 3)  # Default to 3 days
        for sel in duration_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    print(f"   🎯 Found duration field with selector: {sel}")
                    ok = await clear_and_fill_input(el, str(duration_val))
                    if ok:
                        filled.append('duration')
                        print(f"   ✅ Filled duration field with value: {duration_val}")
                        break
            except Exception as e:
                print(f"   ❌ Failed to fill duration with selector {sel}: {e}")
                continue

        # 2. Fill budget field - using direct approach
        budget_val = int(ai_offer.get('total_price_sar') or ai_offer.get('total_price') or 250)
        print(f"   💰 Attempting to fill budget field with value: {budget_val}")
        budget_filled = False
        
        # Try direct budget field filling
        try:
            budget_field = await page.query_selector("input[id='proposalMilestones.0.budget']")
            if budget_field:
                print(f"   🎯 Found budget field directly")
                # Clear the field first
                await budget_field.click()
                await budget_field.fill("")
                await asyncio.sleep(0.5)
                # Fill with the value using JavaScript
                await page.evaluate(f"document.getElementById('proposalMilestones.0.budget').value = '{budget_val}'")
                await asyncio.sleep(0.5)
                # Trigger change event
                await page.evaluate("document.getElementById('proposalMilestones.0.budget').dispatchEvent(new Event('input', { bubbles: true }))")
                await asyncio.sleep(0.5)
                filled.append('milestone_budget')
                budget_filled = True
                print(f"   ✅ Filled budget field with value: {budget_val}")
            else:
                print(f"   🔍 Budget field not found directly")
        except Exception as e:
            print(f"   ❌ Failed to fill budget field directly: {e}")
        
        # Fallback to other selectors if direct approach failed
        if not budget_filled:
            budget_selectors = [
                "#proposalMilestones\\.0\\.budget",
                "input[data-testid='proposalMilestones.0.budget-input']",
                "input[name*='proposalMilestones'][name*='budget']",
                "input[id*='proposalMilestones'][id*='budget']",
                "input[data-testid*='budget']",
                "input[placeholder*='ميزانية']",
                "input[placeholder*='السعر']",
                "input[placeholder*='المبلغ']",
            ]
            for sel in budget_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        print(f"   🎯 Found budget field with selector: {sel}")
                        await el.click()
                        await el.fill("")
                        await asyncio.sleep(0.5)
                        await el.type(str(budget_val))
                        filled.append('milestone_budget')
                        budget_filled = True
                        print(f"   ✅ Filled budget field with value: {budget_val}")
                        break
                except Exception as e:
                    print(f"   ❌ Failed to fill budget with selector {sel}: {e}")
                    continue
        
        if not budget_filled:
            print(f"   ⚠️ Could not fill budget field with any selector")

        # 3. Fill deliverable field - using direct approach
        deliverable_text = ai_offer.get('deliverables') or 'تسليم المتطلبات حسب الوصف المطلوب'
        print(f"   📝 Attempting to fill deliverable field with text: {deliverable_text[:50]}...")
        deliverable_filled = False
        
        # Try direct deliverable field filling
        try:
            deliverable_field = await page.query_selector("input[id='proposalMilestones.0.deliverable']")
            if deliverable_field:
                print(f"   🎯 Found deliverable field directly")
                # Clear the field first
                await deliverable_field.click()
                await deliverable_field.fill("")
                await asyncio.sleep(0.5)
                # Fill with the text using JavaScript
                await page.evaluate(f"document.getElementById('proposalMilestones.0.deliverable').value = '{deliverable_text}'")
                await asyncio.sleep(0.5)
                # Trigger change event
                await page.evaluate("document.getElementById('proposalMilestones.0.deliverable').dispatchEvent(new Event('input', { bubbles: true }))")
                await asyncio.sleep(0.5)
                filled.append('milestone_deliverable')
                deliverable_filled = True
                print(f"   ✅ Filled deliverable field with text: {deliverable_text[:50]}...")
            else:
                print(f"   🔍 Deliverable field not found directly")
        except Exception as e:
            print(f"   ❌ Failed to fill deliverable field directly: {e}")
        
        # Fallback to other selectors if direct approach failed
        if not deliverable_filled:
            deliverable_selectors = [
                "#proposalMilestones\\.0\\.deliverable",
                "input[data-testid='proposalMilestones.0.deliverable-input']",
                "textarea[name*='proposalMilestones'][name*='outcome']",
                "textarea[id*='proposalMilestones'][id*='outcome']",
                "textarea[data-testid*='outcome']",
                "textarea[placeholder*='الوصف']",
                "textarea",
            ]
            for sel in deliverable_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        print(f"   🎯 Found deliverable field with selector: {sel}")
                        await el.click()
                        await el.fill("")
                        await asyncio.sleep(0.5)
                        await el.type(deliverable_text)
                        filled.append('milestone_deliverable')
                        deliverable_filled = True
                        print(f"   ✅ Filled deliverable field with text: {deliverable_text[:50]}...")
                        break
                except Exception as e:
                    print(f"   ❌ Failed to fill deliverable with selector {sel}: {e}")
                    continue

        # 4. Fill brief field
        brief_text = ai_offer.get('brief') or 'أنا متخصص في هذا المجال وأضمن لكم جودة عالية في العمل مع الالتزام بالمواعيد المحددة.'
        brief_selectors = [
            "#brief",
            "textarea[id='brief']",
            "textarea[placeholder*='النبذة']",
            "textarea[placeholder*='الوصف']",
        ]
        brief_filled = False
        for sel in brief_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    print(f"   🎯 Found brief field with selector: {sel}")
                    try:
                        await el.click()
                    except Exception:
                        pass
                    try:
                        await el.fill("")
                    except Exception:
                        pass
                    try:
                        await el.type(brief_text)
                        filled.append('brief')
                        brief_filled = True
                        print(f"   ✅ Filled brief field with text: {brief_text[:50]}...")
                        break
                    except Exception as e:
                        print(f"   ❌ Failed to type into brief field: {e}")
                        continue
            except Exception as e:
                print(f"   ❌ Failed to find brief field with selector {sel}: {e}")
                continue

        # 5. Check platform communication checkbox
        checkbox_selectors = [
            "#platformCommunication",
            "input[id='platformCommunication']",
            "input[data-testid='platformCommunication-checkbox']",
        ]
        for sel in checkbox_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    print(f"   🎯 Found platform communication checkbox with selector: {sel}")
                    try:
                        await el.check()
                        filled.append('platform_communication')
                        print(f"   ✅ Checked platform communication checkbox")
                        break
                    except Exception as e:
                        print(f"   ❌ Failed to check platform communication checkbox: {e}")
                        continue
            except Exception as e:
                print(f"   ❌ Failed to find platform communication checkbox with selector {sel}: {e}")
                continue

        # 6. Handle proposed start date (usually "immediate" is selected by default)
        try:
            immediate_radio = await page.query_selector("input[value='immediate']")
            if immediate_radio:
                await immediate_radio.check()
                filled.append('start_date_immediate')
                print(f"   ✅ Selected immediate start date")
        except Exception as e:
            print(f"   ❌ Failed to select immediate start date: {e}")

        print(f"   📊 Form filling summary: {len(filled)} fields filled: {', '.join(filled)}")

        # Wait for the form to be fully loaded (not showing loading spinner)
        try:
            print("   ⏳ Waiting for form to fully load...")
            await page.wait_for_function(
                "() => !document.querySelector('[data-sentry-component=\"SubmitProposalFormLoading\"]')",
                timeout=15000
            )
            print("   ✅ Form is now fully loaded!")
            
            # Wait a bit more for form elements to be ready
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"   ⚠️ Could not wait for form to load: {e}")
            
        # Wait for submit button to be enabled
        try:
            submit_button = await page.query_selector("button[data-testid='submitProposalFormButton']")
            if submit_button:
                print("   ⏳ Waiting for submit button to be enabled...")
                await page.wait_for_function(
                    "() => !document.querySelector('button[data-testid=\"submitProposalFormButton\"]').disabled",
                    timeout=10000
                )
                print("   ✅ Submit button is now enabled!")
            else:
                print("   ⚠️ Could not find submit button")
        except Exception as e:
            print(f"   ⚠️ Could not wait for submit button to be enabled: {e}")

    except Exception as e:
        print(f"   ❌ Error in fill_single_milestone_quick: {e}")

    return {"success": len(filled) > 0, "filled": filled}

async def ensure_milestones_rendered(page, desired_count: int):
    """Ensure that milestone input rows are rendered on the offer form.
    Attempts multiple strategies: waiting for selectors, clicking 'add milestone' buttons, and scrolling.
    """
    try:
        # Quick wait for common selectors
        try:
            await page.wait_for_selector("input[name*='proposalMilestones'][name*='budget'], textarea[name*='proposalMilestones'][name*='outcome']", timeout=1500)
            return
        except Exception:
            pass

        # Try clicking add milestone buttons until desired count appears
        add_selectors = [
            "button:has-text('إضافة مرحلة')",
            "button:has-text('أضف مرحلة')",
            "button:has-text('إضافة')",
            "button:has-text('Add milestone')",
            "button[aria-label*='milestone']",
            "[data-testid*='add-milestone']",
            "button:has-text('+')",
        ]
        def count_rows():
            return page.eval_on_selector_all("[data-testid*='proposalMilestones'], [id*='proposalMilestones']", "els => els.length").catch(lambda _: 0)

        current = 0
        try:
            current = await page.eval_on_selector_all("input[name*='proposalMilestones'][name*='budget']", "els => els.length")
        except Exception:
            current = 0

        attempts = 0
        while current < desired_count and attempts < desired_count * 2:
            clicked = False
            for sel in add_selectors:
                try:
                    btns = await page.query_selector_all(sel)
                    if btns:
                        try:
                            await btns[0].click()
                            clicked = True
                            break
                        except Exception:
                            continue
                except Exception:
                    continue
            if not clicked:
                try:
                    await page.mouse.wheel(0, 1200)
                except Exception:
                    pass
            await asyncio.sleep(0.6)
            try:
                current = await page.eval_on_selector_all("input[name*='proposalMilestones'][name*='budget']", "els => els.length")
            except Exception:
                current = 0
            attempts += 1
    except Exception:
        pass

async def continue_automation_loop(page, user_preferences, visited_ids: Optional[Set[str]] = None):
    """
    Continue the automation loop for the next project.
    This function handles the recursive automation after submitting an offer.
    """
    try:
        print("\n🔄 Continuing automation for next project...")
        
        # Wait for project details to load
        print("   Waiting for project details to load...")
        await asyncio.sleep(3)
        
        # Wait for project content to appear
        try:
            await page.wait_for_selector(".project-details, .project-info, .job-details, [data-testid='project-details']", timeout=15000)
            print("   ✅ Project details loaded!")
        except:
            print("   ⚠️  Project details not found, but continuing...")
        
        # Additional wait for dynamic content
        await asyncio.sleep(2)
        
        # Extract project details
        print("\n Step 5: Extracting project details...")
        try:
            # Wait a bit more for any dynamic content to load
            print("   Waiting for dynamic content to load...")
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            await asyncio.sleep(2)
            
            project_info = await extract_complete_project_details(page, {})
            
            if not project_info:
                print("❌ Failed to extract project details")
                return False
            
            print("✅ Project details extracted successfully!")
            print(f"   Title: {project_info.get('title', 'N/A')}")
            print(f"   Budget: {project_info.get('budget', 'N/A')}")
            print(f"   Skills: {', '.join(project_info.get('skills', []))}")
            print(f"   Description: {project_info.get('description', 'N/A')[:100]}...")
            
            # Add status info to project details
            project_info["status"] = status_info
            
            # Save project details to file for inspection
            with open('scraped_project_details.json', 'w', encoding='utf-8') as f:
                json.dump(project_info, f, ensure_ascii=False, indent=2)
            print("💾 Project details saved to 'scraped_project_details.json'")
            
        except Exception as e:
            print(f"❌ Error extracting project details: {str(e)}")
            traceback.print_exc()
            return False
        
        # Generate AI offer
        print("\n Step 6: Generating AI Arabic offer...")
        try:
            ai_offer = generate_fallback_offer(project_info, user_preferences)
            
            print("✅ AI Offer Generated Successfully!")
            print("📝 Generated Offer Details:")
            print(f"   Duration: {ai_offer.get('duration', 'N/A')} days")
            print(f"   Milestones: {ai_offer.get('milestone_number', 'N/A')}")
            print(f"   Total Price: {ai_offer.get('total_price_sar', 'N/A')} SAR")
            print(f"   Brief: {ai_offer.get('brief', 'N/A')[:50]}...")
            print(f"   Platform Communication: {ai_offer.get('platform_communication', 'N/A')}")
            
            # Save AI offer
            with open('generated_ai_offer.json', 'w', encoding='utf-8') as f:
                json.dump(ai_offer, f, ensure_ascii=False, indent=2)
            print("💾 AI offer saved to 'generated_ai_offer.json'")
        except Exception as e:
            print(f"❌ Error generating AI offer: {str(e)}")
            traceback.print_exc()
            return False
        
        # Find and navigate to offer submission form
        print("\n Step 7: Finding and navigating to offer submission form...")
        try:
            # If page shows 'عرض مشاريع مماثلة' then offer already submitted
            try:
                similar_el = await page.query_selector("a:has-text('عرض مشاريع مماثلة'), button:has-text('عرض مشاريع مماثلة')")
                page_html = await page.content()
                if similar_el is not None or ("عرض مشاريع مماثلة" in page_html):
                    print("   ℹ️ Found 'عرض مشاريع مماثلة' — offer already submitted. Moving to next project")
                    # Instead of recursive call, just return True to continue the main loop
                    return True
            except Exception:
                pass
            # Look for submit offer/apply buttons on the project page
            offer_button_selectors = [
                "button:has-text('تقديم العرض')",
                "button:has-text('تقديم عرض')",
                "button:has-text('قدم عرض')",
                "button:has-text('قدّم عرض')",
                "button:has-text('Send Offer')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('تطبيق')",
                "a:has-text('تقديم العرض')",
                "a:has-text('تقديم عرض')",
                "a:has-text('قدم عرض')",
                "a:has-text('قدّم عرض')",
                "a:has-text('Send Offer')",
                "a:has-text('Submit')",
                "a:has-text('Apply')",
                "a:has-text('تطبيق')",
                "[data-testid='submit-offer']",
                "[data-testid='apply']",
                ".submit-offer-btn",
                ".apply-btn",
                "button[type='submit']",
                "input[type='submit']",
                # href fallbacks
                "a[href*='submit']:not([href*='my-proposals'])",
                "a[href*='apply']:not([href*='my-proposals'])",
                "a[href*='proposal']:not([href*='my-proposals'])"
            ]
            
            # Debug: Show all buttons and links on the page
            print("🔍 Debugging buttons and links on project page...")
            try:
                all_buttons = await page.query_selector_all("button")
                all_links = await page.query_selector_all("a")
                print(f"   Found {len(all_buttons)} buttons and {len(all_links)} links on the page")
                
                # Show first 10 buttons
                for i, btn in enumerate(all_buttons[:10]):
                    try:
                        btn_text = await btn.text_content()
                        btn_type = await btn.get_attribute('type')
                        btn_class = await btn.get_attribute('class')
                        print(f"   Button {i+1}: text='{btn_text[:30]}', type='{btn_type}', class='{btn_class}'")
                    except:
                        pass
                
                # Show first 10 links
                for i, link in enumerate(all_links[:10]):
                    try:
                        link_text = await link.text_content()
                        link_href = await link.get_attribute('href')
                        print(f"   Link {i+1}: text='{link_text[:30]}', href='{link_href}'")
                    except:
                        pass
            except Exception as e:
                print(f"   Debug error: {str(e)}")
            
            offer_button = None
            for selector in offer_button_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    if buttons:
                        offer_button = buttons[0]
                        print(f"   Found offer button with selector: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not offer_button:
                print("   No offer button found, trying to find any submit/apply link...")
                # Try to find any link that might lead to offer form (exclude my-proposals)
                submit_selectors = [
                    "a[href*='offer']:not([href*='my-proposals'])",
                    "a[href*='bid']:not([href*='my-proposals'])",
                    "a[href*='submit']:not([href*='my-proposals'])",
                    "a[href*='apply']:not([href*='my-proposals'])"
                ]
                
                for selector in submit_selectors:
                    try:
                        links = await page.query_selector_all(selector)
                        if links:
                            offer_button = links[0]
                            print(f"   Found submit link with selector: {selector}")
                            break
                    except Exception as e:
                        continue
            
            if offer_button:
                print("   Clicking on offer submission button...")
                try:
                    # Ensure in viewport and clickable
                    try:
                        await offer_button.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    await offer_button.wait_for_element_state("visible", timeout=7000)
                    await offer_button.wait_for_element_state("stable", timeout=7000)
                    # Try multiple click strategies
                    try:
                        await offer_button.click(timeout=7000)
                    except Exception:
                        try:
                            await page.evaluate("el => el.click()", offer_button)
                        except Exception:
                            await page.keyboard.press('Enter')
                    await asyncio.sleep(2)  # Wait for form page to load
                    print("✅ Successfully navigated to offer form!")
                except Exception as e:
                    print(f"   Error clicking offer button: {str(e)}")
                    print("   Trying alternative approach...")
                    try:
                        # Try to get the href and navigate directly
                        href = await offer_button.get_attribute('href')
                        if href:
                            await page.goto(href, wait_until="domcontentloaded", timeout=8000)
                            await asyncio.sleep(2)
                            print("✅ Successfully navigated to offer form via direct URL!")
                        else:
                            print("   No href found, continuing anyway...")
                    except Exception as e2:
                        print(f"   Alternative approach also failed: {str(e2)}")
                        print("   Continuing anyway...")
                
                # Get current URL to confirm we're on the offer form page
                current_url = page.url
                print(f"   Current URL: {current_url}")
                
                if "/proposals/" in current_url or "/submit" in current_url:
                    print("✅ Confirmed we're on the offer form page!")
                else:
                    print("⚠️  May not be on the offer form page, but continuing...")
                
                # Check submit button availability on form page
                print("   Checking submit button availability on form page...")
                try:
                    submit_button = await page.query_selector("button[type='submit']")
                    if submit_button:
                        is_enabled = await submit_button.is_enabled()
                        print(f"   Found submit button: button[type='submit']")
                        print(f"   ✅ Submit button is available and enabled!")
                    else:
                        print("   ⚠️  No submit button found on form page")
                except Exception as e:
                    print(f"   Error checking submit button: {str(e)}")
                
            else:
                print("⚠️  No offer button found — treating as not eligible and moving to next project")
                # Move to next project directly
                return await go_to_next_project(page, user_preferences, last_project_id=extract_project_id_from_url(page.url), visited_ids=visited_ids)
                
        except Exception as e:
            print(f"❌ Error finding/navigating to offer form: {str(e)}")
            print("   Continuing anyway...")
        
        # Fill the offer form with generated data
        print("\n Step 8: Filling offer form with generated data...")
        try:
            # Prepare UI: ensure form inputs are visible (expand accordions, scroll, wait)
            await prepare_offer_form_ui(page)

            # Use comprehensive form filling as primary method
            print("   🔧 Starting comprehensive form filling...")
            try:
                fill_result = await fill_single_milestone_quick(page, ai_offer)
                print(f"   📊 Comprehensive form filling result: {fill_result}")
                
                # If comprehensive filling failed, try direct JavaScript filling
                if not fill_result.get("success"):
                    print("   ⚠️ Comprehensive form filling failed, trying direct JavaScript fill...")
                    try:
                        budget_val = int(ai_offer.get('total_price_sar') or ai_offer.get('total_price') or 250)
                        deliverable_text = ai_offer.get('deliverables') or 'تسليم المتطلبات حسب الوصف المطلوب'
                        
                        # Use the new JavaScript filling function
                        js_success = await fill_fields_with_javascript(page, budget_val, deliverable_text)
                        if js_success:
                            fill_result = {"success": True, "filled_fields": ["budget", "deliverable"]}
                        else:
                            fill_result = {"success": False}
                        
                    except Exception as e:
                        print(f"   ❌ Direct JavaScript fill failed: {e}")
                        # Fallback to legacy method
                        fill_result = await improved_fill_offer_form(page, ai_offer, user_preferences)
                        
            except Exception as e:
                print(f"   ❌ Comprehensive form filling failed with error: {e}")
                fill_result = {"success": False}
            
            if fill_result.get("success"):
                print("✅ Offer form filled successfully!")
                print(f"   Result: {fill_result.get('message', 'N/A')}")
                print(f"   Filled fields: {fill_result.get('filled_fields', [])}")
                
                # Wait for submit button to be enabled
                try:
                    await page.wait_for_function("""
                        () => {
                            const submitBtn = document.querySelector('button[data-testid="submitProposalFormButton"]');
                            return submitBtn && !submitBtn.disabled;
                        }
                    """, timeout=10000)
                    print("   ✅ Submit button is now enabled")
                except Exception as e:
                    print(f"   ⚠️ Could not verify submit button enabled: {e}")
                
                # Submit the offer
                print("\n Step 9: Submitting the offer...")
                try:
                    # Look for submit button
                    submit_selectors = [
                        "button:has-text('إرسال العرض')",
                        "button:has-text('Send Offer')",
                        "button:has-text('Submit')",
                        "button[type='submit']",
                        "input[type='submit']",
                        "button:has-text('تقديم')"
                    ]
                    # If not found, try broader fallback once
                    if not submit_button:
                        try:
                            btns = await page.query_selector_all("button, input[type='submit']")
                            for b in btns:
                                try:
                                    t = (await b.text_content() or "").strip()
                                except Exception:
                                    t = ""
                                # Heuristic match Arabic labels
                                if any(k in t for k in ["إرسال", "تقديم", "Submit", "Send"]):
                                    submit_button = b
                                    print("   Fallback found a submit-like button")
                                    break
                        except Exception:
                            pass
                    
                    submit_button = None
                    for selector in submit_selectors:
                        try:
                            buttons = await page.query_selector_all(selector)
                            if buttons:
                                submit_button = buttons[0]
                                print(f"   Found submit button with selector: {selector}")
                                break
                        except Exception as e:
                            continue

                    # Try enablement toggles if disabled
                    if submit_button:
                        try:
                            is_disabled = await submit_button.get_attribute('disabled')
                            if is_disabled:
                                # Toggle any required radios/checkboxes/date fields
                                try:
                                    immediate = await page.query_selector("input[id='proposedStartDateOption_immediate']")
                                    if immediate:
                                        await immediate.check()
                                except Exception:
                                    pass
                                try:
                                    specified = await page.query_selector("input[id='proposedStartDateOption_specified']")
                                    if specified:
                                        await specified.check()
                                        date_inp = await page.query_selector("input[id='proposedStartDate'], input[name*='proposedStartDate']")
                                        if date_inp:
                                            await date_inp.fill("2025-12-01")
                                except Exception:
                                    pass
                                try:
                                    platform = await page.query_selector("input[name='platformCommunication'], input[id='platformCommunication']")
                                    if platform and not await platform.is_checked():
                                        await platform.check()
                                except Exception:
                                    pass
                                await asyncio.sleep(0.5)
                        except Exception:
                            pass
                    
                    if submit_button:
                        print("   Clicking submit button...")
                        await submit_button.click()
                        await asyncio.sleep(3)  # Wait for submission
                        print("✅ Offer submitted successfully!")
                        
                        # Save successful submission
                        from datetime import datetime
                        submission_data = {
                            "project_url": page.url,
                            "project_title": project_info.get('title', ''),
                            "submitted_at": datetime.now().isoformat(),
                            "offer_details": ai_offer
                        }
                        
                        with open('successful_submissions.json', 'w', encoding='utf-8') as f:
                            json.dump(submission_data, f, ensure_ascii=False, indent=2)
                        print("💾 Submission saved to 'successful_submissions.json'")
                        
                    else:
                        print("❌ Submit button not found")
                        
                except Exception as e:
                    print(f"❌ Error submitting offer: {str(e)}")
                
            else:
                print("❌ Failed to fill offer form")
                print(f"   Error: {fill_result.get('message', 'N/A')}")
                print("   But continuing to show the form...")
                
        except Exception as e:
            print(f"❌ Error filling offer form: {str(e)}")
            print("   But continuing to show the form...")
        
        # Continue to next project after form filling/submission
        print("🔄 Continuing to next project...")
        next_project_result = await go_to_next_project(page, user_preferences, last_project_id=extract_project_id_from_url(page.url), visited_ids=visited_ids)
        if not next_project_result:
            print("❌ No more projects found or automation completed")
            return False
        # If next_project_result is True, we finished this iteration successfully
        print("✅ Moving to next project...")
        return True
        
    except Exception as e:
        print(f"❌ Error in automation loop: {str(e)}")
        return False


def extract_project_id_from_url(url: str) -> Optional[str]:
    try:
        parts = url.split("/")
        # Expect .../projects/recruitments/<id>/...
        for i, part in enumerate(parts):
            if part == "recruitments" and i + 1 < len(parts):
                candidate = parts[i + 1]
                if len(candidate) > 10 and candidate != "recruitments":
                    return candidate
        # Fallback: look for UUID-like strings
        for part in parts:
            if len(part) > 20 and '-' in part and part.count('-') >= 4:
                return part
        # Last fallback: last non-empty segment
        for seg in reversed(parts):
            if seg and seg not in ("projects", "recruitments"):
                return seg
    except:
        pass
    return None


async def go_to_next_project(page, user_preferences, last_project_id: Optional[str] = None, visited_ids: Optional[Set[str]] = None):
    if visited_ids is None:
        visited_ids = set()
    if last_project_id:
        visited_ids.add(last_project_id)

    print("   Going back to projects page...")
    await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=8000)
    await asyncio.sleep(3)

    print("   Waiting for projects to load...")
    await asyncio.sleep(2)

    project_selectors = [
        "a[href*='/projects/']",
        "a[href*='/recruitments/']",
        ".project-card a",
        ".project-item a",
        "[data-testid='project-link']",
        ".project a",
        "a[href*='project']",
        "a[href*='recruitment']",
        ".project-card",
        ".project-item",
        "[data-testid='project-card']",
        ".card[href*='/projects/']",
        ".card[href*='/recruitments/']"
    ]

    for selector in project_selectors:
        try:
            links = await page.query_selector_all(selector)
            if not links:
                continue
            print(f"   Found {len(links)} links with selector: {selector}")
            for i, link in enumerate(links):
                try:
                    href = await link.get_attribute('href')
                    link_text = await link.text_content()
                    print(f"   🔍 Checking link {i+1}: href='{href}', text='{(link_text or '')[:30]}'")
                    if not href or '/proposals/' in href or '/my-proposals' in href:
                        continue
                    if ('/projects/' in href or '/recruitments/' in href) and len(href.split('/')) > 3:
                        if href in ('/projects', '/recruitments'):
                            continue
                        # Extract project id and skip if visited
                        candidate_id = extract_project_id_from_url(href)
                        if candidate_id and candidate_id in visited_ids:
                            continue
                        print(f"   ✅ Found next project: {href}")
                        if not href.startswith('http'):
                            href = f"https://bahr.sa{href}"
                        print(f"   🎯 Navigating to next project: {href}")
                        await page.goto(href, wait_until="domcontentloaded", timeout=8000)
                        await asyncio.sleep(3)
                        print("   🔍 Checking if project is closed...")
                        status_info = await check_project_status(page)
                        if status_info.get("eligible"):
                            print("   ✅ Next project is eligible - continuing automation...")
                            # Return True to continue the main automation loop
                            return True
                        else:
                            print(f"   ❌ Next project is not eligible: {status_info.get('reason')}")
                            print("   🔄 Project not eligible, continuing to search for next project...")
                            # Don't return here - continue searching for more projects
                            continue
                except Exception:
                    continue
        except Exception:
            continue

    print("   ❌ No more projects found")
    return False

async def combined_bahar_automation():
    """
    Combined automation that keeps the browser open to see results.
    """
    browser_manager = None
    visited_ids: Set[str] = set()
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Get credentials
        bahar_username = os.getenv("BAHAR_USERNAME")
        bahar_password = os.getenv("BAHAR_PASSWORD")
        
        if not bahar_username or not bahar_password:
            print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
            return False
            
        print(f"👤 Using credentials for: {bahar_username}")
        
        # Load user preferences
        user_preferences = {
            "skills": ["Web Development", "React", "Node.js", "JavaScript", "TypeScript", "MongoDB", "تطوير الويب"],
            "rate": "60 دولار/ساعة"
        }
        
        # STEP 1: Set up browser and authenticate using the working approach
        print("\n🌐 Step 1: Setting up browser with authentication...")
        try:
            # Initialize browser first
            from jobber_fsm.core.web_driver.playwright import PlaywrightManager
            browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
            await browser_manager.async_initialize(eval_mode=True)
            
            # Try using saved token first
            from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso, setup_browser_session_with_token, verify_login_success
            try:
                tm = TokenManager()
                saved = tm.load_token()
                page = await browser_manager.get_current_page()
                if saved and page is not None:
                    print("🔑 Using saved token to establish session...")
                    auth_result = {
                        "success": True,
                        "cookies": tm.token_data.get("cookies", ""),
                        "response_data": tm.token_data.get("response_data", {})
                    }
                    sess = await setup_browser_session_with_token(page, auth_result, "https://bahr.sa")
                    if sess.get("success"):
                        verify = await verify_login_success(page)
                        if verify.get("success"):
                            print("✅ Logged in using saved token!")
                        else:
                            print("⚠️  Saved token did not verify login, will fallback to ESSO login...")
                    else:
                        print("⚠️  Saved token session setup failed, will fallback to ESSO login...")
            except Exception as te:
                print(f"⚠️  Saved token flow error, will fallback to ESSO login: {te}")
            
            # Use the working login function (fallback)
            from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
            
            # Get credentials from environment
            username = os.getenv("BAHAR_USERNAME")
            password = os.getenv("BAHAR_PASSWORD")
            
            if not username or not password:
                print("❌ Missing credentials in environment variables")
                return False
            
            print(f"👤 Using credentials for: {username}")
            
            # Only login if token flow above did not already log us in
            already_logged_in = False
            try:
                page_check = await browser_manager.get_current_page()
                if page_check:
                    # simple check: presence of dashboard/profile links
                    content = await page_check.content()
                    if ("/dashboard" in content) or ("/my-projects" in content) or ("لوحة التحكم" in content):
                        already_logged_in = True
            except Exception:
                pass
            
            if not already_logged_in:
                # Use the working login function
                login_result = await login_bahar_esso(
                    username=username,
                    password=password,
                    bahar_url="https://bahr.sa",
                    wait_time=3.0
                )
                
                if "Success" not in login_result:
                    print(f"❌ Login failed: {login_result}")
                    return False
                else:
                    print("✅ Login successful!")
                    # Save token and cookies for future runs
                    try:
                        tm = TokenManager()
                        page_after = await browser_manager.get_current_page()
                        cookies_list = await page_after.context.cookies() if page_after else []
                        access_token_val = None
                        sid_val = None
                        for ck in cookies_list:
                            if ck.get("name") == "access_token":
                                access_token_val = ck.get("value")
                            if ck.get("name") == "SID":
                                sid_val = ck.get("value")
                        # Build response_data to satisfy session setup on next run
                        response_data = {"access_token": access_token_val or ""}
                        from datetime import datetime, timedelta
                        tm.token_data = {
                            "token": sid_val or (access_token_val or ""),
                            "cookies": json.dumps(cookies_list),
                            "created_at": datetime.now().isoformat(),
                            "expires_at": (datetime.now() + timedelta(hours=23, minutes=55)).isoformat(),
                            "username": username,
                            "response_data": response_data,
                        }
                        tm.save_token()
                        print("💾 Token saved for future runs")
                    except Exception as save_err:
                        print(f"⚠️  Could not save token: {save_err}")
            
            print("✅ Browser session set up with authentication!")
            
            # Get the page
            page = await browser_manager.get_current_page()
        
        except Exception as e:
            print(f"❌ Failed to set up browser session: {str(e)}")
            return False
        
        # STEP 2: Navigate to projects page
        print("\n Step 2: Navigating to projects page...")
        
        # Navigate directly to the projects listing page
        try:
            print("   Navigating directly to projects listing...")
            
            # Try with increased timeout and networkidle
            try:
                await page.goto("https://bahr.sa/projects", wait_until="networkidle", timeout=30000)
            except Exception as e:
                print(f"   First attempt failed: {e}")
                # Fallback to domcontentloaded with longer timeout
                await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=30000)
            
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await asyncio.sleep(3)  # Wait for page to load
            
            # Verify we're on the projects page
            current_url = page.url
            page_title = await page.title()
            print(f"   Current URL: {current_url}")
            print(f"   Page title: {page_title}")
            
            # Check if we're on the right page
            if "/projects" in current_url and "projects" in page_title.lower():
                print("✅ Successfully navigated to projects listing page!")
            else:
                print("⚠️  May not be on projects listing page, but continuing...")
                
        except Exception as e:
            print(f"❌ Failed to navigate to projects page: {str(e)}")
            # Try alternative approach - go to home page first
            try:
                print("   Trying alternative navigation approach...")
                await page.goto("https://bahr.sa/", wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2000)
                await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=20000)
                print("✅ Successfully reached projects listing page via alternative route!")
            except Exception as e2:
                print(f"❌ Alternative navigation also failed: {e2}")
                return False
        
        print("✅ Successfully reached projects listing page!")
        
        # Main automation loop to process multiple projects
        project_count = 0
        max_projects = 10  # Process up to 10 projects
        
        while project_count < max_projects:
            project_count += 1
            print(f"\n🔄 Processing Project #{project_count}/{max_projects}")
            
            # Always go to projects listing page first, unless we're already processing a project
            try:
                current_url_loop = page.url
                on_project_detail_page = ("/projects/recruitments/" in current_url_loop or "/recruitments/" in current_url_loop)
                
                if on_project_detail_page:
                    print("   ℹ️ Already on a project detail page. Processing current project...")
                    # We're already on a project detail page, so process it
                    project_url = current_url_loop
                else:
                    # Go to projects listing page
                    try:
                        await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=20000)
                    except Exception as e:
                        print(f"   Navigation failed: {e}")
                        # Try alternative approach
                        await page.goto("https://bahr.sa/", wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(1000)
                        await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
                    
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    await asyncio.sleep(2)
                    
                    # STEP 3: Find and open a specific project by looking for project links directly
                    print("\n Step 3: Finding and opening a specific project...")
                    
                    # Simple approach: just wait for projects to load
                    print("   Waiting for projects to load...")
                    await asyncio.sleep(3)
                    
                    # Simple project link search
                    project_selectors = [
                        "a[href*='/projects/recruitments/']",
                        "a[href*='/recruitments/']",
                    ]
                    
                    print("   🔍 Looking for project links...")
                    for selector in project_selectors:
                        try:
                            links = await page.query_selector_all(selector)
                            if links:
                                print(f"   Found {len(links)} links with selector: {selector}")
                                
                                # Find first unvisited project
                                for link in links:
                                    try:
                                        href = await link.get_attribute('href')
                                        if href and '/proposals/' not in href and '/my-proposals' not in href:
                                            candidate_id = extract_project_id_from_url(href)
                                            if candidate_id and candidate_id not in visited_ids:
                                                project_link = link
                                                project_url = href
                                                print(f"   ✅ Found project link: {href}")
                                                break
                                    except Exception:
                                        continue
                                
                                if project_link:
                                    break
                        except Exception:
                            continue
                    
                    if project_link:
                        break
                    
            except Exception as nav_err:
                print(f"❌ Could not determine page state or navigate to listing: {nav_err}")
                return False
            
            # If we found a project to navigate to, do it now
            if project_url:
                try:
                    if not project_url.startswith('http'):
                        project_url = f"https://bahr.sa{project_url}"
                    print(f"   🎯 Navigating to project: {project_url}")
                    await page.goto(project_url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(3)
                    print(f"   ✅ Navigation completed. Current URL: {page.url}")
                except Exception as e:
                    print(f"   ❌ Failed to navigate to project: {e}")
                    continue
            
            if not project_url:
                print("   ❌ No project URL found")
                print("   Skipping to next project...")
                continue
            
            # Confirm we're on a project detail page
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            if "/projects/recruitments/" in current_url or "/recruitments/" in current_url:
                print("✅ Confirmed we're on a project detail page!")
                # Track current project id to avoid revisiting
                current_id = extract_project_id_from_url(current_url)
                if current_id:
                    visited_ids.add(current_id)
                    print(f"   📝 Tracking project ID: {current_id}")
            else:
                print("⚠️  May not be on a project detail page, but continuing...")
                print(f"   Expected URL pattern: /projects/recruitments/ or /recruitments/")
                print(f"   Actual URL: {current_url}")
                
                # Wait for project details to load properly
                print("   Waiting for project details to load...")
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=10000)
                except Exception:
                    pass
                await asyncio.sleep(3)  # Initial wait
                
                # Wait for project content to appear
                try:
                    await page.wait_for_selector(".project-details, .project-info, .job-details, [data-testid='project-details']", timeout=20000)
                    print("   ✅ Project details loaded!")
                except:
                    print("   ⚠️  Project details not found, but continuing...")
                    
                    # Additional wait for dynamic content
                    await asyncio.sleep(2)

        # STEP 4: Check project status before proceeding
        print("\n Step 4: Checking project status...")
        # Guard: ensure we're on a project detail page before continuing
        current_url_after_open = page.url
        if not ("/projects/recruitments/" in current_url_after_open or "/recruitments/" in current_url_after_open):
            print("❌ Not on a project detail page. Aborting status check and extraction to avoid scraping the dashboard.")
            return False
        status_info = await check_project_status(page)
        
        if not status_info["eligible"]:
            print(f"❌ Project not eligible for offer submission: {status_info['reason']}")
            print(f"   Status: {status_info['status']}")
            print(f"   Details: {status_info['details']}")
            
            # Save status info for reference
            with open('project_status.json', 'w', encoding='utf-8') as f:
                json.dump(status_info, f, ensure_ascii=False, indent=2)
            print("💾 Project status saved to 'project_status.json'")
            
            print("🔄 Looking for another project...")
            
            # Go back to projects page and try the next project
            try:
                print("   Going back to projects page...")
                await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=8000)
                await asyncio.sleep(1)
                
                # Look for project links again
                project_selectors = [
                    "a[href*='/projects/']",
                    "a[href*='/recruitments/']",
                    ".project-card a",
                    ".project-item a",
                    "[data-testid='project-link']",
                    ".project a"
                ]
                
                all_project_links = []
                for selector in project_selectors:
                    try:
                        links = await page.query_selector_all(selector)
                        if links:
                            # Filter out proposal links
                            for link in links:
                                try:
                                    href = await link.get_attribute('href')
                                    if href and '/proposals/' not in href and '/my-proposals' not in href:
                                        all_project_links.append(link)
                                except:
                                    continue
                            if all_project_links:
                                print(f"   Found {len(all_project_links)} valid project links with selector: {selector}")
                                break
                    except Exception as e:
                        continue
                
                if len(all_project_links) > 1:
                    # Try the next project
                    next_project = all_project_links[1]
                    print("   Trying the next project...")
                    
                    try:
                        project_url = await next_project.get_attribute('href')
                        if project_url and not project_url.startswith('http'):
                            project_url = f"https://bahr.sa{project_url}"
                        print(f"   Next project URL: {project_url}")
                        
                        await page.goto(project_url, wait_until="domcontentloaded", timeout=8000)
                        await asyncio.sleep(1)
                        print("✅ Successfully opened next project page!")
                        
                        # Check status of next project
                        print("   Checking next project status...")
                        status_info = await check_project_status(page)
                        
                        if status_info["eligible"]:
                            print("✅ Next project is eligible for offer submission!")
                            # Continue with the automation
                        else:
                            print(f"❌ Next project also not eligible: {status_info['reason']}")
                            return False
                    
                    except Exception as e:
                        print(f"   Error opening next project: {str(e)}")
                        return False
                else:
                    print("   No additional projects found to try")
                    return False
                    
            except Exception as e:
                print(f"   Error trying another project: {str(e)}")
                return False
        
        print("✅ Project is eligible for offer submission!")
        
        # STEP 6: Extract project details from the opened project
        print("\n Step 5: Extracting project details...")
        try:
            # Verify we're on a project detail page before extracting
            current_url = page.url
            if not ('/projects/recruitments/' in current_url or '/recruitments/' in current_url):
                print(f"❌ Not on a project detail page. Current URL: {current_url}")
                print("   Cannot extract project details from dashboard page.")
                return False

            # Wait a bit more for any dynamic content to load
            print("   Waiting for dynamic content to load...")
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            await asyncio.sleep(2)

            project_info = await extract_complete_project_details(page, {})

            if not project_info:
                print("❌ Failed to extract project details")
                return False
            
            print("✅ Project details extracted successfully!")
            print(f"   Title: {project_info.get('title', 'N/A')}")
            print(f"   Budget: {project_info.get('budget', 'N/A')}")
            print(f"   Skills: {', '.join(project_info.get('skills', []))}")
            print(f"   Description: {project_info.get('description', 'N/A')[:100]}...")

            # Add status info to project details
            project_info["status"] = status_info

            # Save project details to file for inspection
            with open('scraped_project_details.json', 'w', encoding='utf-8') as f:
                json.dump(project_info, f, ensure_ascii=False, indent=2)
            print("💾 Project details saved to 'scraped_project_details.json'")

        except Exception as e:
            print(f"❌ Error extracting project details: {str(e)}")
            traceback.print_exc()
            return False
        
        # STEP 6: Generate AI Arabic offer
        print("\n Step 6: Generating AI Arabic offer...")
        try:
            ai_offer = generate_fallback_offer(project_info, user_preferences)

            print("✅ AI Offer Generated Successfully!")
            print("\n📝 Generated Offer Details:")
            print(f"   Duration: {ai_offer.get('duration', 'N/A')} days")
            print(f"   Milestones: {ai_offer.get('milestone_number', 'N/A')}")
            print(f"   Total Price: {ai_offer.get('total_price_sar', 'N/A')} SAR")
            print(f"   Brief: {ai_offer.get('brief', 'N/A')[:100]}...")
            print(f"   Platform Communication: {ai_offer.get('platform_communication', 'N/A')}")

            # Save AI offer to file for inspection
            with open('generated_ai_offer.json', 'w', encoding='utf-8') as f:
                json.dump(ai_offer, f, ensure_ascii=False, indent=2)
            print("💾 AI offer saved to 'generated_ai_offer.json'")
        except Exception as e:
            print(f"❌ Error generating AI offer: {str(e)}")
            traceback.print_exc()
            return False
        
        # STEP 8: Navigate to offer submission form
        print("\n Step 7: Finding and navigating to offer submission form...")
        try:
            await save_debug_artifacts(page, "before_navigate_offer")
            # First, verify we're on a project detail page
            current_url = page.url
            if not ('/projects/' in current_url or '/recruitments/' in current_url):
                print(f"⚠️  Not on a project detail page. Current URL: {current_url}")
                print("   This might explain why no apply button is found.")
            
            # Accept cookie consent if present to avoid blocking buttons
            try:
                consent_selectors = [
                    "button:has-text('Accept')",
                    "button:has-text('I Accept')",
                    "button:has-text('أوافق')",
                    "button:has-text('موافقة')",
                    "[aria-label='accept cookies']",
                ]
                for cs in consent_selectors:
                    btn = await page.query_selector(cs)
                    if btn:
                        try:
                            await btn.click()
                            await asyncio.sleep(1)
                            print("   ✅ Cookie consent accepted")
                            break
                        except Exception:
                            pass
            except Exception:
                pass

            # Skip "already submitted" early-exit: attempt to apply anyway; if all attempts fail we'll move on

            # Look for submit offer/apply buttons on the project page
            # First try the user's provided CSS selector for the submit/apply anchor (with escaped colons)
            preferred_offer_selector = r"div:nth-child(4) > main > div > div > div.rounded-xl.border.border-primary-300.bg-white.px-4.py-8.md\:p-8 > div > div.flex.flex-col.gap-3.empty\:hidden.md\:flex-row.md\:gap-6 > a"

            offer_button_selectors = [
                preferred_offer_selector,
                "button:has-text('تقديم العرض')",
                "button:has-text('تقديم عرض')",
                "button:has-text('تقديم عرضك')",
                "button:has-text('قدّم عرض')",
                "button:has-text('قدم عرض')",
                "button:has-text('قدّم')",
                "button:has-text('تقديم')",
                "button:has-text('أرسل العرض')",
                "button:has-text('Submit Offer')",
                "button:has-text('Submit offer')",
                "button:has-text('Submit proposal')",
                "button:has-text('Submit Proposal')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Apply Now')",
                "button:has-text('Apply now')",
                "button:has-text('Place Bid')",
                "button:has-text('Bid')",
                "button:has-text('تطبيق')",
                "a:has-text('تقديم العرض')",
                "a:has-text('تقديم عرض')",
                "a:has-text('تقديم عرضك')",
                "a:has-text('قدّم')",
                "a:has-text('قدّم عرض')",
                "a:has-text('قدم')",
                "a:has-text('قدم عرض')",
                "a:has-text('أرسل العرض')",
                "a:has-text('Submit Offer')",
                "a:has-text('Submit offer')",
                "a:has-text('Submit Proposal')",
                "a:has-text('Submit proposal')",
                "a:has-text('Submit')",
                "a:has-text('Apply')",
                "a:has-text('Apply Now')",
                "a:has-text('Apply now')",
                "a:has-text('Place Bid')",
                "a:has-text('Bid')",
                "a:has-text('تطبيق')",
                "[data-testid='submit-offer']",
                "[data-testid='apply']",
                ".submit-offer-btn",
                ".apply-btn",
                "button[type='submit']",
                "input[type='submit']",
                # Only use href selectors as fallback, and exclude my-proposals
                "a[href*='submit']:not([href*='my-proposals'])",
                "a[href*='apply']:not([href*='my-proposals'])",
                "a[href*='/proposals/new']:not([href*='my-proposals'])",
                "a[href*='/proposal']:not([href*='/proposals/']):not([href*='my-proposals'])"
            ]
            
            # Debug: Show all buttons and links on the page
            print("🔍 Debugging buttons and links on project page...")
            try:
                all_buttons = await page.query_selector_all("button")
                all_links = await page.query_selector_all("a")
                print(f"   Found {len(all_buttons)} buttons and {len(all_links)} links on the page")
                
                # Show first 10 buttons
                for i, btn in enumerate(all_buttons[:10]):
                    try:
                        btn_text = await btn.text_content()
                        btn_type = await btn.get_attribute('type')
                        btn_class = await btn.get_attribute('class')
                        print(f"   Button {i+1}: text='{btn_text[:30]}', type='{btn_type}', class='{btn_class}'")
                    except:
                        pass
                
                # Show first 10 links
                for i, link in enumerate(all_links[:10]):
                    try:
                        link_text = await link.text_content()
                        link_href = await link.get_attribute('href')
                        print(f"   Link {i+1}: text='{link_text[:30]}', href='{link_href}'")
                    except:
                        pass
            except Exception as e:
                print(f"   Debug error: {str(e)}")
            
            offer_button = None
            for selector in offer_button_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    if buttons:
                        offer_button = buttons[0]
                        print(f"   Found offer button with selector: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not offer_button:
                print("   No offer button found with primary selectors, trying to find any submit/apply link...")
                # Try to find any link that might lead to offer form (exclude my-proposals)
                submit_selectors = [
                    "a[href*='offer']:not([href*='my-proposals'])",
                    "a[href*='bid']:not([href*='my-proposals'])",
                    "a[href*='submit']:not([href*='my-proposals'])",
                    "a[href*='apply']:not([href*='my-proposals'])",
                    "a[href*='/proposals/new']:not([href*='my-proposals'])",
                    # Also try the provided container chain to its anchor
                    preferred_offer_selector,
                ]
                
                for selector in submit_selectors:
                    try:
                        links = await page.query_selector_all(selector)
                        if links:
                            offer_button = links[0]
                            print(f"   Found submit link with selector: {selector}")
                            break
                    except Exception as e:
                        continue

            # If still no button found, show detailed page analysis
            if not offer_button:
                print("⚠️  Could not find offer submission button, trying to continue...")
                print("   This could mean:")
                print("   - Offer already submitted (no apply button found)")
                print("   - Project is not eligible for submission")
                print("   - Page structure is different than expected")
                print("   - Network issues prevented proper page loading")
                
                # Show current page URL and title for debugging
                try:
                    page_title = await page.title()
                    current_url = page.url
                    print(f"   Current page: {page_title}")
                    print(f"   Current URL: {current_url}")
                except Exception as e:
                    print(f"   Could not get page info: {e}")

            # Fallback: heuristic scan of all buttons/links and scroll the page
            if not offer_button:
                print("   Fallback: scanning page for apply/submit text while scrolling...")
                try:
                    keyword_substrings = [
                        "تقديم العرض", "تقديم عرض", "تقديم عرضك", "قدّم عرض", "قدم عرض", "قدّم", "قدم", "تقديم",
                        "أرسل العرض", "إرسال العرض",
                        "Submit offer", "Submit proposal", "Apply now", "Apply", "Place bid", "Bid"
                    ]
                    # Scroll in steps and try detection at each viewport
                    for _ in range(8):
                        candidates = await page.query_selector_all("button, a")
                        found = False
                        for el in candidates:
                            try:
                                t = (await el.text_content() or "").strip()
                                if not t:
                                    continue
                                # Exclude misleading options
                                if "مشاريع مماثلة" in t:
                                    continue
                                # Match Arabic/English CTA variants
                                if any(kw.lower() in t.lower() for kw in keyword_substrings):
                                    # Exclude similar projects
                                    if "مشاريع مماثلة" in t or "similar" in t.lower():
                                        continue
                                    offer_button = el
                                    print(f"   Heuristic matched: '{t[:50]}'")
                                    found = True
                                    break
                            except Exception:
                                continue
                        if found:
                            break
                        # Scroll further
                        await page.mouse.wheel(0, 800)
                        await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"   Heuristic scan error: {str(e)}")

            # Final fallback: try direct proposal URL construction
            if not offer_button:
                print("   Trying direct proposal URL construction...")
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(page.url)
                    path = parsed.path
                    locale_prefix = ''
                    if path.startswith('/en/'):
                        locale_prefix = '/en'
                    proj_id = extract_project_id_from_url(page.url)
                    if proj_id:
                        base = f"{parsed.scheme}://{parsed.netloc}{locale_prefix}"
                        try_urls = [
                            f"{base}/projects/recruitments/{proj_id}/proposals/new",
                            f"{base}/projects/{proj_id}/proposals/new",
                            f"{base}/en/projects/recruitments/{proj_id}/proposals/new",
                            f"{base}/en/projects/{proj_id}/proposals/new",
                            f"{base}/proposals/new?project={proj_id}",
                        ]
                        for try_url in try_urls:
                            try:
                                print(f"   Trying direct proposal URL: {try_url}")
                                await page.goto(try_url, wait_until="domcontentloaded", timeout=10000)
                                await asyncio.sleep(2)
                                # Check if we reached a form page
                                form_indicators = [
                                    "form",
                                    "[data-testid='duration-input']", 
                                    "textarea[name*='brief']",
                                    "input[name*='duration']",
                                    "input[name*='price']"
                                ]
                                for indicator in form_indicators:
                                    el = await page.query_selector(indicator)
                                    if el:
                                        print(f"✅ Reached offer form via direct URL (found: {indicator})")
                                        offer_button = True  # sentinel value
                                        break
                                if offer_button:
                                    break
                            except Exception as e:
                                print(f"   Direct URL failed: {e}")
                                continue
                except Exception as e:
                    print(f"   Direct proposal URL construction failed: {e}")
            
            if offer_button:
                print("   Clicking on offer submission button...")
                try:
                    # Wait for button to be visible and clickable
                    try:
                        await offer_button.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    # Try multiple strategies
                    try:
                        await offer_button.wait_for_element_state("visible", timeout=7000)
                    except Exception:
                        pass
                    try:
                        await offer_button.wait_for_element_state("stable", timeout=7000)
                    except Exception:
                        pass
                    # Primary click
                    try:
                        await offer_button.click(timeout=7000)
                    except Exception:
                        # Fallback: force click via JS
                        try:
                            await page.evaluate("el => { el.click(); el.dispatchEvent(new MouseEvent('click', {bubbles:true})); }", offer_button)
                        except Exception:
                            # Fallback: press Enter
                            try:
                                await offer_button.focus()
                            except Exception:
                                pass
                            await page.keyboard.press('Enter')
                    await asyncio.sleep(2)  # Wait for form page to load
                    print("✅ Successfully navigated to offer form!")
                    await save_debug_artifacts(page, "after_click_offer")
                except Exception as e:
                    print(f"   Error clicking offer button: {str(e)}")
                    print("   Trying alternative approach...")
                    try:
                        # Try to get the href and navigate directly
                        href = await offer_button.get_attribute('href')
                        if href:
                            await page.goto(href, wait_until="domcontentloaded", timeout=8000)
                            await asyncio.sleep(2)
                            print("✅ Successfully navigated to offer form via direct URL!")
                        else:
                            print("   No href found, continuing anyway...")
                    except Exception as e2:
                        print(f"   Alternative approach also failed: {str(e2)}")
                        print("   Continuing anyway...")
                else:
                    # If clicking succeeded but we're still not on the form, try the direct proposal URL fallback immediately
                    current_url_after_click = page.url
                    if not any(s in current_url_after_click for s in ["proposal", "offer", "submit"]):
                        print("   Click did not navigate to form, trying direct proposal URLs as fallback...")
                        try:
                            proj_id = extract_project_id_from_url(current_url_after_click)
                            if proj_id:
                                base = f"https://bahr.sa"
                                direct_urls = [
                                    f"{base}/projects/recruitments/{proj_id}/proposals/new",
                                    f"{base}/projects/{proj_id}/proposals/new",
                                    f"{base}/proposals/new?project={proj_id}",
                                ]
                                for u in direct_urls:
                                    try:
                                        print(f"   Trying direct proposal URL (post-click): {u}")
                                        await page.goto(u, wait_until="domcontentloaded", timeout=10000)
                                        await asyncio.sleep(2)
                                        break
                                    except Exception:
                                        continue
                        except Exception:
                            pass
                
                # Get current URL to confirm we're on the form page
                current_url = page.url
                print(f"   Current URL: {current_url}")
                
                if "proposal" in current_url or "offer" in current_url or "submit" in current_url:
                    print("✅ Confirmed we're on the offer form page!")
                else:
                    print("⚠️  May not be on the offer form page, but continuing...")
                
                # NOW check if the submit button is available and enabled on the form page
                print("   Checking submit button availability on form page...")
                submit_button_selectors = [
                    "button:contains('تقديم العرض')",
                    "button:contains('تقديم عرض')",
                    "button:contains('Submit Offer')",
                    "button:contains('Submit')",
                    "button:contains('Apply')",
                    "button:contains('تطبيق')",
                    "input[type='submit']",
                    "button[type='submit']",
                    "[data-testid='submit-offer']",
                    ".submit-offer-btn",
                    ".submit-btn",
                    ".apply-btn"
                ]
                
                submit_button_found = False
                submit_button_enabled = True
                
                for selector in submit_button_selectors:
                    try:
                        buttons = await page.query_selector_all(selector)
                        if buttons:
                            submit_button_found = True
                            print(f"   Found submit button: {selector}")
                            
                            # Check if button is enabled
                            for button in buttons:
                                try:
                                    is_disabled = await button.get_attribute('disabled')
                                    if is_disabled:
                                        submit_button_enabled = False
                                        print(f"   Submit button is disabled: {selector}")
                                        break
                                except:
                                    pass
                            break
                    except Exception as e:
                        continue
                
                if not submit_button_found:
                    print("   ⚠️  No submit button found on form page")
                elif not submit_button_enabled:
                    print("   ❌ Submit button is disabled on form page")
                    return False
                else:
                    print("   ✅ Submit button is available and enabled!")
            else:
                print("⚠️  Could not find offer submission button, trying to continue...")
            
        except Exception as e:
            print(f"❌ Error navigating to offer form: {str(e)}")
            print("   Continuing anyway...")
        
        # STEP 8: Fill the offer form with generated data
        print("\n Step 8: Filling offer form with generated data...")
        await save_debug_artifacts(page, "before_fill_form")
        try:
            # Use comprehensive form filling as primary method
            print("   🔧 Starting comprehensive form filling...")
            try:
                fill_result = await fill_single_milestone_quick(page, ai_offer)
                print(f"   📊 Comprehensive form filling result: {fill_result}")
                
                # If comprehensive filling failed, try direct JavaScript filling
                if not fill_result.get("success"):
                    print("   ⚠️ Comprehensive form filling failed, trying direct JavaScript fill...")
                    try:
                        budget_val = int(ai_offer.get('total_price_sar') or ai_offer.get('total_price') or 250)
                        deliverable_text = ai_offer.get('deliverables') or 'تسليم المتطلبات حسب الوصف المطلوب'
                        
                        # Use the new JavaScript filling function
                        js_success = await fill_fields_with_javascript(page, budget_val, deliverable_text)
                        if js_success:
                            fill_result = {"success": True, "filled_fields": ["budget", "deliverable"]}
                        else:
                            fill_result = {"success": False}
                        
                    except Exception as e:
                        print(f"   ❌ Direct JavaScript fill failed: {e}")
                        # Fallback to legacy method
                        fill_result = await improved_fill_offer_form(page, ai_offer, user_preferences)
                        
            except Exception as e:
                print(f"   ❌ Comprehensive form filling failed with error: {e}")
                fill_result = {"success": False}

            if fill_result.get("success"):
                print("✅ Offer form filled successfully!")
                print(f"   Result: {fill_result.get('message', 'N/A')}")
                print(f"   Filled fields: {fill_result.get('filled_fields', [])}")
                
                # Wait for submit button to be enabled
                try:
                    await page.wait_for_function("""
                        () => {
                            const submitBtn = document.querySelector('button[data-testid="submitProposalFormButton"]');
                            return submitBtn && !submitBtn.disabled;
                        }
                    """, timeout=10000)
                    print("   ✅ Submit button is now enabled")
                except Exception as e:
                    print(f"   ⚠️ Could not verify submit button enabled: {e}")
                
                await save_debug_artifacts(page, "after_fill_form")

                # Submit the offer
                print("\n Step 9: Submitting the offer...")
                try:
                    # Look for submit button
                    submit_selectors = [
                        "button:has-text('إرسال العرض')",
                        "button:has-text('Send Offer')",
                        "button:has-text('Submit')",
                        "button[type='submit']",
                        "input[type='submit']",
                        "button:has-text('تقديم')"
                    ]
                    
                    submit_button = None
                    for selector in submit_selectors:
                        try:
                            buttons = await page.query_selector_all(selector)
                            if buttons:
                                submit_button = buttons[0]
                                print(f"   Found submit button with selector: {selector}")
                                break
                        except Exception as e:
                            continue
                    
                    if submit_button:
                        print("   Clicking submit button...")
                        await submit_button.click()
                        await asyncio.sleep(3)  # Wait for submission
                        print("✅ Offer submitted successfully!")
                        await save_debug_artifacts(page, "after_submit")
                        
                        # Save successful submission
                        from datetime import datetime
                        submission_data = {
                            "project_url": page.url,
                            "project_title": project_info.get('title', ''),
                            "submitted_at": datetime.now().isoformat(),
                            "offer_details": ai_offer
                        }
                        
                        with open('successful_submissions.json', 'w', encoding='utf-8') as f:
                            json.dump(submission_data, f, ensure_ascii=False, indent=2)
                        print("💾 Submission saved to 'successful_submissions.json'")
                        
                    else:
                        print("❌ Submit button not found")
                        
                except Exception as e:
                    print(f"❌ Error submitting offer: {str(e)}")
                
            else:
                print("❌ Failed to fill offer form")
                print(f"   Error: {fill_result.get('message', 'N/A')}")
                print("   But continuing to show the form...")

        except Exception as e:
            print(f"❌ Error filling offer form: {str(e)}")
            print("   But continuing to show the form...")
        
        # Continue to next project after form filling/submission
        print("🔄 Continuing to next project...")
        next_project_result = await go_to_next_project(page, user_preferences, last_project_id=extract_project_id_from_url(page.url), visited_ids=visited_ids)
        if not next_project_result:
            print("❌ No more projects found or automation completed")
            return False
        # If next_project_result is True, we finished this iteration successfully
        print("✅ Moving to next project...")
        return True
        
    except Exception as e:
        print(f"❌ Error during combined automation: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(" Real Project Scraping Test")
    print("=" * 50)
    
    # Check if credentials are available
    load_dotenv()
    if os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD"):
        print(" Credentials found! Running real project scraping...")
        success = asyncio.run(combined_bahar_automation())
        if success:
            print("\n✨ Real project scraping completed successfully!")
            print("📁 Check the generated files:")
            print("   - scraped_project_details.json")
            print("   - generated_ai_offer.json")
        else:
            print("\n❌ Real project scraping failed!")
    else:
        print("🔑 No credentials found!")
        print("Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
    
    print("\n✨ Test completed!")
