W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out; cd $W; for K in kit_qd kit_n_go; do echo "== $K"; python3 -c "
import json,sys;d=json.load(open('$K/k/p.json'));print({k:(v if not isinstance(v,(dict,list)) else type(v).__name__+str(len(v))) for k,v in d.items() if k in ('local_map','link_checks','namespace','p_root','n_root','pool')})"; done
mkdir -p /tmp/tr16x && cd /tmp/tr16x && tar xf $W/tree_rebuild_b24m2d_a44386aa.tar --wildcards '*q/k/p.json' '*n/k/p.json' 2>&1 | head -3; find /tmp/tr16x -name p.json | head; for f in $(find /tmp/tr16x -name p.json); do python3 -c "
import json;d=json.load(open('$f'));print('$f',d.get('local_map'),len(d.get('link_checks',[])))"; done
python3 - <<'PY'
import json,base64
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_qd/k/j.json'));s=base64.b64decode(d['payload']).decode()
i=s.find('k/0.json');print(s[max(0,i-700):i+300])
PY
