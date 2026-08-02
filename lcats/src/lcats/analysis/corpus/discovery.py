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
    PROP-LCATS-STORY-BUCKET-LAYOUT, as retracted to bucket-only by
    Decision 4: a story is only ``<story>/story.json`` -- a subdirectory
    of ``collection_dir`` containing a file literally named
    ``story.json``. A flat ``<story>.json`` file directly in
    ``collection_dir`` is no longer a valid story source; the production
    ``corpora/`` snapshot has been confirmed fully migrated to the bucket
    layout (see ``WI-STORY-0045``'s execution record).

    Applies only one level of nesting relative to ``collection_dir``. A
    subdirectory without a canonical ``story.json`` is skipped, not searched
    further -- ``collection_dir`` is assumed to already be a single
    collection's own directory. Sibling JSON artifacts inside a story's own
    bucket directory (analysis output, override sidecars) are intentionally
    excluded, since only the canonical leaf name is accepted.

    Directory entries reached via a symlink are skipped, matching
    :func:`find_corpus_stories`'s default ``follow_symlinks=False``.
    """
    path = pathlib.Path(collection_dir)
    if not path.is_dir():
        return
    for entry in sorted(path.iterdir()):
        if entry.is_symlink() and entry.is_dir():
            continue
        if entry.is_dir():
            nested = entry / CANONICAL_STORY_FILENAME
            if nested.is_file():
                yield nested


def _walk_canonical_story_files(directory: pathlib.Path) -> Iterator[pathlib.Path]:
    """Recursively yield canonical story files under directory.

    First checks whether ``directory`` is itself a story bucket (contains
    its own ``story.json``) -- if so, yields only that canonical file and
    stops, regardless of what other JSON sidecars (``audit.json``,
    ``scenes.json``, ``events.json``, and similar per-story analysis
    artifacts) sit alongside it. Every other JSON file in a bucket
    directory is that story's own sidecar content, never an independent
    second story. This only matters when ``directory`` is handed to this
    function directly, as a top-level scan target (e.g. a caller pointing
    straight at one story's bucket) -- reaching a bucket directory via
    recursion from a collection is already handled by
    :func:`iter_collection_story_files`, which stops at the bucket
    boundary and never recurses into it.

    Otherwise applies :func:`iter_collection_story_files`'s bucket-only
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

    Bucket-only, per Decision 4 of PROP-LCATS-STORY-BUCKET-LAYOUT (dual-layout
    retraction): every story is ``<story>/story.json`` via
    :func:`_walk_canonical_story_files`. A JSON file is eligible only if it
    is literally named ``story.json`` -- whether reached by scanning a
    directory, or passed directly as a literal file path in ``directories``.
    A non-canonical file path passed directly is silently skipped, matching
    the same rule a directory scan applies; there is no longer a
    caller-knows-best exception, since the retraction's whole point is that
    ``story.json`` is the one and only valid marker everywhere.
    """
    for directory in directories:
        path = pathlib.Path(directory)
        if not path.exists():
            print(f"warning: directory does not exist: {directory}", file=sys.stderr)
            continue
        if path.is_file():
            if path.name == CANONICAL_STORY_FILENAME:
                yield path
            continue
        yield from _walk_canonical_story_files(path)
