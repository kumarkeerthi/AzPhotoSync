import Foundation
import Photos

@MainActor
final class UploadViewModel: ObservableObject {
    @Published var assets: [PHAsset] = []
    @Published var selectedAssetIDs: Set<String> = []
    @Published var status: String = ""

    private let library = PhotoLibraryService()
    private let client = SecureUploadClient(backendBaseURL: URL(string: "https://your-backend.example.com")!)

    func loadLibrary() async {
        let auth = await library.requestPermission()
        guard auth == .authorized || auth == .limited else {
            status = "Photo permission denied"
            return
        }
        assets = library.fetchLatestAssets()
        status = "Loaded \(assets.count) photos"
    }

    func toggleSelection(for asset: PHAsset) {
        if selectedAssetIDs.contains(asset.localIdentifier) {
            selectedAssetIDs.remove(asset.localIdentifier)
        } else {
            selectedAssetIDs.insert(asset.localIdentifier)
        }
    }

    func uploadSelected(userID: String) async {
        let chosen = assets.filter { selectedAssetIDs.contains($0.localIdentifier) }
        guard !chosen.isEmpty else {
            status = "No photos selected"
            return
        }

        do {
            for asset in chosen {
                let data = try await library.loadData(for: asset)
                let filename = (asset.value(forKey: "filename") as? String) ?? "image.jpg"
                let token = try await client.requestUploadToken(userID: userID, filename: filename)
                try await client.upload(data: data, contentType: "application/octet-stream", token: token)
            }
            status = "Uploaded \(chosen.count) item(s) securely"
            selectedAssetIDs.removeAll()
        } catch {
            status = "Upload failed: \(error.localizedDescription)"
        }
    }
}
