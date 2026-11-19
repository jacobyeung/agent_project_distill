VERDICT: DONE All six target-refusal fixes are delivered for kit2; 140 CPU tests pass directly and from the applied patch, while target staging and the GPU read remain coordinator work.

Completed on trinity-1-18: Thu Nov 19 20:41:26 UTC 2026. The shipped delivery is preserved in `../out_round3/`. This kit stages every runtime group under `/scratch/jjyeung/orch_n30/reads228/private_rt/`, uses an all-archive preflight before extraction, and executes the package through its own private namespace. The default reader remains OFF and all authenticated A10b bytes remain unchanged.

## Numbers and evidence

| Quantity | Value | Basis |
|---|---:|---|
| Runtime archive parts | 13; 10,497,433,600 bytes | Read from package ORCHARD_ASSETS and MISSING pins; target bodies were not available here. |
| Runtime headers | 115,837: r0 41,535; r1 69,177; r2 5,125 | Counted from the three supplied lists; hashes and groups are in RUNTIME_LISTS.json. |
| Expanded runtime file contents | 10,371,055,588 bytes | Sum of regular-file sizes in the supplied lists; excludes directory allocation and symlink metadata. This is not a measured target disk footprint. |
| r0 / r1 / r2 expanded file bytes | 1,579,308,957 / 8,386,282,204 / 405,464,427 | Read from the lists. |
| Planned retained footprint | 94,537,720,332 bytes | Estimate: pinned input/runtime parts, input expansion, listed runtime expansion, conservative 3,450,062,241 shared-SAM allowance, and estimated 5 GB operating allowance. Shared SAM is never used. |
| Enforcement | 40 GB runtime expansion cap; 145 GB staged-footprint check; 150 GB total limit; 200 GiB free floor | Configured limits. The footprint counts private_rt, including symlink metadata, without following directory links into shared environments. |
| Direct / applied-patch tests | 140 / 140 passed | Measured; all eight suites, exact logs below. |
| Before-fix regressions | 21 cases fail; 23 assertion failures including subtests | Measured against out_round3; no test errors. |
| Preserved A10b files | 944 | SHA256-verified against the input mirror, delivery and applied patch. |
| Preserved shipped-delivery files | 1,161 | Verified against out_round3/DELIVERY_MANIFEST.json. |
| Patch | 20,207,395 bytes; 75 additive files | Measured; no existing input file changes. |
| Highest direct / applied-test MaxRSS | 426,660 / 427,532 KiB | `/usr/bin/time -v` measurements; below 30 GB. Tests use at most six CPUs; concurrent header checks kept the total below eight. |
| Target / GPU runs by this agent | 0 / 0 | No SSH, GPU, network download, deletion, Git or paid API call. |

Workspace size and final delivery inventory are measured in [DELIVERY_INTEGRITY.json](checks/round4/DELIVERY_INTEGRITY.json). The publisher refuses a workspace at or above 3 GB.

## Target refusal: finding -> fix -> test

| Finding / decision | Delivered fix | Regression evidence |
|---|---|---|
| 1. Shared runtime extraction and shared native CPython | Every registry destination is `private_rt/<archive-relative path>`. The package namespace receives private_rt. Native stdlib control uses private_rt/sj/uv-python/.../bin/python3.12. Narrow control/output binds preserve kit visibility; the private logical-root bind remains after the SJ bind. | `test_private_runtime_plan_and_native_control`, `test_host_translation_private_sj_and_absolute_link`, and the real-bwrap private runtime/logical/control/x isolation test. |
| 2. Partial writes before a later refusal | `runtime228.preflight_runtime` reads every header and file body in all groups, verifies part/whole hashes and exact header inventories, compares existing files, and checks paths, links, types and cross-group topology. `extract_runtimes` reaches pass 2 only after all groups pass. It preserves matching members and their metadata. | Late unknown namespace, conflict and pin failure all leave no new runtime members. Absolute/parent paths, special files, hardlinks, escaping/cyclic links and symlink parents refuse before writes. The CLI-entry test also verifies STAGE_CHECK records the refusal. |
| 3. x helpers were unregistered | Register the two exact x members as `record_only`, extract their bytes under private_rt/x, and include them in STAGE_CHECK `non_runtime_namespaces`. Neither x nor private_rt is bound wholesale or executed. | Helper extraction checks exact bytes; the real namespace cannot see private_rt/x/pull.py or /x/pull.py. |
| 4. Registry lacked actual membership | Registry destinations are cross-checked against sealed `orchard_job` constants, absolute-link rules, ORCHARD_ASSETS and q/env.json. Subtree receipts are cited below; devs1_direct and helper membership explicitly comes from the coordinator lists. All three list hashes, semantic header digests and expanded sizes are checked. | Zero-body tar fixtures preserve all 115,837 real paths/types/link targets and pass preflight. Adding an unknown namespace refuses without creating private_rt. The fixture also covers both regular-file tar codes for names where the format supports them. |
| 5. Private footprint and authorized stage rerun | The footprint explicitly includes private_rt. The native controller never uses shared uv-python. The authorized kit2 stage begins from the absent private root left by this refusal; matching successful stages are verified and reused. | Listed sizes agree with the plan; symlink-directory metadata is counted. Identical runtime reruns preserve inode/mode/mtime. The existing preparation test proves READY reuse without relaunch. |
| 6a. Bootstrap harness did not use Python 3.6 | `tests/run_tests.sh` selects `/usr/bin/python3` when its version is 3.6.8. The validation driver actually used that interpreter for all seven bootstrap tests. | Harness regression and [interpreter output](checks/round4/bootstrap_version.txt); direct/applied bootstrap suites both pass. |
| 6b. Operator omitted process guard | `operator228.execute` calls sealed `install_process_guard(out)` immediately after installing package imports, before loading the sealed operator or spawning children. | Guard-order regression plus the real sealed-operator CPU fixture, which completes a synthetic 50-item return with the guard installed. |

All 21 target-regression cases fail on the shipped kit: [exact before output](checks/round4/fix4_before_actual.txt). Every case passes in the direct and applied-patch suites. The member fixture contains headers and zero-byte file bodies; it does not substitute for target pin verification or target runtime imports.

## Namespace bindings and private logical root

The physical runtime root is `/scratch/jjyeung/orch_n30/reads228/private_rt`. The package receives that root directly; `sj` is a real private directory.

| Archive group | Host path below private_rt | In-namespace path | Package evidence |
|---|---|---|---|
| devs1_direct, rv_merge_fix, legs1_reads | `sj/orch_cd/<group>` | `/scratch/jjyeung/orch_cd/<group>` | `orchard_job.py:128–129`; `trace_runtime.py:22–25`, `export_stage.py:19` identify the latter two. devs1_direct membership comes from the coordinator list. |
| p1cpu | `sj/envs/p1cpu` | `/scratch/jjyeung/envs/p1cpu` | `orchard_job.py:128`; `orchard_stage.py:19–24` pins its absolute Python link. |
| Native CPython | `sj/uv-python/cpython-3.12.13-linux-x86_64-gnu` | Same suffix below `/scratch/jjyeung`, and `/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu` | `orchard_job.py:128,131`; `orchard_stage.py:19–24`. |
| Base manifest | `m/ap/90da7ac2` | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/90da7ac2` | `orchard_job.py:130`; `ORCHARD_ASSETS.json:7–10`. |
| Base environment | `m/ap/19252904` | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904` | `orchard_job.py:130`; `q/env.json:1`, `orchard_stage.py:22–23`. |
| Empty package fsw bind | `fsw` | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung` | `orchard_job.py:129`; zero archive members. |
| Staging records | `x/pull.py`, `x/need_frames.txt` | None; never bound or executed | Coordinator r0 list; fix4 decision. |
| Private logical root | Outside private_rt: `reads228/private/b01ec87a6f29b` | `/scratch/jjyeung/b01ec87a6f29b` | `namespace228.namespace_command` appends this bind after the package SJ bind. |

Package evidence above is under `A10b/src/orchard_h10/vendor/`; the delivered q receipt is `evidence/q/env.json`. STAGE_PLAN contains receipt sizes/hashes, header digests, member counts and all physical/namespace destinations. RUNTIME_LISTS.json contains source-list hashes and measured listing totals.

The adapter adds narrow binds for the kit, `prepare`, `operator_probe` and `namespace_probe`; an executing operator also gets its own output directory. It changes the namespace working directory to the kit. Neither the stage root nor private_rt is bound wholesale, so the record-only x helpers remain invisible. This allows the private runtime, private logical root and operator control paths to work together while shared environments and orch_cd stay hidden.


`namespace228.py:32–47` preserves the package binds and appends the control and private logical-root binds. `namespace228.py:55–62` adds only the executing operator's output directory. The real-bwrap fixture reads private runtime, m/ap and logical-root sentinel bytes, preserves a shared sentinel, sees the kit operator file, and cannot see the x helper. No authenticated symlink, pyvenv.cfg, settings file or reader source is rewritten.

## Patch and exact validation

[01_trinity_adapter.diff](patches/01_trinity_adapter.diff) is additive against the authenticated A10b input tree. SHA256: `261e5437a55e79ada2a9fba875d75fd2661fd65a97f9371a57ec812de35d6347`. It changes no existing file. Activation requires explicit adapter entry-point invocation; observation requires `--observe`; optional cache extensions require `--on` and default OFF.

[Patch integrity](checks/round4/RELEASE_PATCH_INTEGRITY.json) records the exact bootstrap, `patch --batch --fuzz=0 -p1`, and asset-install commands. The patch applies without offsets or fuzz. All 75 delivered adapter files match the applied patch, all 944 authenticated input files retain their hashes, Python 3.6 grammar checks pass for the bootstrap modules, and shell syntax checks pass. Full patch command outputs are [bootstrap](checks/round4/release_patch_command_0.txt), [apply](checks/round4/release_patch_command_1.txt), and [asset install](checks/round4/release_patch_command_2.txt).

The validation driver sets CUDA_VISIBLE_DEVICES empty, PYTHONDONTWRITEBYTECODE=1, OMP/MKL/OPENBLAS thread limits to eight, TOKENIZERS_PARALLELISM=false, and local caches under work/round4. Torch tests call `torch.set_num_threads(8)` before tensor work. Both controller suites use `-S`; only the separate CPU operator fixture has site-packages. The bootstrap suite uses actual system Python 3.6.8.

| Suite | Tests | Direct / patch exit code | Exact complete outputs |
|---|---:|---|---|
| `test_kit.py` | 39 | 0 / 0 | [release_kit.txt](checks/round4/release_kit.txt), [patch_kit.txt](checks/round4/patch_kit.txt) |
| `test_review.py` | 18 | 0 / 0 | [release_review.txt](checks/round4/release_review.txt), [patch_review.txt](checks/round4/patch_review.txt) |
| `test_prepare.py` | 7 | 0 / 0 | [release_prepare.txt](checks/round4/release_prepare.txt), [patch_prepare.txt](checks/round4/patch_prepare.txt) |
| `test_bootstrap36.py` | 7 | 0 / 0 | [release_bootstrap36.txt](checks/round4/release_bootstrap36.txt), [patch_bootstrap36.txt](checks/round4/patch_bootstrap36.txt) |
| `test_review2.py` | 17 | 0 / 0 | [release_review2.txt](checks/round4/release_review2.txt), [patch_review2.txt](checks/round4/patch_review2.txt) |
| `test_stage2.py` | 12 | 0 / 0 | [release_stage2.txt](checks/round4/release_stage2.txt), [patch_stage2.txt](checks/round4/patch_stage2.txt) |
| `test_review3.py` | 19 | 0 / 0 | [release_review3.txt](checks/round4/release_review3.txt), [patch_review3.txt](checks/round4/patch_review3.txt) |
| `test_target_refusal.py` | 21 | 0 / 0 | [release_target_refusal.txt](checks/round4/release_target_refusal.txt), [patch_target_refusal.txt](checks/round4/patch_target_refusal.txt) |

The exact direct test commands are:

```bash
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_kit.py
```
```bash
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_review.py
```
```bash
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_prepare.py
```
```bash
nice -n 10 /usr/bin/time -v /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_bootstrap36.py
```
```bash
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_review2.py
```
```bash
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_stage2.py
```
```bash
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -S -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_review3.py
```
```bash
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -S -B /scratch/jjyeung/orch_n30/so_reads228/work/round4/kit/tests/test_target_refusal.py
```

The applied-patch commands use `work/round4/applied_release/read228/tests/` in place of `work/round4/kit/tests/`; every complete argv and return code is in [release_RUNS.json](checks/round4/release_RUNS.json) and [patch_RUNS.json](checks/round4/patch_RUNS.json). These are the unedited unittest summary outputs:

`test_kit.py` (direct):

```text
Ran 39 tests in 7.076s

OK
```

`test_review.py` (direct):

```text
Ran 18 tests in 4.876s

OK
```

`test_prepare.py` (direct):

```text
Ran 7 tests in 0.122s

OK
```

`test_bootstrap36.py` (direct):

```text
Ran 7 tests in 0.016s

OK
```

`test_review2.py` (direct):

```text
Ran 17 tests in 2.729s

OK
```

`test_stage2.py` (direct):

```text
Ran 12 tests in 0.037s

OK
```

`test_review3.py` (direct):

```text
Ran 19 tests in 4.334s

OK
```

`test_target_refusal.py` (direct):

```text
Ran 21 tests in 74.154s

OK
```

`test_kit.py` (applied patch):

```text
Ran 39 tests in 6.716s

OK
```

`test_review.py` (applied patch):

```text
Ran 18 tests in 4.784s

OK
```

`test_prepare.py` (applied patch):

```text
Ran 7 tests in 0.106s

OK
```

`test_bootstrap36.py` (applied patch):

```text
Ran 7 tests in 0.012s

OK
```

`test_review2.py` (applied patch):

```text
Ran 17 tests in 2.693s

OK
```

`test_stage2.py` (applied patch):

```text
Ran 12 tests in 0.039s

OK
```

`test_review3.py` (applied patch):

```text
Ran 19 tests in 4.214s

OK
```

`test_target_refusal.py` (applied patch):

```text
Ran 21 tests in 73.820s

OK
```


The seven supplied review-2 comparisons remain DIAGNOSTIC_ONLY. All 18 review-3 outcomes remain unchanged: four refusals, six SAME_INSTRUMENT controls and eight diagnostics. [Review-2 exact output](checks/round4/cr2_replay.txt); [review-3 exact output](checks/round4/cr3_replay.txt). No comparison or reader decoding code changed in this round.

The existing [framework evidence](FRAMEWORK_EVIDENCE.md) cites installed torch 2.11 source file:line for every framework API used by the adapter, with official documentation links retained from the authenticated delivery. No framework behavior was added here. The package q/env.json separately pins reader torch 2.13.0+cu130, torchvision 0.28.0+cu130, transformers 5.19.0 and scipy 1.14.1; those versions still require the target's exact import probe.

## Exact coordinator sequence: stage first, then one card-gated run


These commands belong to the coordinator. The build agent has not executed SSH or any target-node command. All 21 archive parts are staged. The kit checks their pins itself. All eight cards are busy; staging can finish while the read waits for a free card.

In the existing **trinity-2-28** session, refuse an existing kit path before shipping. If this check fails, stop and resolve the existing delivery; do not merge deliveries or retry the transfer.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit2
if ! test ! -e "$kit_dir"; then
  echo 'REFUSED: kit path must be absent before shipping' >&2
  exit 2
fi
```

On **trinity-1-18**, submit this push through the coordinator's rate limiter, reusing its existing SSH master. Use this direction and command; do not pull from 2-28. If the transfer fails or drops, stop without a retry.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-1-18
tar -C /scratch/jjyeung/orch_n30/so_reads228/out -cf - . | timeout 600 ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/reads228/kit2 && tar -C /scratch/jjyeung/orch_n30/reads228/kit2 --skip-old-files -xf -'
date -u
```

As a **separate step on trinity-2-28**, verify the delivery manifest before executing the kit. This uses the existing target session and opens no SSH connection.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit2
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
nice -n 10 /usr/bin/python3 -I -s -B - "$kit_dir" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'DELIVERY_MANIFEST.json').read_text())
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='DELIVERY_MANIFEST.json'}
assert actual==set(manifest['files']),sorted(actual^set(manifest['files']))
for name,spec in manifest['files'].items():
    path=root/name
    assert path.is_file() and not path.is_symlink(),name
    assert path.stat().st_size==spec['bytes'],name
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    assert digest.hexdigest()==spec['sha256'],name
print('DELIVERY_MANIFEST verified: '+str(len(manifest['files']))+' files')
PY
date -u
# One stage-only sequence: hashes, runtime extraction, input extraction, code install,
# namespace check, preparation, stage check, and the exact operator import probe.
bash "$kit_dir/coordinator228.sh" --stage-only
date -u
```

The stage-only sequence never queries a card or creates a run directory. It reads all three runtime archives before creating any runtime member, then extracts every registered group under `reads228/private_rt/`. The `x/` helpers stay there as records and have no namespace bind or execution path. Extraction logs go under `reads228/extraction_logs`; inputs and source go under `reads228/private/b01ec87a6f29b`. The package sees the pinned logical path through its namespace bind. The shared logical root is not a staging source.

Once a card is free, set `CARD` to that single index or UUID and run the following **once on trinity-2-28**. Do not issue a separate manual idle gate: this invocation owns the UUID lock, takes both readings at least 300 seconds apart, and starts the worker. A busy-card refusal after the run directory exists consumes that name; any later authorized attempt needs a fresh name.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit2
stage=/scratch/jjyeung/orch_n30/reads228
test -n "${CARD:?Set CARD to the chosen free index or UUID}"
bash "$kit_dir/coordinator228.sh" --run-only "$CARD" "$stage/runs/a400check1"
date -u
```

`--run-only` rehashes staged data and checks operator imports before the card gate; allow minutes of local scratch IO before the first idle reading. It invokes `run228.sh` exactly once with `--items 50`, compares against `kit2/reference`, unpacks with the unchanged unpacker into `kit2/ingest/a400check1`, and writes `CORPUS_INGEST.json`. A clean 50/636 return has `EXIT.status=FAILED`; ingestion uses `SUMMARY.failure=null`, completion and the comparison result. A diagnostic comparison cannot publish READY_FOR_CORPUS. A failed run stops this sequence and is not retried.

The coordinator-authorized second `--stage-only`, from `kit2` after the reported refusal, starts with an absent `private_rt/`. It verifies the same 13 runtime part pins, completes pass 1 across r0/r1/r2, creates the private runtime in pass 2, extracts inputs into the private logical root, installs sealed code, probes the namespace, prepares once, verifies staging and probes operator imports. It never reads or removes the 443 entries left in shared `orch_cd/` by the refused delivery. The old `kit/` stays in place.

A subsequent authorized stage check on a successfully staged kit compares every existing runtime file and symlink in pass 1, preserves matching files and their metadata in pass 2, skips matching input members, verifies installed code, and reuses READY.json instead of launching preparation again. A conflict refuses before runtime writes. There is no retry loop; an interrupted extraction or failed preparation requires coordinator review before another invocation.


## What could go wrong and how to notice

- Pass 1 refuses unknown/changed headers, unsafe names/links/types, part/hash mismatches, existing conflicts or a changed registry. STAGE_CHECK records the refusal; no runtime member is written. Stage receipts and control logs can be written outside private_rt.
- A pass-2 IO error, source mutation or concurrent writer can leave partial files. Pass 2 checks headers, file digests and the full stream again and refuses on disagreement. Do not run concurrent stage writers or retry a failed/killed stage automatically; the coordinator must inspect its receipt.
- The target may reject bwrap, the pinned runtime ABI or package imports. NAMESPACE.json, STAGE_CHECK and OPERATOR_PROBE.json expose those failures before card access. There is no automatic runtime relocation or native-site fallback.
- The run-only path rehashes staged local data before the first idle reading; allow minutes of scratch IO (timing is an estimate). The two readings cannot reserve a card against another user. The one-second sampler exposes a late arrival; OOM writes OOM.json/STOP and exits 42 without retry.
- A clean 50/636 return has EXIT.status=FAILED. Ingest uses SUMMARY and the comparison. DIAGNOSTIC_ONLY exits 1 after writing CORPUS_INGEST; it does not authorize corpus readiness.
- A standalone stack-dump diagnostic exited with SIGSEGV while its timed faulthandler printed a traceback. It was not retried; no cluster-limit kill was observed. [Exact diagnostic output](checks/round4/headers_debug.txt) is retained. The normal full-list fixture and both final complete suites pass without that diagnostic.

## Not done

No command ran on trinity-2-28. Full runtime extraction, native private CPython startup, pinned framework imports, preparation, the card gate and the GPU read remain target checks. No Ada/H100 equivalence claim is made until the 50-item comparison passes. The old kit and the 443 shared orch_cd entries remain untouched; their removal candidates stay with the coordinator. No deletion was performed or queued by this agent.

The refusal account, explicit second-stage behavior and before/after evidence are retained because the dispatch requires them. Active deployment paths select kit2; sealed source and exact historical test evidence retain their original bytes.
