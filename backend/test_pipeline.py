#!/usr/bin/env python3
"""
Test script for the complete announcement processing pipeline.

This script tests the end-to-end pipeline:
1. Scraping ASX announcements
2. Downloading PDFs
3. Converting to markdown
4. LLM analysis (if API key available)
5. Stock data fetching
6. Complete pipeline orchestration
7. Scheduler setup

Usage:
    python test_pipeline.py [--limit N] [--skip-llm] [--skip-stock]
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.pipeline import get_pipeline
from app.services.scheduler import get_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(result: dict, index: int, total: int):
    """Print a formatted result for a processed announcement."""
    announcement = result["announcement"]
    print(f"\n[{index}/{total}] {announcement.asx_code} - {announcement.title}")
    print(f"  Date: {announcement.announcement_date}")
    print(f"  Price Sensitive: {'Yes' if announcement.is_price_sensitive else 'No'}")

    if result["pdf_path"]:
        print(f"  ✅ PDF Downloaded: {result['pdf_path']}")
    else:
        print(f"  ❌ PDF Download Failed")

    if result["markdown_content"]:
        print(
            f"  ✅ Markdown Converted: {len(result['markdown_content'])} chars"
        )
    else:
        print(f"  ❌ Markdown Conversion Failed")

    if result["analysis"]:
        analysis = result["analysis"]
        print(f"  ✅ LLM Analysis:")
        print(f"     Sentiment: {analysis.sentiment.upper()}")
        print(f"     Confidence: {analysis.confidence_score:.0%}")
        print(f"     Insights: {len(analysis.key_insights)} key insights")
        print(f"     Processing Time: {analysis.processing_time_ms}ms")
    else:
        print(f"  ⚠️  LLM Analysis Skipped/Failed")

    if result["stock_metrics"]:
        metrics = result["stock_metrics"]
        if metrics.data_available:
            print(f"  ✅ Stock Data:")
            if metrics.current_price:
                print(f"     Price: ${metrics.current_price}")
            if metrics.market_cap:
                print(f"     Market Cap: ${metrics.market_cap:,.0f}")
            if metrics.performance_1m_pct:
                print(f"     1M Performance: {metrics.performance_1m_pct}%")
        else:
            print(f"  ⚠️  Stock Data: {metrics.error_message}")
    else:
        print(f"  ⚠️  Stock Data Skipped/Failed")

    if result["success"]:
        print(f"  ✅ OVERALL: SUCCESS")
    else:
        print(f"  ❌ OVERALL: FAILED")


async def test_pipeline_single(limit: int = 1):
    """Test the pipeline with a single announcement."""
    print_section(f"TEST 1: Pipeline - Single Announcement (limit={limit})")

    print(f"Testing pipeline with {limit} announcement(s)...\n")

    try:
        # Get pipeline
        pipeline = get_pipeline()

        # Run pipeline
        results, stats = await pipeline.run_pipeline(
            limit=limit, price_sensitive_only=True
        )

        # Print results
        print_section("Results")

        for i, result in enumerate(results, 1):
            print_result(result, i, len(results))

        # Print stats
        print_section("Pipeline Statistics")
        print(str(stats))

        return True

    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        logger.error(f"Pipeline test error: {e}", exc_info=True)
        return False


async def test_pipeline_batch(limit: int = 5):
    """Test the pipeline with multiple announcements."""
    print_section(f"TEST 2: Pipeline - Batch Processing (limit={limit})")

    print(f"Testing pipeline with up to {limit} announcements...\n")

    try:
        # Get pipeline
        pipeline = get_pipeline()

        # Run pipeline
        results, stats = await pipeline.run_pipeline(
            limit=limit, price_sensitive_only=True
        )

        # Print summary
        print_section("Batch Processing Summary")

        successful = sum(1 for r in results if r["success"])
        print(f"Total Processed: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")
        print(f"Success Rate: {(successful / len(results) * 100) if results else 0:.1f}%")

        # Print detailed stats
        print(str(stats))

        # Print individual results
        if results:
            print_section("Individual Results")
            for i, result in enumerate(results, 1):
                print_result(result, i, len(results))

        return True

    except Exception as e:
        print(f"\n❌ Batch pipeline test failed: {e}")
        logger.error(f"Batch pipeline error: {e}", exc_info=True)
        return False


def test_scheduler_setup():
    """Test the scheduler service setup."""
    print_section("TEST 3: Scheduler Service")

    try:
        print("Testing scheduler service...\n")

        # Get scheduler
        scheduler = get_scheduler()

        # Test configuration
        print(f"✅ Scheduler initialized")
        print(f"   Timezone: {settings.scheduler_timezone}")
        print(f"   Interval: {settings.scrape_interval_minutes} minutes")
        print(f"   Max Instances: {settings.scheduler_max_instances}")

        # Get status
        status = scheduler.get_status()
        print(f"\n📊 Scheduler Status:")
        print(f"   Running: {status['is_running']}")
        print(f"   Total Runs: {status['total_runs']}")
        print(f"   Successful Runs: {status['successful_runs']}")
        print(f"   Success Rate: {status['success_rate']:.1f}%")
        print(f"   Last Run: {status['last_run_time']}")
        print(f"   Next Run: {status['next_run_time']}")

        print(f"\n✅ Scheduler service test complete!")
        print(f"\nℹ️  Note: Scheduler is not started in this test.")
        print(f"   To start the scheduler, use the scheduler service in your app.")

        return True

    except Exception as e:
        print(f"\n❌ Scheduler test failed: {e}")
        logger.error(f"Scheduler test error: {e}", exc_info=True)
        return False


def check_environment():
    """Check environment configuration."""
    print_section("Environment Check")

    checks = {
        "Database URL": bool(settings.database_url),
        "Storage Path": Path(settings.local_storage_path).parent.exists(),
        "ASX URL": bool(settings.asx_url),
        "Scrape Interval": settings.scrape_interval_minutes > 0,
    }

    # Optional checks
    optional_checks = {
        "Gemini API Key": bool(
            settings.gemini_api_key
            and settings.gemini_api_key != "your_gemini_api_key_here"
        ),
    }

    all_required_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
        if not passed:
            all_required_passed = False

    print(f"\nOptional Features:")
    for check, passed in optional_checks.items():
        status = "✅" if passed else "⚠️ "
        print(f"{status} {check}")

    print()

    if not all_required_passed:
        print("❌ Required environment checks failed.")
        return False

    return True


async def main():
    """Run all pipeline tests."""
    parser = argparse.ArgumentParser(
        description="Test the ASX announcement processing pipeline"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=2,
        help="Number of announcements to process (default: 2)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=5,
        help="Number of announcements for batch test (default: 5)",
    )
    parser.add_argument(
        "--skip-scheduler",
        action="store_true",
        help="Skip scheduler service test",
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("  ASX Announcements - Complete Pipeline Test Suite")
    print("=" * 80)

    # Check environment
    if not check_environment():
        print("⚠️  Some environment checks failed, but continuing with tests...\n")

    # Track test results
    results = {}

    try:
        # Test 1: Single announcement
        print("\n🔧 Starting Test 1: Single Announcement Pipeline...")
        results["single"] = await test_pipeline_single(limit=args.limit)

        # Test 2: Batch processing
        if results["single"]:
            print("\n🔧 Starting Test 2: Batch Processing Pipeline...")
            results["batch"] = await test_pipeline_batch(limit=args.batch)
        else:
            print("\n⚠️  Skipping batch test due to single test failure")
            results["batch"] = False

        # Test 3: Scheduler setup
        if not args.skip_scheduler:
            print("\n🔧 Starting Test 3: Scheduler Service...")
            results["scheduler"] = test_scheduler_setup()
        else:
            print("\n⚠️  Skipping scheduler test (--skip-scheduler)")
            results["scheduler"] = None

        # Summary
        print_section("Test Suite Summary")

        passed = sum(1 for r in results.values() if r is True)
        total = sum(1 for r in results.values() if r is not None)

        print(f"Tests Run: {total}")
        print(f"Tests Passed: {passed}")
        print(f"Tests Failed: {total - passed}")

        for name, result in results.items():
            if result is None:
                status = "⊘"
                desc = "Skipped"
            elif result:
                status = "✅"
                desc = "Passed"
            else:
                status = "❌"
                desc = "Failed"
            print(f"  {status} {name.title()}: {desc}")

        print("\n" + "=" * 80)
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        print("=" * 80 + "\n")

        return 0 if passed == total else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user.\n")
        return 130
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}\n")
        logger.error("Test suite error", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
