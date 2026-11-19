VERDICT: PARTIAL The sealed OFF adapter and CPU tests are complete, but deployment needs the runtime closure, IO-governor commands, consistent ON overlays, and an actual Ada parity run.

The kit is in this directory. Start with [README.md](README.md), [STAGE_PLAN.json](STAGE_PLAN.json), and [read228.sh](read228.sh). No GPU, SSH, network, scheduler, Git, or paid API operation ran during this build.

**A4's actual export is m200, not m544.** The sealed plan and authenticated job 172744 return both require step 200 from run `673bc60f`. `package/a/0.json` is an m544 template; `a/1.json` and `a/export.json` in the mirror are placeholders. The delivered copy fills those two unsealed fields from the authenticated return. It preserves every sealed package member and all original reader bytes. The stage plan lists the requested m544 pins separately and excludes them from this A4 run. Comparing m544 against this Orchard return cannot establish the requested same instrument.

## Numbers and evidence

| Quantity | Result | Basis |
|---|---:|---|
| Direct CPU suite | 39 tests passed; 5.104 s | Measured; [exact output](checks/cpu_tests.txt). |
| Direct test process elapsed time | 7.18 s | Measured by `time -v`, including interpreter/import overhead. |
| Direct test MaxRSS | 237,144 kB as reported | Measured by `time -v`; below the 30 GB dispatch cap. |
| Fresh-patch CPU suite | 39 tests passed; 4.837 s | Measured; [exact output](checks/patch_2.txt). |
| Patch application | 36 added files; zero fuzz; exit 0 | Measured; [application output](checks/patch_0.txt). No existing file changes. |
| Original source | 927 files; 24,684,350 bytes | Measured from authenticated payload; every file hash verified. |
| Baseline prefix | 50 ordered items authenticated | Measured against Orchard's returned archive and the sealed item manifest; [proof](REFERENCE_PROOF.json). |
| A4 reference total | 636 items | Read from authenticated return summaries and journals. |
| Orchard elapsed / host MaxRSS | 2 h 07 min / 123 GiB | Supplied by the dispatch, not remeasured here. |
| Ada executions / CUDA measurements | 0 / 0 | No GPU access occurred. No fit, runtime, or parity claim is made. |
| Input archive bytes | 32,613,048,320 | Read from authenticated A4 input pins. |
| Expanded input bytes | 32,606,119,221 | Read from archive expansion pins. |
| Template runtime archive bytes | 10,497,433,600 | Read from packaged `ORCHARD_ASSETS.json`. |
| Planned target peak | 120,716,601,141 bytes | Estimate: pinned input sizes plus 40 GB runtime and 5 GB operating allowances. Below the 150 GB cap; runtime expansion remains unmeasured. |

[RESOURCE.json](checks/RESOURCE.json) records the final workspace and delivery sizes, CPU framework versions, and execution restrictions. The test environment is torch `2.11.0+cpu` and transformers `5.12.1`. This environment is not the production CUDA environment.

## What runs where

On trinity-1-18, the build reads only the named mirrors and installed CPU-library sources. Tests hide CUDA, set the requested eight-thread environment, and call `torch.set_num_threads(8)`. They retain their fixtures under this workspace and load no model weights.

On trinity-2-28, the coordinator first stages the pinned assets on local scratch. `stage228.py --prepare` calls A4's original CPU preparation entry. `run228.sh` checks pins and the staged footprint, then requires two idle GPU readings at least 300 seconds apart. It launches one worker under the required `vnice.sh` with one UUID in `CUDA_VISIBLE_DEVICES`.

The adapter calls the unchanged A4 operator, worker argument builder, and `orchard_h10.entry` action 2. It preserves the 636-item manifest, type order `[3,0,1,2,4]`, `0/1` shard, decoder, call cap, G3T memoization, and OFF cache behavior. `--items` stops only after a durable item commit. The observer records allocated/reserved CUDA peaks without changing the returned output object. It preserves the sealed resolver's source check and maker binding.

The return retains `metadata/reads/0/metadata/journals/<type>/0`, the original summaries, and a full-run `COMPLETE.json`. A partial 50-item return stays 50/636. The original envelope calls incomplete returns `status="FAILED"`; a clean requested prefix has adapter exit 0 and `SUMMARY.failure=null`. The original unpacker accepted this partial layout with exit 0. Full corpus ingestion and real GPU scoring were not executed here.

The local adapter retains `/project` archive references as authenticated source provenance and maps their physical copies to scratch before extraction. It uses A4's existing runtime configuration fields. The original `check_inputs` only permits `/project/community/jjyeung/` archive paths; this kit does not claim that the Orchard batch/bootstrap script itself runs on Trinity. It does not edit that script or the sealed reader to add a local archive path rule.

## Fixed comparison ruling

The comparator requires the authenticated first-50 baseline, matching A4 item order and export, unchanged source bindings, and OFF mode. It reports answer, call-placement, full-text, token, trace, and individual output-field equality counts, with per-item differences.

| CPU regression fixture | Identical answers | Identical call placement | Identical traces | Result |
|---|---:|---:|---:|---|
| Identical returns | 50/50 | 50/50 | 50/50 | SAME_INSTRUMENT |
| One answer changed | 49/50 | 50/50 | 49/50 | SAME_INSTRUMENT |
| One call moved | 50/50 | 49/50 | 49/50 | DIAGNOSTIC_ONLY |

These are **CPU test results, not an Ada verdict**. [COMPARE_CASES.json](checks/COMPARE_CASES.json) records the counts. The adjacent `compare_*.json` files contain the per-item diffs. Trace equality is diagnostic; the fixed acceptance rule remains 49 or 50 matching answers and identical call placement on all 50.

## Patch and exact validation

[01_trinity_adapter.diff](patches/01_trinity_adapter.diff) adds the standalone adapter and its tests beneath `read228/`. It changes no existing A4 file. The original entry points never import the adapter. Observation requires the explicit worker `--observe` switch, and cache extensions default OFF. [The patch manifest](patches/MANIFEST.json) records all added-file hashes and the patch hash.

The direct test command was:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B \
  out/tests/test_kit.py > out/checks/cpu_tests.txt 2>&1
```

Its exact test footer was:

```text
Ran 39 tests in 5.104s

OK
```

Fresh application used `patch --batch --fuzz=0 -p1`, then `bootstrap228.py` against the supplied A4 mirror, then the patched test suite under the same isolated CPU Python and resource environment. [PATCH_TEST.json](checks/PATCH_TEST.json) contains the exact argv and output paths for all three commands. All exited 0. The bootstrap reported:

```text
{"output": "/scratch/jjyeung/orch_n30/so_reads228/work/patch_apply/read228/A4", "files": 927, "expanded_bytes": 24684350, "step": 200}
```

The fresh suite's exact footer was:

```text
Ran 39 tests in 4.837s

OK
```

The tests cover path remapping, missing files, wrong sizes and hashes, both busy-card refusal points, graphics processes, card identity changes, archive traversal and overwrite refusals, original source hashes, original worker arguments, OOM handling without retry, original-unpacker acceptance, malformed returns, source/export/order mismatches, and the fixed comparison ruling. GPU APIs and the worker process are test doubles in the integration cases; no result from those cases is hardware evidence.

Framework behavior is grounded in the installed 2.11 source at the file/line locations in [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md). No online documentation was fetched because this dispatch prohibited network access.

## Open TODOs and failure detection

1. **Authorize and register staging.** The IO-governor README was not mirrored. `STAGE_PLAN.json` explicitly leaves register/launch commands null. The coordinator must supply the real commands, authorize heavy IO, and plan the greater-than-30-GB transfer with an admin. No guessed transport or SSH command is supplied.
2. **Recover the runtime receipt and closure.** The mirror has a 359-byte/SHA256 pin for `q/env.json`, not its contents. It has no `CONFIG/env.json`. The template archive parts are pinned, but their member-to-installed-path map and expanded size are unavailable. [ENVIRONMENT_TODO.md](ENVIRONMENT_TODO.md) specifies the required verification. Preflight refuses missing files, mismatched versions, CPU torch, framework modules outside scratch, and an oversized footprint.
3. **Verify the target's existing SAM3.** Its presence and size are dispatch information. No agent contacted 2-28. Staging must verify its complete SHA256 before reuse. A size match does not authorize a hash mismatch.
4. **Obtain consistent ON overlays.** [SO_READ_CONSISTENCY.json](SO_READ_CONSISTENCY.json) records mismatched `a19.py`, `a20.py`, and `test_round5.py`, plus missing `test_round6.py`. The upstream patch and its manifest disagree. The unverified installation was preserved under `work/unverified_so_read_extensions`; no active overlay tree is delivered. `--on` refuses until every extension pin agrees. OFF does not import those modules.
5. **Run the Ada first-50 OFF trial.** Equal source and checkpoint hashes do not establish equal CUDA arithmetic. Run `run228.sh ... --items 50`, then `compare228.sh`. The first OOM records its phase/item and exits 42; it is not retried. A failure before journal creation remains diagnostic and can be refused by A4's unpacker.
6. **Measure resource use and complete the read.** The 40 GB runtime expansion allowance and 5 GB operating allowance are estimates. Monitor caches and actual device peaks on 2-28. A4's unchanged single-card deadline allows five hours, with its original stop/return margins; Ada throughput is unknown. A hard kill, lost telemetry, or failure returns nonzero and cannot establish a complete read.

The idle gate proves occupancy only at its readings; it does not reserve the GPU against another program. CPU tests establish the adapter contracts and return shape, not live GPU telemetry, CUDA memory peaks, full runtime staging, or cross-device numerical parity. No files were deleted and no other agent's work was stopped.

The documentation applies the no-archaeology rule: it describes the delivered behavior and current evidence. No revision-history sentence was retained. Operational blockers are listed because they determine what the coordinator can run.
