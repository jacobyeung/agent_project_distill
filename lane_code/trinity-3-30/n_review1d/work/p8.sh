W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; H=$W/w24h; I=$W/w24i; P=/scratch/jjyeung/envs/p1cpu/bin/python
cd $I/work/build24m4i; echo "#### EXACT_CONFIG_DELTA.json"; head -c 5000 EXACT_CONFIG_DELTA.json; echo
$P -I -s -B - <<'PY'
import json,base64,hashlib,glob,os
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
def ent(kit,h):
    s=json.load(open(kit+'/k/s.json')); s=json.loads(base64.b64decode(s['payload'])) if 'payload' in s else s
    e=s['entries']['u/'+h]; raw=base64.b64decode(e['payload']); assert hashlib.sha256(raw).hexdigest()==h,(h); return raw
def walk(x,y,p=''):
    if isinstance(x,dict) and isinstance(y,dict):
        for k in sorted(set(x)|set(y)): walk(x.get(k,'<absent>'),y.get(k,'<absent>'),p+'/'+str(k))
    elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
        for i,(u,v) in enumerate(zip(x,y)): walk(u,v,p+'['+str(i)+']')
    elif x!=y: print('  DIFF',p,'|',json.dumps(x)[:300],'->',json.dumps(y)[:300])
a=json.loads(ent(W+'/w24h/out/kit_n_go','c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8'))
b=json.loads(ent(W+'/w24i/out/kit_n_go','b42c5b02e400d2bd1f0f423bd434c720826e66c17932fe22ac89b62e326b64b8'))
print('## card c0167f68 -> b42c5b02'); walk(a,b)
for h0,h1,name in (('b6fdc34ecc3008fef7d906a14631d8687382e2c77eede6bf6a1e864f846d201d','550a74347ff6323c9eb33584ea670d002890325e40328498a8dfca4cf301ecb7','indices'),('a1a79d795739361b5d3bbedbddc5317687fdccc7fc92643f92c22ef5eef1bc2d','2f070c270cecaaf93659c97b22c15f4bbc1fc687dcf4398fe79b5ee3047084c6','population')):
    for kit,h in ((W+'/w24h/out/kit_n_go',h0),(W+'/w24i/out/kit_n_go',h1)):
        try: raw=ent(kit,h); print(name,h[:8],'in s.json',len(raw))
        except Exception as e: print(name,h[:8],'not in s.json',repr(e)[:100])
PY
grep -l "550a7434\|2f070c27" $I/out/UPLOADS_24M4I.json && $P -I -s -B -c "
import json;v=json.load(open('$I/out/UPLOADS_24M4I.json'));print(json.dumps(v)[:3000])"
