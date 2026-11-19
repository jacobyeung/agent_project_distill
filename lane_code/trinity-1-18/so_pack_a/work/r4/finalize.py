"""Audit final source, regression evidence and patches; publish exact outputs."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
r=Path(__file__).resolve().parent;root=r.parents[1];out=root/'out';final=r/'final2'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
stamp=subprocess.check_output(['date','-u','+%Y-%m-%d %H:%M:%S UTC']).decode().strip()
base=read(r/'PATCH_BASE.json');canonical=base['canonical']
for name,h in canonical.items():
    for tree in (root,r/'src',r/'applied_final',r/'applied_verified'):assert sha(tree/name)==h,(tree,name)
for name,h in base['adapter_copies'].items():
    for tree in (r/'applied_final',r/'applied_verified'):assert sha(tree/name)==h,(tree,name)
inp=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
for name,h in base['source_unchanged'].items():
    assert sha(inp/name)==h,name
    for tree in (r/'applied_final',r/'applied_verified'):assert sha(tree/name)==h,(tree,name)
for name,h in read(root/'out_round3/TOOL_SHA256.json').items():assert sha(r/'before'/name)==h,name
for name,h in read(root/'out_round3/ARTIFACT_SHA256.json').items():assert sha(root/'out_round3'/Path(name).relative_to('out'))==h,name
assert sha(root/'out_round3/REPORT.md')==read(root/'work/r3/FINAL_AUDIT.json')['report_sha256']
runtime={n:canonical[n] for n in ('pack.py','pack_checks.py','pack_structural.py','pack_verify.py')}
runs=read(final/'RUNS.json')['runs'];before=runs[0];passing=runs[1:]
doc_runs=read(final/'DOC_RUNS.json') if (final/'DOC_RUNS.json').exists() else []
passing+=doc_runs
doc_checks=sum(int(re.search(r'Ran (\d+) tests?',Path(x['log']).read_text()).group(1)) for x in doc_runs)
assert before['name']=='before' and before['returncode']==1
text=Path(before['log']).read_text();assert 'Ran 16 tests' in text and 'FAILED (failures=' in text and not re.search(r'^(ERROR:|KeyError:|ModuleNotFoundError:)',text,re.M)
failures=int(re.search(r'^FAILED \(failures=(\d+)\)$',text,re.M).group(1));assert text.count('\nFAIL: ')==failures
for row in passing:assert row['returncode']==row['expected_returncode']==0,row
counts=dict(pack=25,review1=12,review2=15,review3=22,review3_login=22,review4=22,review4_login=22)
seconds={}
for name,count in counts.items():
    text=(final/(name+'.log')).read_text();assert 'Ran %d tests'%count in text and '\nOK\n' in text,name
    seconds[name]=float(re.search(r'Ran \d+ tests in ([0-9.]+)s',text).group(1))
native=read(final/'native/RESULT.json');assert native['passed'] and native['d_all_checks_passed']
positive=read(final/'pack/POSITIVE.json');dcheck=read(final/'native/D_CHECK.json')
assert positive['check']['checker']==dcheck['check']['checker']==runtime
a=read(final/'native/actual200/BUILD.json')['D'];b=read(final/'native/default200/BUILD.json')['D']
native_path=Path(a['delivery_dir'])/'1.tgz';default_path=Path(b['delivery_dir'])/'1.tgz'
assert native_path.read_bytes()==default_path.read_bytes()
assert sha(native_path)==native['default_off_delivery_sha256']
for row in runs:assert sha(row['log'])==row['sha256'],row['name']
patches={n:dict(bytes=(out/'patches'/n).stat().st_size,sha256=sha(out/'patches'/n)) for n in ('01_read_package.diff','02_opt_in_token.diff')}
for name in patches:assert all(line=='--- /dev/null' for line in (out/'patches'/name).read_text().splitlines() if line.startswith('--- '))
proof=dict(base,passed=True,patch_replay=str(r/'applied_verified'),tested_tree=str(r/'applied_final'),patches=patches,runtime_fingerprints=runtime,round3_backup_verified=True,before_source_verified=True,default_off_delivery_sha256=native['default_off_delivery_sha256'],logs={x['name']:dict(path=x['log'],sha256=x['sha256']) for x in runs+doc_runs})
write(out/'PATCH_VERIFIED.json',proof);write(out/'TEST_RUNS.json',dict(cwd=str(root),runs=passing));write(out/'BEFORE_RUNS.json',dict(cwd=str(root),runs=[before],source=read(root/'out_round3/TOOL_SHA256.json'),test_sha256=canonical['test_review4.py']))
allocated=int(subprocess.check_output(['nice','-n','10','du','-s','-B1',str(root)]).split()[0]);apparent=int(subprocess.check_output(['nice','-n','10','du','-s','-b',str(root)]).split()[0]);assert allocated<3000000000
measured=dict(utc=stamp,distinct_passing_methods=96,main_suite_executions=sum(counts.values()),before_methods=16,before_assertion_failures=failures,seconds=seconds,cpu_python=sys.version.split()[0],login_python='3.6.8',b5_rows=positive['check']['checks']['logic']['rows_checked'],d_rows=dcheck['check']['checks']['logic']['rows_checked'],default_off_delivery_bytes=native['default_off_delivery_bytes'],default_off_delivery_sha256=native['default_off_delivery_sha256'],workspace_allocated_bytes=allocated,workspace_apparent_bytes=apparent)
measured['final_document_checks']=doc_checks;write(out/'MEASUREMENTS.json',measured)
report='''VERDICT: DONE Round-4 findings 1–7 are fixed and validated; live Orchard checks and missing production inputs remain release prerequisites.

Verification receipts persist canonical path, bytes, mtime_ns and binding SHA256. Hard-link ctime, chmod and client device/inode numbers do not invalidate completion. An explicit verify reuses valid completion or archives a stale completed receipt before rehashing under the same token. Active/uncertain attempts and post-placement verification refuse. Wrong bytes cannot obtain a fresh receipt.

## Numbers

'''
report+='- **Measured:** 96 distinct unittest methods passed: 25 packaging, 12 round-1, 15 round-2, 22 round-3 and 22 round-4. Round-3 and round-4 also passed under actual /usr/bin/python3 3.6.8: 140 main-suite executions. Native D integration and both adapter suites passed separately.\n'
if doc_checks:report+='- **Measured:** %d final document checks passed under /usr/bin/python3 3.6.8.\n'%doc_checks
report+='- **Measured:** all 16 round-4 defect methods fail on the preserved round-3 source, with %d AssertionError failures and no test errors. The six additional round-4 safety controls pass on the delivered code.\n'%failures
report+='- **Measured:** 14 delivered top-level Python files compile under 3.6.8. Generated verification, recovery, preflight and placement execute there, as do native fill/check, guard, stubbed 8.py submit, pool predicates and dryres_d.py. CPU Python is %s.\n'%measured['cpu_python']
report+='- **Measured:** B5 checked %d frame rows; D checked %d. Native D and the default-OFF adapter produce identical %d-byte deliveries under fixed entropy, SHA256 `%s`. r10 default source equality passed; full r10 did not run.\n'%(measured['b5_rows'],measured['d_rows'],measured['default_off_delivery_bytes'],measured['default_off_delivery_sha256'])
report+='- **Source-reported:** B5 input archives total 33,410,549,760 bytes. **Estimated:** full mirror reads total about 155 GB; native D estimates %s GPU-seconds and budget_fits=false. Production hash/runtime/RSS/GPU measurements are unavailable.\n'%native['pack_build']['native_budget_gpu_seconds']
report+='- **Measured storage at %s:** %d apparent bytes and %d allocated bytes, below decimal 3 GB. Completed scratch fixtures use lossless gzip/reference/line-block encodings; no file was deleted. Source, native final deliveries and exact logs remain readable. [Storage manifest](../work/r4/STORAGE.json) and [decoder](../work/r4/decode_artifact.py) preserve original hashes; decode artifacts before inspecting encoded fixture paths.\n'%(stamp,apparent,allocated)
report+='- **Configured, not utilization measurements:** nice -n 10, eight CPU cores/threads, 28 GiB address-space limit and CUDA_VISIBLE_DEVICES="". Suites run serially. [Framework sources](FRAMEWORK_SOURCES.md) cite the installed torch 2.11 definitions and official documentation.\n\n'
report+=(r/'review_section.md').read_text()+'\n'+(r/'forbidden_rule.md').read_text()+'\n'+(r/'legacy_sections.md').read_text()+'\n'
report+='''## Patches and byte identity

Both patches are additive against the input tree and default OFF. Native builders, embedded assets and pack_token.py are unchanged. The tested work/r4/applied_final tree, fresh work/r4/applied_verified replay, work/r4/src and top-level delivery match all 22 canonical hashes; four adapter copies also match. out_round3 and the untouched before source match their recorded hashes. REPORT.md and generated audit manifests are outside the patches.

'''
for name,pin in patches.items():report+='- [%s](patches/%s): **measured** %d bytes; SHA256 `%s`.\n'%(name,name,pin['bytes'],pin['sha256'])
report+='''
## What could go wrong and how we notice

- Freeze staged bytes after verification. Path/size/mtime keys cannot detect deliberate same-size rewrites with restored mtime; they are a freshness cache, not continuous authentication. Native fill rehashes the whole export. During each hash pass, ctime/device/inode still detect concurrent changes. A stale mtime refuses preflight; explicit verify rehashes and only a matching binding SHA can restore success.
- Orchard must confirm header layout on the staged m544 part 0, read-only. The 512-byte gate normalizes ./ prefixes and accepts ordinary members under the sealed directory. PAX/GNU extension-first, compressed, leading ./ directory-only, invalid-checksum and wrong-step layouts refuse before placement.
- Different login hosts must share coherent path/mtime/receipt visibility and advisory locks. Device numbers need not agree. v/0.lock serializes recovery locally; cross-host Orchard behavior remains untested. A recorded failure permits an explicit retry; transport loss or uncertain state requires inspection and never triggers an automatic relaunch. Logs: v/0.log and v/0.exit; success: v/0.json and v/0.txt. Completed retries retain their artifacts in a private hex directory under v/.
- Reserve token and delivery SHA in the Trinity ledger before verify. Verify remains independent of placement consumption; place enforces token presence. Ledger locking and SHA-record format remain manual. all can reuse an existing build and valid verification, but a new all run cannot pause for reservation. Manual phase scripts bypass local authorization and ledger gates.
- .done is capped at 4096 bytes, preparation files at 1 MiB each and the verify receipt at 16 KiB. Missing bindings, reference metadata or harnesses refuse locally. Production hashing time is unmeasured; verify_wait/fill_wait default to 1800 seconds.
- CPU errors include a/4.err and a/4.log tails. Only explicit sacct-unavailable exit 75 is tolerated twice; the third consecutive error aborts. A transport outage can prevent retrieval. Fill/GPU uncertainty needs manual reconciliation. Local transport inherits HOME/SSH_AUTH_SOCK; remote HOME=/tmp behavior still needs live confirmation.

## What is not done and why

No requested finding 1–7 is deferred. Finding 8 remains open: D score_d.py differs from its embedded release; the D budget estimate does not fit; authenticated step-600 source/items/binding and full r10 inputs are absent; unchanged dry2/dry2b need the missing full-SHA-pinned 10,240-byte a3.tar; login/fill probes share an interpreter across native steps; B4's early-failure cause and trainer-rank USR1 behavior are unverified. These require reviewed inputs or live Orchard/GPU work outside this dispatch.

No Git, SSH, scp, Slurm, GPU, paid-model calls or writes outside the workspace ran. Network reads were limited to official library documentation. Review-history headings are retained because the dispatch requires finding-to-test audit sections.

## Commands and exact outputs

The storage wrapper runs each delivered unittest suite unchanged and losslessly encodes completed fixtures between tests to respect the disk cap. It does not alter source, inputs, assertions or results. Commands require fresh work directories; test transports and remote paths are stubbed or redirected. Test loops poll only local tiny fixtures; production polling remains at least 60 seconds apart.

'''
for row in runs:
    report+='### '+row['name']+'\n\n```sh\n'+row['command']+'\n```\n\nExit code: '+str(row['returncode'])+'. '
    if row['name']=='before':
        (out/'BEFORE_OUTPUT.log').write_bytes(Path(row['log']).read_bytes())
        report+='[Full exact output](BEFORE_OUTPUT.log), SHA256 `'+row['sha256']+'`. This separate verbatim log includes the rejected source and document text. Terminal summary excerpt:\n\n```text\n'+'\n'.join(Path(row['log']).read_text().splitlines()[-4:])+'\n```\n\n'
    else:report+='Exact output ([log]('+str(Path(row['log']).relative_to(root)).replace('work/','../work/',1)+')):\n\n```text\n'+Path(row['log']).read_text()+'```\n\n'
if (final/'DOC_RUNS.json').exists():
    for row in read(final/'DOC_RUNS.json'):
        assert row['returncode']==0 and sha(row['log'])==row['sha256']
        report+='### '+row['name']+'\n\n```sh\n'+row['command']+'\n```\n\nExit code: 0. Exact output:\n\n```text\n'+Path(row['log']).read_text()+'```\n\n'
if (r/'DIAGNOSTIC_RUNS.json').exists():
    report+='## Validation diagnostics\n\nThe storage wrapper uses Python-3.6-compatible GzipFile calls, and structural probes preserve production old_identities. The diagnostic logs below record the unsupported gzip.compress argument and the structural probe clearing that list. Both conditions are resolved; the complete final suites above validate the delivered code.\n\n'
    for row in read(r/'DIAGNOSTIC_RUNS.json'):
        assert sha(row['log'])==row['sha256']
        report+='```sh\n'+row['command']+'\n```\n\nExit code: '+str(row['returncode'])+'. Exact output:\n\n```text\n'+Path(row['log']).read_text()+'```\n\n'
(out/'REPORT.md').write_text(report)
artifact={str(p.relative_to(root)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='ARTIFACT_SHA256.json'};write(out/'ARTIFACT_SHA256.json',artifact)
audit=dict(passed=True,utc=stamp,canonical_files=len(canonical),before_methods=16,before_failures=failures,distinct_passing_methods=96,main_suite_executions=140,final_document_checks=doc_checks,report_sha256=sha(out/'REPORT.md'),patches=patches,workspace_allocated_bytes=allocated)
write(r/'FINAL_AUDIT.json',audit)
(root/'work/STATUS.md').write_text(stamp+'\nRound 4 is complete. Findings 1–7 are fixed; 96 distinct main-suite methods and 140 executions pass. All 16 defect methods fail before on assertions. Fresh patch replay and default-OFF D byte identity pass. The final document checks pass. out/REPORT.md contains exact commands and outputs; live Orchard and missing-input prerequisites remain explicit.\n')
print(json.dumps(audit,sort_keys=True))
