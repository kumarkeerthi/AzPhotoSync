from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from azphotosync.config import SyncConfig
from azphotosync.scanner import file_sha256, iter_assets
from azphotosync.state import FileRecord, SyncState

logger = logging.getLogger(__name__)


@dataclass
class SyncStats:
    scanned: int = 0
    uploaded: int = 0
    skipped: int = 0
    failed: int = 0


class SyncRunner:
    def __init__(self, config: SyncConfig):
        self._config = config

    def run(self) -> SyncStats:
        from azphotosync.storage import AzureBlobStore

        stats = SyncStats()
        store = AzureBlobStore(self._config.account_url, self._config.container)
        if not self._config.dry_run:
            store.ensure_container()

        with SyncState(self._config.db_path) as state:
            tasks = []
            with ThreadPoolExecutor(max_workers=self._config.max_workers) as pool:
                for asset in iter_assets(self._config.source_dir):
                    stats.scanned += 1
                    record = state.get_by_path(asset.rel_path)
                    if record and record.file_size == asset.size and record.mtime_ns == asset.mtime_ns:
                        stats.skipped += 1
                        continue
                    tasks.append(
                        pool.submit(
                            self._sync_asset,
                            asset.rel_path,
                            asset.size,
                            asset.mtime_ns,
                            asset.path,
                            store,
                            state,
                        )
                    )

                for fut in as_completed(tasks):
                    ok = fut.result()
                    if ok:
                        stats.uploaded += 1
                    else:
                        stats.failed += 1

        return stats

    def _sync_asset(self, rel_path, size, mtime_ns, path, store, state) -> bool:
        sha = file_sha256(path)
        blob_name = f"{self._config.prefix}/{sha[:2]}/{sha}/{rel_path}"
        if self._config.dry_run:
            logger.info("[DRY RUN] would upload %s -> %s", rel_path, blob_name)
            return True

        etag = self._upload_with_retry(store, path, blob_name)
        if etag is None:
            return False

        state.upsert(
            FileRecord(
                local_path=rel_path,
                file_size=size,
                mtime_ns=mtime_ns,
                sha256=sha,
                blob_name=blob_name,
                etag=etag,
            )
        )
        logger.info("Uploaded %s", rel_path)
        return True

    def _upload_with_retry(self, store, path, blob_name, retries: int = 3) -> str | None:
        delay = 1.0
        for attempt in range(1, retries + 1):
            try:
                return store.upload_file(path, blob_name)
            except Exception as exc:  # Azure SDK may not be installed in local dev env.
                name = exc.__class__.__name__
                if name == "ResourceExistsError":
                    logger.info("Blob already exists %s", blob_name)
                    return "existing"
                transient = {"ServiceRequestError", "ServiceResponseError", "AzureError"}
                if name in transient and attempt < retries:
                    logger.warning("Transient upload error (%s/%s): %s", attempt, retries, exc)
                    time.sleep(delay)
                    delay *= 2
                    continue
                logger.error("Failed upload %s: %s", blob_name, exc)
                return None
