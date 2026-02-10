from datetime import datetime, timezone

import pytest

from azphotosync.mobile_auth import MobileAuthError, MobileTokenIssuer


def test_constructor_rejects_bad_ttl() -> None:
    with pytest.raises(MobileAuthError):
        MobileTokenIssuer(
            account_url="https://example.blob.core.windows.net",
            container="photos",
            token_ttl_minutes=0,
        )


def test_sanitize_component_rejects_bad_characters() -> None:
    with pytest.raises(MobileAuthError):
        MobileTokenIssuer._sanitize_component("../../etc/passwd", "user_id")


def test_sanitize_filename_rejects_long_filename() -> None:
    too_long = "a" * 129
    with pytest.raises(MobileAuthError):
        MobileTokenIssuer._sanitize_filename(too_long)


def test_sanitize_filename_keeps_extension() -> None:
    output = MobileTokenIssuer._sanitize_filename("my-photo.mov")
    assert output == "my-photo.mov"


def test_issue_upload_token_builds_expected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeServiceClient:
        def get_user_delegation_key(self, starts_on: datetime, expires_on: datetime) -> str:
            assert starts_on.tzinfo == timezone.utc
            assert expires_on.tzinfo == timezone.utc
            return "delegation"

    issuer = MobileTokenIssuer.__new__(MobileTokenIssuer)
    issuer._account_url = "https://acct.blob.core.windows.net"
    issuer._container = "photos"
    issuer._prefix = "mobile-import"
    issuer._token_ttl_minutes = 10
    issuer._service_client = FakeServiceClient()

    monkeypatch.setattr(
        "azphotosync.mobile_auth.generate_blob_sas",
        lambda **kwargs: "sig=abc",
    )

    token = issuer.issue_upload_token("ios-user", "camera-roll.jpg")
    assert token.blob_name.startswith("mobile-import/ios-user/")
    assert token.blob_name.endswith("-camera-roll.jpg")
    assert token.upload_url.startswith("https://acct.blob.core.windows.net/photos/")
    assert token.upload_url.endswith("?sig=abc")
