from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS file_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    local_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    blob_name TEXT NOT NULL,
    etag TEXT,
    last_synced_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_file_index_sha ON file_index (sha256);
"""


@dataclass
class FileRecord:
    local_path: str
    file_size: int
    mtime_ns: int
    sha256: str
    blob_name: str
    etag: str | None


class SyncState:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.executescript(SCHEMA)

    def get_by_path(self, local_path: str) -> FileRecord | None:
        cur = self._conn.execute(
            """
            SELECT local_path, file_size, mtime_ns, sha256, blob_name, etag
            FROM file_index
            WHERE local_path = ?
            """,
            (local_path,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return FileRecord(*row)

    def upsert(self, record: FileRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO file_index (local_path, file_size, mtime_ns, sha256, blob_name, etag, last_synced_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(local_path) DO UPDATE SET
                file_size = excluded.file_size,
                mtime_ns = excluded.mtime_ns,
                sha256 = excluded.sha256,
                blob_name = excluded.blob_name,
                etag = excluded.etag,
                last_synced_at = datetime('now')
            """,
            (
                record.local_path,
                record.file_size,
                record.mtime_ns,
                record.sha256,
                record.blob_name,
                record.etag,
            ),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SyncState":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
