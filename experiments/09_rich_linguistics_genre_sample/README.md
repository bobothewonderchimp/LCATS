# Rich Linguistics Genre Sample Pilot

This experiment runs the rich linguistic sidecar pipeline over the fixed
146-story genre-balanced sample selected by
`experiments/05_metadata_genre_prefilter`.

The experiment mirrors source story buckets under `results/copied_buckets/`
before analysis. Generated `linguistics.json`, `linguistics.tokens.json`, and
`linguistics.lexicon.json` files stay inside that mirror and are not written to
`corpora/`.

`parquet_bridge.py` exports those canonical JSON artifacts into a compact
experiment-scoped Parquet package for reusable token statistics, and restores
the canonical JSON files when existing validators or downstream tools need
them.

## Audit Protocol

The pilot preregisters a human POS audit before scoring:

- backend: spaCy by default, with exact model/library provenance from each
  sidecar;
- labels: `NOUN`, `PROPN`, and `OTHER`;
- combined noun family: `NOUN` or `PROPN`;
- pass gate: combined noun-family precision >= 0.90 and recall >= 0.90;
- severe genre-slice failure: any genre with at least 10 audited rows has
  combined noun-family precision or recall below 0.80;
- Stanza comparison: warranted when the spaCy audit misses or is inconclusive
  against the registered gate, otherwise not required for the pilot;
- downstream noun figures: proceed only after scored human labels pass the
  quality gate.

Run without labels to generate the sample packet:

```bash
python experiments/09_rich_linguistics_genre_sample/run_rich_linguistics_sample.py --overwrite
```

Fill `results/pos_audit_sample.csv` with `gold_upos` values of `NOUN`,
`PROPN`, or `OTHER`, then score it:

```bash
python experiments/09_rich_linguistics_genre_sample/run_rich_linguistics_sample.py --resume --audit-labels experiments/09_rich_linguistics_genre_sample/results/pos_audit_sample.csv
```

Export the generated v2 token detail to Parquet:

```bash
python experiments/09_rich_linguistics_genre_sample/parquet_bridge.py export experiments/09_rich_linguistics_genre_sample/results/copied_buckets experiments/09_rich_linguistics_genre_sample/results/parquet
```

Restore canonical JSON from the Parquet package:

```bash
python experiments/09_rich_linguistics_genre_sample/parquet_bridge.py restore experiments/09_rich_linguistics_genre_sample/results/parquet /tmp/lcats_wi0007_restore
```
