# nanayam-protocol

The shared contract between the Nanayam client (`nanayam-flutter`) and server (`nanayam-django`).

This repository contains **no product code**. It holds language-agnostic files that both implementations are tested against, so they cannot silently drift apart:

| Path | Contents |
|---|---|
| `spec/` | Written specification: sync rules, the schema contract, conflict rules |
| `fixtures/` | Test vectors as JSON: "given this input, the correct output is exactly this" |
| `openapi/` | A copy of the server's OpenAPI document (the source of truth lives in `nanayam-django`) |
| `schema/` | JSON Schema that every fixture file must satisfy |
| `scripts/` | `validate_fixtures.py` checks every fixture against the schema; `generate_vectors.py` authors the money and uuid vectors |

## Fixtures

Each fixture file describes one suite and lives in the directory named after it:

```json
{
  "suite": "money",
  "version": 1,
  "description": "What this file checks",
  "cases": [
    { "name": "add same currency", "input": { }, "expected": { } }
  ]
}
```

Both implementations load every file, run each case, and compare the result to `expected`. A change to a fixture is a change to the contract and needs both sides updated.

Suites so far:

| Suite | Files | Covers |
|---|---|---|
| `money` | `arithmetic.json`, `conversion.json` | Construction, add, subtract, negate, abs, compare, FX conversion with integer parts-per-million rates |
| `uuid` | `build.json`, `parse.json`, `sort.json` | UUIDv7 layout, parsing and ordering |

The behaviour these vectors pin down is written in [`spec/money-and-ids.md`](spec/money-and-ids.md). Every 64-bit integer in a fixture is a decimal **string**, because JSON numbers lose precision above 2^53 in some languages.

The money and uuid files are **generated** by `scripts/generate_vectors.py`, a small reference implementation using exact arbitrary-precision integers that shares no code with any client. Edit the generator, not the JSON, then regenerate; CI fails if the committed files differ from the generator's output.

```sh
uv run python scripts/generate_vectors.py                        # regenerate
uv run --with jsonschema python scripts/validate_fixtures.py     # validate against the schema
```

## Versioning

Consumers pin a **git tag** (`v0.1.0`, ...). Fixtures are only changed in a new tag; a tag is never moved.

## Licence

[CC BY 4.0](LICENSE). The protocol is published so that its claims can be reviewed independently.
