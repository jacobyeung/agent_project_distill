"""Write final receipts only after tests, coverage and archives agree."""
from pathlib import Path
import ast,hashlib,json,re,sys,tarfile,time
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
import engine

log=B/'work/tests_sealed.log'
assert re.search(r'Ran 53 tests.*\n\nOK\s*$',log.read_text(),re.S)
inv=[]
for p in sorted((B/'tests').glob('test_*.py')):
    inv += [dict(file=str(p.relative_to(B)),test=n.name) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
assert len(inv)==53
legacy=load(B/'out/LEGACY_TESTS.json');extra=load(B/'out/LEGACY_EXTRA.json')
assert not legacy['failures'] and not legacy['errors'] and extra['passed']
dump(B/'out/TESTS.json',dict(passed=True,kit_run=53,inherited_run=legacy['run']+extra['run'],kit_log=pin(log),
    inherited=pin(B/'out/LEGACY_TESTS.json'),extra=pin(B/'out/LEGACY_EXTRA.json'),inventory=inv,source_pins=engine.source_pins(),
    unexecuted_inherited=[r for r in legacy['inventory'] if not r['executed'] and r['test'] not in extra['tests']]))
pkg=load(B/'out/PACKAGE.json');family=load(checked(pkg['family']))
assert family['code_sources']==engine.source_pins()
for key,root in [('code',B/'code'),('reference',B/'work/reference')]:
    with tarfile.open(checked(pkg[key])) as archive:
        assert {m.name for m in archive if m.isfile()}=={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
        for m in archive:
            if m.isfile():assert hashlib.sha256(archive.extractfile(m).read()).hexdigest()==sha(root/m.name)
dump(B/'out/PACKAGE_VERIFY.json',dict(passed=True,package=pin(B/'out/PACKAGE.json'),source_pins_equal=True,tar_members_equal=True,archive_members_verified=True))
assert sha(B.parent/'02_vsti_b/out/c.tar')=='7895f182da0ea899f2c046378d12755a5da1ed13da745a172572795838afa17d'
assert sha(B.parent/'02_vsti_b/out/FAMILY.json')=='e90df4e0dba6554d665360e7eb71a07726efa1ed9974ac90e12ac2a1dc2bfcd8'

cli=load(B/'work/cli_sealed/RESULT.json');assert cli['passed'] and cli['items']==9 and cli['captures']==2
receipt=dict(cli,namespace='denied by sandbox; operator command provided',namespace_receipt=pin(B/'out/rehearsal/NAMESPACE.json'),
    tower='pinned synthetic raw tower; real frozen-weight tower not exercised',checkpoint_prefill='synthetic depth and gravity; real preparation and guard',decode='synthetic logits through production decoder and replay')
dump(B/'out/rehearsal/RESULT.json',receipt)
for name in ('REPORT.md','REPORT.json'):(B/name).write_bytes((B/'work/cli_sealed/report'/name).read_bytes())
for name in ('RUN_TRINITY.md',):
    p=B/'out'/name;p.write_text(p.read_text().replace('work/cli_delivery/RESULT.json','work/cli_sealed/RESULT.json'))
coverage=load(B/'out/UNEXECUTED.json');assert coverage['passed'] and coverage['authored_counts'].get('UNEXPLAINED',0)==0
assert all(sha(B/f['file'])==f['sha256'] for f in coverage['files'])
scores=load(B/'out/SCORER_CHECK.json');assert [x['kit_primary_pct'] for x in scores.values()]==[66.95,68.71]
assert all(x['items']==450 and not x['mismatches'] for x in scores.values())
full=load(B/'out/FULL_ADAPT.json');assert full['passed'] and full['captures']==311 and full['pngs_verified']==9952
release=load(B/'out/RELEASE_CHECK.json');assert release['status']=='complete' and release['compared_frames']==160
index=load(B/'out/INDEX_CHECK.json')
review={
 'F1':dict(fix='Strict authority parser/metrics; fuzzy diagnostic retained; strict canary recomputation.',tests=['test_comparators','test_f1_strict_answer_forms','test_f1_historical_answer_forms','test_f1_canary_strict_recomputation'],evidence=['out/SCORER_CHECK.json','out/HISTORICAL_FORMS.json']),
 'F2':dict(fix='Shared packet path and /dev/null batch output.',tests=['test_f2_shared_packet','test_primary_packet']),
 'F3':dict(fix='Staged bwrap for both allocation entries; explicit Trinity host fallback.',tests=['test_f3_s1_staged_namespace','test_namespace_shared_memory']),
 'S1':dict(fix='Preserve Slurm CUDA_VISIBLE_DEVICES.',tests=['test_f3_s1_staged_namespace']),
 'S2':dict(fix='Failed proof receipt continues to read; headline states failed/diverged.',tests=['test_s2_proof_failure_continues','test_s4_geometry_scope','test_resume_disjoint_and_pin_rejection']),
 'S3':dict(fix='Exclude refused independent-response positions with reasons; retain full-token and prompt/head checks.',tests=['test_s3_parity_refusal_exclusion','test_inherited_gate_and_failure'],evidence=['out/PARITY_POLICY_CPU.json']),
 'S4':dict(fix='Only geometry-dependent camera items auto-zero; other items decode with all calls refused and own-geometry fallback disabled.',tests=['test_s4_geometry_scope','test_refused_geometry_is_scored'],evidence=['out/GEOMETRY_SCOPE_CPU.json']),
 'S5':dict(fix='Withhold incomplete type/subtask/paired/scripted scores and intervals.',tests=['test_s5_complete_and_incomplete_types','test_s4_geometry_scope']),
 'S6':dict(fix='Primary line names refused subtasks and counts plus proof status and auto-zero counts.',tests=['test_s4_geometry_scope']),
 'S7':dict(fix='Separate item cutoff and kill; 600-second reserve; account for earlier sealed GPU cap.',tests=['test_s7_distinct_deadlines','test_deadline_and_rates']),
 'S8':dict(fix='Assert full video frame count; compare all scene indices when own list is supplied.',tests=['test_s8_frame_count_rejected','test_s8_index_comparison','test_synthetic_video'],evidence=['out/FULL_ADAPT.json','out/RELEASE_CHECK.json','out/INDEX_CHECK.json'],pending='Own selected-frame list absent; command in out/FRAME_CHECKS.md.')}
dump(B/'out/REVIEW_ITEMS.json',review)
footprint=sum(p.stat().st_size for p in B.rglob('*') if p.is_file() and not any(n in p.relative_to(B).parts for n in ('.git','.agents','.aws','.codex')))
assert footprint<6_000_000_000
not_checked=['GPU tower, checkpoint restoration, parity and greedy decoding','Historical GPU proof and prepared-geometry equality','Orchard staged bwrap/CUDA and exact production namespace','Remote uploads, submission, resume and return timing','Own selected-frame list comparison: input absent']
result=dict(status='built and CPU-verified; operator execution and index reference pending',launch_ready=False,
    package=pkg,tests=pin(B/'out/TESTS.json'),review=pin(B/'out/REVIEW_ITEMS.json'),rehearsal=pin(B/'out/rehearsal/RESULT.json'),full_adaptation=pin(B/'out/FULL_ADAPT.json'),
    scorer=pin(B/'out/SCORER_CHECK.json'),historical_forms=pin(B/'out/HISTORICAL_FORMS.json'),release_check=pin(B/'out/RELEASE_CHECK.json'),index_check=pin(B/'out/INDEX_CHECK.json'),
    coverage=dict(source=pin(B/'out/UNEXECUTED.json'),counts=coverage['counts'],authored_unexplained=0,inherited_unexplained=coverage['counts'].get('UNEXPLAINED',0),unreachable_lines=sum(r['count'] for r in coverage['unreachable'])),
    decisions=pin(B/'out/DECISIONS.md'),footprint_bytes_before_final_receipts=footprint,limit_bytes=6_000_000_000,not_checked=not_checked)
dump(B/'out/FINAL_RESULT.json',result)
(B/'STATUS.md').write_text('V1c is built and CPU-verified. All 53 kit and 30 inherited tests pass; both sample job and full-frame adaptation pass. Package pins and review evidence are in out/FINAL_RESULT.json. The release-video check finds pixel differences. The selected-frame reference list, GPU/Orchard execution and upload receipts remain pending.\n')
stats=pkg['diff'];lines=[
 'RESULT: V1c built and CPU-verified; no job submitted. Evidence: out/FINAL_RESULT.json.',
 'V1b archive and family hashes remain unchanged: out/REFRESH.json; work/finalize_c.py.',
 'F1: strict parser/official metrics; kit matches all 900 rows, primaries 66.95/68.71: out/SCORER_CHECK.json; tests/test_v1c.py.',
 'F1 forms: 146/148 distance and 34/36 room tagged answers checked; zero mismatches: out/HISTORICAL_FORMS.json.',
 'F2: shared project packet, /dev/null batch output, no foreign /tmp in a.sh; test_f2_shared_packet: out/TESTS.json.',
 'F3: staged bwrap; explicit host fallback only for Trinity; test_f3_s1_staged_namespace: out/TESTS.json.',
 'S1: allocation CUDA value passes through; test_f3_s1_staged_namespace: out/TESTS.json.',
 'S2: proof exceptions become failed receipts and read continues; test_s2_proof_failure_continues: out/TESTS.json.',
 'S3: refused parity positions excluded with reasons; test_s3_parity_refusal_exclusion: out/PARITY_POLICY_CPU.json.',
 'S4: dependent camera items auto-zero; others decode with all calls refused; test_s4_geometry_scope: out/GEOMETRY_SCOPE_CPU.json.',
 'S5: incomplete rows have no score/interval; test_s5_complete_and_incomplete_types: out/TESTS.json.',
 'S6: headline names refused subtasks/counts and proof status; test_s4_geometry_scope: out/GEOMETRY_SCOPE_CPU.json.',
 'S7: distinct item cutoff/kill, 600-second reserve and earlier cap handling; test_s7_distinct_deadlines: out/TESTS.json.',
 'S8: full frame-count assertion and index comparison tests pass: out/TESTS.json; code/pixels.py; code/indices.py.',
 'S8 pending: own selected-frame list absent; 311-scene command: out/FRAME_CHECKS.md; out/INDEX_CHECK.json.',
 'Release pixels: full counts pass; 0/160 selected frames byte-identical: out/RELEASE_CHECK.json.',
 'Refusal wording is the runtime\'s recoverable error format (trace 3.13): out/LEGALITY.md; REPORT.md.',
 'Tests: 53 kit + 30 inherited pass; unexecuted inherited tests have reasons: out/TESTS.json.',
 'CPU job path: 9 sample items, 2 scenes, synthetic tower/heads/logits; passed: work/cli_sealed/RESULT.json.',
 'Full adaptation: 311 scenes, 9,952 PNG SHA checks, 450 items and fixed canary; passed: out/FULL_ADAPT.json.',
 'Namespace denied by sandbox; operator command: out/rehearsal/RUNBOOK.md; out/rehearsal/NAMESPACE.json.',
 'Unexplained authored reachable lines: 0; inherited: '+str(coverage['counts'].get('UNEXPLAINED',0))+': out/UNEXECUTED.json.',
 'Unexecuted classes: '+json.dumps(coverage['counts'],sort_keys=True)+': out/UNEXECUTED.json.',
 'Code SHA256 '+pkg['code']['sha256']+': out/c.tar; out/PACKAGE_VERIFY.json.',
 'Reference SHA256 '+pkg['reference']['sha256']+': out/d.tar; out/PACKAGE_VERIFY.json.',
 'Family SHA256 '+pkg['family']['sha256']+': out/FAMILY.json; out/PACKAGE.json.',
 'Diff V1b +'+str(stats['V1b']['added'])+'/-'+str(stats['V1b']['removed'])+'; C8r +'+str(stats['C8R']['added'])+'/-'+str(stats['C8R']['removed'])+': out/DIFF_STATS.json.',
 'Options/defaults and operator commands: out/DECISIONS.md; out/RUN_ORCHARD.md; out/RUN_TRINITY.md; out/SIZING.md.',
 'GPU proof/decoding, actual Orchard namespace, transfers and return timing were not checked: out/FINAL_RESULT.json.',
 'No network, SSH, Git, GPU, agent delegation, external write or submission ran.'
 ]
assert len(lines)<=40
event=B/'events'/(time.strftime('%Y%m%dT%H%MZ',time.gmtime())+'_RESULT_final.md')
event.write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(event=str(event),code=pkg['code']['sha256'],family=pkg['family']['sha256'],footprint=footprint,coverage=result['coverage']['counts'])))
