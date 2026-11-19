VERDICT: GO

Fifth independent review of the trinity-2-28 reader kit (`/scratch/jjyeung/orch_n30/so_reads228/out`, after `_fix4`). The coordinator can stage onto trinity-2-28 and run the 50-item OFF device check on one RTX 6000 Ada 49 GB card with this kit, and can trust the comparison. There are no HIGH or MEDIUM findings. One LOW finding is a test-coverage gap, which I closed by hand. Everything else is INFO. Every finding from reviews 1–4 and the target refusal is fixed as decided.

## Evidence run by this review (CPU only, writes only under `so_reads228/work/cr5_tests/`)

- **Full suite passes (rc 0, 140 tests).** Log: `work/cr5_tests/run_tests.log`.
  - test_kit 39, test_review 18, test_prepare 7, test_review2 17, test_stage2 12.
  - test_bootstrap36 7, run under the real `/usr/bin/python3` 3.6.8.
  - test_review3 19 and test_target_refusal 21, both run with `-S`.
  - The `out/` manifest was identical before and after the run (1222 entries).
- **`DELIVERY_MANIFEST.json` matches `out/` byte for byte.** I ran the exact check from `COORDINATOR.md:37-52`: 1221 files, 73,015,962 B, no set difference, no hash mismatch and no symlinks.
- **The real code paths pass under 3.6.8.** `validate_registry(STAGE_PLAN)` covers 10 namespaces and `deployment(A10b)` passes. A zero-body `preflight_runtime` over the real r0/r1/r2 lists accepted all 115,837 members in 19.5 s and created nothing.
- **The r228 lists are clean.** After gunzip they match the hashes in `evidence/runtime/r{0,1,2}.list`. They contain no hardlinks, no backslash or non-ASCII names, and no overlap between r0, r1 and r2. The only absolute links are the 2 registered ones.
- **The reference re-derives from the mirror `ret/`.**
  - The FIRST50 prefix sha, the ID order, the 636-item `full_order`, both reference pins and the kit's reference rows all match.
  - EXPORT_PIN, INPUTS (identical to `a/1.json`), RETURN_ID and CARDS match byte for byte.
  - SUMMARY shows 636/636 with `failure` null. The first 50 items end 49 by eos and 1 by max_calls.
- **The kit's return has the same layout as Orchard's.** Orchard's `package/a/f/0.tgz` holds the five type journals. A 50-item run creates only the type-3 journal, because `launch.py:367` breaks after a partial type. `unpack_return` accepts that layout, and test_kit/test_review cover it.

## Checks

1. **PASS: entry, config, order and decoding are sealed.** The operator calls sealed `tower_sequence.run` → `runner.run` → `entry.py` through runpy. The sealed 9.json gives budget 18000 s with stop/return margins of 1800/1200 s. Remaps go only through the package's own `namespace()`, with the private bind at `namespace228.py:32-53`. The ON overlay applies only with `--on`.
2. **PASS: the card gate fails closed.**
   - `gpu228.py:33-49` requires two readings at least 300 s apart on the monotonic clock, under 100 MiB used, no processes, and the name "RTX 6000 Ada" with 48,000–50,000 MiB.
   - `runner228.py:58-61` takes a UUID flock. CUDA_VISIBLE_DEVICES is set to the UUID.
   - `worker228.py:33` requires exactly one Ada device. Everything runs under vnice through sealed `runner.run`.
3. **PASS: memory is recorded and the run stops cleanly on the first OOM.**
   - Each item records peak allocated/reserved memory to `memory.jsonl`, and a 1 s nvidia-smi sampler runs alongside.
   - `observe228.py:7-37` and `worker228.py:64-68` write OOM.json and STOP, and the run ends with rc 42 (`runner228.py:112`). An OOM during load also gives 42.
   - The sealed reader has no handler that swallows exceptions on the item path (checked in `e2e_reader/parity.py` and `artifact.py`).
4. **PASS: the return layout is accepted.** The unchanged `unpack_return.py` (pinned in A10b_PINS) is called by `coordinator228.sh:64-65`. The return carries `projection.json` and `IDENTITY.json` from sealed `runner.run`.
5. **PASS: the compare is correct and the ruling has no loophole.**
   - The ruling at `compare228.py:173` is eligible AND answers ≥ 49 AND placements == 50.
   - Eligibility requires all of the following. A missing, reordered or duplicated row can't pass.
     - every pin;
     - the first 50 IDs, with the return a prefix of `full_order` (`:104`);
     - whole binding and settings equality;
     - OFF settings, SUMMARY failure null and no FAILED.json;
     - backend, host and mode correct (`:131-138`);
     - `RETURN_ID` ≠ 173060 (`:142`).
6. **PASS: pins, budget and the prior findings.**
   - Budget: estimated peak 94.5 GB against a 150 GB limit and a 145 GB footprint cap. The free-space floor is 200 GiB (`stage228.py:288,327,349`). `MISSING.json` has `fetch_allowed=false`.
   - The private_rt and namespace rules are covered by named tests:
     - two passes that write nothing on refusal: `test_target_refusal.py:68-127,245,261`;
     - `x/` is never bound;
     - the operator runs in the namespace with `d/v/py` and `d/q/vnice.sh`;
     - the import probe runs before the gate, including a case without p1cpu: `test_review3.py:71-104`, `test_prepare.py:98`;
     - the name is checked before the gate: `runner228.py:46-53`, `test_review3.py:139-149`;
     - the private logical root is bound: `test_review3.py:164-209`;
     - the other lane's `d/k` and `d/s` are never read or overwritten: `test_stage2.py:39-72`, `test_target_refusal.py:198`.
7. **PASS: no writes to /home or /data\*.** The control environment pins HOME, TMPDIR and all caches under `/scratch/jjyeung/orch_n30/reads228/control`. The namespace exposes no `/data*`, and `/home/jjyeung` inside it is an empty tmpfs. The only write outside /scratch is the cluster-mandated vnice terminator in /tmp (finding 8).

## Findings

1. **LOW: the 3.6.8 bootstrap tests don't reach the real stage entry.**
   - Evidence: `coordinator228.sh:32-41` runs `stage228.py --verify-runtime-pins/--extract-runtime/...` under `/usr/bin/python3` 3.6.8. `test_bootstrap36.py:46-67` only calls `R.extract_runtime` with a hand-built `namespace_map`. It never runs `validate_registry`, `preflight_runtime` or `S.main([...,'--extract-runtime'])`. I verified by hand that these pass under 3.6.8 (see Evidence).
   - Smallest fix: add one bootstrap36 test that runs `validate_registry(STAGE_PLAN)` and `S.main([fixture_package,'--extract-runtime'])` against a small fixture registry.
2. **INFO: in `all` mode the sealed name check runs after staging.**
   - Evidence: `coordinator228.sh:11-16` only applies a character regex. Sealed `opaque()` (`runner228.py:47-48`) runs after staging. A name with a banned token such as `sam`, `room` or `head` would be refused only after staging, though still before any card or run directory. The documented flow uses `--stage-only` and then `--run-only` with `a400check1`, which passes.
   - Smallest fix: none needed. Optionally call `opaque()` in `--run-only` before the stage rehash.
3. **INFO: the NVIDIA driver version is not checked.**
   - Evidence: the reader uses torch 2.13.0+cu130 (`evidence/runtime/r1.list`, `REPORT.md:240`), which needs driver ≥ 580. `gpu228.py:31` records `driver_version` but nothing checks it. An old driver fails closed at `worker228.py:33`, but only after staging and the 300 s gate. trinity-1-18 runs 595.71.05; 2-28 is unverified.
   - Smallest fix: in `require_idle`, refuse when the driver major version is below 580.
4. **INFO: bwrap creates mount-point directories on the host inside `private_rt/sj`.**
   - Evidence: `namespace228.py:42-61` binds kit2, prepare, operator_probe, namespace_probe, `runs/<name>` and b01ec87a6f29b. These are empty, private directories, and `unexplained()` skips directories.
   - Smallest fix: none.
5. **INFO: absolute symlinks from prepare point at the other lane's tree.**
   - Evidence: `stage_restore.py:143-150` makes absolute links in private `d/e`. On the host they point into the other lane's `/scratch/jjyeung/b01ec87a6f29b`. Host code only calls lstat/readlink on them (`stage228.py:154-167`).
   - Smallest fix: none. Keep host-side code from following them.
6. **INFO: the worker's environment differs from Orchard's.**
   - Evidence: the worker uses cwd `out/`, caches under `out/cache` and 4 threads (`common228.clean_environment`). Orchard ran from `metadata/a`. The sealed `environment()` opaque check still runs. No numeric effect is expected.
   - Smallest fix: none.
7. **INFO: the observer's generator wrapper has no `close()`.**
   - Evidence: `launch.py:368-370` closes only generators that have a callable `close`, so `CappedGenerator.close` is reached only through garbage collection. The 50 rows are unaffected.
   - Smallest fix: forward `close` in the wrapper.
8. **INFO: carried forward from earlier reviews.**
   - The UUID flock does not reserve the card against other users (`runner228.py:57`). The second reading narrows that window but cannot close it.
   - The vnice terminator writes to /tmp.
   - The ship command at `COORDINATOR.md:24` is plain `ssh`. The prose at `:18` routes it through the rate limiter, so wrap it in `lanes/tools/trinity_ssh.sh` literally.
   - The 10.5 GB runtime is rehashed several times, which costs time only.
   - A DIAGNOSTIC result exits rc 1 after `CORPUS_INGEST.json` (`coordinator228.sh:59-60`), as designed.
