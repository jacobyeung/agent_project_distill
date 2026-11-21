export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/174134; date -u +%TZ
squeue -j 174134 -h -o "%i %T %M %N"
python3 - <<'PY'
import json
O='/project/community/jjyeung/okh7/x_22c714e1/o/174134'
d=json.load(open(O+'/q0.json'))
def show(o,ind=0,depth=0):
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(v,(dict,list)) and depth<2:
                print(' '*ind+str(k)+': '+type(v).__name__+' len '+str(len(v))); show(v,ind+2,depth+1)
            else: print(' '*ind+str(k)+' = '+str(v)[:300])
    elif isinstance(o,list):
        for i,v in enumerate(o[:6]):
            print(' '*ind+'['+str(i)+'] '+str(v)[:300])
show(d)
PY
echo ==== q.steps; cat $O/q.steps | tail -c 3600
echo ==== srun node listing
timeout 60 srun --overlap --jobid 174134 -N1 -n1 bash -c 'hostname -s; Q=/tmp/q_22c714e1_174134; ls -la $Q | head -40; echo ---- p; ls -la $Q/p | head; echo ---- p/q; ls -la $Q/p/q | head -60; echo ---- p/q/p; ls -la $Q/p/q/p 2>/dev/null | head -40; df -h /tmp | tail -1; nproc; uptime'
