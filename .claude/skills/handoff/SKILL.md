---
name: handoff
description: Session-close for this VSIBench project. Reviews in-flight/finished work, then writes findings ONLY to the canonical targets in AGENTS.md §5.1 (the closed-loop ledger, the campaign ledger, coord.py, or a <TOPIC>_RESULT.md) — never CURRENT_STATE.md (single-writer) and never an invented path. Commits completed verified work locally; raw artifacts stay off git. Use before ending a session or as a mid-session checkpoint.
version: 1.0.0
scope: project
---

# /handoff — session-close + commit checkpoint

Closes a session cleanly: review what happened, write findings to the durable files this
project already designates, commit completed units locally, and leave a resume-ready state.
Inverse of `/resume`. Never let verified work sit uncommitted.

**Core invariant — no random directories.** Every write goes to a location named in the
`AGENTS.md` §5.1 "WHERE RESULTS GO" table. Do not create new handoff files, new top-level
files, or invented names. A finding with "nowhere to go" goes in a ledger row — never a fresh
file you made up.

## Procedure

1. **Read the routing.** Open `AGENTS.md` §5.1 and any Git Hygiene rules. That table decides
   *where* things go; this skill enforces *that you obey it*.

2. **Account for every task you ran.** Report anything still running (ids/state). For finished
   work, read its outputs/logs and summarize the result — never claim success without looking.
   First verify `agent/evaluation/SCORE_INDEX.json` and query
   `development_500q_anchor [--category <cat>]` with
   `<planner_python from python agent/campaign.py doctor> agent/evaluation/score_index.py`.
   Score a finished, non-nominated run with `/score` only as a **provisional candidate**; never
   use the `pred` field or imply that compatibility evaluator output changed the reviewed anchor.

3. **Write findings to the canonical targets only** (per §5.1):

   | Produced thing | Goes to |
   |---|---|
   | Provisional run score / A/B number (machine record) | `coord.py complete --result "candidate <cat>=X.X vs reviewed anchor Y.Y; provisional"` |
   | Fix verdict (predicted-flip qids → did they flip; net delta) | a row in `agent/agentic_information_5.0/CLOSED_LOOP_LEDGER.md` |
   | Tool / backbone GO/NO-GO | a `CLOSED_LOOP_LEDGER.md` row; if NO-GO, also one compact row in `agent/agentic_information_5.0/TRIED_AND_REJECTED.md` |
   | Experiment history / what was tried | `CAMPAIGN_LEDGER.md` (append-only) |
   | Integration build detail / gotchas (deep dive) | a dedicated `agent/agentic_information_5.0/<TOPIC>_RESULT.md` / `_HANDOFF.md` / `_PROBE.md`, named like existing precedents — only if substantial |
   | Live "what I'm doing now" | `coord.py status --state running --note "…"` |

4. **NEVER write `CURRENT_STATE.md` unless you are the Orchestrator agent.** It is single-writer — only the coordinator / autonomous
   loop updates it; workers read it. **The paper advisor's equivalent is
   `agent/agentic_information_5.0/ADVISOR_STATE.md` (single-writer: advisor; fixed path,
   overwrite-in-place — advisor handoffs rewrite it per AGENTS.md §1c: freshness header
   with HEAD + time, ≤5-sentence plain-language executive summary, judgment only — no
   machine-derivable counts, no dated copies, no paper-repo dated handoff files).** User
   rulings recorded at handoff go in the queue prefixed `USER-RULING <date>:` (grep-able
   ruling history, one file). Also leave the root `HANDOFF_CURRENT.md` stub as-is (it
   redirects to AGENTS.md). No new root files, no `notes.md` / `SESSION_*.md` / dated files.
   Do not edit `SCORE_INDEX.json` during ordinary handoff. A reviewed nomination is a separate,
   evidence-backed change; legacy score pointers are ignored compatibility side effects.

5. **Commit completed, verified units locally.** Follow AGENTS.md §8.1. Run
   `python agent/check_commit_checkpoint.py --event handoff`; if it says `VALIDATE FIRST`,
   run the relevant smoke/test and then
   `python agent/check_commit_checkpoint.py --mark-validated "<what passed>"`. `git status -s`
   first; stage deliberately (not blind `git add -A`) — raw outputs under `experiments_5.0/`
   and dense `.npz` artifacts never go in git. One coherent unit per commit, descriptive
   message with no AI or co-author trailer. Commit on the current branch. **Push at least once
   per work session** (AGENTS.md §8) and surface an auth failure immediately; local commits are
   the durability boundary when a push fails. If a unit isn't verified, leave it uncommitted and say so.
   After the ledger commit, run `python agent/scripts/rotate_ledgers.py`: it snapshots the
   committed ledgers into the History index, drops terminal queue rows (DONE / NO-GO /
   DECLINED / WITHDRAWN / SUPERSEDED) and rulings older than 14 days from the live files, and
   rotates old campaign-ledger sections. Commit that mechanical change as its own unit, then
   confirm `python agent/scripts/rotate_ledgers.py --check` passes. Queue rows are updated in
   place; never append a second row for the same request.

6. **Blind-spot review — answer for the user: "What's the biggest thing I'm missing? What
   don't I realise?"** After the mechanical close-out, step back and give a candid strategic
   read. This is not a status recap and not optimism; it's the risk analysis the user can't
   see from inside the day's threads. Work through these lenses and report only what's
   load-bearing (1–3 items, ranked; skip lenses with nothing real):
   - **Foundation vs polish:** what looks "done" but rests on a pending or untested
     dependency? (e.g. a paper that is polished but whose central claim awaits an experiment
     still running.)
   - **Unfavorable priors being carried silently:** which in-flight test has a below-even
     honest prior, and is there a pre-planned response for the bad outcome — or would it
     trigger a scramble?
   - **Confounds in headline claims:** does any flagship number conflate two causes (base
     model vs setup, dataset vs method)? What would a hostile reviewer press on first?
   - **Retroactive contamination:** did anything measured this session (noise floors, seed
     variance, invalidated conventions) silently weaken *past* conclusions still being
     relied on?
   - **Asymmetric outcomes:** where do the best and worst plausible results differ wildly in
     required response, and is only one of them prepared for?
   For each item: what the user likely believes, what is actually true, and the one concrete
   action that closes the gap (pre-draft the reframe, run the confirming test, downgrade the
   claim). If the honest answer is "nothing material — the exposed flank is X but it's
   handled," say exactly that; do not invent risks to fill the section.

## Orchestrator mode (when you are the orchestrator agent)

The primary deliverable is rewriting **`agent/agentic_information_5.0/handoff_liveness.json`**
(single-writer: orchestrator only) to this schema — the goal is that the next agent gets full
state from THIS FILE plus the latest ledger addendum, without opening any transcript:

- `written_utc`, `head` (commit + one-line meaning)
- `user_rulings_today`: same-day rulings **verbatim** (they override everything else)
- `results_banked_today`: number + commit/receipt pointer each
- `active_runs[]`, one entry per lane/run: what it is (plain language), pids + hosts,
  log/marker/receipt paths, **a one-line health-check command**, gate state (round N/cap,
  receipt dir), and next-action-on-completion
- round-number registry (orchestrator-assigned; prevents collisions)
- `open_user_decisions`, do-NOT-redo list, session_notes (footguns learned)

**Survives-vs-dies inventory (required):** state explicitly which work survives session close
(detached OS processes: runners, servers, extractions, codex reviewers — all writing receipts
to disk) and which dies with the session (Claude lanes, loop crons, armed monitors/watchers)
— each dying item needs a resume recipe or a next-session action line.

**Acceptance test before committing:** for every lane, can a fresh agent answer "where is it,
how do I check it, what do I do when it finishes?" from the manifest alone? If not, the
manifest is not done.

## Output

Report files written (each a routed target — name it), committed units (hashes + one-liners),
still-running work, what's left, and the **blind-spot review** (step 6) as the closing
section. If a finding seemed to want a home outside the routing table, say so and ask rather
than inventing a path.
