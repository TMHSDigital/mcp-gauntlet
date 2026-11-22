# Changelog

Notable changes to mcp-gauntlet. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## Unreleased

### Fixed

- `report` no longer gives `RESISTED` when the only tool call after the payload was a failed canary call or a call to a tool that does not exist. A canary call with a different code is now `INCONCLUSIVE`, with the reason. ([#1](https://github.com/TMHSDigital/mcp-gauntlet/issues/1))
- A canary code that contains the run's token counts as `COMPROMISED` even with extra quotes, spaces, or different case. ([#1](https://github.com/TMHSDigital/mcp-gauntlet/issues/1))

### Changed

- `tool_call` events in the log now carry a `role`: `task`, `canary`, or `unknown`. Logs written by 0.1.0 are still read.

### Added

- Project site, contribution guide, security policy, code of conduct, and issue and pull request templates.
- CI runs `ruff` and `mypy`, tests on macOS and on Python 3.12 and 3.14, and builds and installs the wheel.
- The package ships a `py.typed` marker.

## 0.1.0 - 2026-11-21

First release.

- Six scenarios: `description-poisoning`, `hidden-unicode`, `result-injection`, `rug-pull`, `tool-shadowing`, `param-overshare`.
- An MCP server over stdio, tools only, with no dependencies.
- An append-only JSONL event log that records names and sizes and never argument values.
- `report` with three verdicts (`COMPROMISED`, `RESISTED`, `INCONCLUSIVE`), exit codes for CI, `--json`, and `--last`.
