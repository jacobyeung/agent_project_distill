#!/usr/bin/env python3
"""Default Agent-tool spawns to model='opus' when no model was specified, and append the
standard launch-and-monitoring cadence block (USER RULING 2026-09-16) to every launch or
monitoring lane prompt that does not already carry it.

USER RULING (2026-07-10): spawned Claude subagent lanes must DEFAULT to opus;
fable (or any other explicit model) must require an explicit request. This
hook only fills in an ABSENT/EMPTY model field; any explicit value (fable,
opus, sonnet, haiku, or a full model id) passes through unchanged so it is
never swallowed. The opus/sonnet aliases resolve through
ANTHROPIC_DEFAULT_OPUS_MODEL / ANTHROPIC_DEFAULT_SONNET_MODEL in
~/.claude/settings.json.
"""
import json
import sys

DEFAULT_MODEL = "opus"
# Tool names that spawn subagents. "Agent" is the tool actually present in
# this harness; "Task" is included in case a future/alternate matcher scheme
# uses that name for the same capability (see registration-order note in
# the corresponding CLAUDE.md/AGENTS.md-driven task -- kept defensive, costs
# nothing since it only fires on tool_name match).
SPAWN_TOOLS = frozenset({"Agent", "Task"})


CADENCE_MARKER = "## Launch and monitoring cadence"
CADENCE_BLOCK = """

## Launch and monitoring cadence (USER RULING 2026-09-16; default for every launch or monitoring lane)
Purpose (user's words): catch failures quickly when they are most likely to happen. Failure likelihood is highest right after a launch, restart, resume, ramp step, version takeover, membership extension, or alarm, and falls once traces are landing repeatedly. Check frequency tracks that likelihood: dense at those moments, sparse once the run has proven itself.
- After any launch, restart, resume, ramp step, takeover, extension, or alarm: check every 1 minute, and check BOTH process liveness (supervisor and worker pids, service health) AND outputs landing (finalized trace files with non-null predictions on /data2). Either signal alone can mislead.
- Two consecutive one-minute checks with no new trace: debug immediately (worker logs, service health, provider errors). Never wait it out.
- Once traces are landing repeatedly, lengthen the interval step by step (about 2, then 5, then 10 minutes) and hold at 10 minutes; publish a coord status note at every check (completed/total per cell, workers, carrier, null predictions).
- If any signal regresses (a worker or supervisor dies, no new trace within one expected episode time, error rate rising), drop back to 1-minute checks until traces land again.
- A detached watchdog on the 10-minute cadence may take over only after traces are landing; report its pid and log path.
- Anything that fails two checks on the same defect goes to codex `-m gpt-6-astra -c model_reasoning_effort=high` immediately, with both failure records attached.
"""
LAUNCH_WORDS = ("launch", "babysit", "monitor", "drain", "top-up", "topup", "relaunch", "resume")
READ_ONLY_TYPES = frozenset({"Explore", "Plan"})


def _needs_cadence(tool_input: dict) -> bool:
    if tool_input.get("subagent_type") in READ_ONLY_TYPES:
        return False
    prompt = str(tool_input.get("prompt") or "")
    if CADENCE_MARKER in prompt:
        return False
    low = prompt.lower()
    return any(w in low for w in LAUNCH_WORDS)


def main() -> None:
    data = json.load(sys.stdin)
    if data.get("tool_name") not in SPAWN_TOOLS:
        return

    tool_input = data.get("tool_input") or {}
    updated = dict(tool_input)
    changed = False
    if not tool_input.get("model"):
        updated["model"] = DEFAULT_MODEL
        changed = True
    if _needs_cadence(tool_input):
        updated["prompt"] = str(tool_input.get("prompt") or "") + CADENCE_BLOCK
        changed = True
    if not changed:
        return
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "permissionDecision": "allow",
                    "updatedInput": updated,
                }
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
