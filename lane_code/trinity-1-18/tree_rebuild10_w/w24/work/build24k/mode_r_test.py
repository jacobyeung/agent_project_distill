"""Exercise a.py r through the real planner and native routing producer."""
from pathlib import Path
import sys,os,json,base64,hashlib,shutil,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';F=D/'mode_r_test_v5';F.mkdir();(F/'tmp').mkdir()
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(L/'work/tree_r1')]
import joblib as J
from kit24f import reseal
kit=F/'kit';shutil.copytree(L/'work/build24/kits/n',kit)
def cap(p,v):
 doc=json.loads(p.read_text());raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());p.write_text(json.dumps(doc))
spec=J.load(kit/'k/p.json');spec.update(step=600,uploads=[],host_paths={},n_root=str(F/'target'))
(F/'target/u').mkdir(parents=True)
for item in J.load(L/'work/build24i/UPLOADS_n.json')['files']:
 if item['opaque_name'].startswith('u/'):
  (F/'target/u'/item['sha256']).symlink_to(item['local_path'])
  spec['uploads'].append(dict(sha256=item['sha256'],bytes=item['bytes']))
cap(kit/'k/p.json',spec)
cfg=J.load(L/'work/build24/proofs/capacity/400/request_config.json')
from student_pilot.checkpoint_space import plan
from student_pilot.carrier_c1_sweep import recipe_for
cfg.pop('readout',None)
cfg['checkpoint_disk_guard']=plan(recipe_for(cfg),retained_archive_copies=1)
base=J.load(kit/'k/r.json');base['routing_base']=cfg['streams']['routing'];cap(kit/'k/r.json',base)
resolved=J.load(D/'proofs/resolver600_v2/filled_A_resolved.json')
resolved.update(config=cfg,external_metadata=[],kit_sha256=reseal(kit))
resolved['request']=J.load(L/'work/build24/proofs/capacity/400/request.json')
resolved['request'].update(weights=False,device='cpu',memory_gib=16)
J.write(F/'request.json',dict(_resolved=resolved))
boundary=F/'boundary.py'
boundary.write_text('''from pathlib import Path
import sys,runpy,os,json
L=Path('''+repr(str(L))+''');D=L/'work/build24k'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1'),str(Path(sys.argv[1]).parent)]
import native24 as N
N.C.processor_for=N.processor
import rg
native=rg.regenerate
rg.regenerate=lambda cfg,root:native(cfg,root,compare=False)
helper=sys.argv[1];sys.argv=sys.argv[1:]
runpy.run_path(helper,run_name='__main__')
''')
args=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--bind',str(F),str(F),'--bind',str(F),'/tmp/q_22c714e1','--chdir','/tmp/q_22c714e1']
with (F/'run.log').open('w') as log:
 p=subprocess.run(args+[sys.executable,'-B',str(boundary),str(kit/'b/a.py'),'r','/tmp/q_22c714e1/p','/tmp/q_22c714e1/request.json'],
     env={**os.environ,'SLURM_JOB_ID':'94','TMPDIR':'/tmp/q_22c714e1/tmp'},stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,(p.returncode,'see mode_r_test/run.log')
value=J.load(F/'p/routing_selection.json');published=J.load(F/'target/o/94/routing_selection.json');assert value==published
J.write(D/'MODE_R_TEST.json',dict(status='PASS',returncode=p.returncode,rows=value['rows'],regenerated_sha256=value['regenerated_sha256'],
    row_id_digest=value['row_id_digest'],published=True,GO=False,scope='a.py r, native planner, staging hook, scene gate and s1_routing.build; tiny model/stores; production P equality omitted only for fixture'))
print('a.py r native staging and publication PASS',value['rows'])
