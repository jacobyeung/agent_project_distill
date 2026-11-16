The CPU suite passes **58 tests**, with 0 failures, 0 errors, and 0 skips. Both evaluator kits dry-bind the same **1,525 tasks**, with zero blocking canonical-label gaps and 150 unavailable released labels. `TESTS.log` lists the test names and results.

Run `/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/r2/test_adapter.py` from the lane. The tests use the copied evaluator kits in `work/r2/dry_release_cp1` and `work/r2/dry_release_f17`. All temporary fixtures remain under `work/r2`; no cleanup commands run.

The suite checks:

- The unchanged 2,136-item list, exact partition into 1,525 included and 611 excluded items, identical cell membership, and the 11 explicitly listed unlabeled rooms.
- Content agreement across different option orders; same-letter disagreements; case/whitespace normalization; unavailable released text; ambiguous or absent displayed answers; and released-label remapping through the actual kit scorer.
- The 1,375 primary and 150 unavailable strata, preserved questions/options/raw labels, numeric 10% boundaries, zero and nonfinite handling, and payload hashes.
- Hash ordering and sample sizes, per-type training agreement recomputed from saved option text, all 324 name changes, raw manifest counts, and upstream gate denominators checked against the census.
- Both dry binds, equal prompt hashes, all 11 scorer dispatches, model identities, exact anchor ordering, both-layout synthetic PNG loading, tamper/path/missing-frame rejection, and refusal to launch a dry binding.
- The three report views, null unavailable released scores, separate disagreement-label scores, and reproducible paired room-cluster bootstrap behavior.

The label audit separately checked all **64,515 MC admitted/packed pairs** for equal answers, options, source joins, and packed terminal answer tags. The final eligible pool contains 58,252 MC program rows. The deterministic sample contains 13,413 rows: 3,000 each for the three direction types and relative distance, plus all 1,413 relative-count rows. Relative size has no training rows. The original released source resolves every sampled label and all 889 ordinary dev MC labels.

`DRY_BIND_cp1m200.json` and `DRY_BIND_f17.json` export the bind receipts. Each binding pins its evaluator source, payload, adapter, and prompts; each stops before production PNG reads. The synthetic frame test writes 32 tiny RGB PNGs and loads actual kit receipts for spread and consecutive duplicates.

Production PNG verification, model weight authentication, GPU inference/parity, CP1 budget continuations, and an empirical paired report remain unexecuted. These CPU checks do not certify those run-host steps or establish semantic equivalence for renamed training objects.
