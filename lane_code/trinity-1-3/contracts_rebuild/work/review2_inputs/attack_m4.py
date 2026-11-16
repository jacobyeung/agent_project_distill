import sys,json
TREE=sys.argv[1]; sys.path[:0]=[TREE]
from trace_format.contracts import contract_epoch
from student_pilot.training_contract import audit_training_contract
w=lambda t:'<tool_response>\n'+t+'\n</tool_response>'
ev=[dict(call='<ground obj="lamp" mode="box">',response=w('lamp: frames 2,3 (best 2)\nB1: f1 centre (0.10, 0.00, 2.00) m\nsize 0.40 x 0.40 x 0.40 m\nyaw 0 deg (0 = +x; positive +x toward -z about +y)'))]
base=dict(qid='m4',question='How far is the chair from the table?',options=[],trace_revision='3.14',events=ev,target='<think>\nx\n</think>\n<answer>1</answer>',uses_mask_cache=True)
with contract_epoch(True):
    print('both: phrases=[chair,table], manifest=[chair,table,lamp] ->',audit_training_contract([dict(base,candidate_phrases=['chair','table'],candidate_manifest=['chair','table','lamp'])]))
    print('phrases only [chair,table] ->',audit_training_contract([dict(base,candidate_phrases=['chair','table'])]))
    print('manifest only [chair,table,lamp] ->',audit_training_contract([dict(base,candidate_manifest=['chair','table','lamp'])]))
