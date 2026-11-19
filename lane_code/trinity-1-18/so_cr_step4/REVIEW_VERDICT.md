VERDICT: GO AFTER FIXES

Reviewer: independent, read-only, CPU only. Paths: `S=/scratch/jjyeung/orch_n30/so_step`, `T=S/work/b21_final/work/tree_r1` (patched build 21), `B=/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/tree_r1`, `L=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o`, `NOTE=S/out/NOTE_FOR_TREE_REBUILD.md`.

## Answer

- **First launch of vehicle N (01, 02 and fallback OFF; 03 ON allowed): GO now.** The four patches apply cleanly to build 21. All-OFF output is byte-identical to the base, and no switch-record field appears. The 31-test two-rank gloo gate passed on these bytes (`S/work/round3_b21_gloo_by_coordinator.txt:55-60`: `Ran 31 tests in 880.158s`, `OK`, `EXIT=0`).
- **First continuation with 01 ON: blocked until finding 1 is fixed.** As written, the bounded CPU audit refuses real production rows, so its acceptance gate can never pass. Fix finding 2 in the same round; fix finding 3 if the continuation uses alignment or pointing weights. Every failure mode found fails closed, so nothing here produces a silently wrong run.

## Findings

1. **HIGH: The audit's grid cap rejects portrait videos, so the CPU audit cannot pass on N's data.**
   - **Evidence:** `S/out/kit_timing/audit.py:33-34` caps each dimension separately at `(32,20,26)`. Production batches contain portrait grids `[32,26,20]`: steps 100, 101, 102 and 200 have 5, 7, 9 and 6 of them among their 72 rows (`L/look2.out:694,698,702,706`), in the VQA and routing streams.
   - **Reproduced:** `Coverage().observe({'video_grid_thw': [[32,20,26]]})` passes. `[[32,26,20]]` raises `Processor output exceeds audited grid cap [32,20,26]`.
   - **Consequence:** `data_only.py` observes every row, so both arms raise in the first update on every rank. No audit is produced, and `replay_compare.py` refuses without it, so 01 can never be enabled. The per-element `max_grid` would also report `[32,26,26]`, which is not an observed grid.
   - **Smallest fix:**
     - Accept `t <= 32 and h*w <= 20*26`, or equivalently `sorted((h,w)) <= (20,26)`.
     - Record the maximum grid by `t*h*w`.
     - Add a test that accepts `[32,26,20]` and rejects `[33,20,26]` and `[32,22,26]`.
     - Update the cap's wording at `NOTE:83` and `data_only.py:141`.

2. **MEDIUM: Replay rule 2 almost never passes, so "OFF nondeterminism is not an automatic refusal" is false in practice.**
   - **Evidence:** `S/out/kit_timing/replay_compare.py:19-21` requires `|ON−OFF1| ≤ |OFF1−OFF2|` and `|ON−OFF2| ≤ |OFF1−OFF2|` for every scalar (`NOTE:131-133`). Together these hold exactly when ON lies between OFF1 and OFF2. With three exchangeable runs, that probability is 1/3 per scalar.
   - **Scale:** The rule covers every component, stream mean and microstep loss on 4 ranks. The pass probability is at most (1/3)^4 ≈ 1.2% even if all scalars on a rank move together, and near zero if they move independently.
   - **Consequence:** A correct ON leg is almost always rejected whenever OFF is not bitwise. `NOTE:139` says the opposite. This fails closed, but the previous review's finding 2 asked for a rule that remains usable under nondeterminism, so it is only partly fixed.
   - **Smallest fix:** Either:
     - state that only the bitwise branch is a practical pass and 01 stays OFF after OFF nondeterminism, or
     - pre-register a pooled per-rank bound, e.g. `max_i|ON_i−OFF1_i| ≤ k·max_i|OFF2_i−OFF1_i|` (and the same against OFF2) with `k` fixed in advance, such as 2. Add a test where ON falls just outside [min, max] but inside the bound.

3. **LOW: The audit encodes rows from the raw preparation receipt, but the trainer uses the merged final-mode receipt.**
   - **Evidence:** `data_only.py:57,73` (and `write_plan.py:31`) call `run.load(args.receipt)`. In final mode the trainer merges config levers into that receipt at `T/student_pilot/carrier_c1_run.py:712-720`: `align`, `pointing_weights`, camera overrides and others. The raw receipt written at `:626-637` never contains `align` or `pointing_weights`.
   - **Consequence for `align`:** `descriptor_for` (`data_only.py:19-20`) refuses any config with `align` set, so the previous finding 14 fix fails closed instead of auditing.
   - **Consequence for `pointing_weights`:** Run A's config sets them (`L/look2.out:482-483`). `Rows` adds `aux_token_weights` only from the receipt (`carrier_c1_run.py:1076,1170-1174`), so audited pointing rows skip that encoding path. This includes the worker's per-token `tokenizer.decode`.
   - **Smallest fix:** Build the audit receipt once with `run.prepared(cfg)`, or apply the same final-mode merge, and write it to `AUDIT_DIR` for both scripts. Then drop the equality check in `descriptor_for`.

4. **LOW: The continuation's kill rule has no numeric thresholds.** `NOTE:143-157` names the fields to compare but sets no wall-time threshold. It also does not say which rule the continuation's first update must meet against `off1`/`off2`.
   - **Smallest fix:**
     - Losses: the record at `start_step+1` (`components`, `stream_means`) must meet the replay's acceptance rule against `off1`/`off2`, or else 01 goes OFF at the next checkpoint.
     - Wall time: fix a rule in advance, for example "slowest-rank median `wall_seconds` over updates 2–21 below the first launch's last-20 median, else 01 OFF".

5. **INFO: Status is stale again (previous finding 9).** `S/out/REPORT.md:181` and `S/out/ARTIFACTS.json:14` still say the 31-test gate needs lane execution, and `NOTE:168-173` cites only round-2 results. **Fix:** cite the coordinator's 31-test pass at 12:55:19 UTC.

6. **INFO: Two variables in the replay command are underspecified.**
   - `NOTE:113` uses `$REPLAY_OUT` without defining it. It fails closed through `replay.sh:10`.
   - `NOTE:114` takes `REPLAY_METRICS` from whatever `C1_BATCH_METRICS` the shell holds.
   - **Fix:** define `REPLAY_OUT`, and set `REPLAY_METRICS` explicitly to the continuation's 03 value.

7. **INFO: The fallback key appears only when fallback is ON.** With 01 ON and fallback OFF, `ranks[r].performance` has only the three base keys (`c1_switches.record`). **Fix:** state in `NOTE:150` that r1_ops must not require `C1_CPU_PREFETCH_FALLBACK`.

8. **INFO: The replay runtime's lower bound is below the measured floor.**
   - **Evidence:** In the supplied log, trainer launch was at 05:12:13Z (`L/look1.out:361`) and `attempt_171377.json` was written at 05:20:53 (`look1.out:5`): 8.7 min of startup. The first update then took about 440 s (`inputs/` at 05:28:14, `look1.out:8`). The earlier 02:44–05:10 gap was the preparation stage (`look1.out:346-360`), not the trainer.
   - **Estimate:** Each leg needs at least about 16 min plus checkpoint restore, so three legs take at least about 48 min. `NOTE:121` says 30–60 min.
   - **Fix:** say about 50–75 min. The 3,600-s cap per leg keeps more than 3× margin.

9. **INFO: The audit sidecar is written before validation.**
   - **Evidence:** `data_only.py:135` writes `<out>.manifest.json` before `coverage.require`, `compare_rows` and the budget check (`:147-151`). `replay_compare.py` re-checks everything except two things: that augmentation ran on the prefetch-worker thread, and that `grid_rows > 0`.
   - **Consequence:** A leftover sidecar from a failed ON audit would pass those two checks.
   - **Fix:** write the sidecar after the checks pass, or re-check both fields in `replay_compare.py`.

10. **INFO: No test mixes fallback and non-fallback groups on one rank.** In `T/tests/test_so_round3.py`, each rank either falls back on every group (cap=1) or on none. The code path is simple (`c1_cpu_prefetch.py:130-159`). **Fix:** add one test with a cap between two group sizes.

## Checks

1. **OFF byte-identical: pass.**
   - I re-applied the four diffs to `B` in memory: zero offset and zero fuzz. The 22 touched files match the manifest's output sha256 and `T`, the 927 untouched files are identical, and the input hashes match.
   - A cross-tree all-OFF run produced identical step records and parameters, with no `performance` or `cpu_prefetch` key.
   - When all switches are `'0'`, `record()` returns `{}` and the startup broadcast carries no third element (`carrier_c1_run.py:2909-2936`).
2. **ON semantics unchanged by round 3: pass.**
   - These ON combinations gave the same record hash and parameters once `performance` and `cpu_prefetch` are excluded: 01+03, 03 alone, and 01 plus fallback with no group falling back.
   - With fallback at cap=1, output is bitwise OFF (`test_so_round3`). The coordinator gate includes the two-rank asymmetric-fallback proof (`SO_FALLBACK_PROOF`).
   - On fallback, `prepare` returns `None` and the group goes through the unchanged main-thread fetch and admission (`c1_cpu_prefetch.py:53-69,130-159`).
3. **Kits executable as written: fail for the audit (finding 1); the replay runs, but rule 2 is weak (finding 2).**
   - The plan writer mirrors the sampler call in `run_steps` (`carrier_c1_run.py:2422-2424`).
   - The r1_ops fields in `NOTE:150-155` match the record (`carrier_c1_run.py:1728-1735,2501-2509`), apart from finding 7.
   - Runtimes are labelled as estimates; see finding 8.
4. **Earlier findings: mostly fixed, each with a test that failed before.** Failing-before evidence is in `S/out/evidence/round3_trainer_before.txt` (5 tests: failures=1, errors=4), `round3_kits_before.txt` (6 errors) and `round3_plan_cli_before.txt` (1 failure).

   | Previous # | Disposition |
   |---|---|
   | 1 | Partly fixed. The plan writer and fallback switch are tested, but the audit cannot pass (finding 1). |
   | 2 | Partly fixed. The replay command, OFF/OFF/ON order and comparator are tested, but rule 2 is weak (finding 2). |
   | 3, 4 | Fixed and tested (`performance` record; real `train()` startup). |
   | 5, 6, 7, 8 | Fixed in REPORT and NOTE; documentation only. |
   | 9 | Stale again (finding 5). |
   | 10, 11, 12, 13, 15 | Fixed (GX tests in the gate, peak RSS, clip-mix refusal, worker-augmentation coverage, docstring). |
   | 14 | Ineffective (finding 3). |

5. **Gain estimates: honest.**
   - 03 is about 0 (≤0.1 s).
   - 02 is ≤0 at low reuse.
   - 01 is 0–28.2 s and possibly negative under host/GIL contention.
   - Audit and replay runtimes are labelled as estimates.

## Reruns by this review

All runs used `nice -n 10`, 8 threads, `CUDA_VISIBLE_DEVICES=""` and `PYTHONDONTWRITEBYTECODE=1`.

- `tests.test_so_round3`: 6 OK in 17.4 s.
- `test_round3_kits`: 7 OK.
- `test_round3_plan_cli`: 1 OK.
- `ARTIFACTS.json`: 145 hashes OK.
- In-memory patch replay and the cross-tree OFF/ON parity runs (checks 1 and 2).
- Grid-cap repro (finding 1).

Side effects: temporary `c1_*`/`so_*` directories under `S/work/test_runs/` only. No bytecode was written into the trees or kits.
