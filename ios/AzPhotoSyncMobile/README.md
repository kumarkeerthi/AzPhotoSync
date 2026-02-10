# AzPhotoSyncMobile (iOS)

A SwiftUI iPhone client inspired by Google Photos UX:

- timeline grid from Photos library
- multi-select upload queue
- secure upload via short-lived SAS URL minted by your backend
- no Azure account keys stored on-device

## Security model

1. iOS authenticates to your backend (`/v1/mobile/upload-token`) with your app auth.
2. Backend uses `MobileTokenIssuer` (`src/azphotosync/mobile_auth.py`) and Managed Identity to mint a **write-only SAS URL** for one blob.
3. App uploads bytes directly to Azure Blob Storage over HTTPS.
4. SAS token expires quickly (default 10 minutes).

## App wiring

- Open this folder in Xcode as part of your iOS workspace.
- Ensure `NSPhotoLibraryUsageDescription` is present in Info.plist.
- Set `backendBaseURL` in `UploadViewModel`.

## Minimal backend contract

`POST /v1/mobile/upload-token`

Request:

```json
{
  "user_id": "ios-user-123",
  "filename": "IMG_0001.HEIC"
}
```

Response:

```json
{
  "blob_name": "mobile-import/ios-user-123/2026/02/10/101030-IMG_0001.HEIC",
  "upload_url": "https://...blob.core.windows.net/...?...",
  "expires_at": "2026-02-10T10:20:30Z"
}
```

The provided URL must be used with an HTTP `PUT` and header `x-ms-blob-type: BlockBlob`.
