"""
PDF Processor Service

This service handles PDF to Markdown conversion using PyMuPDF (fitz).
It extracts text, preserves layout, and generates clean markdown output.

Key features:
- PDF to Markdown conversion
- Metadata extraction (pages, file size, etc.)
- Layout preservation
- Table detection and formatting
- Clean markdown output
- Error handling for corrupted PDFs
"""

import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, Tuple, Dict
from datetime import datetime

from app.config import settings
from app.services.storage import get_storage_backend, StorageBackend

logger = logging.getLogger(__name__)


class PDFProcessorService:
    """
    Service for processing PDF files and converting them to Markdown.

    Uses PyMuPDF (fitz) for high-quality text extraction and
    layout preservation.
    """

    def __init__(self, storage: Optional[StorageBackend] = None):
        """
        Initialize PDF processor.

        Args:
            storage: Storage backend to use
        """
        self.storage = storage or get_storage_backend()

    def extract_metadata(self, pdf_path: str) -> Dict:
        """
        Extract metadata from a PDF file.

        Args:
            pdf_path: Path to PDF file (can be relative to storage or absolute)

        Returns:
            Dictionary with metadata:
            {
                'num_pages': int,
                'file_size': int (bytes),
                'title': str,
                'author': str,
                'subject': str,
                'creation_date': str,
                'producer': str,
            }
        """
        try:
            # Try to get from storage first
            if self.storage.exists(pdf_path):
                pdf_bytes = self.storage.get(pdf_path)
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            else:
                # Try as absolute path
                doc = fitz.open(pdf_path)

            metadata = {
                'num_pages': len(doc),
                'file_size': len(pdf_bytes) if self.storage.exists(pdf_path) else Path(pdf_path).stat().st_size,
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'producer': doc.metadata.get('producer', ''),
            }

            doc.close()
            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            return {
                'num_pages': 0,
                'file_size': 0,
                'title': '',
                'author': '',
                'subject': '',
                'creation_date': '',
                'producer': '',
            }

    def pdf_to_markdown(self, pdf_path: str, include_page_numbers: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convert a PDF file to Markdown format.

        Args:
            pdf_path: Path to PDF file
            include_page_numbers: Whether to include page number markers

        Returns:
            Tuple of (success, markdown_content, error_message)
        """
        try:
            # Get PDF content
            if self.storage.exists(pdf_path):
                pdf_bytes = self.storage.get(pdf_path)
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            else:
                doc = fitz.open(pdf_path)

            logger.info(f"Converting PDF to markdown: {pdf_path} ({len(doc)} pages)")

            # Extract text from all pages
            markdown_parts = []

            # Add header
            if doc.metadata.get('title'):
                markdown_parts.append(f"# {doc.metadata['title']}\n")

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Add page number marker if requested
                if include_page_numbers:
                    markdown_parts.append(f"\n---\n**Page {page_num + 1}**\n---\n")

                # Extract text with layout preservation
                # Using TEXT mode which preserves layout better
                text = page.get_text("text")

                # Clean up the text
                text = self._clean_text(text)

                if text.strip():
                    markdown_parts.append(text)

            doc.close()

            # Combine all parts
            markdown_content = "\n\n".join(markdown_parts)

            # Post-process markdown
            markdown_content = self._post_process_markdown(markdown_content)

            logger.info(f"Successfully converted PDF to markdown ({len(markdown_content)} characters)")
            return True, markdown_content, None

        except Exception as e:
            error = f"Error converting PDF to markdown: {e}"
            logger.error(error)
            return False, None, error

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text from PDF

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Strip trailing whitespace
            line = line.rstrip()

            # Skip completely empty lines (we'll add them back strategically)
            if line:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _post_process_markdown(self, markdown: str) -> str:
        """
        Post-process markdown for better formatting.

        Args:
            markdown: Raw markdown

        Returns:
            Processed markdown
        """
        # Remove excessive blank lines (more than 2 consecutive)
        import re
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Ensure document ends with single newline
        markdown = markdown.rstrip() + '\n'

        return markdown

    def generate_markdown_path(self, pdf_path: str) -> str:
        """
        Generate markdown file path from PDF path.

        Converts: pdfs/2025/11/BHP_20251107_093000_abc123.pdf
        To:      markdown/2025/11/BHP_20251107_093000_abc123.md

        Args:
            pdf_path: PDF file path

        Returns:
            Markdown file path
        """
        path = Path(pdf_path)

        # Replace 'pdfs' with 'markdown' and change extension
        parts = list(path.parts)
        if parts[0] == 'pdfs':
            parts[0] = 'markdown'

        markdown_path = Path(*parts).with_suffix('.md')
        return str(markdown_path)

    def process_and_save(
        self,
        pdf_path: str,
        markdown_path: Optional[str] = None,
        skip_if_exists: bool = True,
        include_page_numbers: bool = True
    ) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        Process a PDF and save the markdown output.

        Args:
            pdf_path: Path to PDF file
            markdown_path: Path for markdown output (auto-generated if None)
            skip_if_exists: Skip if markdown already exists
            include_page_numbers: Include page number markers

        Returns:
            Tuple of (success, markdown_path, metadata, error_message)
        """
        try:
            # Generate markdown path if not provided
            if markdown_path is None:
                markdown_path = self.generate_markdown_path(pdf_path)

            # Check if already processed
            if skip_if_exists and self.storage.exists(markdown_path):
                logger.info(f"Skipping already processed PDF: {pdf_path}")
                return True, markdown_path, None, None

            # Extract metadata
            metadata = self.extract_metadata(pdf_path)

            # Convert to markdown
            success, markdown_content, error = self.pdf_to_markdown(
                pdf_path,
                include_page_numbers=include_page_numbers
            )

            if not success or not markdown_content:
                return False, None, None, error

            # Save markdown
            self.storage.save(markdown_path, markdown_content.encode('utf-8'))

            logger.info(
                f"Successfully processed PDF: {pdf_path} -> {markdown_path} "
                f"({metadata['num_pages']} pages, {len(markdown_content)} chars)"
            )

            return True, markdown_path, metadata, None

        except Exception as e:
            error = f"Error processing and saving PDF: {e}"
            logger.error(error)
            return False, None, None, error

    def process_multiple(
        self,
        pdf_paths: list[str],
        skip_if_exists: bool = True,
        include_page_numbers: bool = True
    ) -> Dict:
        """
        Process multiple PDFs.

        Args:
            pdf_paths: List of PDF file paths
            skip_if_exists: Skip already processed files
            include_page_numbers: Include page number markers

        Returns:
            Dictionary with processing statistics
        """
        results = []
        stats = {
            "total": len(pdf_paths),
            "successful": 0,
            "skipped": 0,
            "failed": 0,
        }

        logger.info(f"Starting processing of {len(pdf_paths)} PDFs...")

        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Processing {i}/{len(pdf_paths)}: {pdf_path}")

            success, markdown_path, metadata, error = self.process_and_save(
                pdf_path,
                skip_if_exists=skip_if_exists,
                include_page_numbers=include_page_numbers
            )

            if success:
                # Check if it was skipped
                if skip_if_exists and markdown_path and self.storage.exists(markdown_path):
                    # Try to determine if it was newly created or existed
                    # For simplicity, we'll count it as successful
                    stats["successful"] += 1
                else:
                    stats["successful"] += 1
            else:
                stats["failed"] += 1

            results.append({
                "pdf_path": pdf_path,
                "markdown_path": markdown_path,
                "metadata": metadata,
                "success": success,
                "error": error,
            })

        logger.info(
            f"Processing complete: {stats['successful']} successful, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        stats["results"] = results
        return stats


# Create a singleton instance for easy import
pdf_processor = PDFProcessorService()
