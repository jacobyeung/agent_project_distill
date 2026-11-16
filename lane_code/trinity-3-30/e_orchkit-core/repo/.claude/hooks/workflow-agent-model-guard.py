#!/usr/bin/env python3
"""Deny a Workflow dispatch whose agent() calls lack per-call model: fields.

Workflow-internal agent() call-sites run inside the Workflow runtime, NOT as
top-level Agent tool calls, so they BYPASS the PreToolUse Agent hooks
(subagent-default-opus.py) and silently inherit the
*session* model. This guard blocks a Workflow script when it has agent()
call-sites but fewer explicit `model:` fields than call-sites, forcing the
author to pin a model on every call (or to route through an oagent() wrapper
that injects one).

Behavior:
  * Only fires for tool_name == "Workflow".
  * Inspects the inline `script` string; if absent, reads `scriptPath` from
    disk instead. If neither is present (e.g. a name-only invocation) the
    call passes through untouched.
  * Counts agent() call-sites with a word-boundary regex so subagent(...),
    xagent(...) and the identifier subagent_type do NOT false-count.
  * DENY (permissionDecision "deny", exit 0) iff agent-calls > 0 and
    model-count < agent-call count.

Fails OPEN: any parse/IO/other error passes the call through unblocked.
"""
import json
import re
import sys

# agent( call-sites not preceded by a [A-Za-z0-9_] char, so subagent( /
# myagent( / the identifier "subagent_type" never false-count as an agent call.
AGENT_CALL_RE = re.compile(r"(?<![A-Za-z0-9_])agent\(")
# Explicit model: fields (e.g. model: 'opus').
MODEL_FIELD_RE = re.compile(r"model\s*:")

DENY_MSG = (
    "Workflow script has {n} agent() calls but {m} model: fields — "
    "workflow-internal agents BYPASS hooks and inherit the session model. "
    "Add model: ('sonnet'|'opus'|'haiku'|'fable') to every agent() call, or "
    "define const oagent=(p,o={{}})=>agent(p,{{model:'opus',...o}}) and use it."
)


def main() -> None:
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Workflow":
        return

    tool_input = data.get("tool_input") or {}

    script = tool_input.get("script")
    if not isinstance(script, str):
        script_path = tool_input.get("scriptPath")
        if isinstance(script_path, str) and script_path:
            with open(script_path, "r", encoding="utf-8", errors="replace") as fh:
                script = fh.read()
        else:
            # Neither an inline script nor a readable scriptPath (e.g. a
            # name-only Workflow invocation) -- nothing to inspect.
            return

    agent_calls = len(AGENT_CALL_RE.findall(script))
    if agent_calls == 0:
        return

    model_fields = len(MODEL_FIELD_RE.findall(script))
    if model_fields >= agent_calls:
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": DENY_MSG.format(
                        n=agent_calls, m=model_fields
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
