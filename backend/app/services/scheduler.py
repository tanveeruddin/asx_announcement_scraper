"""
Scheduler Service using APScheduler.

This service manages periodic scraping jobs that run at configured intervals
to fetch and process new ASX announcements.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.services.pipeline import AnnouncementPipeline, get_pipeline

# Configure logging
logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing scheduled announcement scraping jobs.
    """

    def __init__(self):
        """Initialize the scheduler service."""
        self.scheduler = AsyncIOScheduler(
            timezone=settings.scheduler_timezone,
            job_defaults={
                "coalesce": True,  # Combine missed runs
                "max_instances": settings.scheduler_max_instances,
                "misfire_grace_time": 300,  # 5 minutes grace for missed jobs
            },
        )
        self.pipeline: Optional[AnnouncementPipeline] = None
        self.is_running = False
        self.last_run_time: Optional[datetime] = None
        self.last_run_success = False
        self.total_runs = 0
        self.successful_runs = 0

        logger.info(
            f"Scheduler initialized with timezone: {settings.scheduler_timezone}"
        )

    async def scrape_job(self):
        """
        The main scraping job that runs periodically.
        This is the function that APScheduler will execute.
        """
        run_id = self.total_runs + 1
        logger.info("=" * 80)
        logger.info(f"Scheduled scrape job #{run_id} triggered")
        logger.info(f"Time: {datetime.now()}")
        logger.info("=" * 80)

        self.total_runs += 1
        self.last_run_time = datetime.utcnow()

        try:
            # Get or create pipeline
            if self.pipeline is None:
                self.pipeline = get_pipeline()

            # Run the pipeline (process only price-sensitive announcements)
            results, stats = await self.pipeline.run_pipeline(
                price_sensitive_only=True,
                limit=None,  # Process all found announcements
            )

            # Check if run was successful
            if stats.errors:
                logger.warning(
                    f"Scrape job #{run_id} completed with {len(stats.errors)} errors"
                )
                self.last_run_success = False
            else:
                logger.info(f"✅ Scrape job #{run_id} completed successfully!")
                self.last_run_success = True
                self.successful_runs += 1

            logger.info(
                f"Pipeline stats: {stats.announcements_processed}/{stats.announcements_scraped} processed"
            )

        except Exception as e:
            logger.error(f"❌ Scrape job #{run_id} failed with error: {e}")
            logger.exception(e)
            self.last_run_success = False

    def schedule_interval_job(self, minutes: int):
        """
        Schedule scraping to run at regular intervals.

        Args:
            minutes: Interval in minutes between runs
        """
        trigger = IntervalTrigger(minutes=minutes)
        self.scheduler.add_job(
            self.scrape_job,
            trigger=trigger,
            id="scrape_interval",
            name=f"Scrape ASX announcements every {minutes} minutes",
            replace_existing=True,
        )
        logger.info(f"Scheduled interval job: every {minutes} minutes")

    def schedule_cron_job(self, cron_expression: str):
        """
        Schedule scraping using a cron expression.

        Args:
            cron_expression: Cron expression (e.g., "0 9-17 * * 1-5" for weekdays 9am-5pm)
        """
        # Parse cron expression
        # Format: "minute hour day month day_of_week"
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: {cron_expression}. "
                "Expected format: 'minute hour day month day_of_week'"
            )

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone=settings.scheduler_timezone,
        )

        self.scheduler.add_job(
            self.scrape_job,
            trigger=trigger,
            id="scrape_cron",
            name=f"Scrape ASX announcements (cron: {cron_expression})",
            replace_existing=True,
        )
        logger.info(f"Scheduled cron job: {cron_expression}")

    def schedule_market_hours_job(self):
        """
        Schedule scraping during ASX market hours.
        ASX trading hours: 10:00 AM - 4:00 PM AEST/AEDT, Monday-Friday

        Runs every hour during market hours.
        """
        # Run every hour from 10 AM to 4 PM on weekdays
        trigger = CronTrigger(
            minute=0,  # Top of the hour
            hour="10-16",  # 10 AM to 4 PM
            day_of_week="mon-fri",  # Weekdays only
            timezone=settings.scheduler_timezone,
        )

        self.scheduler.add_job(
            self.scrape_job,
            trigger=trigger,
            id="scrape_market_hours",
            name="Scrape ASX announcements during market hours",
            replace_existing=True,
        )
        logger.info(
            "Scheduled market hours job: every hour 10am-4pm AEST/AEDT, Mon-Fri"
        )

    async def run_job_now(self):
        """
        Manually trigger a scraping job immediately (for testing/admin).
        """
        logger.info("Manual job trigger requested")
        await self.scrape_job()

    def start(self, mode: str = "interval"):
        """
        Start the scheduler.

        Args:
            mode: Scheduling mode:
                - "interval": Regular intervals (uses SCRAPE_INTERVAL_MINUTES)
                - "market_hours": Only during ASX market hours
                - "cron": Custom cron expression (provide via environment)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        # Add the appropriate job based on mode
        if mode == "interval":
            self.schedule_interval_job(settings.scrape_interval_minutes)
        elif mode == "market_hours":
            self.schedule_market_hours_job()
        elif mode == "cron":
            # For custom cron, would need to be passed or configured
            # Default to market hours for now
            self.schedule_market_hours_job()
        else:
            raise ValueError(
                f"Invalid scheduler mode: {mode}. "
                "Use 'interval', 'market_hours', or 'cron'"
            )

        # Start the scheduler
        self.scheduler.start()
        self.is_running = True

        logger.info(f"✅ Scheduler started in '{mode}' mode")
        logger.info(f"Next run: {self.get_next_run_time()}")

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Scheduler stopped")

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        jobs = self.scheduler.get_jobs()
        if jobs:
            return jobs[0].next_run_time
        return None

    def get_status(self) -> dict:
        """
        Get the current status of the scheduler.

        Returns:
            Dictionary with scheduler status information
        """
        return {
            "is_running": self.is_running,
            "last_run_time": self.last_run_time,
            "last_run_success": self.last_run_success,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "success_rate": (
                (self.successful_runs / self.total_runs * 100)
                if self.total_runs > 0
                else 0
            ),
            "next_run_time": self.get_next_run_time(),
            "scheduled_jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time,
                }
                for job in self.scheduler.get_jobs()
            ],
        }


# Singleton instance
_scheduler_instance: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """
    Get or create the singleton scheduler instance.

    Returns:
        SchedulerService instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
