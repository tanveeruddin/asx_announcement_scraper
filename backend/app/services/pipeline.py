"""
Pipeline Orchestrator Service.

This service coordinates all the individual services to process ASX announcements:
1. Scrape announcements from ASX
2. Download PDFs
3. Convert to markdown
4. Analyze with LLM
5. Fetch stock data
6. Save to database

The pipeline is designed to be modular, resilient, and easy to monitor.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.services.llm_analyzer import get_llm_analyzer
from app.services.pdf_downloader_playwright import PlaywrightPDFDownloader
from app.services.pdf_processor import PDFProcessor
from app.services.schemas import AnnouncementData, AnalysisResult, StockMetrics
from app.services.scraper import ASXScraper
from app.services.stock_data import get_stock_data_service
from app.services.storage.factory import get_storage

# Configure logging
logger = logging.getLogger(__name__)


class PipelineStats:
    """Statistics for a pipeline run."""

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.announcements_scraped = 0
        self.announcements_processed = 0
        self.pdfs_downloaded = 0
        self.pdfs_converted = 0
        self.llm_analyses_completed = 0
        self.stock_data_fetched = 0
        self.errors: list[str] = []
        self.skipped: list[str] = []

    def record_error(self, context: str, error: Exception):
        """Record an error that occurred during processing."""
        error_msg = f"{context}: {str(error)}"
        self.errors.append(error_msg)
        logger.error(error_msg)

    def record_skip(self, reason: str):
        """Record a skipped item."""
        self.skipped.append(reason)
        logger.info(f"Skipped: {reason}")

    def finalize(self):
        """Mark the pipeline run as complete."""
        self.end_time = datetime.utcnow()

    @property
    def duration_seconds(self) -> float:
        """Calculate pipeline duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.utcnow() - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.announcements_scraped == 0:
            return 0.0
        return (self.announcements_processed / self.announcements_scraped) * 100

    def __str__(self) -> str:
        """Return a formatted summary of the pipeline stats."""
        return (
            f"\nPipeline Statistics:\n"
            f"  Duration: {self.duration_seconds:.2f}s\n"
            f"  Announcements Scraped: {self.announcements_scraped}\n"
            f"  Announcements Processed: {self.announcements_processed}\n"
            f"  PDFs Downloaded: {self.pdfs_downloaded}\n"
            f"  PDFs Converted: {self.pdfs_converted}\n"
            f"  LLM Analyses: {self.llm_analyses_completed}\n"
            f"  Stock Data Fetched: {self.stock_data_fetched}\n"
            f"  Success Rate: {self.success_rate:.1f}%\n"
            f"  Errors: {len(self.errors)}\n"
            f"  Skipped: {len(self.skipped)}\n"
        )


class AnnouncementPipeline:
    """
    Main pipeline orchestrator for processing ASX announcements.
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the pipeline with all required services.

        Args:
            db_session: Optional database session for storing results
        """
        self.db_session = db_session
        self.scraper = ASXScraper()
        self.storage = get_storage()
        self.pdf_downloader = PlaywrightPDFDownloader(
            storage=self.storage,
            max_concurrent=settings.max_concurrent_downloads,
        )
        self.pdf_processor = PDFProcessor(storage=self.storage)
        self.llm_analyzer = get_llm_analyzer()
        self.stock_service = get_stock_data_service()

        logger.info("Pipeline initialized with all services")

    async def process_announcement(
        self, announcement: AnnouncementData, stats: PipelineStats
    ) -> dict:
        """
        Process a single announcement through the entire pipeline.

        Args:
            announcement: The announcement to process
            stats: Statistics tracker for this pipeline run

        Returns:
            Dictionary containing all processed data
        """
        result = {
            "announcement": announcement,
            "pdf_path": None,
            "markdown_content": None,
            "analysis": None,
            "stock_metrics": None,
            "success": False,
        }

        try:
            logger.info(
                f"Processing announcement: {announcement.asx_code} - {announcement.title}"
            )

            # Step 1: Download PDF
            try:
                pdf_info = await self.pdf_downloader.download_pdf(
                    announcement.pdf_url,
                    announcement.asx_code,
                    announcement.title,
                )
                result["pdf_path"] = pdf_info["local_path"]
                stats.pdfs_downloaded += 1
                logger.info(f"PDF downloaded: {pdf_info['local_path']}")
            except Exception as e:
                stats.record_error(
                    f"PDF download failed for {announcement.asx_code}", e
                )
                return result

            # Step 2: Convert PDF to Markdown
            try:
                markdown_result = self.pdf_processor.convert_to_markdown(
                    pdf_info["local_path"]
                )
                result["markdown_content"] = markdown_result["markdown_content"]
                stats.pdfs_converted += 1
                logger.info(
                    f"PDF converted to markdown: {len(markdown_result['markdown_content'])} chars"
                )
            except Exception as e:
                stats.record_error(
                    f"PDF conversion failed for {announcement.asx_code}", e
                )
                return result

            # Step 3: Analyze with LLM
            try:
                analysis = self.llm_analyzer.analyze_announcement(
                    result["markdown_content"], announcement.title
                )
                result["analysis"] = analysis
                stats.llm_analyses_completed += 1
                logger.info(
                    f"LLM analysis complete: {analysis.sentiment} sentiment"
                )
            except Exception as e:
                stats.record_error(
                    f"LLM analysis failed for {announcement.asx_code}", e
                )
                # Continue without analysis (non-critical)

            # Step 4: Fetch Stock Data
            try:
                stock_metrics = self.stock_service.get_stock_metrics(
                    announcement.asx_code, announcement.announcement_date
                )
                result["stock_metrics"] = stock_metrics
                if stock_metrics.data_available:
                    stats.stock_data_fetched += 1
                logger.info(
                    f"Stock data fetched: ${stock_metrics.current_price if stock_metrics.current_price else 'N/A'}"
                )
            except Exception as e:
                stats.record_error(
                    f"Stock data fetch failed for {announcement.asx_code}", e
                )
                # Continue without stock data (non-critical)

            # Step 5: Save to database (if db_session provided)
            if self.db_session:
                try:
                    # TODO: Implement database save logic
                    # This will be done when we create the database service layer
                    logger.info(
                        f"Would save to database: {announcement.asx_code}"
                    )
                except Exception as e:
                    stats.record_error(
                        f"Database save failed for {announcement.asx_code}", e
                    )

            result["success"] = True
            stats.announcements_processed += 1
            logger.info(
                f"✅ Successfully processed: {announcement.asx_code} - {announcement.title}"
            )

        except Exception as e:
            stats.record_error(
                f"Unexpected error processing {announcement.asx_code}", e
            )

        return result

    async def run_pipeline(
        self,
        limit: Optional[int] = None,
        price_sensitive_only: bool = True,
    ) -> tuple[list[dict], PipelineStats]:
        """
        Run the complete pipeline: scrape, process, analyze, and store.

        Args:
            limit: Optional limit on number of announcements to process
            price_sensitive_only: If True, only process price-sensitive announcements

        Returns:
            Tuple of (list of processed results, pipeline statistics)
        """
        stats = PipelineStats()
        results = []

        try:
            logger.info("=" * 80)
            logger.info("Starting pipeline run...")
            logger.info("=" * 80)

            # Step 1: Scrape announcements
            logger.info("Scraping ASX announcements...")
            scrape_result = self.scraper.scrape_announcements()

            if not scrape_result.success:
                stats.record_error(
                    "Scraping failed", Exception(scrape_result.error_message)
                )
                stats.finalize()
                return results, stats

            # Filter announcements
            announcements = scrape_result.announcements
            if price_sensitive_only:
                announcements = [a for a in announcements if a.is_price_sensitive]
                logger.info(
                    f"Filtered to {len(announcements)} price-sensitive announcements"
                )

            # Apply limit if specified
            if limit:
                announcements = announcements[:limit]
                logger.info(f"Limited to {limit} announcements")

            stats.announcements_scraped = len(announcements)
            logger.info(f"Found {len(announcements)} announcements to process")

            # Step 2: Process each announcement
            for i, announcement in enumerate(announcements, 1):
                logger.info(
                    f"\n--- Processing {i}/{len(announcements)}: {announcement.asx_code} ---"
                )
                result = await self.process_announcement(announcement, stats)
                results.append(result)

            # Cleanup
            await self.pdf_downloader.close()

        except Exception as e:
            stats.record_error("Pipeline execution failed", e)

        finally:
            stats.finalize()
            logger.info("=" * 80)
            logger.info("Pipeline run complete!")
            logger.info(str(stats))
            logger.info("=" * 80)

        return results, stats

    async def process_single_announcement_by_url(
        self, pdf_url: str, asx_code: str, title: str
    ) -> dict:
        """
        Process a single announcement given its PDF URL (for testing).

        Args:
            pdf_url: URL to the PDF announcement
            asx_code: ASX stock code
            title: Announcement title

        Returns:
            Dictionary containing all processed data
        """
        stats = PipelineStats()
        stats.announcements_scraped = 1

        announcement = AnnouncementData(
            asx_code=asx_code,
            company_name="",
            title=title,
            announcement_date=datetime.utcnow(),
            pdf_url=pdf_url,
            is_price_sensitive=True,
        )

        result = await self.process_announcement(announcement, stats)
        stats.finalize()

        logger.info(str(stats))

        await self.pdf_downloader.close()

        return result


# Singleton instance
_pipeline_instance: Optional[AnnouncementPipeline] = None


def get_pipeline(db_session: Optional[Session] = None) -> AnnouncementPipeline:
    """
    Get or create the singleton pipeline instance.

    Args:
        db_session: Optional database session

    Returns:
        AnnouncementPipeline instance
    """
    global _pipeline_instance
    if _pipeline_instance is None or db_session is not None:
        _pipeline_instance = AnnouncementPipeline(db_session=db_session)
    return _pipeline_instance
