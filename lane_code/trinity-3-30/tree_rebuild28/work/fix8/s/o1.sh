export TZ=UTC; date -u +%TZ; squeue -j 174134 -h -o "%i %T %M %N"
timeout 240 srun --overlap --jobid 174134 -N1 -n1 python3 -I -B - <<'PYEOF'
import json, os, base64, hashlib, tarfile, io
OUT='/tmp/q_22c714e1_174134'; D='/tmp/a15_f8_174134'; os.makedirs(D,exist_ok=True)
R=json.load(open(OUT+'/p/q/RESULT.json'))
IN='/tmp/q_22c714e1'
def m(p): return OUT+p[len(IN):] if p.startswith(IN) else p
st=[(e['sha256'],m(e['path'])) for e in R['staged']]
print('staged',len(st))
keep=[]
for h,p in st:
    try:
        n=os.path.getsize(p)
        if n>3000000: continue
        with open(p,'rb') as f: b=f.read()
        if not b[:1] in (b'{',b'['): continue
        json.loads(b); keep.append((h,p,n))
    except Exception: pass
print('json objects',len(keep),sum(k[2] for k in keep))
t=tarfile.open(D+'/j.tar','w')
for h,p,n in keep: t.add(p,arcname='u/'+h)
for extra in ('p/q/c.json','p/q/RESULT.json','p/q/p/request.json'):
    if os.path.isfile(OUT+'/'+extra) and os.path.getsize(OUT+'/'+extra)<3000000: t.add(OUT+'/'+extra,arcname='q/'+extra.replace('/','_'))
import glob
for f in glob.glob(OUT+'/p/q/p/prepare_*/*/receipt.json')+glob.glob(OUT+'/p/q/p/prepare_*/*.json')+glob.glob(OUT+'/p/q/twins/*.json')+glob.glob(OUT+'/p/q/q/twins/*.json'):
    if os.path.getsize(f)<3000000: t.add(f,arcname='q/'+f[len(OUT)+1:].replace('/','_'))
t.close()
print('tar bytes',os.path.getsize(D+'/j.tar'))
print('twins dirs',glob.glob(OUT+'/p/q/*/twins')+glob.glob(OUT+'/p/q/twins'))
PYEOF
echo rc=$?
timeout 60 srun --overlap --jobid 174134 -N1 -n1 bash -c 'echo BEGIN_B64; base64 -w0 /tmp/a15_f8_174134/j.tar; echo; echo END_B64'
