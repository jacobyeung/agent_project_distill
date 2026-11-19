VERDICT: GO AFTER FIXES

Scope: every file in `so_read/out/` and `so_read/work/src/u0/`, plus the originals they overlay in the A4 patch base. MANIFEST hashes match the workspace bytes. I ran the non-writing CPU tests with `nice -n 10`, 8 threads, no GPU and `-I -s -B`. I also ran the round-1 F1, F4 and F7 checks against both the pre-fix and the post-fix code. I did not run the suites that write files (`test_read_journal`, `test_off`, `test_public`, `test_compare`, round-1 F2), to honour "write nothing else". GPU parity and persistent-storage requeue remain unrun, as the report says.

## Round-1 findings: disposition

| Round 1 | Fix | Regression test |
|---|---|---|
| 1 Key collisions | Correct and complete. `digest` is typed and length-prefixed (`u0/a0.py:31-83`). | Behavioural. I verified it fails before and passes after (`tests/test_round1.py:35`). |
| 2 Vacuous parity | Correct. It requires 50 unique equal ids, validates traces including scale, calls and served responses, and requires positive hits for every enabled cache (`compare.py`/`a10.py`). | Fails before by inspection, since the old comparator passed empty traces. It is weak: it accepts any `ValueError` (`test_round1.py:44`). |
| 3 OFF not preserved | Correct by construction. The change is additive under `src/u0`, and the originals are byte-unchanged. `reader_sha256`, `code_hash` and `parity_code_sha256` do not cover `u0`. `build.py` does not pack it. | Structural only (`test_round1.py:57`). It fails before by inspection. |
| 4 Model identity | Correct. Vision and SAM keys bind live id, `data_ptr`, version and full content, plus execution state, and SAM bypasses on hooks (`a0.py:302-332`, `a3.py:208-228`). | Behavioural. I verified it fails before and passes after (`test_round1.py:64`). |
| 5 Recovery outside lock | Correct for atomic mode. `writer_guard` recovers under `writer.lock` and only with a matching binding (`a4.py:145-170`). | Textual only: it checks that the handler contains no `.recover()` (`test_round1.py:76-79`). A behavioural lock test exists in `test_read_journal`; I did not run it. |
| 6 Opacity | Partly fixed. Config, IDs and logs are tokenized. Findings 2 and 3 cover the gaps. | A path regex only (`test_round1.py:81`). It does not exercise the real Orchard surface. |
| 7 Memory bound | Correct. The reserve includes overhead, and the cache evicts before the snapshot and admits only `2*reserve` (`a0.py:206-261`). | Behavioural. I verified it fails before and passes after (`test_round1.py:88,94`). |

## Findings

1. **HIGH: the documented ON entrypoint fails under `-I`.** `a8.main` adds `src`, `src/tree` and `src/b` to `sys.path`, but not `u0` (`a8.py:54`). Under `-I` the script directory is not on `sys.path`. As a result, `a4.py:247` (`from a8 import source_hash`) raises `ModuleNotFoundError: a8`, and with `--opaque`, `a8.py:56` raises `ModuleNotFoundError: a9`. I reproduced both. REPORT:60, NOTE:25 and README:3 all document `u0/a8.py --enable-extensions`, and the production runner launches with `-B -I`. The kit (`run.py:41`) and the array template (`template:26`) insert `u0` themselves, so no test noticed. **Fix:** `sys.path[:0]=[str(ROOT), str(source), ...]` in `a8.main`, plus a subprocess `-I` test of `a8.py --enable-extensions` with and without `--opaque`.

2. **MEDIUM: the opaque path grammar rejects every established Orchard layout.** `OPAQUE_PATH` (`a9.py:12`) allows only `/scratch|/project` followed by `u<hex>` segments. Production stages under `/scratch/jjyeung/<token>` and `/project/community/jjyeung/okh7/a15_cot_ap<token>` (`8.py:45`, `common.py:22`). Three call sites enforce the grammar:
   - `validate_paths`/`seal_settings`, which every kit arm calls (`a9.py:36-50`, `run.py:63`).
   - `validate_config`, which the array calls (`a9.py:148-155`, `a7.py:17`).
   - The output check at `run.py:127`.

   So the kit and the array cannot run on real staged assets unless top-level `/scratch/u…` and `/project/u…` directories exist and are writable on Orchard, which is unverified. **Fix:** accept an approved prefix list followed by opaque segments, and screen words with `orchard_h10.common.opaque` (FORBIDDEN, `common.py:18-21`).

3. **MEDIUM: the array template departs from the approved Orchard submit surface.** The template (`array_preempt.template.sh:3-13`) differs from `submit_argv` (`common.py:71-82`) in six ways:
   - The job name is `u0`, not `a15_cot_ap<token>`.
   - There is no `--account=mt01` and no `--export=NONE`.
   - Logs go to `/project/u0/u1/...` instead of `/dev/null`.
   - It uses `preempt` with `--requeue` and a 2-day limit at `--array=0-3%4`, up to 192 GPU-h. `submit_argv` caps an allocation at 5 GPU-h (`common.py:74-75`).
   - The stored batch script contains `from h1eval.h10.array_worker import main` (`template:30`); `h1` and `h10` are FORBIDDEN words.
   - Exit 75 (`a7.py:55,59`) and the catch-all exit 2 (`template:35-37`) end the task FAILED; `--requeue` covers only preemption and node failure.

   **Fix:** generate the array argv through a `submit_argv`-style function, run `opaque()` on the argv and the script text, put the import in a neutral staged file, and have the owner approve the partition and GPU-hour policy.

4. **MEDIUM: no production integration yet (acknowledged at REPORT:396).** `orchard_h10/build.py:31-54` packs no `u0`. `entry.py:22` calls the original `h1eval.h10.launch.main`. `runner.summarize` (`runner.py:97-111`) assumes modulo shards. `merge_read` (`a6.py`) emits a new canonical `answer_trace_return.tgz`, not the existing return envelope. Adoption therefore needs build, pin, runner and return work that is not in this package. **Fix:** add `u0` to the build folders and payload pins, route `entry` through `a8` when ON, and teach `runner` about scene shards and the merge artifact, before step 600.

5. **MEDIUM: the ON caches probably cost more than they save at default settings.** This is an estimate; no GPU measurement exists.
   - `module_identity` streams a full content hash of every vision-tower parameter and buffer on every vision call (`a0.py:319-321`), and the same applies to SAM3 on every detect (`a3.py:223`). That is gigabytes per call.
   - `Sam3Tower.encode` keeps the `backbone_fpn` and `vision_pos_enc` pyramids of each frame on CPU (`tree/student_pilot/sam3_tower.py:213-218`). At 1008 px that is roughly 110–170 MB per frame.
   - Admission requires `BOOKKEEPING+held+2*reserve ≤ cap` (`a0.py:207-213,252`), so at 4 GiB a payload above about 2 GiB, i.e. a clip of about 13 or more frames, is never cached.
   - `compare` requires hits in both SAM namespaces, so a SAM-ON kit run at the default cap should fail with `no_hits`. That is fail-closed, not unsafe.

   **Fix:** hash weights once at install and re-hash only when the `(id, data_ptr, _version)` tuple changes. For SAM, set `read_cache_bytes` to at least 12 GiB, or drop `sam_features`. Measure before crediting any speedup.

6. **LOW: extension-mode non-atomic deadline loses progress telemetry.** `writer_guard` updates SUMMARY and progress only in atomic mode. Otherwise it reports `completed=0, initialized=False` (`a4.py:145-170`, `420-425`), whereas the original counted rows (`launch.py:354-361`). No Orchard consumer reads these files, since `runner.py:173` writes its own SUMMARY. **Fix:** do the original read-only count under the lock.

7. **LOW: the array lock fails fast on shared storage.** `flock(LOCK_EX|LOCK_NB)` (`a7.py:44`) raises `BlockingIOError` if a stale NFS lock survives node loss. The task then exits 2 and does not requeue. **Fix:** bounded wait with backoff, then exit 75 and requeue.

8. **LOW: processor-cache bypasses leave no trace.** When key construction raises `TypeError`, the call returns fresh output and records no stat (`a0.py:278-279`). The kit catches this through its no-hit rule; production telemetry would not. **Fix:** count bypasses in `stats['processor']`.

9. **LOW: the kit trusts its roots.** `run.py:37` does not assert that `original_source_root != source_root`, or that `source_root/u0` matches MANIFEST. If both roots point at the patched tree, the ORIGINAL-versus-OFF check is vacuous; ON still fails if `u0` is absent. **Fix:** two assertions before any arm starts.

10. **LOW: regression tests are weaker than the fixes.** F2 accepts any `ValueError`, F5 is a textual check, and F3 and F6 are structural. **Fix:** assert specific messages and reasons, and run the behavioural lock test in the round-1 suite.

11. **INFO: check (1), default OFF.** It holds. No original file changed, ordinary imports never load `u0`, and the hash trees exclude it. Settings parsing and the timing fields of the ordinary entrypoint are unchanged. Cache keys in the settings without `a8` are silently ignored, as README:3 states. The kit installs the PublicJSON wire on every arm (`run.py:72`), so its OFF bytes are transport bytes; `test_off` covers the real serialization.

12. **INFO: check (2), keys and safety.**
    - Processor keys cover the frame arrays (`batches.py:80`), the `VideoMetadata` dataclass, the kwargs, the config, the method ids and the execution state.
    - Vision and SAM keys cover the full live weight content, dtype, autocast, determinism, TF32 and SDP flags, and hooks.
    - Snapshot and restore copy values, so mutation is safe, and the cache resets on a PID change.
    - No KV, recurrent state, own-depth scale, question text or tool response is cached. SAM detections are a pure function of clip, name and contract.

13. **INFO: check (3), journal and shards.** The design is sound:
    - Commits go through temp, fsync, replace and a directory fsync into `committed/`, and `items.jsonl` is rebuilt from that store.
    - Resume skips committed ids, so nothing is duplicated or skipped.
    - Scene shards assign whole rooms, so shards are disjoint.
    - The merge checks binding, arms, modes, shard identity and count, membership, duplicates, missing and extra ids, and emits canonical bytes equal to the single-shard output.

    Real persistent-storage requeue is unproven.

14. **INFO: check (4), parity kit.** It compares what it claims and is non-vacuous, apart from findings 5 and 9. It runs the ORIGINAL, OFF, OFF_REPEAT and ON arms in fresh `-I` processes. It requires 50 ids, a fixed sample hash and per-cache hits, and excludes only clock and telemetry fields (`seconds`, `timings`, `audit`, `perception_memo`, `read_cache`, `read_profile`).

15. **INFO: check (5), forecast.** `580 × 23.599762 / N + 75.446133 + 49.761372` gives 13813.069 s (3 h 50 min), 6969.138 s (1 h 56 min) and 3547.173 s (59 min). The inputs match the A4 journals. The figures assume caches OFF and item-count-balanced shards, so the largest scene shard sets the wall time.

16. **INFO: check (6), names.** The kit filenames, config examples and logs (via PublicLog) are neutral. Remaining leaks are covered by findings 2 and 3. In addition, the in-process environment variable `H10_SETTINGS` (`run.py:39`) is visible through `/proc`; rename it to a neutral name.

**Release order:** fix 1, then 2 and 3, then 4. Then run the GPU kit: the ORIGINAL, OFF, OFF_REPEAT and ON arms, plus sharded, with the SAM cap from finding 5. Then run the persistent-storage requeue test before adopting at step 600 or later.
