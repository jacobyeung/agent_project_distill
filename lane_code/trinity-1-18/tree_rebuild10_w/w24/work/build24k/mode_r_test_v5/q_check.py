from pathlib import Path
from unittest.mock import patch
import sys,json
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24');sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build24/kits/n/b')]
import z,pl
from launch_r1.entry import check_host_selection
from student_pilot import s1_routing
root=Path('/tmp/q_22c714e1/p/q');cfg=z.load(root/'n.json');value=z.load(root/'selection/receipt.json')
request={'routing_selection':z.write(root.parent/'approved_test.json',z.load(root.parent/'routing_selection.json'))}
result={'assertions':{}}
with patch.object(s1_routing,'build',return_value=value):check_host_selection(cfg,root,request,result)
assert result['assertions']['routing_selection'] is True
bad=z.load(root.parent/'routing_selection.json');bad['regenerated_sha256']='0'*64
request['routing_selection']=z.write(root.parent/'bad_test.json',bad)
try:
 with patch.object(s1_routing,'build',return_value=value):check_host_selection(cfg,root,request,result)
except ValueError as e:assert str(e)=='R1_ROUTING_SELECTION_DIFFERS'
else:raise AssertionError('mismatched regenerated digest passed')
try:pl.selection_pin(L/'work/build24/kits/n')
except ValueError as e:assert str(e)=='R1_ROUTING_SELECTION_PIN_MISSING'
else:raise AssertionError('placeholder passed')
z.write(root.parent/'Q_SELECTION_TEST.json',dict(status='PASS',native_receipt_sha256=z.sha(root/'selection/receipt.json'),fixture_pin_passed=True,placeholder='R1_ROUTING_SELECTION_PIN_MISSING',mutation='R1_ROUTING_SELECTION_DIFFERS',build_boundary='reuse authenticated receipt emitted by a.py r; deterministic native rebuilding tested separately'))
