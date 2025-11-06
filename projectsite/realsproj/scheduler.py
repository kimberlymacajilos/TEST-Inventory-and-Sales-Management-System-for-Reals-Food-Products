"""
Scheduler for automatic expiration checks
Works with both Supabase and localhost databases
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

scheduler = None


def check_expirations_job():
    """
    Job function that runs the check_expirations management command
    """
    try:
        logger.info("Running scheduled expiration check...")
        call_command('check_expirations')
        logger.info("Expiration check completed successfully")
    except Exception as e:
        logger.error(f"Error running expiration check: {str(e)}")


def start_scheduler():
    """
    Start the background scheduler for expiration checks
    Runs daily at midnight (00:00)
    Works with both Supabase and localhost databases
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.info("Scheduler already running, skipping initialization")
        return
    
    try:
        scheduler = BackgroundScheduler()
        
        scheduler.add_job(
            check_expirations_job,
            trigger=CronTrigger(hour=0, minute=0),
            id='check_expirations',
            name='Check Expiring Items',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("✅ Expiration scheduler started successfully")
        logger.info("📅 Scheduled to run daily at 00:00 (midnight)")
        logger.info("🌐 Works with both Supabase and localhost databases")
       
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {str(e)}")


def stop_scheduler():
    """
    Stop the background scheduler
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
