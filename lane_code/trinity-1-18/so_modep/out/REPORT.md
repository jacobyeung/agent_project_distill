VERDICT: DONE Two independent default-OFF speedups are packaged against build 21 and preserve every mode-p output byte on the native CPU fixture; production savings await the lane's launch measurement.

**Expected saving: 10–20 minutes per launch, estimated, from patch 01.** This assumes 40–70 minutes of production work resembles the path-heavy fixture, which measured 26.38% less elapsed time. No production ON launch was run, and the actual saving can be zero. Patch 02 receives **zero additional minutes in the planning estimate** until N's selections and launch timings demonstrate a benefit.

| Quantity | Result | Evidence class |
|---|---:|---|
| Existing mode p, jobs 172660 / 171377 | 140.57 / 145.27 min | Measured launch-to-exit logs |
| Revalidation and frame-audit envelope | 70.20 min | Inferred residual |
| VQA rebuilding | 38.60 min | Inferred from completion mtimes |
| Native preparation | 23.85 min | Inferred from completion mtimes |
| Native frame fixture, 32,768 references | 9.795 s OFF; 7.211 s ON | Measured paired means; 26.38% reduction |
| Sparse native SQL view, 820 / 82 of 8,192 rows | 3.09× / 5.56× throughput | Measured fixture; full pin hashes retained |
| Dense SQL selection | 0.3543 s OFF; 0.3581 s ON | Measured fixture; original scan retained |

[PROFILE.md](PROFILE.md) provides source file/line references, phase calculations, row/frame/byte denominators, thread behavior, uncertainty and fixture rates. The completion mtimes imply that the 38.6-minute interval belongs to VQA, and the 5.42-minute interval to pointing. N's configuration has no MDG block, so the parent-binding branch does not compute confusers. These facts change which phases deserve optimization.

The patches are [01_fast_paths.diff](patches/01_fast_paths.diff) and [02_selected_sql.diff](patches/02_selected_sql.diff). [manifest.json](patches/manifest.json) records SHA256 values, individual base/patched file hashes and base seal `b262e7a7`. Both apply independently and together without offsets, fuzz or rejects; [patch_application.json](tests/patch_application.json) contains exact application output. The input seal was recomputed as `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`; [delivery_verification.json](tests/delivery_verification.json) confirms only the six listed files differ, including three new test files.

| Patch | Enable switch | Work made cheaper | Default |
|---|---|---|---|
| 01 | `S1_PREP_FAST_PATHS=1` | Lexical path containment and repeated parsing of the same mapping text | OFF |
| 02 | `S1_PREP_SELECT_SQL=1` | Reading sparse selected SQLite payloads in bounded ordered queries | OFF |

Patch 01 replaces POSIX lexical ancestry checks with equivalent anchor/component-prefix comparisons and caches at most 32 mapping strings. Every native `resolve`, containment check, existence check, pin hash and SQL update remains. The cache stores parsed text only; changed mappings, symlinks and files are observed again. The OFF branch calls the original operations. See delivered `student_pilot/orchard_paths.py:15-43,84-110` and `student_pilot/s1_admission.py:42-66`. Python documents `is_relative_to` as lexical, without filesystem access, and `lru_cache(maxsize=...)` as bounded: [pathlib](https://docs.python.org/3.12/library/pathlib.html#pathlib.PurePath.is_relative_to), [functools](https://docs.python.org/3.12/library/functools.html#functools.lru_cache). Unit tests compare 25,600 path pairs, refusal behavior, the exact resolution-call sequence, inventory bytes and fixed samples.

Patch 02 preserves the full source hash, both logical validation passes, selected-row order, missing-index refusal and final original-index order. Sparse selections use sorted disjoint chunks of at most 256 integer keys with explicit `ORDER BY i`; dense selections retain the native scan. The native tables use unique integer indices, and the composed view preserves them. No output database write or pragma changes. See delivered `student_pilot/s1_exclusions.py:147-182` and the ordering rule in [SQLite SELECT](https://sqlite.org/lang_select.html). Tests cover native tables/views, dense/sparse/empty/unsorted inputs, chunk boundaries, changed inputs, missing/overflow indices and read-only queries.

No numerical operation, RNG draw, selection rule or authentication step changes. A worker-pool fixture was slower than serial execution, so no pool is delivered. Torch intra-op threads do not parallelize these Python/SQLite loops; the installed Torch source and official documentation are cited in PROFILE.md. No thread-count patch or hash reuse is proposed.

The full parity fixture calls real `s1_admission.admit(..., prepare_only=True)`, using the supplied native preparation builders, tokenizer, selected parent export, persisted-file authentication, opener, routing composition and frame audit. It retains 76 rows and 2,432 frame references across five source groups. VQA selection retains indices 28–31 of 32 to exercise the sparse SQL branch. It compares all **39 files** by both SHA256 and raw bytes under OFF, paths-only, SQL-only and both switches. SQLite databases, receipts, configuration, indices, sample reports, phase markers and retained publication files all match. [modep_file_parity.json](tests/modep_file_parity.json) contains every filename and digest; [native_parity_exclusive.log](tests/native_parity_exclusive.log) contains the full run output.

The harness uses identical physical paths, request/attempt identity and UUID sequence in every run. It fixes exactly the native telemetry fields `resources.seconds` and `resources.peak_rss_kib`, declared in `student_pilot/first_batch_progress.py:44-45`. Their containing result-file hashes consequently match too. It excludes or normalizes no output file after execution. Actual elapsed times and peak RSS are recorded separately in [native_phase_measurements.json](tests/native_phase_measurements.json). The native exclusive file writers run unchanged during admission. Fixture-only host/model construction follows the supplied test helpers; it is not a production patch. Real launches naturally produce different UUIDs, times, RSS and authenticated source seals; byte parity here means identical rebuilt code/inputs/identity under the four switch settings.

Exact parity summary output:

```text
MODEP_PARITY {"label": "off", "files": 39, "seconds": 15.534037466626614, "identical": true}
MODEP_PARITY {"label": "paths", "files": 39, "seconds": 15.650284917093813, "identical": true}
MODEP_PARITY {"label": "sql", "files": 39, "seconds": 16.722545661963522, "identical": true}
MODEP_PARITY {"label": "both", "files": 39, "seconds": 15.279994109645486, "identical": true}
```

These tiny end-to-end times establish parity, not a meaningful end-to-end speedup. Initialization and routing dominate this fixture.

The fresh tree produced by applying both delivered patches passes the 112 focused build-21 native tests plus 57 admission, exclusion, filtering, journaling, path/SQL and related tests in every configuration. Each run reports 167 passes and two explicit skips:

| Configuration | Exact unittest summary | Exact final output | Full log |
|---|---|---|---|
| Both OFF | `Ran 169 tests in 72.051s` | `OK (skipped=2)` | [OFF](tests/final_native_off.log) |
| Paths only | `Ran 169 tests in 63.139s` | `OK (skipped=2)` | [Paths](tests/final_native_paths.log) |
| SQL only | `Ran 169 tests in 68.557s` | `OK (skipped=2)` | [SQL](tests/final_native_sql.log) |
| Both ON | `Ran 169 tests in 61.218s` | `OK (skipped=2)` | [Both](tests/final_native_both.log) |

The skips are the unstaged external dev-S1 manifest and the optional socket-dependent Gloo test. All 112 core native tests pass. Independently applied patch 01 reports `Ran 12 tests in 2.776s` / `OK (skipped=1)`; patch 02 reports `Ran 18 tests in 0.336s` / `OK (skipped=1)`. Their exact outputs are [standalone01.log](tests/standalone01.log) and [standalone02.log](tests/standalone02.log).

Commands used from `/scratch/jjyeung/orch_n30/so_modep`:

```bash
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/validate_matrix.py' > out/tests/native_matrix_driver.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; export MODEP_TREE="$PWD/work/delivery_tree" MODEP_NATIVE_LABEL=native_parity_exclusive; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/native_parity.py' > out/tests/native_parity_exclusive.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; export MODEP_TREE="$PWD/work/patch01" MODEP_TEST_LABEL=standalone01; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_native_tests.py tests.test_modep_fast_paths tests.test_modep_gloo tests.test_s1_admission' > out/tests/standalone01.log 2>&1
nice -n 10 taskset -c 0-7 bash -c 'source work/env.sh; export MODEP_TREE="$PWD/work/patch02" MODEP_TEST_LABEL=standalone02; exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_native_tests.py tests.test_modep_select_sql tests.test_s1_scene_exclusions' > out/tests/standalone02.log 2>&1
```

The matrix driver prints exactly `off 0`, `paths 0`, `sql 0`, `both 0`, one per line. [native_matrix.json](tests/native_matrix.json) preserves every expanded test command and switch value. Test runners retain their artifacts; a future independent replay must use fresh output labels. The complete native parity fixture and its supporting module are in `work/native_parity.py` and `work/fixture_modules/modep_native_fixture.py`. The patches themselves include targeted regression tests. Benchmark code and exact outputs are `work/profile_fixture.py`, `work/bench_paths.py`, `work/bench_sql_final.py` and [profile_fixture.log](tests/profile_fixture.log), [bench_paths.log](tests/bench_paths.log), [bench_sql_final.log](tests/bench_sql_final.log).

[NOTE_FOR_TREE_REBUILD.md](NOTE_FOR_TREE_REBUILD.md) gives the apply-after-first-proof procedure and first-launch timing plan. Rebuild authenticated source identities through N's normal process, prove the rebuilt tree with both switches OFF, then measure patch 01 alone. The read-only `work/measure_modep.py` helper was exercised against real native fixture receipts; [measure_fixture.json](tests/measure_fixture.json) uses synthetic launch timestamps solely to test its arithmetic. It is not an additional timing measurement.

Risks and detection:

- Production Python/pathlib, filesystem latency and row mix may reduce or erase the fixture benefit. Record the worker version and compare native frame seconds per reference plus total elapsed time on matched launches. Turn the switch OFF if it regresses.
- Sparse SQL gains depend on retained-index density and query plans. Dense selections retain the original scan; unusual views may still be slower. Compare preparation/revalidation timing and retain existing source/count checks.
- Path aliases, symlink mutation, corrupted pins or missing files must continue to refuse. Mutation tests pass; a refusal or any byte/count/sample mismatch blocks enabling the corresponding switch.
- Source edits change the authenticated code seal. Rebuild and run normal native proof gates; never reuse build 21's old seal for changed code.

Not done: production-scale timing, an H100 training run, the unstaged external-manifest test and socket-dependent tests. The delivered `work/run_gloo.sh` runs the new two-rank CPU frame-inventory parity test and existing native checkpoint-buffer tests where sockets are available. These are lane follow-ups, as requested. Production per-stream retained counts, unique-frame counts and frame sizes are unavailable in the supplied receipts; PROFILE.md labels estimates and unknowns explicitly.

Runtime: Python 3.12.13, Torch 2.11.0+cpu and SQLite 3.53.1; CUDA hidden, nice 10, Torch/OMP/MKL/OpenBLAS capped at eight threads and CPU affinity 0–7. The complete native fixture observed at most 628,472 KiB peak RSS (not a measurement of every subprocess in all suites). Inputs remain read-only. No Git, SSH, Slurm, GPU execution or deletion was used. Work started 2026-11-19 09:45:47 UTC on trinity-1-18, before the 12:45:47 UTC deadline.

Package verification completed 2026-11-19 10:24:33 UTC. Lane disk usage measured 1,244,780 KiB at 10:23:51 UTC, below the 3 GB limit.
