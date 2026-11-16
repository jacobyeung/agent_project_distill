Question: Which trace failures cost CP1 points on development and ReVSI, and what changes address them?

Answer: Incorrect asserted counts, distances and object sizes dominate the combined official-score ceilings. Most final arithmetic follows those assertions. Route traces frequently omit intermediate waypoints and repeat the initial pose. Smaller, directly testable failures include missing unit conversion, ignored facing reversal, wrong comparison operators, unsummed totals, inconsistent option letters and unfinished thinking.

Status: The requested trace audit and local artifacts are complete. Visual causality and label adjudication remain unresolved where the supplied traces and pricing outputs cannot establish them. No training, inference, external writes or benchmark tuning occurred.

Evidence and scope:

- `TRACE_DIAG.md` contains the ranked ceilings, every CP1 type/leaf, numeric distributions, examples, route/count diagnoses and paired thinking comparisons in at most 150 lines.
- `normalized.jsonl` preserves questions, options, labels, scores and full generations from six journals. There are 1,525 rows in each development arm and 999 in each ReVSI run.
- `per_item_causes.jsonl` records the exclusive primary cause, cause family, rule/reading basis, secondary flags, trace details, reading status and per-type/overall lost points. Its SHA256 is adjacent.
- `reading_sample.jsonl` preserves 534 hash-selected failure IDs; `reading_reviews.jsonl` adds 35 targeted audits, for 569 individually read traces. The 11 additional relative-count reviews cover every uncapped development failure in that type. The 24 other targeted reviews check unit, sum and extremum rules.
- `sources.json` pins the six result sources. `INPUT_PINS.json` additionally pins the merge tables, pricing outputs, pricing geometry formulas and scorer code used here.
- `price_join.jsonl` contains the six pricing conditions for 617 matching development IDs. `intermediate_geometry.jsonl` records 4,818 comparisons: scalar measurements, instance counts, 5 cm box-grid candidate distances and signed bearings. `geometry_statistics.json` summarizes every source/policy, including item/quantity denominators.
- `numeric_statistics.json`, `count_statistics.json`, `route_statistics.json`, `cause_by_type.json` and `ranked_causes.json` contain machine-readable tables. `paired_items.jsonl` identifies the 999 shared items in all three pairwise comparisons; `paired_by_type.json` summarizes them.

Decisions:

1. Analyze CP1 ON16k consistently across sets. Preserve B2048/B4096 separately. Development's 71.64 belongs to the budget arms, whereas ON16k scores 71.28. Its 150 routes use local labels and do not belong to the 1,375-item released-label score. The report supplies an additional 1,525-item view so route losses remain visible.
2. Use imported scores as authoritative. Numeric errors include partial-credit losses. ReVSI's overall score is a mean of seven category means, with equal leaf weighting inside a category. A simple 999-item average is not its official score.
3. Assign each imperfect answer one primary cause with secondary flags. Cap and parse failures take priority; route omission can coexist with sequence contradictions; unit errors can coexist with wrong measurements. Counts are not summed across secondary flags.
4. Group the three count-belief subcauses only for ranking. Preserve their separate labels: two-instance habit, other asserted counts and count comparisons. Ranking sums development-primary and ReVSI official percentage-point ceilings, so each set has equal importance. The report also supplies development all-item ceilings.
5. Apply rules to all items. For each CP1 run/type, sort the non-rule-decided failures by SHA256(`trace-diag-v1|RUN|KEY`) and read the first min(40, pool size). A rule that detects a bad scalar does not prove its visual source; unverified numeric assertions remain eligible for reading. The frozen initial rule labels reproduce the sample. Two joint-count cases initially failed the conservative sum parser; targeted reading corrected those cases.
6. Read the question, options, label, answer and full noncapped generation on each selected card. The saved reading notes describe the observed mechanism and uncertainty. Repeated boilerplate does not constitute independent evidence of a scene measurement. Cap detection uses journal metadata without pretending that entire runaway traces were manually read.
7. Treat GT-mask pricing as a reference program rather than perfect ground truth. Compare by exact ID and verify option order. Recompute candidate gaps using the pricing code's 5 cm oriented-box grid and minimum over instance pairs. Compute bearings from the first box centers in the same operand order as the reference program. Do not compare arbitrary world coordinates across frames or sources.
8. Do not infer object identity or double counting from repeated timestamps. Distinct objects can first appear together. Neither CP1 journal contains `<ground>` tags or explicit centroid/position fields; these runs use natural-language measurement assertions. Their latent coordinates cannot be recovered.
9. Rescore concrete trace-only repairs separately from oracle ceilings. A correct sum or unit conversion can leave the scene estimate wrong. The 26 rotated backward errors are selected using labels; a deployable blanket reversal also harms two correct items. No label-conditioned fix is claimed as a tested deployment policy.
10. Replay numeric scoring locally without importing GPU libraries. Development and ReVSI have slightly different floating-point threshold construction. The validator reproduces every parseable imported numeric score. The inclusive development scorer gives constant-2 = 61.87; strict comparison reproduces the brief's 60.9. The underperformance conclusion holds under either calculation.

What remains undecided:
