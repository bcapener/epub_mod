import shutil
import zipfile
from pathlib import Path

import pytest

from main import explode_epub

DATA_DIR = Path(__file__).parent / "data"

ENTRY_METADATA_FIELDS = ("filename", "compress_type", "date_time", "external_attr", "internal_attr", "create_system")


def entry_metadata(info: zipfile.ZipInfo) -> tuple:
    return tuple(getattr(info, field) for field in ENTRY_METADATA_FIELDS)


@pytest.mark.parametrize("epub_path", sorted(DATA_DIR.glob("*.epub")), ids=lambda p: p.name)
def test_explode_epub_round_trip(epub_path: Path, tmp_path: Path):
    work_epub = tmp_path / epub_path.name
    shutil.copy(epub_path, work_epub)

    with explode_epub(work_epub) as epub_dir:
        assert Path(epub_dir).is_dir()

    rebuilt_epub = tmp_path / f"{work_epub.stem}_edit{work_epub.suffix}"
    assert rebuilt_epub.exists()

    with zipfile.ZipFile(work_epub) as original, zipfile.ZipFile(rebuilt_epub) as rebuilt:
        original_infos = original.infolist()
        rebuilt_infos = rebuilt.infolist()

        assert [entry_metadata(i) for i in original_infos] == [entry_metadata(i) for i in rebuilt_infos]

        for orig_info, new_info in zip(original_infos, rebuilt_infos):
            assert original.read(orig_info.filename) == rebuilt.read(new_info.filename)

        mimetype = original_infos[0]
        assert mimetype.filename == "mimetype"
        assert mimetype.compress_type == zipfile.ZIP_STORED


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
