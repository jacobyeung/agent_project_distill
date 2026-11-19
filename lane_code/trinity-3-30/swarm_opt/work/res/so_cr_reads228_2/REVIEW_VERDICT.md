VERDICT: GO AFTER FIXES

The kit has not started yet. It refuses to run until the 13 runtime parts listed in MISSING.json are staged and a card passes the gate (all 8 cards were busy in the dispatch snapshot). Once those are in place, staging and the 50-item OFF run look sound. The SAME_INSTRUMENT verdict, though, cannot be trusted until findings 2 and 3 are fixed. Each of the fixes below is a few lines of code.

Paths: K = /scratch/jjyeung/orch_n30/so_reads228/out; S = so_in/.../cont_ops/work/r1route/out3/A10b/src (the sealed source mirror).

Evidence run:
- `bash K/tests/run_tests.sh` passed with CPU only: test_kit 39, test_review 18, test_prepare 7, test_bootstrap36 7, all OK.
- `diff -rq` of the kit's A10b tree against the mirror is empty.
- FIRST50.json matches the mirror return: the prefix sha, the 50 IDs, the 636-row order and the export. That mirror return matches all 77 members of package/a/f/0.tgz.
- STAGE_PLAN input archives a0–a5 match a/1.json, and the vnice/terminator shas match the staged lists.
- Comparator probes ran in fixtures under so_reads228/work/review_tests/cr2probe*. Each perturbation below still returned SAME_INSTRUMENT with 50/50 eligibility:
  - binding settings_sha256 changed;
  - binding artifact_manifest_sha256 changed;
  - settings arm and config changed;
  - binding reader_entry, device, arms and modes changed;
  - SUMMARY failure "telemetry failed; run is diagnostic-only" plus FAILED.json;
  - reference and candidate environment.json both edited.

## Findings

1. HIGH (blocking precondition; the kit itself is honest about it). The base Python and torch 2.13.0+cu130 runtime is not staged. K/MISSING.json lists 13 parts, 10,497,433,600 B, on orchard-login-001 with `fetch_allowed:false`. STAGE_PLAN.json has `runtime_archives` r0/r1/r2 with `sha256:null` and no member lists. Several things therefore remain unverified until those bytes arrive:
   - whether the runtime fits the 40 GB expansion estimate (STAGE_PLAN budget);
   - relocation (finding 4);
   - the `versions()` probe (K/stage228.py `versions`);
   - the d/v/py control interpreter.

   Smallest fix: the coordinator delivers the parts together with a member list and a sha256 for each part. Then run `coordinator228.sh` up to and including STAGE_CHECK.json, and only after that reach any card.

2. MEDIUM. The comparator ignores most of the instrument identity. K/compare228.py:12-15 `BINDINGS` omits `settings_sha256`, `artifact_manifest_sha256`, `reader_entry`, `maker_name`, `device`, `arms`, `modes`, `r0_pin`, `schema`, `ids` and `count`. Lines 101-105 check only the `read_*` settings keys. So a 2-28 run with a different SAM3 source tree (finding 3), settings file or entry can still be certified, as the probes above showed. On an honest run all of these fields are logical-path or content values, so they must equal Orchard's.

   Smallest fix: at line 125, compare the whole dicts, `envs[0][kind]['binding']==envs[1][kind]['binding']` and `envs[0][kind]['settings']==envs[1][kind]['settings']`, and list the differing keys in `reasons`.

3. MEDIUM. Pre-existing `/scratch/jjyeung/b01ec87a6f29b/d/s` on 2-28 is never reconciled. r228_lists/existing_d.txt shows `d/s` dated Nov 10 with one subdirectory, created before this staging. K/stage228.py:60-89 only checks the members that a2.tar contains (226 `s/` entries), and K/stage228.py:186-187 only tests `sam_source` with `is_dir()`. Extra or stale files survive extraction. The sealed prepare then pins whatever is present: S/orchard_h10/prepare.py:46-50 builds the manifest from `rglob` over `sam3_source=d/s`, so those files enter the reader's SAM3 import root and `artifact_manifest_sha256`, which is unchecked (finding 2).

   Smallest fix: in `stage_check`, refuse when any file under `d/s` (and the other archive destinations) is absent from the INPUT_EXTRACTION inventory and is not a known prepare product. Alternatively, have the coordinator move d/s aside before extraction; moving needs no deletion.

4. MEDIUM. The runtime path remap edits pinned bytes instead of using a package hook. K/runtime228.py:95-125 (paths at line 112) rewrites `d/v/py` and `d/v/boot.py`, which are authenticated a4.tar members, and also the base `pyvenv.cfg`. On Orchard the same mapping came from the package's own bwrap namespace (`orchard_job.namespace`: sj, fsw, m/ap and the uv cpython binds), and `inputs['python']` is pinned in a/1.json, so no config hook exists. This misses check 1 ("remaps only through the package's config hooks"). Mitigations: no sealed reader or h1eval file changes, the originals and both hashes are kept, and the rewrite refuses if `/lustre/` or `/home/` remain. A wrong relocation fails at the import probe or produces divergent rows. It cannot fake a match once finding 2 is fixed.

   Smallest fix: record an explicit coordinator or user ruling that accepts this deviation (or stage the bwrap pin and run the worker inside `orchard_job.namespace`). Also copy RUNTIME_RELOCATION.json into `ret/metadata` so the comparison shows the before and after hashes.

5. LOW. The comparator ignores the run's own failure status. K/runner228.py:109 marks a telemetry failure "run is diagnostic-only" and K/runner228.py:115-127 records `failure` in ALLOCATION/SUMMARY, yet K/compare228.py never reads `ret/SUMMARY.json`, `FAILED.json` or `ALLOCATION.json` (see the probe above).

   Smallest fix: in `compare()` on the trinity side, add a reason unless SUMMARY `failure is None`, `completed>=50` and no FAILED.json exists.

6. LOW. The reference is pinned only by its rows. FIRST50.json fixes `orchard_prefix_sha256` and EXPORT_PIN, but the reference journals' environment.json and IDENTITY are trusted as found. If they are edited together with the candidate, the result is still SAME_INSTRUMENT (probe above).

   Smallest fix: add the sha256 of `reference/metadata/IDENTITY.json` and of each reference `journals/*/0/environment.json` to FIRST50.json, and check them in `compare()`.

7. LOW. The worker imports differ from Orchard. K/worker228.py:22-23 appends `--settings`, which triggers the `S/h1eval/__init__.py` native-tree branch: sys.path gets p/tree first, and `student_pilot` is imported early. Orchard's worker argv at import was `[5.py, 30.json]`, so Orchard never took that branch, and the comment "supported settings hook" is inaccurate. I checked that p/tree shares no module names with p/b or reader_core, so this is benign today.

   Smallest fix: drop the `--settings` append, or record it as a deviation in LOCAL_RUN.json and correct the comment.

8. LOW. The control wrappers leak HOME and TMPDIR. K/run228.sh, K/read228.sh and K/compare228.sh set only `CUDA_VISIBLE_DEVICES=""` and the thread counts. HOME, the XDG caches and TMPDIR are set only by K/coordinator228.sh:16-22, so the documented `bash read228.sh ...` path runs the control process with HOME=/home/jjyeung and TMPDIR=/tmp. The worker environment is clean (K/common228.py:76-88).

   Smallest fix: export the coordinator228.sh:16-22 block, plus `TMPDIR`, in all three wrappers.

9. LOW. OOM detection is too narrow. K/observe228.py:6-8 matches only `torch.cuda.OutOfMemoryError` or the text "cuda out of memory". "CUDA error: out of memory" and `CUBLAS_STATUS_ALLOC_FAILED` still stop the run (rc 1) but are not labelled OOM and do not write OOM.json.

   Smallest fix: also match `'out of memory'` and `'alloc_failed'` in `str(error).lower()`.

10. INFO.
    - coordinator228.sh never runs `unpack_return.py`. That script requires `--out` inside the kit directory, so the coordinator needs one extra manual step for corpus ingest.
    - The EXIT receipt status is `FAILED` even for a clean 50/636 prefix with rc 0 (K/return228.py). Ingest must read SUMMARY rather than EXIT.
    - The vnice terminator writes `/tmp/terminator` on 2-28. This is cluster-mandated and the only write outside /scratch. vnice.sh and terminator.sh are read from /data3; both are small, read-only and sha-checked.
    - Worker audit write roots (XDG_CACHE_HOME=out/cache) are a superset of Orchard's. Telemetry writes happen outside the audit window.
    - The gate cannot stop another user from taking the card after the second reading. The compare's host and card checks are consistency checks, not attestation.
    - Placing a/6 requires the kit at exactly `/scratch/jjyeung/orch_n30/reads228/kit`.
    - The footprint estimate (124.2 GB) excludes the prepare outputs. These are symlinks (S/b/parity_kit/stage_restore.py:137-150), so the omission is safe. The `stage_check` hard limit of 145 GB applies regardless.
    - `storage_proof` runs only after the 300 s gate (K/runner228.py, inside the lock). A non-local /scratch would be refused late, but the gate still fails closed.

## The seven checks

1. Sealed entry, config, item order and decoding: satisfied. The kit calls `operator.run`, then the sealed `runner.run(launcher=...)`, `entry.py` and h10 `launch.main`. It uses the sealed 30.json, items and max_new_tokens 16384, and edits no sealed reader bytes. Exceptions: the remap edits pinned runtime bytes (finding 4) and the import path deviates (finding 7).
2. Card gate: satisfied. It takes two readings at least 300 s apart on a monotonic clock with the same UUID, under 100 MiB, with no process, Ada 48–50 GB, a UUID flock, `CUDA_VISIBLE_DEVICES=<uuid>`, and vnice with sha pins. Any nvidia-smi or parse error exits non-zero.
3. Memory: satisfied, apart from finding 9. Allocated and reserved peaks are recorded per item and at load, nvidia-smi is polled every 1 s, and the first OOM stops the run with rc 42 and no retry.
4. Return layout: satisfied. The tests run the unchanged unpack_return.py against the partial envelope, and the return keeps the Orchard layout.
5. Compare: answers use the h1eval `answer_text` rule, placement is exactly (index, family, call, served, at_token), and the ruling is `answer>=49 and placement==50`. Findings 2, 5 and 6 are loopholes in eligibility, not in the ruling itself.
6. Pins and budget: satisfied, with one gap. Pins match a/1.json and the kit fetches nothing. The budget of 124.2 GB is an estimate below 150 GB, enforced at 145 GB. The pre-existing d/s is the gap (finding 3).
7. Writes: satisfied for the coordinator path. All writes go under /scratch/jjyeung, apart from /tmp/terminator (INFO). The direct wrappers leak HOME and TMPDIR (finding 8).

First review (so_cr_reads228): HIGH 1–4, MEDIUM 5 and LOW 6–9 are all addressed in code and covered by the regression tests. The only part not yet verifiable is the runtime half of HIGH 1, because the bytes are absent (finding 1).
