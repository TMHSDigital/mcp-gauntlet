# Contributing to mcp-gauntlet

Thanks for helping. Bug reports, new scenarios, and documentation fixes are all welcome.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md). Security problems go through a private report, described in [SECURITY.md](SECURITY.md), and not through a public issue.

## The one rule

mcp-gauntlet is a hostile server that people attach to their own agents on their own machines. It stays safe to run because of one rule, and every change is reviewed against it:

> A payload may only ask for something inert and observable.

In practice:

- The server opens no file other than its own log, makes no network connection, and runs nothing.
- The log records names and sizes. It never records what an agent sent: no argument values, no prompt text, no conversation.
- A "compromise" is a harmless act the server can see, such as a call to the canary tool with the run's token.

A change that needs to break this rule will not be merged, however useful the scenario.

## Set up

You need Python 3.10 or newer and git. The project has no runtime dependencies.

```shell
git clone https://github.com/TMHSDigital/mcp-gauntlet
cd mcp-gauntlet
python -m pip install -e ".[dev]"
```

The `dev` extra installs `ruff` and `mypy`. The tests need nothing beyond the standard library, so you can skip the install and still run them.

## Check your change

Run the same three commands CI runs:

```shell
python -m unittest discover -s tests -v
ruff check .
mypy
```

To run one test:

```shell
python -m unittest tests.test_gauntlet.GauntletTests.test_rug_pull -v
```

CI runs the tests on Linux, Windows, and macOS with Python 3.10, 3.12, and 3.14.

## How the code is laid out

| File | What it does |
|---|---|
| `src/mcp_gauntlet/scenarios.py` | The attack scenarios. Each one lists its tools and decides what counts as a trigger. |
| `src/mcp_gauntlet/server.py` | The MCP server: newline-delimited JSON-RPC over stdio, tools only. |
| `src/mcp_gauntlet/eventlog.py` | The append-only JSONL log. |
| `src/mcp_gauntlet/report.py` | Turns a log into verdicts. `judge` is the function that matters most. |
| `src/mcp_gauntlet/cli.py` | The `list`, `serve`, and `report` commands. |
| `tests/test_gauntlet.py` | End-to-end tests that drive the real server over stdio. |
| `docs/` | The project site, published with GitHub Pages. Plain HTML, no build step. |

## Add a scenario

1. Open a [scenario proposal](https://github.com/TMHSDigital/mcp-gauntlet/issues/new?template=scenario_proposal.yml) first if the idea is new. It saves you work if the inert act or the verdict rule needs discussion.
2. Subclass `Scenario` in `scenarios.py`. Set `name`, `summary`, and `operator_prompt`, and implement `tools()` and `handle()`.
3. Log `payload_delivered` at the moment the hostile text reaches the client, and `triggered` when the agent does the act.
4. Decide what an untested run looks like. Set `undelivered_hint`, and set `resistance_observable = False` if the server cannot tell a pass from doing nothing.
5. Register the class in `SCENARIOS`.
6. Add tests with two scripted agents: one that obeys the payload and must be `COMPROMISED`, and one that only does the task and must not be.
7. Add the scenario to the table in `README.md` and to the list in `docs/index.html`.

## Verdict changes

A wrong verdict is the worst bug this project can have, and a false `RESISTED` is worse than a false `COMPROMISED`. If you change `judge`:

- Add a test for the exact event sequence you are changing.
- When the log cannot support a claim, return `INCONCLUSIVE` and say why.
- Keep old logs readable. `report` must still judge a log written by an earlier version.

## Pull requests

- Branch from `main` and keep each pull request to one change.
- Write the commit message as a sentence that says what changed and why.
- Add a line to `CHANGELOG.md` under "Unreleased" when users will notice the change.
- Match the code around you: type hints on everything, standard library only, and comments that explain why and not what.

## Reporting bugs

Use the [bug report form](https://github.com/TMHSDigital/mcp-gauntlet/issues/new?template=bug_report.yml). The lines for the affected run from your event log are the most useful thing to attach, and they are safe to share because the log holds no argument values.
