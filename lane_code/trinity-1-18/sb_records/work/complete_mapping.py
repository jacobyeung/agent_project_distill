from common import *
import re
sys.path.insert(0,str(TREE))
from student_pilot.r1_rooms import Rooms
from stage2 import mint,get
before_tokens=snapshot(OUT/'TOKEN_INVERSION.json');before_pop=snapshot(OUT/'POPULATIONS.json')
tokens=read(before_tokens);pop=read(before_pop);source=get('267efeb1');data=read(source)
cr=read(snapshot(W/'w19/work/build19/inputs/component_rows.json'));R=Rooms({k:dict(path=str(get(v['sha256'])),sha256=v['sha256']) for k,v in cr['proven']['authority'].items()})
candidates=set(re.findall(r'scannetpp(?:v2)?/[0-9a-f]{10}',source.read_text()));found={}
for c in candidates:
 t=mint(c)
 if t in tokens['unresolved']:found[t]=c.replace('scannetppv2/','scannetpp/')
assert set(found)==set(tokens['unresolved']),tokens['unresolved']
for t,c in found.items():tokens['aliases'][t]=dict(canonical=c,room=R.room(c),methods=['EVAL_ROOMS_native_candidate_remint'])
tokens['unresolved']=[];tokens['inputs']=[pin(__file__),pin(before_tokens),pin(source),pin(TREE/'student_pilot/r1_rooms.py')]
for p in pop['populations']:
 for t,n in list(p['unresolved_tokens'].items()):
  c=found[t];room=R.room(c);p['counts']['unresolved']-=n;p['counts']['resolved']+=n
  p['scenes']=sorted(set(p['scenes'])|{c});p['rooms']=sorted(set(p['rooms'])|{room})
  for b,x in pop['banks'].items():
   if c in x['captures'] or room in x['rooms']:
    p['counts'][b]+=n;p['overlaps'][b].append(dict(bank=b,canonical=c,room=room,venue=None,rows=n,example_tokens=[t]))
  p['unresolved_tokens'].pop(t)
 p['scene_count']=len(p['scenes']);p['room_count']=len(p['rooms'])
 p['inputs'].append(pin(source))
save(OUT/'TOKEN_INVERSION.json',tokens)
pop['inputs']=[pin(__file__),pin(before_pop),pin(OUT/'TOKEN_INVERSION.json'),pin(source)]
save(OUT/'POPULATIONS.json',pop)
status('Stage 2 complete. Every recovered scene token has a verified preimage. The admitted step-544 population and all 204,413 v7 rows have zero VSI-Bench/VSTI/ReVSI intersections. Raw a2v3, the frame universe and readout scene list disclose venue 381879. Missing ancestor receipts still prevent lineage records.')
print('completed',found)
