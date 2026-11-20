from pathlib import Path
import sys,json
from collections import Counter
from fractions import Fraction
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=Path(__file__).parent
sys.path[:0]=[str(D),str(L/'work/tree_r1c')]
from common import J,input_file,kit
from student_pilot import r1_mix
cfg=J.load(kit('n_go')/'k/c.json');card=J.load(input_file(cfg['r2_sampling']['card']['sha256']))
counts={c['type']:int(Fraction(str(c.get('ceiling_rows_per_step',0)))*1000/4) for c in card['cells']}
counts['routing_base']=47898
proof=r1_mix.allocate(card,counts)
indices={'cells':{}};stream_counts=Counter();owner={}
for cell in card['cells']:
 k,s=cell['type'],cell['stream'];offset=stream_counts[s];ids=list(range(offset,offset+counts[k]));indices['cells'][k]=ids;stream_counts[s]+=counts[k]
 owner.update({(s,i):k for i in ids})
count=Counter();steps=[]
# Only replace pin authentication with explicitly synthetic offset pools. The native allocator
# and entire native sampler execute unchanged; no production admission receipt is fabricated.
with patch.object(r1_mix,'validate_binding',return_value=(card,indices,proof)):
 for plan in r1_mix.plans({},dict(stream_counts),200):
  c=Counter((s,owner[s,i]) for s,ids in plan for i in ids);count.update(c)
  steps.append({s+'/'+k:n for (s,k),n in sorted(c.items())})
assert len(steps)==200 and sum(count.values())==200*288 and count['vqa','room_size']==340
before=J.load(D/'CONFIG_DELTA.json')['card_before'];before_proof=r1_mix.allocate(before,counts)
assert before_proof['draws']['room_size']==0 and proof['draws']['room_size']==1700
result=dict(steps=200,counts={s+'/'+k:n for (s,k),n in sorted(count.items())},per_step=steps,configured_counts=counts,allocation=proof,card_sha256=cfg['r2_sampling']['card']['sha256'],production_admission_claimed=False,synthetic_offsets=True,pin_authentication_substitution='validate_binding returns the authenticated card, synthetic nonoverlapping indices and real allocate(card, configured_counts); all sampler logic runs unchanged',counts_basis='Card ceiling_rows_per_step times 1000 / 4. routing_base uses P native count 47898 as an explicit proxy; its 64-row rate is unchanged for every count >=16000. N production counts require native preparation.',code=dict(allocator='work/tree_r1c/student_pilot/r1_mix.py:9',sampler='work/tree_r1c/student_pilot/r1_mix.py:68'))
(D/'N_DRY_COUNT.json').write_text(json.dumps(result,indent=2)+'\n')
print('N native sampler PASS',result['counts'])
