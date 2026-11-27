# Contributing

Fixes and improvements are welcome, especially when an example stops working with a newer Opik or framework
release, or when a README no longer matches what Opik shows.

## Before you open a pull request

1. Keep a pull request to one example (or to the root files).
2. Run that example's offline tests. They need no keys and no Opik server: `uv run pytest`, `npm test`, or
   the command in the example's README. CI runs the same commands for every example.
3. Use fictional data only. No real people, companies, addresses, API keys, tokens or customer content.
4. If the change alters what Opik shows, update the example's README to match.

## How changes land

Every change goes through a pull request. It needs a passing `ci` check and the maintainer's approval, and it is
squash-merged, so the pull request title and description become the commit message. Write them for someone
reading the history later. Commits on `main` must be signed; squash merges made on GitHub are signed for you.

CI runs pull requests from forks only after the maintainer approves the run. It has read-only access to the
repository and no secrets, so no example can depend on a real API key in CI.

## Reporting problems

Use the issue templates for broken examples or ideas. Report security issues privately, as described in
[SECURITY.md](SECURITY.md).
