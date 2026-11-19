"""Write the delivery report from measured test and patch records."""
import collections
import json
from pathlib import Path
import shutil
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round3';K=W/'kit'
def read(path):return json.loads(path.read_text())
final=read(W/'checks/final_RUNS.json');patched=read(W/'checks/patch_RUNS.json')
assert all(r['returncode']==r['expected_returncode'] for r in final+patched)
assert len(final)==8 and len(patched)==7
integrity=read(W/'checks/PATCH_INTEGRITY.json');manifest=read(K/'patches/MANIFEST.json')
probes=read(W/'checks/cr3_after/PROBES.json')['probes']
assert probes==read(W/'checks/cr3_before/PROBES.json')['probes']
shutil.copytree(W/'checks',K/'checks/round3',dirs_exist_ok=True)
rss=max(r['maxrss_kb'] for r in final+patched)
table=[]
for label,rows in [('Direct',final),('Applied patch',patched)]:
    for row in rows:
        footer=row['test_summary'].replace('\n\n','; ')
        table.append('| '+label+' '+row['name']+' | `'+footer+'` | '+str(row['returncode'])+' | '+str(row['maxrss_kb'])+' | [full output](checks/round3/'+Path(row['output']).name+') |')
probe_table=[]
for row in probes:
    counts=row.get('identical',{})
    probe_table.append('| `'+row['probe']+'` | '+row['verdict']+' | '+str(counts.get('answer','—'))+' | '+str(counts.get('call_placement','—'))+' |')
now=subprocess.check_output(['date','-u'],text=True).strip()
recipe=(K/'COORDINATOR.md').read_text().split('\n',1)[1]
report=f'''VERDICT: DONE The third-review fixes, regression tests and delivery patch are complete; the target read waits for a free card on trinity-2-28.

The kit runs A10b read A, Orchard job **173060**, step **400**, run `6ed2c7aa`, artifact SHA256 `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. The sealed source, settings, input pins and item order remain unchanged. The coordinator verified all 21 staged archive parts at 18:37Z; the kit authenticates them again before use. All eight target cards are busy. No target or GPU command ran during this build.

## Numbers: measured, pinned and estimated

| Quantity | Value | Basis |
|---|---:|---|
| Direct CPU tests | **119 passed** | Measured: 39 base, 18 review1, 7 preparation, 7 bootstrap, 17 review2, 12 stage2, 19 review3. |
| Fresh applied-patch tests | **119 passed** | Measured on a newly bootstrapped input copy after zero-fuzz patch application. |
| New regressions against preserved kit | **19 fail** | Measured: 18 failed assertions and one missing-private-path refusal; all 19 pass after the fixes. |
| Round-three reviewer fixtures | **18 outcomes preserved** | Measured: 6 SAME_INSTRUMENT, 8 DIAGNOSTIC_ONLY, 4 refusals. Positive and diagnostic cases retain the fixed ruling. |
| Round-two reviewer fixtures | **7/7 DIAGNOSTIC_ONLY** | Measured replay of every supplied comparison. |
| Maximum individual test-process RSS | **{rss} kB** | Measured with `/usr/bin/time -v`; checks ran serially, with CUDA hidden and at most eight threads. |
| Preserved delivery snapshot | **1086 files** | Measured hashes in `checks/round3/ROUND2_SNAPSHOT.json`; `out_round2/` remains unchanged. |
| Authenticated input files unchanged | **944 files** | Measured against the input mirror, including all 927 sealed source files. |
| Workspace at patch verification | **{integrity['workspace_regular_file_bytes']} bytes** | Measured regular-file sizes under L at {integrity['utc']}; final publication measurement is in `checks/round3/DELIVERY_INTEGRITY.json`. |
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
{chr(10).join(table)}

The measured validation commands were:

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B {W/'validate.py'}
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B {W/'validate.py'} {W/'applied_verified/read228'} patch
```

Each suite command is `nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B <test-file>`, except `test_review3.py`, which uses `-I -S -B`. `bash tests/run_tests.sh` runs all seven suites with that distinction and local caches. The positive integration uses a separate CPU interpreter; its worker and card observations are doubles. Real CUDA kernels, target runtime imports and device parity are not tested here.

The 19 negative regressions use the same test file with READ228_REVIEW3_KIT={L/'out_round2'}. The missing-private-path case raises Refusal on preserved code; it is reported as a unittest error and passes on the fixed code. The other 18 cases fail assertions. None is a target run or a killed job.

## Reviewer fixture replay

Both replays ran `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -S -B {W/'replay_review3.py'} --kit <kit> --out <output>`, once with `out_round2` and once with `work/round3/kit`. [Before output](checks/round3/cr3_before.txt), [after output](checks/round3/cr3_after.txt) and [full comparison records](checks/round3/cr3_after/PROBES.json) retain exact outcomes and reasons. The summaries match for all 18 fixtures.

| Reviewer fixture | Verdict | Identical answers | Identical placements |
|---|---|---:|---:|
{chr(10).join(probe_table)}

The fixed ruling remains at least 49/50 identical answers and 50/50 identical call placements, subject to all eligibility checks. Traces are diagnostics. Provenance establishes consistency, not hardware attestation.

## Additive patch and integrity

[01_trinity_adapter.diff](patches/01_trinity_adapter.diff) adds **{len(manifest['files'])} files**, **{manifest['patch']['bytes']} bytes**, under `read228/` against the supplied input tree. Its SHA256 is `{manifest['patch']['sha256']}`. [patches/MANIFEST.json](patches/MANIFEST.json) pins every patch file. DELIVERY_MANIFEST.json pins the whole delivery except itself.

The adapter requires explicit entry-point invocation; operator execution requires `--execute`, worker observation requires `--observe`, and optional caches default OFF. No existing production file changes. The patch includes tests and the coordinator recipe. Generated REPORT/check logs accompany the delivery rather than entering the patch. [PATCH_INTEGRITY.json](checks/round3/PATCH_INTEGRITY.json) records syntax checks, Python 3.6 bootstrap grammar, shell checks, input hashes and zero-fuzz application.

```bash
date -u
nice -n 10 patch --batch --fuzz=0 -p1 \\
  -d {W/'applied_verified'} \\
  -i {K/'patches/01_trinity_adapter.diff'}
```

That command returned 0; [exact output](checks/round3/patch_command_1.txt) is retained. Bootstrap before and after application also returned 0 ([input](checks/round3/patch_command_0.txt), [adapter assets](checks/round3/patch_command_2.txt)). All 119 tests passed on the applied patch.

## Exact coordinator sequence
{recipe}

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

Build timestamp: {now}. No Git, SSH, scheduler, GPU, network download, paid API, deletion or stopping of another agent's work was used. The review mapping and explicit before/after evidence remain because the dispatch requires regression evidence; other prose describes the delivered behavior.
'''
(K/'REPORT.md').write_text(report)
print(now)
print('REPORT.md written from exact outputs; 119 direct and 119 applied-patch tests pass.')
