"""
Abstract base class for storage backends.

This defines the interface that all storage backends must implement,
allowing easy swapping between local file system, S3, R2, etc.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class StorageBackend(ABC):
    """
    Abstract base class for file storage backends.

    All storage backends (local, S3, R2) must implement these methods
    to provide a consistent interface for file operations.
    """

    @abstractmethod
    def save(self, file_path: str, content: bytes) -> str:
        """
        Save file content to storage.

        Args:
            file_path: Relative path where file should be saved (e.g., "pdfs/2025/11/BHP_123.pdf")
            content: Binary content of the file

        Returns:
            Full path/URL where file was saved

        Raises:
            StorageError: If save operation fails
        """
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_path: Relative path to check

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes:
        """
        Retrieve file content from storage.

        Args:
            file_path: Relative path to file

        Returns:
            Binary content of the file

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If retrieval fails
        """
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Relative path to file

        Returns:
            True if file was deleted, False if it didn't exist

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    def get_full_path(self, file_path: str) -> str:
        """
        Get the full path or URL for a stored file.

        Args:
            file_path: Relative path to file

        Returns:
            Full file system path or URL
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[str]:
        """
        List all files with a given prefix.

        Args:
            prefix: Path prefix to filter by (e.g., "pdfs/2025/11/")

        Returns:
            List of relative file paths
        """
        pass


class StorageError(Exception):
    """Base exception for storage operations."""

    pass
