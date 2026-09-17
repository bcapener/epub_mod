import base64
import contextlib
import json
import os
import sys
import tempfile
import zipfile
from functools import partial
from pathlib import Path
from typing import Generator

LANGUAGE_CLEANER_DIR = Path(__file__).resolve().parents[1] / "third_party" / "calibre-plugin-language-cleaner"
sys.path.insert(0, str(LANGUAGE_CLEANER_DIR))

import cleaner


def _normalize_name(name: str) -> str:
    return name.replace("\\", "/")


def walk(path: Path) -> Generator[Path, None, None]:
    for root, _dirs, files in os.walk(path):
        root = Path(root)
        for file in files:
            yield root / file


def extract_epub(path: Path, output_dir: Path|None=None) -> Path:
    """Extract an epub into a directory, returning that directory."""
    assert path.exists()
    assert path.suffix.lower() == ".epub"

    out = output_dir or path.parent / path.stem
    out.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(path, 'r') as zip_ref:
        rel_path_to_zip_info = zip_ref.NameToInfo
        zip_ref.extractall(out)

        manifest = {
            "header": {"version": "1.0"},
            "entries": [],
        }
        for name, info in rel_path_to_zip_info.items():
            manifest["entries"].append({
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
def explode_epub(path: Path, output_path: Path|None=None) -> Generator[Path, None, None]:
    """Extract an epub, yield its directory, then repackage it as an epub."""
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


def make_epub(path: Path, output_path: Path|None=None) -> Path:
    """Build an epub from an extracted directory, returning the output path."""
    assert path.is_dir()
    manifest_path = path / "MANIFEST.json"
    if not manifest_path.exists():
        raise RuntimeError(f"No MANIFEST.json found in '{path}'.")
    new_path = output_path or path.with_suffix(".epub")

    manifest = json.loads(manifest_path.read_text())
    entries = manifest["entries"] if isinstance(manifest, dict) else manifest
    for entry in entries:
        entry["name"] = _normalize_name(entry["name"])
    rel_path_to_manifest_entry = {entry["name"]: entry for entry in entries}

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
        for entry in entries:
            info = _zip_info_from_entry(entry)
            if entry["name"].endswith('/'):
                zip_ref.writestr(info, b'')
                continue
            full_path = rel_path_to_full_path[entry["name"]]
            zip_ref.writestr(info, full_path.read_bytes(),
                             compresslevel=entry.get("compress_level"))

    return new_path

def iter_lines(file_path: Path):
    with open(file_path, "r", newline="") as file:
        text = file.read()
        for line_no, line in enumerate(text.splitlines(keepends=True), start=1):
            if line.endswith("\r\n"):
                line, line_end = line[:-2], "\r\n"
            elif line.endswith("\n") or line.endswith("\r"):
                line, line_end = line[:-1], line[-1]
            else:
                line_end = ""
            yield line_no, line, line_end

class Cleaner:
    def __init__(self, epub_dir: Path):
        self.html_files = [f for f in walk(epub_dir) if "html" in f.suffix]

        all_text = ""
        for file_path in self.html_files:
            all_text += file_path.read_text()
        self.replacement_list = cleaner.language_check(all_text)

    def clean_line(self, line: str):
        curr_line = str(line)
        modifiers = []
        for search, sub, pcase in self.replacement_list:
            if pcase:  # Preserve case
                line = search.sub(partial(pcase, sub), line)
            else:  # Don't preserve case
                line = search.sub(sub, line)
            if curr_line != line:
                modifiers.append((search.pattern, sub))
            curr_line = str(line)
        return line, modifiers


def edit_epub_dir(epub_dir: Path, debug: bool=False):
    c = Cleaner(epub_dir)

    for file_path in c.html_files:
        modified = False
        lines = []
        for line_no, line, line_end in iter_lines(file_path):
            original_line = str(line)
            line, modifiers = c.clean_line(line)
            modified = modified or bool(modifiers)
            if debug and modifiers:
                mstr = ",".join(f"{repr(pattern)} -- {repr(sub)}" for pattern, sub in modifiers)
                print(f"  Replaced in '{file_path.name}' (line {line_no}): {mstr}")
                print(f"    Original: '{original_line}'")
                print(f"    New:      '{line}'")

            lines.append((line_no, original_line, line, line_end, modifiers))

        if not modified:
            continue
        print(f"Cleaned:   '{file_path}'")

        output = "".join(line + line_end for _, _, line, line_end, _ in lines)
        with open(file_path, "w", newline="") as file:
            file.write(output)


def edit_epub(path: Path, output_path: Path|None=None):
    with explode_epub(path, output_path) as epub_dir:
        edit_epub_dir(epub_dir, debug=False)