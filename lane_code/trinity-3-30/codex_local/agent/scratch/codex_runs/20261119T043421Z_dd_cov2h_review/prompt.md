# Read-only review: coverage v2H for vehicle N (held-out wordings) — rows, generator, split rule, held-out guarantee, wordings, R0 held-out set

You review, you do not fix. Report only verified problems (with the command or line that shows each), then a verdict: GO, GO AFTER FIXES, or NO-GO. Write no file. Work inside this directory (/scratch/jjyeung/orch_n30/dist_diag/review_cov2; `tree` links to ../review_cov1/tree, which you may read). No ssh, no network, no searching elsewhere. Python: /scratch/jjyeung/envs/planner_local_v1/bin/python (3.12, numpy; no sqlite3).

## Order and context
The order is `20261119T0422Z_ORCH_ORDER_coverage_v2_holdout_wordings.md`. Leg R1 skipped the tower call on many dev-S1 absolute-distance questions whose wording differs from the single routed training wording. Coverage v2H adds routed rows in new wordings while keeping a HELD-OUT set of dev-S1 wordings untrained, so that a gate can test transfer.

## Files
- `COVERAGE.json`: the 21 exact dev-S1 wordings (keys of `cells`) with per-unit item counts and step-544/200 call counts; `named` = the 15 with a step-200 call rate under 90%.
- `SPLIT_V2.json`: the split rule and the result (HELD-OUT 8, TRAIN-DEV 10, unused 3).
- `WORDINGS_DRAFT_80.json` (Codex draft), `FORBIDDEN.json`, `filter_wordings.py`, `NEW_WORDINGS_V2.json` (40 chosen), `WORDINGS_V2.md`.
- `pub/`:
  - `coverage_rows_v2h.py` (the generator, run elsewhere on N's bound slices) and `TEMPLATES_V2H.json`;
  - `COVERAGE_UNITS_V2H.jsonl.gz` (4,500 ft/in/cm rows) and `COVERAGE_DISTANCE_V2H.jsonl.gz` (1,500 metre rows);
  - `SUMMARY.json`, `READ30.txt`.
- `sources/COVERAGE_SOURCES_V2H.jsonl.gz`: the 6,000 source rows (match by stripping `_dhNN`).
- `tree/work/tree_r1`: the vehicle-N kit subset (`student_pilot/ground_rows.py` pack and validate, `trace_format/`, `generator/derivgen_v7/derivgen/`, with `candidate_identity` in `ground_v312_quality.py`).
- `R0_HELDOUT_EVAL_V1.json` and `make_r0_heldout.py`: the evaluation-only held-out set (290 reworded R0-dev items plus their 290 original twins).

## Check
1. Split: recompute it from COVERAGE.json and the rule in SPLIT_V2.json. Is it deterministic, and does it give 5 failing + 3 other HELD-OUT wordings and 10 TRAIN-DEV wordings?
2. Held-out guarantee: no output row's question matches any HELD-OUT wording, as a template with {a}/{b}/{u} slots. No TRAIN-DEV or NEW template equals or contains a HELD-OUT wording. Check also near-duplicates between HELD-OUT and NEW wordings by normalized edit distance, and report the minimum.
3. NEW wordings: recompute the filter from the draft, FORBIDDEN.json and the rule. Does each chosen wording name both objects, the closest-point convention and the unit, with no dev or near-dev duplicate? Read all 40 for grammar and for ambiguity across all four units.
4. Rows against sources: every field except qid, question, question_identity, candidate_id (also inside ground_record for units rows) and one provenance edit record equals the source. The question equals its template filled with the source's own objects and unit. Cells hold exactly 50 (template ids 00-09) and 25 (10-49) per unit. Each source is used once, and qids are unique.
5. Arithmetic: for non-metre rows, one printed gap and one "Converting to <unit>: g x F = y." with F = 100 / 3.28084 / 39.3701; y = ROUND_HALF_UP(g x F) to 1 (cm) or 0.01 (ft/in); answer, closing tag, ground_record.unit and the question's unit agree. For metre rows, the answer equals the printed gap.
6. Kit validator on every row: units via ground_rows.pack(dict(ground_record, suffix=target), provenance) then validate; distance after rebuilding events from the suffix. candidate_id equals candidate_identity on the new qid and question (per the provenance rule), is unique, and never equals a source id.
7. R0 held-out set: 290 reworded items, units balanced 73/73/72/72, each with one HELD-OUT wording; the ground truth is converted exactly from gt.distance_m; each twin keeps the original question and metres; no reworded question uses a non-held-out wording. Would anything in the item fields stop a routed read package from scoring them with an official_vsi_mra scorer that takes the unit from the question?
Report counts for every check, then the verdict.
