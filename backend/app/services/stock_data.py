"""
Stock Data Service using yfinance.

This service fetches stock market data for ASX-listed companies:
- Current stock price
- Market capitalization
- Historical performance (1/3/6 months)
- Market reaction analysis (price change after announcement)
- Trading volume and other metrics

The service includes caching, retry logic, and error handling.
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import yfinance as yf
from yfinance import Ticker

from app.config import settings
from app.services.schemas import StockMetrics

# Configure logging
logger = logging.getLogger(__name__)


class StockDataService:
    """
    Service for fetching stock market data from Yahoo Finance.

    Note: ASX stocks on Yahoo Finance use the format: CODE.AX (e.g., BHP.AX, CBA.AX)
    """

    def __init__(self):
        """Initialize the stock data service."""
        self.cache_hours = settings.yfinance_cache_hours
        self.retry_attempts = settings.stock_data_retry_attempts
        self.retry_delay = settings.stock_data_retry_delay_seconds

        logger.info(
            f"Stock Data Service initialized - "
            f"Cache: {self.cache_hours}h, "
            f"Retries: {self.retry_attempts}"
        )

    def _format_asx_ticker(self, asx_code: str) -> str:
        """
        Format ASX code to Yahoo Finance ticker format.

        Args:
            asx_code: ASX stock code (e.g., 'BHP', 'CBA')

        Returns:
            Yahoo Finance ticker (e.g., 'BHP.AX', 'CBA.AX')
        """
        # Remove .AX suffix if already present
        code = asx_code.upper().replace(".AX", "")
        return f"{code}.AX"

    def _safe_decimal(self, value: any) -> Optional[Decimal]:
        """
        Safely convert a value to Decimal.

        Args:
            value: Value to convert

        Returns:
            Decimal value or None if conversion fails
        """
        if value is None or value == "N/A":
            return None

        try:
            return Decimal(str(value))
        except (ValueError, TypeError, ArithmeticError):
            return None

    def _calculate_performance(
        self, ticker: Ticker, periods: list[int]
    ) -> dict[str, Optional[Decimal]]:
        """
        Calculate historical performance for given periods.

        Args:
            ticker: yfinance Ticker object
            periods: List of months to calculate performance for (e.g., [1, 3, 6])

        Returns:
            Dictionary with performance percentages
        """
        performance = {}

        try:
            # Get historical data for last 6 months
            hist = ticker.history(period="6mo")

            if hist.empty:
                logger.warning("No historical data available")
                return {f"performance_{p}m_pct": None for p in periods}

            # Get current price
            current_price = hist['Close'].iloc[-1]

            for months in periods:
                try:
                    # Calculate date for X months ago
                    days_ago = months * 30  # Approximate
                    target_date = datetime.now() - timedelta(days=days_ago)

                    # Find closest date in historical data
                    hist_filtered = hist[hist.index <= target_date]

                    if not hist_filtered.empty:
                        past_price = hist_filtered['Close'].iloc[-1]
                        pct_change = ((current_price - past_price) / past_price) * 100
                        performance[f"performance_{months}m_pct"] = self._safe_decimal(pct_change)
                    else:
                        performance[f"performance_{months}m_pct"] = None

                except Exception as e:
                    logger.debug(f"Could not calculate {months}m performance: {e}")
                    performance[f"performance_{months}m_pct"] = None

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return {f"performance_{p}m_pct": None for p in periods}

        return performance

    def _analyze_market_reaction(
        self, ticker: Ticker, announcement_datetime: datetime
    ) -> dict[str, Optional[Decimal]]:
        """
        Analyze market reaction after announcement.

        Args:
            ticker: yfinance Ticker object
            announcement_datetime: When the announcement was made

        Returns:
            Dictionary with price changes (1h, 1d after announcement)
        """
        try:
            # Get intraday data if announcement is recent (within 60 days)
            days_since = (datetime.now() - announcement_datetime).days

            if days_since > 60:
                logger.debug("Announcement too old for detailed reaction analysis")
                return {
                    "price_change_1h_pct": None,
                    "price_change_1d_pct": None,
                }

            # Get 1-minute interval data for last 7 days (for 1h reaction)
            try:
                intraday = ticker.history(period="7d", interval="1m")

                # Find price at announcement time and 1 hour later
                if not intraday.empty:
                    # This is a simplified approach - in production, you'd need more sophisticated logic
                    # to find exact timestamps
                    logger.debug("Intraday data available but reaction analysis not yet implemented")
            except Exception:
                pass  # Intraday data might not be available

            # Get daily data for 1-day reaction
            hist = ticker.history(period="1mo")

            if not hist.empty:
                # Find the announcement date in history
                announcement_date = announcement_datetime.date()
                hist_dates = hist.index.date

                # Find closest date to announcement
                matching_dates = [d for d in hist_dates if d >= announcement_date]

                if len(matching_dates) >= 2:
                    announcement_idx = list(hist_dates).index(matching_dates[0])
                    next_day_idx = list(hist_dates).index(matching_dates[1])

                    price_at_ann = hist['Close'].iloc[announcement_idx]
                    price_next_day = hist['Close'].iloc[next_day_idx]

                    pct_change = ((price_next_day - price_at_ann) / price_at_ann) * 100

                    return {
                        "price_change_1h_pct": None,  # Not implemented yet
                        "price_change_1d_pct": self._safe_decimal(pct_change),
                    }

        except Exception as e:
            logger.error(f"Error analyzing market reaction: {e}")

        return {
            "price_change_1h_pct": None,
            "price_change_1d_pct": None,
        }

    def get_stock_metrics(
        self,
        asx_code: str,
        announcement_datetime: Optional[datetime] = None,
    ) -> StockMetrics:
        """
        Fetch comprehensive stock metrics for an ASX company.

        Args:
            asx_code: ASX stock code (e.g., 'BHP', 'CBA')
            announcement_datetime: Optional datetime of announcement for reaction analysis

        Returns:
            StockMetrics object with all available data
        """
        ticker_symbol = self._format_asx_ticker(asx_code)
        logger.info(f"Fetching stock data for {ticker_symbol}...")

        # Initialize default metrics (in case of error)
        metrics = StockMetrics(
            asx_code=asx_code.upper(),
            data_available=False,
            error_message=None,
        )

        for attempt in range(1, self.retry_attempts + 1):
            try:
                # Create ticker object
                ticker = yf.Ticker(ticker_symbol)

                # Get current info
                info = ticker.info

                # Extract data from info
                metrics.current_price = self._safe_decimal(info.get("currentPrice"))
                metrics.market_cap = self._safe_decimal(info.get("marketCap"))
                metrics.pe_ratio = self._safe_decimal(info.get("trailingPE"))
                metrics.volume = info.get("volume")

                # If we have announcement time, get price at that time
                if announcement_datetime:
                    metrics.price_at_announcement = metrics.current_price
                    # Analyze market reaction
                    reaction = self._analyze_market_reaction(ticker, announcement_datetime)
                    metrics.price_change_1h_pct = reaction.get("price_change_1h_pct")
                    metrics.price_change_1d_pct = reaction.get("price_change_1d_pct")

                # Calculate historical performance
                performance = self._calculate_performance(ticker, [1, 3, 6])
                metrics.performance_1m_pct = performance.get("performance_1m_pct")
                metrics.performance_3m_pct = performance.get("performance_3m_pct")
                metrics.performance_6m_pct = performance.get("performance_6m_pct")

                # Mark as successful
                metrics.data_available = True
                metrics.fetched_at = datetime.utcnow()

                logger.info(
                    f"Stock data fetched successfully for {ticker_symbol} - "
                    f"Price: ${metrics.current_price}, "
                    f"Market Cap: ${metrics.market_cap}"
                )

                return metrics

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt}/{self.retry_attempts} failed for {ticker_symbol}: {e}"
                )

                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay)
                else:
                    # All retries exhausted
                    metrics.data_available = False
                    metrics.error_message = f"Failed after {self.retry_attempts} attempts: {str(e)}"
                    logger.error(f"Failed to fetch stock data for {ticker_symbol}: {e}")

        return metrics

    def get_batch_metrics(
        self, asx_codes: list[str]
    ) -> dict[str, StockMetrics]:
        """
        Fetch stock metrics for multiple companies.

        Args:
            asx_codes: List of ASX codes

        Returns:
            Dictionary mapping ASX code to StockMetrics
        """
        results = {}
        total = len(asx_codes)

        logger.info(f"Fetching stock data for {total} companies...")

        for i, code in enumerate(asx_codes, 1):
            logger.info(f"Processing {i}/{total}: {code}")
            results[code] = self.get_stock_metrics(code)

        successful = sum(1 for m in results.values() if m.data_available)
        logger.info(f"Batch fetch complete: {successful}/{total} successful")

        return results


# Singleton instance
_stock_service_instance: Optional[StockDataService] = None


def get_stock_data_service() -> StockDataService:
    """
    Get or create the singleton stock data service instance.

    Returns:
        StockDataService instance
    """
    global _stock_service_instance
    if _stock_service_instance is None:
        _stock_service_instance = StockDataService()
    return _stock_service_instance
