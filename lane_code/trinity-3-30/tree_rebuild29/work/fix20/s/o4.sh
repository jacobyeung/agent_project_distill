export TZ=UTC; date -u +%TZ
X=/project/community/jjyeung/okh7/x_22c714e1
echo "== live dirs"; ls -d $X/o/*_live 2>/dev/null | tail -8 | tr '\n' ' '; echo
for L in $(ls -d $X/o/*_live 2>/dev/null | tail -8); do J=$(basename $L _live)
  echo "-- $J start: $(head -1 $X/o/$J/j2.log 2>/dev/null | cut -c1-90) | $(grep -h -m2 'stage .* on ' $X/o/$J/j2.log 2>/dev/null | cut -c1-110 | tr '\n' '|')"
  echo "   df: $(head -1 $L/df.txt 2>/dev/null) $(awk '$NF=="/tmp"{print "size="$2" used="$3" avail="$4; exit}' $L/df.txt 2>/dev/null) end: $(sacct -j $J -n -X -P -o State,NodeList,Start,End 2>/dev/null | head -1)"
done
python3 -I - <<'EOF'
import json, os, struct, collections
H='/project/community/jjyeung/okh7/h_6ed2c7aa/m400/model'
C='/project/community/jjyeung/okh7/l_94a76bda/in/cr/'
try:
    d=json.load(open(H+'/model.safetensors.index.json'))
    print('== index metadata', json.dumps(d.get('metadata')), 'weights', len(d.get('weight_map',{})))
    per=collections.Counter(d['weight_map'].values()); print('   per shard', dict(per))
    grp=collections.Counter('.'.join(k.split('.')[:2]) for k in d['weight_map']); print('   groups', dict(grp.most_common(10)))
except Exception as e:
    print('index ERR', type(e).__name__, str(e)[:100])
try:
    print('== config', open(H+'/config.json').read().replace('\n',' ')[:3200])
except Exception as e:
    print('config ERR', type(e).__name__, str(e)[:100])
W={'F64':8,'F32':4,'F16':2,'BF16':2,'I64':8,'I32':4,'I16':2,'I8':1,'U8':1,'BOOL':1}
for label,f in (('heads', C+'9b9e03337df5.p00'), ('encoder', C+'c449bbe907be.p00')):
    try:
        with open(f,'rb') as h:
            n=struct.unpack('<Q', h.read(8))[0]
            if n>200*2**20: raise ValueError('header too large')
            hd=json.loads(h.read(n))
        cn=collections.Counter(); grp=collections.Counter(); k=0
        for name,t in hd.items():
            if name=='__metadata__': continue
            num=1
            for s in t['shape']: num*=s
            cn[t['dtype']]+=num; k+=1; grp[name.split('.')[0]+'|'+t['dtype']]+=num
        print('==', label, os.path.getsize(f), 'tensors', k, 'numel', dict(cn), 'bytes', {a:b*W.get(a,0) for a,b in cn.items()})
        print('   groups', dict(grp.most_common(14)))
    except Exception as e:
        print(label, 'ERR', type(e).__name__, str(e)[:100])
try:
    import base64, glob
    pc=json.load(open(glob.glob('/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_*/config.json')[0]))
    nc=json.load(open('/project/community/jjyeung/okh7/x_22c714e1/n/k/n.json')); nc=json.loads(base64.b64decode(nc['payload'])) if 'payload' in nc else nc
    vc=json.load(open('/project/community/jjyeung/okh7/x_22c714e1/o/174246/live/v.json'))
    cut=lambda r:{k:v for k,v in r.items() if k not in ('mix','milestones')}
    a,b,c=cut(pc['recipe']),cut(nc['recipe']),cut(vc['recipe'])
    print('== recipe compare (minus mix, milestones): donor==kit', a==b, 'donor==job', a==c, 'keys', sorted(a))
    T=('wall_seconds','stop_before_seconds','resume_every_seconds','export_at_stop')
    print('   donor timing', {k:a.get(k) for k in T}, 'types', [type(a.get(k)).__name__ for k in T])
    b2=dict(b, resume_every_seconds=10800); print('   with interval 10800: equal', a==b2, 'differing', [k for k in a if a[k]!=b2.get(k)])
    print('   donor keys absent in kit cfg', sorted(set(pc)-set(nc))[:20], 'kit keys absent in donor', sorted(set(nc)-set(pc))[:20])
except Exception as e:
    print('recipe ERR', type(e).__name__, str(e)[:120])
EOF
