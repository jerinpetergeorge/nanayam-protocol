## What and why

<!-- One or two sentences. Link the plan item, e.g. E03-T04. -->

Plan item(s):

## Checklist

- [ ] `uv run --with jsonschema python scripts/validate_fixtures.py` passes
- [ ] Fixture files live in the directory matching their `suite`
- [ ] This change to the contract is reflected in **both** `nanayam-django` and `nanayam-flutter` (link the PRs), or is additive and backward-compatible
- [ ] Existing tags are not moved; a new tag is planned for consumers to pin
- [ ] `spec/` updated if behaviour changed
- [ ] Clean-room: I did not read Cashew's source while writing these vectors
