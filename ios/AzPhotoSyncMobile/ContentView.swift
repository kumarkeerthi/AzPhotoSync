import Photos
import SwiftUI

struct ContentView: View {
    @StateObject private var vm = UploadViewModel()
    @State private var userID = "ios-user"

    private let columns = [GridItem(.adaptive(minimum: 90), spacing: 8)]

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                TextField("User ID", text: $userID)
                    .textFieldStyle(.roundedBorder)
                    .padding(.horizontal)

                ScrollView {
                    LazyVGrid(columns: columns, spacing: 8) {
                        ForEach(vm.assets, id: \.localIdentifier) { asset in
                            ZStack(alignment: .topTrailing) {
                                AssetThumbnail(asset: asset)
                                    .onTapGesture {
                                        vm.toggleSelection(for: asset)
                                    }

                                if vm.selectedAssetIDs.contains(asset.localIdentifier) {
                                    Image(systemName: "checkmark.circle.fill")
                                        .font(.title2)
                                        .foregroundStyle(.blue)
                                        .padding(6)
                                }
                            }
                        }
                    }
                    .padding(.horizontal)
                }

                Button("Secure Upload Selected") {
                    Task {
                        await vm.uploadSelected(userID: userID)
                    }
                }
                .buttonStyle(.borderedProminent)

                Text(vm.status)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal)
            }
            .navigationTitle("AzPhotoSync")
            .task { await vm.loadLibrary() }
        }
    }
}

private struct AssetThumbnail: View {
    let asset: PHAsset
    @State private var image: UIImage?

    var body: some View {
        Group {
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
            } else {
                Rectangle().fill(.gray.opacity(0.2))
            }
        }
        .frame(width: 100, height: 100)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .task { await loadThumbnail() }
    }

    private func loadThumbnail() async {
        await withCheckedContinuation { continuation in
            let size = CGSize(width: 180, height: 180)
            PHImageManager.default().requestImage(for: asset, targetSize: size, contentMode: .aspectFill, options: nil) { uiImage, _ in
                self.image = uiImage
                continuation.resume()
            }
        }
    }
}
