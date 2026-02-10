from __future__ import annotations

import mimetypes
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings


class AzureBlobStore:
    def __init__(self, account_url: str, container_name: str):
        self._credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self._service = BlobServiceClient(account_url=account_url, credential=self._credential)
        self._container = self._service.get_container_client(container_name)

    def ensure_container(self) -> None:
        if not self._container.exists():
            self._container.create_container()

    def upload_file(self, local_path: Path, blob_name: str) -> str:
        blob = self._container.get_blob_client(blob_name)
        content_type = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
        with local_path.open("rb") as fd:
            resp = blob.upload_blob(
                fd,
                overwrite=False,
                max_concurrency=4,
                content_settings=ContentSettings(content_type=content_type),
            )
        return resp["etag"]
