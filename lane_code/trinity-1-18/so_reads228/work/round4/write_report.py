"""Write the final report from exact retained validation evidence."""
from pathlib import Path
import json,re,subprocess
L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round4';K=W/'kit'
def read(path):return json.loads(path.read_text())
release=read(W/'checks/release_RUNS.json');patch=read(W/'checks/patch_RUNS.json')
assert len(release)==len(patch)==8 and all(r['returncode']==0 for r in release+patch)
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests',r['summary']).group(1)) for r in rows)
assert count(release)==count(patch)==140
integrity=read(W/'checks/RELEASE_PATCH_INTEGRITY.json');manifest=read(K/'patches/MANIFEST.json')
now=subprocess.check_output(['date','-u'],universal_newlines=True).strip()
rows=[]
for r,p in zip(release,patch):
 rows.append('| `test_'+r['case']+'.py` | '+str(re.search(r'Ran (\d+) tests',r['summary']).group(1))+' | '+str(r['returncode'])+' / '+str(p['returncode'])+' | ['+r['output']+'](checks/round4/'+r['output']+'), ['+p['output']+'](checks/round4/'+p['output']+') |')
outputs='\n'.join('`test_'+r['case']+'.py` ('+label+'):\n\n```text\n'+r['summary']+'\n```\n' for label,data in [('direct',release),('applied patch',patch)] for r in data)
commands='\n'.join('```bash\n'+' '.join(r['argv'])+'\n```' for r in release)
env=(K/'ENVIRONMENT.md').read_text();mapping=env[env.index('The physical runtime root is'):env.index('The adapter calls')]
coordinator=(K/'COORDINATOR.md').read_text().split('\n',1)[1]
report=f'''VERDICT: DONE All six target-refusal fixes are delivered for kit2; 140 CPU tests pass directly and from the applied patch, while target staging and the GPU read remain coordinator work.

Completed on trinity-1-18: {now}. The shipped delivery is preserved in `../out_round3/`. This kit stages every runtime group under `/scratch/jjyeung/orch_n30/reads228/private_rt/`, uses an all-archive preflight before extraction, and executes the package through its own private namespace. The default reader remains OFF and all authenticated A10b bytes remain unchanged.

## Numbers and evidence

| Quantity | Value | Basis |
|---|---:|---|
| Runtime archive parts | 13; 10,497,433,600 bytes | Read from package ORCHARD_ASSETS and MISSING pins; target bodies were not available here. |
| Runtime headers | 115,837: r0 41,535; r1 69,177; r2 5,125 | Counted from the three supplied lists; hashes and groups are in RUNTIME_LISTS.json. |
| Expanded runtime file contents | 10,371,055,588 bytes | Sum of regular-file sizes in the supplied lists; excludes directory allocation and symlink metadata. This is not a measured target disk footprint. |
| r0 / r1 / r2 expanded file bytes | 1,579,308,957 / 8,386,282,204 / 405,464,427 | Read from the lists. |
| Planned retained footprint | 94,537,720,332 bytes | Estimate: pinned input/runtime parts, input expansion, listed runtime expansion, conservative 3,450,062,241 shared-SAM allowance, and estimated 5 GB operating allowance. Shared SAM is never used. |
| Enforcement | 40 GB runtime expansion cap; 145 GB staged-footprint check; 150 GB total limit; 200 GiB free floor | Configured limits. The footprint counts private_rt, including symlink metadata, without following directory links into shared environments. |
| Direct / applied-patch tests | {count(release)} / {count(patch)} passed | Measured; all eight suites, exact logs below. |
| Before-fix regressions | 21 cases fail; 23 assertion failures including subtests | Measured against out_round3; no test errors. |
| Preserved A10b files | 944 | SHA256-verified against the input mirror, delivery and applied patch. |
| Preserved shipped-delivery files | 1,161 | Verified against out_round3/DELIVERY_MANIFEST.json. |
| Patch | {manifest['patch']['bytes']:,} bytes; 75 additive files | Measured; no existing input file changes. |
| Highest direct / applied-test MaxRSS | {max(r['maxrss_kb'] for r in release):,} / {max(r['maxrss_kb'] for r in patch):,} KiB | `/usr/bin/time -v` measurements; below 30 GB. Tests use at most six CPUs; concurrent header checks kept the total below eight. |
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

{mapping}
`namespace228.py:32–47` preserves the package binds and appends the control and private logical-root binds. `namespace228.py:55–62` adds only the executing operator's output directory. The real-bwrap fixture reads private runtime, m/ap and logical-root sentinel bytes, preserves a shared sentinel, sees the kit operator file, and cannot see the x helper. No authenticated symlink, pyvenv.cfg, settings file or reader source is rewritten.

## Patch and exact validation

[01_trinity_adapter.diff](patches/01_trinity_adapter.diff) is additive against the authenticated A10b input tree. SHA256: `{manifest['patch']['sha256']}`. It changes no existing file. Activation requires explicit adapter entry-point invocation; observation requires `--observe`; optional cache extensions require `--on` and default OFF.

[Patch integrity](checks/round4/RELEASE_PATCH_INTEGRITY.json) records the exact bootstrap, `patch --batch --fuzz=0 -p1`, and asset-install commands. The patch applies without offsets or fuzz. All 75 delivered adapter files match the applied patch, all 944 authenticated input files retain their hashes, Python 3.6 grammar checks pass for the bootstrap modules, and shell syntax checks pass. Full patch command outputs are [bootstrap](checks/round4/release_patch_command_0.txt), [apply](checks/round4/release_patch_command_1.txt), and [asset install](checks/round4/release_patch_command_2.txt).

The validation driver sets CUDA_VISIBLE_DEVICES empty, PYTHONDONTWRITEBYTECODE=1, OMP/MKL/OPENBLAS thread limits to eight, TOKENIZERS_PARALLELISM=false, and local caches under work/round4. Torch tests call `torch.set_num_threads(8)` before tensor work. Both controller suites use `-S`; only the separate CPU operator fixture has site-packages. The bootstrap suite uses actual system Python 3.6.8.

| Suite | Tests | Direct / patch exit code | Exact complete outputs |
|---|---:|---|---|
{chr(10).join(rows)}

The exact direct test commands are:

{commands}

The applied-patch commands use `work/round4/applied_release/read228/tests/` in place of `work/round4/kit/tests/`; every complete argv and return code is in [release_RUNS.json](checks/round4/release_RUNS.json) and [patch_RUNS.json](checks/round4/patch_RUNS.json). These are the unedited unittest summary outputs:

{outputs}

The seven supplied review-2 comparisons remain DIAGNOSTIC_ONLY. All 18 review-3 outcomes remain unchanged: four refusals, six SAME_INSTRUMENT controls and eight diagnostics. [Review-2 exact output](checks/round4/cr2_replay.txt); [review-3 exact output](checks/round4/cr3_replay.txt). No comparison or reader decoding code changed in this round.

The existing [framework evidence](FRAMEWORK_EVIDENCE.md) cites installed torch 2.11 source file:line for every framework API used by the adapter, with official documentation links retained from the authenticated delivery. No framework behavior was added here. The package q/env.json separately pins reader torch 2.13.0+cu130, torchvision 0.28.0+cu130, transformers 5.19.0 and scipy 1.14.1; those versions still require the target's exact import probe.

## Exact coordinator sequence: stage first, then one card-gated run

{coordinator}

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
'''
(K/'REPORT.md').write_text(report)
print(now)
print('Report generated from eight passing suites per tree; 140 direct + 140 applied tests.')
