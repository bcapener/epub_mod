import base64
import contextlib
import json
import os
import tempfile
import zipfile
from functools import partial
from pathlib import Path
from typing import Generator

import cleaner


def _normalize_name(name: str) -> str:
    return name.replace("\\", "/")


def walk(path: Path) -> Generator[Path, None, None]:
    for root, _dirs, files in os.walk(path):
        root = Path(root)
        for file in files:
            yield root / file


def extract_epub(path: Path, output_dir: Path|None=None):
    assert path.exists()
    assert path.suffix.lower() == ".epub"

    out = output_dir or path.parent / path.stem
    out.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(path, 'r') as zip_ref:
        rel_path_to_zip_info = zip_ref.NameToInfo
        zip_ref.extractall(out)

        manifest = []
        for name, info in rel_path_to_zip_info.items():
            manifest.append({
                "name": _normalize_name(name),
                "compress_type": info.compress_type,
                "CRC": info.CRC,
                "compress_level": getattr(info, "compress_level", getattr(info, "_compresslevel", None)),
                "date_time": list(info.date_time),
                "external_attr": info.external_attr,
                "internal_attr": info.internal_attr,
                "create_system": info.create_system,
                "comment": base64.b64encode(info.comment).decode("ascii") if info.comment else None,
            })

        (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))

    return out


@contextlib.contextmanager
def explode_epub(path: Path, output_path: Path|None=None):
    assert path.exists()
    assert path.suffix.lower() == ".epub"
    new_path = output_path or path.parent / f"{path.stem}_edit{path.suffix}"

    with tempfile.TemporaryDirectory() as temp_dir:
        epub_dir = extract_epub(path, Path(temp_dir))
        yield epub_dir
        make_epub(epub_dir, new_path)


def _zip_info_from_entry(entry: dict) -> zipfile.ZipInfo:
    name = entry["name"]
    if "date_time" in entry:
        info = zipfile.ZipInfo(name, date_time=tuple(entry["date_time"]))
    else:
        info = zipfile.ZipInfo(name)
    if "external_attr" in entry:
        info.external_attr = entry["external_attr"]
    if "internal_attr" in entry:
        info.internal_attr = entry["internal_attr"]
    if "create_system" in entry:
        info.create_system = entry["create_system"]
    comment_b64 = entry.get("comment")
    if comment_b64:
        info.comment = base64.b64decode(comment_b64)
    info.compress_type = entry["compress_type"]
    return info


def make_epub(path: Path, output_path: Path|None=None):
    assert path.is_dir()
    manifest_path = path / "MANIFEST.json"
    if not manifest_path.exists():
        raise RuntimeError(f"No MANIFEST.json found in '{path}'.")
    new_path = output_path or path.with_suffix(".epub")

    manifest = json.loads(manifest_path.read_text())
    for entry in manifest:
        entry["name"] = _normalize_name(entry["name"])
    rel_path_to_manifest_entry = {entry["name"]: entry for entry in manifest}

    rel_path_to_full_path = {}
    for file_path in walk(path):
        rel_path = file_path.relative_to(path).as_posix()
        if rel_path == "MANIFEST.json":
            continue
        if rel_path in rel_path_to_manifest_entry:
            rel_path_to_full_path[rel_path] = file_path

    # verify no files were added or removed.
    orig_files = sorted(n for n in rel_path_to_manifest_entry if not n.endswith('/'))
    curr_files = sorted(rel_path_to_full_path.keys())
    if orig_files != curr_files:
        raise RuntimeError("No files can be added or deleted from the epub.")

    with zipfile.ZipFile(new_path, 'w') as zip_ref:
        for entry in manifest:
            info = _zip_info_from_entry(entry)
            if entry["name"].endswith('/'):
                zip_ref.writestr(info, b'')
                continue
            full_path = rel_path_to_full_path[entry["name"]]
            zip_ref.writestr(info, full_path.read_bytes(),
                             compresslevel=entry.get("compress_level"))

    return new_path


def edit_epub(path: Path, output_path: Path|None=None):
    with explode_epub(path, output_path) as epub_dir:
        all_text = ""
        html_files = [f for f in walk(epub_dir) if "html" in f.suffix]
        for file_path in html_files:
            content = file_path.read_text()
            all_text += content

        replacement_list = cleaner.language_check(all_text)
        for file_path in html_files:
            text = file_path.read_text()
            output = ""
            for line in text.splitlines():
                # Go through all elements of replacement_list
                for search, sub, pcase in replacement_list:
                    if pcase:  # Preserve case
                        line = search.sub(partial(pcase, sub), line)
                    else:  # Don't preserve case
                        line = search.sub(sub, line)
                output += line + "\n"
            if text.replace('\n', "") == output.replace('\n', ''):
                print(f"Cleaned:   '{file_path}'")
            else:
                print(f"Unchanged: '{file_path}'")
            file_path.write_text(output)


if __name__ == "__main__":
    import argparse

    def _valid_epub_file(path_str) -> Path:
        path = Path(path_str).resolve()

        if not path.exists():
            raise argparse.ArgumentTypeError(f"Invalid path: {path_str}")

        return _valid_is_epub(path)


    def _valid_is_epub(path_str: str|Path) -> Path:
        path = Path(path_str).resolve()

        if path.suffix.lower() != ".epub":
            raise argparse.ArgumentTypeError(f"File must have an 'epub' extension. '{path_str}'")

        return path


    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=_valid_epub_file, help="path to an epub")
    parser.add_argument("-o", "--output", type=_valid_is_epub, default=None, help="output file name")
    args = parser.parse_args()

    edit_epub(args.path, args.output)

