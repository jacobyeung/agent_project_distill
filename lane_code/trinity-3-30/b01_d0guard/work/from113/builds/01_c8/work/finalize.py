from datetime import datetime,timezone
import ast,hashlib,json,time
from pathlib import Path
B=Path(__file__).resolve().parents[1]
def load(p):return json.loads((B/p).read_text())
def sha(p):return hashlib.sha256((B/p).read_bytes()).hexdigest()
now=datetime.now(timezone.utc)
wait=load('out/INPUT_WAIT.json')
started=datetime.strptime(wait['started_utc'][:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
stop=dict(wait,status='ENDED_EARLY_BLOCKED',stopped_utc=now.isoformat(),
    elapsed_seconds=(now-started).total_seconds(),maximum_wait_reached=False,
    reason='The required production interpreter is independently inaccessible in this execution environment; no remaining whole-worker proof can run.',
    monitor_exit_code=130,governor_or_transfer_changed=False)
(B/'out/INPUT_WAIT_STOP.json').write_text(json.dumps(stop,indent=2)+'\n')
package=load('out/PACKAGE_STATUS.json');audit=load('out/PIN_AUDIT.json');cov=load('out/coverage/SUMMARY.json');census=load('out/GUARD_CENSUS.json')
tests={}
for name in ('test_core.py','test_guard.py'):
    t=ast.parse((B/'out/tests'/name).read_text())
    tests[name]=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(t))
value=dict(status='DRAFT_NOT_ADMITTED',code_sha256=sha('out/c8/code_c8.tar'),
    family_sha256=sha('out/c8/FAMILY_C8.json'),diff='out/C8_DIFF_vs_pilot9.patch',diff_sha256=sha('out/C8_DIFF_vs_pilot9.patch'),
    core_tests_passed=tests['test_core.py'],guard_tests_unexecuted=tests['test_guard.py'],
    pin_checks_passed=audit['pass_count'],pin_checks_not_evaluated=audit['not_evaluated'],
    coverage=cov,guard_captures=census['captures'],sealed_refused=len(census['sealed_refused']),
    reviewed_refused=len(census['reviewed_refused']),reviewed_refused_names=census['reviewed_refused'],
    guard_method=census['evidence'],input_wait=stop,open_decisions='out/DECISIONS.md',
    missing_proofs=['production numerical tests','cache-bind reproduction','whole-worker pilot',
                   'whole-worker full','production branch coverage','complete pin/authority admission'])
(B/'out/FINAL_RESULT.json').write_text(json.dumps(value,indent=2)+'\n')
lines=[
 'C8 is DRAFT_NOT_ADMITTED. No whole-worker pass, seal, upload, or launch is claimed.',
 'Code: `out/c8/code_c8.tar`, sha256 `'+value['code_sha256']+'`.',
 'Family: `out/c8/FAMILY_C8.json`, sha256 `'+value['family_sha256']+'`.',
 'Diff: `out/C8_DIFF_vs_pilot9.patch`, sha256 `'+value['diff_sha256']+'`.',
 'Core tests: '+str(value['core_tests_passed'])+' pass under system Python (`out/tests/core.log`); '+str(value['guard_tests_unexecuted'])+' numerical guard tests were not executed (`out/tests/test_guard.py`).',
 'Pilot and full: 0 worker lines executed; production branch coverage is unavailable (`out/coverage/pilot/coverage.json`, `out/coverage/full/coverage.json`).',
 'The conservative inventory has '+str(cov['conservative_unexecuted_lines'])+' source lines not executed by either rehearsal or core tests (`out/coverage/UNEXECUTED.md`, `out/coverage/SUMMARY.json`).',
 'Pins: '+str(audit['pass_count'])+' PASS, '+str(audit['not_evaluated'])+' N/E (`out/PIN_TABLE.md`, `out/PIN_AUDIT.json`).',
 'Independent stdlib census: '+str(census['captures'])+' real captures, '+str(len(census['sealed_refused']))+' sealed refusals, '+str(len(census['reviewed_refused']))+' reviewed refusal: d3/41254810 (`out/GUARD_CENSUS.json`). The production guard wrapper was not executed.',
 'The required Python target is inaccessible here. All streamed completion markers remain absent (`out/INPUT_WAIT_STOP.json`).',
 'The local input monitor ended early; it did not reach its maximum wait. The governor and transfers were untouched (`out/INPUT_WAIT_STOP.json`).',
 'The mask receipt has only a draft producer rebind; cache-bind has not run (`out/MASK_REBIND_STATUS.json`).',
 'The operator must fill code-object generation and md5 after upload; both are PENDING_UPLOAD (`out/PACKAGE_STATUS.json`).',
 'Open defaults and blockers: `out/DECISIONS.md`; required proofs and unvalidated harness limits: `out/DESIGN_RECORD_native_r2_c8_20261115.md`.',
 'No GPU, network, Git, other-agent, official-item, or shared-storage write was performed.',
]
event=B/'events'/(now.strftime('%Y%m%dT%H%MZ')+'_RESULT_final.md')
event.write_text('\n'.join(lines)+'\n')
print(str(event));print(json.dumps({k:v for k,v in value.items() if k in ('status','code_sha256','family_sha256','core_tests_passed','pin_checks_passed')}))
