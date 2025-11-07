"""
LLM Analyzer Service using Google Gemini API.

This service analyzes ASX announcements (in markdown format) and extracts:
- Summary (2-3 sentences)
- Sentiment (bullish/bearish/neutral)
- Key insights (3-5 bullet points)
- Financial impact assessment

The service is designed to be modular and can be easily swapped with other LLM providers.
"""

import json
import logging
import time
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.config import settings
from app.services.schemas import AnalysisResult

# Configure logging
logger = logging.getLogger(__name__)


class LLMAnalyzerService:
    """
    Service for analyzing ASX announcements using Google Gemini API.
    """

    def __init__(self):
        """Initialize the LLM analyzer with Gemini API configuration."""
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)

        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
            ),
        )

        logger.info(
            f"LLM Analyzer initialized with model: {settings.gemini_model}, "
            f"temperature: {settings.gemini_temperature}"
        )

    def _build_analysis_prompt(self, markdown_content: str) -> str:
        """
        Build the analysis prompt for the LLM.

        Args:
            markdown_content: The announcement content in markdown format

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a financial analyst specializing in Australian Securities Exchange (ASX) company announcements.

Analyze the following ASX company announcement and provide a structured analysis.

ANNOUNCEMENT CONTENT:
{markdown_content}

ANALYSIS REQUIREMENTS:
Please provide your analysis in the following JSON format:

{{
  "summary": "A concise 2-3 sentence summary of the announcement highlighting the most important information",
  "sentiment": "bullish|bearish|neutral",
  "key_insights": [
    "First key insight or important takeaway",
    "Second key insight or important takeaway",
    "Third key insight or important takeaway",
    "Fourth key insight (if applicable)",
    "Fifth key insight (if applicable)"
  ],
  "financial_impact": "Brief assessment of the potential impact on the company's stock price and market position",
  "confidence_score": 0.0-1.0
}}

GUIDELINES:
- **Summary**: Focus on material information that would affect investment decisions
- **Sentiment**:
  - "bullish" for positive news (revenue growth, new contracts, positive earnings, expansions)
  - "bearish" for negative news (losses, downgrades, regulatory issues, closures)
  - "neutral" for procedural/administrative announcements without clear market impact
- **Key Insights**: Extract 3-5 actionable insights that an investor should know
- **Financial Impact**: Consider both short-term and long-term implications
- **Confidence Score**: Your confidence in this analysis (0.0 = low, 1.0 = high)

Return ONLY the JSON object, no additional text.
"""
        return prompt

    def analyze_announcement(
        self, markdown_content: str, announcement_title: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze an announcement and extract insights using Gemini.

        Args:
            markdown_content: The announcement content in markdown format
            announcement_title: Optional title for logging purposes

        Returns:
            AnalysisResult containing summary, sentiment, insights, etc.

        Raises:
            Exception: If the API call fails or response parsing fails
        """
        start_time = time.time()

        try:
            # Build the prompt
            prompt = self._build_analysis_prompt(markdown_content)

            # Log request
            title_log = f" ({announcement_title})" if announcement_title else ""
            logger.info(f"Analyzing announcement{title_log}...")

            # Call Gemini API
            response = self.model.generate_content(prompt)

            # Extract response text
            response_text = response.text.strip()

            # Log raw response for debugging
            logger.debug(f"Raw LLM response: {response_text}")

            # Parse JSON response
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse the JSON
            analysis_data = json.loads(response_text)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create AnalysisResult
            result = AnalysisResult(
                summary=analysis_data.get("summary", ""),
                sentiment=analysis_data.get("sentiment", "neutral").lower(),
                key_insights=analysis_data.get("key_insights", []),
                financial_impact=analysis_data.get("financial_impact"),
                confidence_score=float(analysis_data.get("confidence_score", 0.0)),
                llm_model=settings.gemini_model,
                processing_time_ms=processing_time_ms,
            )

            logger.info(
                f"Analysis complete{title_log} - "
                f"Sentiment: {result.sentiment}, "
                f"Insights: {len(result.key_insights)}, "
                f"Time: {processing_time_ms}ms"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            raise Exception(f"Invalid JSON response from LLM: {e}")

        except Exception as e:
            logger.error(f"Error analyzing announcement: {e}")
            raise Exception(f"Failed to analyze announcement: {e}")

    def analyze_batch(
        self, announcements: list[tuple[str, str]]
    ) -> list[AnalysisResult]:
        """
        Analyze multiple announcements in batch.

        Args:
            announcements: List of (markdown_content, title) tuples

        Returns:
            List of AnalysisResult objects

        Note:
            This is a simple sequential implementation.
            For production, consider implementing concurrent processing with rate limiting.
        """
        results = []
        total = len(announcements)

        logger.info(f"Starting batch analysis of {total} announcements...")

        for i, (content, title) in enumerate(announcements, 1):
            try:
                logger.info(f"Processing {i}/{total}: {title}")
                result = self.analyze_announcement(content, title)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze announcement {i}/{total} ({title}): {e}")
                # Continue with next announcement
                continue

        logger.info(
            f"Batch analysis complete: {len(results)}/{total} successful"
        )

        return results


# Singleton instance
_analyzer_instance: Optional[LLMAnalyzerService] = None


def get_llm_analyzer() -> LLMAnalyzerService:
    """
    Get or create the singleton LLM analyzer instance.

    Returns:
        LLMAnalyzerService instance
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = LLMAnalyzerService()
    return _analyzer_instance
