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

## Usage

Dry run first:

```bash
azphotosync --source ~/Pictures --dry-run --verbose
```

Real sync:

```bash
azphotosync --source ~/Pictures --state-dir ~/.azphotosync --max-workers 8
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
