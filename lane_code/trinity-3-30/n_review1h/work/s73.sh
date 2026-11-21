W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z12; B=$Z/work/build24m4z12; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ
ls $B < /dev/null | tr '\n' ' '; echo
for f in ALL_SEALED.json SUITES_SEALED.json findings_sealed/RESULT.json new_verified/RESULT.json e3_sealed/RESULT.json trinity_sealed/RESULT.json FAILURES.json PRIORITY_CONTROLS.json; do echo "#### $f $(sha256sum < $B/$f 2>/dev/null | cut -c1-16) $(stat -c %s $B/$f 2>/dev/null)"; head -c 2500 $B/$f < /dev/null 2>/dev/null; echo; done
echo "== d173966"; ls $W/work/d173966 < /dev/null | tr '\n' ' '; echo
for f in $W/work/d173966/E3.json $W/work/d173966/*/E3.json; do [ -f $f ] && { echo "## $f"; head -c 3000 $f < /dev/null; echo; }; done
echo "== c.json init"
nice -n 10 $P -I -s -B - <<'PY'
import json,base64,hashlib
p='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go/k/c.json'
v=json.load(open(p)); r=base64.b64decode(v['payload']); c=json.loads(r); print('payload',hashlib.sha256(r).hexdigest())
def find(x,keys,path=''):
    if isinstance(x,dict):
        for k,y in x.items():
            if k in keys: print(path+'/'+k, json.dumps(y)[:700])
            find(y,keys,path+'/'+k)
    elif isinstance(x,list):
        for i,y in enumerate(x): find(y,keys,path+'[%d]'%i)
find(c,{'init_policy','handover','handover_receipt','artifact','artifact_sha256','init','export_receipt'})
def rf(x,path=''):
    if isinstance(x,dict):
        for k,y in x.items():
            if k=='remove_files': print(path+'/remove_files',[ (e.get('sha256','')[:8]) for e in y])
            rf(y,path+'/'+k)
    elif isinstance(x,list):
        for i,y in enumerate(x): rf(y,path+'[%d]'%i)
rf(c)
PY
