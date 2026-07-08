# Notes: release-quality

## Open Questions

- Should release checks include a direct `noc doctor .` gate now that the repo dogfoods NOC?

## Technical Debt

- Tests use subprocess calls heavily, which is faithful but slower than unit-level parser tests.

## Future Ideas

- Add CI coverage for `python scripts/noc.py work . --path scripts/noc.py --json`.

