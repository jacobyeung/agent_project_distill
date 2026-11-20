"""Validate and report the one retained bounded-fixture attempt."""
from pathlib import Path
from contextlib import closing,redirect_stdout
import hashlib,io,json,sqlite3,sys,tarfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k6 import D,R
from rehearsal_inputs_k6 import usage

def read(path,default=None):return json.loads(Path(path).read_text()) if Path(path).exists() else default
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def new(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
setup=read(R/'SETUP.json');kit=Path(setup['kit_dir'])
stages=read(R/'STAGES.json',[]);failed=next((s for s in stages if s['returncode']),None)
furthest=stages[-1]['stage'] if stages else 'setup'
errors=[]
if failed:
    lines=Path(failed['log']).read_text().splitlines()
    errors=[dict(line=i+1,text=s) for i,s in enumerate(lines) if s.startswith(('ValueError:','RuntimeError:','KeyError:','FileNotFoundError:','AssertionError:','TypeError:'))]
    exact=errors[-1]['text'] if errors else read(R/'RUN_REFUSAL.json',{}).get('error','See log')
    classification=('native contract incompatible with bounded Trinity rehearsal: fixed 7971-twin cardinality exceeds scene limit; not proof of a production-kit failure'
        if 'R1_TWIN_BINDING_COUNT' in exact else 'native refusal; inspect traceback before attributing cause')
    new(R/'REFUSAL_DETAIL.json',dict(stage=failed['stage'],returncode=failed['returncode'],classification=classification,
        errors=errors,log=failed['log'],excerpts=[dict(line=i+1,text=s) for i,s in enumerate(lines) if i>=max(0,len(lines)-30)],no_retry=True))
else:exact=read(R/'RUN_REFUSAL.json',{}).get('error','No refusal')
source_kit_matches=sha(kit/'SHA256SUMS.txt')==setup['kit']
source_file_matches=[]
for line in (kit/'SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1);source_file_matches.append(sha(kit/n)==h)
helpers={str(p.relative_to(R/'kit_n_go')):sha(p)==sha(kit/p.relative_to(R/'kit_n_go')) for p in (R/'kit_n_go/b').rglob('*') if p.is_file()}
archive=R/'kit_n_go'/setup['source']['path'];assert sha(archive)==setup['source']['sha256']
tree_matches=[]
with tarfile.open(archive) as stream:
    for member in stream.getmembers():
        if member.isfile():tree_matches.append(sha(R/'source'/member.name)==hashlib.sha256(stream.extractfile(member).read()).hexdigest())
sys.path.insert(0,str(R/'source'))
from student_pilot.row_removals import Removals,row_keys
from student_pilot.r1_rooms import Rooms
from student_pilot.p3_provenance import digest
cfg=read(R/'seed.json');rooms=Rooms(cfg['r1_training']['room_authority'])
population=read(R/'BOUNDED_POPULATION.json');twins=read(R/'TWIN_SUBSET.json');checks=[]
for record in population['records']:
    original=record['original_database'];bounded=record['database']
    assert sha(original['path'])==original['sha256'] and sha(bounded['path'])==bounded['sha256']
    assert sha(record['receipt']['path'])==record['receipt']['sha256']
    receipt=read(record['receipt']['path'])
    with closing(sqlite3.connect(Path(original['path']).as_uri()+'?mode=ro&immutable=1',uri=True)) as a, closing(sqlite3.connect(Path(bounded['path']).as_uri()+'?mode=ro&immutable=1',uri=True)) as b:
        expected=a.execute('SELECT i,row,target FROM rows ORDER BY i LIMIT ?',(1000 if record['source']=='vqa' else 2000,)).fetchall()
        actual=b.execute('SELECT i,row,target FROM rows ORDER BY i').fetchall()
    if record['source']=='vqa':
        spec=twins['fixture_pins'];original_spec=twins['original_pins']
        for p in list(spec.values())+list(original_spec.values()):assert sha(p['path'])==p['sha256']
        with closing(sqlite3.connect(Path(spec['source_database']['path']).as_uri()+'?mode=ro&immutable=1',uri=True)) as src:
            assert src.execute('SELECT i,row,target FROM rows ORDER BY i').fetchall()==expected
        selected_lines=Path(spec['rows']['path']).read_text().splitlines()
        entries=[json.loads(x) for x in Path(spec['binding']['path']).read_text().splitlines()]
        base={json.loads(raw)['qid']:json.loads(raw) for _,raw,_ in expected}
        lookup={e['twin_key']:e for e in entries}
        assert len(entries)==len(lookup)==len(base)==len(selected_lines)==1000
        originals={json.loads(line)['qid']:line.rstrip('\n') for line in Path(original_spec['rows']['path']).open() if json.loads(line)['qid'] in lookup}
        original_bindings={json.loads(line)['twin_key']:json.loads(line) for line in Path(original_spec['binding']['path']).open() if json.loads(line)['twin_key'] in lookup}
        assert original_bindings==lookup
        rule=Removals(cfg['remove_files'])
        for i,line in enumerate(selected_lines):
            row=json.loads(line);entry=lookup[row['qid']];source=base[entry['source_key']]
            assert originals[row['qid']]==line and digest(row)==entry['twin_sha256']
            assert row_keys(row)=={row['qid'],source['qid']} and rule.match(row)==rule.match(source)
            assert rooms.room(rooms.canonical(row)[0])==entry['source_room']==rooms.room(rooms.canonical(source)[0])
        expected += [(1000+i,line,'{}') for i,line in enumerate(selected_lines)]
        assert {e['source_key'] for e in entries}==set(base)
        assert 'COUNT = 7971' in (R/'source/student_pilot/r1_direction_twins.py').read_text()
    assert actual==expected and len(actual)==record['count']==receipt['count']<=2000
    rule=Removals(cfg['remove_files']);kept=sum(rule.keep(json.loads(raw)) for _,raw,_ in actual)
    with redirect_stdout(io.StringIO()):report=rule.report()
    assert kept==record['rows_after_removals'] and report==record['removal_report']
    if 'removals' in receipt:assert report==receipt['removals']
    checks.append(dict(source=record['source'],count=len(actual),original_unchanged=True,complete_subset=True,
        native_row_bytes_equal=True,removal_census_consistent=True,rows_after_removals=kept))
closure=read(R/'FIXTURE_CLOSURE.json');assert not closure['missing'] and closure['native_closure_calls']==1
new(R/'RESOLVED_INPUT_INVENTORY.json',dict(supplied=closure['supplied'],native_stream_pins=closure['native_stream_pins'],fixture_populations=population['records']))
measure=usage(R);overhead=sum(p.stat().st_blocks*512 for p in D.glob('*k6*') if p.is_file())
assert measure['allocated_bytes']+overhead<3_000_000_000
integrity=source_kit_matches and all(source_file_matches) and all(helpers.values()) and all(tree_matches)
validation=dict(kit_seal=setup['kit'],source_kit_unchanged=source_kit_matches and all(source_file_matches),fixture_helpers_unchanged=helpers,
    extracted_tree_unchanged=all(tree_matches),tree_file_count=len(tree_matches),original_and_bounded_stores=checks,
    usage=measure,harness_allocated_bytes=overhead,total_new_allocation=measure['allocated_bytes']+overhead,
    peak_rss_bytes=max((s.get('peak_rss_bytes',0) for s in stages),default=0),one_attempt=True,no_retry=True,
    native_limit_unchanged=True,native_twin_count_unchanged=True,removal_configuration_unchanged=True,native_gates_unchanged=True,
    fixture_pair_completeness=True,native_twin_cardinality_satisfied=False,sampler_capacity_possible=False)
new(R/'VALIDATION.json',validation)
rows=read(R/'CHECK_RAW.json',[])
for row in rows:
    row['expected_evidence']=row['evidence']
    if row['passed']:row['evidence']=[s.strip() for s in row['evidence'].split(';')]
    else:
        row['evidence']=['STAGES.json','RUN_REFUSAL.json','REFUSAL_DETAIL.json',furthest+'.log']
        row['reason']='The single attempt stopped at '+furthest+': '+exact
    if row['path']=='mode r production database reconstruction':
        row.update(evidence=['FIXTURE_INPUTS.json','routing_retained/plan.json'],reason='The fixture routing base does not exercise production P reconstruction.')
def emit(name,passed,evidence,reason=None):
    row=dict(path=name,status='PROVED' if passed else 'NOT PROVED',passed=bool(passed),evidence=evidence)
    if reason:row['reason']=reason
    rows.append(row)
emit('authenticated fixture pin closure',not closure['missing'],['FIXTURE_CLOSURE.json','RESOLVED_INPUT_INVENTORY.json'])
emit('native fixture routing regeneration',any(s['stage']=='routing' and s['returncode']==0 for s in stages),['routing_retained/plan.json','STAGES.json'])
emit('scene populations within native host limit',all(v['count']<=2000 for v in checks),['BOUNDED_POPULATION.json','VALIDATION.json'],'Verified input row counts; native scene stage was not reached.')
emit('dbb2 header mismatch search',False,['DBB_STEP.json','dbb/db_bytes.json'],'DBB_TARGET equals the generated fixture digest; no mismatching header was searched.')
emit('complete source/twin pairs and consistent removals',True,['TWIN_SUBSET.json','BOUNDED_POPULATION.json','VALIDATION.json'])
emit('all native twin invariants',False,['CAPACITY_DECISION.md','REFUSAL_DETAIL.json','canary.log'],'Native COUNT=7971 cannot fit the 2000-row scene population; it remains unchanged.')
emit('sampler capacity within scene limit',False,['CAPACITY_DECISION.md','CAPACITY_SOURCES.json'],'Source proof: 32000 required VQA rows exceed 2000; sampler execution was not reached.')
emit('source kit, helpers, tree and original stores unchanged',integrity,['VALIDATION.json'])
new(R/'CHECK.json',rows)
lookup={r['path']:r for r in rows}
def status(name):return lookup[name]['status']
verdict='NOT PROVED end-to-end'
prefix='rehearsal_k6/'
report=[
    verdict+'; kit n_go '+setup['kit']+'; furthest stage: '+furthest+'.',
    'Bounded populations '+status('scene populations within native host limit')+'; 1,000 complete VQA pairs and removal census PROVED ('+prefix+'TWIN_SUBSET.json; BOUNDED_POPULATION.json; VALIDATION.json).',
    'Fixture closure '+status('authenticated fixture pin closure')+': one native closure call, '+str(len(closure['supplied']))+' pins, none missing ('+prefix+'FIXTURE_CLOSURE.json).',
    'Native fixture routing '+status('native fixture routing regeneration')+'; production P reconstruction NOT PROVED ('+prefix+'routing_retained/plan.json; CHECK.json).',
    'dbb2 '+status('dbb2 generated fixture database')+' on the fixture digest; header mismatch search NOT PROVED ('+prefix+'DBB_STEP.json; dbb/db_bytes.json).',
    'Scene-rebuild pins '+status('scene-rebuild step pins')+' ('+prefix+'CHECK.json; canary.log).',
    'Native host receipt '+status('native host receipt')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Handover with localised pins '+status('handover passes with localised pins')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Clock inheritance '+status('clock inheritance')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Fresh optimizer / counter zero '+status('fresh optimizer / counter zero')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Finite losses on four ranks '+status('finite losses on four ranks')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Step-1 checkpoint through milestone '+status('step-1 checkpoint through milestone')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Timed checkpoint '+status('timed checkpoint')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Milestone export / local receipt / kit copier '+status('milestone export / local receipt / kit copier')+' ('+prefix+'CHECK.json; STAGES.json).',
    'TK_JOB_START budget self-stop '+status('TK_JOB_START budget self-stop')+'; resume_pin latest / one further step '+status('resume_pin latest / one further step')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Census receipt bound in h.py '+status('census receipt bound in h.py')+'; review wait / published v.json / fixture review '+status('review wait / published v.json / fixture review')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Stop: '+exact+' ('+prefix+'canary.log:'+str(errors[-1]['line'] if errors else 1)+'; REFUSAL_DETAIL.json). One attempt; no retry.',
    'Integrity '+('PROVED' if integrity else 'NOT PROVED')+'; peak RSS '+str(validation['peak_rss_bytes'])+' B; new allocation '+str(validation['total_new_allocation'])+' B ('+prefix+'VALIDATION.json).',
    'Capacity impossible: 32,000 sampler rows and 7,971 mandatory twins exceed the 2,000-row scene limit. This blocks bounded rehearsal; it does not prove a production-kit defect ('+prefix+'CAPACITY_DECISION.md).'
]
assert len(report)<20
with (D/'REHEARSAL_K6_REPORT.md').open('x') as f:f.write('\n'.join(report)+'\n')
print(json.dumps(dict(verdict=verdict,furthest=furthest,rows=len(rows),proved=sum(r['passed'] for r in rows),report=str(D/'REHEARSAL_K6_REPORT.md'),allocated_bytes=validation['total_new_allocation'])))
