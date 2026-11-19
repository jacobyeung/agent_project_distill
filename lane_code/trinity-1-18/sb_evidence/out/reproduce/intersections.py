"""Recompute observable scene intersections; never infer missing parent membership."""
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from survey import ROOT,W,K,N,OUT,TREE,read,pin,save,sha
from student_pilot.r1_rooms import Rooms
from student_pilot import r2_policy as P

authority=read(W/'w19/work/build19/inputs/component_rows.json')['proven']['authority']
rooms=Rooms(authority)
bench_path=K/'benchmark_scene_exclusions.json'
bench=read(bench_path)
bank_scenes={b:set() for b in P.SCOPE}
bank_rooms={b:set() for b in P.SCOPE}
bank_unknown=[]
for name,facts in bench['members'].items():
    ds,scene=name.split('/',1)
    canonical,how=rooms.canonical(dict(dataset=ds,scene=scene))
    if not canonical:
        bank_unknown.append(name);continue
    room=rooms.room(canonical)
    for bank in set(facts['benchmarks']) & set(P.SCOPE):
        bank_scenes[bank].add(canonical)
        bank_rooms[bank].add(room)
other={}
for corpus,names in bench['other_corpora'].items():
    memberships=[bank for bank in P.SCOPE if corpus in bench['by_benchmark'].get(bank,{})]
    # Attribute union lists only when exactly one benchmark owns the corpus.
    all_owners=[bank for bank,c in bench['by_benchmark'].items() if corpus in c]
    other[corpus]=dict(scope_banks=memberships,all_owners=all_owners,scenes=names,
                       assignment='unique_corpus_owner' if len(all_owners)==1 else 'union_not_attributed')
    if len(all_owners)==1:
        for bank in memberships:
            bank_scenes[bank].update(corpus+'/'+s for s in names)
            bank_rooms[bank].update(corpus+'/'+s for s in names)

common=[pin(__file__),pin(bench_path),pin(TREE/'student_pilot/r1_rooms.py'),*[dict(v) for v in authority.values()]]
save(OUT/'BENCHMARK_SCENES.json',dict(schema='sb-benchmark-scenes-v1',inputs=common,
    method='Use the unchanged r1_rooms.Rooms.canonical and Rooms.room with the five pinned authorities. Preserve member benchmark attribution and ScanNet room / ARKit visit identity. Non-room corpora are attributed only by unique corpus ownership.',
    banks={b:dict(captures=sorted(bank_scenes[b]),rooms=sorted(bank_rooms[b]),capture_count=len(bank_scenes[b]),room_count=len(bank_rooms[b])) for b in P.SCOPE},
    unresolved_members=bank_unknown,other_corpora=other))

def check(label, rows, inputs, scope, apply_removals=False):
    count=Counter();scenes=set();rset=set();overlaps={b:{} for b in P.SCOPE};unknown=[]
    for row in rows:
        count['rows']+=1
        canonical,how=rooms.canonical(row)
        try: room=rooms.room(canonical) if canonical else None
        except (ValueError,TypeError):room=None
        if room is None:
            count['unresolved']+=1
            if len(unknown)<20:unknown.append({k:row.get(k) for k in ('qid','dataset','scene','canonical')})
            continue
        count['resolved']+=1;scenes.add(canonical);rset.add(room)
        for bank in P.SCOPE:
            if canonical in bank_scenes[bank] or room in bank_rooms[bank]:
                count[bank]+=1
                overlaps[bank][canonical]=dict(bank=bank,canonical=canonical,room=room,
                    venue=room.split('venue',1)[1] if room.startswith('arkitscenes/venue') else None)
    return dict(label=label,scope=scope,inputs=inputs,counts=dict(count),unique_scenes=len(scenes),unique_rooms=len(rset),
                scenes=sorted(scenes),rooms=sorted(rset),overlaps={b:list(v.values()) for b,v in overlaps.items()},
                unresolved_examples=unknown,removals_applied=apply_removals,
                certifies_lineage=False,complete_parent_membership=False)

reference=read(K/'scene_reference.json')
dev_rows=[dict(dataset=i['native'].split('/',1)[0],scene=i['native'].split('/',1)[1]) for i in reference['geometry_tower_job']['items']]
results=[check('Dev-S1 captures',dev_rows,[pin(K/'scene_reference.json')],
    'Development-set comparison only. The zero-overlap statement cannot certify any parent training population.')]
cr=read(W/'w19/work/build19/inputs/component_rows.json')
for label,spec in cr['proven']['routing_slices'].items():
    p=Path(spec['source']['path'])
    assert sha(p)==spec['source']['sha256']
    with p.open() as f:
        results.append(check(label,(json.loads(line) for line in f if line.strip()),[pin(p)],
            'Raw surviving N routing-family source before N-side row removals; not an inherited checkpoint scene manifest.'))
db=Path(cr['proven']['store']['database']['path'])
expected=cr['proven']['store']['database']['sha256']
assert any(r['path']==str(db) and r['sha256']==expected for r in read(ROOT/'work/sqlite_index.json'))
connection=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
try:
    results.append(check('v7 row store',(json.loads(row[0]) for row in connection.execute('SELECT row FROM rows ORDER BY i')),
        [dict(path=str(db),sha256=expected)],'Raw full v7 store before N-side removals; unresolved scene tokens remain unknown.'))
finally:connection.close()
save(OUT/'INTERSECTIONS.json',dict(schema='sb-observable-intersections-v1',inputs=common+[pin(OUT/'BENCHMARK_SCENES.json')],
    lineage={s:dict(status='MISSING',overlaps=None,reason='No complete authenticated parent scene manifests found. A zero intersection is not asserted.') for s in P.LINEAGE},
    observable_populations=results,warning='These population checks cannot be substituted for any of the nine component records. All found overlaps are retained.'))
for r in results:print(r['label'],r['counts'],{b:len(v) for b,v in r['overlaps'].items()})
