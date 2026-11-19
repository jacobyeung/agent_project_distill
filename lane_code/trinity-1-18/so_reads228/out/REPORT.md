VERDICT: DONE The third-review fixes, regression tests and delivery patch are complete; the target read waits for a free card on trinity-2-28.

The kit runs A10b read A, Orchard job **173060**, step **400**, run `6ed2c7aa`, artifact SHA256 `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. The sealed source, settings, input pins and item order remain unchanged. The coordinator verified all 21 staged archive parts at 18:37Z; the kit authenticates them again before use. All eight target cards are busy. No target or GPU command ran during this build.

## Numbers: measured, pinned and estimated

| Quantity | Value | Basis |
|---|---:|---|
| Direct CPU tests | **119 passed** | Measured: 39 base, 18 review1, 7 preparation, 7 bootstrap, 17 review2, 12 stage2, 19 review3. |
| Fresh applied-patch tests | **119 passed** | Measured on a newly bootstrapped input copy after zero-fuzz patch application. |
| New regressions against preserved kit | **19 fail** | Measured: 18 failed assertions and one missing-private-path refusal; all 19 pass after the fixes. |
| Round-three reviewer fixtures | **18 outcomes preserved** | Measured: 6 SAME_INSTRUMENT, 8 DIAGNOSTIC_ONLY, 4 refusals. Positive and diagnostic cases retain the fixed ruling. |
| Round-two reviewer fixtures | **7/7 DIAGNOSTIC_ONLY** | Measured replay of every supplied comparison. |
| Maximum individual test-process RSS | **237248 kB** | Measured with `/usr/bin/time -v`; checks ran serially, with CUDA hidden and at most eight threads. |
| Preserved delivery snapshot | **1086 files** | Measured hashes in `checks/round3/ROUND2_SNAPSHOT.json`; `out_round2/` remains unchanged. |
| Authenticated input files unchanged | **944 files** | Measured against the input mirror, including all 927 sealed source files. |
| Workspace at patch verification | **1682875138 bytes** | Measured regular-file sizes under L at Thu Nov 19 19:34:17 UTC 2026; final publication measurement is in `checks/round3/DELIVERY_INTEGRITY.json`. |
| Runtime parts | **13; 10,497,433,600 bytes** | Pinned by MISSING.json; staged according to the coordinator's check. |
| Input archives | **32,613,048,320 packed bytes; 32,606,120,583 expanded bytes** | Package pins; the kit also carries the small pinned a/6 preparation archive. |
| Target peak disk footprint | **124,166,664,744 bytes** | **Estimate**: retained archives, input expansion, 40 GB runtime expansion allowance and 5 GB operating allowance. Includes a conservative 3,450,062,241-byte shared-SAM allowance; shared SAM is never read. Private SAM is already included in a2 expansion. |
| Target limits | **145 GB staged; 150 GB total; 200 GiB free floor** | Configured limits; target expansion remains unmeasured by this build. |
| Target namespace/import/prepare/GPU runs | **0 / 0 / 0 / 0** | This build ran only local CPU fixtures, including a real bwrap private-bind check. |

The package receipt pins torch 2.13.0+cu130, torchvision 0.28.0+cu130, transformers 5.19.0 and scipy 1.14.1. These are pinned versions, not measurements from this build. [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) cites the installed torch 2.11 CPU source and official references for the observer APIs. The fixes add no new torch API behavior.

## Review round 3: finding -> fix -> test

| Finding | Fix and reason | Regression evidence |
|---|---|---|
| HIGH 1: bare control interpreter cannot run the operator | **Approach (b).** Native CPython performs stdlib staging, gating and comparison. `namespace228.operator_command` runs the probe and operator through the package namespace plus unchanged `d/v/py -B -I`. `operator228.py` calls the sealed tower operator and runner with the observation launcher. This retains the interpreter boundary in `A10b/src/orchard_h10/job.py:206–207`. The worker inherits that namespace and uses the package policy prefix from `job.py:194`; no nested bwrap. No `site.addsitedir` fallback or runtime-byte deviation is used. | Seven `test_high1_*` regressions cover the shared command, CLI refusal code 2, pre-gate ordering, dependency-free native controller, worker prefix and test harness. A controller started with `-I -S -B` completes a synthetic 50-item run through a separate CPU operator process using real sealed operator/summary code. |
| HIGH 1: refuse missing imports before consuming a card window | The exact operator command imports `e2e_reader.perception_memo`, `h1eval.h10.launch`, `h1eval.items`, `h1eval.modes`, `h1eval.cli`. Failure writes STAGE/OPERATOR_PROBE.json and exits 2 before snapshot, idle gate, UUID lock or run directory. | `test_high1_no_numpy_probe_refuses_before_any_card_or_run_directory` runs the probe under `-S`, observes missing numpy and exit 2, and asserts that card functions, lock directory and run directory were untouched. The entire 19-test suite runs without parent site-packages. |
| LOW 2: invalid names fail after gating | `run_one` applies the sealed `opaque([str(out)])` before stage_check. The coordinator checks its run-name regex before environment setup or staging. | `test_low2_banned_name_refuses_before_stage`; `test_low2_coordinator_validates_name_before_work`. |
| LOW 3: shipping direction and SSH options | The coordinator pushes from trinity-1-18 through its rate limiter with `timeout 600 ssh -o ConnectTimeout=20`, using the existing master. A separate target-session step verifies the delivery manifest. The absent-kit refusal remains. | `test_low3_report_pushes_with_timeout_and_reuses_master` checks the report; the standalone patch carries the identical recipe in COORDINATOR.md. |
| INFO 4: shared d/s has unexplained files | Inputs and source stage under `reads228/private/b01ec87a6f29b`. The namespace binds that private directory at the pinned logical path. Native checks translate logical paths only for host reads; settings, runtime links and pinned bytes retain their original values. Shared d/s and d/k are never read or used. Private unexplained files still refuse. | Six `test_info4_*` tests check the plan, code install, host translation, bind order, real bwrap behavior, and full stage verification with a guard against opening shared files. Existing mismatch/unexplained-file refusals still pass. |
| INFO 5: extraction logs touch the shared logical root | Extraction logs go under STAGE/extraction_logs. | `test_info5_extraction_logs_stay_under_stage`. |
| INFO 6: policy reads come from /data3 | Bootstrap authenticates the delivered policy copies; stage checks authenticate private d/q; the operator verifies and executes logical d/q inside the namespace. Both hashes retain their package pins. | `test_info6_policy_has_no_data3_dependency`, the private-stage test, and worker-command coverage. |
| INFO 8: failed names cannot be reused | README states: “Any refusal after the run directory exists needs a fresh run name.” | `test_info8_readme_requires_fresh_name_after_directory_exists`. |

The private bind works in the local CPU namespace fixture; the target's full pinned runtime remains a deployment check. This provides no reason to take fallback (a). LOCAL_RUN records the operator probe, interpreter, package policy paths, logical bind and both bwrap identities.

## Review round 2: finding -> fix -> test

The 17 comparison/launch regressions and 12 staging regressions pass. They cover whole binding/settings equality, SUMMARY failure and completion, FAILED.json, pinned reference metadata, preserved runtime links, archive member inventories, exact conflicts, unexplained files, import argv, local cache environments, broad OOM recognition and unchanged unpack/ingest behavior. The original seven reviewer comparisons all remain DIAGNOSTIC_ONLY; [exact replay](checks/round3/cr2_replay.txt) and [results](checks/round3/cr2_replay/PROBES.json) are included.

## Review round 1: finding -> fix -> test

The 18 first-review regressions, 39 base tests and seven preparation tests pass. They cover version/audit checks before the gate, call placement semantics, mandatory local provenance, original return metadata and unpack acceptance, OFF defaults, policy hashes, local write roots, OOM stopping and the worker's separate process group. The updated integration tests cross the operator process boundary while retaining their original metadata assertions.

## Exact commands and outputs

The validation driver records exact argv, environment overrides, UTC starts, exit codes and output paths in [final_RUNS.json](checks/round3/final_RUNS.json) and [patch_RUNS.json](checks/round3/patch_RUNS.json). Every complete stdout/stderr stream is linked below; RSS values are measured kB.

| Run | Exact unittest footer | Exit | MaxRSS | Exact output |
|---|---|---:|---:|---|
| Direct review3_before | `Ran 19 tests in 0.479s; FAILED (failures=18, errors=1)` | 1 | 33052 | [full output](checks/round3/final_review3_before.txt) |
| Direct base | `Ran 39 tests in 7.567s; OK` | 0 | 236164 | [full output](checks/round3/final_base.txt) |
| Direct review1 | `Ran 18 tests in 5.079s; OK` | 0 | 237184 | [full output](checks/round3/final_review1.txt) |
| Direct prepare | `Ran 7 tests in 0.131s; OK` | 0 | 225704 | [full output](checks/round3/final_prepare.txt) |
| Direct bootstrap | `Ran 7 tests in 0.012s; OK` | 0 | 25884 | [full output](checks/round3/final_bootstrap.txt) |
| Direct review2 | `Ran 17 tests in 2.687s; OK` | 0 | 35068 | [full output](checks/round3/final_review2.txt) |
| Direct stage2 | `Ran 12 tests in 0.035s; OK` | 0 | 27192 | [full output](checks/round3/final_stage2.txt) |
| Direct review3 | `Ran 19 tests in 4.446s; OK` | 0 | 233456 | [full output](checks/round3/final_review3.txt) |
| Applied patch base | `Ran 39 tests in 7.409s; OK` | 0 | 236744 | [full output](checks/round3/patch_base.txt) |
| Applied patch review1 | `Ran 18 tests in 5.317s; OK` | 0 | 237248 | [full output](checks/round3/patch_review1.txt) |
| Applied patch prepare | `Ran 7 tests in 0.112s; OK` | 0 | 225328 | [full output](checks/round3/patch_prepare.txt) |
| Applied patch bootstrap | `Ran 7 tests in 0.013s; OK` | 0 | 25748 | [full output](checks/round3/patch_bootstrap.txt) |
| Applied patch review2 | `Ran 17 tests in 2.766s; OK` | 0 | 34836 | [full output](checks/round3/patch_review2.txt) |
| Applied patch stage2 | `Ran 12 tests in 0.041s; OK` | 0 | 27264 | [full output](checks/round3/patch_stage2.txt) |
| Applied patch review3 | `Ran 19 tests in 4.544s; OK` | 0 | 233432 | [full output](checks/round3/patch_review3.txt) |

The measured validation commands were:

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round3/validate.py
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_reads228/work/round3/validate.py /scratch/jjyeung/orch_n30/so_reads228/work/round3/applied_verified/read228 patch
```

Each suite command is `nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B <test-file>`, except `test_review3.py`, which uses `-I -S -B`. `bash tests/run_tests.sh` runs all seven suites with that distinction and local caches. The positive integration uses a separate CPU interpreter; its worker and card observations are doubles. Real CUDA kernels, target runtime imports and device parity are not tested here.

The 19 negative regressions use the same test file with READ228_REVIEW3_KIT=/scratch/jjyeung/orch_n30/so_reads228/out_round2. The missing-private-path case raises Refusal on preserved code; it is reported as a unittest error and passes on the fixed code. The other 18 cases fail assertions. None is a target run or a killed job.

## Reviewer fixture replay

Both replays ran `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -S -B /scratch/jjyeung/orch_n30/so_reads228/work/round3/replay_review3.py --kit <kit> --out <output>`, once with `out_round2` and once with `work/round3/kit`. [Before output](checks/round3/cr3_before.txt), [after output](checks/round3/cr3_after.txt) and [full comparison records](checks/round3/cr3_after/PROBES.json) retain exact outcomes and reasons. The summaries match for all 18 fixtures.

| Reviewer fixture | Verdict | Identical answers | Identical placements |
|---|---|---:|---:|
| `r2_5f0o1qpa` | REFUSED | — | — |
| `r2_8efe82tv` | SAME_INSTRUMENT | 49 | 50 |
| `r2_8u1v8u0a` | DIAGNOSTIC_ONLY | 49 | 49 |
| `r2__qa3gdtw` | SAME_INSTRUMENT | 50 | 50 |
| `r2_aq7uixrb` | REFUSED | — | — |
| `r2_btgyu_e5` | SAME_INSTRUMENT | 50 | 50 |
| `r2_c67p0oj0` | SAME_INSTRUMENT | 50 | 50 |
| `r2_emi63otj` | REFUSED | — | — |
| `r2_j9gy_v5p` | DIAGNOSTIC_ONLY | 50 | 49 |
| `r2_k0eidtwf` | DIAGNOSTIC_ONLY | 50 | 49 |
| `r2_kgo0g8ul` | DIAGNOSTIC_ONLY | 50 | 49 |
| `r2_mb5uq4mr` | DIAGNOSTIC_ONLY | 48 | 50 |
| `r2_myq850aj` | SAME_INSTRUMENT | 50 | 50 |
| `r2_pdfpl_j2` | REFUSED | — | — |
| `r2_syho8c7k` | DIAGNOSTIC_ONLY | 50 | 49 |
| `r2_x6y6wucf` | SAME_INSTRUMENT | 50 | 50 |
| `r2_xibrlh1d` | DIAGNOSTIC_ONLY | 50 | 50 |
| `r2_zmay2_sr` | DIAGNOSTIC_ONLY | 50 | 50 |

The fixed ruling remains at least 49/50 identical answers and 50/50 identical call placements, subject to all eligibility checks. Traces are diagnostics. Provenance establishes consistency, not hardware attestation.

## Additive patch and integrity

[01_trinity_adapter.diff](patches/01_trinity_adapter.diff) adds **69 files**, **3225135 bytes**, under `read228/` against the supplied input tree. Its SHA256 is `ce421876285305c790d0ec6a459b1c1f7d5db7c9a4dcebeeebcefa100899895b`. [patches/MANIFEST.json](patches/MANIFEST.json) pins every patch file. DELIVERY_MANIFEST.json pins the whole delivery except itself.

The adapter requires explicit entry-point invocation; operator execution requires `--execute`, worker observation requires `--observe`, and optional caches default OFF. No existing production file changes. The patch includes tests and the coordinator recipe. Generated REPORT/check logs accompany the delivery rather than entering the patch. [PATCH_INTEGRITY.json](checks/round3/PATCH_INTEGRITY.json) records syntax checks, Python 3.6 bootstrap grammar, shell checks, input hashes and zero-fuzz application.

```bash
date -u
nice -n 10 patch --batch --fuzz=0 -p1 \
  -d /scratch/jjyeung/orch_n30/so_reads228/work/round3/applied_verified \
  -i /scratch/jjyeung/orch_n30/so_reads228/work/round3/kit/patches/01_trinity_adapter.diff
```

That command returned 0; [exact output](checks/round3/patch_command_1.txt) is retained. Bootstrap before and after application also returned 0 ([input](checks/round3/patch_command_0.txt), [adapter assets](checks/round3/patch_command_2.txt)). All 119 tests passed on the applied patch.

## Exact coordinator sequence

These commands belong to the coordinator. The build agent has not executed SSH or any target-node command. All 21 archive parts are staged and match their pins according to the coordinator's 18:37Z check. All eight cards are busy; staging can finish while the read waits for a free card.

In the existing **trinity-2-28** session, refuse an existing kit path before shipping. If this check fails, stop and resolve the existing delivery; do not merge deliveries or retry the transfer.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit
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
tar -C /scratch/jjyeung/orch_n30/so_reads228/out -cf - . | timeout 600 ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/reads228/kit && tar -C /scratch/jjyeung/orch_n30/reads228/kit --skip-old-files -xf -'
date -u
```

As a **separate step on trinity-2-28**, verify the delivery manifest before executing the kit. This uses the existing target session and opens no SSH connection.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit
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

The stage-only sequence never queries a card or creates a run directory. Extraction logs go under `reads228/extraction_logs`; inputs and source go under `reads228/private/b01ec87a6f29b`. The package sees the pinned logical path through its namespace bind. The shared logical root is not a staging source.

Once a card is free, set `CARD` to that single index or UUID and run the following **once on trinity-2-28**. Do not issue a separate manual idle gate: this invocation owns the UUID lock, takes both readings at least 300 seconds apart, and starts the worker. A busy-card refusal after the run directory exists consumes that name; any later authorized attempt needs a fresh name.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit
stage=/scratch/jjyeung/orch_n30/reads228
test -n "${CARD:?Set CARD to the chosen free index or UUID}"
bash "$kit_dir/coordinator228.sh" --run-only "$CARD" "$stage/runs/a400check1"
date -u
```

`--run-only` rechecks staging and operator imports before the card gate, invokes `run228.sh` exactly once with `--items 50`, compares against `kit/reference`, unpacks with the unchanged unpacker into `kit/ingest/a400check1`, and writes `CORPUS_INGEST.json`. A clean 50/636 return has `EXIT.status=FAILED`; ingestion uses `SUMMARY.failure=null`, completion and the comparison result. A diagnostic comparison cannot publish READY_FOR_CORPUS. A failed run stops this sequence and is not retried.


## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Missing, changed or unexplained staged bytes | Archive hashes, member inventories, source checks and private-root reconciliation refuse with paths. STAGE_CHECK retains failure evidence. No shared-file repair or automatic retry occurs. |
| Namespace or runtime incompatibility on 2-28 | NAMESPACE.json records system bwrap identity and probe output. Version and operator probes refuse before card access. No native-site fallback is silently selected. |
| A card is occupied or another process allocates after the gate | The two idle readings refuse known occupancy. The UUID lock coordinates this kit only; nvidia-smi and per-item peaks expose subsequent pressure. |
| Worker OOM or telemetry failure | OOM.json/STOP and exit 42 stop without retry; sampler failure marks the return diagnostic. A killed operator with no result becomes a failed return when the native controller survives. |
| Controller kill or run-directory refusal | A controller kill can prevent packaging. Any refusal after creation requires a fresh run name, and killed work requires the coordinator's decision before another attempt. |
| Instrument or numerical drift | Full binding/settings and provenance checks precede the fixed answer/placement ruling. CPU fixtures cannot establish H100/Ada equality. |

The package namespace retains its read-write /tmp bind. The mandated terminator writes /tmp/terminator; HOME, TMPDIR and framework caches point to scratch. The kit does not claim stronger filesystem isolation than the sealed namespace supplies.

## What is not done

The target's extraction/member census, namespace identity/probe, pinned framework imports, preparation, actual disk footprint, card gate, 50-item Ada read, CUDA peaks and device SAME_INSTRUMENT result remain for the coordinator sequence. The coordinator's completed archive staging and hash check are accepted facts. External corpus ingestion is not performed here. Optional ON overlays retain their documented consistency prerequisite.

Build timestamp: Thu Nov 19 19:37:43 UTC 2026. No Git, SSH, scheduler, GPU, network download, paid API, deletion or stopping of another agent's work was used. The review mapping and explicit before/after evidence remain because the dispatch requires regression evidence; other prose describes the delivered behavior.
