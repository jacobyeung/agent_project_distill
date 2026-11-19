cd /scratch/jjyeung/orch_n30/fb_pack/cam/out && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json,hashlib
rows=[json.loads(l) for l in open('rows/camera_wording.jsonl')]
print('rows',len(rows),'keys',sorted(rows[0].keys())[:25])
qk='qid' if 'qid' in rows[0] else [k for k in rows[0] if 'qid' in k or k=='id'][0]
q=[r[qk] for r in rows]; print('qkey',qk,'distinct',len(set(q)))
ref={}; seen=0
for s in ['shard000','shard001','shard002']:
    d=json.load(open(f'intake/camera_wording_{s}.json')); seen+=d['population_count']
    for x in d['refusals']: ref[x['qid']]=x['reason']
print('shard seen',seen,'refused',len(ref))
rb=json.load(open('REBIND.json')); ex=rb.get('excluded'); print('rebind excluded type',type(ex).__name__, len(ex) if ex else None)
exq=set((e['qid'] if isinstance(e,dict) else e) for e in ex) if ex else set()
print('refused==rebind excluded', set(ref)==exq)
adm=sorted(x for x in set(q) if x not in ref); print('admitted',len(adm))
out={'schema':'camera_admitted_qids_v1','rows':{'path':'/scratch/jjyeung/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl','sha256':hashlib.sha256(open('rows/camera_wording.jsonl','rb').read()).hexdigest(),'count':len(rows)},'refused_count':len(ref),'refused_reasons':sorted(set(ref.values())),'source':'intake/camera_wording_shard00{0,1,2}.json refusals (r2 intake, compose_native r1_routing.py:191)','admitted_count':len(adm),'admitted_qids':adm}
b=json.dumps(out,indent=0,sort_keys=True).encode(); open('ADMITTED_QIDS.json','wb').write(b); print('ADMITTED_QIDS.json',len(b),hashlib.sha256(b).hexdigest())
P
