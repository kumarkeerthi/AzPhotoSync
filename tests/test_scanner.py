from azphotosync.scanner import file_sha256, iter_assets


def test_iter_assets_filters_media(tmp_path):
    p = tmp_path / "img.jpg"
    p.write_bytes(b"123")
    (tmp_path / "doc.txt").write_text("nope")

    assets = list(iter_assets(tmp_path))

    assert len(assets) == 1
    assert assets[0].rel_path == "img.jpg"


def test_file_sha256(tmp_path):
    p = tmp_path / "img.jpg"
    p.write_bytes(b"hello")

    assert file_sha256(p) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
