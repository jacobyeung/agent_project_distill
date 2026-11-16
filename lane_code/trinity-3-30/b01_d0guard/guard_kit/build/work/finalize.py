import datetime,hashlib,json,pathlib,re,subprocess,sys
B=pathlib.Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit';sys.path.insert(0,str(K))
from guard_core import read,write,sha
old={n:sha(O/n) for n in ('code_g1.tar','inputs_g1.tar','FAMILY.json')}
r=subprocess.run([sys.executable,'-I','-s','-B',str(B/'work/package_review.py')],capture_output=True,text=True)
if r.returncode:raise RuntimeError(r.stdout+r.stderr)
new={n:sha(O/n) for n in old}
if old!=new:raise ValueError('Deterministic packaging differed')
write(O/'DETERMINISM.json',dict(status='PASS',first=old,second=new))
def result(path):
 text=(O/path).read_text();matches=re.findall(r'Ran (\d+) tests?',text)
 return dict(log=str(O/path),tests=int(matches[-1]) if matches else None,pass_=bool(re.search(r'^OK$',text,re.M)))
checks=dict(g1=result('tests/g1_final.log'),stager=result('tests/stage_final.log'),c8r=read(O/'C8R_TESTS.json'),report=read(O/'REPORT_TESTS.json'))
count=checks['g1']['tests']+checks['stager']['tests']+checks['c8r']['tests']+checks['report']['tests']
mut=read(O/'MUTANTS.json')
checks['c8r']['pass_']=checks['c8r']['failures']==checks['c8r']['errors']==0
checks['report']['pass_']=checks['report']['failures']==checks['report']['errors']==0
assert all(v['pass_'] for v in checks.values())
assert mut['complete'] and mut['killed']==mut['total']
report=B.parents[1]/'guard_kit/report/guard_read.py';rp=read(O/'rehearsal/records_pass/RESULT.json');rm=read(O/'rehearsal/records_mismatch/RESULT.json')
assert sha(report)==rp['report_sha256']
checks.update(report_mutations=dict(source=str(O/'MUTANTS.json'),total=mut['total'],detected=mut['killed']),
 source_identity=dict(source=str(O/'SOURCE_IDENTITY.json'),status='PASS'),
 archive_validation=dict(source=str(O/'ARCHIVE_VALIDATION.json'),status='PASS'),
 deterministic_packaging=dict(source=str(O/'DETERMINISM.json'),status='PASS'),
 recorded_rehearsal=dict(source=str(O/'rehearsal/records_pass/RESULT.json'),status=rp['status'],whole_worker=False),
 proof_mismatch_rehearsal=dict(source=str(O/'rehearsal/records_mismatch/RESULT.json'),status=rm['status'],candidate_items=rm['candidate_items']),
 whole_worker=dict(status='BLOCKED',source=str(O/'rehearsal/namespace.stderr'),production_config_transport_only=False,
                   reasons=['Namespace denied','Candidate training closure absent','Production workflow integration absent']),
 naming=dict(status='BLOCKED',source=str(O/'NAMING_SCAN.json')))
write(O/'TESTS.json',dict(overall='NOT_READY',unit_tests=count,all_executed_unit_tests_pass=True,checks=checks,
 not_run=['Inherited C8r return/package suites','Whole-worker CPU preparation/restoration/decoding','GPU identity proof and candidate canary','Live cloud/Orchard admission and publication','Candidate restoration with its actual metadata','Hard-link census of unavailable large inherited input archives']))
blocks=read(O/'RELEASE_BLOCKERS.json')['blockers']
code=read(O/'CODE_MANIFEST.json');inp=read(O/'INPUT_MANIFEST.json');size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file() and not p.is_symlink())
if size>6*10**9:raise ValueError('Build exceeds byte cap')
write(O/'BUILD_SIZE.json',dict(measured_bytes=size,cap_bytes=6*10**9,status='PASS',scope=str(B),measurement='Before the final readiness, status and event text; includes existing inputs and logs.'))
ready=['# NOT READY — partial review package','', 'The requested submit-ready kit is not complete. The code, reference inputs, tests and audits below are available for review. `packet.py packet` refuses every launch; no batch was emitted.', '', f'- Code archive: `code_g1.tar`, SHA256 `{code["sha256"]}` (`CODE_MANIFEST.json`).',f'- Input archive: `inputs_g1.tar`, SHA256 `{inp["sha256"]}` (`INPUT_MANIFEST.json`).', '- Draft family: `FAMILY.json`; new object generations are `PENDING_UPLOAD`.', '- Source changes: `DIFF.md`, `DIFF.patch`; original source equality: `SOURCE_IDENTITY.json`.', '- Pin census and restoration requirements: `PIN_CLASSIFICATION.md`, `PIN_CLASSIFICATION.json`, `RESTORATION.md`.', '- Naming audit and operational copy commands: `NAMING.md`, `NAMING_OCCURRENCES.jsonl`, `RUN.md`.', '- Local tests and fixture limits: `TESTS.json`, `rehearsal/RUNBOOK.md`.', '- Resource estimate and measured local size: `SIZING.md`, `SIZING.json`, `BUILD_SIZE.json`.', '', f'Executed unit checks: {count} passed (`TESTS.json`). Report mutants detected: {mut["killed"]} of {mut["total"]} (`MUTANTS.json`). The recorded-row fixture runs the unchanged report against itself; it proves no model/backend identity.', '', 'Release blockers:', '']
ready+=['- '+x for x in blocks]
ready+=['','No candidate restoration, real token replay, live cloud upload, Orchard resource admission or production publication was checked. The sandbox refused namespace creation. This is not solely an environment blocker: production integration and naming migration also remain unfinished.', '', 'An independent review can inspect the implemented components now. It cannot approve this family for submission until the listed work and whole-worker validation are complete.','']
(O/'GUARD_KIT_READY.md').write_text('\n'.join(ready))
(B/'STATUS.md').write_text('# Status: NOT READY\n\nThe one-shot build produced a partial review package in `out/`. It did not produce a submit-ready job.\n\nImplemented: strict completion-record/archive checks, unchanged reviewed stager wrapper, native-arm AST selection, deterministic reference/canary membership, proof/canary sequencing, pin census, naming inventory, deterministic archives and local tests.\n\nBlocked or unfinished: candidate training closure, production batch/staging/publication integration, complete naming migration and whole-worker rehearsal. `out/RELEASE_BLOCKERS.json` records the blockers.\n\n`out/TESTS.json` records passing component checks and explicitly blocked whole-worker/naming checks. No upload, submission, GPU operation or network request ran.\n')
now=datetime.datetime.now(datetime.timezone.utc);event=B/'events'/(now.strftime('%Y%m%dT%H%MZ')+'_RESULT_final.md')
lines=['# RESULT: NOT READY — partial G1 build', '', 'The requested submit-ready kit is incomplete; no runnable batch was emitted.', '', 'Delivered `out/guard_kit/`, deterministic archives, draft FAMILY and source diffs.', f'Code SHA256: `{code["sha256"]}` (`out/code_g1.tar`; `out/CODE_MANIFEST.json`).', f'Input SHA256: `{inp["sha256"]}` (`out/inputs_g1.tar`; `out/INPUT_MANIFEST.json`).', 'All original C8r source bytes remain identical (`out/SOURCE_IDENTITY.json`).', 'The reviewed export stager and checker are copied unchanged (`out/DIFF.md`).', 'Reference and canary membership are deterministic (`out/ITEM_SELECTION.json`).', '', f'Executed unit checks: {count} passed (`out/TESTS.json`).', f'Report mutants detected: {mut["killed"]}/{mut["total"]} (`out/MUTANTS.json`).', 'The unchanged report passes on the recorded-row fixture against itself (`out/rehearsal/records_pass/report/GUARD_READ.json`).', f'Token mismatch produces a proof receipt and {rm["candidate_items"]} candidate rows (`out/rehearsal/records_mismatch/RESULT.json`).', 'The recorded-row run is not a whole-worker or model rehearsal.', '', 'Release blockers:', '- Candidate training config, preparation, data receipt and source-seal closure are absent.', '- Production dual-export staging, worker launch, early publication and packet bootstrap are unfinished.', '- Complete job-visible naming migration is unfinished.', '- The sandbox denied namespaces; whole-worker validation has not completed.', '- Live generations, independent review and launch authority remain pending.', '', 'Pin census: `out/PIN_CLASSIFICATION.md`; restoration requirements: `out/RESTORATION.md`.', 'Naming occurrences and copy commands: `out/NAMING.md`; held operator commands: `out/RUN.md`.', 'Time/disk estimate: `out/SIZING.json`; local usage/cap: `out/BUILD_SIZE.json`.', 'Decisions and defaults: `out/DECISIONS.md`.', '', 'Not checked: actual candidate restore, GPU identity/canary, live Orchard/cloud admission, full inherited archive headers or production return publication.', 'No network, upload, submission, GPU, Git or other agent was used.', 'Request an independent component review; this family cannot yet be approved for launch.']
assert len(lines)<=40;event.write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status='NOT_READY',unit_tests=count,mutants=mut['killed'],measured_bytes=size,event=str(event),code_sha256=code['sha256']),indent=2))
