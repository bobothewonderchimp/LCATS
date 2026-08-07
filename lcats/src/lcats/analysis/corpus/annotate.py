"""Fast-path annotation: genre + scene/sequel sidecars for story buckets.

Runs the two extractors mature enough to trust at scale -- `lcats assess`
(genre) and `scene_analysis` (scene/sequel segmentation) -- over story
buckets under a collection directory, writing `genre.json`/`scenes.json`
sidecars plus a per-bucket `README.md`, per WI-ANNOTATE-0051.

Checkpoint/output split (review-driven design decision, not incidental):
checkpoint.resolve_roots() refuses a working_root under data/ or corpora/
(data/ is a disposable cache, corpora/ is wholesale-copied by `lcats
promote` -- see checkpoint.py's own docstring), so checkpoint bookkeeping
lives in a dedicated --checkpoint-dir (default `.annotate_checkpoints/`,
never data/corpora/cache), separate from the real sidecar files this
module writes directly into each story's bucket directory under data/.
A checkpoint's own `data` field holds the actual computed sidecar
content, so re-materializing the sidecar file from an already-successful
checkpoint is always cheap and idempotent -- no re-payment for a paid
LLM call, even if a prior run was interrupted between recording the
checkpoint and writing the sidecar file itself.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
from typing import Any, Optional

from lcats.analysis import scene_analysis
from lcats.analysis.corpus import assess, discovery
from lcats.analysis.corpus.cli import (
    coerce_story_text,
    infer_story_title,
    read_story_data,
)
from lcats.utils import checkpoint


def _hash_text(text: str) -> str:
    """Deterministic hash of text, for checkpoint fingerprints -- not a
    security hash, just change detection (matches the pattern established
    in experiments/03_cross_segment_relation_pilot/run_pilot.py's
    _hash_json)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def story_item_id(collection_name: str, story_dir_name: str) -> str:
    """Flatten (collection, story) into a single checkpoint-safe item_id.

    Every canonical story file's own leaf filename is literally
    "story.json" post PROP-LCATS-STORY-BUCKET-LAYOUT, so identity must
    come from the bucket directory names, not the file itself. Combines
    collection + story bucket name with "__", since checkpoint item_ids
    must be a single path segment (see checkpoint._validate_path_component)
    -- the same pattern run_pilot.py's _story_identity already
    established for this identical collision risk.
    """
    return f"{collection_name}__{story_dir_name}"


@dataclasses.dataclass(frozen=True)
class AnnotateStoryResult:
    """Outcome of annotating a single story bucket."""

    story_path: pathlib.Path
    genre_error: Optional[str] = None
    scenes_error: Optional[str] = None

    @property
    def clean(self) -> bool:
        return self.genre_error is None and self.scenes_error is None


def _genre_fingerprint(model: str, body: str) -> dict:
    return {
        "model": model,
        "system_prompt_hash": _hash_text(assess.DETECT_SYSTEM_PROMPT),
        "body_hash": _hash_text(body),
    }


def _scenes_fingerprint(model: str, body: str) -> dict:
    return {
        "model": model,
        "system_prompt_hash": _hash_text(scene_analysis.SCENE_SEQUEL_SYSTEM_PROMPT),
        "body_hash": _hash_text(body),
    }


def _annotate_genre(
    *,
    story_path: pathlib.Path,
    item_id: str,
    body: str,
    backend: Any,
    model: str,
    roots: checkpoint.CheckpointRoots,
) -> tuple[Optional[dict], Optional[str]]:
    """Return (genre_data, error). genre_data is the sidecar payload to
    write; error is set (genre_data is None) only on an unrecoverable
    failure. A checkpoint hit skips the paid assess_story call entirely."""
    fingerprint = _genre_fingerprint(model, body)
    cached = checkpoint.read_checkpoint(
        roots.working_root, item_id, "genre", fingerprint
    )
    if cached.done and isinstance(cached.data, dict):
        return cached.data, None

    result = assess.assess_story(story_path, genre="", backend=backend, model=model)
    if result.error:
        checkpoint.write_checkpoint(
            roots.working_root,
            item_id,
            "genre",
            outcome="failure",
            fingerprint=fingerprint,
            data={"error": result.error},
        )
        return None, result.error

    data = result.to_dict()
    checkpoint.write_checkpoint(
        roots.working_root,
        item_id,
        "genre",
        outcome="success",
        fingerprint=fingerprint,
        data=data,
    )
    return data, None


def _annotate_scenes(
    *,
    item_id: str,
    body: str,
    backend: Any,
    model: str,
    roots: checkpoint.CheckpointRoots,
) -> tuple[Optional[dict], Optional[str]]:
    """Return (scenes_data, error), mirroring _annotate_genre's contract."""
    fingerprint = _scenes_fingerprint(model, body)
    cached = checkpoint.read_checkpoint(
        roots.working_root, item_id, "scenes", fingerprint
    )
    if cached.done and isinstance(cached.data, dict):
        return cached.data, None

    seg_extractor = scene_analysis.make_segment_extractor(backend)
    seg_result = seg_extractor.extract(body, model_name=model)
    error = seg_result.get("api_error") or seg_result.get("extraction_error")
    segments = seg_result.get("extracted_output") or []
    if error or not segments:
        error_message = str(error) if error else "segmentation produced no segments"
        checkpoint.write_checkpoint(
            roots.working_root,
            item_id,
            "scenes",
            outcome="failure",
            fingerprint=fingerprint,
            data={"error": error_message},
        )
        return None, error_message

    data = {"segments": segments, "segment_count": len(segments), "model": model}
    checkpoint.write_checkpoint(
        roots.working_root,
        item_id,
        "scenes",
        outcome="success",
        fingerprint=fingerprint,
        data=data,
    )
    return data, None


def _write_json(path: pathlib.Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_readme(
    bucket_dir: pathlib.Path, story_data: dict, story_path: pathlib.Path
) -> None:
    """Write/update the bucket's README.md summarizing story.json plus
    whatever sidecars exist. Never matched by any JSON-only selector
    (find_json_files, iter_collection_story_files), so this is purely
    additive -- no discovery/promote/stats changes needed."""
    title = infer_story_title(story_data, story_path)
    lines = [f"# {title}", ""]

    genre_path = bucket_dir / "genre.json"
    if genre_path.is_file():
        genre_data = json.loads(genre_path.read_text(encoding="utf-8"))
        lines.append("## genre.json")
        lines.append(
            f"- detected_genre: {genre_data.get('detected_genre', '')}"
            f" (confidence {genre_data.get('detected_genre_confidence', 0)})"
        )
        lines.append(f"- verdict: {genre_data.get('verdict', '')}")
        lines.append("")

    scenes_path = bucket_dir / "scenes.json"
    if scenes_path.is_file():
        scenes_data = json.loads(scenes_path.read_text(encoding="utf-8"))
        lines.append("## scenes.json")
        lines.append(f"- segment_count: {scenes_data.get('segment_count', 0)}")
        lines.append("")

    (bucket_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def annotate_story(
    story_path: pathlib.Path,
    *,
    collection_name: str,
    backend: Any,
    model: str,
    roots: checkpoint.CheckpointRoots,
) -> AnnotateStoryResult:
    """Annotate one story bucket: write genre.json, scenes.json, README.md.

    story_path is the story's own story.json file; sidecars are written
    into its parent (bucket) directory.
    """
    bucket_dir = story_path.parent
    item_id = story_item_id(collection_name, bucket_dir.name)

    story_data = read_story_data(story_path)
    body = coerce_story_text(story_data.get("body", ""))

    genre_data, genre_error = _annotate_genre(
        story_path=story_path,
        item_id=item_id,
        body=body,
        backend=backend,
        model=model,
        roots=roots,
    )
    if genre_data is not None:
        _write_json(bucket_dir / "genre.json", genre_data)

    scenes_data, scenes_error = _annotate_scenes(
        item_id=item_id,
        body=body,
        backend=backend,
        model=model,
        roots=roots,
    )
    if scenes_data is not None:
        _write_json(bucket_dir / "scenes.json", scenes_data)

    _write_readme(bucket_dir, story_data, story_path)

    return AnnotateStoryResult(
        story_path=story_path, genre_error=genre_error, scenes_error=scenes_error
    )


def annotate_collection(
    collection_dir: pathlib.Path,
    *,
    backend: Any,
    model: str,
    roots: checkpoint.CheckpointRoots,
) -> list[AnnotateStoryResult]:
    """Annotate every story bucket in one collection directory.

    Uses discovery.iter_collection_story_files, the same narrower
    bucket-only selector promote.survey_collection uses -- deliberately
    not find_json_files, and deliberately called once per collection
    (never directly against a multi-collection root; see
    annotate_collections below).
    """
    collection_name = collection_dir.name
    results = []
    for story_path in discovery.iter_collection_story_files(collection_dir):
        results.append(
            annotate_story(
                story_path,
                collection_name=collection_name,
                backend=backend,
                model=model,
                roots=roots,
            )
        )
    return results


def annotate_collections(
    source_root: pathlib.Path,
    *,
    backend: Any,
    model: str,
    roots: checkpoint.CheckpointRoots,
    collection_names: Optional[list[str]] = None,
) -> dict[str, list[AnnotateStoryResult]]:
    """Annotate every requested collection under source_root.

    Enumerates collection directories first (mirroring
    promote.promote_collections's pattern) and calls
    annotate_collection once per collection -- discovery.
    iter_collection_story_files silently yields nothing if given a
    multi-collection root directly, since it only checks one level of
    nesting (review finding, PR #226).
    """
    if collection_names is None:
        collection_names = sorted(
            entry.name for entry in source_root.iterdir() if entry.is_dir()
        )

    return {
        name: annotate_collection(
            source_root / name, backend=backend, model=model, roots=roots
        )
        for name in collection_names
    }
