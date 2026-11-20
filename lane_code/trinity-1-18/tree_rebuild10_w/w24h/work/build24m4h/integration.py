import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import ast,copy,importlib.util
from unittest.mock import patch
sys.path.insert(0,str(kit('n')/'b'))
import rb,rg
from student_pilot.p3_provenance import file_pin
from student_pilot.r1_persisted import scope
from student_pilot import s1_routing
s=J.load(input_file('5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'));s['sources']['ROUTE_direct']['status']='ELIGIBLE'
f=D/'integration';f.mkdir();pin=J.write(f/'s.json',s);point=J.write(f/'point.json',dict(division={}))
pconfig=input_file('b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad')
cfg=dict(s1_routing=dict(selection=pin),streams=dict(pointing=point),r1_training=dict(p_run=dict(config=file_pin(pconfig))))
paths={'5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af':str(input_file('5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'))}
records=[]
with scope(paths),patch.object(s1_routing,'build') as build:
 try:rg.regenerate(cfg,f/'r')
 except ValueError as e:assert str(e)=='R1_ROUTING_SOURCE_STATUS_DIFFERS:ROUTE_direct';records.append(dict(mode='r',refusal=str(e),build_calls=build.call_count))
 else:raise AssertionError('Mode r guard missed')
 assert not build.called
source=ast.parse((kit('n')/'b/a.py').read_text());node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='guarded_selection')
with scope(paths),patch.object(s1_routing,'build') as build:
 ns=dict(original_selection=build)
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(kit('n')/'b/a.py'),'exec'),ns)
 try:ns['guarded_selection'](cfg,f/'q',{},{} )
 except ValueError as e:assert str(e)=='R1_ROUTING_SOURCE_STATUS_DIFFERS:ROUTE_direct';records.append(dict(mode='q',refusal=str(e),build_calls=build.call_count))
 else:raise AssertionError('Mode q guard missed')
 assert not build.called
# A builder failure still leaves the refresh refusal file for the shell publisher.
import i
with patch.object(i,'_refresh',side_effect=ValueError('synthetic-build-input-failure')):
 try:i.refresh({},f/'refresh')
 except ValueError:pass
assert J.load(f/'refresh/r.json')['status']=='REFUSE'
J.write(D/'INTEGRATION.json',dict(status='PASS',records=records,refresh_failure_persisted=True))
print('INTEGRATION PASS',records)
