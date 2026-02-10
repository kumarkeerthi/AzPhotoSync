import Foundation

final class SecureUploadClient {
    private let backendBaseURL: URL
    private let session: URLSession
    private let tokenStore = KeychainTokenStore()

    init(backendBaseURL: URL, session: URLSession = .shared) {
        self.backendBaseURL = backendBaseURL
        self.session = session
    }

    func requestUploadToken(userID: String, filename: String) async throws -> UploadTokenResponse {
        let endpoint = backendBaseURL.appending(path: "/v1/mobile/upload-token")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let bearer = tokenStore.read() {
            request.setValue("Bearer \(bearer)", forHTTPHeaderField: "Authorization")
        }

        let payload = UploadTokenRequest(userID: userID, filename: filename)
        request.httpBody = try JSONEncoder().encode(payload)

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(UploadTokenResponse.self, from: data)
    }

    func upload(data: Data, contentType: String, token: UploadTokenResponse) async throws {
        var request = URLRequest(url: token.uploadURL)
        request.httpMethod = "PUT"
        request.setValue("BlockBlob", forHTTPHeaderField: "x-ms-blob-type")
        request.setValue(contentType, forHTTPHeaderField: "Content-Type")

        let (_, response) = try await session.upload(for: request, from: data)
        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            throw URLError(.cannotWriteToFile)
        }
    }
}
