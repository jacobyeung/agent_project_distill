"""Bind node-local N inputs and a conservative, explicitly partial room audit."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys,re
L=Path(__file__).resolve().parents[2];B=L/'work/build16';I=B/'inputs';I.mkdir(exist_ok=True)
T=L/'work/tree_r1';sys.path.insert(0,str(T))
from student_pilot.p3_provenance import file_pin,load,pinned
M=Path('/scratch/jjyeung/n30_mirror');E=L.parent
def save(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');return file_pin(p)
def local(v):
    if isinstance(v,list):return [local(x) for x in v]
    if isinstance(v,dict):return {k:local(x) for k,x in v.items()}
    if isinstance(v,str):
        for a,b in [(str(E/'w15'),str(L)),('/scratch/jjyeung/orch_n30/r1_pkt/work/derive_7fh23bg8/b/k',str(E/'ext/pk'))]:
            if v.startswith(a) and Path(v.replace(a,b,1)).is_file():return v.replace(a,b,1)
    return v
cfg=local(load(L/'work/build15/inputs/kit_config.json'))
sources=local(load(L/'work/n1fix2/inputs/row_sources.json'))
paths=dict(recovery=M/'rows_r1/out/recovery_v3/rows.jsonl',units=M/'rows_r1/out/vehN_units/repaired/rows_slice.jsonl',
           absolute_distance=M/'rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl')
expected=dict(recovery='58389a67',units='aa1432cd',absolute_distance='aedd3b54')
for k,p in paths.items():
    pin=file_pin(p);assert pin['sha256'].startswith(expected[k])
    sources[k]['source']=pin
    if k!='absolute_distance':sources[k].pop('filtered_source',None)
sources['absolute_distance']['filtered_source']=file_pin(M/'rows_r2/out/vehN_pool_abs_distance_full/filtered/rows.jsonl')
assert sources['absolute_distance']['filtered_source']['sha256'].startswith('06d8688d')
cfg['r1_training']['row_sources']=save(I/'row_sources.json',sources)
cfg['extent_receipt']=file_pin(M/'rows_r2/out/vehN_pool_abs_distance_full/EXTENT_RECEIPT_merged_n1fix2.json')
assert cfg['extent_receipt']['sha256'].startswith('2c622905')
cfg['scene_division']=file_pin(L/'work/n1fix2/inputs/0d28fdd432b0.json')
assert cfg['scene_division']['sha256'].startswith('0d28fdd4')
division=load(pinned(cfg['scene_division']));train=set(division['train_scenes'])
# The exact full K1 authority and alias maps are absent. The pinned drop list
# authenticates positive hits in this pool; it does not certify other rooms.
drop_pin=file_pin(M/'rows_r2/out/vehN_pool_abs_distance_full/K1_DROP.json')
drop=load(pinned(drop_pin))
kkeys={q.removesuffix('_x2') for q in drop['repaired']['dropped_qids']}
r0pin=file_pin(M/'rows_r1/work/codeB/authority_cache/R0_ROOMS.txt')
assert r0pin['sha256']=='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'
def room(s):
    s=s.replace('scannetppv2/','scannetpp/')
    return re.sub(r'_\d\d$','',s) if s.startswith('scannet/') else s
r0={room(s) for s in pinned(r0pin).read_text().splitlines() if s}
meta={};known_k1=set();catalog={'schema':'r1-source-catalog-v1','sources':{}}
for k,p in paths.items():
    rows=[]
    with p.open() as f:
        for line in f:
            raw=json.loads(line);prov=raw.get('provenance',{})
            can=raw.get('canonical') or prov.get('canonical') or raw.get('gt_authority',{}).get('canonical')
            ds=raw.get('dataset') or {'scannet':'d1','scannetpp':'d2','scannetppv2':'d2','arkitscenes':'d3'}[can.split('/')[0]]
            alias=ds+'/'+raw['scene']
            origin=(raw.get('source_qid') or prov.get('source_qid') or prov.get('a0_v4',{}).get('source_qid') or raw['qid']).removesuffix('_x2')
            rows.append(dict(qid=raw['qid'],canonical=can,alias=alias,origin=origin))
            if origin in kkeys and can:known_k1.add(room(can))
    meta[k]=rows;catalog['sources'][k]=dict(source=sources[k]['source'],qids=[r['qid'] for r in rows])
removals=[];reports={}
for k,rows in meta.items():
    counts=Counter();hits=[]
    for row in rows:
        reasons=[]
        if row['origin'] in kkeys or row['canonical'] and room(row['canonical']) in known_k1:reasons.append('k1_heldout_known')
        if row['canonical'] and room(row['canonical']) in r0:reasons.append('r0')
        if row['alias'] not in train:reasons.append('division_outside_train')
        if not row['canonical']:reasons.append('canonical_unknown')
        counts.update(reasons)
        if reasons:
            hit=dict(row_key=row['qid'],reason='|'.join(reasons),scene=row['alias'],canonical=row['canonical'])
            removals.append(hit);hits.append(hit)
    reports[k]=dict(source=sources[k]['source'],rows=len(rows),hit_counts=dict(counts),removed=len(hits),
                   known_positive_rows=hits,k1_complete=False,r0_canonical_unknown=sum(not r['canonical'] for r in rows))
p=I/'s.json';p.write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in removals))
old=cfg['remove_files'][:-1]
for pin in old:pinned({k:pin[k] for k in ('path','sha256')})
cfg['remove_files']=[*old,file_pin(p),file_pin(E/'inputs/records/n.json'),file_pin(E/'inputs/records/z.json')]
assert cfg['remove_files'][-2]['sha256'].startswith('02315a74') and cfg['remove_files'][-1]['sha256'].startswith('caba6a56')
cfg['r1_training']['source_membership']=save(I/'source_membership.json',catalog)
v=load(L/'work/n1fix2/inputs/v7_receipt.json');v['database']=file_pin(M/'rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
assert v['database']['sha256']=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
cfg['streams']['vqa']=save(I/'v7_receipt.json',v);cfg['r1_training']['store_parameter']=cfg['streams']['vqa']
card=load(L/'work/n1fix2/inputs/mix.json')
for cell in card['cells']:
    if cell['type'] in ('counting','totals','direction'):cell['rows_per_step']={'counting':10.46,'totals':0,'direction':36.69}[cell['type']]
(I/'CARD.md').write_text('# N training card\n\nCounting uses the measured procedure population; totals is zero. Freed VQA slots enter direction. The distance quota is 15.6. Scale weight is 0.04. Full measured ceilings are published after the census.\n')
card['source']=file_pin(I/'CARD.md');cfg['r1_training']['mix']=save(I/'mix.json',card)
save(I/'kit_config.json',cfg);save(I/'config.json',cfg)
audit=dict(slices=reports,remove_file=file_pin(p),r0=r0pin,r0_rooms=len(r0),k1_substitute=drop_pin,
           known_k1_rooms=sorted(known_k1),k1_full_rooms_expected=50,k1_complete=False,
           absent=[str(M/'b12_cntapp/work/auth/K1SPLIT_R0.json'),str(M/'rows_a2/work/alias_map.json'),str(M/'b12_cntapp/work/d3_token_map.json')],
           qualification='Known K1 positives only, from the pool drop receipt and matching source QIDs/rooms. Unknown K1 overlap is not a pass. Production proof requires the full pinned room authority. R0 uses the exact cached authority; canonical provenance substitutes for absent alias maps.')
save(B/'INPUTS.json',audit)
(B/'STATUS.md').write_text('# Build 16 status\n\nStep 1 inputs bound. K1 full authority and alias maps are absent; known K1 hits are removed by a pinned list, with incomplete coverage explicit. Card ceilings await the native census. GO=false.\n')
print(json.dumps({k:{x:v for x,v in r.items() if x not in ('known_positive_rows','source')} for k,r in reports.items()},indent=2))
print('Known K1 rooms',len(known_k1),'R0 rooms',len(r0))
