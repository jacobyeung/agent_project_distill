export TZ=UTC; date -u +%TZ
H=/project/community/jjyeung/okh7/h_6ed2c7aa
echo "== H"; ls -la --time-style=+%m%d-%H:%M $H 2>&1 | cut -c1-150 | head -14
echo "== H/m400"; ls -la --time-style=+%m%d-%H:%M $H/m400 2>&1 | cut -c1-150 | head -30
echo "== H/m400/*"; ls -la --time-style=+%m%d-%H:%M $H/m400/*/ 2>&1 | cut -c1-150 | head -30
python3 -I - <<'EOF'
import json, glob, os, struct, collections
H='/project/community/jjyeung/okh7/h_6ed2c7aa'
W={'F64':8,'F32':4,'F16':2,'BF16':2,'I64':8,'I32':4,'I16':2,'I8':1,'U8':1,'BOOL':1}
files=sorted(set(glob.glob(H+'/m400/*.safetensors')+glob.glob(H+'/m400/*/*.safetensors')+glob.glob(H+'/*.safetensors')))
tot=collections.Counter(); totn=collections.Counter(); grp=collections.Counter(); nt=0
for f in files[:14]:
    try:
        with open(f,'rb') as h:
            n=struct.unpack('<Q', h.read(8))[0]
            if n>200*2**20: raise ValueError('header too large')
            hd=json.loads(h.read(n))
        c=collections.Counter(); cn=collections.Counter(); k=0
        for name,t in hd.items():
            if name=='__metadata__': continue
            num=1
            for s in t['shape']: num*=s
            c[t['dtype']]+=num*W.get(t['dtype'],0); cn[t['dtype']]+=num; k+=1
            grp['.'.join(name.split('.')[:2])+'|'+t['dtype']]+=num
        nt+=k; tot.update(c); totn.update(cn)
        print(f[len(H):], os.path.getsize(f), 'tensors', k, 'numel', dict(cn), 'bytes', dict(c))
    except Exception as e:
        print(f[len(H):], 'ERR', type(e).__name__, str(e)[:100])
print('TOTAL tensors', nt, 'numel', dict(totn), 'bytes', dict(tot), 'numel_all', sum(totn.values()))
print('groups (prefix|dtype: numel):')
for g,v in grp.most_common(28): print('   ', g[:70], v)
print('== artifact')
try:
    d=json.load(open(H+'/m400/artifact.json'))
    for k in ('trained_groups','full_weights','heads','depth_backing','pose_backing','training_mode','step'):
        print('  ', k, json.dumps(d.get(k))[:700])
except Exception as e:
    print('artifact ERR', type(e).__name__, str(e)[:100])
EOF
