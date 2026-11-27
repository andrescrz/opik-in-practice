# Security policy

## Reporting a vulnerability

Please report security issues privately through
[GitHub's private vulnerability reporting](https://github.com/andrescrz/opik-in-practice/security/advisories/new),
not in a public issue or pull request. Include the affected example, how to reproduce the problem and its impact.

This is a maintained side project, so responses are best effort. Reports are acknowledged and fixed in a
new commit on `main`; there are no releases to patch.

## Scope

In scope: the code, scripts, Docker setups and CI in this repository.

Out of scope, please report upstream:

- Opik itself: [comet-ml/opik](https://github.com/comet-ml/opik/security)
- Third-party frameworks and the vendored Dify files in `dify-gym-assistant/dify-docker/`

## Running the examples safely

- API keys belong in a git-ignored `.env`; never commit one.
- The n8n and Dify examples use published demo logins and bind to `127.0.0.1` only. Keep it that way.
- `smolagents-solar-energy-analyst` runs model-written Python on your machine, restricted to `pandas`.
