from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyncConfig:
    source_dir: Path
    state_dir: Path
    account_url: str
    container: str
    prefix: str = "photos"
    dry_run: bool = False
    max_workers: int = 4
    access_tier: str = "cool"

    @property
    def db_path(self) -> Path:
        return self.state_dir / "index.db"


class ConfigError(ValueError):
    """Raised when configuration is invalid."""


def load_config(
    source_dir: str,
    state_dir: str,
    account_url: str | None,
    container: str | None,
    prefix: str,
    dry_run: bool,
    max_workers: int,
    access_tier: str,
) -> SyncConfig:
    source = Path(source_dir).expanduser().resolve()
    state = Path(state_dir).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        raise ConfigError(f"Source directory does not exist or is not a directory: {source}")

    state.mkdir(parents=True, exist_ok=True)

    resolved_account_url = account_url or os.getenv("AZURE_STORAGE_ACCOUNT_URL")
    resolved_container = container or os.getenv("AZURE_STORAGE_CONTAINER")

    if not resolved_account_url:
        raise ConfigError(
            "Azure account URL is required. Pass --account-url or set AZURE_STORAGE_ACCOUNT_URL"
        )
    if not resolved_container:
        raise ConfigError(
            "Azure container is required. Pass --container or set AZURE_STORAGE_CONTAINER"
        )
    if max_workers < 1 or max_workers > 32:
        raise ConfigError("--max-workers must be between 1 and 32")
    resolved_access_tier = access_tier.lower()
    if resolved_access_tier not in {"hot", "cool", "cold", "archive"}:
        raise ConfigError("--access-tier must be one of: hot, cool, cold, archive")

    return SyncConfig(
        source_dir=source,
        state_dir=state,
        account_url=resolved_account_url.rstrip("/"),
        container=resolved_container,
        prefix=prefix.strip("/"),
        dry_run=dry_run,
        max_workers=max_workers,
        access_tier=resolved_access_tier,
    )
