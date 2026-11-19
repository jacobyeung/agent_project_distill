> **SUPERSEDED.** This report describes the sb_rlfix kit (tower pose, `max_calls=200`, claimed arm MISSING, 34 tests, `sb_rlfix.tar`) and no longer matches this kit. The current report is `out/REPORT.md`; the current archive is `out/sb_rlfix3.tar`.

# RL review fixes: CPU validation passes; serving parity remains MISSING

The overlay is ready for review. Blocker 4 cannot be fully closed without the deployed claimed-arm table and evaluator adapter. Production training refuses those missing bindings.

| Finding | Final behavior and location |
|---|---|
| 1 | `rollout.native_kwargs` omits `trace_program_version`; the native signature binds; max_calls=200. |
| 2 | `reward.score` calls N's `evalpath.run.score_item`; the choice test uses a choice question type. |
| 3 | Auxiliary reward requires exactly one think-close; duplicate, case-varied, and malformed closes get zero auxiliary credit. |
| 4 | `rollout`, `serving`, and `train` require tower pose and preserve the G3T path. Own heads are diagnostic and cannot be scored. Claimed-arm verification is MISSING; MDG fallback is refused. |
| 5 | `sample`/`train` convert RowRefusal and tower errors to zero reward with no backward; every rank reduces zero-initialized gradients; adapters+optimizer save every 25 steps and at finish; rank logs retain refusal reasons/counts. |
| 6 | Wrong answers earn no short/route reward; training and CPU reward advantages disable std scaling. |
| 7 | Routing requires exact call kinds; distance requires ground+gap and two grounds before the gap. |
| 8 | Both original pool tests and new exclusion/REMOVE tests use production `pool.RoomGate`; the entire pinned R0 reserve is deliberately excluded. |
| 9 | `pool.clean_row` and `clean_inputs` allow-list fields, including nested frame inputs; labels remain outside model-visible rows. |
| 10 | CPU proof verifies native decoding, masks, reference replay, finite backward, and adapter update under the corrected reward. |
| 11 | `run_gpu_dry_run.sh`/`dry_run.py` supply two timed one-GPU steps with memory/refusal logs; NOT RUN. Rates in GPU_ESTIMATE are assumptions. |
| 12 | README and both reports state measured limits; HASHES.txt exists; Objective rejects non-sequence norm instead of ignoring it. |

`bash scripts/run_tests.sh` produced 34 passing tests (0 failures, 0 errors): the original 20 plus 14 new tests. Log: `out/TEST_RESULTS.log`.
The same command produced scorer parity on 74 review formats plus 36 additional formats: 0 mismatches (`out/PARITY.json`).
It checked K1-heldout 53, R0-dev 100, R0-rl 274, reserve 372, withheld aliases 720, dev-S1 2084, and BENCH 2424: zero admitted. All 233 train controls passed with 0 physical overlaps; 38013 REMOVE keys refused (`out/GATE_CHECK.json`, `out/REMOVE_CHECK.json`).
`bash scripts/run_cpu.sh --out out/CPU_PROOF.json` produced PASS: 143.875 s, 14.630 GiB peak RSS, gradient L1 4186.327728, adapter update L1 1.966013, ratio error 0.0227635; eight CPU threads, no GPU.
The random-model draws earned rewards [0, 0] and production advantages [0, 0]. A declared synthetic scalar pair [1, 0] yields [0.5, -0.5] only for the backward fixture. No answer-quality or learned-routing claim follows.
`PYTHONPATH=overlay python -B scripts/serving_check.py` produced `out/SERVING_CHECK.json`: generic N evaluation defaults to own pose and MDG; native SAM 3 selector support does not establish the required deployed arm.
MISSING: claimed-arm serving table at `configs/h100_{4,8}.json:grounding.serving_table.path` and deployed evaluator adapter at `grounding.evaluator_adapter.path`; neither source path was supplied. Their real settings, including G3T lifting and scale/gap math, remain unverified.
MISSING: admitted pool (`out/PROMPT_POOL.json`, status MISSING), qualified init_m544 evidence (`/scratch/jjyeung/orch_n30/sb_f64/pkg/work/n1fix2/inputs/registry.json`), and source/export/frozen-asset pins in configs. No mappings, scene lists, or production proof were fabricated.
`PYTHONPATH=overlay python -B scripts/make_configs.py` produces the unbound configs and GPU_ESTIMATE; its prompt length and throughput inputs are explicit assumptions, not measurements.
`PYTHONPATH=overlay python -B scripts/package.py` produces `out/sb_rlfix.tar`, `out/SHA256SUMS`, and `out/PACKAGE.json`; JSON receipts record input SHA256 hashes. Python commands used `/scratch/jjyeung/envs/p1cpu/bin/python`, nice 10, and OMP/MKL/OPENBLAS=8.
Distributed collectives use CPU mocks in tests because sockets and GPUs are unavailable. Real NCCL, production export reload, deployed grounding, and GPU memory/timing remain untested.
