"""Validate every fixture file against schema/fixture.schema.json.

Usage: uv run --with jsonschema python scripts/validate_fixtures.py
Exits non-zero if any file is invalid, or if there are no fixtures at all.
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "fixture.schema.json"
FIXTURES_DIR = ROOT / "fixtures"


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    files = sorted(FIXTURES_DIR.rglob("*.json"))
    if not files:
        print("error: no fixture files found under fixtures/", file=sys.stderr)
        return 1

    failures = 0
    for path in files:
        rel = path.relative_to(ROOT)
        try:
            document = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"FAIL {rel}: invalid JSON: {exc}", file=sys.stderr)
            failures += 1
            continue

        errors = sorted(validator.iter_errors(document), key=lambda e: list(e.path))
        for error in errors:
            location = "/".join(str(part) for part in error.path) or "<root>"
            print(f"FAIL {rel}: {location}: {error.message}", file=sys.stderr)
        if errors:
            failures += 1
            continue

        if document["suite"] != path.parent.name:
            print(
                f"FAIL {rel}: suite '{document['suite']}' must equal directory name '{path.parent.name}'",
                file=sys.stderr,
            )
            failures += 1
            continue

        print(f"ok   {rel} ({len(document['cases'])} cases)")

    if failures:
        print(f"{failures} of {len(files)} fixture file(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
