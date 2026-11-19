The production checker requires the configured prior, authenticates its offsets against native-row recomputation, and runs the unchanged production binding.

Real mode anchors the source databases to N’s launch config (`0e78d7f8`), including v7 `210b2534`, authenticates native twin augmentation, and verifies the complete patched tree, source archive, and preparation seal. Handover store hashes must match the native final stream identities.

All 58 regression checks pass: 9 CLI checks, 31 offset/identity checks, 8 tree/seal checks, 4 host-path checks, and 6 native-reader integration checks. TESTS.json records each command, result, and input hash.

All five prior2b checker tests pass. The reviewer’s exact unlabelled fixture fails with `REAL_LAUNCH_STORE_HASHES_MISMATCH:vqa`.

The reviewer’s re-pinned facing-side swap and non-target insertion fail with `PRODUCTION_PRIOR_OFFSETS_MISMATCH:cells`. Full CLI regressions also reject both; removing their fixture labels cannot grant a real PASS.

The labelled fixture still passes with identical plans, cell results, and audits across 31 cells and 288,000 draws. The enabled fixture proves that the checker uses its supplied offsets pin.

The patched tree pins are `35a4753f` (HOST24J base `189df6ac`) and `31c8f6b8` (N base `57a1f14d`). Both reproduce exactly with PATCH_PRIOR and zero fuzz.

The production proof remains **MISSING**. No real prepared population was supplied. HOST_INPUTS.json names the missing final receipts, native pointing/pose/routing databases, launch VQA receipt, augmentation, and source seal by path or native field; no production PASS is claimed.

The preparation receipt is `<proof root>/b/receipt.json`. Use `<root>/h/receipt.json` with the handover config, or `<root>/population/receipt.json` with entry.frame_host. HOST_INPUTS.json lists the fields checked for each.

Before native preparation, bind `r1_training.direction_prior` to the packaged weights. Native `bind_prepared` emits `r2_sampling.direction_prior`; the checker requires both fields.

Reproduce every reported test count and fixture statistic from this workspace:
```bash
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
nice -n 10 "$PY" scripts/test_checker.py
nice -n 10 "$PY" scripts/test_offsets.py
nice -n 10 "$PY" scripts/verify_trees.py
nice -n 10 "$PY" scripts/test_host_wrapper.py
nice -n 10 "$PY" scripts/test_integration.py
nice -n 10 "$PY" scripts/finalize.py
```
The scripts use fresh output paths; retain existing evidence and select a fresh workspace for a rerun. Their source fixtures come from the supplied sibling prior2b and priorrev directories.

Run this exact command on the training host after setting PY, PROOF_ROOT, BASE_TREE, PATCHED_TREE and a new CHECK_OUTPUT directory to their actual locations:
```bash
nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 "$PY" out/run_on_host.py --proof-root "$PROOF_ROOT" --stage b --base-tree "$BASE_TREE" --patched-tree "$PATCHED_TREE" --weights out/TOWARD_HARD_WEIGHTS.json --output-dir "$CHECK_OUTPUT"
```
The wrapper derives all four stream receipts and offset tables from the selected preparation and saves the expanded command and input hashes in HOST_COMMAND.json. Use `--stage h` or `--stage population` with those configs. The checker reads N_LAUNCH_CONFIG.json and TOWARD_HARD_WEIGHTS.json from this package.

The package is `out/fbp_prior2c.tar`; its digest is in `out/fbp_prior2c.tar.sha256`. `scripts/finalize.py` creates the archive, hashes every member, and verifies it against PACKAGE.json. ARCHIVE_CHECK.json records that result.
