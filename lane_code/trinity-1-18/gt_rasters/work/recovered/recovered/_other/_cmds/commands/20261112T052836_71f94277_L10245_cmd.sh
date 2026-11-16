<!-- recovered by seal_plan: transcript=71f94277 line=10245 utc=2026-11-12T05:28:36.330Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/back_dir/out; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - <<'EOF'
import gzip, json
def show(path, n=2, skip=0):
    with gzip.open(path,'rt') as f:
        for i,line in enumerate(f):
            if i<skip: continue
            if i>=skip+n: break
            r=json.loads(line)
            print('KEYS', sorted(r.keys())[:30])
            for k in ('question','prompt','target','trace','think','answer','messages','text','response'):
                if k in r:
                    v=r[k]; s=v if isinstance(v,str) else json.dumps(v)
                    print('--',k,':',s[:1600])
            print('=====')
show('BACKDIR_T0_gen_r2_packed.jsonl.gz',1,5)
show('BACKDIR_T0_gen_r2_direct.jsonl.gz',1,5)
EOF