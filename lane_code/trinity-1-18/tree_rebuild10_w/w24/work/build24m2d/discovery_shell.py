from common import *
import subprocess,shutil,shlex
F=D/'discovery_shell_v2';F.mkdir();k=F/'kit'
mutable={'p.json','a.py','d.py','g.py','x.py','ep.py','BUILD.json','SHA256SUMS.txt'}
def transport(a,b):
 if Path(a).name in mutable:return shutil.copyfile(a,b)
 os.link(a,b);return b
shutil.copytree(kit('qd'),k,copy_function=transport)
target=F/'target';node=F/'nodes/q_22c714e1_94';node.mkdir(parents=True)
spec=J.load(k/'k/p.json');spec['n_root']=str(target);cap(k,'k/p.json',spec)
prepared=J.load(D/'review_tests/no_pass/node/q_22c714e1_91/v.json')
prepared['r1_training'].pop('review',None);prepared['r1_training'].pop('init_policy',None)
prepared['r1_training']['proof_mode']='q'
J.write(F/'prepared.json',prepared)
selection=J.load(D/'tiny_routing/selected.json');J.write(F/'selected.json',selection)
helper='''from pathlib import Path
import sys,os,json
sys.path[:0]=[str(Path(__file__).resolve().parent),'''+repr(str(T))+''']
import z
root=Path(sys.argv[2]);assert not root.exists();root.mkdir(parents=True)
mode=sys.argv[1];F=Path('''+repr(str(F))+''')
(root/'s').symlink_to('''+repr(str(T))+''',target_is_directory=True)
if mode=='r':
 z.write(root/'routing_selection.json',z.load(F/'selected.json'))
 for name in ('receipt.json','materialization.json'):
  source=F.parent/'tiny_routing/r/p/q/selection'/name
  destination=root/'q/selection'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(source.read_bytes())
else:
 from pl import selection_pin
 pin,source=selection_pin(Path(__file__).resolve().parents[1],root.parent/'routing_selection.json')
 assert z.load(source)==z.load(F/'selected.json')
 cfg=z.load(F/'prepared.json')
 from student_pilot.carrier_c1_run import identity
 from launch_r1.entry import ASSERTIONS
 host=z.write(root/'q/host.json',dict(status='PASS',config_identity=identity(cfg),assertions=dict.fromkeys(ASSERTIONS,True),loader_audit=dict(complete=True),stager='hook',staging_plan_sha256='1'*64,routing_selection=pin,regenerated_sha256=z.load(source)['regenerated_sha256'],routing_substituted=False))
 config=z.write(root/'prepared.json',cfg)
 z.write(root/'q/RESULT.json',dict(status='ADMIT',config=config,host_receipt=host,init_milestone=400))
print('fixture boundary '+mode,flush=True)
'''
(k/'b/a.py').write_text(helper)
(k/'b/d.py').write_text("from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom z import write\nwrite(sys.argv[4],dict(status='PASS',scope='Fixture room-audit boundary; native census tested separately'))\n")
(k/'b/g.py').write_text("print('fixture GPU boundary')\n")
decoded=base64.b64decode(json.loads((k/'k/j.json').read_text())['payload']).decode()
tail=decoded[decoded.index('# Both invocations'):]
assert 'b/t.py' not in tail and 'a.py" r' in tail and 'a.py" q' in tail
bw=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--bind',str(node),str(node),'--bind',str(node),'/tmp/q_22c714e1','--bind',str(target),str(target)]
target.mkdir()
prefix='set -euo pipefail\nQ_KIT='+shlex.quote(str(k))+'\nQ_ROOT='+shlex.quote(str(node))+'\nQ_NS=/tmp/q_22c714e1\nPILOT_VENV='+shlex.quote(str(Path(sys.executable).parent.parent))+'\nBW=('+shlex.join(bw)+')\n'
script=F/'staged.sh';script.write_text(prefix+tail)
(k/'b/x.py').write_text('import subprocess\nraise SystemExit(subprocess.run(["/bin/bash",'+repr(str(script))+']).returncode)\n')
reseal(k);J.write(node/'r.json',{});J.write(F/'request.json',{})
env={**os.environ,'SLURM_JOB_ID':'94','SLURM_TMPDIR':str(F/'nodes'),'PATH':str(Path(sys.executable).parent)+':'+os.environ['PATH']}
with (F/'shell.log').open('w') as log:
 p=subprocess.run(['/bin/bash',str(k/'job.sh'),str(F/'request.json')],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=60)
assert p.returncode==0,(p.returncode,(F/'shell.log').read_text(),(node/'h.log').read_text() if (node/'h.log').exists() else '')
live=target/'o/94/live';assert (live/'WAITING_REVIEW.json').is_file()
assert not (live/'REVIEW_ACCEPTED.json').exists() and not (live/'REVIEW_REFUSED.json').exists()
assert J.load(node/'dr/p/routing_selection.json')==J.load(node/'routing_selection.json')
assert J.load(target/'o/94/routing_selection.json')==selection
assert J.load(target/'o/94/RESULT.json')['discovery'] is True
assert J.load(target/'o/94/RESULT.json')['claims']=='nothing'
assert J.load(node/'p/hr.json')==J.load(node/'p/q/host.json')
assert J.load(k/'k/a.json')['GO'] is False
J.write(D/'DISCOVERY_SHELL_TESTS.json',dict(status='PASS',r_then_q=True,fresh_roots=True,self_selection=True,
 h_real=True,rv_real=True,stops_at='WAITING_REVIEW',no_wait=True,GO=False,discovery=True,claims='nothing',
 outputs_published=True,host_fields_preserved=True,
 boundaries=['Staging and GPU','Preparation produces the retained synthetic review stores and a fixture host receipt','Native regeneration/digest and native donor handover are tested separately']))
print('discovery decoded r/q sequence, proof h, rv stop, and final publication PASS')
