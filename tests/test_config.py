from pathlib import Path

import pytest

from azphotosync.config import ConfigError, load_config


def test_load_config_reads_env(monkeypatch, tmp_path):
    source = tmp_path / "photos"
    source.mkdir()
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://acct.blob.core.windows.net")
    monkeypatch.setenv("AZURE_STORAGE_CONTAINER", "media")

    config = load_config(
        source_dir=str(source),
        state_dir=str(tmp_path / "state"),
        account_url=None,
        container=None,
        prefix="photos",
        dry_run=True,
        max_workers=4,
    )

    assert config.account_url == "https://acct.blob.core.windows.net"
    assert config.container == "media"
    assert config.state_dir.exists()


def test_load_config_requires_source(tmp_path):
    with pytest.raises(ConfigError):
        load_config(
            source_dir=str(tmp_path / "missing"),
            state_dir=str(tmp_path / "state"),
            account_url="https://acct.blob.core.windows.net",
            container="media",
            prefix="photos",
            dry_run=False,
            max_workers=4,
        )
