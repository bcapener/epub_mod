
https://github.com/jdanders/calibre-plugin-language-cleaner/tree/master

## Running the CLI

Project is managed with [uv](https://docs.astral.sh/uv). No install needed to
run from a checkout:

```sh
uv run src/main.py edit <path-to-epub>
```

Defaults to `<stem>_edit.epub` alongside the input file. Use `-o` for a custom
output:

```sh
uv run src/main.py edit <path-to-epub> -o <output.epub>
```

Other subcommands:

```sh
uv run src/main.py extract <path-to-epub> -o <dir>   # unzip an epub to a directory
uv run src/main.py make <dir> -o <output.epub>        # build an epub from a directory
```

## Installing with uv

Install the CLI as a user tool with an editable install, so changes to the
checkout take effect immediately:

```sh
uv tool install --editable .
```

The `epub-mod` command is then available anywhere:

```sh
epub-mod edit <path-to-epub>
```

To update after pulling changes (the editable install reflects the checkout, so
this is only needed when dependencies or entry points change):

```sh
uv tool install --editable .
```

To remove it:

```sh
uv tool uninstall epub-mod
```

## Adding more EPUB files

Test fixtures live in `tests/data/` and are stored with [Git LFS](https://git-lfs.com).

1. Copy the file into `tests/data/`:

   ```sh
   cp "/path/to/My Book - Author.epub" tests/data/
   ```

2. Add it to the index — Git LFS picks it up automatically via `.gitattributes`
   (`tests/data/*.epub`):

   ```sh
   git add "tests/data/My Book - Author.epub"
   ```

3. Commit as usual:

   ```sh
   git commit -m "Add test fixture: My Book"
   ```

EPUBs elsewhere in the repo are ignored by `.gitignore`; only `tests/data/*.epub`
is exempted and tracked through LFS.

## Managing Git LFS

Install LFS once per machine, then activate it in your clone:

```sh
sudo dnf install git-lfs   # Fedora; see https://github.com/git-lfs/git-lfs for other platforms
git lfs install            # wires up the clean/smudge filters for your user
```

Useful commands:

```sh
git lfs ls-files                     # list files currently tracked by LFS
git lfs track                        # show all tracked patterns
git lfs track "*.pdf"                # add another pattern (updates .gitattributes)
git lfs untrack "*.pdf"              # remove a pattern from .gitattributes
git lfs status                       # pending LFS changes between worktree/index/HEAD
git lfs migrate import --include="tests/data/*.epub" --everything   # rewrite history so old commits use LFS too
git lfs fetch --all && git lfs push --all origin   # back up every version of every LFS object
```

Notes:

- `.gitattributes` must be committed alongside any newly tracked files, or other
  clones will store the real bytes instead of LFS pointers.
- `git lfs migrate import` rewrites history and requires a force-push — coordinate
  with collaborators first.
- Cloning without git-lfs installed leaves pointer files instead of EPUBs;
  run `git lfs pull` after installing to recover them.

