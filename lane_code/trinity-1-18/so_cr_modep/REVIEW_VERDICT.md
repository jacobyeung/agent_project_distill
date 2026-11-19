VERDICT: GO AFTER FIXES

Patch 01 (`S1_PREP_FAST_PATHS`) can go as delivered. Patch 02 (`S1_PREP_SELECT_SQL`) should stay OFF until finding 1's test exists. By reading the code, I found no change to any produced byte under either switch. The blocking gap is test strength: nothing compares the patch-02 sparse path with more than 256 selected keys against the native scan, and the end-to-end fixture cannot detect a row-order error.

All paths below are relative to `/scratch/jjyeung/orch_n30`. "base" is `so_xstore/in/tree21b/work/tree_r1` and "dlv" is `so_modep/work/delivery_tree`. My own in-memory rerun was blocked by this session's command guard and was not retried. The rest of this review is static reading plus the lane's recorded evidence.

## Checks against the bar

**(1) OFF identity: PASS.** The delivered tree differs from base only in the six manifest files (`diff -rq`). All manifest SHA256 values match. Each hunk equals the actual `diff -u` of the delivered file. With both switches OFF:
- `_within` returns `path.is_relative_to(root)` (dlv `student_pilot/orchard_paths.py:17-18`).
- `resolve_read` runs the original body (dlv `orchard_paths.py:42`).
- `_database` keeps both full `SELECT i,row FROM rows ORDER BY i` scans, evaluated at the same moments as before (dlv `student_pilot/s1_exclusions.py:167-174`).

The authenticated source seal changes. NOTE:9 says so and requires rebuilding the seal.

**(2) Why ON output is identical: PASS by inspection.**
- **Patch 01, `_within`.** On POSIX, `_within` is the same test as `is_relative_to`: anchor equality plus a prefix match on `.parts`. The 3.12 implementation compares string equality of the path against each lexical parent, and `.parts` is the parsed anchor plus tail.
- **Patch 01, `_resolve_read_fast`** (dlv `orchard_paths.py:91-110`). It keeps every refusal, both `resolve()` calls in the original order, `owned()`, the `..` checks and the error strings.
  - `joinpath(*parts[len(source.parts):])` equals `destination / path.relative_to(source)`, including the case `path == source`.
  - The `lru_cache` (`:84-88`) caches only the parse of the mapping string. It is keyed by the exact text and does not cache exceptions.
  - The mapping still arrives through `env_key`, so the `Q_E4` alias keeps working (base `orchard_paths.py:23`).
- **Patch 02.** Every native `rows` relation has a unique integer `i`:
  - Tables: base `carrier_c1_data.py:607`, `carrier_c1_routing.py:974`, `c1r_clips.py:959`, `r2_materialize.py:147`, `decoupled_v_run.py:117`.
  - Views: base `r1_routing.py:137` (over `payloads` with `i` as integer primary key) and `s1_routing.py:251-253` (membership `i` is the primary key, joined 1:1 on unique `k`).
  - So sorted, disjoint chunks of at most 256 keys, each ordered by `i`, give the same rows in the same order as the full scan. The Python `index in wanted` filters remain (dlv `s1_exclusions.py:172-176`).
  - The connection stays `mode=ro`, and the full-file SHA256 pin still runs first (base `s1_exclusions.py:151`).
- **Not touched by either patch:** thread counts, worker pools, RNG draws, float accumulation, SQLite writes, receipt fields and authentication.

**(3) Hash reuse: N/A.** No hash, stat result or resolved path is reused. The only cache holds mapping text parses.

**(4) Error behaviour: PASS.** There is no pool. Exceptions keep the same type and message. With the frame-audit rule, `FrameAudit.expect` never iterates its rows (base `s1_admission.py:39-40`), so ON does not run the unused first query. A SQLite error such as a missing table therefore surfaces at the second loop instead, with the same `OperationalError`. In both cases `PhaseJournal.run` publishes nothing (base `first_batch_progress.py:40-50`).

**(5) Tests: PARTIAL.**
- The 4×169 matrix (`out/tests/final_native_*.log:296-298`) and the four-way native parity run (`out/tests/native_parity_exclusive.log`) drive the real `admit(prepare_only=True)` and byte-compare 39 files.
- ON does take the new paths, though only by deduction; no test asserts it:
  - Patch 01: `STUDENT_ORCHARD=1` and the frame-root map are set (`work/native_parity.py:13-16`).
  - Patch 02: VQA keeps indices 28–31 of 32 (`retained_off/.../prepared/vqa_indices.json`), so \(4 \cdot 4 < 32\) and the sparse branch runs.
- Weaknesses are in findings 1 and 2.

**(6) Minutes saved: labelled, with arithmetic that holds.** The residual \(70.20 = \) 00:15:17→01:25:29. All interval sums reproduce 140.57 min. \(26.38\% = (9.795 - 7.211) / 9.795\). Then \(0.2638 \times [40, 70] = [10.6, 18.5]\). See finding 4.

**(7) Names: PASS.** The new environment names `S1_PREP_FAST_PATHS` and `S1_PREP_SELECT_SQL` (and `export ...=1` lines) produce zero hits from the bound scanner: `bad_string`, with `WORDS` and the hashed lists in `build21/kits/q/b/wh.json` (base `launch_r2/build.py:19-36`; scope in `build21/naming21.py:30-48`). The patches add no logs, paths or arguments. See finding 3.

## Findings

1. **MEDIUM. Patch 02's multi-chunk sparse path is never compared row-by-row against the native scan, and the end-to-end fixture cannot detect order errors.**
   - In dlv `tests/test_modep_select_sql.py:37`, the only sparse case is `[1099,1,400,2]`, a single chunk. `range(1099,-1,-2)` has 550 keys and \(550 \cdot 4 \ge 1100\), so it takes the dense native scan; the "chunk boundaries" in the test name are never reached.
   - Line `:73` checks only `len(...) == 1100`, not order or content.
   - `work/bench_sql_final.py:31` asserts only `out == indices`. The output is rebuilt in the original index order (base `s1_exclusions.py:163`), so that assertion cannot see iteration order.
   - The native parity fixture has one physical frame per source (`retained_off/frames_*/frames.json`: `unique_frames=1`; `PROFILE.md:47`). Its `frame_inventory.sqlite` is therefore insensitive to the order of `keep` calls, and Exclusions counts commute.
   - Production VQA (204,413 source rows) may well take the more-than-256-key path on its first ON launch.
   - Smallest fix: add a sparse case with at least 257 selected keys and density below 1/4, for example `range(0, 2048, 5)` over a table of at least 2048 rows. Compare the full `rule.events` OFF vs ON for both table and view, and check the trace callback shows more than one query. Keep patch 02 OFF until this passes.

2. **LOW. The parity harness does not prove ON took the new code, and its frame set is degenerate.**
   - `work/native_parity.py:73-93` asserts byte equality only.
   - `bench_paths.py` covers 1,024 distinct deep paths, with identical inventory SHA256 (`out/tests/bench_paths.log:1-4`), but it sits outside the patch tests.
   - Smallest fix: wrap `orchard_paths._resolve_read_fast` and `s1_exclusions._selected_rows` with counting spies in the harness, and assert zero calls when OFF and more than zero when ON. Give the fixture rows several distinct frame files.

3. **LOW. Patch 01 reintroduces the literal token `split` into a file whose base deliberately avoids it.**
   - Base `orchard_paths.py:29` writes `mapping.__getattribute__("sp" "lit")('=', 1)`, the idiom used across the tree. dlv `orchard_paths.py:87` writes `mapping.split('=', 1)`.
   - Sealed source is outside the scanner's scope (`naming21.py:48`), and `tests.test_deploy_alias` and `test_s1_production_imports` pass, so nothing blocks it.
   - Smallest fix: copy the base expression verbatim.

4. **LOW. The headline saving is wider than its own arithmetic.**
   - REPORT.md:3 says "10–20 minutes"; the computation gives 10.6–18.5 (`PROFILE.md:47`).
   - The 40–70 min "path-heavy" share is an unmeasured assumption. Its upper bound is the whole residual, which also contains `run.prepared` revalidation (base `s1_admission.py:245`), where patch 01 barely applies.
   - The fixture's files are warm-cache 256-byte files, so the relative saving on Orchard storage is likely smaller. The report does say the saving can be zero.
   - Smallest fix: state "≤18.5 min, estimated (possibly 0)". On the first ON launch, compute the saving as 0.264 × the OFF `phase_resources.frames.seconds` (already native telemetry, base `s1_admission.py:281`).

5. **LOW. The switches apply to the whole process and are not recorded in any artifact.**
   - Both switches are plain `os.environ` reads. They are inherited by the training leg of the same job: `r.sh t` runs `r.sh p` as a child and then trains with the same environment (base `launch_s1/b/r.sh:29-40`).
   - So patch 01 also changes training-time `resolve_read` (for example base `batches.py:76`), and patch 02 changes `run.prepared` checks outside mode p. Both stay semantically equivalent, but neither is tested outside mode p.
   - Neither value appears in `request.json` (base `s1_admission.py:171-174`) or any receipt. Provenance rests on the operator record (NOTE:13).
   - NOTE does not name the file in which the operator sets the switch. A kit shell edit is re-scanned (`naming21.py:30-37`); the names pass.
   - Smallest fix: in NOTE, state the process-wide scope and name the exact kit line used to set each switch. Have the operator record both values beside the job ID in the ledger.

6. **INFO.**
   - The new names bypass the opaque-alias mechanism (base `student_pilot/job_env.py:3-6`). They pass the scanner, so nothing needs to change.
   - The new tests need `TMPDIR` set (dlv `tests/test_modep_fast_paths.py:17`, `test_modep_select_sql.py:22`), and they are not in N's focused list (`build21/focused.py:5-10`).
   - `tests/test_modep_gloo.py` runs a single-process `FrameAudit` on each of two ranks. It exercises no distributed code path of either patch, and it has not run (no sockets).
   - The OFF full scan implicitly reads every page of the source database; ON reads only the selected pages. The full-file SHA256 pin still authenticates every byte first, so no integrity check is lost.
