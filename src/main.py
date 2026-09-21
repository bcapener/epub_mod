import argparse
import os
from pathlib import Path

from epub_mod import edit_epub, edit_epub_dir, extract_epub, make_epub


def _clean_path_arg(path_str: str) -> str:
    """Strip the stray quote PowerShell appends to Windows paths ending in a backslash.

    A double quote is never a valid character in a Windows path, so a trailing
    quote on Windows is always an artifact and safe to remove. On other
    platforms a quote may be a legitimate part of a filename and is preserved.
    """
    if os.name == "nt" and len(path_str) > 1 and path_str.endswith('"'):
        return path_str[:-1]
    return path_str


def _valid_epub_file(path_str) -> Path:
    path = Path(_clean_path_arg(path_str)).resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"Invalid path: {path_str}")

    return _valid_is_epub(path)


def _valid_is_epub(path_str: str|Path) -> Path:
    path = Path(_clean_path_arg(str(path_str))).resolve()

    if path.suffix.lower() != ".epub":
        raise argparse.ArgumentTypeError(f"File must have an 'epub' extension. '{path_str}'")

    return path


def _valid_dir(path_str) -> Path:
    path = Path(_clean_path_arg(path_str)).resolve()

    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Invalid directory: {path_str}")

    return path


def _valid_epub_dir(path_str) -> Path:
    path = _valid_dir(path_str)

    if not (path / "MANIFEST.json").exists():
        raise argparse.ArgumentTypeError(f"No MANIFEST.json found in directory: {path_str}")

    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    edit_parser = subparsers.add_parser("edit", help="clean profanity from an epub")
    edit_parser.add_argument("path", type=_valid_epub_file, help="path to an epub")
    edit_parser.add_argument("-o", "--output", type=_valid_is_epub, default=None, help="output file name")
    edit_parser.add_argument("-v", "--verbose", action="store_true", help="print details of each replacement")

    edit_dir_parser = subparsers.add_parser("edit-dir", help="clean profanity from an extracted epub directory")
    edit_dir_parser.add_argument("path", type=_valid_epub_dir, help="path to an extracted epub directory")
    edit_dir_parser.add_argument("-v", "--verbose", action="store_true", help="print details of each replacement")

    extract_parser = subparsers.add_parser("extract", help="extract an epub into a directory")
    extract_parser.add_argument("path", type=_valid_epub_file, help="path to an epub")
    extract_parser.add_argument("-o", "--output", type=Path, default=None, help="output directory")

    make_parser = subparsers.add_parser("make", help="build an epub from an extracted directory")
    make_parser.add_argument("path", type=_valid_dir, help="path to an extracted epub directory")
    make_parser.add_argument("-o", "--output", type=_valid_is_epub, default=None, help="output file name")

    args = parser.parse_args()

    if args.command == "edit":
        edit_epub(args.path, args.output, debug=args.verbose)
    elif args.command == "edit-dir":
        edit_epub_dir(args.path, debug=args.verbose)
    elif args.command == "extract":
        print(f"Extracted to '{extract_epub(args.path, args.output)}'")
    elif args.command == "make":
        print(f"Created '{make_epub(args.path, args.output)}'")


if __name__ == "__main__":
    main()