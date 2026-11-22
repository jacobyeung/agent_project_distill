export TZ=UTC; date -u +%TZ
P=/project/community/jjyeung/okh7/x_ee227714; R=$P/runs/6ed2c7aa
X=/project/community/jjyeung/okh7/x_22c714e1
echo "== R"; ls -la --time-style=+%m%d-%H:%M $R 2>&1 | cut -c1-160 | head -45
echo "== R/_superseded"; ls -la --time-style=+%m%d-%H:%M $R/_superseded 2>&1 | cut -c1-160 | head -24
echo "== R/persist"; ls -la --time-style=+%m%d-%H:%M $R/persist 2>&1 | cut -c1-160 | head -30
echo "== live"; ls -la --time-style=+%H:%M:%S $X/o/174246/live 2>&1 | cut -c1-160 | head -20
echo "== P/o"; ls $P/o 2>&1 | head -12
echo "== P/n/k"; ls -la --time-style=+%m%d-%H:%M $P/n/k 2>&1 | cut -c1-120 | head -24
echo "== node"; scontrol show node orchard-community-3 2>&1 | tr ' ' '\n' | grep -i -E 'TmpDisk|RealMemory|Partitions|^State=' | head -8
echo "== sinfo"; sinfo -N -h -o '%N %P %d %G %t' 2>&1 | sort -u | cut -c1-120 | head -40
python3 -I - <<'EOF'
import json, glob, os, base64
R='/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa'
P='/project/community/jjyeung/okh7/x_ee227714'
X='/project/community/jjyeung/okh7/x_22c714e1'
K=['required_bytes','available_bytes','state_tensor_bytes','export_tensor_bytes','state_bytes','export_bytes','remaining_full_states','remaining_weight_exports','policy','completed','retained_archive_bytes','native_remaining_bytes','serialized_state_bytes']
T=['wall_seconds','stop_before_seconds','resume_every_seconds','milestones','export_at_stop','steps','world_size']
print('== complete.json')
ms=sorted(glob.glob(R+'/checkpoint_*/complete.json')+glob.glob(R+'/_superseded/*/complete.json'))
first=True
for m in ms[:20]:
    try:
        d=json.load(open(m)); g=d.get('disk_guard') or {}
        print(m[len(R):], 'step', d.get('step'), json.dumps({k:g.get(k) for k in K}))
        if first:
            first=False
            print('  ranks', json.dumps([{k:r.get(k) for k in ('rank','state_tensor_bytes','export_tensor_bytes','free_bytes')} for r in g.get('ranks',[])]))
            c=d.get('config') or {}
            print('  cfg.guard', json.dumps(c.get('checkpoint_disk_guard')), 'cfg.recipe', json.dumps({k:(c.get('recipe') or {}).get(k) for k in T}), 'output', c.get('output'), 'sched', json.dumps(c.get('schedule')))
    except Exception as e:
        print(m[len(R):], 'ERR', type(e).__name__, str(e)[:100])
print('== binding configs')
for b in sorted(glob.glob(R+'/binding_config_*.json'))[:4]:
    try:
        c=json.load(open(b)); c=c.get('config',c)
        print(os.path.basename(b)[:40], os.path.getsize(b), json.dumps(c.get('checkpoint_disk_guard')), json.dumps({k:(c.get('recipe') or {}).get(k) for k in T}))
    except Exception as e:
        print(b[len(R):], 'ERR', type(e).__name__, str(e)[:100])
print('== kit configs')
for root in (P, X):
    for n in ('c','n'):
        f=root+'/n/k/'+n+'.json'
        try:
            d=json.load(open(f))
            if 'payload' in d: d=json.loads(base64.b64decode(d['payload']))
            print(f[len('/project/community/jjyeung/okh7/'):], json.dumps(d.get('checkpoint_disk_guard')), json.dumps({k:(d.get('recipe') or {}).get(k) for k in T}), 'sched', json.dumps(d.get('schedule')))
        except Exception as e:
            print(f[-30:], 'ERR', type(e).__name__, str(e)[:100])
print('== live v.json')
def find(d, key, path='', out=None, depth=0):
    out=[] if out is None else out
    if isinstance(d, dict) and depth<6:
        for k,v in d.items():
            if k==key: out.append((path+'/'+k, v))
            find(v, key, path+'/'+k, out, depth+1)
    return out
for f in (X+'/o/174246/live/v.json', X+'/o/174246/v.json'):
    try:
        raw=open(f).read(); d=json.loads(raw)
        if isinstance(d, dict) and 'payload' in d: d=json.loads(base64.b64decode(d['payload']))
        print(f[-20:], len(raw), sorted(d)[:12] if isinstance(d, dict) else type(d))
        for p,v in find(d,'checkpoint_disk_guard')[:3]: print('  ',p, json.dumps(v))
        for p,v in find(d,'recipe')[:3]: print('  ',p, json.dumps({k:v.get(k) for k in T}) if isinstance(v, dict) else type(v))
    except Exception as e:
        print(f[-20:], 'ERR', type(e).__name__, str(e)[:100])
print('== t.log guard events')
for t in sorted(glob.glob(P+'/o/*/t.log')+glob.glob(P+'/o/*/live/t.log'))[:6]:
    n=0
    try:
        with open(t, errors='replace') as h:
            for line in h:
                if '_disk_guard"' in line[:60]:
                    try:
                        g=json.loads(line); n+=1
                        if n<=14: print(t[len(P):], g.get('event'), json.dumps({k:g.get(k) for k in K[:8]}), json.dumps(g.get('completed')))
                    except Exception as e:
                        print(t[len(P):], 'bad line', len(line))
        print(t[len(P):], os.path.getsize(t), 'guard events', n)
    except Exception as e:
        print(t[len(P):], 'ERR', type(e).__name__, str(e)[:100])
EOF
echo "== R/m400"; ls -la --time-style=+%m%d-%H:%M $R/m400 2>&1 | cut -c1-160 | head -12
