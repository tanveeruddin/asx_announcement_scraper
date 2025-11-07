"""
Local file system storage backend.

This implementation stores files on the local file system,
suitable for development and testing.
"""

import logging
from pathlib import Path
from typing import Optional

from app.services.storage.base import StorageBackend, StorageError

logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    """
    Local file system storage implementation.

    Files are stored in a configurable base directory with proper
    directory structure and permissions.
    """

    def __init__(self, base_path: str = "./data"):
        """
        Initialize local storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path).resolve()
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Create base directory if it doesn't exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage initialized at: {self.base_path}")
        except Exception as e:
            raise StorageError(f"Failed to create base directory: {e}")

    def _get_full_path(self, file_path: str) -> Path:
        """
        Get full file system path for a relative path.

        Args:
            file_path: Relative path

        Returns:
            Full Path object
        """
        # Remove leading slash if present
        file_path = file_path.lstrip("/")
        full_path = self.base_path / file_path

        # Security check: ensure path is within base directory
        try:
            full_path.resolve().relative_to(self.base_path)
        except ValueError:
            raise StorageError(f"Invalid path: {file_path} (path traversal detected)")

        return full_path

    def save(self, file_path: str, content: bytes) -> str:
        """
        Save file to local file system.

        Args:
            file_path: Relative path where file should be saved
            content: Binary content

        Returns:
            Full file system path

        Raises:
            StorageError: If save fails
        """
        try:
            full_path = self._get_full_path(file_path)

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            full_path.write_bytes(content)

            logger.debug(f"Saved file to: {full_path}")
            return str(full_path)

        except Exception as e:
            raise StorageError(f"Failed to save file {file_path}: {e}")

    def exists(self, file_path: str) -> bool:
        """
        Check if file exists.

        Args:
            file_path: Relative path to check

        Returns:
            True if file exists
        """
        try:
            full_path = self._get_full_path(file_path)
            return full_path.exists() and full_path.is_file()
        except StorageError:
            return False

    def get(self, file_path: str) -> bytes:
        """
        Retrieve file content.

        Args:
            file_path: Relative path to file

        Returns:
            Binary content

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If retrieval fails
        """
        try:
            full_path = self._get_full_path(file_path)

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            return full_path.read_bytes()

        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to read file {file_path}: {e}")

    def delete(self, file_path: str) -> bool:
        """
        Delete a file.

        Args:
            file_path: Relative path to file

        Returns:
            True if deleted, False if didn't exist

        Raises:
            StorageError: If deletion fails
        """
        try:
            full_path = self._get_full_path(file_path)

            if not full_path.exists():
                return False

            full_path.unlink()
            logger.debug(f"Deleted file: {full_path}")
            return True

        except Exception as e:
            raise StorageError(f"Failed to delete file {file_path}: {e}")

    def get_full_path(self, file_path: str) -> str:
        """
        Get full file system path.

        Args:
            file_path: Relative path

        Returns:
            Full file system path as string
        """
        return str(self._get_full_path(file_path))

    def list_files(self, prefix: str = "") -> list[str]:
        """
        List all files with a given prefix.

        Args:
            prefix: Path prefix to filter by

        Returns:
            List of relative file paths
        """
        try:
            if prefix:
                search_path = self._get_full_path(prefix)
            else:
                search_path = self.base_path

            if not search_path.exists():
                return []

            # Find all files recursively
            files = []
            if search_path.is_file():
                # If prefix is a file, return just that file
                files = [str(search_path.relative_to(self.base_path))]
            else:
                # List all files in directory recursively
                for file_path in search_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(self.base_path)
                        files.append(str(relative_path))

            return sorted(files)

        except Exception as e:
            logger.error(f"Failed to list files with prefix '{prefix}': {e}")
            return []

    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            file_path: Relative path to file

        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            full_path = self._get_full_path(file_path)
            if full_path.exists():
                return full_path.stat().st_size
            return None
        except Exception:
            return None
