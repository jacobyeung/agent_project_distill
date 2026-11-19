# RESULT review_tree: NOT READY (tree a1f559e2, kits A0 5c2ca33ca02a / A2 473395544605)
Verdict file: REVIEW_VERDICT_TREE.md, in this folder; the evidence/ folder holds the harness scripts and JSON outputs.
Blocking:
1. Neither kit creates a runtime environment. job.sh runs bare python3 and f.sh runs /usr/bin/python3 with env -i, while the pinned venv is never staged or activated, so both stop with ModuleNotFoundError numpy before any gate. With numpy available, mode t stops at init_m544 evidence and mode h at the missing pose sources, which are the intended refusals.
2. The A0 config references 57 relative u/<hash> paths; none is in the kit and nothing stages them (the parent's c.sh did).
3. Real rows do not pass intake as published (all 30 slices refused). With my adapter, recovery admits 0/1532: r2_contract.py:196 requires a literal 'Locate:' label, but the rows use prose. Totals admits 0/1240 because the tree pins grammar 49e814eb and the rows use a41ba191. Empty cells make the mix preflight and the host job refuse.
4. No GCS-first persistence: the parent's tk_persist_exports/gcsput path is bypassed, outputs go to the project filesystem, and job.sh has no USR1 signal.
5. The bank gateway trusts the caller's catalog: MindCube items labelled dev-S1 are admitted, and a relabelled VSTI camera item skips the freeze. The selector refusal keys on caller-declared choices.
6. The old-selector training-response refusal keys only on the self-declared response_source label: rows with mask_source=deployed are admitted.
Fixes: the four-stream parity test only compares a copy with its source, so garbage files pass. The three sealed withheld bindings are untouched and the card never mentions the 80 rooms. The opener keep switch has no witness bound, so it first refuses at GPU load. e.py skips the ANON/commit checks. Job-visible words appear in kit records, in the extracted source and as STUDENT_* env vars. k/4.json is the parent's authorization.
Row mutations: 15 of 17 refused; the 2 old-selector rows were admitted. Statement mutations: 11 of 18 killed by the 32 tests runnable from the package.
Not confirmed: 136/136 tests (12 of 20 modules need builder-lane files missing from the package), coverage 4358/4370, and most B3_* proofs (not packaged).
No GPU, Orchard call, Git or deletion. Removal candidates are listed in REMOVAL_CANDIDATES.md in the lane folder.
