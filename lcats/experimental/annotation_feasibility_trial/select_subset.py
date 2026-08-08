"""Build a small genre-balanced subset of corpora/ stories for the
lcats annotate feasibility trial (WI-ANNOTATE-0054).

The 24 (collection, story) picks below were chosen by hand, reading
each candidate's title/author/opening text directly -- no lcats assess
or other paid API call was used to build this subset, since the whole
point is to test annotate's own genre detection against an independent
provisional guess, not to bootstrap the guess from the same model.

Run from the corpora/ repo root's sibling `lcats/` directory:

    python3 experimental/annotation_feasibility_trial/select_subset.py

Writes each selected story's story.json into
experimental/annotation_feasibility_trial/source/trial/<story>/story.json
-- `source/` is the --source root lcats annotate takes, and `trial/` is
its one collection directory (the bucket layout lcats annotate expects:
a source root containing collection directories, each containing one
subdirectory per story) -- and a subset_manifest.md documenting the
selection.
"""

from __future__ import annotations

import json
import pathlib
import shutil

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CORPORA_ROOT = REPO_ROOT / "corpora"
SOURCE_ROOT = pathlib.Path(__file__).resolve().parent / "source"
TRIAL_DIR = SOURCE_ROOT / "trial"
MANIFEST_PATH = pathlib.Path(__file__).resolve().parent / "subset_manifest.md"

# (source collection/story under corpora/, provisional genre guess,
# one-line rationale for the guess -- title/author/setting only, not
# a full read).
SELECTIONS: tuple[tuple[str, str, str], ...] = (
    (
        "mass_quantities/a_martian_odyssey__weinbaum",
        "science fiction",
        "Classic pulp SF; Mars exploration, alien contact (Weinbaum).",
    ),
    (
        "mass_quantities/2_b_r_0_2_b__vonnegut",
        "science fiction",
        "Vonnegut dystopian-future SF (population control, euthanasia).",
    ),
    (
        "mass_quantities/a_city_near_centaurus__doede",
        "science fiction",
        "Title signals interstellar/space setting.",
    ),
    (
        "lovecraft/the_call_of_cthulhu",
        "horror",
        "Lovecraft; cosmic horror, canonical genre example.",
    ),
    (
        "lovecraft/the_dunwich_horror",
        "horror",
        "Lovecraft; supernatural threat, title says horror.",
    ),
    (
        "lovecraft/the_colour_out_of_space",
        "horror",
        "Lovecraft; dread/alien contamination horror.",
    ),
    (
        "wodehouse/extricating_young_gussie",
        "humor",
        "Wodehouse; farcical comedy of manners.",
    ),
    (
        "wodehouse/crowned_heads",
        "humor",
        "Wodehouse; comedic tone throughout the collection.",
    ),
    (
        "wodehouse/one_touch_of_nature",
        "humor",
        "Wodehouse; comedic tone throughout the collection.",
    ),
    (
        "grimm/rapunzel",
        "fantasy",
        "Fairy tale; magic, witch, tower -- fantasy elements.",
    ),
    (
        "grimm/hansel_and_gretel",
        "fantasy",
        "Fairy tale; witch, magic forest -- fantasy elements.",
    ),
    (
        "grimm/snow_white_and_rose_red",
        "fantasy",
        "Fairy tale; enchanted bear/dwarf -- fantasy elements.",
    ),
    (
        "sherlock/scandal_in_bohemia",
        "mystery",
        "Sherlock Holmes; detective mystery, canonical genre example.",
    ),
    (
        "sherlock/red_headed_league",
        "mystery",
        "Sherlock Holmes; detective mystery.",
    ),
    (
        "sherlock/speckled_band",
        "mystery",
        "Sherlock Holmes; detective mystery.",
    ),
    (
        "london/love_of_life",
        "adventure",
        "Jack London; wilderness survival adventure.",
    ),
    (
        "london/story_of_keesh",
        "adventure",
        "Jack London; Arctic/hunting adventure.",
    ),
    (
        "london/brown_wolf",
        "adventure",
        "Jack London; wilderness setting, man-vs-nature adventure.",
    ),
    (
        "mass_quantities/the_sheriff_and_his_partner__harris",
        "western",
        "Opens in frontier Kansas, 1869; sheriff protagonist.",
    ),
    (
        "mass_quantities/the_cowboy_and_the_lady_and_her_pa_b_a_story_of_a__cobb",
        "western",
        "Wagon-train boss, cowboy protagonist, frontier setting.",
    ),
    (
        "ohenry-whirligigs/chaparral_christmas_gift",
        "western",
        "O. Henry 'Heart of the West' story; Texas ranch/prairie setting.",
    ),
    (
        "ohenry-four_million/gift_of_the_magi",
        "romance",
        "O. Henry; canonical romantic-sacrifice story.",
    ),
    (
        "ohenry-four_million/springtime_a_la_carte",
        "romance",
        "O. Henry; romantic-comedy premise (personal ad courtship).",
    ),
    (
        "ohenry-four_million/service_of_love",
        "romance",
        "O. Henry; title and premise center on a marriage/romance.",
    ),
)


def build_subset() -> list[tuple[str, str, str, int]]:
    """Copy each selected story into TRIAL_DIR; return manifest rows.

    Each returned row is (source_path, provisional_genre, rationale,
    body_length) -- body_length is read back from the copied file so
    the manifest reflects what was actually written, not an assumption.
    """
    if TRIAL_DIR.exists():
        shutil.rmtree(TRIAL_DIR)
    TRIAL_DIR.mkdir(parents=True)

    rows: list[tuple[str, str, str, int]] = []
    for rel_path, genre, rationale in SELECTIONS:
        collection, story_name = rel_path.split("/", 1)
        source = CORPORA_ROOT / collection / story_name / "story.json"
        if not source.is_file():
            raise FileNotFoundError(f"expected source story not found: {source}")

        data = json.loads(source.read_text(encoding="utf-8"))
        body = data.get("body", "")
        if not body:
            raise ValueError(f"source story has an empty body, refusing: {source}")

        dest_dir = TRIAL_DIR / story_name
        dest_dir.mkdir(parents=True)
        dest_path = dest_dir / "story.json"
        dest_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        rows.append((rel_path, genre, rationale, len(body)))
    return rows


def write_manifest(rows: list[tuple[str, str, str, int]]) -> None:
    lines = [
        "# Annotation feasibility trial: subset manifest",
        "",
        "24 stories (3 per genre x 8 `VALID_GENRES`), selected by hand from",
        "`corpora/` -- title/author/opening-text judgment only, no paid API",
        "call -- for `WI-ANNOTATE-0054`'s feasibility run. `provisional_genre`",
        "is this manual guess, to compare against `lcats annotate`'s actual",
        "`detected_genre` output in the stats report.",
        "",
        "| source (corpora/) | provisional_genre | rationale | body_chars |",
        "|---|---|---|---|",
    ]
    for rel_path, genre, rationale, body_len in rows:
        lines.append(f"| {rel_path} | {genre} | {rationale} | {body_len} |")
    lines.append("")
    MANIFEST_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_subset()
    write_manifest(rows)
    print(f"wrote {len(rows)} stories to {TRIAL_DIR}")
    print(f"wrote manifest to {MANIFEST_PATH}")
    print(f"run: lcats annotate --source {SOURCE_ROOT}")


if __name__ == "__main__":
    main()
