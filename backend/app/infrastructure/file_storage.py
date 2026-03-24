"""File storage abstraction – local filesystem for MVP, swappable to S3."""

from __future__ import annotations

import os, shutil, uuid
from pathlib import Path

from app.config import settings


class FileStorage:
    """Read/write files to the configured storage root."""

    def __init__(self, root: str | None = None) -> None:
        self._root = Path(root or settings.FILE_STORAGE_PATH)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, source_path: str, *, prefix: str = "") -> str:
        """Copy file from *source_path* into storage, return relative path."""
        dest_name = f"{prefix}{uuid.uuid4().hex}_{Path(source_path).name}"
        dest = self._root / dest_name
        shutil.copy2(source_path, dest)
        return str(dest)

    def save_bytes(self, data: bytes, filename: str, *, prefix: str = "") -> str:
        """Write raw bytes to storage, return absolute path."""
        dest_name = f"{prefix}{uuid.uuid4().hex}_{filename}"
        dest = self._root / dest_name
        dest.write_bytes(data)
        return str(dest)

    def read_path(self, stored_path: str) -> Path:
        """Resolve a stored path to an absolute Path."""
        p = Path(stored_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {stored_path}")
        return p

    def delete(self, stored_path: str) -> None:
        p = Path(stored_path)
        if p.exists():
            os.remove(p)
