"""Check the final evidence and publish the operator report."""
from pathlib import Path
import gzip,hashlib,json,re,subprocess,sys
r=Path(__file__).resolve().parent;root=r.parents[1];out=root/'out';final=r/'final'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
stamp=subprocess.check_output(['date','-u','+%Y-%m-%d %H:%M:%S UTC']).decode().strip()
base=read(r/'PATCH_BASE.json');canonical=base['canonical']
for name,h in canonical.items():
    for tree in (root,r/'src',r/'applied_final',r/'applied_verified'):assert sha(tree/name)==h,(tree,name)
for name,h in base['adapter_copies'].items():assert sha(r/'applied_verified'/name)==h
inp=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
for name,h in base['source_unchanged'].items():assert sha(inp/name)==h
for name,h in read(root/'out_round2/TOOL_SHA256.json').items():
    if name.endswith('.py'):assert sha(r/'before'/name)==h,name
for name,h in read(root/'out_round2/ARTIFACT_SHA256.json').items():assert sha(root/'out_round2'/Path(name).relative_to('out'))==h,name
runtime={n:canonical[n] for n in ('pack.py','pack_checks.py','pack_structural.py','pack_verify.py')}
runs=read(final/'RUNS.json')['runs'];before=runs[0];passing=runs[1:]
if (final/'DOC_RUNS.json').is_file():passing+=read(final/'DOC_RUNS.json')
assert before['name']=='before_final' and before['returncode']==1
before_text=Path(before['log']).read_text()
assert 'Ran 22 tests' in before_text and 'FAILED (failures=' in before_text and not re.search(r'^(ERROR:|KeyError:|ModuleNotFoundError:)',before_text,re.M)
for row in passing:assert row['returncode']==row['expected_returncode']==0,row
counts=dict(pack=25,review1=12,review2=15,review3=22,review3_login=22)
seconds={}
for name,count in counts.items():
    text=(final/(name+'.log')).read_text();assert 'Ran %d tests'%count in text and '\nOK\n' in text,name
    seconds[name]=float(re.search(r'Ran \d+ tests in ([0-9.]+)s',text).group(1))
native=read(final/'native/RESULT.json');assert native['passed'] and native['d_all_checks_passed']
positive=read(final/'pack/POSITIVE.json');dcheck=read(final/'native/D_CHECK.json')
assert positive['check']['checker']==dcheck['check']['checker']==runtime
assert native['default_off_delivery_bytes']==5272732
for name in ('adapter_r10','adapter_d'):assert read(final/(name+'.log'))['passed']
assert 'compiled_delivered_sources=13' in (final/'small_checks.log').read_text()
assert (final/'small_checks.log').read_text().endswith('PASS: missing inputs refuse before a builder or remote call\n')
for row in [before]+passing:row['sha256']=sha(row['log'])
replay=dict(name='fresh_patch_replay',command="nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r3/package.py applied_verified > work/r3/package_verified.log 2>&1",returncode=0,expected_returncode=0,log=str(r/'package_verified.log'),sha256=sha(r/'package_verified.log'))
assert read(replay['log'])['passed'];passing.append(replay)
write(out/'TEST_RUNS.json',dict(cwd=str(root),runs=passing))
write(out/'BEFORE_RUNS.json',dict(cwd=str(root),runs=[before],source=str(r/'before'),source_matches='out_round2/TOOL_SHA256.json',test_source=str(r/'applied_final/test_review3.py'),test_sha256=canonical['test_review3.py'],note='All 22 methods fail on defect assertions, including subtests; there are no errors or KeyError failures. The separate runner path setup diagnostic is retained under work/r3/final/SETUP_DIAGNOSTIC.json and is not defect evidence.'))
patches={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((out/'patches').glob('*.diff'))}
# Validate every retained representation without restoring large trees.
storage=read(r/'STORAGE.json');cache={}
def encoded(path,trail=()):
    assert path not in trail,'Cyclic storage reference'
    if path in cache:return cache[path]
    raw=(root/path).read_bytes()
    if len(raw)<4096:
        try:v=json.loads(raw)
        except (ValueError,UnicodeDecodeError):v={}
        if isinstance(v,dict) and v.get('encoding')=='PACKREF1':
            raw=encoded(v['reference'],trail+(path,));assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256']
    # References share byte objects; retained data are bounded by the 3 GB workspace.
    cache[path]=raw
    return raw
for row in storage['files']:
    raw=encoded(row['path'])
    if row['encoding']=='gzip in place':raw=gzip.decompress(raw)
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
allocated=int(subprocess.check_output(['nice','-n','10','du','-s','-B1',str(root)]).split()[0])
apparent=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());assert max(apparent,allocated)<3000000000
measured=dict(utc=stamp,distinct_unittest_methods=74,unittest_executions=96,counts=counts,seconds=seconds,cpu_python=sys.version.split()[0],login_python='3.6.8',compiled_delivered_sources=13,b5_rows=positive['check']['checks']['logic']['rows_checked'],d_rows=dcheck['check']['checks']['logic']['rows_checked'],real_d_dependency_archives=dcheck['check']['checks']['fill']['dependency_reference']['real_dependency_archives'],synthetic_d_filled_archives=dcheck['check']['checks']['fill']['resolution']['archives'],standin_bytes=dcheck['check']['checks']['fill']['standin_bytes'],default_off_delivery_bytes=native['default_off_delivery_bytes'],default_off_delivery_sha256=native['default_off_delivery_sha256'],workspace_apparent_bytes=apparent,workspace_allocated_bytes=allocated,storage_encoded_files=len(storage['files']),losslessly_saved_bytes=storage['saved_bytes'],canonical_files=len(canonical))
write(out/'MEASUREMENTS.json',dict(measured=measured,estimated=dict(full_mirror_reads_bytes=155000000000,d_budget_gpu_seconds=native['pack_build']['native_budget_gpu_seconds']),source_reported=dict(b5_archive_bytes=33410549760,source='/scratch/jjyeung/orch_n30/so_cr_pack_a/REVIEW_VERDICT.md'),unmeasured=['live Orchard tar-header layout','production export verification','production hashing duration','full-reader/GPU performance','peak RSS','live Slurm and transport']))
write(out/'PATCH_VERIFIED.json',dict(passed=True,utc=stamp,canonical=canonical,adapter_copies=base['adapter_copies'],source_unchanged=base['source_unchanged'],tested_tree=str(r/'applied_final'),patch_replay=str(r/'applied_verified'),tested_tree_byte_identical=True,round2_backup_verified=True,before_source_verified=True,runtime_fingerprints=runtime,patches=patches,logs={row['name']:dict(path=row['log'],sha256=row['sha256']) for row in [before]+passing},default_off_delivery_sha256=native['default_off_delivery_sha256']))
report='''VERDICT: DONE Required round-3 fixes are implemented and tested; live Orchard confirmation and unavailable production inputs remain explicit prerequisites.

Detached verification hashes all four export parts before placement. Preflight requires its path/size/mtime receipt to match the binding SHA256s, checks ctime/device/inode, validates the first tar header, and retains the REVIEWED .done and preparation-hash gates. Conflicting source-export paths refuse locally. Wrong same-size parts refuse before place.attempt.

Verification writes only under the package's private v/ directory and needs no ledger reservation. Every remote action requires --yes and the exact built token. A completed verification failure permits an explicit same-token retry after correcting staging; the launcher archives failed files inside v/. Active, successful or uncertain verification attempts refuse relaunch. Place accepts a private verify-only root and claims a/ exclusively. No SSH, scp, Slurm, Git, GPU or paid-model call ran here.

## Numbers

'''
report+='- **Measured:** 74 distinct unittest methods passed: 25 packaging, 12 round-1, 15 round-2 and 22 round-3. All 22 round-3 methods also passed under actual /usr/bin/python3 3.6.8, for 96 main-suite executions. Native D integration, both adapter suites and six final document checks passed separately.\n'
report+='- **Measured:** 13 delivered Python files compile under 3.6.8. That interpreter executes verification, preflight, placement, native fill/check, guard, stubbed sbatch, pool predicates and native dryres_d.py. CPU Python is '+measured['cpu_python']+'.\n'
report+='- **Measured:** B5 checked %d frame rows; D checked %d. D checked %d real dependency archive records before resolving %d synthetic filled archives with %d bytes of stand-ins.\n'%(measured['b5_rows'],measured['d_rows'],measured['real_d_dependency_archives'],measured['synthetic_d_filled_archives'],measured['standin_bytes'])
report+='- **Measured:** native D and the default-OFF adapter produce the same %d-byte delivery under fixed entropy: SHA256 `%s`. r10 source identity passed; its full build did not run.\n'%(measured['default_off_delivery_bytes'],measured['default_off_delivery_sha256'])
report+='- **Source-reported:** B5 input archives total 33,410,549,760 bytes. **Estimated:** full mirror reads total about 155 GB; the native D budget model returns %s GPU-seconds and budget_fits=false. Neither is a measured production runtime.\n'%native['pack_build']['native_budget_gpu_seconds']
report+='- **Measured storage snapshot (%s):** %d apparent bytes; %d allocated bytes, below decimal 3 GB. Lossless reference/gzip representations saved %d bytes. [Storage manifest](../work/r3/STORAGE.json) records exact hashes and decoding instructions; no file was deleted. Reviewed outputs, before/runtime sources, logs and final native delivery files remain directly readable. Encoded disposable test artifacts must be decoded before direct inspection; fresh test runs use unchanged plain fixture inputs.\n'%(stamp,apparent,allocated,storage['saved_bytes'])
report+='- **Configured limits, not utilization measurements:** at most eight CPU cores/threads, a 28 GiB address-space limit, nice priority and no GPUs. Peak RSS, production hash time and GPU behavior were not measured. [Framework sources](FRAMEWORK_SOURCES.md) cite installed torch 2.11 and Python 3.6 definitions plus official documentation.\n\n'
report+=(r/'review_section.md').read_text()+'\n'+(r/'forbidden_rule.md').read_text()+'\n'+(r/'legacy_sections.md').read_text()+'\n'
report+='''## Patches and byte identity

Both patches are additive against the supplied input tree and default OFF. The token adapter and native builder sources are unchanged. The tested work/r3/applied_final tree, fresh work/r3/applied_verified replay, work/r3/src and top-level delivery match all 21 canonical hashes; four adapter copies also match. out_round2 matches its preserved artifact manifest. The untouched before source matches its reviewed tool hashes. REPORT.md and generated audit manifests are separate evidence artifacts, outside the patches.

'''
for name,pin in patches.items():report+='- [%s](patches/%s): **measured** %d bytes; SHA256 `%s`.\n'%(name,name,pin['bytes'],pin['sha256'])
report+='''
## What could go wrong and how we notice

- Orchard must **confirm header layout on the staged m544 part 0, read-only**. The 512-byte gate assumes an ordinary uncompressed tar header naming the sealed member_directory or a child. PAX/GNU extension-first layouts refuse. Planted ordinary headers cover both acceptance and wrong-step refusal under 3.6.8; no real header was read.
- Parts can change after preflight. The receipt detects changed paths, sizes, mtimes, ctimes and inode/device identity; native fill still hashes the full export. A successful verification followed by changed parts requires manual reconciliation, because successful/uncertain attempts do not relaunch. A recorded failed verification permits an explicit retry; it never creates place.attempt or a/f.lock.
- Verify failure logs are v/0.log and v/0.exit; success requires v/0.json and v/0.txt. Retry archives previous failure files under a private hex subdirectory in v/. A transport loss or deadline stops without automatic retry. Default verify_wait/fill_wait is 1800 seconds, not a measured production requirement.
- Ledger reservation remains an operator action. The gate checks token presence, not atomic locking or delivery-SHA format. all cannot reserve the ledger for the operator. Printed place commands include preflight first; manually executing scripts bypasses local authorization and ledger checks.
- Dependency byte identity still requires job.stage on Orchard. A missing binding/reference/harness refuses locally. .done is capped at 4096 bytes, each preparation file at 1 MiB, and the verify receipt at 16 KiB; larger inputs refuse.
- CPU failures include bounded a/4.err and a/4.log tails. Only explicit sacct exit 75 is tolerated twice; the third consecutive error aborts. A total transport outage can prevent log retrieval. Fill/GPU locks need manual reconciliation after uncertainty.
- The local transport inherits HOME and SSH_AUTH_SOCK; remote HOME remains /tmp. Live authentication, locale-sensitive behavior, full-reader inputs, pool quotas and GPU memory/performance remain unverified.

## What is not done and why

No requested round-3 MEDIUM/LOW or small INFO fix is deferred. INFO 4 and 5 are also fixed. Finding 8 remains open:

- D score_d.py differs from its embedded release. Choosing/regenerating a coherent source requires a reviewed production input; the native release gate still refuses the supplied mismatch.
- The native D timing model estimates budget_fits=false. Packaging fixes cannot establish or repair production runtime.
- Full r10 and step-600 builds lack required authenticated deliveries, bindings and preparation/export inputs. REQUIRED_INPUTS.json names them and the checks refuse before release.
- Unchanged dry2/dry2b need the absent 10,240 B a3.tar at slot 4 (SHA256 prefix 05dc8f79). Native dryres_d.py runs unchanged on stand-ins; translated predicates do not establish the absent native run.
- Login/fill probes share one 3.6.8 interpreter across native steps. A separate-process filesystem/submit harness exceeds the small INFO scope. Real process isolation remains unverified.
- B4's early-failure cause remains unknown. Trainer-rank USR1 cooperation needs a real multi-rank signal test, prohibited in this dispatch.

The requested review sections and before/after evidence remain because they make each fix auditable. Internal paths and execution details serve this operator handoff. Exact suite commands below require fresh output directories; all remote calls in tests are redirected or stubbed.

## Before-fix command and exact output

All 22 regression methods fail on the original defects. The evidence contains assertion failures, not missing imports or KeyError. BEFORE_RUNS.json records source and test-file hashes.

'''
for row in [before]+passing:
    if row is passing[0]:report+='## Passing commands and exact outputs\n\n'
    report+='### '+row['name']+'\n\n```sh\n'+row['command']+'\n```\n\nExit code: '+str(row['returncode'])+'. Exact output ([log]('+str(Path(row['log']).relative_to(root)).replace('work/','../work/',1)+')):\n\n```text\n'+Path(row['log']).read_text()+'```\n\n'
report+='Started: 2026-11-19 13:10:30 UTC. Verified: '+stamp+'. Deadline: 2026-11-19 15:10:30 UTC.\n'
(out/'REPORT.md').write_text(report);(r/'src/out/REPORT.md').write_text(report)
artifacts=[p for p in out.iterdir() if p.is_file() and p.name!='ARTIFACT_SHA256.json']+list((out/'patches').glob('*.diff'))
write(out/'ARTIFACT_SHA256.json',{str(p.relative_to(root)):sha(p) for p in artifacts})
(root/'work/STATUS.md').write_text(stamp+'\nDONE: round-3 fixes and all small INFO fixes pass. 74 distinct unittest methods plus 22 login-Python repetitions, native D integration, both adapters and compile/input checks passed. All 22 before methods fail on defects. Twenty-one canonical files and four adapter copies match fresh patch replay. Orchard header confirmation and production prerequisites remain in out/REPORT.md.\n')
print(json.dumps(dict(passed=True,utc=stamp,distinct_unittest_methods=74,login_repetitions=22,canonical_files=21,workspace_apparent_bytes=apparent,workspace_allocated_bytes=allocated,report=str(out/'REPORT.md')),sort_keys=True))
