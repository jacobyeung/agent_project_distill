"""Write the current contract, deployment prerequisites and literal test evidence."""
from pathlib import Path
import json,re,shlex,subprocess

L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
m=json.loads((O/'patches/MANIFEST.json').read_text())
r=json.loads((C/'RESULTS.json').read_text())
runtime=json.loads((C/'RUNTIME_PREREQUISITES9.json').read_text())
cost=json.loads((C/'CACHE_COST3.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
stamp=subprocess.check_output(['date','-u'],text=True).strip()
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
review='''
| Finding | Fix | Regression |
|---|---|---|
| MEDIUM 1: the wrapper needs A4's namespace | The host helper authenticates the package and staging modules, executes A4's unchanged runtime-group/bwrap staging block, and extracts the CPU-bound archive to root/sj/<logical>/d. Preflight, parent and every worker use J.namespace(root), inputs['python'] and A4's -B -I convention. J.environment supplies HOME, TMPDIR and OPENBLAS_NUM_THREADS=1. | Four round-9 tests cover real namespace argv, actual parent launch, authenticated bootstrap/data extraction, the unchanged staging block and part hashes. The round-8 host-executable wrapper double is removed. |
| LOW 2: framework version gap | FRAMEWORK_EVIDENCE states CPU torch 2.11.0+cpu / transformers 5.12.1 versus production torch 2.13.0+cu130 / transformers 5.19.0. Before readers, the production interpreter must detect add_, copy_ and load_state_dict on fresh frozen scratch modules. ue.json records each result; submit requires all three. | Four tests exercise the actual guard, each injected miss, receipt refusal, actual main's failed receipt with zero worker launches, setup exceptions, and submit rejection. |
| LOW 3: idle H100 allocation and incomplete staging commands | The private configuration gate, seal, stage-kit and archive transfer precede salloc. README gives exact kit and original/patched source extraction commands. | The ordering regression also executes README's extraction block on small authenticated archives. Fresh application separately authenticates both complete 927-file roots. |
| INFO: token, environment, log labels and limits | A fresh opaque token determines the kit root; A4 owns HOME/TMPDIR/OPENBLAS. Eight carried applied logs live under checks/round7/. Frozen ownership and raw-write limits remain explicit. | Two regressions check fresh-token/version/guard documentation and all eight moved logs; namespace tests check the actual environment. |
'''
runtime_table='\n'.join('| '+str(v['group'])+' | `'+v['path']+'` | '+str(v['bytes'])+' | `'+v['sha256']+'` |' for v in runtime['rows'])
patch_table='\n'.join('| ['+n+'](patches/'+n+') | '+str(p['bytes'])+' | `'+p['sha256']+'` |' for n,p in m['patches'].items())
bench='\n'.join('| '+str(v['parameter_count'])+' | '+str(v['parameter_tensors'])+'/'+str(v['buffer_tensors'])+' | '+str(v['weight_and_buffer_bytes'])+' | '+f"{v['before_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_install_seconds']:.3f}"+' | '+f"{v['boundary']['median_seconds']:.3f}"+' |' for v in cost['cases'])
old=(L/'out_round9/REPORT.md').read_text()
profile=old[old.index('## Measured profile and forecast'):old.index('## Measured CPU guard overhead')]
report=f'''VERDICT: DONE The round-9 fixes pass CPU verification; deployment still requires the pinned runtime files and a passing step-400 H100 byte-parity gate.

| Quantity | Value | Evidence type |
|---|---:|---|
| Workspace tests | {workspace} passed | Measured; RESULTS.json and exact outputs below |
| Fresh-application tests | {applied} passed | Measured; MANIFEST applied_cpu_suites |
| Round-9 regressions | 11 fail before; 11 pass after | Measured; round9_before.txt and round9.txt |
| Retained fail-before controls | 13 rerun | Measured; exact outputs below |
| Original base | 927 files unchanged | Measured; full inventory/hash comparison |
| Additive reader files | 40 | Measured; patches 01–03 |
| Runtime archive parts | 13; 10,497,433,600 bytes | Read from A4's own receipt; bytes not supplied |
| bwrap | 72,160 bytes | Read from A4's own receipt; binary not supplied |
| Prepared asset archive | About 33 GB | Estimate from 32,606,120,583 declared expanded input bytes plus tar headers |
| Largest suite child RSS | {r['max_child_rss_bytes']:,} bytes | Measured CPU process resource counter |
| Guard benchmark peak RSS | {cost['max_rss_bytes']:,} bytes | Measured CPU process resource counter |
| Workspace at report generation | {size:,} unique-inode bytes | Measured; below 3,000,000,000 |

OFF reader source and output bytes remain unchanged. ON CPU fixtures preserve exact answers and traces. GPU equality, throughput and memory remain unmeasured. Zero answer/trace byte differences remain mandatory; aggregate score equality cannot authorize adoption.

Work started at **18:38:16 UTC on 2026-11-19**; the deadline is **19:38:16 UTC**. This report was generated at {stamp}. [out_round9](../out_round9/) preserves the reviewed delivery. All local computation used nice 10, hidden CUDA and at most eight torch/OMP/MKL/OpenBLAS threads. No Git, SSH, SCP, Slurm operation, GPU, paid API, input-tree edit or deletion command ran. Network reads were limited to library documentation.

## Review round 9: finding -> fix -> test
{review}

## Runtime prerequisites and exact pins

The following files must be reachable at their **exact Orchard paths** before the H100 gate can stage. None exists at its corresponding path in the supplied so_in mirror. This is a prerequisite, not a claim that the files are absent on Orchard: this task had no host access. No alternative source or substitute interpreter is assumed.

The authoritative receipt is A4/src/orchard_h10/vendor/ORCHARD_ASSETS.json, SHA256 `{runtime['source_sha256']}`, observed on **orchard-login-001**. [RUNTIME_PINS.json](kit_parity50/RUNTIME_PINS.json) copies its three groups and bwrap pin. [RUNTIME_PREREQUISITES9.json](checks/RUNTIME_PREREQUISITES9.json) records each exact supplied-mirror path checked. Group numbers retain the package's grouping; archive member lists were not supplied, so this report does not guess which part contains each library.

| Group | Exact Orchard source | Bytes, from receipt | SHA256, from receipt |
|---|---|---:|---|
{runtime_table}

The helper executes the runtime-group and bwrap block copied unchanged from `job.stage:110–117`; a regression compares that block with the real package source. Its S.copy_parts checks every part's bytes and SHA256 before S.unpack; S.room retains A4's 200 GiB free-space floor. Only the tiny fixture archives were staged here. The real runtime expansion and host disk usage are not measured.

The runtime binds supply `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e` and `/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu`, following `vendor/orchard_job.py:129–131`. The wrapper is inputs['python'], `/scratch/jjyeung/b01ec87a6f29b/d/v/py`, from the CPU-authenticated a/1.json. The wrapper and its site overlay remain intact. The host helper, not the wrapper, runs under `/usr/bin/python3`; the helper passes actual Python 3.6 syntax/import checks.

## Staging and adoption contract

Follow [README](kit_parity50/README.md): apply patches 01–03 to the pinned full A4 source and 04–05 to its operator; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; place, fill and obtain the CPU proof. Then run the private configuration gate, seal, stage-kit and archive transfer before salloc. The fresh token determines kit and source paths. Exact commands extract the public kit and both full source roots on the allocated host.

The H100 host uses a fresh job-private `/tmp/<token>` root. Its namespace maps root/sj to /scratch/jjyeung and binds the runtime roots; no bare-host /scratch path is needed. The helper authenticates the package payload and staging members, CPU proof and exact a/1.json, restores the pinned full payload at logical/p for the code paths authenticated by d/manifest.json, then verifies the prepared archive's bytes/hash and extracts it through bwrap into root/sj/<logical>/d. Absolute in-tree links retain their logical targets. The neutral binding/environment aliases are symlinks. Runtime/data staging must finish before the preflight or reader starts.

Preflight, parent and every worker run as `J.namespace(root) + [inputs['python'], '-B', '-I', ...]`. Every process uses J.environment(root), including HOME, TMPDIR and OPENBLAS_NUM_THREADS=1, with explicit XDG/HF/Triton caches under the opaque kit root. The parent and all workers authenticate environment, assets and kit bytes. The host helper is included in the package's kit hashes and checked at submit.

The gate binds **step 400 only**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. Other exports cannot authorize adoption. The candidate is A4's **636-item** schedule, one card, caches only, general/no-requeue. All-cache allowance is 12 GiB; processor-only is 4 GiB and requires its own matching gate. The gate requires exactly NVIDIA H100 80GB HBM3, 132 SMs, capability 9.0 and 79–86 billion bytes of memory.

The CPU proof preserves in-tree symlinks, rejects escaping/broken/cyclic links, records archive hash/bytes before CPU.json and retains tar stderr in results/4.err. Reserve about 33 GB for that archive **as an estimate**, plus data extraction and runtime space. Missing pins, failed staging, failed self-tests or byte differences stop the attempt; no automatic retry or substitute runtime is provided.

## Framework gap, equality and guard limits

CPU verification uses **torch {r['torch']} / transformers {r['transformers']}**. The production receipt requires **torch 2.13.0+cu130 / transformers 5.19.0**. [PRODUCTION_ENVIRONMENT9.json](checks/PRODUCTION_ENVIRONMENT9.json) is authenticated against the 359-byte a/1.json files.env pin; it was copied into this delivery, so no reference-workspace file is needed to run the kit. [FRAMEWORK_EVIDENCE](FRAMEWORK_EVIDENCE.md) distinguishes local source evidence from production requirements and cites installed source lines plus official documentation. Torch counter/loading behavior and transformers processor/model/kernel dispatch may differ across these versions.

The production interpreter runs the actual WeightGuard self-test before reader workers. Each fresh frozen scratch module undergoes one of add_, copy_ or load_state_dict, followed by check(); all three must raise ModelMutationError. A missed detection or setup error writes a failed ue.json and starts no workers. The receipt and submit checker require complete passing guard evidence. Local tests measured this on torch 2.11 only; no torch 2.13 outcome is claimed.

Models must remain frozen. Calls check identities, pointers, tensor versions, shapes/dtypes/devices and requires_grad; installation and type boundaries hash content. Persistent raw writes fail at a boundary. **Raw writes restored between boundaries remain undetected**; private tensor attributes and arbitrary non-tensor state also remain outside coverage. A hard kill can leave an unchecked journal requiring fresh output. The cache cap covers retained storage and transient copies, not model/caller memory.

The gate requires all 50 expected IDs, full production output schemas, useful hits for every enabled cache, unchanged ORIGINAL/OFF source hashes and zero semantic byte differences across the arms. Only clocks and explicit audit/cache/memo telemetry are excluded; audit violations fail. Sequential scene shards test equality, not parallel speed. Batching and numerical tolerances are not offered. A multi-card A4 operator is not delivered; the array prototype remains approved=false.

A refused unpack leaves its extracted tree behind. Scorers require **success output after exit status 0**, and complete=false remains partial. Submit retains cont_ops' complete CPU assertions, cache memory, dry proofs, queue/pool checks and matching plan/profile/assets/device/environment/kit/self-test evidence.

{profile}
## Measured CPU guard overhead

These rerun CPU stubs use bf16 2048×1024 parameter tensors and 1024-element buffers. Their forward returns a 32-element tensor without model-sized matrix work. Seven warm cache hits and three boundary hashes are timed per case. The numbers do not predict H100 speedup; raw samples are in [CACHE_COST3.json](checks/CACHE_COST3.json).

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Full hashing ms/call | Live guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
{bench}

## Patches and authentication

Base SHA256: `{m['base_pin']['sha256']}` across {m['base_pin']['files']} files. Reader patches add 40 files and change no original reader bytes. Operator changes remain behind read_extensions, default OFF. Five patches apply with zero fuzz to fresh copies; full original/patched base inventories and extension hashes pass. MANIFEST pins copied A4 members, payload, batch/bootstrap, operators, kit, operation files and export provenance.

| Patch | Bytes | SHA256 |
|---|---:|---|
{patch_table}

Eight carried round-7 applied logs were moved into **checks/round7/** without changing their bytes. Current applied logs are listed by MANIFEST. Identical completed fixture files share storage after byte-for-byte checks; paths and contents remain intact. [STORAGE9.json](checks/STORAGE9.json) records bounded local sharing passes.

## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Missing runtime part, bwrap, insufficient local space or failed extraction | Exact part hash/size checks, S.room and staging errors refuse before the preflight. Supply the named prerequisite; do not substitute an environment. |
| Namespace or wrapper cannot start on H100 | Preflight is wrapped in real J.namespace and uses the authenticated wrapper; failure stops the attempt. Actual bwrap execution is untested here. |
| Torch 2.13 changes guarded mutation behavior | In-gate self-test writes failed per-operation evidence and starts no readers; submit rejects it. |
| Different versions, export, source, operator or kit | CPU, gate, worker and submit pins refuse. |
| GPU kernels or eager SAM loading change bytes | Zero-difference acceptance refuses; score agreement is insufficient. |
| Cache overhead or caller/model memory dominates | Measure whole-worker time and host/GPU peaks before crediting savings. |
| Raw write restored between boundaries | Frozen ownership remains required; the guard cannot detect that sequence. |
| Partial or refused output reaches a scorer | Require successful unpack output and complete status. |

## Not done

The 13 runtime parts and bwrap were not fetched. No real H100 namespace, production wrapper/overlay, torch 2.13 self-test, GPU byte parity, throughput, memory peak, large archive, transfer, submit, return publication or persistent-storage requeue was run. The source/bootstrap/extraction tests use tiny files; namespace execution and missing-runtime I/O are explicit doubles. CPU checks need no local OS sockets. No runtime dependency on so_reads228 remains.

The requested review sections below are retained as test traceability. They state current contracts; the required round labels are the only historical framing retained under the no-archaeology writing rule.
'''
# Preserve requested prior-round traceability without superseded host/interpreter claims.
for round_number in range(8,0,-1):
    report+=f'\n## Review round {round_number}: finding -> fix -> test\n\n'
    summaries={
      8:'Symlink-preserving archive/real-loader admission, CPU-bound runtime versions, step-400-only build admission, resolved archive paths and retained tar diagnostics pass. The interpreter command is checked inside A4’s namespace. The preserved control reproduces 29 assertion failures.',
      7:'CPU-job asset staging, bounded fill waits, exact HBM3/132-SM admission, kit/input evidence and step-400 export binding pass. The preserved control reproduces ten assertion failures.',
      6:'Executable unpack, detached locked fill, complete cont_ops CPU assertions, copied-member pins and export/device admission pass. The preserved control reproduces 31 assertion failures.',
      5:'Batch wrapping, package/operator/extension authentication, executable operations, exact adoption profile, pool bound and unpack checks pass. The preserved control reproduces eleven assertion failures.',
      4:'The A4 builder retains export binding and compatible operation helpers. Preparation, rehearsal, bootstrap/action dispatch and return checks pass, including 636 stub reads. Both preserved controls reproduce their failures.',
      3:'Install/boundary hashing, fatal per-call identity/counter checks, processor-only mode, operator cache allowance/dispatch, base authentication, lock recovery and worker arguments pass. Preserved controls reproduce their failures.',
      2:'Entry isolation, path policy, bounded arrays, overlay pins, SAM capacity, deadline/lock/accounting and worker setup pass. The preserved control reproduces thirteen assertions and one expected CLI import error.',
      1:'Cache keys, strict parity schema/hits, unchanged OFF bytes, weight identity, writer-lock recovery, opacity and hard retained-memory accounting pass. The preserved control reproduces eight assertion failures.'}
    report+=summaries[round_number]+'\n'
report+='\n## Exact commands and outputs\n\nCommands run from the workspace use work/cpu.sh, which sets the required environment and execs nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B. Fixture commands additionally use work/run_fixture5.py to share immutable fixture bytes; this does not replace production logic. Before-control failures below are expected. Development failures remain in separately labelled logs.\n'

def transcript(command,name):
    global report
    report+='\nCommand: `'+command+'`\n\nOutput ([checks/'+name+'](checks/'+name+')):\n\n```text\n'+(C/name).read_text().rstrip()+'\n```\n'

for row in r['results']+m['applied_cpu_suites']:
    transcript(' '.join(shlex.quote(x) for x in row['command']),row['output'])
for name in ('round1_before','round2_before','round3_before','operator3_before','lock3_before','round4_before','node4_before','round5_before','round6_before','round7_before','round8_before','round9_before','f16_behavior_before'):
    transcript('bash work/cpu.sh work/run_checks.py  # '+name+' control, exact invocation in the runner',name+'.txt')
for script,name in (('run_checks.py','run_checks9.txt'),('build_patches.py','build_patches9.txt'),
                    ('gate_integration9.py','gate_integration9.txt'),('docs_check9.py','docs9.txt'),
                    ('verify_archive_command8.py','archive_command9.txt'),('profile.py','profile_rerun.txt'),
                    ('torch_versions3.py','torch_versions3.txt'),('benchmark_round3.py','cache_cost3.txt')):
    transcript('bash work/cpu.sh work/'+script,name)
(O/'REPORT.md').write_text(report)
short_review='''
| Finding | Fix and test |
|---|---|
| 1. Namespace | A4 staging, namespace and wrapper commands; authenticated extraction and all launch sites pass. |
| 2. Version gap | Production guard self-test and submit evidence; each injected miss fails closed with a recorded receipt. |
| 3. Idle allocation | Gate/seal/stage-kit/transfer precede salloc; exact extraction commands execute on fixtures. |
| 4. INFO | Fresh token, J.environment, labelled logs and explicit guard limits; all regressions pass. |
'''
note=f'''VERDICT: DONE Round-9 fixes pass {workspace} workspace and {applied} fresh-application CPU tests; production adoption still requires the pinned runtime and the H100 byte gate.

The kit binds **step 400 only**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. Follow [README](kit_parity50/README.md): apply patches; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; place, fill and obtain CPU proof; run the private gate, seal, stage-kit and transfer **before salloc**; stage the H100 namespace; run parity; return the receipt; submit and unpack.

**Prerequisite:** all 13 runtime parts and bwrap in [RUNTIME_PINS](kit_parity50/RUNTIME_PINS.json) must be reachable at their exact Orchard paths. Their bytes are absent from the supplied files. REPORT lists every path, byte count and hash. The helper reuses A4's runtime staging block and maps the archive into root/sj/<logical>/d. Preflight, parent and workers use `J.namespace(root) + [inputs['python'], '-B', '-I', ...]` and J.environment, including HOME/TMPDIR/OPENBLAS=1. Fresh opaque tokens isolate kit/source roots. Reserve **about 33 GB for the asset archive (estimate)** plus extraction/runtime space.

The CPU environment is torch 2.11.0+cpu / transformers 5.12.1; production is torch 2.13.0+cu130 / transformers 5.19.0. The production interpreter must detect add_, copy_ and load_state_dict mutations before reader work. A miss writes failed ue.json and starts no workers; submit requires all three checks. The real production self-test remains unrun.

Require **zero answer/trace byte differences**, useful hits, lower full-worker time and measured memory headroom before crediting savings. A4's **636-item** single-card cache-only route allows 12 GiB for all caches or 4 GiB for processor-only, each with a matching gate. OFF remains byte-identical. Models must remain frozen; raw writes restored between boundaries can escape detection.

**Estimates with zero credited saving:** A4's 636-item schedule takes **7,351.824 s (11.559 s/item; 2 h 02 min 32 s)** if supplied throughput carries forward. **Package D**, the separate 580-item distance read, has **no ON route** in a19; its estimate is **13,813.069 s (3 h 50 min)**. Neither measures step-400 performance. A refused unpack leaves its extracted tree behind; scorers require **success output after exit status 0**, and partial returns remain partial.

## Review round 9: finding -> fix -> test
{short_review}

All 11 round-9 tests fail before and pass after. Eight carried round-7 applied logs are labelled under checks/round7/. [REPORT](REPORT.md) contains exact outputs, all prior required review sections and the remaining production prerequisites. [MANIFEST](patches/MANIFEST.json) pins the delivery. GPU parity/performance/memory, real namespace/runtime execution, transfer/submit and persistent requeue remain unrun; no multi-card A4 operator is delivered.
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
print('Wrote REPORT and NOTE:',workspace,'workspace tests;',applied,'fresh-application tests; 11 round-9 fail-before/pass-after regressions; 14 exact runtime prerequisites.')
