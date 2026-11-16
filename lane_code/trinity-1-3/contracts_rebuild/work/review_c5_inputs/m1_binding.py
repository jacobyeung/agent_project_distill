import sys,json,itertools
T=sys.argv[1]; sys.path[:0]=[T]
from trace_format.contracts import contract_epoch
from student_pilot.training_contract import audit_training_contract
from student_pilot.phrases import candidate_binding
w=lambda t:'<tool_response>\n'+t+'\n</tool_response>'
ev=[dict(call='<ground obj="lamp" mode="box">',response=w('lamp: frames 2,3 (best 2)\nB1: f1 centre (0.10, 0.00, 2.00) m\nsize 0.40 x 0.40 x 0.40 m\nyaw 0 deg (0 = +x; positive +x toward -z about +y)'))]
base=dict(qid='m4',question='How far is the chair from the table?',options=[],trace_revision='3.14',events=ev,target='<think>\nx\n</think>\n<answer>1</answer>',uses_mask_cache=True)
A=['chair','table']; B=['chair','table','lamp']
fields=['batch_cache_phrases','candidate_phrases','cache_phrases','candidate_manifest']
with contract_epoch(True):
  for combo in itertools.product([None,'A','B'],repeat=4):
    row=dict(base)
    for f,c in zip(fields,combo):
        if c: row[f]={'A':A,'B':B}[c]
    adm=audit_training_contract([row])[0]
    rt=candidate_binding(row,{})
    # runtime admits lamp iff lamp in binding
    rt_ok = rt is not None and 'lamp' in rt
    if (adm is None) != rt_ok: print('DISAGREE',combo,adm,rt)
  # manifest supplied separately
  for combo in itertools.product([None,'A','B'],repeat=2):
    row=dict(base)
    if combo[0]: row['candidate_phrases']={'A':A,'B':B}[combo[0]]
    man={'m4':{'A':A,'B':B}[combo[1]]} if combo[1] else {}
    adm=audit_training_contract([row],man)[0]
    mat=candidate_binding(row,manifest=man)
    print('row',combo[0],'manifest',combo[1],'-> admission',adm,'| materialized binding',mat)
  print('dict without phrases ->',candidate_binding(dict(candidate_manifest={'x':1}),{}))
print('done')
