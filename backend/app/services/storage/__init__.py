"""
Storage backends for PDF and markdown files.

This module provides a pluggable storage system that can work with:
- Local file system (development)
- AWS S3 (production)
- Cloudflare R2 (production alternative)
"""

from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorage
from app.services.storage.factory import get_storage_backend

__all__ = ["StorageBackend", "LocalStorage", "get_storage_backend"]
