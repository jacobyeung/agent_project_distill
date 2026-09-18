#!/usr/bin/env python3
"""rm_guard — pre-exec guard that blocks file-deletion commands for agent sessions.

USER RULING 2026-09-11: agents never run deletion commands directly. When a
command that deletes files is attempted, this guard (a) refuses it and
(b) appends the exact command to agent/PENDING_USER_COMMANDS.md so the user
can review and run it personally.

Hook modes (read the tool-call JSON on stdin):
    --hook claude   Claude Code PreToolUse (Bash)        -> exit 2 blocks
    --hook cursor   Cursor beforeShellExecution          -> exit 2 blocks (or JSON deny)
    --hook codex    Codex hooks.json PreToolUse          -> JSON deny + exit 2
    --hook devin    Devin CLI .devin/hooks.v1.json (exec) -> non-zero blocks

Direct mode:
    --command "<shell command>"   -> exit 1 and message if blocked, else exit 0

The guard FAILS OPEN on any internal error: a broken guard must never stall
experiment lanes. It is accident-prevention, not an adversarial boundary.

Python 3.6 compatible (hooks on this host may invoke python3 == 3.6).
"""

import json
import os
import re
import sys
from datetime import datetime

PENDING_FILE = os.environ.get(
    "PENDING_COMMANDS_FILE",
    "/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md",
)

# A deletion utility in command position: start of string, after a shell
# separator/quote/subshell, or right after a common launcher keyword.
_SEP = (
    r"(?:^|[\s;|`'\"$(){}&<>]|"
    r"\b(?:then|do|else|sudo|xargs|timeout|nice|ionice|taskset|chrt|"
    r"nohup|setsid|env|command|builtin|exec|stdbuf|watch|time|ssh|srun)\b)\s*"
)
_DANGER = r"(?:rm|rmdir|unlink|shred|truncate|wipefs|mkfs(?:\.\w+)?)"
# The token must take at least one argument (\s+\S): a bare 'rm' deletes
# nothing, and requiring an argument skips quoted patterns like grep 'rm'.
RX_TOKEN = re.compile(_SEP + r"\\?" + _DANGER + r"(?=\s+\S)")
# Absolute or dot-relative invocation: /bin/rm, /usr/bin/rm, ./tools/rm.
# A relative trailing component (mkdir -p foo/rm) and a bare trailing name
# with no arguments (mkdir -p /tmp/foo/rm) are both safe.
RX_PATH = re.compile(
    r"(?:^|[\s;|`'\"$()&])\.{0,2}/(?:[\w.-]+/)*" + _DANGER + r"(?=\s+\S)")

RX_FIND = re.compile(
    r"\bfind\b[^;&|`]*?(?:-delete\b|-exec(?:dir)?\s+\\?"
    r"(?:rm|rmdir|unlink|shred)\b)"
)
RX_GITCLEAN = re.compile(r"\bgit\s+(?:-C\s+\S+\s+|--git-dir[=\s]\S+\s+)*clean\b")
RX_GITWT = re.compile(
    r"\bgit\s+(?:-C\s+\S+\s+)*worktree\s+(?:remove|prune)\b"
)
_PYDEL = re.compile(
    r"(?:os\.(?:remove|unlink|rmdir|removedirs)\s*\(|shutil\.rmtree\s*\(|"
    r"\.(?:unlink|rmdir)\s*\(|os\.system\s*\(\s*['\"][^'\"]*\brm\b)")
RX_PY = re.compile(r"\bpython\w*\b")
RX_SCRIPT = re.compile(r"\b(?:perl|ruby|node|php)\b")
_RX_SCRIPT_DEL = re.compile(
    r"(?:\bunlink\b|\brmtree\b|\brm_rf\b|\brmSync\b|\bremove\s*\()")
# apply_patch-style deletion hunks (no shell command involved).
RX_PATCH_DEL = re.compile(r"\*\*\*\s*Delete File")


def extract_commands(payload):
    """Pull candidate shell-command strings out of any known hook payload."""
    cmds = []
    for source in (payload.get("tool_input") or {}, payload):
        if not isinstance(source, dict):
            continue
        for key in ("command", "cmd", "commands", "argv", "input",
                    "text_input", "bytes_input", "shell_command"):
            v = source.get(key)
            if isinstance(v, str):
                cmds.append(v)
            elif isinstance(v, list):
                cmds.append(" ".join(str(x) for x in v))
    return cmds


def find_hit(command):
    for rx in (RX_TOKEN, RX_PATH, RX_FIND, RX_GITCLEAN, RX_GITWT,
               RX_PATCH_DEL):
        m = rx.search(command)
        if m:
            return m.group(0).strip()
    if RX_PY.search(command):
        m = _PYDEL.search(command)
        if m:
            return m.group(0).strip()
    if RX_SCRIPT.search(command):
        m = _RX_SCRIPT_DEL.search(command)
        if m:
            return m.group(0).strip()
    return None


def queue_request(command, payload, source):
    """Append the blocked command to the pending file (dedup exact PENDING rows)."""
    one_line = " ".join(command.split()).replace("`", "'")
    agent = os.environ.get("AGENT_ID") or source
    sess = str(payload.get("session_id") or payload.get("conversation_id") or "")[:8]
    cwd = payload.get("cwd") or os.getcwd()
    row = "- [ ] `{}` — src={}:{} cwd={} queued={}\n".format(
        one_line, agent, sess, cwd, datetime.utcnow().isoformat() + "Z")
    try:
        try:
            with open(PENDING_FILE) as f:
                if ("`%s`" % one_line) in f.read():
                    return  # already queued
        except IOError:
            pass
        import fcntl
        with open(PENDING_FILE, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(row)
            fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        pass  # fail open; the block message still tells the agent the file path


def block(source, command, payload, hit):
    queue_request(command, payload, source)
    msg = (
        "BLOCKED by rm_guard (user rule 2026-09-11): this command deletes "
        "files (matched: %r). Agent sessions never run deletion commands. "
        "The exact command was queued in %s — do NOT retry it or a variant; "
        "the user reviews and runs queued deletions. Continue other work, or "
        "report the needed deletion in your response." % (hit, PENDING_FILE)
    )
    if source == "cursor":
        print(json.dumps({
            "permission": "deny",
            "user_message": msg,
            "agent_message": msg,
        }))
    else:
        # Claude Code, Codex, and Devin all honor exit 2 / non-zero + stderr.
        # Also emit the Claude-compatible JSON so JSON-reading hosts see a
        # structured deny.
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": msg,
            }
        }))
        sys.stderr.write(msg + "\n")
    return 2


def allow(source):
    if source == "cursor":
        print(json.dumps({"permission": "allow"}))
    return 0


# A tool whose name says delete/remove is a deletion attempt no matter what
# its arguments look like (covers non-shell delete tools in Cursor/Devin/etc).
RX_TOOL_NAME = re.compile(r"(?i)delet|remov|trash|unlink|shred")


def main():
    source = "direct"
    command = None
    payload = {}
    args = sys.argv[1:]
    if "--command" in args:
        i = args.index("--command")
        command = args[i + 1] if i + 1 < len(args) else ""
    else:
        if "--hook" in args:
            source = args[args.index("--hook") + 1]
        try:
            payload = json.load(sys.stdin)
        except Exception:
            payload = {}

    tool_name = str(payload.get("tool_name") or "")
    if RX_TOOL_NAME.search(tool_name):
        return block(source, "<tool:%s>" % tool_name, payload, tool_name)

    commands = [command] if command is not None else extract_commands(payload)
    for cmd in commands:
        if not cmd:
            continue
        hit = find_hit(cmd)
        if hit:
            return block(source, cmd, payload, hit)
    return allow(source)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # fail open
