import json
import shutil
import zipfile
from pathlib import Path

import pytest

from epub_mod import explode_epub, extract_epub, make_epub

DATA_DIR = Path(__file__).parent / "data"

ENTRY_METADATA_FIELDS = ("filename", "compress_type", "date_time", "external_attr", "internal_attr", "create_system")


def entry_metadata(info: zipfile.ZipInfo) -> tuple:
    return tuple(getattr(info, field) for field in ENTRY_METADATA_FIELDS)


def assert_same_epub(original_path: Path, rebuilt_path: Path):
    with zipfile.ZipFile(original_path) as original, zipfile.ZipFile(rebuilt_path) as rebuilt:
        original_infos = original.infolist()
        rebuilt_infos = rebuilt.infolist()

        assert [entry_metadata(i) for i in original_infos] == [entry_metadata(i) for i in rebuilt_infos]

        for orig_info, new_info in zip(original_infos, rebuilt_infos):
            assert original.read(orig_info.filename) == rebuilt.read(new_info.filename)

        mimetype = original_infos[0]
        assert mimetype.filename == "mimetype"
        assert mimetype.compress_type == zipfile.ZIP_STORED


@pytest.mark.parametrize("epub_path", sorted(DATA_DIR.glob("*.epub")), ids=lambda p: p.name)
def test_explode_epub_round_trip(epub_path: Path, tmp_path: Path):
    work_epub = tmp_path / epub_path.name
    shutil.copy(epub_path, work_epub)

    with explode_epub(work_epub) as epub_dir:
        assert Path(epub_dir).is_dir()

    rebuilt_epub = tmp_path / f"{work_epub.stem}_edit{work_epub.suffix}"
    assert rebuilt_epub.exists()

    assert_same_epub(work_epub, rebuilt_epub)


@pytest.mark.parametrize("epub_path", sorted(DATA_DIR.glob("*.epub")), ids=lambda p: p.name)
def test_extract_make_round_trip(epub_path: Path, tmp_path: Path):
    epub_dir = extract_epub(epub_path, tmp_path / epub_path.stem)
    rebuilt_epub = make_epub(epub_dir, tmp_path / f"{epub_path.stem}_made.epub")

    assert_same_epub(epub_path, rebuilt_epub)


def test_make_epub_supports_legacy_manifest(tmp_path: Path):
    epub_dir = tmp_path / "book"
    (epub_dir / "META-INF").mkdir(parents=True)
    (epub_dir / "mimetype").write_bytes(b"application/epub+zip")
    (epub_dir / "META-INF" / "container.xml").write_text("<container/>")
    (epub_dir / "chapter.xhtml").write_text("<p>hi</p>")
    (epub_dir / "MANIFEST.json").write_text(json.dumps([
        {"name": "mimetype", "compress_type": 0, "CRC": 0, "compress_level": None},
        {"name": "META-INF/", "compress_type": 0, "CRC": 0, "compress_level": None},
        {"name": "META-INF/container.xml", "compress_type": 8, "CRC": 0, "compress_level": 9},
        {"name": "chapter.xhtml", "compress_type": 8, "CRC": 0, "compress_level": None},
    ]))

    out = make_epub(epub_dir, tmp_path / "book.epub")

    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert z.namelist() == ["mimetype", "META-INF/", "META-INF/container.xml", "chapter.xhtml"]


def test_make_epub_normalizes_windows_separators(tmp_path: Path):
    epub_dir = tmp_path / "book"
    (epub_dir / "META-INF").mkdir(parents=True)
    (epub_dir / "mimetype").write_bytes(b"application/epub+zip")
    (epub_dir / "META-INF/container.xml").write_text("<container/>")
    (epub_dir / "chapter.xhtml").write_text("<p>hi</p>")
    (epub_dir / "MANIFEST.json").write_text(json.dumps([
        {"name": "mimetype", "compress_type": 0, "CRC": 0, "compress_level": None},
        {"name": "META-INF\\", "compress_type": 0, "CRC": 0, "compress_level": None},
        {"name": "META-INF\\container.xml", "compress_type": 8, "CRC": 0, "compress_level": 9},
        {"name": "chapter.xhtml", "compress_type": 8, "CRC": 0, "compress_level": None},
    ]))

    out = make_epub(epub_dir, tmp_path / "book.epub")

    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert z.namelist() == ["mimetype", "META-INF/", "META-INF/container.xml", "chapter.xhtml"]


def test_explode_epub_rejects_added_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    epub_path = next(DATA_DIR.glob("*.epub"))
    work_epub = tmp_path / epub_path.name
    shutil.copy(epub_path, work_epub)

    def add_stray_file(_self, path: str) -> None:
        (Path(path) / "stray.txt").write_text("nope")

    monkeypatch.setattr(zipfile.ZipFile, "extractall", add_stray_file)

    with pytest.raises(RuntimeError, match="No files can be added or deleted"):
        with explode_epub(work_epub):
            pass


def test_explode_epub_rejects_deleted_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    epub_path = next(DATA_DIR.glob("*.epub"))
    work_epub = tmp_path / epub_path.name
    shutil.copy(epub_path, work_epub)

    real_extractall = zipfile.ZipFile.extractall

    def drop_mimetype(_self, path: str) -> None:
        real_extractall(_self, path)
        (Path(path) / "mimetype").unlink()

    monkeypatch.setattr(zipfile.ZipFile, "extractall", drop_mimetype)

    with pytest.raises(RuntimeError, match="No files can be added or deleted"):
        with explode_epub(work_epub):
            pass

    assert not (tmp_path / f"{work_epub.stem}_edit{work_epub.suffix}").exists()
