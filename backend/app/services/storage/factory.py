"""
Storage backend factory.

This module provides a factory function to get the appropriate storage
backend based on configuration settings.
"""

import logging
from app.config import settings
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorage

logger = logging.getLogger(__name__)


def get_storage_backend() -> StorageBackend:
    """
    Get the configured storage backend.

    Returns the appropriate storage implementation based on
    the STORAGE_TYPE configuration setting.

    Returns:
        StorageBackend instance

    Raises:
        ValueError: If storage type is not supported
    """
    storage_type = settings.storage_type.lower()

    if storage_type == "local":
        logger.info(f"Using local storage at: {settings.local_storage_path}")
        return LocalStorage(base_path=settings.local_storage_path)

    elif storage_type == "s3":
        # TODO: Implement S3 storage when needed
        raise NotImplementedError(
            "S3 storage not yet implemented. "
            "Use LOCAL storage for now or implement S3Storage class."
        )

    elif storage_type == "r2":
        # TODO: Implement Cloudflare R2 storage when needed
        raise NotImplementedError(
            "Cloudflare R2 storage not yet implemented. "
            "Use LOCAL storage for now or implement R2Storage class."
        )

    else:
        raise ValueError(
            f"Unknown storage type: {storage_type}. "
            f"Supported types: local, s3, r2"
        )


# Create a singleton instance for easy import
storage = get_storage_backend()
