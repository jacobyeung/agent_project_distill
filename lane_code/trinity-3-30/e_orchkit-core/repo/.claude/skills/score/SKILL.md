---
name: score
description: Verify and query the reviewed VSIBench score index, or inspect a new experiment as a provisional candidate. Never use results.json predictions, log prose, or legacy score pointers.
---

# Score a VSIBench experiment

`agent/evaluation/SCORE_INDEX.json` is the score-selection authority. It contains reviewed,
content-addressed mechanical records; it does not infer semantic integrity or automatically rank
runs. Legacy `LATEST_EXP`, `BEST_EXP`, `BEST_EXP_with_score`, and `BEST_SCORES.md` files are never
inputs.

## Reviewed baseline

From `/home/jjyeung/agent_project`, run `python agent/campaign.py doctor` and use the reported
`planner_python` and benchmark paths; doctor-reported paths win. On Trinity, `planner_python`
currently resolves to `/data2/jjyeung/envs/planner/bin/python` (an example only; do not hardcode it).

```bash
<planner_python from the selected site profile> agent/evaluation/score_index.py verify
<planner_python from the selected site profile> agent/evaluation/score_index.py \
  query development_500q_anchor [--category <cat>]
```

Both operations are read-only and fail closed: `verify` checks the authority, while `query` returns
structured JSON. Stop if `verify` fails. Report the role, record id, scope, metric, score, dataset id, scorer id, and
`semantic_integrity` exactly as returned. Do not call the development anchor “strict,” “deployed,”
or “best.” The separate `legacy_reference` role is historical context only.

## New experiment

A run absent from the reviewed index has no authoritative baseline status. If the user asks for
its score, inspect it as a **provisional candidate** with the compatibility evaluator. That legacy
CLI flat-weights every `trace_*.json`, including `_clean` siblings, so never point it at a mixed
experiment directory. Stage only exact raw names in a temporary directory and confirm the count
matches the declared category/dataset scope:

```bash
EXP_DIR=$(realpath <exp_dir>)
RAW_DIR=$(mktemp -d)
find "$EXP_DIR" -regextype posix-extended -maxdepth 1 -type f \
  -regex '.*/trace_[0-9]+\.json' -exec ln -s {} "$RAW_DIR/" \;
find "$RAW_DIR" -maxdepth 1 -type l | wc -l
<planner_python from the selected site profile> agent/evaluate_benchmark_v4.py "$RAW_DIR" \
  --dataset_path <benchmark path from the selected site profile>
```

Report `$RAW_DIR/results_evaluated.json`, including overall, per-type metrics, exact raw count, and
matched question count, then remove the temporary directory.
State that the number is provisional until an exact raw-trace record is reviewed and nominated in
`SCORE_INDEX.json`. Do not select an experiment directory from a pointer or score `results.json`.

## Guardrails

- Authoritative records accept exact `trace_<integer>.json` files only and exact declared qid
  scope; `_clean`, live JSONL, malformed, duplicate, missing, and unexpected traces are excluded or
  rejected by the record contract.
- `results.json` predictions and log prose are never score sources.
- A mechanical score does not prove primitive-only composition or scientific eligibility.
- One run is noisy: 500q mean swings ±2–3 points, and absolute distance can swing ±12. Require a
  repeated win or a gain outside that range before proposing a reviewed anchor change.
