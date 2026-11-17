python3 - <<'PYEOF'
import json,collections,re,sys
sys.path[:0]=['/project/community/jjyeung/okh7/e6fc152498/p446']
F='/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
M=json.load(open('/project/community/jjyeung/okh7/e6fc152498/p446/items/devs1_routed.json')); by={r['id']:r for r in M['items']}
FAC={'centimet':100,'inch':1/0.0254,'feet':1/0.3048,'foot':1/0.3048,'meter':1,'metre':1}
c=collections.Counter()
for x in map(json.loads,open(F)):
    if x['output']['finish']=='max_calls': continue
    q=by[x['id']]['question'].lower(); unit=next((w for w in FAC if w in q),'?'); f=FAC.get(unit)
    g=[c2['printed']['distance'] for c2 in x['measurements']['M2']['calls'] if c2.get('printed')]
    t=x['output']['text']; m=re.findall(r'<answer>\s*(.*?)\s*</answer>',t,re.S)
    try: a=float(re.match(r'\s*([-\d.]+)',m[-1])[1])
    except Exception: c[(unit,'noparse')]+=1; continue
    if not g: c[(unit,'no_gap_value')]+=1; continue
    d=g[-1]; near=lambda v: abs(a-v)<=0.05*abs(v)+1e-9
    k='metres_unconverted' if near(d) and f!=1 else 'converted' if near(d*f) else 'other'
    c[(unit,k)]+=1
    u=x['measurements'].get('M3',{})
    if u.get('eligible') and not u['follow'] and not u['stick']: c[('M3_other_answered',k)]+=1
for k in sorted(c,key=str): print(k,c[k])
PYEOF
