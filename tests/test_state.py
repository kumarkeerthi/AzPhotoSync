from azphotosync.state import FileRecord, SyncState


def test_state_upsert_and_get(tmp_path):
    db = tmp_path / "index.db"
    with SyncState(db) as state:
        record = FileRecord(
            local_path="a/b.jpg",
            file_size=100,
            mtime_ns=200,
            sha256="abc",
            blob_name="photos/ab/abc/a/b.jpg",
            etag="1",
        )
        state.upsert(record)

        loaded = state.get_by_path("a/b.jpg")
        assert loaded is not None
        assert loaded.sha256 == "abc"

        state.upsert(
            FileRecord(
                local_path="a/b.jpg",
                file_size=101,
                mtime_ns=300,
                sha256="def",
                blob_name="photos/de/def/a/b.jpg",
                etag="2",
            )
        )
        loaded = state.get_by_path("a/b.jpg")
        assert loaded is not None
        assert loaded.sha256 == "def"
        assert loaded.file_size == 101
