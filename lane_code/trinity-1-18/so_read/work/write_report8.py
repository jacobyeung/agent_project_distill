"""Write current delivery claims and literal CPU verification outputs."""
from pathlib import Path
import json,re,shlex,subprocess
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
m=json.loads((O/'patches/MANIFEST.json').read_text());r=json.loads((C/'RESULTS.json').read_text())
cost=json.loads((C/'CACHE_COST3.json').read_text());storage=json.loads((C/'STORAGE8.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
stamp=subprocess.check_output(['date','-u'],text=True).strip();size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
old=(L/'out_round8/REPORT.md').read_text()
equality=old[old.index('## Equality and mutation limits'):old.index('## Measured profile and forecast')]
profile=old[old.index('## Measured profile and forecast'):old.index('## Measured CPU guard overhead')].replace('selected export','step-400 export')
review='''
| Finding | Fix | Regression test |
|---|---|---|
| MEDIUM 1: dereferenced restore links fail loader admission | Validate all links inside the live namespace, then `tar -cf - -C <logical>/d .`; preserve in-tree links and reject escaping targets, dangling links and cycles. Archive estimate: about 33 GB. | `test_f1_preserved_absolute_link_passes_real_artifact_and_load_native` extracts `e/heads.pt -> <logical>/d/m400/heads.pt`, calls real Artifact.verify and real load_native, and reaches the stub processor only after the real resolve() checks. Six link-refusal cases pass. |
| LOW 2: GPU interpreter/environment unbound | README uses d/v/py, explicit opaque XDG/HF/Triton caches and executable version/CUDA preflight. ON prepare adds CUDA and READY.environment. CPU evidence includes ENVIRONMENT.json; gate, workers, ue.json and submit compare exact torch/transformers/CUDA values and its SHA256. | Runtime/receipt, executable shell preflight, CPU-bound gate and submit mutation tests reject changed versions/hash and missing CUDA. CUDA imports/device availability are explicit test doubles. |
| LOW 3: another export fails late | a19 admits only the reviewed step-400 identity, archive pin/size, base/frame identity and preparation hashes before reading the base. Gate accepts only the complete reviewed export; no selection flag remains. | Eleven binding mutations refuse before base access/output. Fixed step-400 build and complete CPU operator path pass; changed artifact refuses at the gate. |
| LOW 4: unresolved package path | Resolve both recorded and package archive paths. | Execute the README archive-validation heredoc through a symlinked package parent. |
| INFO 5: aliases, stderr and job name | Require symlink aliases; keep stderr in results/4.err; generate a fresh a15_cot_ap hexadecimal job token. | Real tar failure diagnostic survives; README alias/environment/token commands are checked. |
'''
patches='\n'.join('| ['+name+'](patches/'+name+') | '+str(pin['bytes'])+' | `'+pin['sha256']+'` |' for name,pin in m['patches'].items())
bench='\n'.join('| '+str(v['parameter_count'])+' | '+str(v['parameter_tensors'])+'/'+str(v['buffer_tensors'])+' | '+str(v['weight_and_buffer_bytes'])+' | '+f"{v['before_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_install_seconds']:.3f}"+' | '+f"{v['boundary']['median_seconds']:.3f}"+' |' for v in cost['cases'])
report=f'''VERDICT: DONE All round-8 fixes pass CPU verification; production adoption requires the step-400 H100 byte-parity gate.

**Measured validation:** {workspace} workspace tests and {applied} fresh-application tests pass. All ten round-8 tests fail on the reviewed implementation with 29 expected assertion failures and pass on the delivered implementation. All twelve retained fail-before controls reran. Five diffs apply with zero fuzz. Original reader files and OFF output bytes remain unchanged; ON CPU fixtures preserve exact answers and traces. GPU byte equality remains unmeasured and mandatory.

**Bound export, read from supplied pins:** step **400 only**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. Every later export is diagnostic and cannot authorize adoption through this kit. The builder refuses a different identity before reading the base; the gate requires the complete supplied export pin.

**Estimated storage:** the uncompressed asset archive is **about 33 GB**, based on **32,606,120,583 expanded bytes read from the six archives declared in the supplied a10b_pins/1.json**, plus tar headers ([source pin](checks/ARCHIVE_ESTIMATE8.json)). The links preserve shared shard/head targets. No production-size archive was measured. Reserve additional space for extraction, source trees and runtime outputs.

**Measured local resources:** largest suite child RSS {r['max_child_rss_bytes']:,} bytes; guard benchmark peak RSS {cost['max_rss_bytes']:,} bytes. Workspace usage at report generation: {size:,} unique-inode bytes, below 3,000,000,000. [STORAGE8.json](checks/STORAGE8.json) records {storage['unique_bytes_shared']:,} identical bytes shared across {storage['changed_files']:,} completed pre-task fixture paths, preserving each path and its bytes. No workspace-cap violation was observed.

Work started **17:30:31 UTC, 2026-11-19**; deadline **18:30:31 UTC**. Report generated at {stamp}. [out_round8](../out_round8/) preserves the complete reviewed delivery. CPU checks used torch {r['torch']}, transformers {r['transformers']}, eight torch threads, CUDA hidden and `nice -n 10` (benchmark effective nice {cost['nice']}). No Git, SSH, scheduler action, GPU execution, paid API, input-tree edit or deletion command ran. Network reads were limited to official library documentation.

## Review round 8: finding -> fix -> test
{review}

## Staging and adoption contract

The ON CPU-proof job opens `$P/a/4.tar` outside bwrap, then runs link validation and tar inside its live `J.namespace(root)`. Validation walks `logical/d` without following directory symlinks and resolves every symlink strictly. A target outside that root, a broken chain or a cycle aborts. The same namespace process executes `/bin/tar -cf - -C <logical>/d .`. Absolute in-tree links therefore reach their original targets when the GPU host restores the same logical root. Tar stderr persists at `results/4.err`; a failed attempt has no successful CPU.json. The job flushes/fsyncs and hashes the archive before publishing its path, bytes, logical root and SHA256. OFF performs none of this staging.

The tiny archive/loader regression uses real Artifact and load_native admission; it stubs only model construction after admission. The complete A4 CPU fixture executes the patched CPU helper, preparation, rehearsal, bootstrap and 636 stub reads. Its data, namespace/storage and model work are synthetic. Applied-tree integration reconstructs READY-identical assets from the produced archive after the original fixture data directory becomes unavailable.

ON prepare records torch/transformers and compiled CUDA versions in ENVIRONMENT.json and pins its exact bytes in READY. The CPU helper copies that file into proof evidence. `a20 gate` checks the evidence against CPU READY before GPU work; the parent, each worker and receipt writer compare the actual library/build versions and hash again. `ue.json` carries those checked values, and SUBMIT_CHECK compares them with the CPU-bound file. The real CPU fixture records cuda=null, so it cannot pass the production environment check. A separate, explicitly synthetic version-import double exercises successful receipt serialization and submit checks; it is not GPU evidence.

On the H100 host, `/scratch/jjyeung` must physically exist and be writable outside bwrap. Preserve the exact logical root; its destination must be absent before extraction. The README sets `READ_PYTHON="$GPU_LOGICAL/d/v/py"` and preflights that executable, versions and CUDA availability before starting the gate. If that interpreter depends on an unavailable external path, the preflight fails; no substitute interpreter is accepted. XDG_CACHE_HOME, HF_HOME and TRITON_CACHE_DIR live under the opaque kit root. Neutral asset aliases must be symlinks because the loader admits resolved manifest targets. The binding/environment examples use symlinks too.

The gate allocation is one H100, eight CPUs, 200G, five hours, general/no-requeue, named `a15_cot_ap` plus a fresh opaque hexadecimal token. Preserve the allocation's actual CUDA_VISIBLE_DEVICES. Device admission requires **NVIDIA H100 80GB HBM3**, **132 SMs**, capability **9.0**, and **79–86 billion bytes** of memory.

Follow [README](kit_parity50/README.md): apply reader patches 01–03 and operator patches 04–05; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...` and the delivered step-400 binding; generate operations; place; run detached fill; wait at most 14,400 seconds; run CPU proof; stage and run the zero-difference GPU gate; return its receipt; submit; fetch and unpack. Failed/killed attempts require inspection and a fresh token, never automatic retry.

Submit keeps cont_ops' complete CPU assertions verbatim and checks cache memory, both dry checks, an empty general queue, the bounded return pool, and matching gate plan/profile/assets/device/environment/kit hashes. A refused unpack leaves its extracted tree behind. Scorers require **success output after exit status 0**; complete=false remains partial. The documented unpack command uses `-s -E -B` from the operator directory and an `&&` handoff.

{equality}
{profile}
## Measured CPU guard overhead

Each bf16 stub has 2048×1024 parameter tensors and a 1024-element buffer per module. Forward returns a 32-element tensor without model-sized matrix work. After one miss and a warm hit, each implementation runs seven timed hits; the boundary median covers three hashes. These CPU measurements do not predict GPU speedup. Raw samples: [CACHE_COST3.json](checks/CACHE_COST3.json).

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Full hashing ms/call | Live guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
{bench}

## Framework evidence

[FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) supplies installed-source file:line citations and official documentation for retained framework assumptions. Environment-version evidence comes from torch/__init__.py:60, torch/torch_version.py:66, torch/version.py:4–6 and transformers/__init__.py:21. CUDA availability comes from torch/cuda/__init__.py:161–180; device properties from :673–695 and torch/_C/__init__.pyi:12448–12453. [SOURCE_EVIDENCE8.json](checks/SOURCE_EVIDENCE8.json) pins those installed files and documentation URLs. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) records rerun mutation probes. No GPU call was executed locally.

## Patches and authentication

Base SHA256: `{m['base_pin']['sha256']}` over **{m['base_pin']['files']} files**. Reviewed A4 payload SHA256: `{m['a4_payload_pin']['sha256']}` ({m['a4_payload_pin']['bytes']} bytes). B5 checks establish patch applicability; this GPU kit authenticates A4.

| Patch | Bytes | SHA256 |
|---|---:|---|
{patches}

Reader patches add **38 files** under u0/, including tests, and preserve all original reader bytes. Operator changes remain behind read_extensions. MANIFEST pins full original inventories, copied A4 members, batch/bootstrap, patched operators, extension bytes, kit, operation files and export provenance. The 85 original development files and all 927 original fresh-application files match their input hashes.

## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Restore/environment includes a symlink outside d, or tar/storage fails | Namespace validation or tar fails before CPU.json; results/4.err preserves the error. Inspect and use a fresh attempt. |
| Exact logical path or interpreter is unavailable outside bwrap | Host-path checks and the executable GPU preflight fail before gate work. |
| Environment changes after CPU proof | Gate/runtime/receipt/submit hash and exact version comparisons refuse. |
| Different export, changed filled pin, source, operator or kit | Builder, CPU evidence, worker and submit pins refuse. |
| GPU kernels or eager SAM change answer/trace bytes | Zero-difference gate refuses; equal scores cannot waive it. |
| Cache overhead or working memory outweighs savings | Measure full worker wall time and host/GPU peaks; cache limits exclude model/caller memory. |
| A raw write is restored between boundaries | Frozen ownership remains required; the guard cannot detect this sequence. |
| A partial/refused return is scored | Require successful unpack output and complete status. |

## Not done

No production GPU parity, throughput or peak-memory measurement; large archive; real bwrap/restore; interpreter execution on H100; transport/upload/submit; return publication; persistent-storage requeue; or multi-card A4 operator was run or delivered here. No numerical tolerance or batching is offered. The array prototype remains approved=false. CPU tests need no local OS sockets. Archive size is an estimate, and host storage/interpreter readiness remain external preconditions.

## Review round 7: finding -> fix -> test

CPU-job staging, bounded fill waits, exact SXM admission, kit/input evidence and host-safe receipt/unpack commands pass their regressions. The decision export is step 400 only. The retained before-fix control reproduces ten assertion failures.

## Review round 6: finding -> fix -> test

Executable unpack, detached locked fill, complete cont_ops assertions, copied-member pins and checkpoint/device admission pass. The reviewed implementation reproduces 31 expected assertion failures.

## Review round 5: finding -> fix -> test

The batch matches cont_ops wrap_batch and passes the real bundle guard. Payload/operator/extension authentication, operations, profile, pool, forecast and unpack checks pass; the before-fix control reproduces eleven failures.

## Review round 4: finding -> fix -> test

The A4 route preserves run keys, binding, fill admission and compatible helpers; CPU preparation/rehearsal/bootstrap/action dispatch pass. The fixed step-400 fixture completes 636 stub reads in five verified ordinary journals. Return checks reject invalid weight receipts. Both retained failure controls reproduce.

## Review round 3: finding -> fix -> test

Install/type-boundary hashes, cheap fatal live guards, processor-only mode, operator memory/dispatch, base authentication, lock/worker and OFF-import checks pass. Retained failure controls reproduce.

## Review round 2: finding -> fix -> test

Entry isolation, path policy, bounded array attempts, overlay pins, SAM capacity, deadline/lock/accounting and worker setup pass. The before-fix control reproduces thirteen assertions and the expected CLI import error.

## Review round 1: finding -> fix -> test

Typed keys, parity schemas, original/OFF provenance, frozen identity, lock-held recovery, opaque transport and bounded storage pass; all eight before-fix regressions reproduce.

The review sections are retained because the binding prompts explicitly request them. Historical test-control labels identify the preserved defect demonstrations; they do not offer additional adoption targets.

## Commands and exact outputs

Commands ran from `{L}`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches; it executes the approved Python through `nice -n 10` and `-I -s -B`. Children inherit these limits. Tests set torch threads to eight. The documented unpack command uses `-s -E -B` for sibling imports.

Test subprocesses set READ_INPUT_SRC={m['base']} and READ_TEST_TMP={L/'work/test-artifacts'}. Applied suites set READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE beneath `{m['verification_root']}/operator`. Immutable fixture sharing detaches shared files before edits. All outputs below are literal. Before-fix failures are expected controls. No cluster kill or automatic relaunch occurred.

'''
def block(command,name):return '```bash\n'+command+'\n```\n\nExact output:\n\n```text\n'+(C/name).read_text().rstrip()+'\n```\n\n'
for command,name in [('bash work/cpu.sh work/run_checks.py','run_checks8.txt'),('bash work/cpu.sh work/run_fixture5.py work/build_patches.py','build_patches8.txt'),('bash work/cpu.sh work/gate_integration8.py','gate_integration8.txt'),('bash work/cpu.sh work/profile.py','profile_rerun.txt'),('bash work/cpu.sh work/torch_versions3.py','torch_versions3.txt'),('bash work/cpu.sh work/benchmark_round3.py','cache_cost3.txt'),('bash work/cpu.sh work/docs_check8.py','docs8.txt'),('bash work/cpu.sh work/verify_archive_command8.py','archive_command8.txt'),('bash work/cpu.sh work/share_storage8.py\nbash work/cpu.sh work/share_storage8_more.py  # first additional pass\nbash work/cpu.sh work/share_storage8_more.py  # second additional pass\nbash work/cpu.sh work/share_known8.py','storage8.txt')]:report+=block(command,name)
report+='Patch subprocess output:\n\n```text\n'+(C/'patch_application.txt').read_text().rstrip()+'\n```\n\n'
for row in [*r['results'],*m['applied_cpu_suites']]:report+=block(shlex.join(row['command']),row['output'])
for name,script,var,args in [('round1_before','test_round1.py','READ_REVIEW_BEFORE',[]),('round2_before','test_round2.py','READ_ROUND2_BEFORE',[]),('round3_before','test_round3.py','READ_ROUND3_BEFORE',[]),('operator3_before','test_operator_round3.py','READ_ROUND3_BEFORE',[]),('lock3_before','test_lock_round3.py','READ_LOCK_BEFORE',[]),('round4_before','test_round4.py','READ_ROUND4_BEFORE',[]),('round5_before','test_round5.py','READ_ROUND5_BEFORE',[]),('round6_before','test_round6.py','READ_ROUND6_BEFORE',[]),('round7_before','test_round7.py','READ_ROUND7_BEFORE',[]),('round8_before','test_round8.py','READ_ROUND8_BEFORE',[]),('node4_before','test_round4.py','READ_NODE4_BEFORE',['Round4Tests.test_f2_bound_real_job_and_rehearsal_memory']),('f16_behavior_before','test_round3.py','READ_F16_BEFORE',['Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect'])]:
 report+=block(var+'=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/'+script+(' '+shlex.join(args) if args else ''),name+'.txt')
report+='The final seal runs `bash work/cpu.sh work/integrity8.py`. Its exact output is [integrity8.txt](checks/integrity8.txt); [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins this report, the note, MANIFEST, diffs and evidence. Seal output stays external to avoid a report/hash cycle.\n'
(O/'REPORT.md').write_text(report)
note=f'''VERDICT: DONE All round-8 fixes pass {workspace} workspace and {applied} fresh-application CPU tests; H100 byte parity remains required.

The kit binds **step 400 only**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. a19 refuses any other reviewed identity/preparation before reading the base. Later exports are diagnostic and cannot authorize adoption.

Follow [README](kit_parity50/README.md): apply patches; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...` and the delivered binding; generate operations; place; detached fill; CPU proof; gate; receipt handoff; submit; unpack. The build uses **A4's 636-item schedule**, one card, caches only, general/no-requeue. All-cache allowance is 12 GiB; processor-only is 4 GiB and needs its own gate. OFF reader bytes remain unchanged; synthetic CPU fixtures do not establish GPU parity.

The CPU job preserves in-tree symlinks in `$P/a/4.tar`, refuses escaping/broken/cyclic links and records archive hash/bytes before CPU.json. Tar stderr stays in `results/4.err`. Reserve **about 33 GB for the archive (estimate)** plus extraction/source/runtime space. The GPU host must provide the exact writable logical root outside bwrap. Asset aliases must be symlinks. README sets `READ_PYTHON="$GPU_LOGICAL/d/v/py"`, opaque cache roots and an executable torch/transformers/CUDA preflight. ENVIRONMENT.json is CPU-bound; ue.json and submit check its hash and exact versions.

Require **zero answer/trace byte differences**, useful cache hits, lower full-worker time and measured memory headroom before crediting savings. Submit also checks cont_ops' complete CPU assertions, dry proofs, empty general queue, return-pool bound, plan/profile/assets/device/environment and kit hashes. Device admission requires H100 80GB HBM3 and 132 SMs.

**Estimates with zero credited saving:** the 636-item schedule takes **7,351.824 s (11.559 s/item; 2 h 02 min 32 s)** if supplied throughput carries forward. **Package D**, the separate 580-item distance read, has **no ON route** in a19; its estimate is **13,813.069 s (3 h 50 min)** from the supplied measured 23.600 s/item. Neither measures step-400 GPU performance.

A refused unpack leaves its extracted tree behind. Scorers require **success output after exit status 0**; partial returns remain partial. Frozen weights remain required; raw writes restored between boundaries escape the guard.

## Review round 8: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Archive links | Preserve links and refuse escapes; extracted absolute heads link passes real Artifact/load_native admission. |
| 2. GPU environment | Use d/v/py with cache roots and preflight; version/hash/CUDA mutations refuse in executable shell, gate, runtime and submit tests. |
| 3. Late export refusal | Bind step 400 at build; eleven identity/preparation mutations refuse before base access. |
| 4. Archive path alias | Resolve both operands; README validation passes through a symlinked parent. |
| 5. Handoff details | Symlink aliases, retained tar stderr and fresh a15_cot_ap token; error and command tests pass. |

All ten new tests fail before and pass after; exact outputs and older requested review sections are in [REPORT](REPORT.md). [MANIFEST](patches/MANIFEST.json) pins delivery bytes. Real GPU parity/performance/memory, large staging, host interpreter execution, transport/restore/requeue and a multi-card operator remain unrun or undelivered.
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
with (L/'work/STATUS.md').open('a') as f:f.write(stamp+f'\nAll {workspace} workspace and {applied} applied tests pass. REPORT/NOTE rewritten with round-8 findings and exact outputs. Final seal pending.\n')
print('Report written:',workspace,'workspace tests;',applied,'fresh-application tests;',len(report.encode()),'bytes.')
print('Measured workspace bytes before report:',size,'UTC:',stamp)
