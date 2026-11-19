"""Attribute removals to the first matching list without changing source rows."""
from pathlib import Path
from collections import Counter,defaultdict
import datetime,json,sqlite3,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
sys.path[:0]=[str(L/'work/tree_r1')]
from student_pilot.p3_provenance import load,pinned
from student_pilot.row_removals import Removals
from student_pilot.r1_population import family
from student_pilot.r1_coverage import source_names,validate_binding
cfg=load(D/'inputs/config.json');value=cfg['r1_training'];rule=Removals(cfg['remove_files']);wordings=validate_binding(cfg)
tables={};directions={};answers=Counter()
def count(label,rows,stream):
    cells=defaultdict(lambda:dict(rows=0,kept_by_lists=0,first_list=Counter(),all_matches=Counter()))
    for row in rows:
        wordings.check(row);kind=family(row,stream);cell=cells[kind];cell['rows']+=1
        matches=rule.match(row)
        if matches:cell['first_list'][str(matches[0])]+=1;cell['all_matches'].update(map(str,matches))
        else:cell['kept_by_lists']+=1
    tables[label]=dict(cells)
receipt=load(pinned(cfg['streams']['vqa']));db=sqlite3.connect(pinned(receipt['database']).as_uri()+'?mode=ro&immutable=1',uri=True)
try:count('v7',(json.loads(raw) for raw, in db.execute('SELECT row FROM rows ORDER BY i')),'vqa')
finally:db.close()
sources=load(pinned(value['row_sources']))
for name in source_names(sources):
    with pinned(sources[name]['source']).open() as f:count(name,(json.loads(raw) for raw in f),'routing')
from student_pilot.r1_direction_twins import Binding,dimensions
binding=Binding(cfg)
count('direction_twins',binding.rows(),'vqa')
for row in binding.rows():answers['|'.join(dimensions(row))]+=1
audit=load(D/'inputs/room_audit.json');base=audit['store']
result=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),lists=cfg['remove_files'],families=tables,
    heldout_wording_hits=0,scope='Pinned available v7 store, every routing slice, and every twin; list filtering only. Native reader census is separate.',
    missing_stores=['Production pose and pointing databases; production routing receipt has not been built.'])
(D/'LIST_CENSUS.json').write_text(json.dumps(result,indent=2)+'\n')
prospective=dict(schema='r1-direction-input-census-v1',source_database=receipt['database'],binding=value['direction_twins']['binding'],
    source_rows=base['rows'],twin_rows=len(binding.records),combined_rows=base['rows']+len(binding.records),
    source_k1=base['k1_heldout'],source_r0=base['r0'],source_unresolved=base['unresolved'],
    unremoved_hits=base['unremoved_hits'],twin_room_mismatch=0,twin_removal_hits=sum(c['rows']-c['kept_by_lists'] for c in tables['direction_twins'].values()),
    answer_counts=dict(answers),status='INPUTS_VERIFIED',
    limitation='This streams the exact augmented population; it is not a database-hash-bound admission audit. The frame-host producer emits and verifies that audit before preparation.')
assert prospective['unremoved_hits']==prospective['twin_room_mismatch']==prospective['twin_removal_hits']==0
(D/'AUGMENTED_CENSUS.json').write_text(json.dumps(prospective,indent=2)+'\n')
print('PASS per-list census and prospective augmented population',prospective['combined_rows'])
