"""Bounded local tests; all simulated records remain under tests_local."""
import copy,hashlib,importlib.util,json,os,shutil,subprocess,sys,tarfile,base64,re,tempfile
from pathlib import Path
from packet_config import PINS, fixture, render
from review_policy import build_chain
W=Path(__file__).resolve().parent
if any(W.glob('tests_p3_*')):raise SystemExit('REFUSED: existing fixture outputs; inspect them and use the user cleanup queue before another bulk test')
# One synthetic input view and one READY kit plus trainer trees fit the 300 MB limit.
source_bytes=sum(p.stat().st_size for p in (W/'fixture_h').rglob('*') if p.is_file())
if 2*source_bytes+70_000_000>=280_000_000:raise SystemExit('REFUSED: fixture size exceeds the local test budget')
T=Path(tempfile.mkdtemp(prefix='tests_p3_',dir=W))
B=fixture();H=W/'fixture_h'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n')
def run(args,okay=True):
 r=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if okay and r.returncode:raise RuntimeError(r.stdout+r.stderr)
 if not okay:assert r.returncode!=0,r.stdout
 return r
# Verify transport content without sending anything.
s=(W/'u1.sh').read_text();data=base64.b64decode(s.split("<<'PAYLOAD_FINAL_R1P'\n",1)[1].split('\nPAYLOAD_FINAL_R1P',1)[0]);assert hashlib.sha256(data).hexdigest()==PINS['outer']
from io import BytesIO
with tarfile.open(fileobj=BytesIO(data)) as tf:
 assert len(tf.getmembers())==PINS['members']
 pins=dict(reversed(x.split('  ',1)) for x in tf.extractfile('sums.txt').read().decode().splitlines())
 for n,h in pins.items():assert hashlib.sha256(tf.extractfile(n).read()).hexdigest()==h
print('PASS upload outer SHA, 35 members, inner sums')
# Raw receipt and index bytes are real H1 evidence; relocate paths only for local validation.
N=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/evidence/fix7_selection/orchard_equal_6c18a2bf/o/native')
shutil.copytree(N,T/'native');raw=load(T/'native/receipt.json')
for entry in raw['sources'].values():
 if 'selection' in entry:entry['selection']['path']=str(T/'native'/Path(entry['selection']['path']).name)
write(T/'native/receipt_local.json',raw)
qargs=[sys.executable,'-B',str(B/'q.py'),'--parent',str(H/'k/pool_selection_eac5f9f0.json'),'--indices',str(H/'k'),'--native-receipt',str(T/'native/receipt_local.json'),'--implementation',str(B/'j.json'),'--code-record',str(B/'c.json')]
from selection_runtime import selection_tree
tree=selection_tree(B,T/'tree')
os.environ.update(PYTHONPATH=str(tree),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
qargs+=['--unit-binding',str(B/'u.json'),'--config',str(B/'config.json')]
run(qargs+['--out',str(T/'q')]);q=load(T/'q/q.json');assert q['native_regeneration_executed'] and q['native_unit_regeneration_executed'] and q['selection_sha256']==load(B/'BINDING.json')['selection_sha256']
unit=load(T/'q/r.json')['sources']['U_Faithful'];assert unit['retained']==747
assert load(T/'q/r.json')['implementation']==load(B/'j.json')
print('PASS 747 unit rows regenerated through sealed s1_pool.prepare; native_unit_regeneration_executed=true')
print('PASS q.py raw native receipt projection; final selection',q['selection_sha256'])
# Wrong receipt type and changed ordered index must fail.
bad=qargs.copy();bad[bad.index('--native-receipt')+1]=str(N.parent/'q.json');run(bad+['--out',str(T/'q_bad_report')],False)
idx=next(T/'native'/Path(e['selection']['path']).name for n,e in raw['sources'].items() if 'selection' in e and n!='ROUTE_direct')
old=idx.read_bytes();idx.write_bytes(b'[]\n');run(qargs+['--out',str(T/'q_bad_index')],False);idx.write_bytes(old)
print('PASS negative projection: EQUAL report rejected; altered index rejected')
# Exercise the actual H1 staging check with bounded inherited and changed inputs.
spec=importlib.util.spec_from_file_location('staging',W/'staging_check.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
st=T/'stage';(st/'k').mkdir(parents=True);a=st/'a';a.write_bytes(b'inherited');b=st/'b';b.write_bytes(b'changed')
base={'extra':[dict(dest='a',parts=[str(a)],sha256=sha(a))]};cur=copy.deepcopy(base);cur['extra'].append(dict(dest='b',parts=[str(b)],sha256=sha(b)))
write(st/'base.json',base);write(st/'k/0.json',cur);c=v.main(st,st/'base.json');assert c['missing']==[] and c['verified']==[[str(b)]]
b.write_bytes(b'bad')
try:v.main(st,st/'base.json');raise AssertionError('accepted corrupted changed input')
except ValueError:pass
print('PASS inherited staging checker: changed bytes verified and corruption rejected')
# Use metadata-only H1 evidence copies; no duplicate derived fixture is needed.
old=T/'old';old.mkdir()
for name in ('review.json','staging.json','archive.json','4.json'):
 shutil.copyfile(H/'k'/name,old/name)
ev=T/'e';ev.mkdir();write(ev/'c.json',{'missing':[],'fixture':True})
spec=importlib.util.spec_from_file_location('evidence',W/'evidence_body.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
e.make_records(B,H,old,ev,{'missing':[]},build_chain({'r1.txt':'# GO AFTER FIXES — LOCAL FIXTURE','r2.txt':'# GO AFTER FIXES — LOCAL FIXTURE','r3.txt':'# GO — LOCAL FIXTURE','r4.txt':'# GO — LOCAL ANTECEDENT','r5.txt':'# GO — LOCAL FIXTURE\n'+PINS['identity']},PINS['identity'],PINS['tree'],PINS['outer']))
arc=load(ev/'archive.json');arc['location']=PINS['bundle']+'/t.tar';arc['fixture']=True;write(ev/'archive.json',arc)
# Complete only the two missing fixture members with sentinels. This tests control flow,
# never native data or archive authenticity. Runtime pins remain byte-for-byte original.
source=T/'synthetic_h';source.mkdir()
# Immutable source members share local inodes; only the small manifest is copied.
# The sealed deriver writes independent output bytes and never mutates this input.
for item in H.rglob('*'):
 target=source/item.relative_to(H)
 if item.is_dir():target.mkdir(exist_ok=True)
 elif item.name=='SHA256SUMS.txt':shutil.copyfile(item,target)
 else:os.link(item,target)
manifest=dict(reversed(x.split('  ',1)) for x in (source/'SHA256SUMS.txt').read_text().splitlines())
for name in manifest:
 if not(source/name).exists():
  (source/name).write_bytes(b'LOCAL TEST SENTINEL; NOT PRODUCTION\n');manifest[name]=sha(source/name)
(source/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()))
args=[sys.executable,'-B',str(B/'d.py'),'--source',str(source),'--source-manifest-sha256',sha(source/'SHA256SUMS.txt'),'--packet',str(B),'--bundle',str(B),'--selection-evidence',str(T/'q/q.json'),'--evidence',str(ev)]
# Run the sealed production path with no Slurm identity and a call guard that
# rejects any allocation-time verifier or persistent initializer. No runtime is stubbed.
wrapper="""import os,runpy,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
script=sys.argv[2]
sys.argv=sys.argv[2:]
for key in list(os.environ):
 if key.startswith('SLURM_'):os.environ.pop(key)
def calls(frame,event,arg):
 if event=='call':
  name=Path(frame.f_code.co_filename).name
  func=frame.f_code.co_name
  if (name=='g.py' and func in ('check','persistent_launch')) or (name=='r8.py' and func=='main'):
   raise RuntimeError('Allocation-time initializer reached before submission')
def audit(event,args):
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
   if not Path(os.fsdecode(path)).resolve().is_relative_to(root):raise RuntimeError('Write outside test root')
 if event in ('os.mkdir','os.chmod') and isinstance(args[0],(str,bytes)):
  if not Path(os.fsdecode(args[0])).resolve().is_relative_to(root):raise RuntimeError('Mutation outside test root')
sys.addaudithook(audit);sys.setprofile(calls)
runpy.run_path(script,run_name='__main__')
"""
production=[sys.executable,'-B','-c',wrapper,str(T)]+args[2:]
r=run(production+['--out',str(T/'derived_ready')]);(T/'production_derivation_ready.txt').write_text(r.stdout)
k=T/'derived_ready';result=json.loads(r.stdout)
assert result['status']=='READY' and result['missing_source_members']==[]
assert result['config_identity']==PINS['identity']
launch=load(k/'k/launch.json');cfg=load(k/launch['config']['file'])
assert cfg['h1']['routing_pose_targets'] is True and cfg['h1']['faithful_own_camera_rows'] is False
assert cfg['scheduled_sampling']['max_own_probability']==cfg['recipe']['scheduled_sampling']['max_own_probability']==0
print('PASS READY kit has S2=true, S1=false, and both max_own_probability=0')
assert result['production_authorized'] is False
assert load(k/'k/4.json')['production_go_granted'] is False
assert not (k/'runs').exists() and not (k/'arm').exists()
review=load(k/'k/review.json');assert review['reviewers']==['review_r1p','review_r1p2','review_r1p3','review_r1p4','review_r1p5']
equality=load(k/'k/selection_equality.json');assert equality['native_unit_regeneration_executed'] is True
staged={item['dest']:item for item in load(k/'k/0.json')['extra']}
for name,pin in load(B/'u.json')['artifacts'].items():
 assert staged[pin['path']]['sha256']==pin['sha256'] and staged[pin['path']]['parts']==[str(B/name)]
print('PASS unit artifacts enter the derived staging plan with exact hashes and source paths')
print('PASS production-form evidence reaches READY; final identity; no Slurm identity, g.check, persistent initialization or external writes')
# Exercise the sealed evidence validator on small record copies; do not repeat
# full derivations merely to reject malformed evidence.
from test_evidence import check_mutations
check_mutations(B,k,T)
# Test the deployed driver hash refusal before it reads H or starts derivation.
root=T/'driver_guard';root.mkdir();bun=root/Path(PINS['bundle']).name;bun.mkdir()
(bun/'d.py').write_bytes((B/'d.py').read_bytes()+b'\n# altered\n')
body=render((W/'derive_body.py').read_text()).replace('/project/community/jjyeung/okh7',str(root))
script=T/'derive_guard.py';script.write_text(body)
r=run([sys.executable,'-OO','-B',str(script)],False)
assert 'd.py SHA differs from final archive' in r.stderr
assert not (root/Path(PINS['kit']).name).exists()
print('PASS dv1 refuses altered d.py before source reads or kit creation')
print('Local checks finished; production-form fixture READY; production data authenticity and Orchard proof remain untested.')
print('Test artifacts:',T)
