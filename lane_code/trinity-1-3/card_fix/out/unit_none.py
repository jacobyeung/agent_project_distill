"""Unit-conversion baseline of step 544 on UNPERTURBED reads (card R1, gate "Units").
unit.py of h10_score/work/results/170706 with one change: reads are split by mode, and capped reads are counted.
Run where the scored file is (Orchard): python3 unit_none.py
An item counts as converted when the read answers with a served gap value and the answer equals the printed
metres times the question's unit factor within 5%."""
import json,collections,re
W='/project/community/jjyeung/okh7/e6fc152498'
F=W+'/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
M=json.load(open(W+'/p446/items/devs1_routed.json')); by={r['id']:r for r in M['items']}
FAC={'centimet':100,'inch':1/0.0254,'feet':1/0.3048,'foot':1/0.3048,'meter':1,'metre':1}
c=collections.Counter(); per_item={}
for x in map(json.loads,open(F)):
    mode=x['mode']; q=by[x['id']]['question'].lower(); unit=next((w for w in FAC if w in q),'?'); f=FAC.get(unit)
    c[(mode,unit,'reads')]+=1
    if x['output']['finish']=='max_calls': c[(mode,unit,'capped')]+=1; k='capped'
    else:
        g=[c2['printed']['distance'] for c2 in x['measurements']['M2']['calls'] if c2.get('printed')]
        m=re.findall(r'<answer>\s*(.*?)\s*</answer>',x['output']['text'],re.S)
        try: a=float(re.match(r'\s*([-\d.]+)',m[-1])[1])
        except Exception: a=None
        if a is None: k='noparse'
        elif not g: k='no_gap_value'
        else:
            d=g[-1]; near=lambda v: abs(a-v)<=0.05*abs(v)+1e-9
            k='metres_unconverted' if near(d) and f!=1 else 'converted' if near(d*f) else 'other'
        c[(mode,unit,k)]+=1
    if mode=='none': per_item[x['id']]=dict(unit=unit,room=by[x['id']].get('room_key') or by[x['id']].get('room'),cls=k)
for k in sorted(c,key=str): print(k,c[k])
nm=[v for v in per_item.values() if v['unit'] not in ('meter','metre')]
print('unperturbed non-metre items',len(nm),'converted',sum(v['cls']=='converted' for v in nm),
      'answered with a gap value',sum(v['cls'] in ('converted','metres_unconverted','other') for v in nm),'rooms',len({v['room'] for v in nm}))
json.dump(per_item,open('unit_none_per_item.json','w'),indent=0)
