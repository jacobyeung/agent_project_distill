"""Validate and seal the small report build."""
from pathlib import Path
import ast,difflib,json,re,sys,time
B=Path(__file__).resolve().parents[1];S=B.parent/'03_vsti_c'
sys.path.append(str(B/'code'))
from adapter import dump,load,pin,sha
import engine
log=B/'work/tests_d_final.log';assert re.search(r'Ran 59 tests.*\n\nOK\s*$',log.read_text(),re.S)
legacy=load(B/'out/LEGACY_TESTS.json');extra=load(B/'out/LEGACY_EXTRA.json')
assert legacy['run']==28 and not legacy['failures'] and not legacy['errors'] and extra['passed'] and extra['run']==2
inventory=[]
for p in sorted((B/'tests').glob('test_*.py')):
    inventory.extend(dict(file=str(p.relative_to(B)),test=n.name) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))
assert len(inventory)==59
dump(B/'out/TESTS.json',dict(passed=True,kit_run=59,inherited_run=30,kit_log=pin(log),inherited=pin(B/'out/LEGACY_TESTS.json'),extra=pin(B/'out/LEGACY_EXTRA.json'),inventory=inventory,source_pins=engine.source_pins(),unexecuted_inherited=[r for r in legacy['inventory'] if not r['executed'] and r['test'] not in extra['tests']]))
cli=load(B/'work/cli_d_final/RESULT.json');rh=load(B/'out/rehearsal/RESULT.json')
assert cli['passed'] and rh['passed'] and cli['items']==rh['items']==9 and cli['captures']==rh['captures']==2
for name in ('REPORT.json','REPORT.md'):(B/name).write_bytes((B/'work/cli_d_final/report'/name).read_bytes())
report=load(B/'REPORT.json');assert report['primary']['score'] is None and report['primary']['incomplete_subtasks']
assert all(m['score'] is not None and m['scene_interval'] is not None for m in report['per_type'].values() if m['items'])
assert report['refusal_note'] in (B/'REPORT.md').read_text()
package=load(B/'out/PACKAGE.json');family=load(B/'out/FAMILY.json')
for k in ('code','reference','family'):assert sha(package[k]['path'])==package[k]['sha256']
assert family['code_sources']==engine.source_pins()
assert sha(S/'out/c.tar')=='dc40cf60212a34c2789a9821bb558e0592074c4d81b0bb1239e55c238f093eaa'
assert sha(S/'out/FAMILY.json')=='3cf68794ee715bdad6936486ce64edc72c40b08165f9e0763c126aaa685eecf6'
assert sha(S/'out/d.tar')==package['reference']['sha256']=='9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f'
coverage=load(B/'out/UNEXECUTED.json');assert all(sha(B/f['file'])==f['sha256'] for f in coverage['files'])
review=load(B/'out/REVIEW_ITEMS.json');review['S5']=dict(fix='Observed-item scores and scene intervals on PARTIAL type/subtask rows; primary requires all five complete subtasks.',tests=[r['test'] for r in inventory if r['file']=='tests/test_v1d.py'])
dump(B/'out/REVIEW_ITEMS.json',review)
files=[p.relative_to(B) for folder in ('code','tests') for p in (B/folder).rglob('*') if p.is_file()]
files += [Path(p) for p in ('out/DECISIONS.md','out/LEGALITY.md','out/RUN_TRINITY.md','out/RUN_ORCHARD.md','out/SIZING.md','out/ASSETS.json','out/rehearsal/RUNBOOK.md','work/py','work/ns_op.py','work/package_d.py','work/finalize_d.py','REPORT.md')]
patch=[];stats=[]
for rel in sorted(files):
    p=B/rel;old=S/rel
    if old.is_file() and p.read_bytes()==old.read_bytes():continue
    lines=list(difflib.unified_diff(old.read_text().splitlines(True) if old.is_file() else [],p.read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
    patch.extend(lines);stats.append(dict(file=str(rel),added=sum(x.startswith('+') and not x.startswith('+++') for x in lines),removed=sum(x.startswith('-') and not x.startswith('---') for x in lines)))
(B/'out/DIFF_vs_V1c.patch').write_text(''.join(patch))
summary=dict(files=stats,added=sum(x['added'] for x in stats),removed=sum(x['removed'] for x in stats),production_changed=['code/report.py'],scope='Sources, tests, report prose, operator paths and packaging helpers; generated JSON evidence and binary archives are pinned separately.')
dump(B/'out/DIFF_STATS.json',summary)
descriptions={'code/report.py':'Reports observed-item scores and intervals for partial rows, gates the primary, and explains refusal recovery above the existing refusal results.','tests/test_v1c.py':'Updates only the assertions superseded by the partial-score ruling.','tests/test_v1d.py':'Checks partial and empty rows, grouped estimates, scene bootstrap intervals, primary gating and refusal wording.','out/LEGALITY.md':'States the reviewer training-row finding and partial-report contract.','out/DECISIONS.md':'Records the observed-item scoring default, unchanged reference archive and review attribution.','REPORT.md':'Shows the regenerated CPU sample report with partial scores and the refusal explanation.'}
(B/'out/DIFF_FILES.md').write_text(summary['scope']+'\n\n'+'\n'.join('- `'+r['file']+'`: '+descriptions.get(r['file'],'Makes the local build, package or operator instructions use the V1d artifacts.') for r in stats)+'\n')
footprint=sum(p.stat().st_size for p in B.rglob('*') if p.is_file() and not any(n in p.relative_to(B).parts for n in ('.git','.agents','.aws','.codex')))
assert footprint<2_000_000_000
not_checked=['GPU decode and real frozen-weight tower','Actual checkpoint heads and historical GPU equality','Orchard namespace, transfers and submission','Full-frame adaptation and release-video checks were inherited from V1c, not rerun','The reviewer training-row audit was not rerun','Own selected-frame reference remains unavailable']
value=dict(status='built and CPU-verified',launch_ready=False,package=package,tests=pin(B/'out/TESTS.json'),rehearsal=pin(B/'out/rehearsal/RESULT.json'),cli_rehearsal=pin(B/'work/cli_d_final/RESULT.json'),report=pin(B/'REPORT.json'),patch=pin(B/'out/DIFF_vs_V1c.patch'),diff=summary,coverage=dict(source=pin(B/'out/UNEXECUTED.json'),counts=coverage['counts'],authored_counts=coverage['authored_counts']),reference_byte_identical=True,v1c_archive_hashes_unchanged=True,footprint_bytes_before_final_receipts=footprint,limit_bytes=2_000_000_000,not_checked=not_checked,operator_command='cd '+str(B)+' && ./work/py out/rehearsal/run_rehearsal.py --fixture-tower')
dump(B/'out/FINAL_RESULT.json',value)
(B/'STATUS.md').write_text('V1d is built and CPU-verified. All 59 kit and 30 inherited tests pass. Both CPU sample paths pass with 9 items in 2 scenes and synthetic tower/heads/logits. The reference archive is unchanged. See out/FINAL_RESULT.json for hashes, namespace outcome and unchecked work.\n')
dump(B/'STATUS.json',dict(status='complete',result=pin(B/'out/FINAL_RESULT.json')))
lines=[
'RESULT: V1d built and CPU-verified; no job submitted. Evidence: out/FINAL_RESULT.json.',
'Partial types/subtasks show counts, observed-item scores, scene intervals and PARTIAL: code/report.py; REPORT.md.',
'The primary requires all five complete subtasks; otherwise it lists incomplete subtasks: REPORT.json; REPORT.md.',
'Refusal recovery wording attributes the 0/165 training-row finding to the reviewer: out/LEGALITY.md; REPORT.md.',
'Per-type refusal answer distributions and observed-item scores are preserved: REPORT.json; REPORT.md.',
'Tests: 59 kit and 30 inherited pass: out/TESTS.json; work/tests_d_final.log.',
'CPU library and CLI sample paths: 9 items, 2 scenes; synthetic tower/heads/logits: out/rehearsal/RESULT.json; work/cli_d_final/RESULT.json.',
'Namespace outcome: '+rh['namespace']+'; out/rehearsal/NAMESPACE.json. Operator command: out/rehearsal/RUNBOOK.md.',
'Code SHA256 '+package['code']['sha256']+': out/c.tar.',
'Reference SHA256 '+package['reference']['sha256']+': out/d.tar; byte-identical to V1c.',
'Family SHA256 '+package['family']['sha256']+': out/FAMILY.json.',
'Only production report.py changed; archive members and source pins verified: out/PACKAGE_VERIFY.json.',
'Diff +'+str(summary['added'])+'/-'+str(summary['removed'])+': out/DIFF_vs_V1c.patch; out/DIFF_STATS.json.',
'Coverage counts '+json.dumps(coverage['counts'],sort_keys=True)+': out/UNEXECUTED.json.',
'Footprint '+str(footprint)+' bytes, below 2 GB: out/FINAL_RESULT.json.',
'GPU/real tower, checkpoint/proof, Orchard, transfers, full-frame/release reruns and reviewer-audit rerun were not checked: out/FINAL_RESULT.json.',
'Defaults: out/DECISIONS.md. V1c remains unchanged: out/FINAL_RESULT.json.'
]
assert len(lines)<=20
event=B/'events'/(time.strftime('%Y%m%dT%H%MZ',time.gmtime())+'_RESULT_final.md');event.write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(event=str(event),footprint=footprint,package=package,coverage=coverage['counts']),indent=2))
