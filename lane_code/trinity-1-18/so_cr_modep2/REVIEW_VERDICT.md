VERDICT: GO

Both patches can go under NOTE's adoption rule: both switches OFF on N's first launch, and each turned ON only after real-store parity. All five round-1 findings are fixed, and each fix has a test that fails on a broken variant. Reading the code, I found no change to any produced byte and no skipped check under either switch. Two remaining gaps are LOW and should close before the first ON launch. Two refusal branches that patch 01 reimplements have no failing-case test (finding 1). NOTE puts a free-form ledger on Orchard (finding 2).

Paths are relative to `/scratch/jjyeung/orch_n30`. "base" is `so_xstore/in/tree21b/work/tree_r1` and "dlv" is `so_modep/work/delivery_tree`. This session's command guard rejected my in-memory test and mutant rerun, as in round 1, and I did not retry it. Test strength below therefore rests on the lane's retained logs plus line-by-line reading of the test source. I wrote nothing except this file.

## Round-1 findings: fix, test, broken variant

| # | Fix (dlv file:line) | Test | Fails on a broken variant | Status |
|---|---|---|---|---|
| 1 MEDIUM | 820 sparse keys, density below 1/4, four chunks per pass, table and view | `tests/test_modep_select_sql.py:48-93`. It compares every ordered `expect`/`keep` event (`:88`) and the order-dependent output (`:89`), traces 8 vs 2 queries (`:82`), and checks raw `(i,row)` against the full scan (`:90-92`). Inventory bytes over 820 distinct frames: `:96-122` | Reversed chunks fail both tests (`out/tests/review1_mutant_0/1_*.log`). Ignoring ON fails with `0 != 2` (`mutant_3`). | Fixed |
| 2 LOW | Spies on `_resolve_read_fast` and `_selected_rows`, asserting zero calls OFF and positive calls ON (`work/native_parity.py:82-90`). 32 distinct frames per source, with VQA frame order rotated (`work/fixture_modules/modep_native_fixture.py:25-27,77-81`) | `tests/test_modep_fast_paths.py:48-53`. Native calls: paths 3768, sql 10 (`out/tests/review1_parity.log`) | Ignoring ON fails with `0 != 1` (`mutant_4`). The one-frame fixture fails at `native_parity.py:92` (`review1_parity_degenerate.log`). | Fixed |
| 3 LOW | `orchard_paths.py:87` uses the base `__getattribute__("sp" "lit")` spelling | `test_modep_fast_paths.py:55-58` | Restoring the literal attribute spelling fails it (`mutant_5`) | Fixed |
| 4 LOW | Headline now reads "≤18.5 min, estimated (possibly 0)" (REPORT.md:3). Helper: `work/measure_modep.py:22` | `work/test_review_contracts.py:17-21,39-55` | Inflated headline and 0.3 multiplier both fail (`review1_contract_mutant_*.log`) | Fixed |
| 5 LOW | NOTE:12 (scope), NOTE:14-19 (exact kit lines), NOTE:23 (ledger) | `test_review_contracts.py:23-28` | Missing scope, missing SQL line and missing ledger all fail | Fixed (see finding 2) |

## Checks against the bar

1. **OFF byte-identity: PASS.**
   - `diff -rq` base vs dlv shows only the six manifest files. All six SHA256 values and both patch hashes and sizes match `manifest.json`. Each patch hunk equals `diff -u` of base vs dlv for all three source files. `work/tree` is identical to dlv.
   - OFF behaviour:
     - `_within` returns `path.is_relative_to(root)` (dlv `orchard_paths.py:17-18`).
     - `resolve_read` runs the base body unchanged (`:44-63` = base `:29-47`).
     - `_database` issues both full `SELECT i,row FROM rows ORDER BY i` scans at the same two moments: genexpr creation and the loop (dlv `s1_exclusions.py:169-174`).
   - The source seal changes, so `request.json.source_revision` changes (base `s1_admission.py:167-171`). NOTE:3 requires a rebuild.

2. **ON identical: PASS by inspection.** Neither patch adds threads or pools, or touches RNG, float work, SQLite writes, receipt fields or pins.
   - **Patch 01:** `_within` is the same test as `is_relative_to` for POSIX paths: equal anchor plus a tail-prefix match. `_resolve_read_fast` (`:91-110`) keeps every refusal of base `:32-46` in the same order. It makes the same resolve calls in the same left-to-right order (`:107`). `joinpath(*parts[n:])` equals `/ relative_to(source)`, including `path == source`. The cache holds parsed mapping text only (`:84-88`).
   - **Patch 02:** every `rows` relation has a unique integer `i`.
     - Six tables are declared `i INTEGER PRIMARY KEY` (`carrier_c1_data.py:607`, `carrier_c1_routing.py:974`, `c1r_clips.py:959`, `decoupled_v_run.py:117`, `r1_routing.py:74`, `r2_materialize.py:147`).
     - The two views join 1:1: `r1_routing.py:137`, and `s1_routing.py:252-253` (membership `i` PK, `k UNIQUE`, `candidates.k` PK).
     - So sorted, disjoint 256-key chunks, each `ORDER BY i`, give exactly the full scan's wanted rows in order (`s1_exclusions.py:147-156`).
     - The pin (`:163`), `mode=ro`, the `index in wanted` filters and the `found != wanted` check (`:180`) remain.
   - **Switch reach:** the switch values reach the worker. Bubblewrap has no `--clearenv` (base `launch_s1/b/c.sh:334-358`), `i.py` has no environment allowlist, and the admission child inherits `{**os.environ}` (`s1_admission.py:376`). `request.json` does not record the switches (`:171-174`), so ON does not change its bytes.

3. **Hash reuse: N/A.** No hash, stat result or resolved path is cached. The `lru_cache` key is the exact mapping text (`orchard_paths.py:84-85`). `test_modep_fast_paths.py:76-90` asserts 6 resolve calls per 2 lookups and that a changed mapping is re-parsed.

4. **Error behaviour: PASS.**
   - No workers are involved. Exception types and messages are unchanged.
   - Under ON, the first sparse pass is a lazy generator, so a SQLite error such as a missing table surfaces at the second loop (or inside `Exclusions.expect`), with the same `OperationalError`.
   - `PhaseJournal.run` publishes the marker only after `action` returns (`first_batch_progress.py:40-50`), so no partial output is published.

5. **Tests: PASS, with the gap in finding 1.**
   - **Real native code:** the native harness drives real `admit(prepare_only=True)` on N's fixtures. It fixes only `resources.seconds`/`peak_rss_kib`, UUIDs and uname (`native_parity.py:51-53,83-86`). It byte-compares all 39 files (`:96-99`) and asserts that native writes stay under the destination (`:94`).
   - **Matrix:** it sets both switches for each of the four configurations (`work/validate_matrix.py:9`). Every run shows `Ran 173` / `OK (skipped=2)`; the skips are the unstaged manifest and Gloo.
   - **End-to-end order sensitivity:** limited to VQA's rotated rows (4 rows, one chunk). The multichunk unit tests cover the rest.
   - **Additional broken variants I checked by reading:**

     | Broken variant | Caught by |
     |---|---|
     | Python-level row reversal inside a chunk (SQL text unchanged) | `:45`, `:88`, `:90-92`, via `Rule.expect` `list(rows)` at `:16` |
     | Unsorted keys (set order, which interleaves above 2048) | `:88` |
     | Duplicated chunk head | `:88` |
     | Dropped int64 filter | `OverflowError` is not `ValueError`, so `:124-133` errors |
     | `_within` without the anchor check | `_within('/a', '.')`: `test_modep_fast_paths.py:38-46` |
     | `_within` as a string `startswith` | `_within('a/b', '.')`: `:38-46` |
     | Symlink-escape check removed | `:60-74`, via `escape` |
     | `..` path check removed | `:60-74`, message differs |
     | Wrong join | `:60-74`, `:92-113` |
     | Cached resolution | `:88-89` |

     Two variants survive every listed suite; see finding 1.

6. **Minutes saved: PASS.** The OFF mean is 9.795 s and the ON mean 7.211 s (`out/tests/bench_paths.log:1-4`), a 26.38% reduction. Then \(0.2638 \times [40, 70] = [10.55, 18.47]\) min, stated as "≤18.5 min, estimated (possibly 0)" (REPORT.md:3, PROFILE.md:47). The 40–70 min share is labelled unmeasured. Patch 02 adds 0 minutes to the estimate.

7. **Names: PASS for the patches.**
   - I ran `bad_string` in memory with `WORDS` (base `launch_r2/build.py:19-21`) and all three `wh.json` lists. These produce zero hits: `export S1_PREP_FAST_PATHS=0/1`, `export S1_PREP_SELECT_SQL=0/1`, `test_modep_*.py`, `MODEP_RUN_GLOO`, the `modep_*_` temp prefixes and `o/modep_switches.jsonl`.
   - Control strings are flagged as expected.
   - The patches add no logs or arguments. The kit `b/r.sh` edit point is real (base `launch_s1/build.py:38`) and inside the scanner's scope (`build21/naming21.py:30`).

## Findings

1. **LOW. Two refusal branches on the ON path have no failing-case test, so deleting either would leave every suite green.**
   - **Fast resolver destination check.** `'..' in destination.parts or not owned(destination)` (dlv `orchard_paths.py:100-101`) is never reached with a refusing input.
     - Every mapping in `test_modep_fast_paths.py:67-71` is either refused earlier or passes ownership.
     - `data2root/../data2root` fails `destination == allowed` and is refused by the "must stay" check at `:98-99`.
     - No test in the tree asserts "escapes owned storage".
   - **FrameAudit frame-root check.** The root containment in `FrameAudit.keep` (dlv `s1_admission.py:57`) has no test with an existing file outside the frame roots, either OFF or ON. No test asserts "outside its frame store".
   - The delivered code keeps both checks (read against base `orchard_paths.py:38-39` and `s1_admission.py:57`). This is a regression-protection gap for logic patch 01 duplicates.
   - **Smallest fix (about 15 lines in `test_modep_fast_paths.py`):**
     - Patch `paths.SCRATCH` to `self.root/'scratch'`.
     - Add the mappings `{'/data2': str(scratch)}` (fails ownership because the path equals the root) and `{'/data2': str(scratch/'a/../b')}`.
     - Add a `FrameAudit.keep` case, under flags `0` and `1`, whose pin resolves to an existing file outside `self.frames`, and assert `ValueError`.
     - Show that removing `or not owned(...)` and the `_within` root test each fails.

2. **LOW. NOTE puts the per-job switch ledger on Orchard with unconstrained path fields.**
   - NOTE:23 requires `<kit>/o/modep_switches.jsonl`. `<kit>/o` is the kit output directory that `tk_persist_small` mirrors to Orchard home (base `launch_s1/b/c.sh:399`).
   - Its rows must carry "paths to the OFF baseline and real-store parity evidence". Nothing stops a Trinity lane path or another forbidden word from being written there.
   - The file name passes the scanner, and `a.py:31` only inventories `b/` and `k/`, so nothing breaks.
   - **Smallest fix:** keep this ledger on Trinity beside the lane's other ledgers. Otherwise, require every field to pass `bad_string` and every path to be an opaque Orchard path.

3. **INFO. The measurement helper's output trips the scanner's `sti` word.**
   - `estimated_path_saving_seconds`, `estimate_basis` and "substitute" all contain `sti` (`work/measure_modep.py:22-23,33`).
   - The helper is outside the patches, and stdout is outside scan scope (`naming21.py:48`). It would only matter if it ran in an Orchard job log.
   - **Smallest fix:** rename the keys to `projected_path_saving_seconds` and `projection_basis`, and reword the note.

4. **INFO. The reverse-rows mutant is caught by the query-text check, not by the row-order comparison.**
   - `sql_reverse_rows` fails at `endswith('ORDER BY i')` (`test_modep_select_sql.py:83`; log: `False is not true`). REPORT.md:24 says "descending rows fail the ordered test".
   - By reading, a reversal that leaves the SQL text unchanged is still caught at `:88` and `:45`. No test change is needed.

5. **INFO. The production adoption gate has no tool.**
   - NOTE:25-35 requires an isolated real-store OFF/ON shadow run that replays the same paths and identities. Nothing delivered implements it.
   - `native_parity.py` is bound to the lane fixture.
   - Without a tool, the switches may simply stay OFF. That is safe, but no time is saved.
   - **Smallest fix:** a script that calls `admit(prepare_only=True)` twice against the production request into two fresh node-local directories. It should fix `uuid4`, `perf_counter` and `getrusage` exactly as `native_parity.py:83-86` does, then byte-compare the two directories.

6. **INFO. OFF implicitly decodes every row; ON reads selected rows only.**
   - OFF's full scan decodes every row's text and touches every page. ON does neither for unselected rows.
   - An invalid-UTF-8 or malformed page in an unselected row would refuse OFF and pass ON. That case is unreachable: the full-file SHA256 pin (`s1_exclusions.py:163`) authenticates every byte, and native writers bind Python `str`.

7. **INFO, carried from round 1.**
   - `tests/test_modep_gloo.py` is still unrun (no sockets), and it covers no distributed path of either patch.
   - The new tests need `TMPDIR` set and are not in N's focused list. `validate_matrix.py` includes them.
