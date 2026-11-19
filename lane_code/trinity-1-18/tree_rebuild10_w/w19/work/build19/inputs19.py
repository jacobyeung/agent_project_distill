"""Retain the existing census and measure withheld-room overlap on the slices."""
from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build19';I=B/'inputs';O=B/'proofs/rows'
I.mkdir(exist_ok=True);O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/tree_r1')]
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r1_components import NOTICE
from student_pilot.r2_withheld import Withheld
from student_pilot.r1_rooms import Rooms
from student_pilot.row_removals import Removals
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');return file_pin(p)
cfg=load(L/'work/build18/inputs/config.json');audit=load(L/'work/build18/proofs/rooms/RESULT.json')['audit_after']
withheld=file_pin(L/'fixtures/work/shared/WITHHELD_ROOMS_80.json');rule=Withheld(withheld)
rooms=Rooms(cfg['r1_training']['room_authority']);removals=Removals(cfg['remove_files']);slices={}
for name,spec in load(pinned(cfg['r1_training']['row_sources'])).items():
    if name not in ('recovery','units','absolute_distance'):continue
    counts=dict(rows=0,admitted=0,k1_heldout=0,r0=0,withheld=0,unresolved=0)
    with pinned(spec['source']).open() as source:
        for line in source:
            row=json.loads(line);counts['rows']+=1
            if not removals.keep(row):continue
            counts['admitted']+=1
            status,canonical,_=rooms.status(row)
            if status!='ok':counts[status]+=1
            counts['withheld']+=int(rule.touches(dict(row,dataset=row.get('dataset',''),scene=row.get('scene','')),dict(names=[canonical] if canonical else [])))
    slices[name]=dict(counts,source=spec['source'])
record=dict(schema='r1-component-rows-v1',status='DEFERRED',
    proven=dict(routing_slices=slices,room_rule='student_pilot/r1_rooms.py',authority=cfg['r1_training']['room_authority'],withheld=withheld,
        store=dict(database=audit['store']['database'],removals=cfg['remove_files'],appended_rows=cfg['r1_training']['room_authority']['build'],
                   census_source=file_pin(L/'work/build18/proofs/rooms/RESULT.json'))),
    unproven=dict(unresolved_v7_rows=audit['store']['unresolved'],
        reason='Alias-map rebuild pending. Benchmark exclusion rests on per-stream benchmark_scene_exclusions at every admission; unresolved tokens are not certified clean.',
        benchmark_scene_exclusions=cfg['benchmark_scene_exclusions']),
    inputs=[withheld,file_pin(L/'work/build18/proofs/rooms/RESULT.json'),cfg['benchmark_scene_exclusions'],*cfg['r1_training']['room_authority'].values()])
assert all(all(v[k]==0 for k in ('k1_heldout','r0','withheld','unresolved')) for v in slices.values())
pin=write(I/'component_rows.json',record);write(O/'RESULT.json',record)
card=load(pinned(cfg['r1_training']['mix']));card.update(vehicle='N',leg='R1',component_evidence=NOTICE)
cfg['r1_training'].update(mix=write(I/'mix.json',card),component_rows=pin)
for name in ('config.json','kit_config.json'):write(I/name,cfg)
(B/'STATUS.md').write_text('Build 19: GO=false. The narrow deferral and claim guards are implemented. The withheld list is present and all filtered routing slices have zero measured room hits. Native proof and validation remain.\n')
print(json.dumps(slices,indent=2))
