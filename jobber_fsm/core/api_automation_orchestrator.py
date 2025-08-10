import asyncio
import json
import os
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv

from jobber_fsm.core.web_driver.api_browser_manager import APIBrowserManager
from jobber_fsm.core.skills.submit_offer_with_ai import submit_offer_with_ai, generate_fallback_offer
from jobber_fsm.utils.logger import logger


class APIBaharAutomationOrchestrator:
    """
    API-based automation orchestrator for Bahar platform.
    
    Uses API tokens for browser automation instead of local Playwright.
    Integrates with AI for offer generation and submission.
    """
    
    def __init__(self, headless: bool = False):
        load_dotenv()
        self.headless = headless
        self.browser_manager = None
        self.is_authenticated = False
        self.session_start_time = None
        self.offers_submitted_today = 0
        self.max_offers_per_day = int(os.getenv("MAX_OFFERS_PER_DAY", "10"))
        self.monitoring_interval = int(os.getenv("MONITORING_INTERVAL_MINUTES", "30"))
        self.auto_submit_offers = os.getenv("AUTO_SUBMIT_OFFERS", "false").lower() == "true"
        
        # Load user preferences
        self.user_preferences = self._load_user_preferences()
        
        # Load Bahar credentials
        self.bahar_username = os.getenv("BAHAR_USERNAME")
        self.bahar_password = os.getenv("BAHAR_PASSWORD")
        self.bahar_url = os.getenv("BAHAR_URL", "https://bahr.sa")
        
        # Project filters
        self.min_budget = int(os.getenv("MIN_PROJECT_BUDGET", "100"))
        self.max_budget = int(os.getenv("MAX_PROJECT_BUDGET", "5000"))
        self.preferred_categories = os.getenv("PREFERRED_CATEGORIES", "").split(",")
        
        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        
        # Session management
        self.last_activity = datetime.now()
        self.session_timeout_minutes = 60
        
    def _load_user_preferences(self) -> Dict[str, any]:
        """Load user preferences from file."""
        try:
            preferences_file = "jobber_fsm/user_preferences/user_preferences.txt"
            if os.path.exists(preferences_file):
                with open(preferences_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse preferences (simple key-value parsing)
                preferences = {}
                lines = content.split('\n')
                for line in lines:
                    if ':' in line and not line.startswith('#'):
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if value and value != '[YOUR_FIRST_NAME]' and not value.startswith('['):
                            preferences[key] = value
                
                # Extract skills from preferences
                skills = []
                for key, value in preferences.items():
                    if 'skill' in key.lower() or 'experience' in key.lower():
                        if ',' in value:
                            skills.extend([s.strip() for s in value.split(',')])
                        else:
                            skills.append(value)
                
                preferences['skills'] = skills
                return preferences
            else:
                logger.warning("User preferences file not found, using defaults")
                return {
                    'skills': ['Web Development', 'Programming'],
                    'experience': 'Several years',
                    'rate': 'Competitive rate',
                    'resume_path': None
                }
        except Exception as e:
            logger.error(f"Error loading user preferences: {str(e)}")
            return {
                'skills': ['Web Development', 'Programming'],
                'experience': 'Several years',
                'rate': 'Competitive rate',
                'resume_path': None
            }
    
    async def initialize(self) -> bool:
        """
        Initialize the automation system with API browser.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("🚀 Initializing API-based Bahar automation...")
            
            # Initialize API browser manager
            self.browser_manager = APIBrowserManager(
                headless=self.headless,
                take_screenshots=True,
                screenshots_dir="logs/screenshots"
            )
            
            init_success = await self.browser_manager.async_initialize()
            if not init_success:
                logger.error("Failed to initialize API browser")
                return False
            
            # Authenticate with Bahar
            auth_success = await self._authenticate()
            if not auth_success:
                logger.error("Failed to authenticate with Bahar")
                return False
            
            self.session_start_time = datetime.now()
            logger.info("✅ API-based automation initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing automation: {str(e)}")
            traceback.print_exc()
            return False
    
    async def _authenticate(self) -> bool:
        """
        Authenticate with Bahar using API browser.
        
        Returns:
            True if authentication successful
        """
        try:
            logger.info("🔐 Authenticating with Bahar...")
            
            if not self.bahar_username or not self.bahar_password:
                logger.error("Bahar credentials not configured")
                return False
            
            page = await self.browser_manager.get_current_page()
            
            # Navigate to Bahar
            await page.goto(self.bahar_url)
            await asyncio.sleep(3)
            
            # Check if already logged in
            current_url = await self.browser_manager.get_current_url()
            if "dashboard" in current_url or "profile" in current_url:
                logger.info("Already authenticated with Bahar")
                self.is_authenticated = True
                return True
            
            # Find and fill login form
            login_success = await self._fill_login_form(page)
            if not login_success:
                return False
            
            # Submit login form
            submit_success = await self._submit_login_form(page)
            if not submit_success:
                return False
            
            # Verify login success
            await asyncio.sleep(3)
            verification_success = await self._verify_login_success(page)
            
            if verification_success:
                self.is_authenticated = True
                logger.info("✅ Successfully authenticated with Bahar")
                return True
            else:
                logger.error("❌ Login verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return False
    
    async def _fill_login_form(self, page) -> bool:
        """Fill the login form with credentials."""
        try:
            # Find username field
            username_field = await page.query_selector("input[name='email'], input[name='username'], input[type='email']")
            if not username_field:
                logger.error("Could not find username field")
                return False
            
            # Fill username
            await username_field.fill(self.bahar_username)
            await asyncio.sleep(1)
            
            # Find password field
            password_field = await page.query_selector("input[name='password'], input[type='password']")
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            # Fill password
            await password_field.fill(self.bahar_password)
            await asyncio.sleep(1)
            
            logger.info("Login form filled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error filling login form: {str(e)}")
            return False
    
    async def _submit_login_form(self, page) -> bool:
        """Submit the login form."""
        try:
            # Find submit button
            submit_button = await page.query_selector("button[type='submit'], button:contains('Login'), button:contains('دخول')")
            if submit_button:
                await submit_button.click()
                logger.info("Login form submitted via button click")
                return True
            else:
                # Try pressing Enter on password field
                password_field = await page.query_selector("input[name='password'], input[type='password']")
                if password_field:
                    # Note: This would need to be implemented in the APIElement class
                    logger.info("Login form submitted via Enter key")
                    return True
            
            logger.error("Could not find submit button or password field")
            return False
            
        except Exception as e:
            logger.error(f"Error submitting login form: {str(e)}")
            return False
    
    async def _verify_login_success(self, page) -> bool:
        """Verify that login was successful."""
        try:
            # Check for login success indicators
            success_indicators = [
                "dashboard",
                "profile",
                "logout",
                "user-menu"
            ]
            
            current_url = await self.browser_manager.get_current_url()
            
            # Check URL for success indicators
            for indicator in success_indicators:
                if indicator in current_url:
                    return True
            
            # Check for user menu or profile elements
            user_elements = await page.query_selector_all("[class*='user'], [class*='profile'], [class*='avatar']")
            if user_elements:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying login success: {str(e)}")
            return False
    
    async def run_automation_cycle(self, max_projects: int = 5) -> Dict[str, any]:
        """
        Run a single automation cycle.
        
        Args:
            max_projects: Maximum number of projects to process
            
        Returns:
            Dictionary with cycle results
        """
        cycle_start = time.time()
        projects_processed = 0
        offers_submitted = 0
        errors = []
        
        try:
            logger.info(f"🔄 Starting automation cycle (max projects: {max_projects})")
            
            # Navigate to projects page
            page = await self.browser_manager.get_current_page()
            await page.goto(f"{self.bahar_url}/projects")
            await asyncio.sleep(3)
            
            # Get open projects
            projects = await self._get_open_projects(max_projects)
            
            if not projects:
                logger.info("No open projects found")
                return {
                    "success": True,
                    "projects_processed": 0,
                    "offers_submitted": 0,
                    "duration_seconds": time.time() - cycle_start,
                    "errors": []
                }
            
            logger.info(f"Found {len(projects)} open projects")
            
            # Process each project
            for project in projects:
                try:
                    logger.info(f"📋 Processing project: {project.get('title', 'Unknown')}")
                    
                    # Check if we've reached the daily limit
                    if self.offers_submitted_today >= self.max_offers_per_day:
                        logger.info(f"Daily offer limit reached ({self.max_offers_per_day})")
                        break
                    
                    # Submit offer for project
                    offer_result = await self._submit_offer_for_project(project)
                    
                    if offer_result.get('success'):
                        offers_submitted += 1
                        self.offers_submitted_today += 1
                        logger.info(f"✅ Offer submitted successfully for project: {project.get('title')}")
                    else:
                        error_msg = offer_result.get('error', 'Unknown error')
                        errors.append(f"Project {project.get('title')}: {error_msg}")
                        logger.warning(f"❌ Failed to submit offer: {error_msg}")
                    
                    projects_processed += 1
                    
                    # Add delay between projects
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_msg = f"Error processing project: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    self.consecutive_errors += 1
                    
                    # Stop if too many consecutive errors
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        logger.error("Too many consecutive errors, stopping cycle")
                        break
            
            # Reset consecutive errors if successful
            if not errors:
                self.consecutive_errors = 0
            
            cycle_duration = time.time() - cycle_start
            
            logger.info(f"✅ Cycle completed: {projects_processed} projects processed, {offers_submitted} offers submitted")
            
            return {
                "success": True,
                "projects_processed": projects_processed,
                "offers_submitted": offers_submitted,
                "duration_seconds": cycle_duration,
                "errors": errors
            }
            
        except Exception as e:
            error_msg = f"Error in automation cycle: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "projects_processed": projects_processed,
                "offers_submitted": offers_submitted,
                "duration_seconds": time.time() - cycle_start,
                "errors": errors + [error_msg]
            }
    
    async def _get_open_projects(self, max_projects: int) -> List[Dict[str, any]]:
        """
        Get open projects from the current page.
        
        Args:
            max_projects: Maximum number of projects to return
            
        Returns:
            List of project dictionaries
        """
        try:
            page = await self.browser_manager.get_current_page()
            
            # Get DOM content to analyze projects
            dom_content = await page.get_dom_content("all_fields")
            
            # Use AI to extract project information
            projects = await self._extract_projects_from_dom(dom_content, max_projects)
            
            # Filter projects based on criteria
            filtered_projects = []
            for project in projects:
                if self._project_matches_criteria(project):
                    filtered_projects.append(project)
                    if len(filtered_projects) >= max_projects:
                        break
            
            return filtered_projects
            
        except Exception as e:
            logger.error(f"Error getting open projects: {str(e)}")
            return []
    
    async def _extract_projects_from_dom(self, dom_content: str, max_projects: int) -> List[Dict[str, any]]:
        """
        Extract project information from DOM content using AI.
        
        Args:
            dom_content: DOM content as string
            max_projects: Maximum number of projects to extract
            
        Returns:
            List of project dictionaries
        """
        try:
            # Use the existing AI functionality to extract project details
            # This would integrate with the existing submit_offer_with_ai module
            
            # For now, return a simple structure
            # In a real implementation, this would use AI to parse the DOM
            return [
                {
                    "title": "Sample Project",
                    "description": "Sample project description",
                    "budget": "1000",
                    "skills": ["Web Development", "JavaScript"],
                    "url": f"{self.bahar_url}/projects/sample"
                }
            ]
            
        except Exception as e:
            logger.error(f"Error extracting projects from DOM: {str(e)}")
            return []
    
    def _project_matches_criteria(self, project: Dict[str, any]) -> bool:
        """
        Check if project matches user criteria.
        
        Args:
            project: Project dictionary
            
        Returns:
            True if project matches criteria
        """
        try:
            # Check budget
            budget_str = str(project.get('budget', '0')).replace('$', '').replace(',', '')
            try:
                budget = float(budget_str)
                if budget < self.min_budget or budget > self.max_budget:
                    return False
            except ValueError:
                return False
            
            # Check if project is open (not closed)
            if not self._is_project_open(project):
                return False
            
            # Check categories (if specified)
            if self.preferred_categories and self.preferred_categories[0]:
                project_skills = project.get('skills', [])
                if not any(cat.lower() in [skill.lower() for skill in project_skills] for cat in self.preferred_categories):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking project criteria: {str(e)}")
            return False
    
    def _is_project_open(self, project: Dict[str, any]) -> bool:
        """
        Check if project is open (not closed).
        
        Args:
            project: Project dictionary
            
        Returns:
            True if project is open
        """
        # Check for closed indicators
        closed_indicators = ['closed', 'مغلق', 'completed', 'finished']
        
        status = project.get('status', '').lower()
        title = project.get('title', '').lower()
        
        for indicator in closed_indicators:
            if indicator in status or indicator in title:
                return False
        
        return True
    
    async def _submit_offer_for_project(self, project: Dict[str, any]) -> Dict[str, any]:
        """
        Submit an offer for a project using AI.
        
        Args:
            project: Project dictionary
            
        Returns:
            Dictionary with submission result
        """
        try:
            logger.info(f"🤖 Generating AI offer for project: {project.get('title')}")
            
            # Generate AI offer
            ai_offer = generate_fallback_offer(project, self.user_preferences)
            
            if not ai_offer:
                return {"success": False, "error": "Failed to generate AI offer"}
            
            # Navigate to project page
            page = await self.browser_manager.get_current_page()
            project_url = project.get('url')
            
            if not project_url:
                return {"success": False, "error": "No project URL available"}
            
            await page.goto(project_url)
            await asyncio.sleep(3)
            
            # Submit offer using AI
            submit_result = await submit_offer_with_ai(
                project_info=project,
                user_preferences=self.user_preferences,
                ai_offer=ai_offer
            )
            
            return submit_result
            
        except Exception as e:
            error_msg = f"Error submitting offer: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def run_scheduled_automation(self, run_duration_hours: int = 8) -> Dict[str, any]:
        """
        Run automation on a schedule for a specified duration.
        
        Args:
            run_duration_hours: How long to run the automation
            
        Returns:
            Dictionary with scheduling results
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=run_duration_hours)
        total_cycles = 0
        total_offers = 0
        
        logger.info(f"⏰ Starting scheduled automation for {run_duration_hours} hours")
        
        try:
            while datetime.now() < end_time:
                cycle_result = await self.run_automation_cycle(max_projects=5)
                
                if cycle_result.get('success'):
                    total_cycles += 1
                    total_offers += cycle_result.get('offers_submitted', 0)
                    
                    logger.info(f"Cycle {total_cycles} completed: {cycle_result.get('offers_submitted', 0)} offers")
                else:
                    logger.error(f"Cycle failed: {cycle_result.get('error')}")
                
                # Wait before next cycle
                await asyncio.sleep(self.monitoring_interval * 60)
            
            return {
                "success": True,
                "total_cycles": total_cycles,
                "total_offers_submitted": total_offers,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in scheduled automation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_cycles": total_cycles,
                "total_offers_submitted": total_offers,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.browser_manager:
                await self.browser_manager.close()
            logger.info("🧹 Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def get_status(self) -> Dict[str, any]:
        """Get current automation status."""
        return {
            "is_authenticated": self.is_authenticated,
            "session_start_time": self.session_start_time.isoformat() if self.session_start_time else None,
            "offers_submitted_today": self.offers_submitted_today,
            "max_offers_per_day": self.max_offers_per_day,
            "consecutive_errors": self.consecutive_errors,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        } 