"""Validate retained evidence after the sole run; do not execute another stage."""
from pathlib import Path
import hashlib,json,sys,tarfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k4 import D,R
from rehearsal_inputs_k4 import usage

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def new(p,value):
    with Path(p).open('x') as f:json.dump(value,f,indent=2);f.write('\n')

setup=read(R/'SETUP.json');kit=Path(setup['kit_dir'])
assert sha(kit/'SHA256SUMS.txt')==setup['kit']
for line in (kit/'SHA256SUMS.txt').read_text().splitlines():
    h,name=line.split('  ',1);assert sha(kit/name)==h,name
fixture_kit=R/'kit_n_go'
unchanged_helpers=[]
for p in (kit/'b').rglob('*'):
    if p.is_file():
        rel=p.relative_to(kit);assert sha(p)==sha(fixture_kit/rel),str(rel)
        unchanged_helpers.append(str(rel))
source=setup['source'];archive=kit/source['path'];assert sha(archive)==source['sha256']
source_count=0
with tarfile.open(archive) as t:
    for member in t.getmembers():
        if member.isfile():
            expected=hashlib.sha256(t.extractfile(member).read()).hexdigest()
            assert sha(R/'source'/member.name)==expected,member.name
            source_count+=1
layout=read(R/'INPUT_LAYOUT.json');stores={}
for h,item in layout['stores'].items():
    p=Path(item['path']);assert sha(p)==h
    a=p.stat();b=(R/'routing_retained/q/u'/h).stat()
    assert (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino)
    stores[h]=dict(unchanged=True,hardlinked=True,bytes=a.st_size)
closure=read(R/'FIXTURE_CLOSURE.json');assert not closure['missing']
stages=read(R/'STAGES.json')
assert [(s['stage'],s['returncode']) for s in stages]==[('routing',0),('dbb2',0),('canary',1)]
sc=read(R/'p2/i/sc.json');camera=sc['spec']['sources']['camera']
error='Local metadata slices must contain at most 2000 rows per family'
assert error in (R/'canary.log').read_text()
blocked=dict(stage='canary/sc.bind -> r2_scene_bindings.rebuild',error=error,
             source='camera',population=camera['rows'],count=camera['count'],
             reason='The nested sc.py process runs on trinity-1-18 and does not inherit the parent in-memory fixture hostname boundary; native decoded() refuses row 2001.',
             production_bytes_missing=False,no_retry=True)
new(R/'SCENE_REFUSAL_DETAIL.json',blocked)
measure=usage(R)
scripts=list(D.glob('*k4*'))
overhead=sum(p.stat().st_blocks*512 for p in scripts if p.is_file())
assert measure['allocated_bytes']+overhead<3_000_000_000
new(R/'VALIDATION.json',dict(kit_seal=setup['kit'],source_kit_verified=True,
    fixture_helpers_unchanged=unchanged_helpers,extracted_source_files_unchanged=source_count,
    fixture_stores=stores,usage=measure,harness_allocated_bytes=overhead,
    peak_rss_bytes=max(s['peak_rss_bytes'] for s in stages),
    planner_closure_calls=closure['native_closure_calls'],supplied_pin_count=len(closure['supplied']),
    native_stream_pin_count=len(closure['native_stream_pins']),stages=stages,
    limitations=['No training or host admission was reached.','Production P database reconstruction is not exercised by the synthetic routing_base.',
                 'The unchanged dbb2 helper uses DBB_TARGET equal to the fixture database digest; its brute-force mismatch branch is not exercised.']))
resolved=read(R/'r2.json')['_resolved']
new(R/'RESOLVED_INPUT_INVENTORY.json',dict(supplied=closure['supplied'],
    small_files=resolved['small_files'],receipt=resolved['receipt'],payload_parts=resolved['parts'],
    native_plan='routing_retained/plan.json',scene_inputs='p2/i/sc.json'))
rows=read(R/'CHECK.json');new(R/'CHECK_INITIAL.json',rows)
for row in rows:
    row['expected_evidence']=row['evidence']
    if not row['passed']:
        row['evidence']=['STAGES.json','RUN_REFUSAL.json','SCENE_REFUSAL_DETAIL.json','canary.log']
        row['reason']='Not reached: native scene rebuild refused before canary host admission.'
    else:row['evidence']=['DBB_STEP.json','dbb/db_bytes.json','dbb2.log']
    if row['path']=='mode r production database reconstruction':
        row['evidence']=['FIXTURE_INPUTS.json','routing_retained/plan.json']
        row['reason']='Synthetic routing_base does not enter the production-specific P reconstruction branch.'
rows.extend([
    dict(path='authenticated fixture pin closure',status='PROVED',passed=True,evidence=['FIXTURE_CLOSURE.json','RESOLVED_INPUT_INVENTORY.json','VALIDATION.json']),
    dict(path='native fixture routing regeneration',status='PROVED',passed=True,evidence=['routing_retained/routing_selection.json','routing_retained/plan.json','STAGES.json'])])
(R/'CHECK.json').write_text(json.dumps(rows,indent=2)+'\n')
report=[
    'NOT PROVED end-to-end; kit n_go '+setup['kit']+' (tree C 0c7614c8).',
    'Cause of the missing 6ed81f1d pin: the fixture linked five databases but omitted them from the planner source map; native resolver checks remain unchanged (rehearsal_k4/FIXTURE_CLOSURE.json).',
    'Fixture closure PROVED: the selected planner closure ran once, enumerated 13 stream pins, and the harness supplied 62 authenticated pins with none missing (rehearsal_k4/RESOLVED_INPUT_INVENTORY.json).',
    'Native fixture routing PROVED, exit 0, with d21e374f bound; production P reconstruction NOT PROVED because the fixture uses its own routing_base (rehearsal_k4/routing_retained/plan.json).',
    'dbb2 PROVED on the generated fixture database with its digest as DBB_TARGET; header mismatch search NOT PROVED (rehearsal_k4/dbb/db_bytes.json).',
    'Scene-rebuild pins NOT PROVED: native child refuses the 16,000-row camera pin '+camera['rows']['sha256']+' at its Trinity 2,000-row limit; no production bytes are missing (rehearsal_k4/SCENE_REFUSAL_DETAIL.json; canary.log).',
    'Native host receipt NOT PROVED: canary stopped before admission (rehearsal_k4/STAGES.json).',
    'Handover with localised pins NOT PROVED: canary stopped before admission (rehearsal_k4/STAGES.json).',
    'Clock inheritance NOT PROVED: four-rank training was not reached (rehearsal_k4/STAGES.json).',
    'Fresh optimizer / counter zero NOT PROVED: training was not reached (rehearsal_k4/STAGES.json).',
    'Finite losses on four ranks NOT PROVED: training was not reached (rehearsal_k4/STAGES.json).',
    'Step-1 checkpoint through milestone NOT PROVED: training was not reached (rehearsal_k4/STAGES.json).',
    'Timed checkpoint NOT PROVED: training was not reached (rehearsal_k4/STAGES.json).',
    'Milestone export / local receipt / kit copier NOT PROVED: training was not reached (rehearsal_k4/STAGES.json).',
    'TK_JOB_START budget self-stop NOT PROVED: training was not reached (rehearsal_k4/STAGES.json).',
    'resume_pin latest / one further step NOT PROVED: training was not reached (rehearsal_k4/STAGES.json).',
    'Census receipt bound in h.py NOT PROVED: the canary refused before publication (rehearsal_k4/STAGES.json).',
    'Review wait / published v.json / fixture review NOT PROVED: the canary refused before publication (rehearsal_k4/STAGES.json).',
    'One attempt, no retry; peak RSS '+str(max(s['peak_rss_bytes'] for s in stages))+' bytes; new allocation '+str(measure['allocated_bytes']+overhead)+' bytes. Source kit, extracted tree and five stores verify unchanged; k2 evidence was not written (rehearsal_k4/VALIDATION.json; CHECK.json).']
assert len(report)<20
with (D/'REHEARSAL_K4_REPORT.md').open('x') as f:f.write('\n'.join(report)+'\n')
print(json.dumps(dict(report=str(D/'REHEARSAL_K4_REPORT.md'),rows=len(rows),proved=sum(r['passed'] for r in rows),usage=measure)))
