---
name: codex
description: >-
  Dispatch a task to the Codex CLI as an independent subagent that shares no context with you.
  Use GPT-5.6 SOL for hard tasks (adversarial review, complex implementation, deep analysis)
  and GPT-5.6 Terra for easier mechanical work. NOT for benchmark planning or ideation
  (that stays on Fable/Opus). Supports read-only review and write-mode execution.
version: 1.1.0
scope: project
---

# /codex — Codex as a working subagent

**Default executor: prefer codex over Claude Code subagents** for
any new self-contained dispatch; Claude lanes are the exception (live multi-step cluster ops,
SendMessage coordination, repo skills). Long WATCH phases belong to neither — arm a detached
shell watchdog from a real shell and let orchestrator ticks + codex checks cover the wait.

The `codex` CLI (`/home/jjyeung/.local/bin/codex`) runs as a subagent that **shares no
context with you.** Two legitimate uses here:

1. **Independent review / second opinion.** Because it shares none of your context, it's a real
   cross-model reviewer — adversarial code review before an expensive commit, design
   pre-mortems, attacking a verdict or a statistics claim.
2. **Offload mechanical implementation.** When you'd otherwise spawn a Sonnet/Haiku subagent for
   self-contained work and your Codex budget is larger, dispatch Codex. It writes the code and
   runs the tests; **you review the diff and verify before keeping it.**

**Role limit (project rule).** Codex is a reviewer/analyst and a mechanical worker — **not the
benchmark planner or idea generator.** Campaign ideation, experiment design, and analysis
synthesis stay on Fable/Opus. Don't ask Codex to decide the next round or invent levers.

## Model selection

| Tier | Model | When |
|---|---|---|
| **Hardest** | `gpt-6-astra` | Planning, scientific reasoning, architecture, gate review (`-c model_reasoning_effort=high`) |
| **Hard** | `gpt-5.6-sol` | Adversarial review, multi-file implementation, deep one-shot analysis/synthesis, gated harness-round builds, anything needing strong reasoning |
| **Easy** | `gpt-5.6-terra` | Mechanical execution, single-file edits, log greps, inventories, permission-blocked bash fallback, recipe-following builds with tight acceptance criteria |

Default to **Terra** when the task is clearly mechanical; escalate to **SOL** when judgment,
architecture, or cross-file reasoning matters. For SOL review lanes, add
`-c model_reasoning_effort=high` unless the user asks for more.

## Modes (pick the least privilege that works)

| Goal | Sandbox flag | Notes |
|---|---|---|
| Review / second opinion only | `-s read-only` | Safe default for any "just look" task. |
| Implement: edit repo + run tests | `-s workspace-write -C <repo>` | Writes confined to the repo. `--add-dir <dir>` to also write another. |
| Implement: needs network / outside-repo writes | `-s danger-full-access` | Most powerful; isolate in a git worktree so it can't disturb the live tree. |

For launch/ops dispatches that curl localhost or external endpoints, add
`-c sandbox_workspace_write.network_access=true`. Detached processes (`setsid nohup`) die when
sandboxed `codex exec` returns — plan long-running launches accordingly.

## Review recipe (Astra)

```bash
codex exec -m gpt-6-astra -c model_reasoning_effort=high -s read-only \
  -C /home/jjyeung/agent_project \
  -o /tmp/codex_<task>.md - < /tmp/codex_<task>_prompt.md
```
Prompt it to attack/refute, default to skeptical, cite `file:line`, and end with a BLOCKER/OK
or PASS/FAIL verdict. Treat its findings as claims to verify, not ground truth.

**Reviewer-prompt rules:** never include "do not execute"-style headers
or lane-scoping preambles in the prompt — reviewers obey them literally and refuse the review.
Include the packet's `SCOPE_RULING_VERBATIM.md` text when a scope ruling governs findings
classification. **Verdict pickup:** the dispatching agent's own waiter may not re-wake it —
whoever dispatches should also arm an orchestrator-side watcher on
`<receipt_dir>/meta.json` (its appearance = verdict landed; `tail -1 final_message.md`).

## Implementation-offload recipe

1. **Write a self-contained spec** to a prompt file: goal, exact files to touch, constraints,
   and explicit acceptance criteria (which tests must pass). Codex starts cold — it can't see
   this conversation.
2. **Pick the model tier** from the table above.
3. **Optionally isolate** in a worktree:
   `git -C <repo> worktree add /tmp/cdx_<task> HEAD`, then point `-C` there.
4. **Run in the background** (SOL/high runs take minutes):
   ```bash
   # Hard implementation
   codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s workspace-write \
     -C /home/jjyeung/agent_project \
     -o /tmp/codex_<task>.md - < /tmp/codex_<task>_prompt.md \
     > /tmp/codex_<task>.log 2>&1 &

   # Easy mechanical implementation
   codex exec -m gpt-5.6-terra -s workspace-write \
     -C /home/jjyeung/agent_project \
     -o /tmp/codex_<task>.md - < /tmp/codex_<task>_prompt.md \
     > /tmp/codex_<task>.log 2>&1 &
   ```
   `-o <file>` captures Codex's final message; the redirect keeps the transcript.
5. **Verify before keeping.** `git -C <repo> diff` to read every change, run the acceptance
   tests yourself, then keep or commit. Codex is the worker; you own the merge.

## Notes

- `--output-schema <schema.json>` forces the final message to conform to a JSON schema.
- A significant deployment (e.g. a pre-commit review gate) is worth a `CLOSED_LOOP_LEDGER.md`
  note with the transcript path.
- `/critique` uses the `review` preset (Astra @ high).

## Wrapper: `agent/scripts/codex_dispatch.sh`

For repeatable dispatches, prefer the wrapper over hand-assembling `codex exec`. It picks the
sandbox/model/effort from a preset, writes a per-dispatch **receipt**, appends one line to a
spend log, and (informationally) tracks the run in a registry while it is live. It does **not**
couple to `/critique` — it is a plain launcher.

```bash
agent/scripts/codex_dispatch.sh <preset> <dir> <prompt-file> \
  [--net] [--model X] [--effort Y] [--label NAME] [--skip-git-check]
```

**Presets** (least-privilege first):

| Preset | Sandbox | Model | Effort |
|---|---|---|---|
| `review` | `read-only` | `gpt-6-astra` | `high` |
| `implement` | `workspace-write` | `gpt-5.6-sol` | `high` |
| `mech` | `workspace-write` | `gpt-5.6-terra` | (default) |

**Flags:** `--net` enables `sandbox_workspace_write.network_access=true`; `--model` / `--effort`
override the preset; `--label NAME` names the receipt dir (defaults to the prompt filename);
`--skip-git-check` passes `--skip-git-repo-check`. Outside a git work tree the git check is
**auto-skipped**. A prompt mentioning `setsid`/`nohup` emits a stderr warning (detached procs die
when the sandboxed `codex exec` returns). The wrapper **passes the codex exit code through**.

**Receipts** land in `agent/scratch/codex_runs/<UTC-timestamp>_<label>/`, each holding:
`prompt.md` (copy of the prompt), `transcript.log` (full stdout/stderr), `final_message.md`
(codex `-o` final message), `meta.json` (preset/model/effort/dir/label/exit_code/times/pid).
`agent/scratch/codex_runs/CODEX_SPEND.log` gets one `start | preset | model | effort | label |
wall_s | exit` line per dispatch; `RUNNING.registry` holds `pid|label|start|receipt_dir` rows for
live runs and is cleaned on exit. Receipts/logs are scratch — keep them out of git except when a
dispatch is worth a ledger note.

Examples (the two checked-in smoke dispatches):

```bash
# mech (Terra, write): print AGENTS.md's first line
agent/scripts/codex_dispatch.sh mech . /tmp/prompt_agentsline.md --label smoke_mech_agentsline
# review (Astra/high, read-only): count a script's lines
agent/scripts/codex_dispatch.sh review . /tmp/prompt_linecount.md --label smoke_review_linecount
```
