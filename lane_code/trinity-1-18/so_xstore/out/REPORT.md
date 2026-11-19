VERDICT: PARTIAL CPU entry and store/recorder groundwork are tested on build 21b; native portable production, planning, GPU adoption and first-loss equivalence remain unimplemented.

Measured native mode-p envelopes are **140.57 min** for job 172660 and **145.27 min** for job 171377. The timestamps give 8,434 s and 8,716 s respectively; [timing evidence](evidence/timing.json) retains exact file/line references. Peak production preparation RAM, CPU utilization and disk footprint are unknown. Native admission is configured for 16 CPU threads and a 256 GiB address-space ceiling; those are settings, not measured requirements.

**Estimated saving from this delivered package: 0 minutes per GPU launch.** There is no adopter. For a future verified hit, saving would be 140.57–145.27 minutes minus measured fetch, full SHA verification, native adoption and remaining frame work. Those costs are unmeasured. The design's 10–30 minute combined-cost allowance would imply an estimated 110.57–135.27 minute saving, but this package provides no evidence for that allowance or speedup. A fallback would add lookup/planning cost and save no native preparation time.

**Full N preparation cannot precede the export selected for N's handover.** The native code reads its parent artifact, weight manifest/index, donor metadata and handover closure. It also hashes available export payloads and RNG files. If N selects step 600, those bytes must exist first. CPU execution can overlap another GPU job once its inputs exist; no GPU job or allocation was launched here. The [input audit](INPUT_AUDIT.md) gives source-line evidence and distinguishes native reads from wrapper staging. Its static inventory is not a complete runtime read trace.

The native identity still consumes `output` and `preparation_output`. Native frame inventories also embed physical paths. The tests demonstrate both facts. Excluding those fields from an external key would leave a key gap. This package does not bypass native authentication or normalize away observed differences.

## Delivered scope

| Task | Result |
|---|---|
| 0: input/CPU audit | Source-backed audit and static read-site inventory delivered. Exact runtime read closure and production resource peaks remain unknown. Build 21b environment aliases and coverage/wording inputs are included. |
| 1: prepare-only store | A default-OFF CPU entry calls the same native admission function and writes separate telemetry. An experimental recorder and atomic object/root publisher are tested. A native planner, portable native receipt/SQLite schema and native store producer are **not implemented**. |
| 2: GPU adopt/fallback | **Not implemented.** Existing wrappers are byte-identical. No store root can enter training through a new wrapper path. No adopt/fallback job receipts are claimed. |
| 3: determinism | A CLI verifies and compares two supplied object graphs. Two independent protocol-fixture processes with different directories, HOSTNAME and TMPDIR produce equal roots. These are **not native prepare-only runs or two-node evidence**. |
| 4: first loss/twins | **Not implemented.** Corrupt/missing objects, changed consumed fields/files, partial roots and foreign keys are tested at the primitive boundary. Their native fallback losses are not tested. The optional Gloo script runs existing baseline tests only. |
| 5: admission argument | [One-page argument](ADMISSION_ARGUMENT.md) lists tested checks and missing proofs. It explicitly demonstrates that hashes and a matching key do not authenticate a producer. |
| 6: package | Pinned additive patch, fresh-patch verification, commands, operator note and retained test output delivered. |

## Patch and verification

Base: **build 21b**, source seal `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`. The patch is [01_native_cpu_and_store_groundwork.diff](patches/01_native_cpu_and_store_groundwork.diff), 52,630 bytes, SHA256 `a817c3b47ec7678016b95e6c1851890962b037326f62925f453dc339a2147455`. [manifest.json](patches/manifest.json) pins the base and every added file; [base inventory](evidence/base_inventory.json) lists all 936 original files.

The patch applies with `patch --batch --fuzz=0 -p1` to a fresh copy. All **936 existing source files remain byte-identical**. The seven added files require rebuilding the source archive and seals before real use. Both switches default OFF: `TK_NATIVE_CPU_PREPARE` for the diagnostic native CPU entry and `TK_XSTORE_EXPERIMENT` for the prototype library. No existing importer or wrapper calls them. Apply only after N's first proof, as described in [the rebuild note](NOTE_FOR_TREE_REBUILD.md).

**47 tests pass, with zero failures and zero skips.** Their scope is recorder/store primitives, native dependency/format boundaries, and CPU-entry forwarding/refusal. The CPU-entry forwarding test uses an explicit spy; it is not an end-to-end native prepare proof. Native parent metadata and frame-inventory tests execute the real native functions.

| Suite | Exact summary | Evidence |
|---|---|---|
| test_preparation_store.py | `Ran 34 tests in 0.061s; OK`; exit 0 | [exact output](tests/20261119T092557Z/test_preparation_store.py.txt) |
| test_preparation_native_boundary.py | `Ran 13 tests in 0.053s; OK`; exit 0 | [exact output](tests/20261119T092557Z/test_preparation_native_boundary.py.txt) |

The fresh-patch runner was:

```bash
source work/env.sh
nice -n 10 "$XSTORE_PYTHON" -I -s -B work/package.py > out/evidence/package.json
nice -n 10 "$XSTORE_PYTHON" -I -s -B work/verify_package.py > out/tests/package_verification.txt 2>&1
```

Its exact child commands were:

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_xstore/work/verified_20261119T092557Z/tests/test_preparation_store.py -v
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_xstore/work/verified_20261119T092557Z/tests/test_preparation_native_boundary.py -v
```

[Full verification output](tests/package_verification.txt) and [structured verification](tests/VERIFICATION.json) retain exit codes and commands. The children inherit nice level 10, empty CUDA visibility, eight-thread CPU-library limits and local scratch paths. The native-boundary process measured a cumulative child peak RSS of **329,000 KiB**; this is a small-test process measurement, not production preparation sizing.

The protocol-fixture command was `nice -n 10 "$XSTORE_PYTHON" -I -s -B work/check_fixture.py`. Its exact comparator output was:

```json
{"key": "1021d3ebbe4690861188aaaefd67c17ce4e1668adf5f78bee573225047e3188b", "object_count": 2, "root_digest": "3c1d5e2adbf6d8d60b025110ae33c95561b2a896422dc28249a077c997941d8d", "status": "IDENTICAL"}
```

[Fixture evidence](evidence/cold_fixture.json) records each process's environment and the exact comparator command. Telemetry lives outside the root. The objects are generated by a tiny lexical-row fixture, **not N's native preparation**. The comparator performs no normalization. `work/run_gloo.sh` is supplied but **not executed** because local sockets are unavailable; it does not satisfy task 4.

The installed framework reports `2.11.0+cpu`, CUDA build `None`, and eight intra-op threads ([framework pins](evidence/framework.json)). Source references for the behavior used here are `torch/_torch_docs.py:9815` for intra-op control, `:9828` for inter-op control, `torch/random.py:45` for CUDA seed-helper dispatch, and `torch/cuda/__init__.py:450`/`:478` for lazy CUDA initialization, under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages`. Official versioned references: [intra-op threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html) and [inter-op threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_interop_threads.html). The CPU parent test forbids the lazy CUDA initializer; it is not a claim that no library imports any CUDA-related Python module.

## Failure modes and outstanding work

| Risk | How we would notice; current limit |
|---|---|
| Stale store or changed consumed inputs | Expected-key/read replay checks reject fixture changes. A complete native expected-key computation is missing, so production adoption stays absent. |
| Pool purge, corruption or partial root | Complete object hashes/sizes and root hash fail. Native GPU fallback and its receipt still need implementation. |
| Key gap | Injected recorder reads fail; the actual native identity refuses excluded fields. The Python guard does not cover C extensions, captured references or all environment/filesystem metadata reads. Its file reader is bounded to 64 MiB. It is not a production read barrier. |
| Nondeterminism | Object-by-object comparison fails any difference. Native two-node output equality and every-rank bitwise first-loss equality remain unproved. |
| Coherent forged store | A test constructs different valid payloads with the same key. Require independent trusted producer/root binding plus deterministic native production, or recompute outputs. Self-hashes alone are insufficient. |
| Foreign/partial native destination | The primitive refuses an existing destination; native CPU refusal preserves its journal. No GPU publication or journal migration is implemented. |
| Run-specific receipt or checkpoint binding | Current native formats bind paths, config/source seals and handover progress. A native regeneration and checkpoint compatibility design must preserve these checks. |
| Resource/latency overrun | Capture real phase RSS, CPU utilization and input/output/temp peaks; measure end-to-end fetch/verify/adopt. Neither the tiny fixtures nor the GPU allocation's memory request sizes a production CPU job. |

No production dataset, GPU, SSH, Git, scheduler command, paid API, deletion or other agent's work was used or stopped. Documentation browsing was limited to official Torch library documentation. A local workspace inventory measured **306,514,850 bytes** including supplied inputs, below the 3 GB cap; [storage evidence](evidence/storage.json) records its scope.

The central unfinished work is the native content/admission separation, exhaustive native planning/recording, portable native producer, trusted root binding, verified GPU adoption with fallback receipts, and native first-loss/two-node proof. These are implementation gaps, not passing tests deferred for deployment. The package is ready for review of its limited scope; it is **not ready to enable cross-run reuse**.

Writing-skill note: technical identifiers are retained because this is an internal implementation review. No superseded ruling or narrative revision history is used as evidence.

Report written 2026-11-19T09:29:33.576518+00:00.
