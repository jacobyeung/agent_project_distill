---
name: error-swarm
description: Run the per-category failure-analysis swarm after a round completes — one Sonnet subagent per category, fixed [FAIL:*] taxonomy, two-tier output, then aggregate and pick next-round levers. Use after an experiment round finishes to diagnose failures.
---

# Per-category error-analysis swarm

Canonical protocol lives in `agent/agentic_information_5.0/SUBAGENT_ANALYSIS_PROMPT.md` — read it
before dispatching; this skill is the runbook. Error-analysis agents run on **Sonnet 5**
(`model: 'sonnet'`) — authorized; never use Haiku or Opus for this.
Reviewed baselines come only from `agent/evaluation/SCORE_INDEX.json` through its read-only CLI.

## Pre-conditions (enforce before dispatch)

1. Every runner being analyzed has exited, and the directory contains the exact declared raw
   `trace_<qid>.json` set for its dataset/category. Do not use mutable `pred` fields or an old
   12-of-15 heuristic as completion evidence. **Do not dispatch against a live run.**
2. The reviewed score index verifies, and every analyzed category has a development anchor:
   ```bash
   <planner_python from python agent/campaign.py doctor> agent/evaluation/score_index.py verify
   <planner_python from python agent/campaign.py doctor> agent/evaluation/score_index.py \
     query development_500q_anchor --category <cat>
   ```
   Run from the repository root. Do not fall back to a legacy pointer if either command fails.

## Dispatch

One `general-purpose` subagent **per category**, all in a single message (parallel Agent calls,
`model: 'sonnet'`). Each subagent reads only its category's traces. Use the dispatch prompt from
`SUBAGENT_ANALYSIS_PROMPT.md` verbatim — it must instruct each subagent to:

- Tag every wrong question with **exactly one** root cause: `[FAIL:SENSOR_POSE]`,
  `[FAIL:SENSOR_GROUNDING]`, `[FAIL:LOGIC_MATH]`, `[FAIL:LOGIC_PROMPT]`, `[FAIL:RECURSION]`,
  `[FAIL:NO_ANSWER]`, `[FAIL:UNCLEAR]`.
- Write **both** artifacts into `agent/experiments_5.0/<cat>/experiment_<N>/`:
  1. `errors.md` — per-question drilldown
  2. `evaluator_agent_<cat>.out` — the subagent's full reply verbatim
- Return a short structured summary to the orchestrator — headline, failure-tag tally, dominant
  failure mode, one proposed change. The full analysis lives in the two files, not the reply.

The orchestrator MUST verify both files exist per category before treating analysis as done
(re-dispatch any that omitted the `.out`).

## Consider EA v2 refinements (default)

- **Stability filter first**: ~30% of "errors" are run-to-run churn, not real faults — filter to
  stable failures before drawing conclusions; report stable-only flip estimates.
- Pair any flip-claim with a net A/B check (a fix can hit its pre-registered flips yet net-regress).

## Aggregate

1. Collect all 10 reports. Re-query `development_500q_anchor --category <cat>` for each reviewed
   baseline; candidate scores remain provisional and do not rewrite the index.
2. Append a ≤250-word aggregate to `agentic_information_5.0/EXPERIMENT_FAILURE_ANALYSIS.md`.
3. Pick **≤2** of the 10 proposed changes for the next round; prioritize categories still below
   the 0.50 floor.
