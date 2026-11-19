"""Publish current evidence and the requested review mapping; no inferred target results."""
import json
from pathlib import Path
import shutil
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round2';K=W/'kit'
def read(p):return json.loads(p.read_text())
direct=read(W/'checks/final_RUNS.json');applied=read(W/'checks/patch_RUNS.json')
manifest=read(K/'patches/MANIFEST.json');integrity=read(W/'checks/PATCH_INTEGRITY.json')
before=read(W/'checks/probes_before/PROBES.json');after=read(W/'checks/probes_after/PROBES.json')
assert all(v['returncode']==v['expected_returncode'] for v in direct+applied)
assert all(v['verdict']=='SAME_INSTRUMENT' for v in before['comparisons'])
assert all(v['verdict']=='DIAGNOSTIC_ONLY' and not v['eligible'] for v in after['comparisons'])
for path in (W/'checks').rglob('*'):
    if path.is_file():
        target=K/'checks'/path.relative_to(W/'checks');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
rss=max(v['maxrss_kb'] for v in direct+applied)
table=[]
for label,rows in [('Direct',direct),('Applied patch',applied)]:
    for row in rows:
        footer=row['test_summary'].replace('\n\n','; ')
        name=Path(row['output']).name
        table.append(f"| {label} {row['name']} | `{footer}` | {row['maxrss_kb']} kB | [full output](checks/{name}) |")
probe_table=[]
for row in after['comparisons']:
    reasons='; '.join(row['ineligibility_reasons'])
    probe_table.append(f"| `{row['probe']}` | DIAGNOSTIC_ONLY | {reasons} |")
cases=read(W/'checks/COMPARE_CASES.json')['cases'];case_table=[]
for name,row in cases.items():
    i=row['identical'];case_table.append(f"| {name} | {i['answer']}/50 | {i['call_placement']}/50 | {i['trace']}/50 | {row['verdict']} |")
shipping=r'''set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
stage=/scratch/jjyeung/orch_n30/reads228
kit_dir="$stage/kit"
test ! -e "$kit_dir"
nice -n 10 mkdir -p "$kit_dir" "$stage/ssh"
# One reused compute-to-compute connection over InfiniBand; no head-node relay.
ssh -o ProxyJump=none -o ControlMaster=auto -o ControlPersist=30m \
  -o ControlPath="$stage/ssh/cm-%C" trinity-1-18.ib \
  'nice -n 10 tar -C /scratch/jjyeung/orch_n30/so_reads228/out -cf - .' \
  | nice -n 10 tar --extract --skip-old-files --directory "$kit_dir"
date -u
nice -n 10 /usr/bin/python3 -I -s -B - "$kit_dir" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'DELIVERY_MANIFEST.json').read_text())
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
# CARD is one chosen card index/UUID; no polling or automatic retry.
test -n "${CARD:?Set CARD to the chosen index or UUID}"
bash "$kit_dir/coordinator228.sh" "$CARD" "$stage/runs/a400check1"
'''
report=f'''VERDICT: DONE The second-review kit fixes and CPU regressions are complete; target namespace, preparation and Ada parity still require execution on trinity-2-28.

The kit targets A10b read A, Orchard job **173060**, step **400**, run `6ed2c7aa`, artifact SHA256 `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. All second-review probes refuse. The sealed source, package configuration, item order and reader defaults remain unchanged. The coordinator's 18:06Z ruling treats the 13 runtime parts as staged; the kit verifies their hashes and never fetches.

## Numbers: measured, pinned and estimated

| Quantity | Value | Evidence or status |
|---|---:|---|
| Direct current CPU tests | **100 passed** | Measured: 39 base, 18 first-review, 7 prepare, 7 bootstrap, 17 second-review, 12 stage/namespace/ingest. |
| Fresh applied-patch CPU tests | **100 passed** | Measured after authenticating the input copy, applying the additive patch and bootstrapping its A10b assets. |
| Second-review tests on preserved code | 17 tests, 34 failed assertions; 12 tests, 12 failures | Measured; subtests contribute multiple assertions. The comparator positive control passes. No baseline test errors. |
| Reviewer fixtures | **8 directories, 7 comparisons** | Measured: all seven accept on preserved code and all seven refuse on revised code; the eighth directory is the paired edited reference. |
| Maximum individual test-process RSS | **{rss} kB** | Measured by `/usr/bin/time -v`; tests ran serially with CUDA hidden and thread limits of eight. |
| Preserved delivery snapshot | {integrity['round1_preserved_files']} files | Measured byte equality of `out_round1/` and the untouched delivery before publication. |
| Authenticated base files unchanged | {integrity['base_original_files_unchanged']} files | Measured against the input mirror, including all 927 sealed source files. |
| Workspace at patch verification | {integrity['workspace_regular_file_bytes']} bytes | Measured sum of regular-file sizes under L at {integrity['utc']}; below 3 GB. Final delivery measurement is in checks/DELIVERY_INTEGRITY.json. |
| Runtime parts | 13 parts; 10,497,433,600 bytes | Pinned in MISSING.json; staged by coordinator ruling, not read from 2-28 during this build. |
| Input archives | 32,613,048,320 packed bytes; 32,606,120,583 expanded bytes | Package pins in STAGE_PLAN.json. |
| Target peak footprint | 124,166,664,744 bytes | **Estimate** from pinned inputs, retained archives, 40 GB runtime expansion allowance and 5 GB operating allowance. |
| Target staging limits | 145 GB staged; 150 GB overall; 200 GiB free floor | Configured limits, not target measurements. All archive runtime roots enter the footprint check. |
| Actual target namespace/import/prepare/GPU runs | **0 / 0 / 0 / 0** | Not performed; this dispatch permits only local CPU work on trinity-1-18. |

The runtime receipt pins torch 2.13.0+cu130, torchvision 0.28.0+cu130, transformers 5.19.0 and scipy 1.14.1. These are reader receipt values. The mandated CPU test interpreter uses torch 2.11; [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) cites installed source lines and official documentation for framework behavior. Bootstrap contracts ran on the mandated Python 3.12; the five bootstrap modules also pass Python 3.6 grammar parsing. Target Python 3.6.8 execution remains a deployment check.

## Review round 2: finding -> fix -> test

| Finding | Fix and decision | Regression evidence |
|---|---|---|
| HIGH 1: staged runtime needs verification and member evidence | `--verify-runtime-pins` hashes every MISSING.json target. Extraction authenticates all ordered parts, enumerates members at run time and caps expansion. STAGE_CHECK records member lists and checks wrapper, boot module, CPython, pyvenv.cfg, encodings and framework entry modules before the namespace version probe and sealed preparation. A refused stage check also retains the inventory. No member list or target measurement is invented. | `test_high1_runtime_inventory_records_all_names`, `test_high1_runtime_members_must_supply_prepare`, `test_stage_refusal_persists_runtime_member_list`; all fail on preserved code and pass now. Existing wrong-part/last-part hash tests pass. |
| MEDIUM 2: incomplete instrument comparison | The comparator compares the entire binding and settings dictionaries, including missing and additional keys, and names every differing key in its reasons. | `test_medium2_whole_binding`, `test_medium2_whole_settings`, `test_medium2_missing_keys`; all fail before and pass after. All supplied probes refuse; exact reasons appear below. |
| MEDIUM 3: another lane owns d/k and d/s | The kit authenticates and lists input members before extraction, uses GNU tar `--skip-old-files`, then checks every member's size/hash. It preserves existing bytes, inode and mode. A complete destination scan permits only archive members and exact known/recorded preparation products. Unexplained files stop staging before imports or preparation, with their paths listed. The coordinator resolves shared-file conflicts with swarm_build. | `test_medium3_conflicts_list_all_and_preserve_other_lane` checks two mismatches and confirms no new file was extracted; `test_medium3_matching_member_is_skipped_without_metadata_change` checks literal tar flags and preserved metadata; `test_medium3_unexplained_files_refuse_with_list` and `test_medium3_stage_refuses_extras_before_import_or_prepare` check the other refusal. All fail before and pass after. |
| MEDIUM 4: runtime remap edits authenticated files | The adapter calls the package's own `orchard_job.namespace` with its sj/fsw/m-ap/uv binds. Only argv[0] selects the coordinator-approved `/usr/bin/bwrap`. NAMESPACE and LOCAL_RUN record the executed binary's measured identity and the package bwrap pin. Absolute runtime links, a4 members and pyvenv.cfg remain unchanged. **Decision: namespace only; no relocation fallback.** A target failure records its tested reason and stops. The comparator also reports a supplied legacy runtime-relocation deviation as ineligible. | `test_medium4_calls_sealed_namespace_and_records_both_bwrap_identities`, `test_medium4_runtime_absolute_link_bytes_preserved`, `test_medium4_no_relocation_of_authenticated_bytes`, `test_medium4_namespace_used_without_relocation`, and `test_namespace_probe_maps_preserved_absolute_python_link`; all fail before and pass after. Preparation and worker integration tests check namespace invocation. Actual bwrap execution awaits 2-28. |
| LOW 5: ignored failed-run status | Eligibility requires explicit SUMMARY failure=None, integer completed>=50 and no root FAILED.json. Missing SUMMARY refuses. | Separate `test_low5_*` cases for failure, insufficient completion, FAILED marker and missing SUMMARY all fail before and pass after. |
| LOW 6: mutable reference metadata | FIRST50 pins the SHA256 of reference IDENTITY and every included reference journal environment, in addition to the row/export pins. The included reference is the authenticated first-50 prefix, with one journal environment; both metadata files are pinned. Pin inventory changes also refuse. | `test_low6_reference_identity_pin`, `test_low6_reference_environment_pin`, `test_low6_first50_contains_all_reference_pins`; all fail before and pass after. Joint reference/candidate edits cannot recover eligibility. |
| LOW 7: --settings changes imports | **Decision: drop the argv append**, because Orchard imports h1eval with entry and dispatch arguments only. The adapter preserves that branch; the sealed worker_args still passes settings to launch.main as designed. Observation still preimports framework/reader modules and requires the numerical comparison. | `test_low7_no_settings_import_append` fails before and passes after. Sealed resolver and orchestration tests pass. |
| LOW 8: wrapper HOME/XDG/TMPDIR leaks | run228.sh, read228.sh, compare228.sh and coordinator228.sh source the same local environment block. HOME, all XDG locations, TMPDIR and framework caches resolve to scratch. | `test_low8_all_wrapper_environments` executes all three direct wrappers against an environment-recording interpreter; all three subtests fail before and pass after. |
| LOW 9: narrow OOM recognition | RuntimeError messages containing `out of memory` or `alloc_failed` count as OOM, alongside torch.cuda.OutOfMemoryError. | `test_low9_cuda_oom_variants` and `test_low9_cuda_oom_variants_write_marker_and_stop` fail before and pass after. Both variants write OOM.json/STOP, generate once and commit nothing. |
| INFO 10: unpack and ingest handoff | Coordinator invokes the unchanged unpacker through its authenticated wrapper into `kit/ingest/<run-name>`. Ingest reads SUMMARY and the comparison, not EXIT.status. The kit must be exactly `/scratch/jjyeung/orch_n30/reads228/kit`; a/6 and unpack containment require it. | `test_info10_coordinator_unpacks_for_ingest` and `test_info10_ingest_uses_summary_despite_failed_exit_status` fail before and pass after. The original unpacker's partial-envelope test passes. |

The supplied d/s inventory reports 251 files owned by swarm_build. This build does not infer which files conflict with a2.tar; target staging lists the exact conflicts. No other lane's file was moved, overwritten or deleted.

## Review round 1: finding -> fix -> test

The standing first-review requirements remain covered by the 18-test review suite, 39 base tests and preparation/bootstrap tests. The active runtime policy is the namespace policy above.

| Finding | Current behavior | Passing coverage |
|---|---|---|
| Environment and preparation | Exact receipt versions; preparation/stage checks precede the GPU gate; READY is checked without relaunch. | Version, audit-root, preparation-order and idempotence tests. |
| Transfers | Coordinator supplies staged bytes; the kit has no fetch/governor/SSH actions. | Stage-plan and missing-part refusal tests. |
| Placement | Only index/family/call/served/at_token determine placement; one-ulp stage-1 drift stays in trace. | `test_high3_one_ulp_stage1_drift_preserves_instrument` and call-moved tests. |
| Provenance | LOCAL_RUN backend/host/OFF, Ada card, all journal hosts and distinct RETURN_ID are mandatory. | Positive local fixture and five provenance refusals. |
| Sealed runner metadata | The adapter calls sealed runner.run with launcher=; IDENTITY, projection and dispatch files retain the Orchard layout. | Runner integration, original member/schema comparison and unchanged unpacker. |
| Environment/policy/write boundaries | Worker identity/cache roots are local; OFF checks read settings; both vnice scripts are pinned; test/output writes stay under allowed scratch. | Worker environment, OFF settings, policy hash and output-containment tests. |
| Gate, memory and receipt | Two idle readings, UUID lock, worker process group, OOM stop and partial-return handling remain. | Idle, observer, process-group and return tests. |

## Exact tests and outputs

| Run | Exact unittest footer | Measured MaxRSS | Exact complete output |
|---|---|---:|---|
{chr(10).join(table)}

[final_RUNS.json](checks/final_RUNS.json) and [patch_RUNS.json](checks/patch_RUNS.json) record every exact argv, environment override, UTC start, exit code and output path. The before tests use the same regression files with READ228_REVIEW2_KIT=`{L/'out_round1'}`. The expected exit code is 1 before and 0 after. The measured serialized commands were:

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B {W/'validate.py'}
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B {W/'validate.py'} {W/'applied_verified/read228'} patch
```

Each test process runs `nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B <test-file>`; JSON records the full test-file path. From the delivered kit, `bash tests/run_tests.sh` runs every current test with the same interpreter and thread limits.

Reviewer replay used `work/round2/replay_probes.py --kit out_round1 --out work/round2/checks/probes_before` and then `--kit work/round2/kit --out work/round2/checks/probes_after`, each prefixed by the mandated nice/Python command. [Before stdout](checks/probes_before.txt), [after stdout](checks/probes_after.txt), [before results](checks/probes_before/PROBES.json) and [after results](checks/probes_after/PROBES.json) retain exact outputs. The edited reference `cr2probek3q1gfoz/ref` is paired with `cr2probexe5qlhqd/ret`.

| Reviewer candidate | Revised verdict | Exact ineligibility reasons |
|---|---|---|
{chr(10).join(probe_table)}

Each binding/settings regression also runs with a clean SUMMARY, so missing summaries do not mask those checks. The shared edited-reference probe independently checks the reference hash.

| Synthetic CPU case | Answers | Placements | Traces | Verdict |
|---|---:|---:|---:|---|
{chr(10).join(case_table)}

[COMPARE_CASES.json](checks/COMPARE_CASES.json) and adjacent per-item JSON files record these measured fixture results. They are not GPU measurements.

## Additive patch and integrity

[01_trinity_adapter.diff](patches/01_trinity_adapter.diff) adds **{len(manifest['files'])} files**, **{manifest['patch']['bytes']} bytes**, under `read228/` against the supplied A10b input. It changes no existing production file. Its SHA256 is `{manifest['patch']['sha256']}`. [patches/MANIFEST.json](patches/MANIFEST.json) pins every added file; DELIVERY_MANIFEST.json pins the complete delivery except itself.

New entry points explicitly activate the adapter. Observation requires `--observe`; cache overlays default OFF. The original input tree remains byte-identical. [PATCH_INTEGRITY.json](checks/PATCH_INTEGRITY.json) records the authenticated bootstrap, zero-fuzz application, unchanged base hashes, Python syntax/3.6 grammar checks, shell syntax checks and preserved snapshot. The exact patch command returned 0:

```bash
nice -n 10 patch --batch --fuzz=0 -p1 \\
  -d {W/'applied_verified'} \\
  -i {K/'patches/01_trinity_adapter.diff'}
```

[Patch stdout](checks/patch_command_1.txt) and both [input-bootstrap](checks/patch_command_0.txt) / [patched-bootstrap](checks/patch_command_2.txt) outputs are retained. The fresh applied adapter passed all 100 tests.

## Exact coordinator sequence on trinity-2-28

The following shipping command is for the coordinator's existing compute-node session; it was **not executed by this agent**. It uses one persistent InfiniBand connection, copies the finished kit, and verifies its manifest. It requires the kit path to be absent, so an existing delivery cannot be silently overwritten. If it exists, the coordinator resolves its own kit placement before proceeding. The command never touches swarm_build's d/k or d/s.

```bash
{shipping}```

Run that invocation once, after governed staging has completed. Its coordinator script is reproduced verbatim below for review; do not execute the sequence a second time. The single run228 invocation performs the card gate and 50-item run while retaining its UUID lock.

```bash
{(K/'coordinator228.sh').read_text()}```

The final `CORPUS_INGEST.json` names `kit/ingest/a400check1` only when SUMMARY has no failure, at least 50 completed items, no FAILED marker and an eligible SAME_INSTRUMENT comparison. EXIT authenticates the partial archive but continues to label a 50/636 envelope FAILED. The corpus consumer must use SUMMARY; no external corpus database is edited here.

## What could go wrong and how we would notice

- **Shared staging conflict:** differing archive members or unexplained d/s/d/k files refuse with a complete list for that check. Files remain in place. STAGE_CHECK captures stage refusal evidence; extraction errors print the mismatches and keep a log. The coordinator resolves ownership; the kit never cleans up another lane.
- **Runtime or namespace mismatch:** missing/wrong part pins stop extraction; absent required members stop staging; wrong root ownership, bwrap version, namespace creation, imports or audit roots stop before the gate. NAMESPACE.json records the target bwrap probe. No fallback edits pinned bytes.
- **Partial preparation or disk pressure:** an existing restore without READY refuses a relaunch; READY/product hashes must remain valid. Runtime expansion, complete staged roots and the free-space floor enforce the budget. Actual target expansion remains unmeasured.
- **A card becomes busy or OOMs:** the gate refuses current occupancy. Another program can still allocate afterward. One-second nvidia-smi sampling and per-item peaks expose contention; the first recognized OOM writes OOM.json and stops without retry.
- **A kill prevents a receipt:** a worker-group exit can leave the separate control process able to package failure; killing the control process can prevent that. A failure before journals exist can make the unchanged unpacker refuse.
- **Numerical or instrument drift:** full binding/settings equality, reference pins, SUMMARY and provenance are eligibility conditions. Answer/placement differences then decide the fixed 49/50-and-50/50 rule. Neither byte equality nor CPU doubles establish H100/Ada parity.

The pinned vnice/terminator scripts remain small read-only `/data3` inputs; the cluster terminator's `/tmp/terminator` write is the required exception to scratch output. Audit/cache-root differences and observation timing remain documented limits. The provenance checks are consistency checks, not attestation.

## What is not done

No command ran on trinity-2-28. Target runtime hashes, actual archive member lists, system bwrap hash/probe, native CPython startup, framework imports, full preparation, live card gate, 50-item Ada execution, CUDA peaks and the device SAME_INSTRUMENT verdict await the coordinator sequence. The staging decision is accepted; this build does not claim to have measured those staged bytes. External corpus ingestion/scoring is not performed. Optional ON overlays remain unavailable until their documented consistency issue is resolved.

This build used no Git, SSH, scheduler, GPU, paid model API, deletion or agent stopping. The no-archaeology skill governs the report's current-state prose. The explicit before/after test evidence and the two review mapping sections are retained because the dispatch requires them; they establish regressions rather than narrate implementation history.
'''
(K/'REPORT.md').write_text(report)
print(subprocess.check_output(['date','-u'],text=True).strip())
print('REPORT.md written; exact check logs copied; patch inputs unchanged.')
