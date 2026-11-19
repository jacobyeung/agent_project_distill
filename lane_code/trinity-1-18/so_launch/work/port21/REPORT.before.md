VERDICT: PARTIAL Findings 1–7 have code or design fixes and passing CPU regressions; the required Orchard reuse-floor measurement remains unavailable under this dispatch.

Patch 03 ranks first; application order is **03, 04, 02** after N's first proof and a rebuilt, rescanned kit. Every switch defaults OFF. **01 stays OFF: it cannot hit in the production topology in a way that avoids native work.** Its estimated production saving is zero or worse. No production speedup was measured.

The builder fixes `run_directory=/tmp/jjyeung/okit_8865619b/runs/<run_key>` (`in/tree/work/tree_r1/launch_s1/build.py:221`); `b/g.py:66` requires node-local run storage. A complete same-node journal already supports native reuse. Another node lacks the source; another logical run changes the config/key. Defensive relocation fixtures do not establish a useful production HIT.

The [so_xstore design](CROSS_RUN_STORE_DESIGN.md) specifies external GCS sessions, verified login-node cache publication, portable phase identities and exact derived-config/preparation checkpoint bindings. Its planning estimate is **about 70 min, the prepare half, until measured**, before fetch, full SHA and adoption costs. Node-local frame work remains necessary. Estimated effort is **13–22 engineering days plus 1–2 reviewer-days**. This package neither implements nor approves the store.

## Measured phases and preparation inputs

Mode p measured **140.57 minutes in job 172660** and **145.27 minutes in job 171377**. The [interval arithmetic](phase_timing.json) retains timestamps and evidence labels; [numbered log excerpts](evidence/startup_log_excerpts.txt) retain the raw evidence. The source logs are `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/r1_ops6/work/mon/last.txt` and `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/look1.out`. Preparation mtimes and C' step duration also use the supplied `PROMPT.md`. Measured envelopes overlap where stated and must not be added blindly. Table source paths refer to the input tree; trainer code is unchanged.

| Phase | 172660 minutes | 171377 minutes | Evidence | Reads and writes | Pure function of named inputs? |
|---|---:|---:|---|---|---|
| Submission to wrapper | 2.27 | unavailable | Supplied submission time and measured wrapper start | Allocation availability; starts wrapper | No; scheduler and host state. |
| Wrapper to import stage | 0.17 | 0.03 | Measured timestamps | Staging inventory and export-session setup; wrapper log | No; filesystem/runtime state. |
| Import preflight | 1.22 | 0.60 | Measured; logs report 73 and 36 seconds | `job.sh`, `b/p0.sh`, `b/p0.py`: sealed kit, venv, trainer, neutral runtime record, NumPy/FLA overlays; writes import reports for p/t/u | Import acceptance depends on these identities and runtime; report timing is not pure. |
| Preflight PASS to first stage prep | 11.25 | 0.02 | Measured gap; hashing attribution inferred | Three full checkpoint checks through the guard, chooser and recursive preparation guard | No; checkpoint inventory, locks and I/O state. |
| Model, store and archive staging before frames | 7.60 | 7.27 | Measured envelope | `b/c.sh`: venv/closure/trainer archives, base model, small metadata, receipt/database parts, extra archives, art assets; writes node-local union tree and stamps | Payloads are content-bound; execution and stamps depend on existing pool state. |
| Frame-bundle staging and verification | 23.87 | 23.35 | Measured envelope, including extraction | `b/c.sh:184`, `b/f2.py`, `b/s.py`: frame archives, shard inventories, f3–f14 manifests/store mapping; writes RGB files, import receipts and stamps | Verified bytes depend on manifest/archive pins; extraction time and whether work runs are not pure. |
| Init mirror | 0.25 | 0.25 | Measured envelope | `b/c.sh:217`: pinned init artifact and export member hashes; writes verified mirror | Payload yes; mirror location and completion marker depend on pool state. |
| Native CPU preparation, entire mode p | **140.57** | **145.27** | Measured launch-p to exit | `b/w.py:34`, `student_pilot/s1_admission.py:132`: input config, all stream receipts and dependencies below; writes native phase journals, prepared stores/config and frame inventory | Semantic selections are input-bound. Receipt bytes also contain UUID paths, timings, resources and resolved paths. |
| Within p: start to preparation result | 70.37 | approximately 73.20 | Inferred from supplied mtimes; A's completion time is approximate | Parent metadata/confusers, pointing/VQA rebuilds, routing materialization/composition, native preparation; writes `prepare_<uuid>/` | Same qualification as mode p. |
| Within p: result to mode-p exit | 70.20 | approximately 72.07 | Inferred residual, not an isolated frame measurement | `run.prepared`, retained-row traversal, frame existence checks, SQLite inventory/ref counts and fixed SHA samples; writes `frames_<uuid>/` and `data_receipt.json` | Acceptance is input-bound; timing, SQLite artifacts and paths need not be byte-deterministic. |
| Mode-p exit to second stage | 1.43 | 0.02 | Measured gap; hashing attribution inferred | Parent resume guard performs the fourth full checkpoint check | No. |
| Second stage prep | 2.37 | 2.13 | Measured envelope | Repeats staging entrypoints; `b/s.py` checks existing packages/files/rasters and frame shards; init mirror usually present | Acceptance is content-bound; execution depends on pool state. |
| Training launch to binding mirror | 10.93 | 9.10 | Measured timestamps; overlaps the beginning of the first optimizer step | Distributed startup, preparation authentication, processor/model/init loading, wrapping, optimizer creation/restoration, run binding; wrapper copies binding | No; includes hardware/runtime work and durable state. |
| First actual optimizer step | approximately 7.22 | 7.34 | C': supplied 433 seconds. A: raw metric 440.3–440.4 seconds | Native rows/RGB/masks, model and optimizer; updates parameters/state and writes all-rank first-step admission | No; hardware and state matter. |
| End-of-job slot copy, then destination verification | unavailable | 7.78 + 7.52 | Measured: 467 + 451 seconds for 113,540,341,760 bytes | External wrapper copies checkpoint to slot A, then verifies destination | Verified content is input-bound; elapsed time and publication state are not pure. |

Patch 01's key contains the exact input config-file pin, the complete parsed config, stream receipts, all frame manifests, complete staging identity, trainer/wrapper/code identity, admission contract and relevant environment. It retains run paths deliberately; it is not a portable native preparation identity. The following audit explains coverage for this version, not a future general cache guarantee.

| Preparation input or dependency | Reader | Key coverage and admission limit |
|---|---|---|
| Original configuration and every setting, including output/preparation paths, recipe, seed, world size, frame layout/markers, pixel/sequence settings, route table, filters and optional feature blocks | `s1_admission.admit`; `carrier_c1_run.validate/prepare` | Entire parsed configuration is `preparation_config`; its launch pin is checked before forming the key. No field is excluded to improve hit rate. |
| Pose, pointing, VQA, routing and optional MDG source receipts | `s1_admission.py:181`; `carrier_c1_run.py:482` | `store_receipts=cfg.streams`, also contained in the full configuration. |
| Original SQLite rows/targets, divisions and parent-division ancestry, source memberships, pose mix sources and clip/dense plans | `carrier_c1_data.build_stream`; `c1_pose_mix.prepare`; `r1_routing.compose_native` | Their SHA pins occur in the source receipts or in config. Hashing the parent receipt binds its nested expected hashes; a changed valid child requires a changed parent/key. Prepared local copies also enter the published file inventory. |
| Pointing GT raster bytes and raster key, per-row geometry and shape/quality rules | `carrier_c1_data.py:513`; `ground_target_filter`; `build_stream` | Raster SHA/key are in pinned database rows; thresholds/filters are in config or the sealed preparation implementation. |
| REMOVE lists and defect restrictions | `row_removals.Removals`; pointing/VQA/routing preparation | Config contains each path, SHA and restriction. Path-only REMOVE lists are refused by the cache and use native preparation. |
| Dev/benchmark/pose/report exclusions, held-out QIDs/sources, scene-coverage reference and source mapping | `s1_exclusions.Exclusions/apply`; `carrier_c1_run.prepare` | Config pins/values and receipt ancestry bind every authority. Packaged reserve-scene data such as `r0_scenes.json` belongs to the trainer archive identity. |
| Routing selection/manifest, eligible packed/row sources and selection indices, source exclusions, relocation catalog, candidate manifest | `s1_routing.py:202`; `s1_pool_relocate.relocate`; `s1_pool.selected_rows` | `cfg.s1_routing` and its pinned selection/manifest closure. Catalog destinations are also included, even when bytes match. |
| Routing frame map/plan, FPS authority and frame counts; source-row scene/FPS metadata | `s1_routing.Frames`, legacy routing database traversal | Config pins bind map, plan and optional FPS authority; legacy database pins bind source metadata. |
| Base-model manifest, architecture and tokenizer/processor metadata/files | `mdg_parent.bind`; `s1_routing`; `carrier_c1_run.prepare` | Pose-source receipt points to the base manifest, whose file hashes bind metadata. `staging` also contains model/runtime archive identities. |
| Parent init artifact, full-weight manifest/index, selected embedding shard, parent heads and MDG init weights | `mdg_parent.py:23`; `carrier_c1_run.validate_init` | Config init pin plus artifact/export nested pins; current staging/init identity also enters the key. The no-MDG branch reads metadata without loading parent weight payloads. |
| MDG clips and optional clip-source manifest, scene identity map, raster/frame manifests, per-clip raster hashes, vocabulary, confusers, stem weights, exclusions and init metadata/weights | `stageb_mdg.inputs/prepare`; `mdg_inputs`; `mdg_parent.bind` | Full MDG block and transitive manifests/payload pins. Cache admission requires pinned file inputs, `{root, manifest}` directories and pinned init members. Mutable path-only variants are refused. Literal exclusion lists are already part of config. |
| Optional validation rows/slice, depth-init metadata and paired-layout partner pins | `carrier_c1_run.prepare_validation/prepare`; `carrier_c1_data.layout_inputs` | Config pins and pinned row/receipt closure. |
| R1 registry/evidence, row-source catalog and membership, mixture/sampling bindings and hand-over/persisted-file mapping when used through S1 | `r1_training`; `r1_components`; `r1_routing`; `r1_handover` | Entire optional config blocks and their pinned nested records. This does not adapt `launch_r2`'s separate host-preparation receipt. |
| All frame bytes reused by the cache, fN manifests, store mapping and archives | `b/pc.py`; native frame audit | `frame_manifests` plus entire `k/0.json` as `staging`. Publication requires every retained logical frame in the native SQLite inventory to be covered. Noncanonical/uncovered frames decline publication. Every reused RGB file is SHA256-checked. |
| Trainer source, source seal/archive, wrapper and staging implementation, venv/overlays and packaged authorities | `run.authenticate`; `b/a.py`; `b/pc.py.Context` | Preparation code identity contains commit, trainer archive, config code pin and SHA256 of every kit `b/` file. Entire deployment identity also includes venv/closure/overlay pins. |
| Preparation environment and logical-to-physical frame mapping | `b/c.sh:382`; `orchard_paths`; native admission request | Only pass-through rehearsal, CPU-count and hash-seed values enter `environment`; the removed names are not read on this preparation path. `tk_env`'s fixed mount, student ID, frame mapping, init mirror and CPU settings are bound by its wrapper hash. Contract frame roots are also keyed. |

Cache metadata uses a key and per-component SHA256 digests; full components remain in memory for key construction. Schema v2 refuses v1 cache entries. Native prepared/config files remain byte-preserved.

The native preparation path also has mutable journal state. Its `request.json` binds config/source/CPU/frame roots; `PhaseJournal` reuses completed phases, and admission refuses another request. A MISS leaves the destination intact, including a partial or foreign-config journal. Destination quarantine occurs only after a candidate copy fully verifies and immediately before its installation. A failed final rename restores the native destination. A report-write or uncertain-install error exits with a non-MISS status. Cached RGB corruption still invalidates the affected frame files/stamps through the existing staging repair path; it does not rename the native journal.

A verified synthetic copy preserves native receipt bytes. The hit report records source job, paths, key/components, producer receipt pin and verified file/frame counts. A valid destination from another preparation generation remains native because retained checkpoints may bind its UUID paths. None of these checks grants training authorization or replaces actual all-rank first-step admission.

## Launch wins, in priority order

| Patch or candidate | Evidence | Expected saving and limit |
|---|---|---|
| **03: same-allocation checkpoint verification memo** | Four `complete()` calls each hash the 113.5-GB checkpoint. C' has measured 675-s and 86-s guard envelopes. | **Estimate: about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint**. The memo removes three repeated payload reads. The first check and every new allocation still hash fully. |
| **04: phase and lock timing** | Existing logs combine several guards and waits. | Estimate: zero minutes directly. Boundaries in `job.sh` and both recursive/parent `r.sh` guards separate these costs. Logging failure cannot abort a job. |
| **02: parallel frame SHA, optional** | Already-covered f2-only checks take a measured 1–19 s in C' (`last.txt:218–224,232–239`). The 23-minute cold envelope includes extraction. | No useful measured saving yet. Estimate: seconds on the supplied warm checks; storage contention can make it slower. Measure f2 alone on a warm Orchard node before enabling. Four workers by default, capped at eight, at most twice that many pending tasks, and all bytes still hash. |
| **01: prepared-input cache — OFF** | Same node-local source/destination; different-node source absent; new-run key differs. | Estimate: zero minutes or worse. Misses add full publication hashing; same-path hits add hashes to native reuse and hold the stage lock during restore. |
| Second-stage bypass, not built | Measured 142 s in C', 128 s in A. | Estimate: at most 2.13–2.37 min if a future proof removes the whole stage. Shared inputs and full staging closure still need verification. |
| First-step change, not built | A's first step takes 440.3–440.4 s vs 133.14 s at step 200. | About 300–307 s is observed excess, not a demonstrated removable cost. No GPU trace supports changing RNG, sampler, optimizer or admission behavior. |
| Slot-copy destination verification, not built | Measured 467-s write and 451-s verify for 113,540,341,760 B. | The entire verification envelope is 7.52 min; no delivered saving. The external copier is outside this source tree, and destination durability checks remain required. |

The four checkpoint checks explain the **11-minute gap** as an inference supported by code and logs. In the input tree, they run through:

1. `job.sh:16`: `g.py p` → `persistent_launch()` → `r8.main()` → `complete()`.
2. `job.sh:18`: the direct `r8.py` chooser → `complete()`.
3. `b/r.sh:40` in the **recursive** p child: `g.py p` → the same verifier.
4. `b/r.sh:40` in the **parent** u leg: `g.py u` → the same verifier.

C' spent **675 s** between preflight PASS and first stage prep, covering three checks, and **86 s** between p exit and second stage prep, covering one. A had no checkpoint and one second in each gap (`look1.out:280–281,347–348`). The node reports 1842 GiB RAM (`last.txt:163`), which makes page-cache retention plausible but does not measure cache residency. Subtracting that one-second baseline gives an inferred warm pass of about 85 s. Removing three warm passes saves about 255 s, or **about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint**. The conditional upper estimate is 2 × (675 / 3) + 86 = 536 s, assuming the first pass is at least as slow as each later pass. It is not a throughput measurement.

Set `TK_LAUNCH_TIMING=1` on the **first resume** job and retain the four guard envelopes and `.checkpoint-verification/<job>.events.jsonl`. The four-process CPU regression exercises real `g.py.persistent_launch` and the direct chooser; it records `[false, true, true, true]` memo hits and refuses a subsequently corrupted payload. Its tiny fixtures do not measure checkpoint throughput.

Patch 03 binds a memo to job ID, allocation start, host, checkpoint path, binding and validator SHA. It checks marker SHA and dev/inode/size/mtime_ns/ctime_ns for the marker and every payload. New jobs, clock changes, inode replacement, restored-mtime writes, marker/binding changes, purge and malformed memo force full verification or refusal. This assumes cooperating writers keep completed checkpoints immutable; it does not authenticate against a same-user forger or prove immediate ctime updates for arbitrary mmap writes.

## Review round 2: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1 MEDIUM: unsupported adoption saving | Budget only the prepare half; explicitly retain node-local frame audit and the unmeasured complete-journal floor. | Planning/design contract fails on the reviewed text and passes now. [Native measurement procedure](MEASURE_NATIVE_REUSE.md) is delivered but **not run**: no Orchard access or production journal is authorized here. |
| 2 MEDIUM: missing Orchard data channel and identity work | Specify external GCS session issuance, candidate verification/root publication, login-node read-only cache, zero-write job staging, content-derived phase names and exact config/preparation binding; re-estimate effort. | Transport/identity design contract fails before and passes after. This checks design requirements, not a store implementation. |
| 3 LOW: unsupported memo range | Infer three warm passes from the 86-s envelope and 1-s no-checkpoint baseline; state the conditional 536-s upper estimate. | Report/note contract fails before and passes after; four-process guard/chooser regression passes. Production timing remains pending. |
| 4 LOW: real stage-lock timing untested | Execute whole real `c.sh` under `bash -euo pipefail`, with only staging dependencies stubbed. | Coverage contract fails on the reviewed tests and passes now. Prep/preflight ON emit exactly two lock lines and exit 0; OFF output equals input byte for byte. The implementation already worked; the defect was coverage. |
| 5 LOW: offset hunks leave inventory-visible backups | Apply with `--no-backup-if-mismatch` in the note, manifest and verifier. | The documented all-four application leaves `.orig` files before; the same order leaves no `.orig` or `.rej` after. Fresh standalone, recommended and combined trees pass. |
| 6 LOW: inherited `TK_PC_LOCK_HELD=1` skips lock | Export `TK_PC_LOCK_HELD="$$"`; a child accepts it only when it equals `$PPID`. Keep `flock -w 600 7 || exit 75`. | Inherited `1` bypasses contention before; t/u with unset, `1` or stale-PID markers exit 75 after. Recursive and symlink-parent runs still succeed; concurrent preparation remains serialized. |
| 7 LOW: full config copies and method-bearing refusal | Store only key/component digests; compare them on restore. Use generic optional-input errors and catch context refusal before restore starts. | Two new tests fail before and pass after: a method-bearing valid config publishes/restores without copying its fields, changed component digest refuses, and the CLI safely misses without method text or traceback. |

Exact before/after outputs and commands are indexed in [review_round2/INDEX.md](tests/review_round2/INDEX.md). The full final suites include every earlier behavior regression. Documentation and coverage contracts are explicitly distinguished from runtime failures.

## Review round 1: finding -> fix -> test

| Finding | Current invariant and rerun evidence |
|---|---|
| 1 | 01 OFF; production-path/design contract and same-path/purge tests pass. |
| 2 | MISS leaves partial/foreign journals untouched; native reuse/refusal, copy/install failure and report-error tests pass. |
| 3 | 03 first; all four real guard/chooser calls pass with one full verification. |
| 4 | Parent-bound lock marker and 600-s request; symlink, duplicate t/u and concurrent-job tests pass. |
| 5 | Whole real `c.sh` HIT/MISS/error/missing-root matrix passes. |
| 6 | Missing/unwritable timing logs cannot abort; recursive/parent guard events and exit-7 behavior pass. |
| 7 | Full launch-kit, production-import and checkpoint-buffer modules are selected; explicit environment skips appear below. |
| 8 | Unused environment names do not change the key; written cache metadata uses generic component names and digests. |

## Risks, remaining work and detection

The Orchard complete-journal measurement required by finding 1 remains **not done**. This dispatch is confined to trinity-1-18, forbids SSH/Slurm and has no complete production journal. The supplied procedure preserves native hashes and refuses cold phases; use it only in the authorized Orchard namespace with matching CPU bindings and approved full-rehash I/O. This outstanding measurement is why the verdict is PARTIAL. No other HIGH, MEDIUM or qualifying LOW finding is deferred. The review contains no HIGH findings.

The separate so_xstore build owns implementation, two-node determinism, cross-node adoption/restore, transport authorization and independent admission review. Its runtime and effort numbers are estimates. Checkpoint bindings still pin the derived config and preparation receipt; a path or seal change must refuse resume. Preserve native authorization, frame, parent, checkpoint and all-rank first-step gates.

Patch 03 assumes cooperating writers leave completed checkpoints immutable. Its stat guard is not authentication against a same-user forger or a proof of immediate timestamps for arbitrary mmap writes. Reproduced probes force full hashing after chmod, refuse a write during verification, and disable memo hits under a symlinked parent. Check the events file; missing events mean no demonstrated memo benefit. Native loaders still SHA-check shards, replicated payload and RNG before deserialization (`student_pilot/full_ft.py:563–567,603,618`; `carrier_c1_run.py:2063`).

Patch 02 still hashes all bytes and may lose time under storage contention. CPU probes confirm verdict/count parity on deterministic randomized corrupt/missing fixtures and at most twice the worker count outstanding. No production throughput improvement is claimed. Patch 04 adds timing only. OFF-path CPU tests check native command/output behavior, including byte-identical real-stage output. Patch 01 remains OFF despite its defensive fixes; its self-hashed index does not authenticate a hostile writer, and its parent-PID marker prevents accidental inheritance rather than same-user forgery.

This sandbox rejects socket creation with `PermissionError: [Errno 1] Operation not permitted`. A native attempt confirms that checkpoint-buffer `setUpClass` cannot start. The supported gate explicitly skips those ten Gloo tests plus one unstaged authenticated-pool test. The reviewer reports Gloo success in its own environment; this run does not count that as reproduced evidence. Five native admission-fixture failures match exactly on input and patched trees, so they remain an input-fixture limitation.

No Git, SSH, Slurm, GPU, paid API, production job, heavy dataset I/O or file deletion ran. No other agent's work was stopped. Tests retain small local fixtures, hide CUDA and inherit nice level 10 and eight-thread CPU library limits. The failed socket attempt was an environment refusal, not a cluster-killed job. Network access read only official library documentation.

## Framework evidence

Installed Torch reports `2.11.0+cpu` at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/version.py:4`. Its CPU intra-op thread control is documented in that installation's `torch/_torch_docs.py:9814–9824`; every Torch test calls `torch.set_num_threads(8)` before test work. The same behavior is described by [PyTorch 2.11 set_num_threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html). This is a CPU validation run, not CUDA 12.9/H100 validation.

The native checkpoint-buffer fixture calls `init_process_group('gloo', init_method='tcp://…')` (`tests/test_s1_checkpoint_buffers.py:28–32`). Installed `torch/distributed/rendezvous.py:190–207,210–237` constructs its TCPStore and `distributed_c10d.py:1605` implements process-group setup. [PyTorch 2.11 distributed documentation](https://docs.pytorch.org/docs/2.11/distributed.html#tcp-initialization) describes that TCP rendezvous. Socket refusal prevents this fixture before any checkpoint behavior executes.

## Exact commands and results

Final fresh-patch verification: **20261119T094926Z**. Report assembled at Thu Nov 19 09:57:17 UTC 2026.

Every patch applies independently with `--fuzz=0 --no-backup-if-mismatch`. Recommended order is 03, 04, 02; combined adds 01 last with its switch OFF. Offset hunks are accepted only when exact context matches; no fuzz, rejected hunk or backup file is accepted. Manifest entries pin each input/result file, the complete base-tree digest, patch SHA256/bytes and native-gate SHA256.

```bash
source work/fix2_env.sh
SO_NO_LOCAL_SOCKETS=1 nice -n 10 "$PY" -I -s -B work/verify_delivery.py
```

`work/fix2_env.sh` selects `/scratch/jjyeung/envs/p1cpu/bin/python`, sets `CUDA_VISIBLE_DEVICES=''`, `PYTHONDONTWRITEBYTECODE=1`, OMP/MKL/OpenBLAS threads to 8, disables tokenizer parallelism, and keeps TMPDIR/TEST_TMP_ROOT/LANE_TEST_OUTPUT inside this workspace. The verifier gives each fresh tree its own fixture paths. Exact per-test commands, stdout/stderr and exit statuses are retained below.

| Application | Exact test summaries | Command/output |
|---|---|---|
| 01_prepared_input_cache.diff | `Ran 33 tests in 1.020s`; `OK`; `Ran 9 tests in 3.351s`; `OK` | [log](tests/20261119T094926Z/01_prepared_input_cache.diff.txt) |
| 02_parallel_frame_sha.diff | `Ran 7 tests in 0.043s`; `OK` | [log](tests/20261119T094926Z/02_parallel_frame_sha.diff.txt) |
| 03_checkpoint_verify_memo.diff | `Ran 10 tests in 0.249s`; `OK` | [log](tests/20261119T094926Z/03_checkpoint_verify_memo.diff.txt) |
| 04_launch_phase_timing.diff | `Ran 7 tests in 1.361s`; `OK` | [log](tests/20261119T094926Z/04_launch_phase_timing.diff.txt) |
| recommended | `Ran 10 tests in 0.254s`; `OK`; `Ran 7 tests in 1.388s`; `OK`; `Ran 7 tests in 0.043s`; `OK`; `Ran 86 tests in 2.699s`; `OK (skipped=11)` | [log](tests/20261119T094926Z/recommended.txt) |
| combined | `Ran 10 tests in 0.250s`; `OK`; `Ran 7 tests in 1.359s`; `OK`; `Ran 7 tests in 0.040s`; `OK`; `Ran 33 tests in 0.986s`; `OK`; `Ran 9 tests in 3.510s`; `OK`; `Ran 86 tests in 2.686s`; `OK (skipped=11)` | [log](tests/20261119T094926Z/combined.txt) |

The combined run registers **152 tests: 141 pass and 11 skip** (66 patch tests and 86 native tests). The recommended set registers 110 tests: 99 pass and 11 skip. Skips are never counted as passes.

Additional runs use the same CPU environment:

| Check | Exact test summaries | Output |
|---|---|---|
| Native input baseline | `Ran 86 tests in 2.741s`; `OK (skipped=11)` | [log](tests/20261119T094926Z/native_input.txt) |
| Native recommended, 02–04 ON | `Ran 86 tests in 2.736s`; `OK (skipped=11)` | [log](tests/20261119T094926Z/native_recommended_on.txt) |
| Input with known admission fixture | `Ran 92 tests in 2.714s`; `FAILED (failures=4, errors=1, skipped=11)` | [log](tests/20261119T094926Z/known_native_failures_input.txt) |
| Combined with known admission fixture | `Ran 92 tests in 2.773s`; `FAILED (failures=4, errors=1, skipped=11)` | [log](tests/20261119T094926Z/known_native_failures_patched.txt) |
| Review metadata/frame probes | `Ran 5 tests in 0.103s`; `OK` | [log](tests/20261119T094926Z/review_extra_probes.txt) |
| Round 1 delivery contracts | `Ran 6 tests in 0.008s`; `OK` | [log](tests/review_round2/round1_contracts.after.txt) |
| Round 2 delivery contracts | `Ran 5 tests in 0.017s`; `OK` | [log](tests/review_round2/delivery.after.txt) |

The known-failure comparison exits 0 after confirming the same five identities; its two 92-test runs intentionally exit 1. Exact comparison output:

```text
PASS: the same five native admission-fixture failures reproduce on input and patched trees
ERROR: test_reviewed_derivation_loads_from_a_restaged_host_directory (tests.test_s1_in_job_gate.InJobGateTests.test_reviewed_derivation_loads_from_a_restaged_host_directory)
FAIL: test_changed_proof_payload_and_foreign_parent_are_rejected (tests.test_s1_in_job_gate.InJobGateTests.test_changed_proof_payload_and_foreign_parent_are_rejected)
FAIL: test_fixture_evidence_does_not_authorize_real_training (tests.test_s1_in_job_gate.InJobGateTests.test_fixture_evidence_does_not_authorize_real_training)
FAIL: test_scene_coverage_cannot_be_omitted_or_rebound (tests.test_s1_in_job_gate.InJobGateTests.test_scene_coverage_cannot_be_omitted_or_rebound)
FAIL: test_self_consistent_unreviewed_configuration_change_is_rejected (tests.test_s1_in_job_gate.InJobGateTests.test_self_consistent_unreviewed_configuration_change_is_rejected)
```

The initial unskipped native attempt is retained in [socket attempt](tests/20261119T094816Z/recommended.txt): `Ran 76 tests` and `FAILED (errors=1, skipped=1)`, with the Gloo class blocked at socket creation. Its four standalone patch suites already passed. The final run uses explicit environment skips, without changing native tests or bypassing their assertions.

Full supplemental commands are in [commands.txt](tests/20261119T094926Z/commands.txt). Phase arithmetic was regenerated from the supplied timestamps; its exact output is [phase_arithmetic.txt](tests/20261119T094926Z/phase_arithmetic.txt). Delivery contracts and final artifact checks are indexed in [review_round2/INDEX.md](tests/review_round2/INDEX.md). All earlier relevant fixes are rechecked by these current runs, not assumed from an earlier model's verdict.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_prepared_input_cache.diff](patches/01_prepared_input_cache.diff) | 74827 | `e623c669d71344a5297c25dda2114128024a6804102488b303018cd6640b2e41` |
| [02_parallel_frame_sha.diff](patches/02_parallel_frame_sha.diff) | 6324 | `9f20e45be76d5ad356df185f6604c6e6ea822d6378286e1f8f3ed7df81158ea9` |
| [03_checkpoint_verify_memo.diff](patches/03_checkpoint_verify_memo.diff) | 13638 | `bf0ea4745a3e059fd0d0cdffc5fa7cd99ad646b7d70c7957df95f87b4f6c4e54` |
| [04_launch_phase_timing.diff](patches/04_launch_phase_timing.diff) | 11751 | `c939f738090ac7ad78ce3aadf596ccbc5862945a1cd8fb55655f29141aa03120` |

Base-tree pin: `780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278`. See [manifest.json](patches/manifest.json) for the exact hash encoding and per-file base/result pins. [Final artifact audit](tests/final_artifact_audit.txt) checks fresh-tree identities, shell/Python syntax, counts, before/after source identity, document links, workspace size and output checksums.

The required review-round mappings are retained as audit evidence; this is the deliberate exception to the no-archaeology writing rule.
