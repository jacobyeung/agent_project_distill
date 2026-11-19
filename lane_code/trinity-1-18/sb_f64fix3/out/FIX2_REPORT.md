# sb_f64fix2: pilot-gate fix for review sb_f64rev2 (GO AFTER FIXES)

The required code fix is in place. `kit/scripts/mem_pilot.py:check_audit` refuses an audit with any `check_row` failure or ceiling violation and still accepts tripwire-only rows; four new tests and the reviewer's matrix confirm it. Launch stays blocked on OPEN items 3, 4, 7 and 8 below. The work ran on CPU only, and paths are relative to this workspace.

**Fix (`kit/scripts/mem_pilot.py:58-86`; docstring lines 19-20).** After the existing coverage check, `check_audit` reads the complete per-stream counts that `token_audit.summarize` re-derives from the shard files, not the 200-row `flagged` list. It refuses when the counts do not sum to the planned rows, or when any stream has a failed or over-ceiling row. It also refuses when a stream's longest-row list omits an audited row: the list must hold min(rows, 256) entries and start at the stream's maximum over all rows, failed rows included. The error names each refused stream with its counts. Rows over the tripwire alone pass and feed the longest-row plan.

**Tests.** New `kit/tests/test_pilot_gate.py` runs 4 tests over real encodes of the 16 dry-run rows. A passing audit is accepted with all 16 rows in the plan. A tripwire-only audit (8 rows over 9,200 tokens) is accepted with `launch_ready=false`. A failed row refuses, in two cases: a routing `check_row` failure and a pose fetch failure, each of which the longest list omits. A ceiling violation refuses, in two cases: a vqa row encoded under a 9,000-token ceiling and a flag-only pointing row. Against the unfixed `mem_pilot.py`, all four refusal subtests fail (`out/test_pilot_gate_old_mem_pilot.log`).

**Reviewer matrix rerun** (`work/review2/pilot_gate_matrix.py` writes `out/pilot_gate_matrix.json`). It uses the reviewer's retained fixtures, checked by sha256, with the three reviewer cases unchanged and a ceiling case added.
| Case | Required | Reviewed code | This code |
|---|---|---|---|
| passing | accept | accept | accept |
| tripwire_only (8 rows) | accept | accept | accept |
| failed_check (routing 0) | refuse | accept | refuse: routing failed 1, omitted from longest 1 |
| ceiling_violation (vqa, added) | refuse | not run | refuse: vqa over_ceiling 1 |

`token_audit.summarize` still gives `launch_ready=true` to the flag-only ceiling row, because it ignores `over_ceiling` when `check_row` is ok. A real audit cannot write that record, since `check_row` raises above the same ceiling. `token_audit.py` is out of this task's scope and unchanged.

**Reruns.** All 49 kit tests (the 45 plus the 4 new) pass in the workspace (`out/kit_tests.log`) and from the extracted tar (`out/extract_tests.log`). Both regressions run 109 tests with 0 failures and the same single error, the MISSING `POOL.jsonl` (`out/{baseline,patched}_regression.json`). The earlier review's seven counterexamples still refuse (`out/review_replay.json`).

**OPEN items.** Each path below is still absent on trinity-1-18. Paths and owners come from `/scratch/jjyeung/orch_n30/sb_f64rev3/out/static_review.json` (`missing_inputs`) and `/scratch/jjyeung/orch_n30/sb_f64rev3/out/OPEN_ITEMS.md`; none is invented, and an unknown one reads "MISSING: orchestrator assigns". The two config files sit in `/scratch/jjyeung/orch_n30/sb_f64fix3/kit` and are byte-identical to the reviewed sb_f64fix2 copies (`configs/r1_config_f64.json` sha256 `cc811f9ad166cba19f8a3540ef9577a7379c8fc7c7cd972735a152434d884072`, `read/READ_CONFIG_F64.json` sha256 `7bfe2d0214a6efe33667e54aff88e4485c2c1fcd5ddb3dc7de0661f5a2a3d6e7`).
| Item | Exact path | Owner |
|---|---|---|
| 3 first batches: preparation receipt | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json` | lane tree_rebuild (W) |
| 3: code pin | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/7.json` | orchestrator |
| 3: admission pin | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/review.json` | independent reviewer |
| 3: depth init | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/97a6a3eb/runs/b19c1200/train/step_400/heads.json` | lane P's kit x_ee227714, staged by lane tree_rebuild (W) |
| 3: config bindings (absent or null) | `/scratch/jjyeung/orch_n30/sb_f64fix3/kit/configs/r1_config_f64.json` keys `r2_sampling`, `preparation`, `r1_training.store_hashes.pose`, `r1_training.store_hashes.routing` and `r1_training.store_hashes.pointing` (absent), and `r1_training.row_plan_sha256`, `r1_training.host_receipt` and `r1_training.review` (null) | lane tree_rebuild (W) binds the production values; the host audit and one independent review then check them |
| 3: reader manifest | `/scratch/jjyeung/orch_n30/sb_f64fix3/kit/read/READ_CONFIG_F64.json` key `settings_add.student_manifest` (placeholder) | reader lane |
| 4 GPU pilot (also needed for 8) | Output directory: MISSING: orchestrator assigns. `/scratch/jjyeung/orch_n30/sb_f64fix3/kit/scripts/mem_pilot.py --out DIR` writes `DIR/PILOT.json`. The gate is fixed here; the pilot is unmeasured, and `mem_pilot.py` refuses (`R1_ALL_STREAM_IDENTITIES_REQUIRED`) until item 3 binds | Allocation: the orchestrator authorizes four 80-GB GPUs. Operator: MISSING: orchestrator assigns |
| 7 baseline pool | `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`. trinity-1-18 has no `/scratch/jjyeung/orch_cd/derivgen`, and the host that holds it is unreachable from this lane | Producer: MISSING: orchestrator assigns |
| 8 closure: gate review | `/scratch/jjyeung/orch_n30/sb_f64rev3/out/REVIEW_VERDICT.md` reviewed this gate (GO AFTER FIXES); the fixes it requires sit in sb_f64fix3 | independent reviewer, assigned by the orchestrator |
| 8: actual all-rank CPU first batches | Evidence output path: MISSING: orchestrator assigns | Production binding: lane tree_rebuild (W). Operator: MISSING: orchestrator assigns |
| 8: complete full-horizon token audit | Shard and summary output paths: MISSING: orchestrator assigns. `/scratch/jjyeung/orch_n30/sb_f64fix3/kit/scripts/token_audit.py run --out SHARD` and `summarize --out SUMMARY` take them | Operator: MISSING: orchestrator assigns |
| 8: reader memory evidence | Evidence output path: MISSING: orchestrator assigns | reader lane |

**Deliverable.** `out/sb_f64fix2.tar` holds the kit, the run and review scripts, and the result JSONs and logs. Its sha256 is `472d7775378a82ee365f11aa531f25b065129e339be1a3157abe1b85d24c6f89` (`out/sb_f64fix2.tar.sha256`). Relative to sb_f64fix, the kit changes only `scripts/mem_pilot.py`, the new `tests/test_pilot_gate.py` and `SHA256SUMS`. `work/scripts/run_fix.sh` and `work/regress/run_regress.sh` now point at this workspace, and nothing else changed.
