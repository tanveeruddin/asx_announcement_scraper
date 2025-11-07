#!/usr/bin/env python3
"""
Test script for Intelligence Layer (LLM Analyzer + Stock Data Service).

This script tests:
1. Stock data service with yfinance
2. LLM analyzer service with Gemini API
3. Integration of both services

Usage:
    python test_intelligence_layer.py
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.llm_analyzer import get_llm_analyzer
from app.services.stock_data import get_stock_data_service

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


def test_stock_data_service():
    """Test the stock data service with real ASX companies."""
    print_section("TEST 1: Stock Data Service")

    # Test with major ASX companies
    test_codes = ["BHP", "CBA", "CSL", "WES"]

    stock_service = get_stock_data_service()

    print(f"Testing stock data fetch for: {', '.join(test_codes)}\n")

    for code in test_codes:
        print(f"📊 Fetching data for {code}...")
        metrics = stock_service.get_stock_metrics(code)

        if metrics.data_available:
            print(f"  ✅ Success!")
            print(f"  Current Price: ${metrics.current_price}")
            print(f"  Market Cap: ${metrics.market_cap:,.0f}" if metrics.market_cap else "  Market Cap: N/A")
            print(f"  P/E Ratio: {metrics.pe_ratio}" if metrics.pe_ratio else "  P/E Ratio: N/A")
            print(f"  1M Performance: {metrics.performance_1m_pct}%" if metrics.performance_1m_pct else "  1M Performance: N/A")
            print(f"  3M Performance: {metrics.performance_3m_pct}%" if metrics.performance_3m_pct else "  3M Performance: N/A")
            print(f"  6M Performance: {metrics.performance_6m_pct}%" if metrics.performance_6m_pct else "  6M Performance: N/A")
        else:
            print(f"  ❌ Failed: {metrics.error_message}")

        print()

    print("✅ Stock Data Service test complete!\n")


def test_llm_analyzer_service():
    """Test the LLM analyzer service with sample announcement."""
    print_section("TEST 2: LLM Analyzer Service")

    # Sample announcement markdown (shortened for testing)
    sample_announcement = """
# BHP Group Limited - Quarterly Production Report

**Date:** November 7, 2025
**ASX Code:** BHP

## Highlights

BHP Group Limited today announced its quarterly production results for the period ending September 30, 2025.

### Key Results

**Iron Ore:**
- Production: 71.5 million tonnes (Mt)
- 5% increase compared to previous quarter
- Exceeded market expectations by 3.2 Mt

**Copper:**
- Production: 445,000 tonnes
- Stable quarter-on-quarter performance
- On track to meet full-year guidance

**Coal:**
- Production: 12.3 Mt
- Slight decrease due to planned maintenance
- Expected to return to normal levels next quarter

## Operational Updates

- Successfully completed major maintenance at Olympic Dam
- Jansen potash project progressing on schedule
- Cost reduction initiatives delivering $500M in annual savings

## Market Outlook

Management remains optimistic about iron ore demand, particularly from Chinese steel producers. Copper demand continues to be supported by renewable energy and EV sectors.

## Financial Implications

The strong iron ore performance is expected to positively impact earnings for the current half-year. The company maintains its full-year production guidance across all commodities.
"""

    print("Testing LLM analysis with sample BHP announcement...\n")

    try:
        analyzer = get_llm_analyzer()
        print(f"🤖 Using model: {settings.gemini_model}")
        print(f"🌡️  Temperature: {settings.gemini_temperature}\n")

        print("Analyzing announcement...\n")
        result = analyzer.analyze_announcement(
            sample_announcement,
            announcement_title="BHP - Quarterly Production Report"
        )

        print("✅ Analysis complete!\n")
        print("📝 ANALYSIS RESULTS:")
        print(f"\n  Summary:")
        print(f"  {result.summary}\n")
        print(f"  Sentiment: {result.sentiment.upper()} 🎯")
        print(f"  Confidence: {result.confidence_score:.2f}\n")
        print(f"  Key Insights:")
        for i, insight in enumerate(result.key_insights, 1):
            print(f"    {i}. {insight}")
        print(f"\n  Financial Impact:")
        print(f"  {result.financial_impact}\n")
        print(f"  Processing Time: {result.processing_time_ms}ms")
        print(f"  Model Used: {result.llm_model}\n")

        print("✅ LLM Analyzer Service test complete!\n")
        return True

    except Exception as e:
        print(f"❌ LLM Analyzer test failed: {e}\n")
        logger.error(f"LLM test error: {e}", exc_info=True)
        return False


def test_integrated_pipeline():
    """Test the integrated pipeline with both services."""
    print_section("TEST 3: Integrated Intelligence Layer Pipeline")

    print("Testing integrated pipeline: Stock Data + LLM Analysis\n")

    asx_code = "BHP"
    announcement_title = "Quarterly Production Report"

    # Sample markdown (same as above)
    sample_markdown = """
# BHP Group Limited - Quarterly Production Report

BHP Group reported strong quarterly production figures with iron ore output exceeding
market expectations by 5%. Copper production remained stable despite weather challenges.
Cost reduction initiatives are on track, delivering $500M in annual savings.

Key highlights:
- Iron ore production: 71.5 Mt (up 5% vs expectations)
- Copper production: 445,000 tonnes (stable)
- Cost savings: $500M annually
- Outlook: Positive on iron ore demand

The strong performance is expected to support the share price in the short term.
"""

    try:
        # Step 1: Fetch stock data
        print(f"📊 Step 1: Fetching stock data for {asx_code}...")
        stock_service = get_stock_data_service()
        stock_metrics = stock_service.get_stock_metrics(
            asx_code,
            announcement_datetime=datetime.now()
        )

        if stock_metrics.data_available:
            print(f"  ✅ Stock data retrieved")
            print(f"  Price: ${stock_metrics.current_price}")
            print(f"  Market Cap: ${stock_metrics.market_cap:,.0f}" if stock_metrics.market_cap else "  Market Cap: N/A")
        else:
            print(f"  ⚠️  Stock data unavailable: {stock_metrics.error_message}")

        # Step 2: Analyze with LLM
        print(f"\n🤖 Step 2: Analyzing announcement with LLM...")
        analyzer = get_llm_analyzer()
        analysis = analyzer.analyze_announcement(sample_markdown, announcement_title)

        print(f"  ✅ Analysis complete")
        print(f"  Sentiment: {analysis.sentiment.upper()}")
        print(f"  Insights: {len(analysis.key_insights)}")

        # Step 3: Combined output
        print(f"\n📈 Step 3: Combined Intelligence Report")
        print(f"\n  Company: {asx_code}")
        print(f"  Stock Price: ${stock_metrics.current_price}")
        print(f"  Announcement Sentiment: {analysis.sentiment.upper()}")
        print(f"  Confidence: {analysis.confidence_score:.0%}")
        print(f"\n  Summary: {analysis.summary}")
        print(f"\n  Financial Impact: {analysis.financial_impact}")

        if stock_metrics.performance_1m_pct:
            print(f"\n  Recent Performance:")
            print(f"    1M: {stock_metrics.performance_1m_pct}%")
            if stock_metrics.performance_3m_pct:
                print(f"    3M: {stock_metrics.performance_3m_pct}%")
            if stock_metrics.performance_6m_pct:
                print(f"    6M: {stock_metrics.performance_6m_pct}%")

        print("\n✅ Integrated pipeline test complete!\n")
        return True

    except Exception as e:
        print(f"❌ Integrated pipeline test failed: {e}\n")
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return False


def check_environment():
    """Check if required environment variables are set."""
    print_section("Environment Check")

    checks = {
        "Gemini API Key": bool(settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here"),
        "Gemini Model": bool(settings.gemini_model),
        "Database URL": bool(settings.database_url),
    }

    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
        if not passed:
            all_passed = False

    print()

    if not all_passed:
        print("⚠️  Warning: Some environment variables are not configured.")
        print("   Make sure you have a .env file with required settings.")
        print("   Copy .env.example to .env and update the values.\n")
        return False

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  ASX Announcements - Intelligence Layer Test Suite")
    print("=" * 80)

    # Check environment
    has_gemini_key = check_environment()

    # Run tests
    try:
        # Test 1: Stock Data Service (doesn't require API key)
        test_stock_data_service()

        # Test 2 & 3: LLM tests (only if API key is configured)
        if has_gemini_key:
            # Test 2: LLM Analyzer Service (requires API key)
            llm_success = test_llm_analyzer_service()

            # Test 3: Integrated Pipeline
            if llm_success:
                test_integrated_pipeline()
        else:
            print_section("Skipping LLM Tests")
            print("⚠️  Gemini API key not configured.")
            print("   To test the full Intelligence Layer, add your API key to .env\n")
            print("   GEMINI_API_KEY=your_api_key_here\n")
            print("   Get a free API key at: https://makersuite.google.com/app/apikey\n")

        # Summary
        print_section("Test Summary")
        if has_gemini_key:
            print("✅ All tests completed!")
        else:
            print("✅ Stock Data Service tests completed!")
            print("⚠️  LLM tests skipped (API key required)")
        print("\nNext steps:")
        print("  1. Review the results above")
        if not has_gemini_key:
            print("  2. Add Gemini API key to .env to test LLM analyzer")
            print("  3. Re-run this script to test full Intelligence Layer")
        else:
            print("  2. Check that stock data is accurate")
            print("  3. Verify LLM analysis quality")
            print("  4. Ready to integrate into full pipeline")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user.\n")
        return 130
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}\n")
        logger.error("Test suite error", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
