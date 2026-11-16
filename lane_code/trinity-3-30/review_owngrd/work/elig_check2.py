import json, sys, shutil, os, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/review_owngrd/work/code2')
from owngrd.eligibility import Gate, canon
A='/scratch/jjyeung/orch_n30/b05_owngrd/work/auth/'
g=Gate(A)
ev=json.load(open(A+'EVAL_ROOMS.json')); caps=json.load(open(A+'CAPTURES.json'))
devm=json.load(open(A+'DEVS1_MANIFEST.json')); wh=json.load(open(A+'WITHHELD_ROOMS_80.json'))
bench=json.load(open(A+'BENCH_SCENE_EXCLUSIONS_v2.json')); devx=json.load(open(A+'dev_scene_exclusions_d0.json'))
def room(can):
    ds,s=can.split('/',1)
    if ds=='scannet': return 'scannet/'+s[:9]
    if ds=='arkitscenes': return ev['arkit_rooms'].get(s, can)
    return can
byroom=collections.defaultdict(list)
for c in caps['captures']:
    byroom[room(c['canonical'])].append(c['canonical'])
    if c['room']!=room(c['canonical']): print('room derivation differs', c['canonical'], c['room'], room(c['canonical']))
excl_rooms=set()
excl_rooms |= {room(canon(c['scene'])) for c in devm['captures']}
excl_rooms |= {canon(r) for r in wh['rooms']}
excl_rooms |= {canon(g_) for g_ in bench['physical_groups']} | {room(canon(s)) for s in bench['scenes']}
excl_rooms |= set(ev['evaluation_rooms'])|set(ev['qualification_rooms'])
excl_rooms |= {room(s) for s in ev['clean_scenes']+ev['tuning_scenes']+ev['frames32_scenes']}
rs=json.load(open(A+'ROOM_SPLIT.json'))
excl_rooms |= {room(s) for k in ('tuning_scenes','legacy_read_scenes','room_disjoint_scenes','overlapping_read_scenes') for s in rs[k]} | set(rs['overlapping_rooms'])
excl_rooms |= {canon(x) for x in devx['physical_groups']}
leak=[can for r in excl_rooms for can in byroom.get(r,[]) if not g.reasons(can)]
print('excluded rooms', len(excl_rooms), 'pool captures in them admitted:', len(leak), leak[:10])
# frames32 scenes as rooms: gate adds rooms only for scannet; ARKit frames32 scene -> venue?
f32=[s for s in ev['frames32_scenes'] if s.startswith('arkitscenes/')]
f32v=[(s, room(s)) for s in f32 if room(s)!=s]
adm=[can for s,r in f32v for can in byroom.get(r,[]) if can!=s and not g.reasons(can)]
print('frames32 ARKit scenes whose venue holds other admitted captures', len(adm), adm[:5])
# tamper test
T='/scratch/jjyeung/orch_n30/review_owngrd/work/auth_tamper/'
os.makedirs(T, exist_ok=True)
for f in os.listdir(A): shutil.copy(A+f, T+f)
d=json.load(open(T+'WITHHELD_ROOMS_80.json')); d['rooms']=d['rooms'][1:]; json.dump(d, open(T+'WITHHELD_ROOMS_80.json','w'))
try: Gate(T); print('TAMPER ACCEPTED')
except ValueError as e: print('tamper refused:', str(e)[:80])
