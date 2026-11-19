# NO-GO
The supplied kit must not consume the R0-dev comparison in its current form.
Reviewed archive SHA256: `f1dfce8d0f9e2c56aec9e1ebf05f5d1daa8a88ce5a836e370dbc86e4c29d9be1`.
Commands for every reproduced number: [COMMANDS.md](COMMANDS.md); input digests: [PROVENANCE.json](PROVENANCE.json).

1. **K1 numbers reproduce with the local mirror, not from the kit alone.**
`score_count_pricing.py --k1` reproduces 42.3/39.4/39.7/46.1/42.5 for truths 1/2/3/4/5+, with 254 large pairs.
`audit_cpu.py` reproduces constant 55.2362, identity oracle 80.5512, and ground-truth frame maximum 48.2353 (306 large pairs).
MISSING from `kit/work/`: `K1_PAIRS.json.gz`, `K1_LIFT.npz`, `K1_NMS.npz`, `K1_LMERGE.json`, `K1_LEARN_EST.json`; the full pilot table cannot be rerun.

2. **Selection and one-look requirements fail.**
The scorer chooses `best_const` from 5/6/7 on the 64 R0-dev large items, 29 dev-S1 large items, and pooled groups, then uses it in INFORMATIVE.
Spec §4 admits K1 held-out visibility during rule choice; the NMS-only candidate restriction has no training-only selection receipt.
Spec §2 uses R0-dev composite results to decide floor rows; §9 lets dev-S1 change the primary verdict. Neither executable enforces one look.
[SELECTION_AUDIT.md](SELECTION_AUDIT.md) lists every selection point, item set, and required change.

3. **CPU execution passes; official-MRA equivalence fails the available evidence.**
The self-test passes. The real manifest verifies 3,136 frame hashes, 98 captures, and 464 prompts; the full CPU stub completes with coverage 385/385.
The packaged two-capture fixture's 64 frames are MISSING; their exact first path and the full-stub replacement command are in COMMANDS.md.
`audit_cpu.py` finds 3 mismatches among 1,605 stored direct scores: prediction 11/truth 10 scores 0.8 instead of stored 0.9 in both R0-dev comparator arms; prediction 23/truth 20 scores 0.7 instead of 0.8 in R1_100.
MISSING: a pinned official scorer implementation and its source location. The self-test's agreement with its own formula does not establish correctness.

4. **Local inputs exist; runtime safeguards fail.**
Frames exist at `/scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp`; the builder verifies their supplied manifests.
Weights at `/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt` hash to `9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e`; all six source-receipt hashes match.
The documented b05 code, SAM environment, source tree, and K1 mirror exist on trinity-1-18; no dev-S1 frame root is supplied.
K1 completion receipts give 9,276.03 seconds/4,546 prompts: 2.0405 seconds/prompt, projecting 0.263 GPU-hours for 464 prompts. A 0.5-hour allowance is plausible, not a measured R0-dev runtime.
The launch text uses vnice and scratch data paths, but the vnice executable and GPU availability were not checked; this review used no GPU or network.
`--hours` checks only between captures and resets on resume. `audit_controls.py` proves exit 0/`shard_complete` with 98 invalid DONE markers and zero teacher files.

5. **Required edits before another review.**
- In `score_count_pricing.py`, use a pinned official metric; test all stored scores plus threshold boundaries, recompute affected references, and decide from unrounded values.
- In spec §§2/4/8/9 and the design gates, freeze all tunable rules, constants, thresholds, response/row choices, and the decision on K1 TRAINING; make dev-S1 diagnostic only.
- Add an atomic shared one-look ledger keyed by evaluation category, binding authorized item IDs and item/config/code/manifest hashes before exposing scores; reject repeated or changed reads across output directories.
- In builder/runner, enforce the pinned dev allowlist and resolved scratch paths; schema/set strings plus a caller-supplied hash do not exclude official items. Keep stub runs separate.
- In runner/scorer, validate DONE contents, teacher checksum, manifest/contract/settings hashes, full frame/category coverage, and non-stub provenance; reject stale or incomplete completion markers.
- Add an absolute launch deadline and cumulative budget accounting across resumes; retain vnice, set scratch caches and eight-thread CPU limits, and prohibit automatic relaunch after a kill.
- Package the missing pilot/fixture inputs and pinned scorer; record input hashes in score outputs and emit the category-error report that spec §7 requests but the scorer omits.
The claims that dev is “untouched,” all rules came from training alone, and the runner provides a hard stop lack adequate supporting files or code.
No official item file was read. All writes stayed inside this workspace.
