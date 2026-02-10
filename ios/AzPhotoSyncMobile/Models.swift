import Foundation

struct UploadTokenResponse: Decodable {
    let blobName: String
    let uploadURL: URL
    let expiresAt: Date

    enum CodingKeys: String, CodingKey {
        case blobName = "blob_name"
        case uploadURL = "upload_url"
        case expiresAt = "expires_at"
    }
}

struct UploadTokenRequest: Encodable {
    let userID: String
    let filename: String

    enum CodingKeys: String, CodingKey {
        case userID = "user_id"
        case filename
    }
}
