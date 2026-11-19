VERDICT: GO

TL;DR: The coordinator can stage the kit onto trinity-2-28 and run the 50-item OFF device check on one RTX 6000 Ada card, and it can trust the comparison. I found no HIGH or MEDIUM issue. Every finding from the three prior reviews is closed. The findings below are LOW or INFO; none of them blocks the run or changes how the ruling reads.

Reviewed: `/scratch/jjyeung/orch_n30/so_reads228/` (the four prompts, the three prior verdicts, `out/REPORT.md`, every `out/*.py` and `out/*.sh`, `STAGE_PLAN.json`, `tests/`, and the sealed `out/A10b/src` and `out/A10b/package`). Paths below are relative to `so_reads228/out/` unless stated otherwise.

## Findings

1. **LOW: runtime extraction can add files to shared `/scratch/jjyeung` before it refuses on a conflict.**
   - Evidence: `STAGE_PLAN.json:364-368` maps `sj` to the shared `/scratch/jjyeung`. `runtime228.py:54-95` creates missing directories and files as it streams. Conflicts are collected and refused only after the loop, at `runtime228.py:99`.
   - An existing file is never overwritten, because existing files are opened `rb` and compared (`:79-89`). All writes stay on `/scratch`.
   - Current exposure is low. On 2-28, `/scratch/jjyeung/envs` holds only `sam3_capretry_native_v1` and `sam3_scipy_ovl` (`r228_lists/envs.txt`).
   - Smallest fix: compare all members in a first pass, before any write, or list the files that stay behind in the refusal receipt.

2. **LOW: `test_bootstrap36` does not run under Python 3.6, though its docstring says it exercises the 3.6.8 interface.**
   - Evidence: `tests/test_bootstrap36.py:1` makes the claim, but `tests/run_tests.sh:16` runs it with the p1cpu Python 3.12.
   - I ran it under the real `/usr/bin/python3` 3.6.8 and all 7 tests passed. `deployment()` and the imports of stage228, namespace228, inventory228 and runtime228 also worked under 3.6. The defect is only in the test harness.
   - Smallest fix: run line 16 with `/usr/bin/python3 -I -s -B` when that interpreter is present.

3. **LOW: a `--run-only` launch rehashes about 50 GB of staged data before the idle gate.**
   - Evidence: `runner228.py:52` calls `stage_check(...,prepare=True)` before `snapshot`/`idle_gate` (`:58-63`).
   - This adds minutes of local scratch IO between "the card looked free" and the first gate reading. It has no correctness effect and fails closed.
   - Smallest fix: none required. Tell the coordinator to expect this delay.

4. **INFO: `operator228.execute` does not call `install_process_guard`.**
   - Evidence: `operator228.py:28-75`. Orchard's operator calls it at `A10b/src/orchard_h10/job.py:142-143`. The worker still installs it through the sealed `entry.py:10`.
   - It affects process hygiene only, not decoding.
   - Smallest fix: call `orchard_h10.common.install_process_guard(out)` at the top of `execute`, or record the omission in REPORT.md.

5. **INFO: preparation runs with 4 threads; Orchard ran it with 16.**
   - Evidence: the kit uses `common228.py:80-81`, while Orchard used `job.py:178-179`.
   - The worker uses 4 threads on both sides (`runner.py:87`). Preparation only restores files and makes an exactness check, so the thread count cannot change any read.

6. **INFO: the idle gate cannot reserve the card.**
   - Evidence: `gpu228.py:40-51`. Trinity has no scheduler, so another user can take the card between the second reading and model load.
   - A late arrival is visible in the 1 s `Sampler` log and in `memory.jsonl`, and an OOM stops the run with rc 42 (`OOM.json` plus `STOP`).
   - Smallest fix: none. The coordinator should read the sampler log before trusting a DIAGNOSTIC result.

7. **INFO: the run writes to `/tmp` on 2-28.**
   - Evidence: the sealed namespace binds `/tmp` read-write (`A10b/src/orchard_h10/vendor/orchard_job.py:118-137`), and the cluster's own `d/q/vnice.sh` terminator writes there.
   - Nothing is written to `/home` or `/data*`, and Orchard behaved the same way. Every write the kit itself makes (TMPDIR, caches, HOME, outputs) is on `/scratch`.

8. **INFO: the ship command uses plain ssh, not the rate limiter.**
   - Evidence: `COORDINATOR.md:24` pipes `tar` into `timeout 600 ssh -o ConnectTimeout=20 trinity-2-28.ib`, not through `lanes/tools/trinity_ssh.sh`.
   - This is the text fix3 decided on, and the copy goes node to node over InfiniBand.
   - Smallest fix: the coordinator runs it through the limiter, as one call.

9. **INFO: two exit codes the coordinator should read correctly.**
   - A DIAGNOSTIC result ends `coordinator228.sh` with rc 1, after `CORPUS_INGEST.json` is written (`ingest228.py:29`, `coordinator228.sh:68`). This is intended and is not a crash.
   - An `nvidia-smi` failure raises `CalledProcessError`, `ParseError` or `TimeoutExpired`. None of these is in the caught set at `runner228.py:132`, so the run prints a traceback and exits rc 1. It still fails closed.

## The seven checks

1. **PASS: sealed reader with the same entry, config, order and decoding.**
   - The worker runs the sealed `entry.py` through `runpy`. The prefix is the sealed `['bash', d/q/vnice.sh]`, and `worker_args` and `launch.main` are unchanged.
   - Remaps happen only through the package hooks: `load_native` wrapping, the commit-record stop, and the per-item memory hooks outside the audited `generate` window (`artifact.py:253-305`).
   - The 1161-file `DELIVERY_MANIFEST` matches exactly, and the A10b tree matches the mirror.
2. **PASS: card gate, CUDA_VISIBLE_DEVICES and vnice all fail closed.**
   - The gate requires the name 'RTX 6000 Ada', 48000-50000 MiB total, under 100 MiB used and no processes, on two readings on a monotonic clock at least 300 s apart with the same UUID (`gpu228.py:40-51`). It holds a flock on the UUID.
   - Control processes export `CUDA_VISIBLE_DEVICES=''`. The operator and worker get the card UUID, and `worker228` requires exactly one 'RTX 6000 Ada' device.
   - `vnice.sh` and `terminator.sh` are checked against their pins (`operator228.py:36`).
3. **PASS: memory recording and the stop at the first OOM.**
   - Each item resets the peak counters and synchronizes, then records max allocated and reserved in `telemetry/memory.jsonl`. `nvidia-smi -l 1` samples throughout.
   - An OOM (`OutOfMemoryError`, 'out of memory' or 'alloc_failed') leaves the reader uncaught, writes `OOM.json` and `STOP`, and exits rc 42. The coordinator stops on that rc under `set -e`.
4. **PASS: the return layout is accepted unchanged.**
   - `package_return` writes `result.tar.gz` (files only, no symlinks, under 90 MB) and an `EXIT.json` with schema a3. The unchanged `unpack_return.py` takes it through `unpack228.py` after the pin checks.
   - Ingest reads SUMMARY, not EXIT.status, which is FAILED for a clean 50/636 run.
5. **PASS: the compare is correct and the ruling has no loophole.**
   - Placement is (index, family, call, served, at_token), and answers follow the sealed `answer_text` rule.
   - The IDENTITY, environment, binding and settings dicts are compared whole. The first 50 IDs and their order, the schedule prefix and the export hash (content-based) are pinned.
   - The candidate must have LOCAL_RUN, CARDS showing the Ada card, journal host trinity-2-28, a RETURN_ID other than 173060, SUMMARY failure None with at least 50 completed, and no FAILED.json.
   - Ruling: `eligible and answers>=49 and placement==50`. Empty, torn, duplicate, shard or fixture returns are refused, and a missing item makes the run ineligible.
   - I re-derived `FIRST50` and `reference/` from the authenticated `package/a/f/0.tgz` (77 members). The prefix sha 61b385f8…, both reference pins, EXPORT_PIN, INPUTS, RETURN_ID, CARDS, the 50 rows, `full_order` (636 items) and the first-50 IDs all match.
6. **PASS: staged files and pins match A10b, the budget holds, and nothing is fetched.**
   - Archives a0-a5 equal the `a/1.json` archives (path, bytes, sha, expanded size, destination). The runtime archives r0-r2 equal the ORCHARD_ASSETS groups, and all 13 expanded files equal the `a/1.json` files.
   - The planned footprint is 124.2 GB against a 145 GB check (`stage228.py:302-304`) and a 150 GB limit, with a 200 GiB free floor.
   - `MISSING.json` lists 13 parts (10.5 GB) with `fetch_allowed: false`.
   - All prior-review fixes are confirmed:
     - The operator runs in the package namespace with `d/v/py` and the `d/q/vnice.sh` prefix (`namespace228.py`, `operator228.py`).
     - The import probe runs before the gate (`runner228.py:53`). `test_review3` proves it under `-I -S`, without p1cpu packages.
     - The opaque name is checked before the gate, in `coordinator228.sh:11-16` and in `runner228` before `mkdir`.
     - The private logical root is bound in the namespace (`namespace228.py:42`). A real-bwrap test passes.
     - Another lane's `d/k` and `d/s` on 2-28 (`r228_lists/existing_d.txt`) are hidden by the bind and never read or written. Host code goes through `host_path`.
   - The preparation-product allowlist (`inventory228.py:21-35`) matches what the sealed `stage_restore` writes. The `p0/*` files come from a5 (`a/6`): 20569 + 73933 + 86401 = 180903 B. `inputs.optional` is absent, so no `8.json` is written.
7. **PASS: no writes to `/home` or `/data*`.**
   - Every kit write is under `/scratch/jjyeung/orch_n30/reads228`. Runtime extraction may also write under shared `/scratch/jjyeung` (finding 1).
   - The only other write is the cluster terminator's `/tmp` write (finding 7).
   - The control environment puts HOME, TMPDIR, XDG, the caches and USER on `/scratch` and unsets LD_LIBRARY_PATH, PYTHONPATH and H10_SETTINGS.

## Evidence I ran (all CPU, writes only under `so_reads228/work/cr4_tests`)

- `READ228_TEST_WORK=.../work/cr4_tests bash tests/run_tests.sh`: 119 tests in 7 suites, all OK. The log is `work/cr4_tests/run_tests.log`, and nothing was written under `/scratch/jjyeung/orch_n30/reads228`.
- `test_bootstrap36` under `/usr/bin/python3` 3.6.8: 7 OK.
- I compared the pins against `a/1.json`, `ORCHARD_ASSETS.json` and `DELIVERY_MANIFEST.json`, and re-derived FIRST50 from the authenticated `package/a/f/0.tgz`. All checks matched.
