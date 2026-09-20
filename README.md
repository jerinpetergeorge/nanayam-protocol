# nanayam-protocol

The shared contract between the Nanayam client (`nanayam-flutter`) and server (`nanayam-django`).

This repository contains **no product code**. It holds language-agnostic files that both implementations are tested against, so they cannot silently drift apart:

| Path | Contents |
|---|---|
| `spec/` | Written specification: sync rules, the schema contract, conflict rules |
| `fixtures/` | Test vectors as JSON: "given this input, the correct output is exactly this" |
| `openapi/` | A copy of the server's OpenAPI document (the source of truth lives in `nanayam-django`) |
| `schema/` | JSON Schema that every fixture file must satisfy |
| `scripts/` | Tooling, currently the fixture validator |

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

Validate locally:

```sh
uv run --with jsonschema python scripts/validate_fixtures.py
```

## Versioning

Consumers pin a **git tag** (`v0.1.0`, ...). Fixtures are only changed in a new tag; a tag is never moved.

## Licence

[CC BY 4.0](LICENSE). The protocol is published so that its claims can be reviewed independently.
