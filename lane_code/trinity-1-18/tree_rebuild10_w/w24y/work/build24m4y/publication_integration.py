from pathlib import Path
import sys,json,importlib.util,time
from types import SimpleNamespace
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4y'
sys.path[:0]=[str(D),str(L/'out/kit_qd/b'),str(L/'out/rcj')]
from common import *
import z,rv
s=importlib.util.spec_from_file_location('xp',L/'out/rcj/x.py');x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
root=D/'real/node';pool=D/'real/pool';target=pool/'o/173724'
assert not target.exists()
assert (root/'dr/live/s0.json').is_file() and (root/'dr/live/s1.json').is_file()
original={n:z.sha(root/'dr/live'/n) for n in ('s0.json','s1.json')}
load=z.load
class Z:
 sha=staticmethod(z.sha);write=staticmethod(z.write);screen=staticmethod(z.screen)
 @staticmethod
 def load(p):
  return dict(n_root=str(pool),namespace=str(root/'dr')) if str(p).endswith('k/p.json') else load(p)
def check(kit,r,job,action='run'):
 if action in ('types','nsample'):return x.nd_worker(kit,r,action)
 assert action=='check';z.write(r/'proc_check.json',dict(status='PASS',fixture=True));return 0
with patch.object(x,'attach',return_value=Z),patch.object(x,'launch',side_effect=check):
 rc=x.publish(kit('qd'),root,'173724',0)
assert rc==1 # Synthetic P bytes correctly fail the production hash gate.
v=z.load(target/'timings.json')
assert v['aggregate_limit_status']=='PASS' and v['aggregate_publication_bytes']<5_000_000
assert v['publication_errors']==[]
assert {'live/s0.json','live/s1.json'}<=v['files'].keys()
for n,h in original.items():assert z.sha(root/'dr/live'/n)==h
assert z.load(target/'routing_types.json')['status']=='REFUSE' and (target/'proc_check.json').is_file()
for action,field in (('nt','routing_types_refusal'),('ns','nsample')):
 raw=z.load(root/action/'result.json')['traceback']
 expected=z.screen(raw,z.load(kit('qd')/'k/g.json'),z.load(kit('qd')/'b/wh.json'))
 actual=v[field] if field=='routing_types_refusal' else v[field]['reason']
 assert actual=='ValueError: E96:child:1\n'+expected
assert v['routing_types']=='UNAVAILABLE' # Synthetic config cannot pass native_rules.
assert v['rdiff_status']=='UNAVAILABLE' and v['nsample']['status']=='REFUSE'
# Mode q still creates its original remote location, without a local alias.
Q=D/('q_location_'+str(time.time_ns()));Q.mkdir();namespace=Q/'namespace';namespace.mkdir()
with patch.object(rv,'load',return_value=dict(n_root=str(Q/'pool'))):
 live,review=rv.location(kit('qd'),namespace,'173725')
assert live==Q/'pool/o/173725/live' and live.is_dir() and review==Q/'pool/n_r/review.json'
assert not (namespace/'live').exists()
write(D/'PUBLICATION_INTEGRATION.json',dict(status='PASS',production_hash_gate_preserved=True,returncode=rc,aggregate_bytes=v['aggregate_publication_bytes'],live_files=original,host_only_output_created=True,local_receipts_preserved=True,routing_types=v['routing_types'],nsample=v['nsample'],mode_q_location_unchanged=True))
print('Actual outside publisher PASS; live receipts preserved, screened and bounded; synthetic P hash refused; mode q location unchanged')
