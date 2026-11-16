import json, re, sys, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/review_owngrd/work/code2')
from owngrd.eligibility import Gate, canon
A='/scratch/jjyeung/orch_n30/b05_owngrd/work/auth/'
man=json.load(open('/scratch/jjyeung/orch_n30/b05_owngrd/work/manifests/TEACHER_K1.json'))
print('manifest gate_root', man['gate_root'], 'by_split', man['counts']['by_split'], 'refused', len(man['refused']), 'missing_gt', len(man['missing_gt']), 'idx_mismatch', len(man['index_mismatch']))
# independent: collect every string from every authority except CAPTURES/K1 base
strings=set()
def walk(x):
    if isinstance(x,str): strings.add(x)
    elif isinstance(x,dict):
        for k,v in x.items(): strings.add(k); walk(v)
    elif isinstance(x,list):
        for v in x: walk(v)
for f in ['BENCH_SCENE_EXCLUSIONS_v2.json','DEVS1_MANIFEST.json','EVAL_ROOMS.json','ROOM_SPLIT.json','WITHHELD_ROOMS_80.json','dev_scene_exclusions_d0.json']:
    d=json.load(open(A+f))
    if f=='EVAL_ROOMS.json':
        # alias_rooms / arkit_rooms are maps of ALL scenes, not exclusions; exclude them from string bag
        d={k:v for k,v in d.items() if k not in ('alias_rooms','arkit_rooms','provenance')}
    if f=='BENCH_SCENE_EXCLUSIONS_v2.json':
        d={k:v for k,v in d.items() if k not in ('inputs',)}
    walk(d)
# normalize: strip dataset prefixes
def bare(s):
    return s.split('/',1)[1] if '/' in s else s
bag=set(bare(s) for s in strings)
ev=json.load(open(A+'EVAL_ROOMS.json'))
caps=json.load(open(A+'CAPTURES.json'))
inv={c['canonical']:c for c in caps['captures']}
hits=collections.Counter(); rooms_split=collections.defaultdict(set)
for c in man['captures']:
    can=c['canonical']; ds,s=can.split('/',1)
    keys={s, bare(c['room'])}
    if ds=='scannet': keys.add(s[:9])
    if ds=='arkitscenes':
        r2=ev['arkit_rooms'].get(s)
        if r2 and r2!=c['room']: print('ARKIT ROOM DISAGREES', can, c['room'], r2)
        if r2 is None: hits['arkit_not_in_eval_map']+=1
        keys.add(bare(r2 or ''))
    if inv[can]['room']!=c['room']: print('INV ROOM DISAGREE', can)
    # bench tokens for this scene
    import hashlib
    nd={'scannet':'scannet','scannetpp':'scannetppv2','arkitscenes':'arkitscenes'}[ds]
    keys.add('v'+hashlib.sha256(('rung1 scene '+nd+'/'+s).encode()).hexdigest()[:12])
    bad=keys & bag
    if bad: print('INDEPENDENT HIT', can, c['room'], c['k1_split'], bad)
    rooms_split[c['room']].add(c['k1_split'])
    hits[ds]+=1
print(hits)
print('rooms in both splits', [r for r,v in rooms_split.items() if len(v)>1])
# gate on the manifest
g=Gate(man['gate_root']); print('gate digest match', g.digest==man['gate_receipt']['gate_digest'])
print('gate admit', g.admit(man['captures'])['captures'])
# room field form for scannet
print(collections.Counter((c['canonical'].split('/')[0], bool(re.search(r'_\d\d$', c['room']))) for c in man['captures']))
print([ (c['canonical'],c['room']) for c in man['captures'] if c['canonical'].startswith('scannet/')][:3])
# test gate on known excluded items
devm=json.load(open(A+'DEVS1_MANIFEST.json'))
wh=json.load(open(A+'WITHHELD_ROOMS_80.json'))
bench=json.load(open(A+'BENCH_SCENE_EXCLUSIONS_v2.json'))
miss=[]
for c in devm['captures']:
    if not g.reasons(c['scene']): miss.append(('devs1',c['scene']))
for r in wh['rooms']:
    ds=canon(r).split('/')[0]
    sc = canon(r)+'_00' if ds=='scannet' else canon(r)
    if not g.reasons(sc): miss.append(('withheld',sc))
for s in bench['scenes']:
    if not g.reasons(canon(s)): miss.append(('bench',s))
for s in ev['clean_scenes']+ev['tuning_scenes']+ev['frames32_scenes']:
    if not g.reasons(s): miss.append(('evalr',s))
for r in ev['evaluation_rooms']+ev['qualification_rooms']:
    # find a pool capture in that room
    pass
print('gate misses on known exclusions', len(miss), miss[:10])
# rooms of eval: any pool capture admitted whose EVAL_ROOMS map room is excluded
evrooms=set(ev['evaluation_rooms'])|set(ev['qualification_rooms'])
adm_bad=[]
for can,c in inv.items():
    ds,s=can.split('/',1)
    r = ev['arkit_rooms'].get(s) if ds=='arkitscenes' else None
    rr = {c['room']} | ({r} if r else set())
    if ds=='scannet': rr.add('scannet/'+s[:9])
    if rr & evrooms and not g.reasons(can): adm_bad.append(can)
print('admitted pool captures whose room is an eval room', len(adm_bad), adm_bad[:5])
# ARKit room disagreement in whole inventory
dis=[(can,c['room'],ev['arkit_rooms'].get(can.split('/')[1])) for can,c in inv.items() if can.startswith('arkitscenes/') and ev['arkit_rooms'].get(can.split('/')[1]) not in (None,c['room'])]
print('inventory ARKit room != EVAL_ROOMS arkit_rooms', len(dis), dis[:5])
