VERDICT: GO AFTER FIXES

Scope of the GO. Patches 03, 04 and 02 can be applied now, with every switch OFF, and then enabled one at a time in the NOTE's order. Patch 01 may be applied with its switch OFF, but it must never be enabled. I found no path on which any patch trains on stale or changed bytes. The fixes below correct numbers in the report and gaps in the cross-run design. Findings 1 and 2 must be fixed before anyone plans work on that design. Findings 3 and 5 must be fixed before the NOTE is used. Finding 4 is optional.

Paths are relative to `/scratch/jjyeung/orch_n30/so_launch/`.
- `I` is the input tree `in/tree/work/tree_r1`.
- `V` is the delivered verification directory `work/verify_20261119T082118Z` (standalone, `recommended` and `combined` trees).
- `L1` is `/scratch/jjyeung/orch_n30/so_in/.../r1_ops6/work/mon/last.txt` (job 172660).
- `L2` is `.../swarm_opt/work/o/look1.out` (job 171377).

## Findings

1. **MEDIUM: the design's 110–135 min saving assumes the frames half of mode p is cheap to adopt, but that work is tied to the node.**
   - The frames phase audits this node's frame roots (`I/student_pilot/s1_admission.py:249-255`).
   - Its inventory stores physical paths. On reuse, every retained frame is re-checked on the node (`s1_admission.py:103-117,258-259`).
   - The native request binds the node's resolved frame roots and the frame-root map (`s1_admission.py:170-173`).
   - The report itself marks the result-to-exit interval (70.20 and about 72.07 min) as inferred, not isolated (`out/REPORT.md:25`).
   - The design gives a 10–30 min allowance for fetch, full SHA, adoption and remaining frame work (`out/CROSS_RUN_STORE_DESIGN.md:41`), and nothing measures it.
   - If adoption must redo the frame audit on each node, the saving is about 70 min minus fetch and verification, not 110–135.
   - Smallest fix:
     - State the planning number as "about 70 min, the prepare half, until measured."
     - Add one cheap CPU measurement: native mode p on a complete journal on one Orchard node. Both phases are reused, so this times the full `pinned()` rehash, `run.prepared` and `verify_frames`. That is the floor of any adoption cost.

2. **MEDIUM: the design does not name the Orchard data path, so its store cannot be built as written.**
   - The design calls for a store "readable by every Orchard node" with an uploader, costed at 1–2 days (`CROSS_RUN_STORE_DESIGN.md:5,29`).
   - Today, inputs reach Orchard only through the login node, which fetches from GCS into the cache (`I/launch_s1/b/c.sh:4,11-13`).
   - Staging must report `project_community_write_bytes == 0` (`I/launch_s1/b/g.py:110-113,134-137`).
   - Job-side uploads go through GCS sessions minted outside the job, one per milestone name (`c.sh:404-435`).
   - The design does not say which channel publishes a store root, or how a job gets that right. Its effort estimate leaves this out.
   - Checkpoint bindings also pin the derived config identity and the preparation pin (`I/student_pilot/carrier_c1_run.py:2920`), and phase directories are `uuid4` (`I/student_pilot/first_batch_progress.py:40`). The design names this only abstractly (`CROSS_RUN_STORE_DESIGN.md:21`).
   - Smallest fix:
     - Name the channel, for example the existing GCS export, then a login-node fetch into a read-only store in the Orchard cache.
     - Keep the zero-write staging invariant.
     - Add content-derived phase directory names as a design item.
     - Re-estimate the effort.

3. **LOW: patch 03's upper bound of 10 min is not supported by the logs. The likely saving is about 4–5 min per resume launch.**
   - Gap measurements:
     - The 675-s gap covers three passes (`L1:162-163`).
     - The 86-s gap covers one warm pass plus about 1 s of overhead. Job 171377, with no checkpoint, shows 1 s in both gaps (`L2:280-281,347-348`).
   - The node has 1842 GiB of RAM (`L1:163`), so passes 2–3 read from page cache, as pass 4 did. The memo removes passes 2–4, which are the warm ones: about 3 × 85 s ≈ 255 s.
   - The report's even split (`out/REPORT.md:75`) assigns about 190 s to pass 4, which was measured at 86 s.
   - Even the largest value consistent with the logs (pass 1 at least as slow as passes 2–3) is 2 × 225 + 86 ≈ 536 s ≈ 9 min. That requires the page cache to drop the checkpoint between passes.
   - Smallest fix:
     - Change the claim at `out/REPORT.md:60,75` and `out/NOTE_FOR_TREE_REBUILD.md:19` to "about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint."
     - Measure the real figure with `TK_LAUNCH_TIMING=1` on the first resume job.

4. **LOW: no test executes patch 04's `c.sh` stage-lock timing branch.**
   - `TK_LAUNCH_TIMING` appears only in `tests/test_launch_phase_timing.py:33,102`, and both cases stub `c.sh`.
   - `V/04_launch_phase_timing/launch_s1/b/c.sh:271-278` (`stage_wait_start`, `wait_seconds`) is therefore never run.
   - I probed it with the real recommended `c.sh` and stubbed staging helpers under `bash -euo pipefail`:
     - Both `tk_stage prep` and `tk_stage preflight` exit 0.
     - ON writes the two lock lines. OFF output is byte-identical to the input's.
   - Smallest fix: add that case to the existing real-`c.sh` harness, asserting the two lines and exit code 0.

5. **LOW: applying all four patches in the documented order leaves `b/c.sh.orig` and `b/r.sh.orig` in the kit.**
   - Patch 01's hunks apply with offsets after patch 04, so GNU patch writes backups. They are present in `V/combined/launch_s1/b/`.
   - `I/launch_s1/b/a.py:31-33` inventories every file under `b/`. A rebuilt kit therefore either fails the inventory or seals stale copies.
   - The recommended set (03, 04, 02) produces no backups.
   - Smallest fix: add `--no-backup-if-mismatch` to the commands at `out/NOTE_FOR_TREE_REBUILD.md:4-6`.

6. **LOW (patch 01, OFF): any inherited `TK_PC_LOCK_HELD=1` silently disables the run lock.**
   - The child trusts a bare environment variable (`V/01_prepared_input_cache/launch_s1/b/r.sh:34-37`).
   - Slurm exports the submitter's environment by default, and `I/launch_s1/b/r.sh:6-8` scrubs only secret names. A stray value would skip the lock and its duplicate-job protection.
   - Fix, if 01 is ever enabled: export `TK_PC_LOCK_HELD="$$"`, and have the child accept it only when it equals `$PPID`.

7. **LOW (patch 01, OFF): the cache files and logs copy the full config and name the method.**
   - `o/<job>.prepared-cache.json` and every cache receipt embed the full parsed config and the full `k/0.json` (`V/01_.../b/pc.py:200-202`, `seal()`).
   - The refusal texts name "MDG" (`pc.py:129-148`). When `Context()` refuses at `pc.py:474`, outside any `try`, that text reaches the job log as a traceback, and the exit code 1 counts as a MISS.
   - The forbidden-word test scans only the fixture config (`tests/test_prepared_input_cache.py:462-471`). That config's field names, `vqa` and `pointing`, pass its regex.
   - Native receipts already carry this config, so these are extra copies, not new disclosure.
   - Fix, if 01 is ever enabled: write the key and per-component digests instead of the components, and use generic refusal text.

8. **INFO, check 1: with every switch OFF, all four patches are inert.**
   - The only OFF-path additions are:
     - shell assignments: `TK_PC_HIT=0`, `TK_PC_PREPARE=0`, `local stage_wait_start`;
     - function definitions;
     - environment reads;
     - an unconditional `import os` at `f2.py:4`. `pathlib` has already loaded `os`, so no new module loads.
   - There are no new file reads, writes or receipt fields.
   - All patches dry-run cleanly with `--fuzz=0` against `I`. Their SHA256 and base hashes match `manifest.json`, and every delivered tree matches its patch hunks.

9. **INFO, check 4: the patch 03 memo cannot skip a verification of bytes that may have changed, within its model.**
   - The first call in each allocation always hashes in full.
   - A hit requires all of these to be unchanged: job, start time, host, path, binding and validator SHA; the marker SHA256; and dev/inode/size/mtime_ns/ctime_ns of the marker and every payload (`V/03_.../b/r8.py:50-114`).
   - The fingerprint is re-taken after the full hash (`r8.py:114`).
   - The trainer re-hashes every shard, the replicated file and the RNG payloads when it loads them (`I/student_pilot/full_ft.py:563-567,603,618`; `carrier_c1_run.py:2063`). A wrong memo hit could therefore never train on changed bytes.
   - My probes:
     - A `chmod` forces a re-hash.
     - A write during the first verification makes the job refuse, and the next call refuses too.
     - A symlinked parent disables the memo, so every call hashes in full and no event line is written. Check `.checkpoint-verification/<job>.events.jsonl` on the first resume job.
   - Residual risks: shared-mmap writes with deferred timestamp updates, and a same-user forger.

10. **INFO, check 3: patch 02 gives the same verdict and count as serial hashing.**
    - Worker threads are capped at 8 (`f2.py:63`), and in-flight tasks at 2 × workers (`f2.py:77`).
    - Worker errors surface through `result()`. Only the error message can differ when two frames fail.
    - No test asserts the in-flight bound.
    - The saving is unmeasured, and the report says so.
    - My randomized serial-versus-parallel fault probe was blocked by the deletion guard, so it did not run.

11. **INFO, check 5: patch 04 writes only timing lines.**
    - `job.sh` and `r.sh` append "job phase …" lines to `o/<job>.steps`, guarded and `|| true`.
    - `c.sh` writes through `tk_step` (`I/launch_s1/b/c.sh:25-30`), which also echoes to stdout.
    - A missing `o/` or an unwritable steps file is tolerated. A failed guard keeps exit code 7.

12. **INFO, check 2 (patch 01): I found no preparation input outside the key.**
    - The native request fields (`s1_admission.py:170-173`) map to:
      - the input config pin and the commit;
      - the contract's frame roots;
      - constants in hashed `b/` files (`STUDENT_FRAME_ROOT_MAP` at `c.sh:371`, 16 threads at `w.py:44-45`);
      - `S1_CPU_REHEARSAL` (`I/launch_s1/b/q0.py:6`), which is in `ENVIRONMENT`.
    - The three dropped environment names are not read on this path: the C1 path hard-codes `get_student('qwen35')` (`carrier_c1_run.py:516-517`).
    - Reuse hashes every receipt file and every manifest frame. A MISS now leaves the destination intact. Corrupt, missing, partial, purged and concurrent cases miss or serialize. The HIT report records the source job, paths, key and a SHA-pinned receipt.
    - A same-node HIT only replaces native reuse that already hashes every output in full (`I/student_pilot/p3_provenance.py:44-51`, through `first_batch_progress.py:36-38`). Its saving is zero, confirmed.

13. **INFO, check 7: patch 01 cannot help at successive training boundaries.**
    - A next leg on another node finds no source (`g.py:66-67`, node-local `/tmp`).
    - A native rebuild there gets new `uuid4` phase directories, so the checkpoint binding (`carrier_c1_run.py:2920`) changes and resume refuses.
    - A new logical run, the pattern of the continuation job 172660 (`6ed2c7aa` at `L1:248`, versus 171377's `673bc60f` at `L2:367`), changes `cfg.output` and so the key.
    - So the expected saving per boundary is 0.
    - A safe cross-run design needs the items already listed in the design, plus findings 1 and 2. For one logical run, a smaller first step is content-derived phase directory names plus a verified byte-identical copy. That keeps paths stable across nodes, so the existing binding holds without regenerating seals.

14. **INFO, check 8: patches 02–04 add only generic names.**
    - The added names are `TK_*` switches, `.checkpoint-verification`, `<job>.events.jsonl` and "job phase …" / "lock wait" log lines.
    - The memo schema string `s1-job-checkpoint-verification-v1` follows the native `s1-*` convention.
    - `tk_persist_small` mirrors the memo JSON into the kit's `runs/` (`c.sh:401-402`), and the binding it copies is already mirrored there.

15. **INFO: reproduction and the phase table.**
    - My re-runs on `V/combined`: 10 + 6 + 7 + 31 + 9 tests, all OK. The standalone 03, 04 and 02 trees: 10, 6 and 7 tests, all OK.
    - Native gate: 86 tests, OK (1 skip, the unstaged pool receipt) on `I`, `recommended` and `combined`. Local sockets work here, so the 10 Gloo tests that the report skipped ran and passed.
    - The native gate is also OK with `TK_CHECKPOINT_VERIFY_MEMO=1`, `TK_PARALLEL_FRAME_SHA=1` and `TK_LAUNCH_TIMING=1` set on `recommended`.
    - I recomputed every row of the phase table from `L1` and `L2`, including 140.57 and 145.27 min for mode p and the 675-s and 86-s gaps. All match.
    - My scratch went only under `/scratch/jjyeung/orch_n30/so_cr_launch2/review_tmp/` (39 MB).
