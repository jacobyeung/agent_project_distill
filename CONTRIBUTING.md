# Contributing

## Commit and run discipline

Fix distillation code in place and commit each logical change. Do not create immutable package copies for routine work in this repository. Keep each imported source's provenance and preserve its history. Do not amend or rewrite published history to hide a correction.

A launch must use a clean, committed checkout. Commit SHA and the exact config SHA-256 identify a run epoch; record both in every run, trace, and target. Drain or close the current epoch before changing code or config. A new commit must not silently change an active run.

Use `tools/provenance.py` as a required preflight:

```sh
if ! PYTHONDONTWRITEBYTECODE=1 python -B tools/provenance.py "$CONFIG" > "$NEW_RUN_ROOT/provenance.json"; then
  echo "Launch refused by provenance preflight" >&2
  exit 1
fi
```

`CONFIG` must name the exact config bytes the run will consume, and `NEW_RUN_ROOT` must be a new output directory under `/data2/jjyeung/agent_project_data/`. Check the command's exit code before proceeding: 0 means clean, 1 means dirty, and 2 means invalid or unavailable provenance. Persist the returned `repo_commit` and `config_sha256`; never substitute a branch name, a hand-written hash, or a hash of reserialized config content. Launchers must require the reviewed commit where a gate specifies one.

The copied source launchers are not automatically governed by this helper. Bind their deployment paths, config, source dependencies, and provenance explicitly before using them. An imported contract does not authorize a new run.

## Review and verification

Require one independent review only when a change touches admission, legality, or scoring. Operational wrappers and glue need relevant smoke tests, not additional review rounds. Keep an unresolved gate closed; do not treat passing unit tests as admission or benchmark nomination.

Run the relevant checks in `README.md`, record exact totals and failures, and inspect the staged diff before committing. Keep source snapshots byte-identical when importing them; record intentional follow-up changes in separate commits. Preserve failed-test evidence. Do not modify sealed or candidate source packages in place.

The main repository remains authoritative for benchmark scoring and the experiment request queue. Privileged teacher supervision is training-only. Student benchmark inference must remain RGB-only and tool-free, without answers, ground-truth geometry, or correctness-derived state.

## Data and coordination

Keep data, caches, models, checkpoints, traces, targets, run receipts, and large artifacts outside Git under `/data2/jjyeung/agent_project_data/`. Never delete or clean files. If a workspace artifact must move, rename it under `_quarantine/` and preserve its provenance. Do not alter another lane's working files or shared coordination state.

Follow the main repository's legality, answer-bank preservation, no-deletion, and coordination rules. Win the applicable lease before launching an experiment. Scope searches to explicit named directories; never sweep filesystem or data roots.

## Lane liveness

Within the first minute of a lane, and at least every five minutes afterward, append `<UTC timestamp> | <current step in at most 12 words>` to its `out/HEARTBEAT.log`. Rewrite `out/PROGRESS.md` in at most 15 lines with done, doing, next, and blockers. Use a plain shell `echo >>` between steps; do not wait for a milestone. Ten silent minutes may terminate a lane.

Always finish with the lane's `out/REPORT.md`, including on failure. For this repository's migration convention, keep it within 30 lines and end with `DEVIN_LANE_DONE`. Respect each brief's limits on API calls, GPUs, remote execution, and process lifetime; a general autonomy ruling does not waive those boundaries.
