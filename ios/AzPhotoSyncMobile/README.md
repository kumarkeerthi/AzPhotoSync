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

## Build, deploy, and run on your iPhone (step-by-step)

This section walks you from prerequisites to a real upload from your phone.

### 1) Prerequisites

1. A Mac with the latest stable Xcode installed.
2. An Apple ID signed into Xcode (`Xcode > Settings > Accounts`).
3. An iPhone signed into the same Apple ID and connected by cable (first setup) or available on local network (wireless debugging).
4. A backend endpoint that implements `POST /v1/mobile/upload-token` (contract above).
5. Azure Storage container already created for uploads.

### 2) Backend preparation (required before app testing)

1. Deploy your AzPhotoSync backend (or service containing `MobileTokenIssuer`) to a reachable HTTPS URL.
2. Grant backend identity `Storage Blob Data Contributor` to the target container.
3. Confirm your API can mint short-lived write-only SAS URLs.
4. Test token API from terminal before touching iOS:

```bash
curl -X POST "https://<your-backend>/v1/mobile/upload-token" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"ios-test-user","filename":"IMG_0001.HEIC"}'
```

Expected: JSON containing `upload_url`, `blob_name`, and `expires_at`.

### 3) Open project and configure iOS app

1. Open `ios/AzPhotoSyncMobile` in Xcode.
2. Select the app target and set:
   - **Bundle Identifier**: unique value you own, e.g. `com.<you>.azphotosyncmobile`.
   - **Team**: your personal/team Apple Developer signing team.
3. Verify `Info.plist` includes `NSPhotoLibraryUsageDescription` explaining why photos are needed.
4. Update `backendBaseURL` in `UploadViewModel.swift` to your deployed backend URL.

Example:

```swift
let backendBaseURL = URL(string: "https://api.example.com")!
```

### 4) Enable iPhone for development

1. Connect iPhone to Mac via USB.
2. On iPhone, tap **Trust This Computer** and enter passcode.
3. In Xcode, choose your iPhone as the run destination.
4. If prompted on iPhone for **Developer Mode**, enable it and reboot device.

### 5) Build and deploy from Xcode

1. In Xcode toolbar, confirm your iPhone is selected (not Simulator).
2. Press **Run** (`⌘R`).
3. If this is first install from your Apple ID:
   - On iPhone: `Settings > General > VPN & Device Management`.
   - Trust your developer certificate/profile.
4. Re-run from Xcode if needed after trusting profile.

When successful, the app launches on your phone.

### 6) First-run permission flow on iPhone

1. App asks for Photos access.
2. Choose **Allow Full Access** (recommended) or selected photos.
3. Confirm timeline thumbnails appear in the app grid.

### 7) End-to-end upload verification

1. Select one or more photos in the app.
2. Start upload.
3. Watch app status for completion.
4. Verify blobs landed in Azure container:

```bash
az storage blob list \
  --account-name <account> \
  --container-name <container> \
  --auth-mode login \
  --output table
```

You should see new blobs under your configured mobile prefix/path.

### 8) Troubleshooting checklist

- **401/403 during upload**: SAS token expired or lacks write permission.
- **Token endpoint fails**: backend auth or RBAC misconfiguration.
- **No photo thumbnails**: Photos permission denied; re-enable in iOS Settings.
- **Build/signing errors in Xcode**: Bundle ID not unique or wrong signing team selected.
- **App cannot reach backend**: verify HTTPS URL, certificates, and device network path.

### 9) Optional: testing without cable after first deploy

1. Keep iPhone and Mac on same Wi-Fi.
2. In Xcode `Window > Devices and Simulators`, enable **Connect via network**.
3. Next runs can be launched wirelessly from Xcode.
