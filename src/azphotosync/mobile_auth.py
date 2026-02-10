from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from urllib.parse import urlparse

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

_SAFE_COMPONENT = re.compile(r"^[a-zA-Z0-9._-]+$")


class MobileAuthError(ValueError):
    """Raised when a mobile upload token request is invalid."""


@dataclass(frozen=True)
class MobileUploadToken:
    blob_name: str
    upload_url: str
    expires_at: datetime


class MobileTokenIssuer:
    """Issues short-lived, write-only SAS upload URLs for iOS clients."""

    def __init__(
        self,
        account_url: str,
        container: str,
        prefix: str = "mobile-import",
        token_ttl_minutes: int = 10,
    ) -> None:
        if token_ttl_minutes < 1 or token_ttl_minutes > 60:
            raise MobileAuthError("token_ttl_minutes must be between 1 and 60")

        self._account_url = account_url.rstrip("/")
        self._container = container
        self._prefix = prefix.strip("/")
        self._token_ttl_minutes = token_ttl_minutes

        self._credential = DefaultAzureCredential()
        self._service_client = BlobServiceClient(account_url=self._account_url, credential=self._credential)

    def issue_upload_token(self, user_id: str, original_filename: str) -> MobileUploadToken:
        safe_user = self._sanitize_component(user_id, "user_id")
        safe_name = self._sanitize_filename(original_filename)

        now = datetime.now(timezone.utc)
        starts_on = now - timedelta(minutes=1)
        expires_on = now + timedelta(minutes=self._token_ttl_minutes)

        delegation_key = self._service_client.get_user_delegation_key(starts_on, expires_on)
        blob_name = f"{self._prefix}/{safe_user}/{now.strftime('%Y/%m/%d/%H%M%S')}-{safe_name}"

        parsed = urlparse(self._account_url)
        account_name = parsed.netloc.split(".", 1)[0]

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=self._container,
            blob_name=blob_name,
            user_delegation_key=delegation_key,
            permission=BlobSasPermissions(create=True, write=True),
            start=starts_on,
            expiry=expires_on,
            protocol="https",
        )

        upload_url = f"{self._account_url}/{self._container}/{blob_name}?{sas_token}"
        return MobileUploadToken(blob_name=blob_name, upload_url=upload_url, expires_at=expires_on)

    @staticmethod
    def _sanitize_component(value: str, field_name: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise MobileAuthError(f"{field_name} is required")
        if len(candidate) > 64:
            raise MobileAuthError(f"{field_name} must be <= 64 chars")
        if not _SAFE_COMPONENT.fullmatch(candidate):
            raise MobileAuthError(f"{field_name} contains invalid characters")
        return candidate

    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        name = Path(filename).name.strip()
        if not name:
            raise MobileAuthError("original_filename is required")
        if len(name) > 128:
            raise MobileAuthError("original_filename must be <= 128 chars")

        pieces = name.split(".")
        sanitized_pieces: list[str] = []
        for piece in pieces:
            cleaned = cls._sanitize_component(piece, "original_filename_part")
            sanitized_pieces.append(cleaned)
        return ".".join(sanitized_pieces)
