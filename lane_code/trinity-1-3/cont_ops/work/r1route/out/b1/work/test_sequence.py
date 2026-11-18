import sys,json,unittest,tarfile,io,re,hashlib,tempfile,ast
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).resolve().parents[1];O=W;P=O/'src'
sys.path[:0]=[str(O),str(P/'b'),str(P/'tree'),str(P)]
import tower_sequence as T
from orchard_h10.common import ORDER
T.ORDER=ORDER
from orchard_h10.common import read_config,canonical,sha,write,opaque
from orchard_h10.job import check_inputs,verify_config

class Sequence(unittest.TestCase):
 def fresh(self):return Path(tempfile.mkdtemp(prefix='s_',dir=W/'work/tmp'))
 def config(self):
  root=self.fresh();settings=root/'settings.json';write(settings,dict(arm='own_depth',save_own_depth=False,stage1_select_rule='null_argmax',perception_memo_modules=['g3t'],perception_memo='off',perception_memo_verify_ids=[]))
  return dict(package=str(P),output=str(root/'r'),settings=str(settings),python=sys.executable,
     export='e',binding='b',export_pin='p',plan_sha256='a',inputs_sha256='b',operator_sha256=sha(O/'tower_sequence.py'),prefix=[],device='cpu')
 def test_empty_root_payload_pins_admission_and_args(self):
  root=self.fresh();package=root/'p';package.mkdir()
  with tarfile.open(O/'package/0.tgz') as tar:
   for m in tar:
    assert m.isfile() and '..' not in Path(m.name).parts
    dest=package/m.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(tar.extractfile(m).read())
  cfg=read_config(O/'package');verify_config(cfg)
  for name,pin in cfg['payload_pins'].items():self.assertEqual(sha(package/name),pin['sha256'])
  inp=json.loads((O/'inputs_tower.json').read_text());admit=root/'a';admit.mkdir()
  (admit/'export.json').write_bytes((O/'export_544.json').read_bytes())
  check_inputs(inp,cfg,package=root)
  settings=root/'s.json';write(settings,dict(arm='own_depth',save_own_depth=False,stage1_select_rule='null_argmax',perception_memo_modules=['g3t'],perception_memo='off',perception_memo_verify_ids=[]))
  rc=dict(package=str(package),output=str(root/'r'),settings=str(settings),python=sys.executable,
   export='e',binding='b',export_pin='p',plan_sha256=cfg['plan_sha256'],inputs_sha256=canonical(inp),operator_sha256=sha(O/'tower_sequence.py'),prefix=[],device='cpu')
  result=T.rehearsal(rc)
  self.assertEqual(sum(r['expected'] for r in result),786)
  self.assertEqual(len(result),2)
  for i,read in enumerate(result):
   self.assertEqual(read['settings']['perception_memo_modules'],['g3t'])
   self.assertEqual(read['settings']['perception_memo'],'verify' if i==1 else 'on')
   ids=[v['id'] for v in json.loads((package/'items/devs1_routed.json').read_text())['items'] if v['question_type']=='object_abs_distance'][:30]
   self.assertEqual(read['settings']['perception_memo_verify_ids'],ids if i==1 else [])
  write(O/'LOCAL_REHEARSAL.json',dict(passed=True,root=str(root),real_model_reads=False,
    scope='Empty-root payload extraction, every payload pin, step-544 admission, two settings/identities, two workers, six type journals.',workers=result))
 def test_order_complete_and_no_partial_merge(self):
  cfg=self.config();seen=[]
  def runner(c,cards,end,**kw):
   i=int(Path(c['output']).name);seen.extend((i,T.ORDER.index(t)) for t in c['types'])
   n=636 if i==0 else 150
   return dict(completed=n,expected=n,complete=True,failure=None)
  r=T.run(cfg,2000,['0'],runner=runner,clock=lambda:0)
  self.assertEqual(seen,[(1,3),(0,3),(0,0),(0,1),(0,2),(0,4)]);self.assertEqual(seen,list(T.SCHEDULE));self.assertEqual(r['completed'],786);self.assertTrue(r['complete'])
  cfg=self.config()
  def partial(*a,**k):return dict(completed=10,expected=150,complete=False,failure=None)
  r=T.run(cfg,2000,['0'],runner=partial,clock=lambda:0)
  self.assertFalse(r['complete']);self.assertEqual(r['completed'],10);self.assertEqual(len(r['segments']),1)
 def test_clean_stop_and_identity_refuses(self):
  cfg=self.config();r=T.run(cfg,1800,['0'],runner=lambda *a,**k:self.fail('no time'),clock=lambda:1)
  self.assertFalse(r['complete']);self.assertEqual(r['completed'],0)
  path=Path(cfg['output'])/'metadata/reads/0/metadata/0.json';s=json.loads(path.read_text());s['stage1_select_rule']=T.RULES[1];write(path,s)
  with self.assertRaisesRegex(ValueError,'identity'):T.prepare(cfg)
 def test_batch_and_private_helpers_authenticate(self):
  cfg=read_config(O/'package');receipt=json.loads((O/'package/PACKAGE.json').read_text())
  for n,h in receipt['files'].items():self.assertEqual(sha(O/'package'/n),h)
  batch=(O/'package/BATCH.sh').read_text();opaque([batch])
  raw=bytes.fromhex(re.search(r"bytes.fromhex\('([0-9a-f]+)'\)",batch)[1])
  with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
   self.assertEqual(tar.extractfile('7.py').read(),(O/'tower_sequence.py').read_bytes())
   self.assertEqual(tar.extractfile('0.py').read(),(O/'tower_bootstrap.py').read_bytes())
   self.assertEqual(json.load(tar.extractfile('0.json'))['plan_sha256'],cfg['plan_sha256'])
 def test_bootstrap_intercepts_only_allocation_dispatch(self):
  source=ast.parse((O/'tower_bootstrap.py').read_text());fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='make_dispatch')
  root=self.fresh();(root/'a').mkdir();write(root/'a/1.json',dict(action=1,config={}))
  (root/'7.py').write_bytes((O/'tower_sequence.py').read_bytes())
  digest=sha(root/'7.py')
  calls=[];ns=dict(root=root,json=json,sha=sha,operator_sha256=digest,original=lambda argv,*a,**k:calls.append(argv))
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'bootstrap','exec'),ns)
  dispatch=ns['make_dispatch'](root,ns['original'],digest)
  dispatch(['prefix','python',str(root/'a/5.py'),str(root/'a/0.json')])
  self.assertEqual(calls[-1][-2],str(root/'a/5.py'))
  dispatch(['prefix','python',str(root/'a/5.py'),str(root/'a/1.json')])
  self.assertEqual(calls[-1][-2],str(root/'7.py'))
  self.assertEqual(json.loads((root/'a/1.json').read_text())['config']['operator_sha256'],digest)

if __name__=='__main__':unittest.main(verbosity=2)
