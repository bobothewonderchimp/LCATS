# verify_assess_api

Dogfood check for `assess_story()` (`lcats.analysis.corpus.assess`) against
a real Anthropic API call.

## Background

Real (non-`FakeBackend`) calls to `assess_story()` were failing outright
with:

```
Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error',
'message': "tools.0.custom: For 'number' type, properties maximum, minimum
are not supported"}}
```

`ASSESSMENT_TOOL`'s `detected_genre_confidence` property declared
`minimum`/`maximum` constraints, which Anthropic's strict tool-schema mode
rejects on `number`-type properties. Unit tests use `FakeBackend`, which
doesn't validate against Anthropic's real schema constraints, so this went
unnoticed. Fixed by dropping the `minimum`/`maximum` keys (the description
already documents the 0.0-1.0 range for the model).

## Run

```bash
python verify_assess_api.py
```

Makes **one real, billable** Anthropic API call (`assess_story()` against
`corpora/lovecraft/the_case_of_charles_dexter_ward/story.json` in detect-only
mode, `max_tokens=16384`). Requires `ANTHROPIC_API_KEY` (env var or
`.secrets/anthropic_api_keys.env` - see `docs/secrets-setup.md`).

Optionally pass a different story and/or claimed genre:

```bash
python verify_assess_api.py ../../corpora/sherlock/five_orange_pips/story.json --genre mystery
```

Exits non-zero and prints `FAIL` if the call errors (including a
recurrence of the schema 400); prints `OK` on success.
