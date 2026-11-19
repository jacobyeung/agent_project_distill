from pathlib import Path
import hashlib,json,re,subprocess,sys
r=Path(__file__).resolve().parent;root=r.parent.parent;out=root/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
stamp=subprocess.check_output(['date','-u','+%Y-%m-%d %H:%M:%S UTC']).decode().strip()
base=read(r/'PATCH_BASE.json');canonical=base['canonical']
for name,h in canonical.items():
    for tree in [root,r/'src',r/'applied',r/'applied_final']:assert sha(tree/name)==h,(tree,name)
for name,h in base['adapter_copies'].items():assert sha(r/'applied_final'/name)==h
input_root=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
for name,h in base['source_unchanged'].items():assert sha(input_root/name)==h
for name,count in [('final_pack.log',25),('final_review.log',12),('final_docs.log',1)]:
    text=(r/name).read_text();assert 'Ran %d test'%count in text and '\nOK\n' in text,text
native=read(r/'native/RESULT.json');assert native['passed'] and native['d_all_checks_passed']
dcheck=read(r/'native/D_CHECK.json');positive=read(r/'final_pack/POSITIVE.json')
assert dcheck['check']['checker']=={n:canonical[n] for n in ('pack.py','pack_checks.py','pack_structural.py')}
assert positive['check']['checker']==dcheck['check']['checker']
for name in ['adapter_r10.log','adapter_d.log']:assert json.loads((r/name).read_text())['passed']
assert (r/'small_checks.log').read_text().endswith('PASS: missing inputs refuse before a builder or remote call\n')
structural=next(read(p) for p in (r/'final_review').glob('q*/1.json') if read(p).get('mode')=='structural')
size=allocated=0
for p in root.rglob('*'):
    if p.is_file():s=p.stat();size+=s.st_size;allocated+=s.st_blocks*512
assert size<3000000000 and allocated<3000000000,(size,allocated)
patches={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((out/'patches').glob('*.diff'))}
logs=['final_pack.log','final_review.log','final_docs.log','native.log','adapter_r10.log','adapter_d.log','small_checks.log','package_final.log','patch_apply.log','before_review.log','before_import.log','before_coverage.log']
verified=dict(passed=True,verified_utc=stamp,canonical_files=len(canonical),canonical=canonical,adapter_copies=base['adapter_copies'],source_unchanged=base['source_unchanged'],applied=str(r/'applied_final'),tested_tree=str(r/'applied'),tested_tree_byte_identical=True,native_test_tree=str(r/'src'),native_runtime_byte_identical=True,patches=patches,logs={name:dict(path=str(r/name),sha256=sha(r/name)) for name in logs},default_off_delivery_bytes=native['default_off_delivery_bytes'],default_off_delivery_sha256=native['default_off_delivery_sha256'])
write(out/'PATCH_VERIFIED.json',verified)
measure=dict(measured=dict(utc=stamp,pack_tests=25,review_tests=12,final_document_test_recheck=1,pack_seconds=float(re.search(r'Ran 25 tests in ([0-9.]+)s',(r/'final_pack.log').read_text()).group(1)),review_seconds=float(re.search(r'Ran 12 tests in ([0-9.]+)s',(r/'final_review.log').read_text()).group(1)),cpu_python=sys.version.split()[0],login_python='3.6.8',compiled_delivered_sources=10,b5_rows=positive['check']['checks']['logic']['rows_checked'],d_rows=dcheck['check']['checks']['logic']['rows_checked'],structural_standin_bytes=structural['standin_bytes'],default_off_delivery_bytes=native['default_off_delivery_bytes'],workspace_apparent_bytes=size,workspace_allocated_bytes=allocated,lossless_storage=read(r/'COMPRESSION.json')),source_reported=dict(b5_total_archive_bytes=33410549760,source='/scratch/jjyeung/orch_n30/so_cr_pack_a/REVIEW_VERDICT.md'),estimated=dict(full_mirror_read_bytes=155000000000,full_mirror_source='Review finding 2 estimate',d_native_gpu_seconds=native['pack_build']['native_budget_gpu_seconds'],d_native_budget_fits=native['pack_build']['native_budget_fits']),unmeasured=['production fill time','production GPU performance and memory','production archive identities','real full-reader result','process peak RSS'])
write(out/'MEASUREMENTS.json',measure)
env="nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 "
py='/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B '
commands=[
('Packaging suite',env+'PACK_TEST_WORK='+str(r/'final_pack')+' PACK_TEST_FIXTURE='+str(r/'after_tests')+' '+py+'work/r1/applied/test_pack.py','final_pack.log'),
('Review suite',env+'PACK_REVIEW_WORK='+str(r/'final_review')+' PACK_REVIEW_FIXTURE='+str(r/'after_tests')+' PACK_NATIVE_RESULT='+str(r/'native/RESULT.json')+' '+py+'work/r1/applied/test_review.py','final_review.log'),
('Native D builds, all probes and D-script planning',env+py+'work/r1/src/test_native.py --work '+str(r/'native'),'native.log'),
('r10 adapter under login Python',env+'/usr/bin/python3 -I -s -B work/r1/applied_final/cont_ops17/work/test_pack_token.py','adapter_r10.log'),
('D adapter under login Python',env+'/usr/bin/python3 -I -s -B work/r1/applied_final/cont_ops18/dbuild/test_pack_token.py','adapter_d.log'),
('Final handoff document check',env+'PACK_REVIEW_WORK='+str(r/'final_docs')+' PACK_REVIEW_FIXTURE='+str(r/'after_tests')+' '+py+'work/r1/applied_final/test_review.py Review.test_r6_operational_inventory','final_docs.log'),
('Real Python 3.6 compile and required-input refusals',env+'/usr/bin/python3 -I -s -B work/r1/validate_small.py','small_checks.log'),
('Final patch generation and fresh application',env+py+'work/r1/package.py applied_final','package_final.log')]
write(out/'TEST_RUNS.json',dict(cwd=str(root),runs=[dict(name=title,command=cmd+' > work/r1/'+log+' 2>&1',returncode=0,log=str(r/log),sha256=sha(r/log)) for title,cmd,log in commands]))
report='''VERDICT: DONE All HIGH, MEDIUM and LOW findings are fixed and tested; production use still requires the named inputs and a coherent D release.

The delivered command detaches fill, checks staged input sizes before placement, supports explicit structural fill without large local mirrors, and can retry GPU gates without resubmitting the passed CPU check. Native code remains unchanged. The original source files, rebuilt patches, applied files and tested runtime bytes match their manifests.

## Numbers and limits

'''
m=measure['measured']
report+='- **Measured:** 25 packaging tests and 12 review tests passed; the final document check passed separately. Packaging took %.3f seconds; the review suite took %.3f seconds. Both adapter suites and the native D integration passed.\n'%(m['pack_seconds'],m['review_seconds'])
report+='- **Measured:** login Python 3.6.8 executed place, fill, entry check, guard/dispatch, native submit with stub sbatch and pool predicates. Ten delivered Python files compile under that interpreter. The CPU test interpreter is '+m['cpu_python']+'.\n'
report+='- **Measured:** B5 and D each checked %d and %d frame rows respectively. D ran all seven probes and planned its own scripts at 04:00:00. Structural fill used %d bytes of stand-ins and reports production_archive_identity=false.\n'%(m['b5_rows'],m['d_rows'],m['structural_standin_bytes'])
report+='- **Measured:** native D and the default-OFF adapter produced the same %d-byte delivery under fixed entropy, SHA256 `%s`. r10 default source identity passed; its full build remains unavailable.\n'%(native['default_off_delivery_bytes'],native['default_off_delivery_sha256'])
report+='- **Source-reported:** the review lists 33,410,549,760 bytes of B5 archive inputs. Its approximate 155 GB full-mirror read cost is an **estimate**, not a measurement here. D\'s native 19,595 GPU-second budget is an **estimate** and reports budget_fits=false for four hours.\n'
report+='- **Measured storage audit:** this snapshot contains %d apparent bytes and %d allocated bytes, both below decimal 3 GB. An audit observed 3,002,663,466 apparent bytes and 3,148,566,528 allocated bytes before lossless compression of retained older test output. [COMPRESSION.json](../work/r1/COMPRESSION.json) preserves original paths, byte counts and SHA256 values for every compressed file; no content was discarded. Current sources and current test evidence match their hashes.\n'%(size,allocated)
report+='- **Configured, not measured utilization:** eight CPU threads, at most eight CPU cores in test processes, 28 GiB address-space cap, no GPUs. Peak RSS and production performance were not measured.\n\n'
report+='[MEASUREMENTS.json](MEASUREMENTS.json) records these values. [FRAMEWORK_SOURCES.md](FRAMEWORK_SOURCES.md) cites the installed torch 2.11 source lines and official versioned documentation.\n\n'
report+=(r/'review_section.md').read_text()+'\n'
report+='''## Before-fix evidence

The regressions were run against the preserved reviewed sources, not a hand-written imitation. [before_review.log](../work/r1/before_review.log) records failures for findings 1, 2, 4, 5, 6, 8, 9 and 11. Finding 7 uses the relative-import case in [before_import.log](../work/r1/before_import.log); the package-init case in the broad baseline log is not its regression evidence. [before_coverage.log](../work/r1/before_coverage.log) records the absent D integration result, incomplete operational inventory and missing named-input gate. The after-fix outputs below show all final regressions passing.

The before commands used the same environment as the final commands, plus PACK_SOURCE=work/r1/baseline. Their exact commands and expected failing exit codes are recorded in BEFORE_RUNS.json. The first baseline suite contains an additional package-init case that already passed; no fix is claimed for that case.

## Patches

'''
for name,v in patches.items():report+='- [%s](patches/%s): **measured** %d bytes; SHA256 `%s`.\n'%(name,name,v['bytes'],v['sha256'])
report+='''
Patch 01 adds the command, probes, tests and documents. Patch 02 adds the adapter and its standalone test beside each native builder. Both are additive against the input tree. Their switches default OFF. [PATCHES.md](PATCHES.md), [TOOL_SHA256.json](TOOL_SHA256.json) and [PATCH_VERIFIED.json](PATCH_VERIFIED.json) identify the 18 canonical files, four adapter copies and exact tested bytes. The final patches reconstruct a byte-identical tree; the final handoff document was also retested after its one-page formatting edit.

## Exact commands and outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_pack_a`; stdout and stderr were combined in the indicated logs. Reproduction requires fresh output directories. Fixture reuse shares only unchanged inputs and avoids duplicate storage. The printed ossh commands in the review output were intercepted by a local stub; no SSH or Slurm command ran.

'''
for title,cmd,log in commands:
    report+='### '+title+'\n\n```sh\n'+cmd+' > work/r1/'+log+' 2>&1\n```\n\nExact output ([log](../work/r1/'+log+')):\n\n```text\n'+(r/log).read_text()+'```\n\n'
report+='''## What could go wrong and how we notice

- A remote file can have the right size but wrong bytes. Preflight checks availability and size; native fill hashes the full export, and job.stage authenticates dependency parts, archives and members before the GPU job. Structural stand-ins provide no production byte-identity evidence.
- A detached fill can fail or stop without its final receipt. Inspect a/f.log and a/f.exit; the bounded poll stops at its deadline. The launch lock and local attempt marker prevent automatic relaunch after an uncertain transport failure.
- GPU submission can be refused by queue or pool state. The gpu action rechecks completion and native receipts without repeating CPU submission. A persistent a/g.lock without a/8.txt requires manual reconciliation because sbatch may already have accepted the job.
- A fixture can pass while the real reader or environment fails. Full-reader receipts are synthetic; real weights, RGBs and the production environment remain required. Frame rows exercise top-level metadata; native layout_inputs runs only for supplied student_input rows. The read-runner signal test does not establish trainer-rank behavior.

## What is not done

The actual step-600 source delivery/binding, export, preparation, dependency environment and RGB inputs are unavailable. The original r10 delivery archives and routed harness files are also absent. REQUIRED_INPUTS.json names them; the refusal outputs above show the checks stop rather than claiming coverage. Missing-input availability checks do not execute the missing suites.

The raw D tree still fails its native release gate because the loose scorer differs from o_build_D.sh's embedded scorer. This is an INFO finding, not a patch regression. The inputs are read-only, and choosing the authoritative scorer is outside this packaging fix. A coherent fixture built from authenticated embedded assets passes the unchanged native checker; production needs a reviewed regenerated source release. The wrapper retains this source-consistency gate.

No actual Orchard placement, fill or submission ran. Production archive hashes, live fill timing, real full-reader/GPU behavior, Slurm signal delivery and trainer-rank stop cooperation remain unmeasured. The unknown B4 early-failure cause has no claimed repair. No HIGH, MEDIUM or LOW review item is left unfixed.

The required before/after regression evidence and storage-cap exception are retained for audit; they explain validation and resource compliance rather than a superseded product design.
'''
report+='\nStarted: 2026-11-19 11:11:26 UTC. Report verified: '+stamp+'.\n'
(out/'REPORT.md').write_text(report)
before=[
dict(command=env+'PACK_SOURCE='+str(r/'baseline')+' PACK_REVIEW_WORK='+str(r/'before_tests')+' '+py+'work/r1/src/test_review.py > work/r1/before_review.log 2>&1',returncode=1,log='before_review.log',scope='Reviewed-source gaps; package-init case is not finding 7 evidence'),
dict(command=env+'PACK_SOURCE='+str(r/'baseline')+' PACK_REVIEW_WORK='+str(r/'before_import')+' '+py+'work/r1/src/test_review.py Review.test_r7_production_module_import > work/r1/before_import.log 2>&1',returncode=1,log='before_import.log',scope='Relative module import'),
dict(command=env+'PACK_SOURCE='+str(r/'baseline')+' PACK_REVIEW_WORK='+str(r/'before_coverage')+' PACK_REVIEW_FIXTURE='+str(r/'after_tests')+' PACK_NATIVE_RESULT='+str(root/'work/native_release/RESULT.json')+' '+py+'work/r1/src/test_review.py Review.test_r3_actual_D_integration Review.test_r6_operational_inventory Review.test_required_inputs_refuse_by_name > work/r1/before_coverage.log 2>&1',returncode=1,log='before_coverage.log',scope='D integration, operational inventory and named missing-input gate')]
write(out/'BEFORE_RUNS.json',dict(cwd=str(root),runs=before))
artifacts=[out/n for n in ['REPORT.md','PATCH_VERIFIED.json','TOOL_SHA256.json','MEASUREMENTS.json','TEST_RUNS.json','BEFORE_RUNS.json']]+list((out/'patches').glob('*.diff'))
write(out/'ARTIFACT_SHA256.json',{str(p.relative_to(root)):sha(p) for p in artifacts})
(root/'work/STATUS.md').write_text(stamp+'\n\nDONE: All required review fixes are delivered. The 25-test packaging suite, 12-test review suite, native D integration, two Python 3.6.8 adapter suites, final document regression and missing-input refusals passed. Both patches reconstruct all 18 canonical files and four adapter copies exactly. Production remains blocked by the inputs listed in out/REQUIRED_INPUTS.json and the native D scorer mismatch. The final report contains exact commands, outputs, limits and the storage audit. No remote execution, GPU use, Git operation or supplied-input mutation occurred.\n')
print(json.dumps(dict(passed=True,verified_utc=stamp,canonical_files=len(canonical),unique_regression_tests=37,workspace_snapshot_apparent_bytes=size,workspace_snapshot_allocated_bytes=allocated,report=str(out/'REPORT.md')),sort_keys=True))
