from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p):sha(p) for p in (r/'work/extract/kit_v2').rglob('*') if p.is_file()}
pins[str(Path(__file__))]=sha(Path(__file__))
g=json.loads((r/'work/review/out/v2/GUARD.json').read_text());pins[str(r/'work/review/out/v2/GUARD.json')]=sha(r/'work/review/out/v2/GUARD.json')
original=r/'out/v2/POPULATION.json';pop=json.loads(original.read_text());pins[str(original)]=sha(original)
rows=pop['excluded_from_decision']['rows']
assert len(set(pop['decision']['rows']))==1012 and len(set(pop['decision']['captures']))==204
assert set(pop['decision']['rows']).isdisjoint(rows)
assert set(pop['decision']['rows'])|set(rows)==set(pop['beside']['rows'])
assert set(g['lists']['withheld_80']['hit_captures'])==set(pop['excluded_from_decision']['captures'])
result={'command':'python -B work/check_receipts.py','counts':pop['counts'],'exclusion_pins':{},'input_sha256':pins}
for name,item in g['lists'].items():
 result['exclusion_pins'][name]={k:item[k] for k in ['pin','sha256','hit_captures','hit_rooms','hit_rows']}
 result['input_sha256'][item['path']]=item['sha256']
 if name=='K1_heldout': result['exclusion_pins'][name]['pin_scope']='teacher_k1.sha256 within the pinned authority JSON, not whole-file hash'
(r/'out/check/POPULATION_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(pop['counts'])
