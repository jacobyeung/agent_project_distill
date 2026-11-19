from pathlib import Path
import json,runpy,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24h'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build24')]
import joblib as J
from launch_r1 import entry
k=L/'work/build24/kits/n';root=Path('/tmp/q_22c714e1/capture')
fixture=dict(status='PASS',config_identity='fixture only',assertions=dict.fromkeys(entry.ASSERTIONS,True),loader_audit={'complete':True},scope='fixture frame-host boundary')
with patch.object(entry,'frame_host',return_value=fixture) as boundary,patch.object(sys,'argv',[str(k/'b/a.py'),'p',str(root)]):
 try:runpy.run_path(str(k/'b/a.py'),run_name='__main__')
 except SystemExit as e:assert e.code==0
 assert boundary.call_count==1
assert J.load(root/'host.json')==fixture
J.write(D/'HOST_CAPTURE_TEST.json',dict(status='PASS',actual_frame_host_result_preserved=True,fixed_file='Q_NS/p/host.json',fixture_boundary=True,production_q_calls_frame_host=False))
print('actual frame_host return capture PASS; mode q producer absent')
