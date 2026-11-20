W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
python3 - <<'P'
import json,collections
for f in ('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/UPLOADS_24M4.json','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/UPLOADS_24M3.json'):
    d=json.load(open(f)); c=collections.Counter()
    def walk(x):
        if isinstance(x,dict):
            if 'local_path' in x: n=x.get('name') or x.get('opaque_name'); c[(n.split('/')[0], x['local_path'].rsplit('/',3)[0])]+=1
            else: [walk(v) for v in x.values()]
        elif isinstance(x,list): [walk(v) for v in x]
    walk(d); print(f.rsplit('/',1)[1], dict(c))
P
cd $W/work/conf24m4/pkg; find . -name SHA256SUMS.txt | head; tmux ls | grep tr17; ls -lt $W/w24c/out | head -5
