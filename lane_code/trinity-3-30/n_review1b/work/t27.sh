K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build22/upload/u/27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390
F=/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl
python3 - <<P
import json
k=json.load(open('$K'))['teacher_k1']
print(list(k.keys()))
for kk,v in k.items():
    if kk!='captures': print(kk, str(v)[:300])
caps=k['captures']; print(len(caps), caps[0])
rooms=set(c['room'] for c in caps); canon={c['canonical']:c['room'] for c in caps}
print(sorted(set(c.get('split',c.get('role','?')) for c in caps)))
rows=[json.loads(l) for l in open('$F')]
print('list rooms in K1 caps:', {r['room']: r['room'] in rooms for r in rows})
print('canonical->room consistent:', all(canon.get(r['canonical'])==r['room'] for r in rows), sorted(set(r['canonical'] for r in rows)))
print([c for c in caps if c['room'] in ('scannet/scene0630','scannet/scene0280')][:8])
P
