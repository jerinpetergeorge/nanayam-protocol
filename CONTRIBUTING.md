# Contributing

This repository is the contract between the Nanayam client and server. A careless change here breaks both, so changes are small and deliberate.

## Rules

1. **Fixtures are contract.** A change to an existing fixture changes the behaviour both implementations must have. Update both sides in the same change window and link the pull requests.
2. **Prefer additive changes.** New cases and new suites are safe; changing or removing an existing case is a breaking change.
3. **Tags are immutable.** Consumers pin a tag (`v0.1.0`). Never move or delete one; cut a new one.
4. **Edit the generator, not the generated JSON.** The money and uuid vectors come from `scripts/generate_vectors.py`; regenerate and commit both. CI fails on any difference.
5. **Validate before pushing:**
   ```sh
   uv run python scripts/generate_vectors.py
   uv run --with jsonschema python scripts/validate_fixtures.py
   ```
6. **One suite per directory.** A file's `suite` must equal its directory name.

## Clean-room

Do not read Cashew's source code while writing vectors or specs for behaviour Nanayam implements. Nanayam is a clean-room build; feature ideas are free, source code is not.

## Licence

Contributions are accepted under [CC BY 4.0](LICENSE).
