X=/project/community/jjyeung/okh7/x_22c714e1; ls $X/o | tail -4; python3 -I -s -B - <<'PY'
import json,glob,os
X='/project/community/jjyeung/okh7/x_22c714e1'
v=json.load(open(X+'/u/5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'))
s=v['sources']; print(type(s).__name__, len(s))
items=s.items() if isinstance(s,dict) else enumerate(s)
for k,e in list(items)[:16]:
    print(k, json.dumps({a:b for a,b in e.items() if not isinstance(b,(dict,list))} if isinstance(e,dict) else e)[:300])
for j in sorted(os.listdir(X+'/o'))[-3:]:
    p=X+'/o/'+j+'/routing_selection.json'
    if os.path.isfile(p):
        n=json.load(open(p)); print('N',j,list(n)[:20]); ns=n.get('sources'); print(type(ns).__name__, len(ns) if ns else None)
        if ns:
            it=ns.items() if isinstance(ns,dict) else enumerate(ns)
            for k,e in list(it)[:3]: print('  ',k,json.dumps({a:b for a,b in e.items() if not isinstance(b,(dict,list))} if isinstance(e,dict) else e)[:300])
PY
