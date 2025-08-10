#!/usr/bin/env python3
"""
Bahar Automation Main Entry Point

This script provides a comprehensive automation system for the Bahar platform.
It can be run as a standalone script or scheduled to run automatically.

Features:
- Authentication with Bahar platform
- Project filtering (open vs closed)
- AI-powered offer generation and submission
- Error handling and recovery
- Scheduling and monitoring
- Daily offer limits
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobber_fsm.core.automation_orchestrator import BaharAutomationOrchestrator
from jobber_fsm.utils.logger import logger


async def run_single_cycle(orchestrator: BaharAutomationOrchestrator, max_projects: int = 5) -> Dict[str, Any]:
    """
    Run a single automation cycle.
    
    Args:
        orchestrator: The automation orchestrator
        max_projects: Maximum number of projects to process
        
    Returns:
        Dictionary with cycle results
    """
    logger.info("🔄 Running single automation cycle...")
    
    try:
        # Initialize if not already done
        if not orchestrator.is_authenticated:
            init_success = await orchestrator.initialize()
            if not init_success:
                return {"success": False, "error": "Failed to initialize automation"}
        
        # Run the cycle
        cycle_result = await orchestrator.run_automation_cycle(max_projects=max_projects)
        
        # Print results
        print(f"\n📊 Cycle Results:")
        print(f"   Projects Processed: {cycle_result.get('projects_processed', 0)}")
        print(f"   Offers Submitted: {cycle_result.get('offers_submitted', 0)}")
        print(f"   Duration: {cycle_result.get('duration_seconds', 0):.1f} seconds")
        
        if cycle_result.get('errors'):
            print(f"   Errors: {len(cycle_result['errors'])}")
            for error in cycle_result['errors'][:3]:  # Show first 3 errors
                print(f"     - {error}")
        
        return cycle_result
        
    except Exception as e:
        logger.error(f"Error running single cycle: {str(e)}")
        return {"success": False, "error": str(e)}


async def run_scheduled_automation(orchestrator: BaharAutomationOrchestrator, duration_hours: int = 8) -> Dict[str, Any]:
    """
    Run automation on a schedule for a specified duration.
    
    Args:
        orchestrator: The automation orchestrator
        duration_hours: How long to run the automation
        
    Returns:
        Dictionary with scheduling results
    """
    logger.info(f"⏰ Running scheduled automation for {duration_hours} hours...")
    
    try:
        # Initialize if not already done
        if not orchestrator.is_authenticated:
            init_success = await orchestrator.initialize()
            if not init_success:
                return {"success": False, "error": "Failed to initialize automation"}
        
        # Run scheduled automation
        scheduling_result = await orchestrator.run_scheduled_automation(run_duration_hours=duration_hours)
        
        # Print results
        print(f"\n📊 Scheduling Results:")
        print(f"   Total Cycles: {scheduling_result.get('total_cycles', 0)}")
        print(f"   Total Offers Submitted: {scheduling_result.get('total_offers_submitted', 0)}")
        print(f"   Start Time: {scheduling_result.get('start_time', 'Unknown')}")
        print(f"   End Time: {scheduling_result.get('actual_end_time', 'Unknown')}")
        
        if scheduling_result.get('errors'):
            print(f"   Errors: {len(scheduling_result['errors'])}")
            for error in scheduling_result['errors'][:3]:  # Show first 3 errors
                print(f"     - {error}")
        
        return scheduling_result
        
    except Exception as e:
        logger.error(f"Error running scheduled automation: {str(e)}")
        return {"success": False, "error": str(e)}


async def run_continuous_monitoring(orchestrator: BaharAutomationOrchestrator, check_interval_minutes: int = 30) -> None:
    """
    Run continuous monitoring with periodic automation cycles.
    
    Args:
        orchestrator: The automation orchestrator
        check_interval_minutes: How often to run cycles
    """
    logger.info(f"🔄 Starting continuous monitoring (check interval: {check_interval_minutes} minutes)...")
    
    try:
        # Initialize if not already done
        if not orchestrator.is_authenticated:
            init_success = await orchestrator.initialize()
            if not init_success:
                logger.error("Failed to initialize automation")
                return
        
        cycle_count = 0
        
        while True:
            cycle_count += 1
            logger.info(f"🔄 Cycle {cycle_count} starting...")
            
            try:
                # Run a single cycle
                cycle_result = await orchestrator.run_automation_cycle(max_projects=3)
                
                # Print cycle summary
                print(f"\n📊 Cycle {cycle_count} Summary:")
                print(f"   Offers Submitted: {cycle_result.get('offers_submitted', 0)}")
                print(f"   Projects Processed: {cycle_result.get('projects_processed', 0)}")
                print(f"   Success: {cycle_result.get('success', False)}")
                
                # Check if we've reached daily limit
                status = orchestrator.get_status()
                if status['offers_submitted_today'] >= status['max_offers_per_day']:
                    logger.info(f"⚠️ Daily offer limit reached ({status['offers_submitted_today']}/{status['max_offers_per_day']})")
                    print("🛑 Daily offer limit reached. Stopping continuous monitoring.")
                    break
                
                # Wait before next cycle
                if cycle_count < 1000:  # Safety limit
                    logger.info(f"⏳ Waiting {check_interval_minutes} minutes before next cycle...")
                    print(f"⏰ Next cycle in {check_interval_minutes} minutes...")
                    await asyncio.sleep(check_interval_minutes * 60)
                else:
                    logger.info("Reached maximum cycle limit, stopping")
                    break
                    
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping continuous monitoring")
                break
            except Exception as e:
                logger.error(f"Error in cycle {cycle_count}: {str(e)}")
                print(f"❌ Cycle {cycle_count} failed: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        print(f"✅ Continuous monitoring completed. Total cycles: {cycle_count}")
        
    except Exception as e:
        logger.error(f"Error in continuous monitoring: {str(e)}")


def print_status(orchestrator: BaharAutomationOrchestrator) -> None:
    """Print current automation status."""
    status = orchestrator.get_status()
    
    print("\n📊 Automation Status:")
    print(f"   Authenticated: {status['is_authenticated']}")
    print(f"   Auto Submit Enabled: {status['auto_submit_enabled']}")
    print(f"   Offers Submitted Today: {status['offers_submitted_today']}/{status['max_offers_per_day']}")
    print(f"   Consecutive Errors: {status['consecutive_errors']}")
    print(f"   User Preferences Loaded: {status['user_preferences_loaded']}")
    
    if status['session_start_time']:
        print(f"   Session Start: {status['session_start_time']}")
    
    if status['last_activity']:
        print(f"   Last Activity: {status['last_activity']}")


def save_results(results: Dict[str, Any], filename: str = None) -> None:
    """Save automation results to a JSON file."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"automation_results_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Results saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")


async def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Bahar Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a single cycle
  python automation_main.py --cycle --max-projects 5
  
  # Run scheduled automation for 8 hours
  python automation_main.py --scheduled --duration 8
  
  # Run continuous monitoring
  python automation_main.py --continuous --interval 30
  
  # Show status only
  python automation_main.py --status
  
  # Run in headless mode
  python automation_main.py --cycle --headless
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--cycle", action="store_true", help="Run a single automation cycle")
    mode_group.add_argument("--scheduled", action="store_true", help="Run scheduled automation")
    mode_group.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    mode_group.add_argument("--status", action="store_true", help="Show current status only")
    
    # Parameters
    parser.add_argument("--max-projects", type=int, default=5, help="Maximum projects to process per cycle")
    parser.add_argument("--duration", type=int, default=8, help="Duration in hours for scheduled mode")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in minutes for continuous mode")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--save-results", type=str, help="Save results to specified file")
    
    args = parser.parse_args()
    
    # Check environment variables
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   You can create a .env file with these variables or set them in your shell")
        return 1
    
    # Check for Llama AI configuration
    llama_configs = [
        os.getenv("OLLAMA_HOST"),
        os.getenv("LLAMA_MODEL_PATH"),
        os.getenv("LLAMA_MODEL_NAME")
    ]
    
    if not any(llama_configs):
        print("⚠️ Warning: No local Llama AI configuration found.")
        print("   Run 'python setup_llama_ai.py' to set up local AI")
        print("   AI offer generation will use fallback templates.")
    
    # Create orchestrator
    orchestrator = BaharAutomationOrchestrator(headless=args.headless)
    
    try:
        if args.status:
            # Just show status
            print_status(orchestrator)
            return 0
        
        elif args.cycle:
            # Run single cycle
            print("🎯 Running single automation cycle...")
            result = await run_single_cycle(orchestrator, args.max_projects)
            
            if args.save_results:
                save_results(result, args.save_results)
            
            return 0 if result.get("success", False) else 1
        
        elif args.scheduled:
            # Run scheduled automation
            print(f"⏰ Running scheduled automation for {args.duration} hours...")
            result = await run_scheduled_automation(orchestrator, args.duration)
            
            if args.save_results:
                save_results(result, args.save_results)
            
            return 0 if result.get("success", False) else 1
        
        elif args.continuous:
            # Run continuous monitoring
            print(f"🔄 Running continuous monitoring (interval: {args.interval} minutes)...")
            await run_continuous_monitoring(orchestrator, args.interval)
            return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        return 1
    finally:
        # Cleanup
        try:
            await orchestrator.cleanup()
        except:
            pass


if __name__ == "__main__":
    print("🚀 Bahar Automation System")
    print("=" * 50)
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 