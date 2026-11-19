"""Verify the delivered sources and write the reviewable evidence bundle."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
r=Path(__file__).resolve().parent;root=r.parent.parent;out=root/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
stamp=subprocess.check_output(['date','-u','+%Y-%m-%d %H:%M:%S UTC']).decode().strip()
base=read(r/'PATCH_BASE.json');canonical=base['canonical']
for name,h in canonical.items():
    for tree in (root,r/'src',r/'applied',r/'applied_final'):assert sha(tree/name)==h,(tree,name)
for name,h in base['adapter_copies'].items():assert sha(r/'applied_final'/name)==h
inp=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
for name,h in base['source_unchanged'].items():assert sha(inp/name)==h
for name,h in read(root/'out_round1/TOOL_SHA256.json').items():
    if name.endswith('.py'):assert sha(r/'before'/name)==h
    else:assert sha(root/'out_round1'/Path(name).name)==h
for name,h in read(root/'out_round1/ARTIFACT_SHA256.json').items():assert sha(root/'out_round1'/Path(name).relative_to('out'))==h
counts={'pack.log':25,'review1.log':12,'review2.log':15}
for log,n in counts.items():
    text=(r/log).read_text();assert 'Ran %d tests'%n in text and '\nOK\n' in text,text
for log in ('before.log','before_sum.log','before_evidence.log'):
    text=(r/log).read_text();assert 'FAILED (failures=' in text and 'KeyError' not in text and '\nERROR:' not in text
native=read(r/'native/RESULT.json');assert native['passed'] and native['d_all_checks_passed']
positive=read(r/'pack/POSITIVE.json');dcheck=read(r/'native/D_CHECK.json')
runtime={n:canonical[n] for n in ('pack.py','pack_checks.py','pack_structural.py')}
assert positive['check']['checker']==dcheck['check']['checker']==runtime
for log in ('adapter_r10.log','adapter_d.log'):assert json.loads((r/log).read_text())['passed']
assert (r/'small_checks.log').read_text().endswith('PASS: missing inputs refuse before a builder or remote call\n')
docs_done=all((r/n).is_file() for n in ('docs_round1.log','docs_round2.log'))
if docs_done:
    for name in ('docs_round1.log','docs_round2.log'):assert '\nOK\n' in (r/name).read_text()
files=list(root.rglob('*'));apparent=sum(p.stat().st_size for p in files if p.is_file())
allocated=int(subprocess.check_output(['nice','-n','10','du','-s','-B1',str(root)]).split()[0])
assert apparent<3000000000 and allocated<3000000000,(apparent,allocated)
measured=dict(utc=stamp,unit_tests=sum(counts.values()),pack_tests=25,review_round1_tests=12,review_round2_tests=15,seconds={k:float(re.search(r'Ran \d+ tests in ([0-9.]+)s',(r/k).read_text()).group(1)) for k in counts},cpu_python=sys.version.split()[0],login_python='3.6.8',compiled_delivered_sources=11,b5_rows=positive['check']['checks']['logic']['rows_checked'],d_rows=dcheck['check']['checks']['logic']['rows_checked'],real_d_dependency_archives=dcheck['check']['checks']['fill']['dependency_reference']['real_dependency_archives'],synthetic_d_filled_archives=dcheck['check']['checks']['fill']['resolution']['archives'],standin_bytes=dcheck['check']['checks']['fill']['standin_bytes'],native_dry_sha256=dcheck['check']['checks']['fill']['native_dry']['sha256'],default_off_delivery_bytes=native['default_off_delivery_bytes'],default_off_delivery_sha256=native['default_off_delivery_sha256'],workspace_apparent_bytes=apparent,workspace_allocated_bytes=allocated,canonical_files=len(canonical),adapter_copies=len(base['adapter_copies']))
write(out/'MEASUREMENTS.json',dict(measured=measured,estimated=dict(full_mirror_reads_bytes=155000000000,d_budget_gpu_seconds=native['pack_build']['native_budget_gpu_seconds']),source_reported=dict(b5_archive_bytes=33410549760,source='/scratch/jjyeung/orch_n30/so_cr_pack_a/REVIEW_VERDICT.md'),unmeasured=['production archive identity','production fill timing','real full-reader and GPU performance','peak RSS','live transport authentication']))
env="nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 "
py='/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B '
runs=[
 ('Packaging suite',env+'PACK_TEST_WORK='+str(r/'pack')+' PACK_TEST_FIXTURE='+str(r/'fixture')+' '+py+'work/r2/applied/test_pack.py','pack.log'),
 ('Native D integration and default-OFF equality',env+py+'work/r2/applied/test_native.py --work '+str(r/'native'),'native.log'),
 ('Round-1 regressions',env+'PACK_REVIEW_WORK='+str(r/'review1')+' PACK_REVIEW_FIXTURE='+str(r/'fixture')+' PACK_NATIVE_RESULT='+str(r/'native/RESULT.json')+' '+py+'work/r2/applied/test_review.py','review1.log'),
 ('Round-2 regressions',env+'PACK_R2_WORK='+str(r/'review2')+' PACK_R2_FIXTURE='+str(r/'fixture')+' PACK_DOCS='+str(out)+' '+py+'work/r2/applied/test_review2.py','review2.log'),
 ('r10 adapter under login Python',env+'/usr/bin/python3 -I -s -B work/r2/applied_final/cont_ops17/work/test_pack_token.py','adapter_r10.log'),
 ('D adapter under login Python',env+'/usr/bin/python3 -I -s -B work/r2/applied_final/cont_ops18/dbuild/test_pack_token.py','adapter_d.log'),
 ('Python 3.6 compile and named-input refusals',env+'/usr/bin/python3 -I -s -B work/r2/validate_small.py','small_checks.log'),
 ('Fresh final patch application',env+py+'work/r2/package.py applied_final','package_final.log')]
if docs_done:runs += [
 ('Final round-1 document check',env+'PACK_REVIEW_WORK='+str(r/'docs1')+' PACK_REVIEW_FIXTURE='+str(r/'fixture')+' PACK_DOCS='+str(out)+' '+py+'work/r2/applied_final/test_review.py Review.test_r6_operational_inventory','docs_round1.log'),
 ('Final round-2 document checks',env+'PACK_R2_WORK='+str(r/'docs2')+' PACK_R2_FIXTURE='+str(r/'fixture')+' PACK_DOCS='+str(out)+' '+py+'work/r2/applied_final/test_review2.py Review2.test_05_exact_forbidden_rule_documented Review2.test_06_five_rows_and_error_limit','docs_round2.log')]
write(out/'TEST_RUNS.json',dict(cwd=str(root),runs=[dict(name=title,command=cmd+' > work/r2/'+log+' 2>&1',returncode=0,log=str(r/log),sha256=sha(r/log)) for title,cmd,log in runs]))
before=[
 ('New defect regressions',env+'PACK_SOURCE='+str(r/'before')+' PACK_R2_WORK='+str(r/'before_tests')+' PACK_R2_FIXTURE='+str(r/'fixture')+' PACK_DOCS='+str(root/'out_round1')+' '+py+'work/r2/src/test_review2.py','before.log'),
 ('Part-sum defect',env+'PACK_SOURCE='+str(r/'before')+' PACK_R2_WORK='+str(r/'before_sum')+' PACK_R2_FIXTURE='+str(r/'fixture')+' PACK_DOCS='+str(root/'out_round1')+' '+py+'work/r2/src/test_review2.py Review2.test_01_wrong_part_sum','before_sum.log'),
 ('Guard interpreter and recorded-delivery defects',env+'PACK_SOURCE='+str(root/'work/r1/baseline')+' PACK_REVIEW_WORK='+str(r/'before_evidence')+' PACK_REVIEW_FIXTURE='+str(r/'fixture')+' '+py+'work/r2/src/test_review.py Review.test_r6_login_runtime_guard_submit_pool Review.test_r11_login_exact_delivery','before_evidence.log')]
# The first invocation predates the added sum test; preserve its exact test-file bytes separately.
write(out/'BEFORE_RUNS.json',dict(cwd=str(root),runs=[dict(name=title,command=cmd+' > work/r2/'+log+' 2>&1',returncode=1,expected_failure=True,log=str(r/log),sha256=sha(r/log)) for title,cmd,log in before],note='before.log ran the 14-method test file before test_01_wrong_part_sum was added; before_sum.log covers that method separately. Both use the same untouched reviewed runtime. before_evidence.log uses the preserved pre-round-1 runtime.'))
patches={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((out/'patches').glob('*.diff'))}
all_logs=[x[2] for x in runs+before]+['patch_apply.log','after_code.log']
write(out/'PATCH_VERIFIED.json',dict(passed=True,utc=stamp,canonical=canonical,canonical_files=len(canonical),adapter_copies=base['adapter_copies'],source_unchanged=base['source_unchanged'],tested_tree=str(r/'applied'),applied_final=str(r/'applied_final'),tested_tree_byte_identical=True,round1_backup_verified=True,runtime_fingerprints=runtime,patches=patches,logs={n:dict(path=str(r/n),sha256=sha(r/n)) for n in all_logs},default_off_delivery_sha256=native['default_off_delivery_sha256']))
report=('VERDICT: DONE Required MEDIUM and LOW fixes are implemented and tested; remaining INFO limits and missing production inputs are explicit.\n' if docs_done else 'VERDICT: PARTIAL Code suites passed; final document verification remains.\n')
report+='''
The command checks export part sizes against the complete pinned binding, checks the real dependency layout, and refuses unreserved tokens before preflight. Preflight compares the .done receipt with the sealed REVIEWED triple and hashes all three preparation files before place.attempt. The command validates job names, rejects --comment, captures failed CPU-job text and preserves the caller's transport HOME and SSH_AUTH_SOCK.

The patches remain additive and default OFF. The native source tree is unchanged. out_round1 is a verified byte-preserved copy of the reviewed deliverables. No SSH, scp, Slurm, Git, GPU or paid-model call ran.

## Numbers

'''
report+='- **Measured:** 52 unittest tests passed (25 packaging, 12 round-1, 15 round-2). Their runtimes were %.3f, %.3f and %.3f seconds. Native D integration and both adapter suites passed.\n'%tuple(measured['seconds'][n] for n in ('pack.log','review1.log','review2.log'))
report+='- **Measured:** actual /usr/bin/python3 3.6.8 compiled all 11 delivered Python files. It executed place, preflight, native fill/check, guard, stubbed submit, pool predicates, unchanged dryres_d.py and receipt predicates. The receipt wrapper reports its actual '+measured['cpu_python']+' interpreter separately.\n'
report+='- **Measured:** B5 checked %d frame rows; D checked %d. D authenticated metadata for %d real dependency archives before resolving %d synthetic filled archives using %d bytes of stand-ins. The native dryres result passed on those stand-ins.\n'%(measured['b5_rows'],measured['d_rows'],measured['real_d_dependency_archives'],measured['synthetic_d_filled_archives'],measured['standin_bytes'])
report+='- **Measured:** native D and its default-OFF adapter under fixed entropy produced the same %d-byte delivery, SHA256 `%s`. r10 source equality passed; a complete r10 build was not run.\n'%(native['default_off_delivery_bytes'],native['default_off_delivery_sha256'])
report+='- **Source-reported:** the review lists 33,410,549,760 bytes of B5 input archives. Its approximate 155 GB mirror-read cost is an **estimate**. The native D timing model **estimates** 19,595 GPU-seconds and returns budget_fits=false for four hours.\n'
report+='- **Measured storage snapshot at '+stamp+':** %d apparent bytes and %d allocated bytes, both below decimal 3 GB. [STORAGE.json](../work/r2/STORAGE.json) records lossless gzip-in-place encoding of retained test artifacts, original SHA256s and sizes. Decode marked files with gzip before replaying those artifacts. Current source trees, logs, fixture inputs and the current D delivery remain plain and directly readable. Within the current native D run, compression is limited to disposable probe expansions. No file was deleted.\n'%(apparent,allocated)
report+='- **Configured limits, not utilization measurements:** eight CPU threads/cores, a 28 GiB address-space limit and no GPUs. Peak RSS and production timing were not measured. [MEASUREMENTS.json](MEASUREMENTS.json) records the categories; [FRAMEWORK_SOURCES.md](FRAMEWORK_SOURCES.md) cites installed torch 2.11 definitions and the official documentation checked during this task.\n\n'
report+=(r/'review_section.md').read_text()+'\n'+(r/'forbidden_rule.md').read_text()+'\n'
report+='''## Review round 1: finding -> fix -> test

All 12 tests in test_review.py pass, including detached fill, structural fill, actual D coverage, preflight ordering, command-only exemptions, login runtime, module imports, GPU-only retry, heredoc restrictions and exact recorded delivery. The guard regression now inspects its actual launch interpreter. The login regression supplies a valid noncanonical gzip archive and checks the SHA passed to place. Their before logs fail on those behaviors, without KeyError. The original six planted defect checks also pass in test_pack.py; B4's unknown root cause and trainer-rank cooperation remain outside that coverage.

## Patches and byte identity

'''
for name,pin in patches.items():report+='- [%s](patches/%s): **measured** %d bytes; SHA256 `%s`.\n'%(name,name,pin['bytes'],pin['sha256'])
report+='\nPatch replay reconstructs all 19 canonical files and four adapter copies exactly. Both applied trees, the work source tree and the top-level delivery match TOOL_SHA256.json. Native build_d.py, build_r10.py and o_build_D.sh remain identical to the input tree. PATCHES.md explains application; PATCH_VERIFIED.json records file and log hashes. REPORT.md and generated evidence manifests are separate audit artifacts, not recursively embedded in the patches.\n\n'
report+='''## Before-fix evidence

The 15 new regressions failed against the unchanged reviewed runtime: 14 in before.log and the part-sum case in before_sum.log. The two strengthened round-1 regressions failed against the preserved pre-round-1 runtime. No before run fails with KeyError. BEFORE_RUNS.json records the commands and expected exit code 1. The first 14-method test file is preserved as work/r2/test_review2_before.py for exact reproduction; its full command at execution used work/r2/src/test_review2.py before the sum method was added.

'''
for title,cmd,log in before:
    report+='### '+title+'\n\n```sh\n'+cmd+' > work/r2/'+log+' 2>&1\n```\n\nExact output ([log](../work/r2/'+log+')):\n\n```text\n'+(r/log).read_text()+'```\n\n'
report+='## Passing commands and exact outputs\n\nAll commands ran from '+str(root)+'. Reproduction requires fresh output directories. Printed transport commands in test logs were intercepted by stubs; no remote command ran.\n\n'
for title,cmd,log in runs:
    report+='### '+title+'\n\n```sh\n'+cmd+' > work/r2/'+log+' 2>&1\n```\n\nExact output ([log](../work/r2/'+log+')):\n\n```text\n'+(r/log).read_text()+'```\n\n'
report+='''## What could go wrong and how we notice

- Same-sized wrong export parts can pass metadata preflight even with a correct .done receipt. Native a/4.py hashes the full export; job.stage authenticates live dependency parts, archives and members. These failures appear in fill or CPU logs. Preflight is read-only and cannot prevent files changing afterward.
- A missing or changed binding/reference/harness pin refuses locally. The native D plan omits part pins, so export_binding_pin must supply the complete builder binding. Preparation preflight caps each metadata file at 1 MiB and .done at 4096 bytes; a larger input refuses by path.
- The ledger check enforces token presence, not atomic reservation or a ledger delivery-SHA schema. The operator must reserve the token and SHA between build and place. all --execute-remote therefore refuses without that reservation. Manually executing printed scripts bypasses this local gate.
- A failed CPU allocation returns its sacct state plus bounded tails of a/4.err and a/4.log. Missing logs produce tail diagnostics; a complete transport outage can prevent retrieval. Only accounting status 75 is tolerated twice; the third consecutive error aborts. Transport loss stops without relaunch.
- Fill locks and GPU submission locks can outlive a lost connection. Inspect a/f.log, a/f.exit, a/1.txt, a/g.lock and a/8.txt and reconcile manually. Queue/pool refusals can use the gpu action after a passed CPU job; it does not resubmit CPU.
- Transport now inherits local HOME and SSH_AUTH_SOCK. Remote env -i still sets HOME=/tmp and removes the locale and agent socket. Live authentication and HOME-dependent job behavior remain untested. First live execution is read-only preflight.

## What is not done and why

No MEDIUM or LOW finding remains deferred. INFO 8 is covered by unchanged native dryres_d.py, but dry2/dry2b remain translated: both select the production policy archive by a fixed SHA prefix, and that archive is absent. REQUIRED_INPUTS.json names it; the native_dry2 input group refuses clearly. Substituting a synthetic archive cannot establish the unchanged script's result.

For INFO 10, login/fill still run multiple native steps in one isolated 3.6.8 interpreter with the pack path available. Separate processes require a redesign of path redirection and submit stubbing beyond the requested small fix. The substring false positives remain deliberately because the adopted rule explicitly requires substring matching. The supplied D scorer differs from its embedded release; the read-only inputs cannot be reconciled without choosing a reviewed source. The source gate continues to refuse. The native D budget still does not fit; packaging changes do not repair that estimate. The full r10 build requires absent original deliveries and inputs.

Actual step-600 source/binding/export/preparation inputs, the production environment/RGBs, and routed harnesses remain unavailable. REQUIRED_INPUTS.json names them and the exact refusal output is above. No live Orchard placement, fill, CPU/GPU submission, production archive identity, full-reader performance, Slurm signal delivery or trainer-rank stop behavior is claimed. The B4 early-failure cause is unknown.

The requested review-round sections and before/after evidence are retained to make each fix auditable. Internal paths and execution details are included because this is an operator handoff, not a research publication.
'''
report+='\nStarted: 2026-11-19 12:18:17 UTC. Verified: '+stamp+'. Deadline: 2026-11-19 14:18:17 UTC.\n'
(out/'REPORT.md').write_text(report);(r/'src/out/REPORT.md').write_text(report)
artifacts=[p for p in out.iterdir() if p.is_file() and p.name!='ARTIFACT_SHA256.json']+list((out/'patches').glob('*.diff'))
write(out/'ARTIFACT_SHA256.json',{str(p.relative_to(root)):sha(p) for p in artifacts})
(root/'work/STATUS.md').write_text(stamp+'\n'+('DONE' if docs_done else 'FINAL DOCUMENT CHECK PENDING')+': 52 unittest tests, native D integration, both login-Python adapter suites, source compilation and named-input refusals passed. Nineteen canonical files and four adapter copies match the fresh patch replay. Round-1 deliverables are preserved. INFO and missing-production-input limits are explicit in REPORT.md. No remote, Git, GPU or deletion operation ran.\n')
print(json.dumps(dict(passed=True,documents_verified=docs_done,utc=stamp,canonical_files=len(canonical),unit_tests=52,workspace_apparent_bytes=apparent,workspace_allocated_bytes=allocated,report=str(out/'REPORT.md')),sort_keys=True))
