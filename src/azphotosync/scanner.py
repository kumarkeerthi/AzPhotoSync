from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".heic",
    ".heif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
}


@dataclass(frozen=True)
class LocalAsset:
    path: Path
    rel_path: str
    size: int
    mtime_ns: int


def iter_assets(source_dir: Path):
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        stat = path.stat()
        yield LocalAsset(
            path=path,
            rel_path=path.relative_to(source_dir).as_posix(),
            size=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
        )


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()
