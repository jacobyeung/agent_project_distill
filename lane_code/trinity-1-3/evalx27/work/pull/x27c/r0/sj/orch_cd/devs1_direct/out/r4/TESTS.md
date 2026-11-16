All 11 CPU tests pass. `TESTS.log` records the run; `test_r4.py` repeats the checks without reading model weights or production PNGs.

| Check | Result | Evidence |
|---|---|---|
| Membership and strata | 150 rows per family; 50 easy, 50 medium, 50 hard; 40 captures and 33 rooms, all held out. All 152 frame-manifest captures are held out. | `COUNTS.json`, both `STRATA.jsonl` files |
| Away byte identity | Complete ITEMS, ROWS, CELL_ITEMS and EXCLUDED files match the source bytes. Every task field except timing and stratum metadata matches its original JSON value-token bytes. | `BYTE_IDENTITY.json` |
| Forward twins | 150 unique dev source rows; exact stored question/options/answer; source-line hashes, GT authority and paired capture/frame metadata agree. GT letters are compared by content in their own option orders. | `FORWARD_SOURCE_PROOF.json`, `PAIRS.jsonl` |
| Timing | Both complete manifests equal pass 3. All source indices, fps, totals, lower-bound flags and timestamps validate. Every new JSON/JSONL file is scanned for fps placeholders. | `DEV_BACKDIR/FRAMES.json`, `DEV_FORWARD_TWINS/FRAMES.json` |
| Baselines | All away letter/content counts, constant accuracies and back-family counts equal back_dir’s manifest. Forward controls are recomputed separately. | `COUNTS.json` |
| Dry binds | Six successful dry binds: two main cells and four new cells. New cells each contain 150 tasks, zero missing GT labels and 150 unused/unavailable released labels. | `DRY_BINDS.json` |
| Reviewed evaluators | Every copied evaluator Python/JSON file and source archive matches its reviewed kit; no evaluator is edited. | `DRY_BINDS.json`, each bind’s `kit/CODE_PINS.json` |
| New prompts and receipts | 600 fresh prompt/receipt reconstructions match all four new dry binds. The two checkpoints’ prompt inventories match within each family. CP1 expands to 64 frames; f17 retains 32. | `SCORER_CHECKS.json`, dry-bind receipts |
| Exact-option scoring | 2,400 cases run through the actual reviewed scorers: correct option, wrong option, closed thought at cap, unclosed thought at cap. | `SCORER_CHECKS.json` |
| CP1 budget contract | Both new CP1 cells pass reviewed THINK settings; B2048/B4096 constants, worker derivation and budget-merger dispatch match the main cells. | Unchanged `budget.py`, `worker.py`, `budget_merge.py` |
| Refusal cases | Altered fps, indices, timestamps, totals, lower-bound flag, held-out membership, answer mapping, released labels and protocol settings are rejected, including task tampering with recomputed file pins. Dry binds cannot launch. | `TESTS.log` |

The pass-3 comparison covers every file in `work/r3/final_cp1` and `final_f17`. `PASS3_COMPATIBILITY.json` records original, new and normalized SHA256 values. All files except `request.json` and `RECEIPT_TEMPLATES.json` match literally. Those two contain absolute destination paths: replacing only the new destination with the original and recomputing the covered request binding yields byte-identical files. The adapter hash remains the original pass-3 hash because the new entrypoint delegates main-cell binding to that pinned code. The comparison does not remove fields or normalize model, task, prompt, code or timing content. The two normalized artifacts per model are retained in `work/r4/compat_cp1m200` and `compat_f17`.

CPU checks establish payload, prompt, timing and scorer contracts. Production PNG verification, model authentication, processor parity, inference and actual budget continuations remain run-host checks. No empirical model score or budget journal was generated here.

Repeat the checks from this lane:

```bash
cd /scratch/jjyeung/orch_cd/devs1_direct/out/r4
sha256sum -c SHA256SUMS
/scratch/jjyeung/envs/p1cpu/bin/python -I -s test_r4.py
```

Tests retain their small tamper fixtures under `work/r4`. They recompute the deterministic proof JSON files. To recreate dry binds, use the operator commands with fresh destinations; existing destinations are refused.
