"""A minimal MCP server over stdio: newline-delimited JSON-RPC 2.0, tools only."""

from __future__ import annotations

import json
import sys
from typing import Any, BinaryIO

from . import __version__
from .eventlog import EventLog
from .scenarios import CANARY_TOOL, Scenario, UnknownTool

KNOWN_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
FALLBACK_PROTOCOL_VERSION = "2025-06-18"


class _Context:
    def __init__(self, log: EventLog) -> None:
        self._log = log
        self.pending: list[str] = []

    def log(self, kind: str, **fields: Any) -> None:
        self._log.write(kind, **fields)

    def notify(self, method: str) -> None:
        self.pending.append(method)


class Server:
    def __init__(self, scenario: Scenario, log: EventLog) -> None:
        self.scenario = scenario
        self.log = log
        self.ctx = _Context(log)

    # -- wire ----------------------------------------------------------------

    def _send(self, out: BinaryIO, message: dict[str, Any]) -> None:
        out.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))
        out.flush()

    def _result(self, out: BinaryIO, mid: Any, result: dict[str, Any]) -> None:
        self._send(out, {"jsonrpc": "2.0", "id": mid, "result": result})

    def _error(self, out: BinaryIO, mid: Any, code: int, message: str) -> None:
        self._send(out, {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}})

    def _flush_notifications(self, out: BinaryIO) -> None:
        for method in self.ctx.pending:
            self._send(out, {"jsonrpc": "2.0", "method": method})
            self.log.write("notification_sent", method=method)
        self.ctx.pending.clear()

    # -- loop ----------------------------------------------------------------

    def run(self, stdin: BinaryIO | None = None, stdout: BinaryIO | None = None) -> None:
        stdin = stdin or sys.stdin.buffer
        stdout = stdout or sys.stdout.buffer
        for raw in stdin:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self._error(stdout, None, -32700, "Parse error")
                continue
            if not isinstance(message, dict):
                self._error(stdout, None, -32600, "Invalid request")
                continue
            method = message.get("method")
            if not isinstance(method, str):
                continue  # a response to something we sent; nothing to do
            if "id" in message:
                self._handle_request(stdout, message["id"], method, message.get("params") or {})
            else:
                self.log.write("notification_received", method=method)
            self._flush_notifications(stdout)
        self.log.write("run_end")

    def _handle_request(self, out: BinaryIO, mid: Any, method: str, params: Any) -> None:
        if not isinstance(params, dict):
            params = {}

        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in KNOWN_PROTOCOL_VERSIONS else FALLBACK_PROTOCOL_VERSION
            client = params.get("clientInfo") if isinstance(params.get("clientInfo"), dict) else {}
            self.log.write(
                "initialize",
                client_name=str(client.get("name", ""))[:80],
                client_version=str(client.get("version", ""))[:40],
                protocol=version,
            )
            self._result(
                out,
                mid,
                {
                    "protocolVersion": version,
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "gauntlet", "version": __version__},
                },
            )
        elif method == "ping":
            self._result(out, mid, {})
        elif method == "tools/list":
            self.log.write("tools_listed")
            self._result(out, mid, {"tools": self.scenario.tools()})
            self.scenario.on_listed(self.ctx)
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments")
            if not isinstance(args, dict):
                args = {}
            # Only a call to one of the scenario's own task tools shows the agent
            # kept working; the canary and tools that do not exist do not.
            if name == CANARY_TOOL:
                role = "canary"
            elif any(tool["name"] == name for tool in self.scenario.tools()):
                role = "task"
            else:
                role = "unknown"
            # Argument names only. Values are never written to the log.
            self.log.write(
                "tool_call", tool=str(name)[:80], role=role, arg_keys=sorted(map(str, args))[:20]
            )
            try:
                text = self.scenario.call(str(name), args, self.ctx)
            except UnknownTool:
                self._error(out, mid, -32602, f"Unknown tool: {name}")
                return
            except Exception as exc:
                # Exception messages and tracebacks can contain argument values.
                self.log.write("handler_error", error_type=type(exc).__name__)
                self._error(out, mid, -32603, "Internal error")
                return
            self._result(out, mid, {"content": [{"type": "text", "text": text}], "isError": False})
        else:
            self._error(out, mid, -32601, f"Method not found: {method}")
