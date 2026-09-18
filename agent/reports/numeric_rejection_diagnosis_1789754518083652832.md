# Numeric rejection diagnosis — census 1789754518083652832 (REQ-20260917-232)

Scope: `object_size_estimation`, `room_size_estimation`, `object_abs_distance` records from
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/census_r1313/1789754518083652832/DECISIONS.json`.
Selection = reason `numeric_mra_1.0` OR trace `question_type` in the three types (all records
of these three types, 121 total, satisfy the OR — every one was pulled in). No `offline_labels`
or `answer_bank` path was opened; only `trace_path` JSONs and `collector/census.py` were read.

## 1. The census numeric rule (quoted)

`/home/jjyeung/agent_project_distill/collector/census.py`:

- Lines 34–42, `requested_unit(row)` — extracts the unit the question text asks for. For
  `room_size_estimation` it looks only for `m2`/`ft2` phrasing; for the other numeric types it
  looks for `m`/`cm`/`ft`/`inch(es)` and explicitly excludes the bare token `in` (`label!='in'`)
  because it collides with the English preposition. `raise ValueError('ambiguous or missing
  requested unit')` if more than one unit phrase matches or none does.
- Lines 45–61, `grade(row, gold, answer)`:
  - Line 50: `match=re.fullmatch(r'\s*('+NUMBER+r')\s*(.*?)\s*', answer)` — parses the model's
    `<ANSWER>` text into a leading number plus an optional trailing suffix.
  - Lines 57–58: `unit=requested_unit(row); if suffix and UNITS.get(suffix)!=unit: return
    False,'incompatible_or_unknown_unit'` — a unit check fires **only if the model's answer text
    itself carries a unit suffix that disagrees with the question's unit**. If the answer is a
    bare number with no suffix (the common case — see §2), no unit check happens at all; the
    number is compared as-is, in whatever unit the model implicitly meant.
  - Lines 59–61 (the rule that produces `numeric_mra_1.0`):
    ```
    # MRA at thresholds .50,.55,...,.95 awards full credit only through 5% error.
    correct=target>0 and abs(pred-target)/target <= .05+1e-12
    return correct,'numeric_mra_1.0'
    ```
    So `numeric_mra_1.0` is a binary pass/fail at a flat **5% relative-error** band around the
    (unseen) gold value — not the graded multi-threshold MRA curve its name references.

## 2. Counts, magnitude distributions, units

| type | selected | accepted | rejected |
|---|---|---|---|
| object_size_estimation | 26 | 6 | 20 |
| room_size_estimation | 5 | 1 | 4 |
| object_abs_distance | 90 | 43 | 47 |

Pred magnitude (in the question's own requested unit):

| type | group | n | min | median | max |
|---|---|---|---|---|---|
| object_size_estimation | accepted | 6 | 0.492 | 40.5 | 319.0 |
| object_size_estimation | rejected | 20 | 0.353 | 21.8 | 113.0 |
| room_size_estimation | accepted | 1 | 20.5 | 20.5 | 20.5 |
| room_size_estimation | rejected | 4 | 37.0 | 113.0 | 1633.0 |
| object_abs_distance | accepted | 43 | 1.36 | 17.0 | 1286.0 |
| object_abs_distance | rejected | 45 | 0.353 | 19.3 | 612.0 |

(`object_abs_distance` rejected n=45/47 and `pred` stats exclude the 2 records with no
parseable numeric `pred` — both `missing_answer`.) Accepted vs. rejected magnitude ranges
overlap heavily within each type; rejection is not concentrated at one end of the scale.

Units implied by question phrasing (via `requested_unit`, replicated from census.py; every one
of the 121 questions resolved to exactly one unit — no ambiguous/missing cases):

- `object_size_estimation`: `ft`=5, `cm`=8, `m`=4, `in`=9
- `room_size_estimation`: `m2`=2, `ft2`=3
- `object_abs_distance`: `in`=28, `ft`=26, `m`=23, `cm`=13

## 3. Classification of rejected traces

Method: for each rejected record, collected (a) every number the `execute_python_code` tool
printed to stdout, tagged with its unit where a unit word appears on the same line/adjacent to
the number; (b) every `extent_xyz` / `extent_xyz_p90` axis value from `get_3d_points_in_mask`
and `aggregate_aabbs_median/robust` returns (always meters); (c) `object_label` arguments passed
to `find_frames_with_object` / `predict_2d_segmentation_masks*`; (d) `pred_source` (a clean
`<ANSWER>` tag vs. a harness salvage/fallback). Categories applied in priority order e→c→a→b→d→f.

| type | n rejected | (a) unit mismatch | (b) wrong dimension | (c) wrong object | (d) close self-consistent match | (e) no tool / no clean answer | (f) other |
|---|---|---|---|---|---|---|---|
| object_size_estimation | 20 | 0 | 0 | 0 | **16 (80%)** | 4 (20%) | 0 |
| room_size_estimation | 4 | 0 | 0 | 0 | **4 (100%)** | 0 | 0 |
| object_abs_distance | 47 | 0 | 0 | 0 | **40 (85%)** | 7 (15%) | 0 |

Examples:

- **(d) close self-consistent match** — the model's final `pred` equals (usually within 1–5%,
  always within the 25% band) a number its own tool chain already computed for the right object
  in the right unit; it still misses the grader's 5% band, i.e. the arithmetic/unit handling is
  not what fails.
  - `vsi590k_056355` (object_size_estimation): pred=1.7 ft ≈ printed `1.7024...` ft.
  - `vsi590k_058828` (room_size_estimation): pred=37 m² ≈ printed `Floor area: 36.66`.
  - `vsi590k_059303` (room_size_estimation): pred=167 ft² ≈ printed `Area in sq ft: 167.029`.
  - `vsi590k_048392` (object_abs_distance): pred=7.55 ft ≈ printed `7.4` ft (one of several
    frame-pair distance estimates the code tried).
- **(e) no measurement tool used / no clean final answer** — `pred_source` is
  `salvage_commit`/`tool_output_fallback`, or `reason='missing_answer'`: the agent never emitted
  a parseable `<ANSWER>` tag and the harness substituted a recovered number.
  - `vsi590k_056353` (object_size_estimation): `pred_source='tool_output_fallback'`, pred=0.3527
    — no printed stdout number anywhere near this value; a stray fallback pick.
  - `vsi590k_048396` (object_abs_distance): repeated `find_frames_with_object` retries over
    `clock`/`wall clock`/`alarm clock`/`digital clock`/`mantel clock`/`grandfather clock`/`watch`
    label variants with stdout only `"Ready"` — no distance was ever computed; `pred_source='salvage_commit'`.
  - `vsi590k_048416` (object_abs_distance): `pred_source='salvage_commit'`, pred=27 in — this one
    *does* match a computed value almost exactly (`Min dist: 27.356 inches`), so the underlying
    math was fine; the failure is that the agentic loop never wrapped it in a clean `<ANSWER>`
    tag before the harness intervened.

No record in any of the three types was classified (a) unit mismatch, (b) wrong dimension, or
(c) wrong object under this scheme. Two apparent (a)/(b) hits from an earlier pass turned out to
be false positives from the classifier itself: a ×100 m↔cm ratio between `pred` and a raw meter
extent is what a *correct* conversion looks like, not a bug, and pred≈raw-extent-on-the-z-axis
for a "longest side" question can be legitimate when an object's height genuinely is its longest
side (confirmed on an accepted record, `vsi590k_056357`, see §4). The heuristic is deliberately
loose per the task's "about 100x", "within 25%" language; it should be read as evidence, not
proof, but the complete absence of a/b/c hits across 71 rejected records (drawn from unit
requests spanning `ft`, `cm`, `m`, `in`, `m2`, `ft2`) is a strong, non-coincidental signal.

## 4. Same classification, 12 accepted traces (what passing looks like)

| id | type | pred | req unit | category | note |
|---|---|---|---|---|---|
| vsi590k_056354 | object_size_estimation | 319 | cm | d | matches extent 2.7051 m ×100 (axis x) within 25% |
| vsi590k_056357 | object_size_estimation | 71 | in | b* | matches z-axis (height) extent 1.8131 m; question asks "longest side" — here height genuinely is the longest side |
| vsi590k_056359 | object_size_estimation | 6 | ft | d | matches printed 6.29 ft |
| vsi590k_056362 | object_size_estimation | 0.4917 | m | d | matches printed 0.4917 m exactly |
| vsi590k_177342 | object_size_estimation | 120 | cm | d | matches printed 120.0 cm exactly |
| vsi590k_178286 | room_size_estimation | 20.5 | m2 | d | matches printed alpha-shape area 20.617 m² |
| vsi590k_048391 | object_abs_distance | 204 | in | d | matches printed 204.07 in |
| vsi590k_048397 | object_abs_distance | 12.7 | ft | d | matches printed 12.65 ft |
| vsi590k_048400 | object_abs_distance | 14.18 | ft | d | matches printed 14.17 ft |
| vsi590k_048402 | object_abs_distance | 192 | cm | d | matches printed 197.18 cm (within 25%) |
| vsi590k_048404 | object_abs_distance | 5.26 | m | d | matches printed 4.846 m (within 25%) |

Over the full accepted set (50 records across the three types): 48/50 classify (d), 1/50 (b*,
the height/longest-side case above — a classifier artifact, not a real bug), 1/50 (f, unresolved
by the heuristic). Accepted traces look exactly like the rejected (d) majority: a self-consistent
match between `pred` and the agent's own computed number. The census's 5% cutoff, not the
category, is what separates them.

## 5. scannet vs. scannetppv2 (rejected only, by class)

| type | scannet | scannetppv2 |
|---|---|---|
| object_size_estimation | d=8, e=1 (n=9) | d=8, e=3 (n=11) |
| room_size_estimation | d=2 (n=2) | d=2 (n=2) |
| object_abs_distance | d=28, e=3 (n=31) | d=12, e=4 (n=16) |

scannetppv2's share of rejections that fall in (e) — no clean computed answer at all — runs
higher than scannet's in both types where the comparison is meaningful: object_size_estimation
(3/11 = 27% vs. 1/9 = 11%) and object_abs_distance (4/16 = 25% vs. 3/31 = 10%). The (d)
self-consistent-but-outside-tolerance share is comparable between the two datasets. No record in
either dataset prefix classified as (a), (b), or (c).

## 6. Plain observations

Across 71 rejected traces in these three numeric types, the census's stated failure signature —
`numeric_mra_1.0`, a flat 5% relative-error band with no unit or dimension check beyond what a
bare-number `<ANSWER>` answer skips entirely — matches a pipeline where the model's tools ran,
computed a number for the object and unit the question actually asked about, and the model
reported that number essentially unchanged into its answer. Roughly four in five rejections in
every type put `pred` within 25% (usually within a few percent) of a value its own tool chain
already printed, for the correct object and requested unit, leaving the 5% gate itself — not a
unit, dimension, or object-identity mistake — as the immediate reason those cases fail. The
remaining rejections, roughly one in five for object_size_estimation and object_abs_distance and
none observed for room_size_estimation, trace to the agent never producing a clean `<ANSWER>` tag
at all (harness salvage/fallback substitutes a stray or partially-computed number), sometimes
after visibly failing to resolve an object label like "clock" through several synonym retries.
object_abs_distance traces frequently ran the same distance computation across many frame-pair
and mask-erosion parameter combinations that produced widely scattered raw distances (an
observed spread from under 0.01 ft to over 11 ft for one object pair) before settling on a final
number, pointing to measurement instability across viewpoints as a contributor distinct from any
unit or dimension confusion. Room-size rejections were small in count (n=4) but uniformly showed
the agent's own printed area, correctly unit-converted where the question asked for square feet,
adopted verbatim as `pred`. scannetppv2 scenes showed a higher share of no-clean-answer failures
than scannet scenes in both types where that comparison had enough rejected records to compare.

---
Diagnostic script and intermediate extraction were run in-memory via `python3 -B` against
`DECISIONS.json` and each selected `trace_path`; no other files were written except this report.
