#!/usr/bin/env python3
"""
Test script for PDF processor service.

This script tests the PDF to Markdown conversion with real PDFs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from app.services.pdf_processor import pdf_processor
from app.services.storage import get_storage_backend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def main():
    """Main test function."""
    print_separator()
    print("Testing PDF Processor Service")
    print_separator()

    # Get storage backend
    storage = get_storage_backend()
    print(f"Storage backend: {type(storage).__name__}")
    if hasattr(storage, 'base_path'):
        print(f"Storage location: {storage.base_path}")

    # Step 1: List available PDFs
    print_separator()
    print("Step 1: Finding downloaded PDFs...")

    pdf_files = storage.list_files("pdfs/")
    print(f"Found {len(pdf_files)} PDF files")

    if not pdf_files:
        print("❌ No PDFs found. Please run test_playwright_downloader.py first.")
        return

    # Show first few
    print("\nFirst 5 PDFs:")
    for i, pdf_path in enumerate(pdf_files[:5], 1):
        if hasattr(storage, 'get_file_size'):
            size = storage.get_file_size(pdf_path)
            size_kb = size / 1024 if size else 0
            print(f"  {i}. {pdf_path} ({size_kb:.1f} KB)")
        else:
            print(f"  {i}. {pdf_path}")

    # Step 2: Test metadata extraction
    print_separator()
    print("Step 2: Testing metadata extraction...")

    test_pdf = pdf_files[0]
    print(f"\nExtracting metadata from: {test_pdf}")

    metadata = pdf_processor.extract_metadata(test_pdf)
    print(f"\nMetadata:")
    print(f"  Pages: {metadata['num_pages']}")
    print(f"  File size: {metadata['file_size']:,} bytes ({metadata['file_size']/1024:.1f} KB)")
    print(f"  Title: {metadata['title'] or '(none)'}")
    print(f"  Author: {metadata['author'] or '(none)'}")
    print(f"  Subject: {metadata['subject'] or '(none)'}")
    print(f"  Creation date: {metadata['creation_date'] or '(none)'}")
    print(f"  Producer: {metadata['producer'] or '(none)'}")

    # Step 3: Test single PDF conversion
    print_separator()
    print("Step 3: Testing single PDF conversion...")

    print(f"\nConverting: {test_pdf}")

    success, markdown_path, metadata, error = pdf_processor.process_and_save(
        test_pdf,
        skip_if_exists=False,
        include_page_numbers=True
    )

    if success:
        print(f"✓ Success: {markdown_path}")

        # Show markdown preview
        if storage.exists(markdown_path):
            markdown_content = storage.get(markdown_path).decode('utf-8')
            print(f"\nMarkdown preview (first 500 characters):")
            print("-" * 80)
            print(markdown_content[:500])
            print("-" * 80)
            print(f"\nTotal markdown length: {len(markdown_content):,} characters")

            # Count pages in markdown
            page_markers = markdown_content.count("**Page ")
            print(f"Page markers found: {page_markers}")
    else:
        print(f"❌ Failed: {error}")
        return

    # Step 4: Test batch processing
    print_separator()
    print("Step 4: Testing batch processing (first 3 PDFs)...")

    batch_pdfs = pdf_files[:3]
    print(f"\nProcessing {len(batch_pdfs)} PDFs...")

    stats = pdf_processor.process_multiple(
        batch_pdfs,
        skip_if_exists=True,
        include_page_numbers=True
    )

    print(f"\nBatch processing results:")
    print(f"  Total: {stats['total']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")

    # Show details
    print(f"\nDetailed results:")
    for i, result in enumerate(stats['results'], 1):
        pdf_path = Path(result['pdf_path']).name
        status = "✓ Success" if result['success'] else "❌ Failed"
        print(f"  {i}. {pdf_path}: {status}")

        if result['success'] and result['metadata']:
            md = result['metadata']
            print(f"     Pages: {md['num_pages']}, Size: {md['file_size']/1024:.1f} KB")

        if result['error']:
            print(f"     Error: {result['error']}")

    # Step 5: List generated markdown files
    print_separator()
    print("Step 5: Listing generated markdown files...")

    markdown_files = storage.list_files("markdown/")
    print(f"\nFound {len(markdown_files)} markdown files:")

    for i, md_path in enumerate(markdown_files[:10], 1):
        if hasattr(storage, 'get_file_size'):
            size = storage.get_file_size(md_path)
            size_kb = size / 1024 if size else 0
            print(f"  {i}. {md_path} ({size_kb:.1f} KB)")
        else:
            print(f"  {i}. {md_path}")

    if len(markdown_files) > 10:
        print(f"  ... and {len(markdown_files) - 10} more files")

    # Step 6: Verify a markdown file
    print_separator()
    print("Step 6: Verifying markdown file content...")

    if markdown_files:
        verify_md = markdown_files[0]
        print(f"\nReading: {verify_md}")

        try:
            content = storage.get(verify_md).decode('utf-8')
            lines = content.split('\n')

            print(f"\nMarkdown file stats:")
            print(f"  Total characters: {len(content):,}")
            print(f"  Total lines: {len(lines):,}")
            print(f"  Page markers: {content.count('**Page ')}")

            # Show first 10 lines
            print(f"\nFirst 10 lines:")
            for i, line in enumerate(lines[:10], 1):
                print(f"  {i}. {line[:100]}")

            print("\n✓ Markdown file is valid and readable")

        except Exception as e:
            print(f"❌ Error reading markdown: {e}")

    print_separator()
    print("✓ PDF Processor test completed!")
    print_separator()


if __name__ == "__main__":
    main()
