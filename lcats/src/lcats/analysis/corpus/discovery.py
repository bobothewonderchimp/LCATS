"""Corpus file discovery helpers."""

import os
import pathlib
import sys
import typing

from typing import Iterable, Iterator, Union

CANONICAL_STORY_FILENAME = "story.json"


def find_corpus_stories(
    root: Union[str, pathlib.Path],
    *,
    ignore_dir_names: Iterable[str] = ("cache",),
    follow_symlinks: bool = False,
    ignore_hidden: bool = False,
    sort: bool = True,
) -> list[pathlib.Path]:
    """Recursively list all JSON files under root."""
    root_path = pathlib.Path(root).expanduser()
    if not root_path.exists():
        raise FileNotFoundError(f"Root path not found: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Root is not a directory: {root_path}")

    ignore_set = {name.casefold() for name in ignore_dir_names}
    results: typing.List[pathlib.Path] = []

    for dirpath, dirnames, filenames in os.walk(
        root_path, topdown=True, followlinks=follow_symlinks
    ):
        pruned = []
        for directory_name in dirnames:
            if directory_name.casefold() in ignore_set:
                continue
            if ignore_hidden and directory_name.startswith("."):
                continue
            pruned.append(directory_name)
        dirnames[:] = pruned

        for filename in filenames:
            if ignore_hidden and filename.startswith("."):
                continue
            if filename.lower().endswith(".json"):
                results.append(pathlib.Path(dirpath) / filename)

    if sort:
        results.sort()
    return results


def iter_collection_story_files(
    collection_dir: Union[str, pathlib.Path],
) -> Iterator[pathlib.Path]:
    """Yield canonical story files that are immediate entries of collection_dir.

    The canonical story-file selector, per Decision 3 of
    PROP-LCATS-STORY-BUCKET-LAYOUT. Tolerates both layouts:

    - Flat: any ``<story>.json`` file directly in ``collection_dir``, other
      than the literal name ``story.json`` (reserved, see below).
    - Bucket: ``<story>/story.json`` -- a subdirectory of ``collection_dir``
      containing a file literally named ``story.json``.

    Applies only one level of nesting relative to ``collection_dir``. A
    subdirectory without a canonical ``story.json`` is skipped, not searched
    further -- ``collection_dir`` is assumed to already be a single
    collection's own directory. Sibling JSON artifacts inside a story's own
    bucket directory (analysis output, override sidecars) are intentionally
    excluded once nested, since only the canonical leaf name is accepted.

    ``story.json`` is reserved exclusively for the nested bucket marker: a
    flat file directly in ``collection_dir`` literally named ``story.json``
    is skipped (with a warning) rather than treated as an ordinary flat
    story. Without this reservation, a directory one level up could never
    structurally distinguish "a collection whose own flat file happens to be
    named story.json" from "a story's own bucket directory" -- the two look
    identical from outside. Reserving the name removes that ambiguity
    entirely instead of trying to guess it away.

    Directory entries reached via a symlink are skipped, matching
    :func:`find_corpus_stories`'s default ``follow_symlinks=False``.
    """
    path = pathlib.Path(collection_dir)
    if not path.is_dir():
        return
    for entry in sorted(path.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_file():
            if entry.suffix == ".json":
                if entry.name == CANONICAL_STORY_FILENAME:
                    print(
                        f"warning: skipping {entry} -- {CANONICAL_STORY_FILENAME!r} "
                        "is reserved for per-story bucket directories and cannot "
                        "be used as a flat story filename",
                        file=sys.stderr,
                    )
                    continue
                yield entry
        elif entry.is_dir():
            nested = entry / CANONICAL_STORY_FILENAME
            if nested.is_file():
                yield nested


def _walk_canonical_story_files(directory: pathlib.Path) -> Iterator[pathlib.Path]:
    """Recursively yield canonical story files under directory.

    First checks whether ``directory`` is itself a story bucket (contains
    its own ``story.json``) -- if so, yields only that canonical file and
    stops, regardless of what other JSON sidecars sit alongside it. This
    only matters when ``directory`` is handed to this function directly, as
    a top-level scan target (e.g. a caller pointing straight at one story's
    bucket) -- reaching a bucket directory via recursion from a collection
    is already handled by :func:`iter_collection_story_files`, which stops
    at the bucket boundary and never recurses into it.

    Otherwise applies :func:`iter_collection_story_files`'s flat-vs-bucket
    predicate to ``directory``, then recurses into subdirectories that are
    not themselves story buckets -- so this behaves correctly whether
    ``directory`` is a corpus root (immediate children are collection
    directories), a single collection directory, or a single story's own
    directory.
    """
    canonical = directory / CANONICAL_STORY_FILENAME
    if canonical.is_file():
        yield canonical
        return
    yield from iter_collection_story_files(directory)
    for entry in sorted(directory.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_dir() and not (entry / CANONICAL_STORY_FILENAME).is_file():
            yield from _walk_canonical_story_files(entry)


def find_json_files(
    directories: Iterable[Union[str, pathlib.Path]],
) -> Iterator[pathlib.Path]:
    """Yield canonical story files from provided paths in deterministic order.

    Tolerates both the flat and per-story-bucket layouts (Decision 3 of
    PROP-LCATS-STORY-BUCKET-LAYOUT) via :func:`_walk_canonical_story_files`:
    a JSON file directly inside whatever directory is being scanned is always
    eligible regardless of name; a JSON file reached by descending into a
    subdirectory is eligible only if it is literally named ``story.json``.
    """
    for directory in directories:
        path = pathlib.Path(directory)
        if not path.exists():
            print(f"warning: directory does not exist: {directory}", file=sys.stderr)
            continue
        if path.is_file():
            if path.suffix == ".json":
                yield path
            continue
        yield from _walk_canonical_story_files(path)
