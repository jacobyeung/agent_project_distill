<!-- recovered by seal_plan: transcript=71f94277 line=11731 utc=2026-11-12T11:07:04.938Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/leg_s1_tree; ls work | grep -E "^kit_s1_release" | tail -3; K=$(ls -d work/kit_s1_release_* | tail -1); echo $K; ls $K/k | head -20; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - "$K" <<'EOF'
import json,sys,glob,os
K=sys.argv[1]
for p in sorted(glob.glob(os.path.join(K,'k','*.json'))):
    try: d=json.load(open(p))
    except Exception as e: continue
    def walk(x,path=''):
        if isinstance(x,dict):
            for k,v in x.items():
                if 'route' in k.lower() or 'tool_mode' in k.lower():
                    s=json.dumps(v)
                    print(os.path.basename(p), path+'/'+k, s[:900])
                else: walk(v,path+'/'+k)
        elif isinstance(x,list):
            for i,v in enumerate(x[:3]): walk(v,path+'[%d]'%i)
    walk(d)
EOF