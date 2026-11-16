<!-- recovered by seal_plan: transcript=71f94277 line=32918 utc=2026-11-14T18:38:51.665Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,hashlib
B='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
old=json.load(open(B+'actual_cache_cpu/MASK_CACHE.json')); new=json.load(open(B+'native_fix_s23_01/orchard_native/MASK_CACHE_P6_BOUND.json'))
def flat(d,p=''):
    out={}
    if isinstance(d,dict):
        for k,v in d.items(): out.update(flat(v,p+'/'+str(k)))
    elif isinstance(d,list):
        for i,v in enumerate(d): out.update(flat(v,p+'/'+str(i)))
    else: out[p]=d
    return out
fo,fn=flat(old),flat(new)
ch=[k for k in sorted(set(fo)|set(fn)) if fo.get(k)!=fn.get(k)]
print('MASK receipts: values',len(fo),len(fn),'changed keys',ch,[ (fo.get(k),fn.get(k)) for k in ch][:3])
print('new receipt sha',hashlib.sha256(open(B+'native_fix_s23_01/orchard_native/MASK_CACHE_P6_BOUND.json','rb').read()).hexdigest()[:16])
F=B+'native_package_s23_03/seal/FAMILY.json'; P=B+'native_package_s23_02/seal/FAMILY.json'
n=json.load(open(F)); o=json.load(open(P))
print('family',hashlib.sha256(open(F,'rb').read()).hexdigest())
f1,f2=flat(o),flat(n)
ch=[k for k in sorted(set(f1)|set(f2)) if f1.get(k)!=f2.get(k)]
print(len(f1),len(f2),'changed',len(ch))
for k in ch[:70]: print(' ',k[-88:],'|',str(f1.get(k))[:16],'->',str(f2.get(k))[:16])
pins=n['code_pins']; wk=[k for k in pins if k.endswith('orchard_native/native_worker.py')][0]; nk=[k for k in pins if k.endswith('native/out2/nomdg.py')][0]
print('worker_entrypoint==code pin:', n['assets']['worker_entrypoint']['sha256']==pins[wk], pins[wk][:12])
print('mask producer==nomdg pin:', new.get('producer_sha256')==pins[nk], pins[nk][:12], '; kernel pin==code pin:', n['worker_contract']['kernel_source_pins']['nomdg']==pins[nk])
print('mask_cache contract:', json.dumps(n['worker_contract'].get('mask_cache'))[:300])
r=json.load(open(B+'native_package_s23_03/REUSE_COMPARISONS.json'))
rows=r.get('rows') or r.get('checks') or []
import collections
print('rows',len(rows), collections.Counter((x.get('disposition'),x.get('status') or x.get('passes') or x.get('result')) for x in rows))
bad=[x for x in rows if str(x.get('status') or x.get('passes') or x.get('result')).lower() not in ('pass','true','passed','ok','pending_controls','requires_controls','authority_pending')]
print('non-pass rows:',[(x.get('row') or x.get('id'),x.get('disposition'),x.get('status') or x.get('result')) for x in bad][:10])
EOF