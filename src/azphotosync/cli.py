from __future__ import annotations

import logging

import click

from azphotosync.config import ConfigError, load_config
from azphotosync.syncer import SyncRunner


@click.command()
@click.option("--source", "source_dir", required=True, type=click.Path(exists=True, file_okay=False))
@click.option("--state-dir", default="~/.azphotosync", show_default=True, type=click.Path(file_okay=False))
@click.option("--account-url", help="Azure storage account URL, e.g. https://myacct.blob.core.windows.net")
@click.option("--container", help="Blob container name")
@click.option("--prefix", default="photos", show_default=True, help="Prefix for uploaded blobs")
@click.option("--dry-run", is_flag=True, help="Scan and plan uploads without writing to Azure")
@click.option("--max-workers", default=4, show_default=True, help="Concurrent hashing/upload workers")
@click.option("--verbose", is_flag=True, help="Enable debug logs")
def main(source_dir, state_dir, account_url, container, prefix, dry_run, max_workers, verbose):
    """Sync local photo/video assets into Azure Blob Storage safely and incrementally."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        config = load_config(
            source_dir=source_dir,
            state_dir=state_dir,
            account_url=account_url,
            container=container,
            prefix=prefix,
            dry_run=dry_run,
            max_workers=max_workers,
        )
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    stats = SyncRunner(config).run()
    click.echo(
        f"scan={stats.scanned} uploaded={stats.uploaded} skipped={stats.skipped} failed={stats.failed}"
    )


if __name__ == "__main__":
    main()
