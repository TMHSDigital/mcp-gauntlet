# Security policy

## Reporting a problem

Report security problems privately:

**<https://github.com/TMHSDigital/mcp-gauntlet/security/advisories/new>**

Do not open a public issue for them. Include the version (`mcp-gauntlet --version`), what you did, and what happened. You should get a first reply within seven days.

## What counts

mcp-gauntlet is hostile to the agent on purpose. It must never be hostile to the person running it. These are security problems:

- The server reading or writing any file other than its own log, opening a network connection, or running a command.
- Anything an agent sent (argument values, prompts, conversation text) ending up in the log or in the report.
- A crafted event log, MCP message, or client causing harm to the machine or terminal of the person running `serve` or `report`.
- A payload that asks an agent for something that is not inert.

These are not security problems, and a normal issue is the right place for them:

- An agent following a payload. That is the tool working. If the verdict is wrong, file a bug.
- A scenario that an agent resists too easily or not at all.

## Supported versions

Fixes go into the latest release and the `main` branch.

## Using the tool responsibly

Attach mcp-gauntlet only to agents and clients you own or have written permission to test.
