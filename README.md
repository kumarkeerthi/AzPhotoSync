# AzPhotoSync

A production-minded, secure photo/video sync tool that pushes your local media library to Azure Blob Storage with a Google Photos-like reliability model:

- incremental scans
- deduplicated object paths by content hash
- resumable behavior with local sync index
- non-interactive authentication using Azure Identity

## Why this is Google-Photos-like

- **Automatic incremental sync**: only changed/new files are uploaded on subsequent runs.
- **Stable identity**: each asset is keyed by SHA-256 content hash and source-relative path.
- **Background-ready**: designed to run by scheduler (cron/systemd) or container job.
- **Large library support**: concurrent workers, retry/backoff on transient network issues.

## Security posture

- Uses `DefaultAzureCredential` (Managed Identity / Workload Identity / CLI identity), no hard-coded secrets.
- Supports least-privilege RBAC via `Storage Blob Data Contributor` scoped only to target container.
- Uses MIME-aware uploads and does not execute or transform media.
- Local metadata state is SQLite, containing hash/path/etag only (no secrets).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Azure setup

1. Create a storage account and private container.
2. Grant identity running this tool `Storage Blob Data Contributor` to that container.
3. Set environment variables (or pass CLI flags):

```bash
export AZURE_STORAGE_ACCOUNT_URL="https://<account>.blob.core.windows.net"
export AZURE_STORAGE_CONTAINER="photos-archive"
```

## iPhone app workflow (recommended)

Use the built-in **Files** app on iPhone with Azure Storage mounted through a third-party client that supports Blob Storage sync (for example, **PhotoSync** app, which can auto-transfer photos/videos to Azure Blob-compatible targets). Point uploads to this project's source folder on your always-on machine, then run `azphotosync` on a schedule.

Practical setup:

1. Install **PhotoSync** on iPhone and enable automatic transfer (Wi-Fi + charging).
2. Transfer to a folder watched by this tool (for example `/data/iphone-import`).
3. Run AzPhotoSync against that folder via systemd timer/cron.

This keeps phone-side automation simple and preserves end-to-end incremental syncing in Azure.


## Native iPhone app (new)

This repository now includes a SwiftUI iPhone client at `ios/AzPhotoSyncMobile` that provides a Google Photos-style experience (photo grid, multi-select, secure upload queue).

Security design:

- iOS never stores Azure account keys.
- iOS requests short-lived upload URLs from your backend.
- Backend should mint write-only SAS tokens using Managed Identity via `MobileTokenIssuer` (`src/azphotosync/mobile_auth.py`).
- Upload URLs are HTTPS-only and short-lived (default 10 minutes).

See `ios/AzPhotoSyncMobile/README.md` for integration details and backend API contract.

## Choosing the cheapest Azure storage tier

For your request (low cost, but still fast enough to download photos/videos), use:

- **Standard GPv2 storage account**
- **Blob access tier: `cool`** (recommended default)

Why `cool`:

- lower storage cost than `hot`
- retrieval is still online and generally fast enough for photo/video downloads
- avoids archive rehydration delays and complexity

Avoid `archive` for normal browsing/downloading because retrieval can take hours.

AzPhotoSync now supports upload tier selection via `--access-tier`.

## Usage

Dry run first:

```bash
azphotosync --source ~/Pictures --dry-run --verbose
```

Real sync:

```bash
azphotosync --source ~/Pictures --state-dir ~/.azphotosync --max-workers 8 --access-tier cool
```

## Production deployment patterns

### 1) Linux systemd timer (recommended for home server/NAS)

`/etc/systemd/system/azphotosync.service`

```ini
[Unit]
Description=AzPhotoSync job
After=network-online.target

[Service]
Type=oneshot
User=photosync
Environment=AZURE_STORAGE_ACCOUNT_URL=https://<account>.blob.core.windows.net
Environment=AZURE_STORAGE_CONTAINER=photos-archive
ExecStart=/opt/azphotosync/.venv/bin/azphotosync --source /data/photos --state-dir /var/lib/azphotosync --max-workers 8
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/azphotosync /data/photos
```

`/etc/systemd/system/azphotosync.timer`

```ini
[Unit]
Description=Run AzPhotoSync every 15 min

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

### 2) Containerized job

Run as a Kubernetes CronJob or Azure Container Apps scheduled job with Managed Identity.

## Data model

State DB (`index.db`) tracks per local file:

- relative path
- file size + mtime (fast unchanged checks)
- SHA-256 content hash
- Azure blob name + etag

Blob naming format:

```text
<prefix>/<sha[0:2]>/<sha256>/<relative/path/from/source>
```

This layout keeps object distribution balanced while preserving original structure.

## Limitations / roadmap

- No web gallery yet (upload/sync engine only).
- No album model yet.
- Optional future additions: thumbnail generation, face/object indexing with Azure AI Vision, signed-sharing links, lifecycle policies.

## Testing

```bash
pytest
```
