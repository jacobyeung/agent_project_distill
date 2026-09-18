---
name: resume
description: Session-start bootstrap for this VSIBench project. Reads AGENTS.md and the agent/agentic_information_5.0 ledgers in the documented order, drains the analysis queue check, looks for in-flight work and uncommitted changes, and prints a tight standup (where we are / in flight / next step / blockers / do-not-rerun NO-GOs). Read-only. Use at the start of any working session.
version: 1.0.0
scope: project
---

# /resume — session-start standup

Rebuilds context fast by following this project's own start ritual instead of guessing.
**Read-only: never edit or commit here** — that is `/handoff`'s job.

## Procedure

0. **Pick your role's state doc (AGENTS.md §1c).** Experimenter/orchestrator
   sessions bootstrap from `CURRENT_STATE.md`; **paper-advisor sessions bootstrap from
   `agent/agentic_information_5.0/ADVISOR_STATE.md`** (fixed path; the paper repo's dated
   `PAPER_ADVISOR_HANDOFF_*.md` files are archive only — never bootstrap from them).
   **Freshness contract:** if the state doc's header HEAD is >15 commits or >12 hours behind
   `git log -1`, do NOT trust its volatile claims — orient from
   `grep "USER-RULING" agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md | tail -20`,
   the CAMPAIGN_LEDGER tail, and `campaign.py doctor` (+ `status` once it lands) instead of
   deep-reading history. If the snapshot is fresh, orient from it alone and verify only the
   pointers your first action depends on.

1. **Confirm the root.** Use `git rev-parse --show-toplevel`; the campaign lives under
   `agent/`. Confirm `AGENTS.md` and `agent/agentic_information_5.0/` exist.

2. **Read in the documented order:**
   - `AGENTS.md` (canonical bootstrap)
   - **`agent/agentic_information_5.0/handoff_liveness.json` FIRST for state** — the
     orchestrator's single-writer snapshot: per-lane pids/hosts/log+marker paths, one-line
     health-check commands, gate states with receipt paths, the round-number registry, and
     same-day user rulings. Do not re-derive what it already answers; instead **verify its
     claims** (pid liveness via `[b]racket`-guarded pgrep, file freshness via `find -mmin`,
     endpoint health) and flag divergence rather than trusting either side silently.
   - `python agent/campaign.py doctor` (read-only site, coord, freshness, local worker,
     data-path, Git, and legacy-view checks; report fatal findings first)
   - `agent/evaluation/SCORE_INDEX.json`, validated with
     `<planner_python from doctor> agent/evaluation/score_index.py verify`, then
     `... score_index.py query development_500q_anchor` (reviewed score authority; read-only;
     stop and report the blocker if verification fails)
   - `agent/agentic_information_5.0/CURRENT_STATE.md` (coordinator cache; compare with
     doctor because the checkout may be stale)
   - `agent/agentic_information_5.0/CAMPAIGN_LEDGER.md` — **tail only: the last 2–3 addenda
     (`tail -n 250` or search for the highest `### Addendum`)**. Older sections rotate to the
     archive named in the file's history index; grep a specific round there on demand.
   - `agent/agentic_information_5.0/PERCEPTION_TOOLS_RESEARCH.md` (tool candidates) as needed

   Do not read `LATEST_EXP`, `BEST_EXP`, `BEST_EXP_with_score`, or `BEST_SCORES.md` to select a
   score or baseline. They are ignored compatibility side effects.

3. **Drain-the-queue check (do this every session start).** Count pending closed-loop rows:
   ```bash
   grep -c "| pending |" agent/agentic_information_5.0/CLOSED_LOOP_LEDGER.md
   ```
   If greater than zero, an analysis swarm has left fixes waiting — those get implemented and
   retested before any new experiment. Flag the count in the standup.

3b. **Orphaned-verdicts scan.** Gate verdicts and drain
   completions land as files while no agent is awake — a stopped lane does NOT reliably
   re-wake on its waiter. Scan for state that advanced silently:
   ```bash
   ls -t agent/scratch/codex_runs/ | head -8   # newest receipt dirs
   # for each newer than the last ledger addendum: tail -1 <dir>/final_message.md
   ```
   Any verdict newer than the last addendum and not reflected in `handoff_liveness.json` is
   an action item for the standup (a lane needs nudging or its next step needs dispatching).

4. **Check what's in flight.**
   ```bash
   python agent/campaign.py doctor
   ls agent/rounds/runners/run_experiment_r*.py | sort -V | tail
   GIT_OPTIONAL_LOCKS=0 git --no-optional-locks log --oneline -5
   ```
   Doctor's worker scan is host-local and heuristic; missing remote evidence is unknown.
   Include its reported-lanes section in the standup. Treat exact local PID matches as
   supporting evidence only, and treat stale, unmatched, or remote workers as unknown.
   Do not use `coord.py list` for read-only orientation: its current entry point creates
   a missing coord skeleton before dispatch.

5. **Check working-tree state.** Doctor reports tracked dirty state using non-refreshing Git
   reads. If exact paths are needed, run
   `GIT_OPTIONAL_LOCKS=0 git --no-optional-locks status -s`. Flag uncommitted work from a prior session
   as a loose end, and flag a `main` that is ahead of origin (AGENTS.md §8: push at least once
   per work session; local commits are the durability boundary when a push fails).

6. **Scan for landmines.** Pull the entries in
   `agent/agentic_information_5.0/TRIED_AND_REJECTED.md` and recent `no_go` rows in
   `CLOSED_LOOP_LEDGER.md` so you don't re-propose a rejected approach without a new argument.

## Output (a standup, not a report)

- **Where we are:** reviewed development-anchor score, active round, primary metric, and the
  target (if any) named by the newest `USER-RULING` in the queue. Label conflicting prose as
  stale rather than silently reconciling it.
- **Pending analysis fixes:** the drain-queue count and what they are.
- **In flight:** running experiments/agents with ids and state.
- **Immediate next step:** the single next action from CURRENT_STATE.md.
- **Open blockers** and **uncommitted work.**
- **Don't re-run:** the relevant NO-GOs.

End by asking what to pick up, or proceed if the next step is unambiguous.
