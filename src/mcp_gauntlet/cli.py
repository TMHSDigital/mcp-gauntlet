from __future__ import annotations

import argparse
import secrets
import sys

from . import __version__
from .eventlog import EventLog
from .report import load_verdicts, render_json, render_text, worst_exit_code
from .scenarios import SCENARIOS
from .server import Server

DEFAULT_LOG = "gauntlet-events.jsonl"


def _cmd_list(_: argparse.Namespace) -> int:
    for name, cls in SCENARIOS.items():
        print(f"{name}\n    {cls.summary}\n    Try: {cls.operator_prompt}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    run_id = secrets.token_hex(4)
    token = "GX-" + secrets.token_hex(4)
    scenario = SCENARIOS[args.scenario](token, after=args.after)
    log = EventLog(args.log, run_id)
    log.write(
        "run_start",
        scenario=scenario.name,
        version=__version__,
        resistance_observable=scenario.resistance_observable,
        resisted_requires_later_call=scenario.resisted_requires_later_call,
        undelivered_hint=scenario.undelivered_hint,
    )
    # stdout is the protocol channel, so anything for the operator goes to stderr.
    print(f"mcp-gauntlet {__version__}: {scenario.name}, run {run_id}, log {log.path}", file=sys.stderr)
    try:
        Server(scenario, log).run()
    except KeyboardInterrupt:
        pass
    finally:
        log.close()
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    try:
        verdicts = load_verdicts(args.log)
    except FileNotFoundError:
        print(f"No log at {args.log}", file=sys.stderr)
        return 2
    if args.last:
        verdicts = verdicts[-1:]
    print(render_json(verdicts) if args.json else render_text(verdicts))
    return worst_exit_code(verdicts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcp-gauntlet",
        description="A deliberately hostile MCP server for testing agents you own or are authorized to test.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="show the available scenarios")
    p_list.set_defaults(func=_cmd_list)

    p_serve = sub.add_parser("serve", help="run one scenario as an MCP server on stdio")
    p_serve.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    p_serve.add_argument("--log", default=DEFAULT_LOG, help=f"event log path (default: {DEFAULT_LOG})")
    p_serve.add_argument(
        "--after", type=int, default=1, help="rug-pull: change the definition after this many calls"
    )
    p_serve.set_defaults(func=_cmd_serve)

    p_report = sub.add_parser("report", help="read an event log and print verdicts")
    p_report.add_argument("log", nargs="?", default=DEFAULT_LOG)
    p_report.add_argument("--json", action="store_true", help="machine-readable output")
    p_report.add_argument("--last", action="store_true", help="only the most recent run")
    p_report.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)
