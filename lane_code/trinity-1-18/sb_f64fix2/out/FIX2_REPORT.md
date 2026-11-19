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

**OPEN items.** Paths and owners come from `static_review.json:missing_inputs`; each path is still absent on trinity-1-18. `P` = `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap`. `CFG` = `kit/configs/r1_config_f64.json`, byte-identical to the reviewed copy (sha256 `cc811f9a…`).
| Item | Exact missing path | Owner |
|---|---|---|
| 3 first batches | `P/8865619b/f/469ddece/receipt.json` (preparation) | tree_rebuild (W) |
| 3 | `P/8865619b/k/7.json` (code pin) | orchestrator |
| 3 | `P/8865619b/k/review.json` (admission pin) | independent reviewer |
| 3 | `P/97a6a3eb/runs/b19c1200/train/step_400/heads.json` (depth init) | P x_ee227714, staged by W |
| 3 | `CFG:r2_sampling`, `CFG:preparation`, `CFG:r1_training.{row_plan_sha256,host_receipt,review}`, `CFG:r1_training.store_hashes.{pose,routing,pointing}` (all null) | W production binding; host audit; independent review |
| 3 | `kit/read/READ_CONFIG_F64.json:settings_add.student_manifest` (placeholder) | reader lane |
| 4 GPU pilot | The gate is fixed here. No `missing_inputs` entry exists; `PILOT.json` is unmeasured, and `mem_pilot.py` refuses (`R1_ALL_STREAM_IDENTITIES_REQUIRED`) until item 3 binds | orchestrator authorizes 4×80 GB; item 3 owners |
| 7 baseline | `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`. It is absent on trinity-1-18, which has no `derivgen/` under `orch_cd`, and the host that holds it is unreachable from this lane | derivgen/review-pool owner, not named in the kit; the orchestrator routes it |
| 8 closure | The builder part is done here and needs one independent review of this gate change. The rest needs every item 3 and 7 input, actual all-rank CPU first batches, the complete full-horizon token audit, the authorized four-rank pilot, and the reader manifest with memory evidence | production owners above; reader lane |

**Deliverable.** `out/sb_f64fix2.tar` holds the kit, the run and review scripts, and the result JSONs and logs. Its sha256 is `472d7775378a82ee365f11aa531f25b065129e339be1a3157abe1b85d24c6f89` (`out/sb_f64fix2.tar.sha256`). Relative to sb_f64fix, the kit changes only `scripts/mem_pilot.py`, the new `tests/test_pilot_gate.py` and `SHA256SUMS`. `work/scripts/run_fix.sh` and `work/regress/run_regress.sh` now point at this workspace, and nothing else changed.
