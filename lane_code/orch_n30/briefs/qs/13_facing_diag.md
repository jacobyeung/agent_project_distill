# Build brief 13: facing-away diagnosis from D0's read outputs, and the alternative row forms held ready

Builder: Claude Opus, medium effort. Written by lane queue_synth, 2026-11-16. CPU only. Useful from D0's step-200 read (about 18:00 to 19:30Z).

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU, no Orchard call. The D0 stop rule and the init rule are registered: this lane changes no verdict and no rule; it explains failures. Lane folder `/scratch/jjyeung/orch_n30/facing_diag`; events `B/events/facing_diag/`.

## Why
On ReVSI the step-544 student scores 88.3 when it faces toward the named object and 14.0 when it faces away; direction is one of seven categories, so the defect is worth about 5.3 ReVSI points (direction 51.2 to about 88) and nothing on VSI-Bench or VSTI. D0 trains toward/away twins with an explicit half-turn line (`distill_design/TRACE_RULING_20261115.md` section 2.3). Its reads report away accuracy and pair classes, but not why an away answer is wrong. If the fix stalls, the next rows build must know which line of the trace failed.

## Inputs
- D0 read kit and its outputs per milestone: lane cont_ops on trinity-1-3 (`work/d0/readk/`, `f1f2.py`, the per-item ITEMS.jsonl with generated traces; `B/events/cont_ops/STATUS.md`, `READS_PLAN_D0.md`), step 544's baseline `evidence/A544.jsonl` (away 38 / 20 / 6; 49.3% of pairs answered alike).
- The 150 dev twins and the twelve transitions (`FACING_AWAY_DIRECTION_ROWS_20261112.md`; dev constants 54 / 40 / 36), the row form of section 2.3.
- ReVSI backward items' wording class (33 away items in the official read; question text only, no labels needed for the classifier).

## What to build
1. `classify_away.py`: for every away item of a read, from the generated trace alone: (a) no facing clause written; (b) clause written, relation not turned; (c) turned on one axis only (front and back, or left and right); (d) forward relation itself wrong (the toward twin is also wrong); (e) correct; (f) other or unparsed. Output per level and per transition, with the toward twin's status beside it.
2. A table per milestone (544, D0 m200, m400, ...) so the trend of each class is visible; it is printed beside `f1f2.py`'s verdict, never instead of it.
3. Three alternative renderings of the away rows, built and validated but not admitted, one per failure class: for (a) more phrasings of the away clause, including ReVSI's "facing in the opposite direction of"; for (b) a form that writes the turned relation as its own line before the option; for (c) per-level rules written out for hard and medium. Each as a deterministic rewrite of the existing 33,985 twins with labels unchanged.
4. A one-page rule for the rows lane: which rendering to take for the next leg given the class table.

## Tests
Classifier unit tests on hand-written traces for each class; agreement with `f1f2.py`'s pair classes on step 544 (74 unchanged, 41 opposite, 35 neither); validator a41ba191 on 100 rows of each rendering; label equality with the source twins.

## Do not touch
The D0 read kit (read its outputs only), the registered rules, the D0 v5 row store, benchmark labels.

## Deliver
The classifier, the tables for every milestone read so far, the three renderings with hashes, STATUS.md, one RESULT event per milestone. Review: none for the diagnosis; an admitted rendering goes through the rows lane's review.
