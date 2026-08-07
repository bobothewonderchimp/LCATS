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
import os
import pathlib
import tempfile
from typing import Any, Optional

from lcats.analysis import scene_analysis
from lcats.analysis.corpus import assess, discovery
from lcats.analysis.corpus import cli as corpus_cli
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


def _hash_json(obj: Any) -> str:
    """Deterministic hash of a JSON-serializable value (e.g. a tool
    schema), for checkpoint fingerprints."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _genre_fingerprint(model: str, story_data: dict, body: str) -> dict:
    """Fingerprint the complete effective assessment input, not just body
    -- assess_story also sends author/url (from metadata) to the model
    and stores them in AssessmentResult, so a metadata-only change (no
    body change) must still invalidate the checkpoint (review finding,
    PR #241). Title is intentionally excluded: infer_story_title derives
    it purely from the bucket directory name, already encoded in
    item_id -- it cannot change independently of that."""
    metadata = story_data.get("metadata") or {}
    return {
        "model": model,
        "system_prompt_hash": _hash_text(assess.DETECT_SYSTEM_PROMPT),
        "tool_schema_hash": _hash_json(assess.ASSESSMENT_TOOL),
        "author": metadata.get("author", "Unknown"),
        "url": metadata.get("url", ""),
        "body_hash": _hash_text(body),
    }


def _scenes_fingerprint(model: str, body: str) -> dict:
    return {
        "model": model,
        "system_prompt_hash": _hash_text(scene_analysis.SCENE_SEQUEL_SYSTEM_PROMPT),
        "user_prompt_template_hash": _hash_text(
            scene_analysis.SCENE_SEQUEL_USER_PROMPT_TEMPLATE
        ),
        "tool_schema_hash": _hash_json(scene_analysis.SEGMENT_TOOL_SCHEMA),
        "body_hash": _hash_text(body),
    }


def _annotate_genre(
    *,
    story_path: pathlib.Path,
    item_id: str,
    story_data: dict,
    body: str,
    backend: Any,
    model: str,
    roots: checkpoint.CheckpointRoots,
) -> tuple[Optional[dict], Optional[str]]:
    """Return (genre_data, error). genre_data is the sidecar payload to
    write; error is set (genre_data is None) only on an unrecoverable
    failure. A checkpoint hit skips the paid assess_story call entirely."""
    fingerprint = _genre_fingerprint(model, story_data, body)
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
    # Check alignment_error/validation_error too, not just api_error/
    # extraction_error -- JSONPromptExtractor.extract() still sets
    # extracted_output on an alignment/validation exception (the raw,
    # un-aligned parsed value), which is truthy and would otherwise be
    # recorded as a successful checkpoint (review finding, PR #241).
    error = (
        seg_result.get("api_error")
        or seg_result.get("extraction_error")
        or seg_result.get("alignment_error")
        or seg_result.get("validation_error")
    )
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
    """Atomically publish a sidecar file -- a plain write_text can leave
    torn JSON if interrupted mid-write even though the success checkpoint
    was already published (review finding, PR #241), the same failure
    mode checkpoint.write_checkpoint's own tempfile+os.replace pattern
    exists to prevent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(data, tmp_file, indent=2)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _remove_if_exists(path: pathlib.Path) -> None:
    path.unlink(missing_ok=True)


def _write_readme(
    bucket_dir: pathlib.Path, story_data: dict, story_path: pathlib.Path
) -> None:
    """Write/update the bucket's README.md summarizing story.json plus
    whatever sidecars exist. Never matched by any JSON-only selector
    (find_json_files, iter_collection_story_files), so this is purely
    additive -- no discovery/promote/stats changes needed."""
    title = corpus_cli.infer_story_title(story_data, story_path)
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

    story_data = corpus_cli.read_story_data(story_path)
    body = corpus_cli.coerce_story_text(story_data.get("body", ""))

    genre_data, genre_error = _annotate_genre(
        story_path=story_path,
        item_id=item_id,
        story_data=story_data,
        body=body,
        backend=backend,
        model=model,
        roots=roots,
    )
    # A failed recompute must not leave a stale sidecar from a prior,
    # differently-configured run in place -- the bucket would otherwise
    # silently mix a new-config scenes.json with an old-config genre.json
    # (review finding, PR #241).
    if genre_data is not None:
        _write_json(bucket_dir / "genre.json", genre_data)
    elif genre_error is not None:
        _remove_if_exists(bucket_dir / "genre.json")

    scenes_data, scenes_error = _annotate_scenes(
        item_id=item_id,
        body=body,
        backend=backend,
        model=model,
        roots=roots,
    )
    if scenes_data is not None:
        _write_json(bucket_dir / "scenes.json", scenes_data)
    elif scenes_error is not None:
        _remove_if_exists(bucket_dir / "scenes.json")

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
