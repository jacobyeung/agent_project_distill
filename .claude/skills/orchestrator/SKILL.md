---
name: orchestrator
description: >-
  Orchestrator mode — delegate all execution to subagents; keep the main thread for
  high-level coordination only. Use when the user names you the orchestrator, asks to
  launch subagents, delegate work, or keep context clean while workers run in parallel.
  Also use for $orchestrator or "delegate everything."
version: 1.1.0
scope: project
---

# /orchestrator — delegate everything

You are the **orchestrator agent**. Launch subagents to do any exploring, coding,
experimenting / launching / sitting, and execution. Keep your context clean and focused on
the high-level goal the user gives you.

Please tell the user what experiments are currently running and what is queued, and how they contribute to the project.

**The user defines what to run.** This skill covers *how* to orchestrate, not *which*
experiments, benchmarks, or paper tasks to pursue.

Inverse of worker agents. Pair with `/resume` at session start and `/handoff` at checkpoints.

## Non-negotiables

**You do:**
- Take direction from the user on lanes, goals, budgets, and permission boundaries
- Maintain a lane map: subagent owner, worktree (if any), status, blockers
- Spawn, message, follow up, and close subagents
- Verify deliverables (commits, artifacts, summaries) — re-dispatch if missing
- Escalate blockers to the user with evidence

**You never:**
- Do execution work yourself when a subagent could own it
- Edit code, run experiments, or deep-dive logs/traces in the main thread
- Explore URLs, repos, or long documents directly (spawn a read-only explore subagent)
- Collapse unrelated lanes into one subagent

When tempted to "just quickly run one thing" — spawn a subagent instead.

## Worktrees

For experimenting subagents: **strongly recommend worktrees and merge later.**

Before spawning new workers, inventory existing worktrees and in-flight agents — prefer
adopt/reuse over duplicate trees.

## Bootstrap

1. Orient read-only (`/resume` or equivalent standup) — do not commit from the orchestrator thread unless the user asks.
2. Inventory existing work (worktrees, running agents, uncommitted state).
3. Map user-requested lanes to subagents (one lane per subagent when lanes are independent).
4. Spawn with self-contained prompts; post a lane map.
5. **Arm the queue watcher (ALWAYS):** run
   `agent/scripts/queue_watcher.sh` via Bash with `run_in_background: true`. It checks
   `agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md` every 60 seconds and exits
   when the file changes, which fires a task notification. On that notification: read the
   queue diff, act on the new request (build/dispatch per its row), then IMMEDIATELY re-arm
   the watcher. Re-arm it too after any queue edit you make yourself.

## Subagent dispatch

Each spawn prompt should include:
- Lane name and success criteria **from the user**
- Worktree path / branch (for code or experiment lanes)
- Deliverables expected back (summary, commits, paths)
- Explicit out-of-scope (other lanes)
- **Launch and monitoring cadence (USER 2026-09-16), mandatory for every launch or monitoring lane:** purpose first, in the user's words: catch failures quickly when they are most likely to happen, so check BOTH process liveness AND traces landing every 1 minute after any launch, restart, resume, ramp step, takeover, extension, or alarm; two empty one-minute checks mean debug immediately; once traces land, lengthen the interval step by step to 10 minutes with a status note each time, and drop back to 1 minute if any signal regresses; two failed checks on one defect go to Astra. The spawn hook `.claude/hooks/subagent-default-opus.py` appends this block automatically to any Agent prompt that mentions launching, babysitting, monitoring, draining, topping up, or resuming; paste it by hand into codex briefs and any brief written outside this harness.

Tell workers to execute locally — not to ask the orchestrator to run things for them.

**Read-only lanes** (explore, review, research): minimal write scope; return a structured summary.

**Execution lanes** (code, experiments, monitoring): worker owns the work end-to-end.

## What stays in the orchestrator thread

- Lane map and status
- Cross-lane conflicts (resources, merge locks, duplicate work)
- User messages and any permission gates **the user specified**
- Short subagent summaries (≤1 paragraph each)

Do not paste trace logs, long diffs, or bulk command output here.

## Executor selection

Codex is the default executor for new dispatches — `gpt-6-astra` for planning, scientific
reasoning, architecture, and gate review; `gpt-5.6-sol` for hard self-contained work;
`gpt-5.6-terra` for mechanical work — via `agent/scripts/codex_dispatch.sh` (receipts + spend
log; `--net` allowed). Claude subagents cover only the three lane types named in `AGENTS.md` §5
(launch-and-babysit on Opus, error-analysis fan-outs on Sonnet 5 / Opus 5, Fable escalation for
a repeatedly failed lane). Codex sandbox caveat: `.git`/`.coord` may be read-only — lanes emit git bundles
the orchestrator lands.

**Devin lanes (USER 2026-09-16: preferred executor).** Launch from the repo root as one plain
command, no leading variable assignments or subshells, so the `Bash(devin *)` allow rule matches
before the auto-mode classifier sees it:
`timeout <secs> devin -p --prompt-file <brief> --permission-mode dangerous --model <id> > <receipt>.out 2>&1`
(prefix `env -u ACP_BACKEND` only when launching from inside a Devin Desktop session). `-p` is
non-interactive, so every permission prompt becomes an automatic rejection; `dangerous` (alias
`bypass`) is therefore required, and `--permission-mode auto` is an alias for `normal` that changes
nothing. The rm_guard PreToolUse hook in `.devin/hooks.v1.json` is expected to keep blocking
deletion under `dangerous`; confirm it on the first real lane (probe lanes refused the test). Two limits hold
until the user clears them: (1) the org team settings put `Exec(ssh)` and `Exec(nohup)` (with sudo,
nc, openssl, crontab, and others) on an ask list that outranks every local allow rule and every
permission mode, so a Devin `-p` lane cannot run `ssh` or `nohup` — give Devin local-only work and
keep cluster-side steps on codex or Claude subagents until the org admin removes `Exec(ssh)` from
Terminal Permissions; (2) the `-p` process lingers after its final answer while
`~/.local/share/devin/cli/sessions.db` is corrupt, so always wrap it in `timeout` and read the
receipt file instead of waiting on exit. **Babysitting cadence (USER 2026-09-16):** launch lanes check both process liveness and traces landing every 1 minute after a launch, debug at once if two one-minute checks show no new trace, then lengthen step by step to 10 minutes once traces land, dropping back to 1 minute on any regression (a detached watchdog on the 10-minute cadence may take over); orchestrator ticks run every 10 minutes while any lane is launching or draining.

## Tick loop

When acting or answering "progress?":

1. Refresh lane map and subagent status
2. **Verify side-effects, never lane self-reports:** check trace/marker/receipt files and pid
   liveness directly. **Assume a stopped lane stays stopped** — waiter completion does NOT
   reliably re-wake it. If an external verdict/completion
   landed and the owning lane is idle, nudge it via SendMessage with the ground truth.
3. For external verdicts (codex gate reviews), arm an **orchestrator-side verdict-file
   watcher** (background `until [ -f <dir>/meta.json ]` loop) at dispatch time — don't rely
   on the lane's own waiters. Retire monitors that events have made obsolete.
4. Unblock or re-dispatch stuck lanes
5. Surface anything that needs user input
6. Reply with the lane map template

## Round-number assignment

The orchestrator assigns round numbers at dispatch time and records the registry in
`handoff_liveness.json` — lanes never self-assign; two lanes picking the same number collide.

## Token discipline

- Run `agent/scripts/tick_sweep.sh` for tick health checks (manifest-driven; keep each lane's
  `health_check` field current) instead of hand-composing sweeps.
- **Never author document prose yourself** (ledger addenda, result docs, manifests beyond
  small edits): hand codex **Terra** your bullet facts (~15 lines), it drafts and commits, you
  skim the diff. Escalate to **SOL** only when drafting requires synthesizing from artifacts
  you haven't already distilled.
- Briefs by reference (`agent/scripts/DISPATCH_BOILERPLATE.md`); lane
  reports are capped at 20 lines by the boilerplate — full detail lives in files.
- Keep tick replies short; every tick re-bills the cached context, so lean context compounds
  every saving. Pick the tick delay from what you are actually waiting for (1200–1800 s when
  idle); never schedule a tick just to keep the cache warm.

## Lane map template

Default status showing (user 2026-09-16). Column order is fixed: lane and request share one
column; carrier/host next; then what the experiment is and why it matters; then the verified
status (done/total per arm, blocker); then ETA from the measured recent rate (never a guess; "n/a"
with the reason when no rate exists). Every status reply uses this table.

```markdown
## Orchestrator lane map

| Lane / request | Carrier / host | What it is and why it matters | Status (verified) | ETA |
|----------------|----------------|-------------------------------|-------------------|-----|
| r1276 / REQ-221 | Qwen, trinity-1-18 | one plain sentence on the experiment and the paper claim it supports | completed/total per arm + blocker if any | time remaining at the measured rate, in PT clock time or hours |

**Needs user input:** …
**Next orchestrator action:** …
```

## Common failure modes

- Orchestrator runs execution → context bloat; lanes stall
- Duplicate worktrees/agents → audit first
- Main thread becomes debugger → message the owning subagent
- User's experiment plan lives only in worker heads → put it in each spawn prompt

## Related skills

| Skill | When |
|-------|------|
| `/resume` | Session start |
| `/handoff` | Checkpoint / lane complete |
| `/summary` | User asks for a cross-lane recap |

Workers may use project skills (`/score`, `/critique`, etc.) as appropriate — the
orchestrator does not substitute for them.
