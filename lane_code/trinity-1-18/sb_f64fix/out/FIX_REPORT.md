# sb_f64fix: fixes for review sb_f64rev (NO-GO)

The four code blockers are fixed and tested, and every reviewer counterexample now refuses (`out/review_replay.json`). The kit
is still not launchable: real inputs are MISSING (finding 3) and GPU memory is unmeasured until the pilot runs (finding 4). CPU only; paths are under `kit/`.

**1. `scripts/nest_store.py` dropped and renumbered rows; `nest_row` sorted reversed anchors.**
- Fix: `apply` preflights every source row and publishes all rows or none. A missing or stale frame pin
  (`FRAME_MISSING:<ordinal>`), an unpinned source frame or non-increasing anchors (`SOURCE_ANCHORS_NOT_INCREASING`)
  refuse the store. A post-write check confirms that source indices, targets, row count and anchor order survive.
- Tests: `tests/test_nest_store.py`, 6 pass. They cover the reviewer's empty-pins store (4 of 4 refused, no output file)
  and reversed anchors, plus absent and stale frames and a sparse-index store with an exact single-image row.

**2. `scripts/token_audit.py` granted `launch_ready` to empty, single-row and duplicated shards.**
- Fix: a shard header binds config, preparation, sampler (with `r2_sampling`), stores, horizon, limits, code, the
  whole plan and the shard's rows by sha256, and a footer hashes its records. `summarize` is ready only when one run's
  shards 0..n-1 each appear once, cover every planned row once over the full horizon with every field, and none fails.
- Tests: `tests/test_token_audit.py`, 16 pass, with a real encode of 16 planned dry-run rows. They cover the reviewer's
  empty shard, single pose row and duplicate pair, plus partial, missing, duplicate-index, mixed-run, missing-field,
  off-plan, tampered, short-horizon, wrong-config and unbound-preparation shards.

**3. Real inputs are MISSING.** None is fabricated, and `token_audit run` and `mem_pilot.py` refuse without them.
| Input | State | Owner |
|---|---|---|
| preparation receipt `/scratch/fsw/.../ap/8865619b/f/469ddece/receipt.json`, config `preparation` pin | MISSING; needs a new preparation over nested stores | lane tree_rebuild (W); its native prepare is NO-GO |
| `r2_sampling`; `r1_training.row_plan_sha256`, `host_receipt`, `review`; `store_hashes` for pose, routing, pointing | MISSING or null (only vqa bound); admit refuses `R1_ALL_STREAM_IDENTITIES_REQUIRED` | W's production binding, host audit, independent reviewer |
| code pin `.../8865619b/k/7.json`, admission pin `.../k/review.json` | MISSING; tree_f64 needs its own | orchestrator (sealed epoch contract), independent reviewer |
| depth-init `heads.json` (sha fd60ac2f…) | absent at its in-job path; a sha-matching copy is in W's `ext/preceipts` | P's kit x_ee227714, staged by W |
| reader `student_manifest`; 3,733 bisection PNGs | placeholder; not decoded | reader lane |

**4. Memory claims were estimates.**
- Fix: `F64_REPORT.md` and `DESIGN_F64.md` now say GPU memory is unmeasured. The 33.78 GiB/rank of sharded FP32 masters,
  gradients and Adam state is arithmetic, CPU RSS is not a GPU peak, the kit has no H100 logs, 48-GB cards are
  unsupported for the non-offloaded config, and the forward-coverage claim matches the evidence.
- New `scripts/mem_pilot.py` (not run) pilots 4 ranks on 80-GB cards with the trainer's FSDP, FP32 masters, AdamW state and
  LM checkpointing. It runs full 72-microstep cycles of the longest audited rows, then a checkpoint, and writes
  `PILOT.json`; it refuses cards under 79 GiB unless offload is on. `test_f64_fix` checks every trainer call it makes.

**5. `read/f64_read.training_layout` accepted a missing export `frame_input`.**
- Fix: export and config must declare equal `frame_input` values, which `check_spec` validates; with both absent the
  export reads as 32 frames. `student_row` also refuses anchors that are not strictly increasing or differ from the capture's.
- Tests: `tests/test_f64_fix.py`, 11 pass: absent, null and mismatched declarations on either side, invalid spec, reversed anchors.

**6. Install path was ambiguous.** Fix: the docstring, `READ_CONFIG_F64.json` (`install_as: src/b/f64_read.py`, plus the module sha256) and
the report say to install at `src/b/f64_read.py`, beside `e2e_reader`, as the patch's absolute imports require. Test: `test_f64_fix` resolves it from the installed root.

**Regression.** Both suites (`work/regress/`) give 109 tests and 1 error on tree_r1 and on tree_f64, as the review found; the error comes from the
MISSING `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`. The 12 layout tests and all 45 kit tests pass, from the workspace and the extracted tar.

**Deliverable.** `out/sb_f64fix.tar` (kit, run and replay scripts, result JSONs), sha256 `da6405ae0f0095414deecf3727a7aa88937686bfcbfa2dcf09e5aa8b1678a4bb` (`out/sb_f64fix.tar.sha256`).
