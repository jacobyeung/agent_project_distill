import sys
sys.path[:0]=['/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build21', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build22', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24d', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/tree_r1']
from common import *
import sqlite3,subprocess,copy
F=D/'tiny_routing';F.mkdir()
cfg=J.load(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')/'work/build24/proofs/capacity/400/request_config.json')
receipt=J.load(cfg['streams']['routing']['path']);source=Path(receipt['database']['path'])
db=F/'legacy.sqlite'
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(db) as b:
 b.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
 row=a.execute('SELECT i,row,target FROM rows ORDER BY i LIMIT 1').fetchone()
 b.execute('INSERT INTO rows VALUES(?,?,?)',row)
receipt.update(database=J.write(F/'unused.json',{}))
receipt.update(database=dict(path=str(db),sha256=J.sha(db)),count=1)
first=json.loads(row[1]);receipt['types']={first['routing']['question_type']+':'+first['routing']['category']:1}
cfg['streams']['routing']=J.write(F/'legacy.json',receipt)
J.write(F/'cfg.json',cfg)
runner=F/'run.py';runner.write_text('''from pathlib import Path
import sys,json,os
L=Path('''+repr(str(L))+''');F=Path('''+repr(str(F))+''')
sys.path[:0]=['/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24',str(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')/'work/build21'),str(L/'work/tree_r1'),str(L/'out/kit_qd/b')]
import native24 as N
N.C.processor_for=N.processor
from z import load,write
from i import refresh
from student_pilot.p3_provenance import file_pin,pinned
from launch_r1.entry import check_host_selection
import rg
root=Path('/tmp/qd/p/q');root.mkdir(parents=True)
cfg=load(F/'cfg.json')
pin=write(root.parent/'input.json',cfg)
refreshed=refresh(dict(config=pin,staged_pins=[pin]),root.parent/'refresh')
cfg=load(pinned(refreshed['config']))
if sys.argv[1]=='r':
 value=rg.regenerate(cfg,root,compare=False)
 write(F/'selected.json',value)
else:
 request=dict(routing_selection=file_pin(F/'selected.json'))
 host=dict(assertions={});check_host_selection(cfg,root,request,host)
 assert host['assertions']['routing_selection']
 write(F/'q_result.json',host)
''')
for mode in ('r','q'):
 node=F/mode;node.mkdir()
 cmd=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(F),str(F),'--tmpfs','/tmp','--bind',str(node),'/tmp/qd',sys.executable,'-B','-s',str(runner),mode]
 with (F/(mode+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 assert r.returncode==0,(mode,(F/(mode+'.log')).read_text()[-2500:])
selected=J.load(F/'selected.json');assert selected['rows']==2
J.write(D/'ROUTING_TESTS.json',dict(status='PASS',rows=selected['rows'],native_builder=True,native_q_digest_check=True,
 regenerated_sha256=selected['regenerated_sha256'],logical_output=selected['logical_output'],fresh_roots=['r','q'],
 stand_ins=['One retained synthetic legacy row plus one native pool row','Fixture processor','Production P-row comparison tested separately; unavailable production data is not claimed']))
print('native mode-r regeneration and native q self-selection check PASS',selected['rows'])
