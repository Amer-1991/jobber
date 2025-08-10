import asyncio
import json
import os
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv

from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.skills.search_bahar_projects import search_bahar_projects
from jobber_fsm.core.skills.filter_open_projects import filter_open_projects
from jobber_fsm.core.skills.submit_offer_with_ai import submit_offer_with_ai
from jobber_fsm.utils.logger import logger


class BaharAutomationOrchestrator:
    """
    Comprehensive automation orchestrator for Bahar platform.
    
    Handles:
    - Authentication
    - Project filtering (open vs closed)
    - AI-powered offer generation and submission
    - Error handling and recovery
    - Scheduling and monitoring
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
        """Initialize the automation system."""
        try:
            logger.info("🚀 Initializing Bahar Automation Orchestrator...")
            
            # Check credentials
            if not self.bahar_username or not self.bahar_password:
                logger.error("❌ Bahar credentials not found in environment variables")
                return False
            
            # Initialize browser
            self.browser_manager = PlaywrightManager(browser_type="chromium", headless=self.headless)
            await self.browser_manager.async_initialize(eval_mode=True)
            
            # Authenticate
            auth_success = await self._authenticate()
            if not auth_success:
                logger.error("❌ Authentication failed")
                return False
            
            self.session_start_time = datetime.now()
            self.is_authenticated = True
            logger.info("✅ Automation system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing automation: {str(e)}")
            traceback.print_exc()
            return False
    
    async def _authenticate(self) -> bool:
        """Authenticate with Bahar platform."""
        try:
            logger.info("🔐 Authenticating with Bahar...")
            
            login_result = await login_bahar_esso(
                username=self.bahar_username,
                password=self.bahar_password,
                bahar_url=self.bahar_url,
                wait_time=3.0
            )
            
            if "Success" in login_result:
                logger.info("✅ Authentication successful")
                return True
            else:
                logger.error(f"❌ Authentication failed: {login_result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during authentication: {str(e)}")
            return False
    
    async def run_automation_cycle(self, max_projects: int = 5) -> Dict[str, any]:
        """
        Run a complete automation cycle.
        
        Args:
            max_projects: Maximum number of projects to process
            
        Returns:
            Dictionary with cycle results
        """
        cycle_start = datetime.now()
        cycle_results = {
            "cycle_start": cycle_start.isoformat(),
            "projects_processed": 0,
            "offers_submitted": 0,
            "errors": [],
            "success": True
        }
        
        try:
            logger.info(f"🔄 Starting automation cycle (max projects: {max_projects})")
            
            # Check if we can submit more offers today
            if self.offers_submitted_today >= self.max_offers_per_day:
                logger.info(f"⚠️ Daily offer limit reached ({self.offers_submitted_today}/{self.max_offers_per_day})")
                cycle_results["message"] = "Daily offer limit reached"
                return cycle_results
            
            # Step 1: Filter and get open projects
            logger.info("📋 Step 1: Filtering open projects...")
            open_projects_result = await self._get_open_projects(max_projects)
            
            if "error" in open_projects_result:
                cycle_results["errors"].append(f"Failed to get open projects: {open_projects_result['error']}")
                cycle_results["success"] = False
                return cycle_results
            
            open_projects = open_projects_result.get("open_projects", [])
            logger.info(f"📊 Found {len(open_projects)} open projects")
            
            if not open_projects:
                cycle_results["message"] = "No open projects found"
                return cycle_results
            
            # Step 2: Process each project
            for i, project in enumerate(open_projects):
                if self.offers_submitted_today >= self.max_offers_per_day:
                    logger.info("⚠️ Daily offer limit reached during processing")
                    break
                
                cycle_results["projects_processed"] += 1
                logger.info(f"🎯 Processing project {i+1}/{len(open_projects)}: {project.get('title', 'Unknown')}")
                
                try:
                    # Check if project matches our criteria
                    if not self._project_matches_criteria(project):
                        logger.info(f"⏭️ Project doesn't match criteria, skipping")
                        continue
                    
                    # Submit offer for the project
                    offer_result = await self._submit_offer_for_project(project)
                    
                    if offer_result.get("success"):
                        cycle_results["offers_submitted"] += 1
                        self.offers_submitted_today += 1
                        logger.info(f"✅ Offer submitted successfully for: {project.get('title', 'Unknown')}")
                    else:
                        error_msg = f"Failed to submit offer for {project.get('title', 'Unknown')}: {offer_result.get('error', 'Unknown error')}"
                        cycle_results["errors"].append(error_msg)
                        logger.error(f"❌ {error_msg}")
                    
                    # Brief pause between projects
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_msg = f"Error processing project {project.get('title', 'Unknown')}: {str(e)}"
                    cycle_results["errors"].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    self.consecutive_errors += 1
                    
                    # If too many consecutive errors, stop processing
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        logger.error(f"⚠️ Too many consecutive errors ({self.consecutive_errors}), stopping cycle")
                        cycle_results["success"] = False
                        break
                    
                    continue
            
            # Reset consecutive errors if cycle was successful
            if cycle_results["success"]:
                self.consecutive_errors = 0
            
            cycle_end = datetime.now()
            cycle_results["cycle_end"] = cycle_end.isoformat()
            cycle_results["duration_seconds"] = (cycle_end - cycle_start).total_seconds()
            
            logger.info(f"✅ Automation cycle completed: {cycle_results['offers_submitted']} offers submitted")
            return cycle_results
            
        except Exception as e:
            error_msg = f"Error during automation cycle: {str(e)}"
            cycle_results["errors"].append(error_msg)
            cycle_results["success"] = False
            logger.error(f"❌ {error_msg}")
            traceback.print_exc()
            return cycle_results
    
    async def _get_open_projects(self, max_projects: int) -> Dict[str, any]:
        """Get open projects using filtering."""
        try:
            # First try to search with filters
            search_result = await search_bahar_projects(
                search_query="",
                min_budget=self.min_budget,
                max_budget=self.max_budget,
                max_results=max_projects * 2  # Get more to filter
            )
            
            search_data = json.loads(search_result)
            if "error" in search_data:
                logger.warning(f"Search failed: {search_data['error']}, trying direct filtering")
                # Fallback to direct filtering
                return await filter_open_projects(max_projects=max_projects, scroll_to_last_open=True)
            
            # Filter the search results to only open projects
            projects = search_data.get("projects", [])
            open_projects = []
            
            for project in projects:
                # Check if project is open (basic check)
                if self._is_project_open(project):
                    open_projects.append(project)
                    if len(open_projects) >= max_projects:
                        break
            
            return {
                "open_projects": open_projects,
                "total_found": len(open_projects)
            }
            
        except Exception as e:
            logger.error(f"Error getting open projects: {str(e)}")
            return {"error": str(e)}
    
    def _is_project_open(self, project: Dict[str, any]) -> bool:
        """Check if a project is open based on its information."""
        try:
            # Check for closed indicators in title or description
            title = project.get('title', '').lower()
            description = project.get('description', '').lower()
            
            closed_indicators = [
                'closed', 'completed', 'finished', 'ended', 'expired',
                'مغلق', 'مكتمل', 'منتهي', 'مقفل'  # Arabic
            ]
            
            for indicator in closed_indicators:
                if indicator in title or indicator in description:
                    return False
            
            # Check budget range
            budget_text = project.get('budget', '')
            if budget_text:
                try:
                    # Extract numeric value from budget text
                    import re
                    budget_match = re.search(r'\d+', budget_text)
                    if budget_match:
                        budget_value = int(budget_match.group())
                        if budget_value < self.min_budget or budget_value > self.max_budget:
                            return False
                except:
                    pass
            
            return True
            
        except Exception as e:
            logger.debug(f"Error checking project status: {str(e)}")
            return True  # Assume open if we can't determine
    
    def _project_matches_criteria(self, project: Dict[str, any]) -> bool:
        """Check if project matches our criteria."""
        try:
            # Check budget
            budget_text = project.get('budget', '')
            if budget_text:
                try:
                    import re
                    budget_match = re.search(r'\d+', budget_text)
                    if budget_match:
                        budget_value = int(budget_match.group())
                        if budget_value < self.min_budget or budget_value > self.max_budget:
                            return False
                except:
                    pass
            
            # Check category/skills match
            if self.preferred_categories:
                title = project.get('title', '').lower()
                description = project.get('description', '').lower()
                
                has_matching_category = False
                for category in self.preferred_categories:
                    if category.lower() in title or category.lower() in description:
                        has_matching_category = True
                        break
                
                if not has_matching_category:
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error checking project criteria: {str(e)}")
            return True  # Assume matches if we can't determine
    
    async def _submit_offer_for_project(self, project: Dict[str, any]) -> Dict[str, any]:
        """Submit an offer for a specific project."""
        try:
            project_url = project.get('url')
            if not project_url:
                return {"success": False, "error": "No project URL found"}
            
            logger.info(f"📝 Submitting offer for: {project.get('title', 'Unknown')}")
            
            offer_result = await submit_offer_with_ai(
                project_url=project_url,
                project_info=project,
                user_preferences=self.user_preferences,
                auto_submit=self.auto_submit_offers
            )
            
            result_data = json.loads(offer_result)
            
            if "error" in result_data:
                return {"success": False, "error": result_data["error"]}
            else:
                return {"success": True, "offer_data": result_data}
                
        except Exception as e:
            logger.error(f"Error submitting offer: {str(e)}")
            return {"success": False, "error": str(e)}
    
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
        
        scheduling_results = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_cycles": 0,
            "total_offers_submitted": 0,
            "cycles": [],
            "errors": []
        }
        
        logger.info(f"⏰ Starting scheduled automation for {run_duration_hours} hours")
        logger.info(f"📅 Start: {start_time}, End: {end_time}")
        
        try:
            while datetime.now() < end_time:
                # Check if we've reached daily limit
                if self.offers_submitted_today >= self.max_offers_per_day:
                    logger.info(f"⚠️ Daily offer limit reached ({self.offers_submitted_today}/{self.max_offers_per_day})")
                    break
                
                # Run one cycle
                cycle_result = await self.run_automation_cycle(max_projects=3)
                scheduling_results["cycles"].append(cycle_result)
                scheduling_results["total_cycles"] += 1
                scheduling_results["total_offers_submitted"] += cycle_result.get("offers_submitted", 0)
                
                if not cycle_result.get("success", True):
                    scheduling_results["errors"].append(f"Cycle {scheduling_results['total_cycles']} failed")
                
                # Wait before next cycle
                wait_minutes = self.monitoring_interval
                logger.info(f"⏳ Waiting {wait_minutes} minutes before next cycle...")
                await asyncio.sleep(wait_minutes * 60)
            
            scheduling_results["actual_end_time"] = datetime.now().isoformat()
            logger.info(f"✅ Scheduled automation completed: {scheduling_results['total_offers_submitted']} offers submitted")
            return scheduling_results
            
        except Exception as e:
            error_msg = f"Error during scheduled automation: {str(e)}"
            scheduling_results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
            traceback.print_exc()
            return scheduling_results
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.browser_manager:
                await self.browser_manager.stop_playwright()
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
            "auto_submit_enabled": self.auto_submit_offers,
            "user_preferences_loaded": bool(self.user_preferences),
            "last_activity": self.last_activity.isoformat()
        } 