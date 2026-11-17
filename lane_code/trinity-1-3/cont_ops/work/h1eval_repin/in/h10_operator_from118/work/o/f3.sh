X=/project/community/jjyeung/okh7/x_07ca49df
ls $X | tr '\n' ' '; echo
ls $X/k 2>/dev/null | head; ls $X/u 2>/dev/null | head -20
python3 - <<'P'
import json
k=json.load(open('/project/community/jjyeung/okh7/x_07ca49df/k/b02e4385.json'))
def walk(o,p=''):
    if isinstance(o,dict):
        for a,b in o.items(): walk(b,p+'/'+a)
    elif isinstance(o,list):
        for i,b in enumerate(o[:3]): walk(b,p+'/%d'%i)
    elif isinstance(o,str) and ('rout' in p.lower() or 'rout' in o.lower()): print(p, o[:150])
walk(k)
P
