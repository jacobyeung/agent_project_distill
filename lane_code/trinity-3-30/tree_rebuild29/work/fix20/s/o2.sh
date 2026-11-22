export TZ=UTC; date -u +%TZ
P=/project/community/jjyeung/okh7/x_ee227714; R=$P/runs/6ed2c7aa
X=/project/community/jjyeung/okh7/x_22c714e1; L=$X/o/174246_live
echo "== L"; ls -la --time-style=+%H:%M:%S $L 2>&1 | cut -c1-140 | head -22
echo "== df"; cat $L/df.txt 2>&1 | cut -c1-200 | head -16
echo "== steps"; cat $X/o/174246/live/174246.steps 2>&1 | cut -c1-170 | tail -22
echo "== copy"; cat $X/o/174246/live/copy.json 2>&1 | cut -c1-900; echo
echo "== P/o"; ls -la --time-style=+%m%d-%H:%M $P/o 2>&1 | awk '{print $5,$7}' | head -70 | tr '\n' ';'; echo
echo "== R/inputs"; ls -la --time-style=+%m%d-%H:%M $R/inputs 2>&1 | cut -c1-160 | head -10
echo "== attempt P"; cat $R/attempt_172660.json | cut -c1-900; echo; cat $R/h1_stop_000600.json | cut -c1-300; echo
echo "== P steps"; grep -h -i 'free\|GiB\|checkpoint\|ck\|stop' $P/o/172660.steps $P/o/172660.w.steps 2>/dev/null | cut -c1-200 | head -24
python3 -I - <<'EOF'
import json, glob, os, re
P='/project/community/jjyeung/okh7/x_ee227714'; R=P+'/runs/6ed2c7aa'
K=['required_bytes','available_bytes','state_tensor_bytes','export_tensor_bytes','state_bytes','export_bytes','remaining_full_states','remaining_weight_exports','policy','completed','retained_archive_bytes','native_remaining_bytes']
T=['wall_seconds','stop_before_seconds','resume_every_seconds','milestones','export_at_stop','steps','world_size']
print('== m400')
def walk(d, path='', out=None, depth=0):
    out=[] if out is None else out
    if isinstance(d, dict) and depth<7:
        if 'bytes' in d and type(d['bytes']) is int: out.append((path, d['bytes']))
        for k,v in d.items(): walk(v, path+'/'+str(k), out, depth+1)
    elif isinstance(d, list) and depth<7:
        for i,v in enumerate(d[:40]): walk(v, path+'/'+str(i), out, depth+1)
    return out
for n in ('artifact.json','e.json','RP.json'):
    try:
        d=json.load(open(R+'/m400/'+n))
        print(n, sorted(d)[:40] if isinstance(d, dict) else type(d))
        w=walk(d)
        for p,b in w[:24]: print('   ', p[-70:], b)
        if w: print('    sum bytes', sum(b for _,b in w), 'n', len(w))
        for k in ('disk_guard','space','step','dtype','export_dtype','parameters','parameter_count','tensors'):
            if isinstance(d, dict) and k in d: print('   ', k, json.dumps(d[k])[:500])
    except Exception as e:
        print(n, 'ERR', type(e).__name__, str(e)[:100])
print('== P config')
for c in sorted(glob.glob(R+'/inputs/*/config.json'))[:3]:
    try:
        d=json.load(open(c))
        print(c[len(R):][:60], json.dumps(d.get('checkpoint_disk_guard')), json.dumps({k:(d.get('recipe') or {}).get(k) for k in T}), 'sched', json.dumps(d.get('schedule')), 'out', str(d.get('output'))[-40:], 'r2p', 'r2_persistence' in d, 'r1', 'r1_training' in d, 'r2id', 'r2_identity' in d)
    except Exception as e:
        print(c[len(R):], 'ERR', type(e).__name__, str(e)[:100])
print('== metrics')
try:
    rows=[]; n=0; head=None
    ck=re.compile(r'"checkpoint_seconds": ([0-9.eE+-]+)'); ex=re.compile(r'"export_seconds": ([0-9.eE+-]+)'); st=re.compile(r'"step": (\d+)'); ws=re.compile(r'"wall_seconds": ([0-9.eE+-]+)')
    with open(R+'/metrics_172660.jsonl', errors='replace') as h:
        for line in h:
            n+=1
            if head is None: head=line[:260]
            c=max([float(x) for x in ck.findall(line)] or [0]); e=max([float(x) for x in ex.findall(line)] or [0])
            if c>0 or e>0:
                s=st.search(line); rows.append((int(s.group(1)) if s else -1, round(c,1), round(e,1)))
    print('lines', n, 'head', head)
    print('saves (step, checkpoint_s, export_s):', rows[:60], 'count', len(rows))
except Exception as e:
    print('metrics ERR', type(e).__name__, str(e)[:100])
print('== guard events in P logs')
dec=json.JSONDecoder()
for t in sorted(glob.glob(P+'/o/*')):
    if not os.path.isfile(t) or os.path.getsize(t)>400*2**20 or not t.rsplit('.',1)[-1] in ('err','out','log','txt'): continue
    n=0
    try:
        with open(t, errors='replace') as h:
            for line in h:
                i=line.find('_disk_guard"')
                if i<0: continue
                j=line.rfind('{', 0, i)
                try:
                    g,_=dec.raw_decode(line[j:]); n+=1
                    if n<=12: print(os.path.basename(t), g.get('event'), json.dumps({k:g.get(k) for k in K}))
                    if n==1: print('   ranks', json.dumps([{k:r.get(k) for k in ('rank','state_tensor_bytes','export_tensor_bytes','free_bytes')} for r in g.get('ranks',[])]))
                except Exception as e:
                    print(os.path.basename(t), 'bad', len(line), line[max(0,i-40):i+120])
        print(os.path.basename(t), os.path.getsize(t), 'guard events', n)
    except Exception as e:
        print(os.path.basename(t), 'ERR', type(e).__name__, str(e)[:100])
EOF
