from pathlib import Path
import sys, json, gzip, hashlib, shutil, traceback
from collections import Counter
L=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path[:0]=[str(L/'out/rcj'),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
import nd,x,z
R=L.parent/'work/d173725/173725'
O=D/'observations';O.mkdir(exist_ok=True)
def write(p,v):p.write_bytes(nd.raw(v))
def pin(p):return dict(sha256=z.sha(p),bytes=p.stat().st_size,path=str(p))
summary=nd.load(R/'rd0/rdiff_summary.json')
assert summary['inputs']['P']['sha256']==nd.GATE
assert summary['rdiff_sha256']==z.sha(R/'rd0/rdiff.json.gz')
detail=json.loads(gzip.decompress((R/'rd0/rdiff.json.gz').read_bytes()))
assert len(detail['N'])==summary['N_rows']==43101
assert len(detail['P_absent'])==summary['P_rows_absent_from_N']==4797
removals,scenes,state=nd.native_rules(D/'native/p/q/selection/rows.sqlite')
rows=[]
for v in detail['P_absent']:
    ds,scene,qid,source=v['key']
    # These are the recorded identity fields, not invented SQL row contents.
    record=dict(dataset=ds,scene=scene,qid=qid,label_row_keys=v['removal_keys'])
    why=nd.attribution(record,removals,scenes)
    assert why['removal_list_sha256s']==v['removal_list_sha256s']
    rows.append(dict(why,key=v['key'],i=v['i'],source=source,content_sha256=v['content_sha256']))
causes=Counter(v['attribution'] for v in rows)
assert causes==dict(scene=4768,list=29),causes
sources={n:pin(R/n) for n in ('rd0/rdiff_summary.json','rd0/rdiff.json.gz','materialization.json','routing_selection.json')}
na=dict(schema='na-v2',status='PASS',count=len(rows),unattributed=0,rows=rows,
    counts_by_attribution=dict(causes),state=state,sources=sources,
    scope='All absent identities and removal keys from the authenticated published comparison; native predicates.')
(O/'na.json.gz').write_bytes(gzip.compress(nd.raw(na),mtime=0))
material=nd.load(R/'materialization.json')
counts=Counter({k:material['types'][k]['r16_kept'] for k in ('camera_displacement','camera_movement_direction','camera_rotation')})
pool=[v for v in detail['N'] if v['key'][3] is not None]
units=sum(v['key'][2].startswith('a0_units_') for v in pool)
assert len(pool)==material['types']['object_abs_distance']['pool_program_rows']==11663
assert units==718 and all(v['key'][3]=='U_Faithful' for v in pool if v['key'][2].startswith('a0_units_'))
counts.update(units=units,absolute_distance=len(pool)-units)
assert sum(counts.values())==summary['N_rows']
rt=nd.type_table(counts,summary['inputs']['N']['sha256'])
rt.update(sources=sources,scope='Published complete native materialization type counts, with prefixed unit QIDs counted in every published N key; CPU helper must independently classify full native rows.')
write(O/'routing_types.json',rt)
contract=nd.load(L/'out/rcj/f.json')
diagnosis=dict(schema='nd-v2',status='UNAVAILABLE',task_i='UNAVAILABLE',task_ii='PASS',task_iii='PASS',
    P_rows=summary['P_rows'],N_rows=summary['N_rows'],matched_rows=len(detail['N']),
    absent_count=len(rows),absent_unattributed=0,
    metadata_classes={k:dict(rows=None,path_differences=None,content_rows=None,status='UNAVAILABLE') for k in contract['allowed_metadata_classes']},
    reason='Full SQL row and target text were not published; hashes cannot reveal per-field changes. No substitute databases were constructed.',
    U_Faithful=dict(P=747,kept=718,expected_kept=718,status='PASS'),sources=sources,
    original_refusal=nd.load(R/'timings.json')['task_a'])
ordinal=sum(v['i']!=v['P']['i'] for v in detail['N'])
diagnosis['metadata_classes']['ordinal']=dict(rows=ordinal,path_differences=ordinal,content_rows=ordinal,status='COUNTED',source='published N.i and N.P.i over every matched key')
write(O/'nd.json',diagnosis)
# Exercise publication against the authentic output bytes. The job log is outside
# the published 5 MB set and is intentionally not part of this replay.
stage=D/'publication_source';stage.mkdir(exist_ok=True)
for p in R.rglob('*'):
    if p.is_file() and p.name not in ('job.log','timings.json'):
        q=stage/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True)
        if not q.exists():shutil.copyfile(p,q)
for p in O.iterdir():shutil.copyfile(p,stage/p.name)
dest=D/'publication_result';dest.mkdir(exist_ok=True)
timing=nd.load(R/'timings.json')
timing['republication']=dict(original_timings=pin(R/'timings.json'),cpu_job_rerun=False,
    scope='Publication replay of real job artifacts plus explicitly qualified offline observations; original refusals remain recorded.')
x.bounded_publication(stage,dest,timing)
z.write(dest/'timings.json',timing)
actual=sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())
assert actual==timing['aggregate_publication_bytes']<x.LIMIT
pc=nd.load(dest/'proc_check.json');assert len(pc['rows'])==80 and all(v['status']=='PASS' for v in pc['rows'])
assert all(isinstance(v['n']['values']['prompt_ids'],dict) for v in pc['rows'])
write(D/'REAL_EVIDENCE.json',dict(status='PASS',publication_bytes=actual,absences=causes,
    routing_types=rt,metadata_classes='UNAVAILABLE; full stores absent',
    omitted={k:v for k,v in timing['publication_selection'].items() if v['status']=='OMITTED'}))
print(json.dumps(dict(publication_bytes=actual,absences=causes,routing_types=rt['status'],
    per_type=[(v['type'],round(v['percent_off'],4),v['status']) for v in rt['types']],metadata_classes='UNAVAILABLE')))
