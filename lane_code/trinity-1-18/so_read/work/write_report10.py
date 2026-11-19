"""Write the delivery contract and literal verification transcripts."""
from pathlib import Path
import json,re,shlex,subprocess

L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
m=json.loads((O/'patches/MANIFEST.json').read_text())
r=json.loads((C/'RESULTS.json').read_text())
runtime=json.loads((C/'RUNTIME_PREREQUISITES9.json').read_text())
wrapper=json.loads((C/'A4_WRAPPER_PINS10.json').read_text())
cost=json.loads((C/'CACHE_COST3.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
stamp=subprocess.check_output(['date','-u'],text=True).strip()
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
assert size<3_000_000_000,size
review='''
| Finding | Fix | Regression |
|---|---|---|
| MEDIUM 1: boot.py refuses -c | Ship `u0/u5.py`, pin it in MANIFEST/validate_kit and the built package's gate hashes, and invoke `[inputs['python'], '-B', '-I', kit+'/u0/u5.py', config]` inside A4's namespace. | The exact 443-byte boot rejects -c and runs the shipped preflight plus parent. Only the wrapper double changes its interpreter and physical boot pathname; boot.py stays byte-identical. CPU doubles supply version/CUDA imports. Public stage-kit preserves preflight bytes; mutation refuses. |
| MEDIUM 2: sealed paths have no aliases | One `host.ALIASES` table defines seven relative symlinks under logical/d. README generates PRIVATE_ALIASES from it, and host.stage creates them. The gate recursively checks every absolute sealed-settings path exists before the self-test. | A fixture executes authenticated host staging, seals settings, and resolves 12 absolute paths, including the ten prepared-settings paths and two gate receipt paths. Missing nested paths refuse before the self-test. |
| LOW 3: nested bwrap | When running under U0_ROOT, workers call the input wrapper directly, retaining J.environment. | Direct argv, HOME and OPENBLAS=1 assertions pass. Parent and preflight still enter J.namespace. |
| INFO: 4.tar read three times | Hash/count the one stream sent to tar; check its exit code and expected size/hash before aliases or successful staging records are published. README performs only metadata checks before extraction. | A 10,240-byte tar fixture is opened once and read once. A wrong hash refuses. README has no asset hash preread. |
'''
patch_table='\n'.join('| ['+n+'](patches/'+n+') | '+str(p['bytes'])+' | `'+p['sha256']+'` |' for n,p in m['patches'].items())
runtime_table='\n'.join('| '+str(v['group'])+' | `'+v['path']+'` | '+str(v['bytes'])+' | `'+v['sha256']+'` |' for v in runtime['rows'])
wrapper_table='\n'.join('| `'+n+'` | '+str(p['bytes'])+' | `'+p['sha256']+'` |' for n,p in wrapper['members'].items())
bench='\n'.join('| '+str(v['parameter_count'])+' | '+str(v['parameter_tensors'])+'/'+str(v['buffer_tensors'])+' | '+str(v['weight_and_buffer_bytes'])+' | '+f"{v['before_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_install_seconds']:.3f}"+' | '+f"{v['boundary']['median_seconds']:.3f}"+' |' for v in cost['cases'])
old=(L/'out_round10/REPORT.md').read_text()
profile=old[old.index('## Measured profile and forecast'):old.index('## Measured CPU guard overhead')]
report=f'''VERDICT: DONE The four round-10 fixes pass CPU verification; adoption still requires the pinned runtime and a zero-difference step-400 H100 gate.

| Quantity | Value | Evidence type |
|---|---:|---|
| Workspace tests | {workspace} passed | Measured; RESULTS.json and exact outputs below |
| Fresh-application tests | {applied} passed | Measured; MANIFEST applied_cpu_suites |
| Round-10 regressions | 7 fail before; 7 pass after | Measured; round10_before.txt and round10.txt |
| Retained fail-before controls | 14 rerun | Measured; transcripts below |
| Original A4 reader base | 927 files unchanged | Measured; full inventory/hash comparison |
| Additive reader files | 42 | Measured; patches 01–03 |
| Prepared-path aliases | 7 | Read from the shared host table |
| Fixture sealed paths | 12 resolved | Measured; ten prepared-settings paths plus two gate receipt paths |
| Extraction fixture | 10,240 bytes; one open, one full read | Measured; no production archive throughput claim |
| Runtime archive parts | 13; 10,497,433,600 bytes | Read from A4 receipt; bytes not supplied |
| bwrap | 72,160 bytes | Read from A4 receipt; binary not supplied |
| Prepared asset archive | About 33 GB | Estimate from declared expanded inputs and tar headers |
| Largest suite child RSS | Unavailable | Full-suite runner stopped at final size assertion before recording RSS |
| Largest fresh-application child RSS | {m['applied_max_child_rss_bytes']:,} bytes | Measured process resource counter |
| Guard benchmark peak RSS | {cost['max_rss_bytes']:,} bytes | Measured process resource counter |
| Workspace at report generation | {size:,} unique-inode bytes | Measured; below 3,000,000,000 |

OFF reader source and output bytes remain unchanged. ON CPU fixtures preserve exact answers and traces. H100 equality, throughput and memory remain unmeasured. Zero answer/trace byte differences remain mandatory; score equality cannot authorize adoption.

The task started at **19:47:20 UTC on 2026-11-19** and is due at **20:47:20 UTC**. This report was generated at {stamp}. [out_round10](../out_round10/) preserves the reviewed delivery. Computation used nice 10, hidden CUDA and at most eight torch/OMP/MKL/OpenBLAS threads. No Git, SSH, SCP, Slurm operation, GPU, paid API, input-tree edit or file-deletion command ran. Network reads were limited to official library documentation.

Storage limitation: one sample during verification measured **3,041,057,187 bytes**, above the requested 3 GB cap. Completed immutable fixture files were shared only after byte-for-byte comparison; no paths were removed. [STORAGE10_FIXTURES.json](checks/STORAGE10_FIXTURES.json) and [STORAGE10_EXTRA.json](checks/STORAGE10_EXTRA.json) record the bounded sharing passes. All tests passed before the runner failed its final size assertion; finish_checks10.py verifies their outputs and the restored storage cap. Aggregate RSS for that runner is unavailable; fresh-application RSS is recorded separately. The final size is reported above. The fixture harness also shares known archive members after their real writes close.

## Review round 10: finding -> fix -> test
{review}

## Wrapper bytes and pin comparison

| Supplied A4 member | Measured bytes | Measured SHA256 |
|---|---:|---|
{wrapper_table}

Both hashes match the coordinator's supplied prefixes, and both sizes match the A4 archive listing. The preserved MANIFEST's `a4_member_pins` covers six package/operator files; it contains no v/py or v/boot.py SHA256. Therefore an independent full-hash match against prior wrapper-member pins cannot be claimed. [A4_WRAPPER_PINS10.json](checks/A4_WRAPPER_PINS10.json) records that distinction, the exact supplied bytes' hashes and the pinned a4.tar receipt. The regenerated MANIFEST carries this evidence under `a4_wrapper_member_pins`; the regression's embedded exact bytes match both supplied files. The production archive itself was not fetched or rehashed here.

The wrapper double preserves the `-I -B` interpreter flags and all boot.py bytes. It replaces the production interpreter with the required CPU interpreter and maps the boot pathname into the local fixture. The real boot still calls site.addsitedir with its production path. No production site overlay is claimed to have run: tiny CPU modules supply the preflight's CUDA/version imports. The test proves the script-path calling convention and confirms -c refusal.

## Staging and adoption contract

Follow [README](kit_parity50/README.md): apply patches 01–03 to the pinned full A4 source and 04–05 to its operator; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; place, fill and obtain CPU proof. Run the private gate, seal, stage-kit and transfer before salloc. The host then stages runtime and data, runs the gate, and returns its receipt before submit/unpack.

The candidate binds **step 400 only**, read A/job **173060**, package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. It uses A4's 636-item schedule, one card, caches only, general/no-requeue. All-cache allowance is 12 GiB; processor-only is 4 GiB and needs its matching gate. The required device is exactly NVIDIA H100 80GB HBM3, 132 SMs, capability 9.0 and 79–86 billion bytes of memory.

`host.ALIASES` owns the names and targets. Under logical/d it creates `7.json -> binding.json`, `9.json -> ENVIRONMENT.json`, `a0 -> ../p/tree`, `a1.json -> p0/config.json`, `a2.pt -> k/sam3.pt`, `a3.json -> k/SAM3_RECEIPT.json`, and `a4 -> v/site`. README generates PRIVATE_ALIASES by importing that table. The a18/settings and pinned step-400 input audit found export, frames, selector-directory and SAM source-root paths already opaque at d/e, d/f, d/h and d/s. The decision input has no optional item-set path. Relative symlinks preserve resolved-path loader admission. Missing absolute sealed-settings paths fail before the guard self-test.

The host restores the authenticated package at logical/p and extracts 4.tar into root/sj/<logical>/d. It reads 4.tar once, hashing/counting the bounded stream sent to tar. A wrong hash, wrong byte count or tar failure prevents aliases and the successful staging record; the incomplete tree remains unusable. No wall-time or bandwidth saving was measured for the production archive.

The host starts the preflight and parent with `J.namespace(root) + [inputs['python'], '-B', '-I', script, config]`. The preflight is the pinned `u0/u5.py`. Workers under U0_ROOT invoke `[inputs['python'], '-B', '-I'] + args` directly. J.environment supplies HOME, TMPDIR and OPENBLAS=1; XDG/HF/Triton caches remain under the fresh opaque kit root. All workers authenticate assets, environment and kit bytes. Preflight hashes flow through stage-kit, package construction, gate validation, ue.json and submit admission.

## Runtime prerequisites and exact pins

All files below must be reachable at their exact Orchard paths. Their bytes are absent from the supplied mirror; this does not establish present-day Orchard reachability. [RUNTIME_PINS.json](kit_parity50/RUNTIME_PINS.json) copies A4's own runtime receipt. Its source SHA256 is `{runtime['source_sha256']}`. No alternate runtime is assumed.

| Group | Exact Orchard path | Bytes from receipt | SHA256 from receipt |
|---|---|---:|---|
{runtime_table}

The helper reuses the unchanged runtime-group/bwrap block from A4 job.stage. S.copy_parts verifies parts before unpacking; S.room retains the 200 GiB free-space floor. Runtime expansion, H100 namespace execution and host disk peaks are unmeasured. Reserve about 33 GB for 4.tar as an estimate, plus extraction/runtime/source space. Only tiny archive fixtures were extracted here.

## Framework evidence and guard limits

CPU tests use **torch 2.11.0+cpu / transformers 5.12.1**. The pinned production receipt specifies **torch 2.13.0+cu130 / transformers 5.19.0**. [FRAMEWORK_EVIDENCE](FRAMEWORK_EVIDENCE.md) gives installed file:line citations and official documentation links for every framework behavior used. CUDA availability, version counters and default load_state_dict copying were rechecked against installed source and the official 2.11 pages in this round. Torch 2.13 can differ in counters, loading, inference tensors, dispatch and CUDA kernels; transformers 5.19 can differ in processor/model dispatch and returned containers.

Before readers, the production interpreter must detect add_, copy_ and load_state_dict mutations with the actual WeightGuard. Any miss or setup failure records failed ue.json and starts no workers; submit requires all three passing checks. This behavior passes on local torch 2.11 only. No production torch 2.13 result is claimed.

Weights must remain frozen. Calls check identities, pointers, versions, shapes/dtypes/devices and requires_grad; installation and type boundaries hash content. Persistent raw writes fail at a boundary. **Raw writes restored between boundaries remain undetected**; private tensor attributes and arbitrary non-tensor state also remain outside coverage. A hard kill can leave an unchecked journal. Cache budgets cover retained storage and transient cache copies, not model/caller memory.

The 50-item gate requires complete output schemas, every expected ID, useful hits for each enabled cache, unchanged ORIGINAL/OFF source hashes and zero semantic byte differences. Only clocks and declared audit/cache/memo telemetry are excluded; audit violations fail. Sequential shards establish equality, not parallel speed. No batching tolerance or multi-card A4 operator is offered; the array prototype remains approved=false. Scorers require successful unpack output after exit status 0; partial returns remain partial.

{profile}

## Measured CPU guard overhead

These rerun CPU stubs contain bf16 2048×1024 parameters and 1024-element buffers. Their forward returns 32 elements without model-sized matrix work. Seven warm hits and three boundaries are timed per case. These measurements do not predict H100 speedup; [CACHE_COST3.json](checks/CACHE_COST3.json) holds raw samples.

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Full hash ms/call | Live guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
{bench}

## Patches and authentication

Base SHA256: `{m['base_pin']['sha256']}` across 927 files. Reader patches add 42 files without changing original reader bytes. Operator changes remain behind read_extensions, default OFF. All five patches apply with zero fuzz; base inventories and added hashes authenticate. MANIFEST pins payload, copied A4 files, bootstrap, operators, kit, operation files and wrapper evidence.

| Patch | Bytes | SHA256 |
|---|---:|---|
{patch_table}

## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Missing runtime, disk space, alias target or failed extraction | Part pins, space checks, tar status/stream hash and sealed-path existence checks refuse before reader work. |
| Actual H100 namespace/wrapper/overlay differs from the CPU fixture | Script preflight and environment pins refuse; only the real host gate establishes compatibility. |
| Torch 2.13 changes mutation behavior | Production self-test writes failed evidence and starts no readers. |
| Export, source, operator, preflight or environment differs | CPU, gate, worker and submit authentication refuses. |
| CUDA kernels or eager SAM loading change outputs | The zero-byte-difference gate refuses; matching aggregate scores do not suffice. |
| A worker fails before a final receipt | Nonzero exit stops the run; no ue.json means no return archive and submit cannot pass. The worker log remains only until allocation cleanup. |
| Hash mismatch during extraction | No successful stage record is published; extracted bytes remain untrusted and must not be executed. |
| Cache overhead dominates | Measure full-worker elapsed time and memory before crediting any speedup. |
| A raw write is restored between boundaries | Frozen ownership is required; the guard cannot detect that sequence. |

## Not done

No real H100 bwrap namespace, production interpreter/site overlay, torch 2.13 guard, GPU byte parity, throughput, GPU memory, large 4.tar extraction, transfer, submit or persistent requeue ran. Runtime files remain exact-path prerequisites. Tests use explicit namespace/runtime doubles and tiny assets. The boot bytes themselves did execute. Independent prior wrapper-member SHA256 pins were unavailable. CPU checks require no local OS sockets. Host argv screening and a receipt for arbitrary worker failure remain outside this fix set; current failures refuse adoption.

The review labels below remain because the dispatch explicitly requires finding/fix/test traceability. Other documentation states the current behavior.
'''
# Keep required earlier finding mappings; the new namespace details above govern.
prior=old[old.index('## Review round 8: finding -> fix -> test'):old.index('## Exact commands and outputs')]
report+='\n## Review round 9: finding -> fix -> test\n\nAuthenticated A4 runtime staging, production guard self-tests, pre-allocation kit preparation, fresh tokens, J.environment and labelled logs pass. Preflight and parent enter the namespace; workers call its wrapper directly. All eleven preserved controls fail before and pass after.\n\n'+prior
report+='\n## Exact commands and outputs\n\nAll commands run from this workspace through `bash work/cpu.sh`, which exports hidden CUDA, thread/cache limits and PYTHONDONTWRITEBYTECODE, then execs `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Fixture commands use work/run_fixture5.py to share identical local bytes after real writes. No production logic is replaced by that storage harness. Expected before-control failures are labelled; the development-only README assertion failure is retained in run_checks10_development.txt.\n'

def transcript(command,name):
    global report
    report+='\nCommand: `'+command+'`\n\nExact output ([checks/'+name+'](checks/'+name+')):\n\n```text\n'+(C/name).read_text().rstrip()+'\n```\n'

for row in r['results']+m['applied_cpu_suites']:
    transcript(' '.join(shlex.quote(x) for x in row['command']),row['output'])
controls=('round1_before','round2_before','round3_before','operator3_before','lock3_before','round4_before','node4_before','round5_before','round6_before','round7_before','round8_before','round9_before','round10_before','f16_behavior_before')
for name in controls:transcript('bash work/cpu.sh work/run_checks.py  # '+name+'; exact environment/argv in runner',name+'.txt')
for script,name in (('run_checks.py','run_checks10.txt'),('run_fixture5.py work/build_patches.py','build_patches10.txt'),('finish_checks10.py','finish_checks10.txt'),('gate_integration10.py','gate_integration10.txt'),('docs_check10.py','docs10.txt'),('verify_archive_command8.py','archive_command10.txt'),('profile.py','profile_rerun.txt'),('torch_versions3.py','torch_versions3.txt'),('benchmark_round3.py','cache_cost3.txt')):
    transcript('bash work/cpu.sh work/'+script,name)
(O/'REPORT.md').write_text(report)
note=f'''VERDICT: DONE Round-10 fixes pass {workspace} workspace and {applied} fresh-application CPU tests; H100 byte parity remains required.

The kit binds **step 400 only**, read A/job **173060**, artifact **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. Follow [README](kit_parity50/README.md): apply patches; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; obtain CPU proof; gate, seal, stage-kit and transfer before salloc; stage the host, run parity, return the receipt, then submit/unpack.

All **13 runtime parts plus bwrap** in [RUNTIME_PINS](kit_parity50/RUNTIME_PINS.json) remain exact-path Orchard prerequisites; their bytes are not supplied. Reserve **about 33 GB for 4.tar (estimate)** plus extraction/runtime space. The host hashes 4.tar once while extracting it. It enters A4's namespace for script preflight and parent; workers call the wrapper directly with J.environment, including HOME/TMPDIR/OPENBLAS=1.

Require **zero answer/trace byte differences**, useful hits, lower full-worker time and measured memory headroom before crediting savings. OFF bytes remain unchanged. A4's 636-item, single-card cache-only route allows 12 GiB for all caches or 4 GiB for processor-only with its own matching gate. No multi-card A4 operator is delivered.

CPU checks use torch 2.11.0+cpu / transformers 5.12.1; production requires torch 2.13.0+cu130 / transformers 5.19.0. The production guard must detect add_, copy_ and load_state_dict before readers. A miss fails ue.json and submit. Models must remain frozen; raw writes restored between boundaries can escape detection.

**Estimates with zero credited cache saving:** A4's 636-item schedule takes **7,351.824 s (11.559 s/item; 2 h 02 min 32 s)** if supplied throughput carries forward. The separate 580-item distance Package D has no ON route in a19; its estimate is **13,813.069 s (3 h 50 min)**. Neither measures step-400 performance. Scorers require successful unpack output after exit status 0; partial returns remain partial.

## Review round 10: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Wrapper rejects -c | Pinned u0/u5.py script; exact boot bytes reject -c and execute preflight through the wrapper double; tampering refuses. |
| 2. Missing aliases | One table generates PRIVATE_ALIASES and seven host symlinks; staged fixture resolves all 12 paths; missing nested settings path refuses before self-test. |
| 3. Nested bwrap | Direct wrapper argv inside U0_ROOT; J.environment assertions pass. |
| 4. Repeated reads | One extraction/hash stream; measured one open/read and wrong-hash refusal. |

All seven new regressions fail before and pass after. Both supplied wrapper hashes match the coordinator prefixes and listed sizes; prior MANIFEST had no independent full wrapper-member hashes. [REPORT](REPORT.md) records exact hashes, outputs and that limitation. [MANIFEST](patches/MANIFEST.json) pins the delivery. Real H100 namespace/runtime execution, GPU parity/performance/memory, transfer and submit remain unrun.
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
print('Wrote REPORT and NOTE:',workspace,'workspace tests;',applied,'fresh-application tests; 7 round-10 fail-before/pass-after tests; 14 baseline controls.')
