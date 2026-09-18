---
name: critique
description: >-
  Read-only Codex review of a non-trivial change before it ships: verified legality,
  scientific-validity, duplication, and executability problems only. The critic never designs
  fixes; the orchestrator adjudicates and remediates. Use before writing code, launching a run,
  or committing a new experiment lever, tool, prompt, or refactor.
version: 4.2.0
scope: project
---

# /critique — verified-invalidity review before an idea ships

Before building a non-trivial idea, have an independent Codex reviewer inspect the brief and the
actual code for **verified, material invalidities**. The gate protects legality and experimental
interpretability; it does not predict whether the metric will improve.

**Sandbox/isolation objections are out of scope.** State in every brief that the current sandbox
is ratified as sufficient; discard any sandbox/isolation objections that appear.

## The reviewer (independent and read-only)

| Reviewer | Model | How to launch |
|---|---|---|
| **Codex critic** | **GPT-6 Astra @ high**, read-only hermetic sandbox | the `codex exec` recipe below |

```bash
# Codex critic — run in the BACKGROUND (high takes minutes), then poll the output file
codex exec -m gpt-6-astra -c model_reasoning_effort=high -s read-only \
  -C /home/jjyeung/agent_project \
  -o "$AUDIT/round${R}_gpt.md" < "$AUDIT/round${R}_prompt.md" \
  > "$AUDIT/round${R}_gpt.log" 2>&1 &
```

It may read any file in the repo; writes are blocked at the OS level (`-s read-only`).

## The loop

1. **Write the brief** → `AUDIT=.dual_critique/<timestamp>_<slug>/brief.md` (≤400 words):
   hypothesis · mechanism · what it changes · cost · how it's falsified + the exact
   command/metric that will judge it · why it isn't an already-tried idea (check the ledgers)
   · note that sandbox/isolation objections are out of scope.
2. **Round 1 — the critic reviews.** Fill `CRITIQUE_PROMPT.md` with the brief, dispatch, save
   the verdict (`round1_gpt.md`).
3. **The orchestrator adjudicates.** Verify every objection against the repo. The critic does not
   propose fixes. The orchestrator decides whether and how to repair a real issue; unverifiable
   accusations are Warnings.
4. **Re-run the critic** on the revised brief — hand it the prior verdicts + your diff so it
   confirms you actually fixed things, not just reworded them.
5. **Stop at the verdict or three rounds:**
   - `PASS` → the scoped implementation or run may proceed.
   - `REJECT` → stop and record a mechanism/design NO-GO with the verified fatal reason.
   - `REVISE` → do not launch as written; revise and re-review if rounds remain.
6. **At a three-round `REVISE` cap**, record exactly
   `NO-GO (launch package only; mechanism untested)` in the mandatory `<TOPIC>_RESULT.md` and
   applicable ledger. Include the controlling flaw, violated acceptance condition, and salvage
   boundary. Do **not** add the mechanism to the tried-and-rejected list or claim empirical
   failure. A substantive repair or new evidence may open a fresh gate.

## Rules (short)

- **The reviewer critiques only.** It reports the flaw, evidence, consequence, and violated
  acceptance condition. It never proposes an implementation, fix, or replacement idea.
- `REJECT` is reserved for a verified fatal issue: GT/oracle leakage or other illegality,
  intrinsic unfalsifiability, or an unchanged mechanism already empirically rejected under
  comparable conditions.
- An unchanged resubmission of a **package-only gate failure** remains `REVISE`, not `REJECT`.
- `REVISE` is for a concrete fixable omission that makes the proposed result uninterpretable,
  such as missing mandatory provenance, executable scoring, or a primary causal control.
- Uncertain gain, run noise, incomplete optimization, and missing secondary ablations for a
  bounded pilot are Warnings. Experiments exist to resolve empirical uncertainty.
- Answer shape and deterministic packaging are not legality criteria. Apply `AGENTS.md` §7:
  inference-time-available, GT/oracle-free computation is legal, including answer-shaped tools.
- Every VSIBench package review verifies that `audit_package.py` calls
  `agent/scripts/cohort_guard.py` on both the membership authority and answer-free admission
  input and refuses retired cohorts for fresh evaluation cells.
- Distinguish verified absence of mandatory evidence (`REVISE`) from an unsupported accusation
  (`[UNVERIFIED]`, Warning).
- **Build nothing between rounds** — only the written brief changes. No code, no launches, no
  prompt files until the gate passes.
- **Save every round** (each brief version + verdict) under `$AUDIT/`. No saved rounds = the
  gate didn't happen. `.dual_critique/` is git-ignored; cite its path in
  `CLOSED_LOOP_LEDGER.md` if the idea ships.
- **If the reviewer mutates the repo**, `git checkout --` the touched paths before re-running —
  never re-run against a mutated tree. Don't re-run a *content* FAIL hoping for a luckier
  verdict; advance only by revising into a new brief version.
- **Skip the gate** only for trivial/mechanical work (scoring, bookkeeping, doc edits, tiny bug
  fixes) or when the user explicitly waives it. A tweaked re-run of a rejected lever is a NEW
  idea — gate it. When unsure, gate it.

## Optional pre-launch check

Right before you commit/launch what passed, run one more codex read-only pass on the real
`git diff` / launch config to confirm it matches the brief that passed. Judge provenance and
inference availability, not answer shape, and catch the stale-runner prompt-fallback trap.
End it with `## Verdict: PASS | REVISE | REJECT`.

## Install

Canonical path: `agent_project/.claude/skills/critique/` (symlinked at
`~/.codex/skills/critique` so the codex CLI finds it). Prompt template:
[CRITIQUE_PROMPT.md](CRITIQUE_PROMPT.md).
