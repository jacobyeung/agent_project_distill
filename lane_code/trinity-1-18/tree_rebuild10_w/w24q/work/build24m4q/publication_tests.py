import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
import unittest,importlib.util,copy,gzip
from types import SimpleNamespace
from unittest.mock import patch
import ep,ch

def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
x=module('pub_x',L/'out/rcj/x.py');old=module('pub_old',L/'attic/build24m4q/out/rcj/x.py')
F=D/('publication_'+str(time.time_ns()));F.mkdir()

class Tests(unittest.TestCase):
 def publication(self,module,label,mode='r',rc=0,gate=True,proc_rc=0,rd_rc=0,chain='PASS',preexisting=True,ep_bad=False,target_bad=False,extra=0):
  root=F/label;root.mkdir();remote=root/'remote';target=remote/'o/123';native=root/('dr/p/q' if mode=='r' else 'r');native.mkdir(parents=True)
  bases=[native/'base',native/'selection'] if mode=='r' else [native]
  for b in bases:b.mkdir(exist_ok=True);(b/'rows.sqlite').write_bytes(b'SQLite format 3\x00fixture')
  z.write(root/'mode.json',dict(mode=mode));z.write(remote/'rcj/P_SAMPLE_I.json',{})
  if preexisting and mode=='r':z.write(root/'chain.json',dict(status=chain,count=7));(root/'cc.json.gz').write_bytes(gzip.compress(b'{}'))
  def load(p):return dict(n_root=str(remote)) if str(p).endswith('k/p.json') else z.load(p)
  def sha(p):return x.DB if Path(p)==bases[0]/'rows.sqlite' and gate else z.sha(p)
  def put(p,v):
   if target_bad and Path(p).is_relative_to(target):raise PermissionError('fixture destination')
   return z.write(p,v)
  Z=SimpleNamespace(load=load,sha=sha,write=put);calls=[]
  def rd(*args):
   calls.append('rdiff');(root/'rd.log').write_text('diff\n')
   if extra:(target/'rd0').mkdir();(target/'rd0/r.json').write_bytes(b'x'*extra)
   return rd_rc
  def launch(*args,**kw):
   calls.append(kw['action'])
   if kw['action']=='chain':z.write(root/'chain.json',dict(status=chain,count=9));return 0
   z.write(root/'proc_check.json',dict(status='FAIL' if proc_rc else 'PASS'));(root/'pc_n.log').write_text('child\n');return proc_rc
  def ns(*args):
   for n in ('n_sample.json','nd.json','na.json.gz'):(target/n).write_bytes(b'{}\n')
   return dict(status='PASS',task_i='PASS',task_ii='PASS',task_iii='PASS',files=['n_sample.json','nd.json','na.json.gz'])
  def types(*args):z.write(target/'routing_types.json',dict(status='PASS'));return dict(status='PASS')
  with patch.object(module,'attach',return_value=Z),patch.object(ep,'artifact_entries',side_effect=ValueError('fixture enumerator') if ep_bad else None,return_value=[]),patch.object(module,'launch',side_effect=launch),patch.object(module,'rdiff',side_effect=rd),patch.object(module,'sample',return_value=dict(status='PASS')),patch.object(module,'nsample',side_effect=ns),patch.object(module,'type_counts',side_effect=types),patch.object(module.time,'monotonic',return_value=1):
   if ep_bad or target_bad:
    with self.assertRaisesRegex(ValueError,'R1_PUBLICATION_INCOMPLETE'):module.publish(kit('qd'),root,'123',rc)
    result=None
   else:result=module.publish(kit('qd'),root,'123',rc)
  return result,root,target,calls
 def test_chain_fail_does_not_change_status_and_fourth_condition(self):
  for rc in (0,7):
   result,root,target,calls=self.publication(x,'fail'+str(rc),rc=rc,chain='FAIL')
   v=z.load(target/'timings.json');self.assertEqual(result,0);self.assertEqual(v['returncode'],rc);self.assertEqual(v['chain'],'FAIL')
   self.assertEqual(v['task_a'],dict(status='FAIL',task_i='PASS',task_ii='PASS',task_iii='PASS',task_iv='FAIL'))
   self.assertEqual(z.load(target/'chain.json')['status'],'FAIL')
 def test_chain_fallback_precedes_later_publication_failure(self):
  result,root,target,calls=self.publication(x,'ep',preexisting=False,ep_bad=True)
  self.assertEqual(calls[0],'chain');self.assertEqual(z.load(target/'chain.json')['count'],9)
  self.assertEqual(z.load(root/'publication.json')['chain'],'PASS');self.assertEqual(z.load(target/'timings.json')['chain'],'PASS')
 def test_failed_destination_keeps_local_chain(self):
  _,root,_,calls=self.publication(x,'destination',target_bad=True,preexisting=False)
  self.assertEqual(calls[0],'chain');self.assertEqual(z.load(root/'chain.json')['status'],'PASS')
  self.assertEqual(z.load(root/'publication.json')['chain'],'PASS')
 def test_other_failures_keep_build_and_check_statuses(self):
  for i,(rc,gate,proc,rd) in enumerate([(0,True,0,0),(7,True,0,0),(0,True,1,0),(7,True,1,1),(7,False,1,0)]):
   a,_,_,_=self.publication(old,'old'+str(i),rc=rc,gate=gate,proc_rc=proc,rd_rc=rd)
   b,root,target,_=self.publication(x,'new'+str(i),rc=rc,gate=gate,proc_rc=proc,rd_rc=rd)
   self.assertEqual(a,b);self.assertEqual(z.load(target/'timings.json')['returncode'],rc)
 def test_mode_b_publication_byte_identical(self):
  for rc in (0,7):
   a,_,at,ac=self.publication(old,'old_b'+str(rc),mode='b',rc=rc)
   b,_,bt,bc=self.publication(x,'new_b'+str(rc),mode='b',rc=rc)
   self.assertEqual(a,b);self.assertEqual(ac,bc)
   self.assertEqual({p.name:p.read_bytes() for p in at.iterdir()},{p.name:p.read_bytes() for p in bt.iterdir()})
 def test_timing_bytes_exact_in_both_totals(self):
  _,root,target,_=self.publication(x,'budget',extra=5_000_000)
  v=z.load(target/'timings.json');sizes={str(p.relative_to(target)):p.stat().st_size for p in target.rglob('*') if p.is_file()}
  self.assertEqual(v['aggregate_publication_bytes'],sum(sizes.values()))
  self.assertEqual(v['helper_publication_bytes'],sum(s for n,s in sizes.items() if n!='p_sample.json' and not n.startswith('rd0/')))
  self.assertEqual(v['aggregate_limit_status'],'FAIL');self.assertEqual(v['helper_limit_status'],'PASS')
 def test_audit_runs_in_build_finally_after_native_failure(self):
  root=F/'build_failure';(root/'dr/p/q/selection').mkdir(parents=True);(root/'dr/p/q/selection/rows.sqlite').write_bytes(b'fixture')
  z.write(root/'env.json',dict(paths=[]));z.write(root/'mode.json',dict(mode='r'))
  def audit(k,r):z.write(Path(r)/'chain.json',dict(status='FAIL'));return dict(status='FAIL')
  with patch.object(x,'attach',return_value=z),patch.object(x,'run_r',side_effect=ValueError('native failure')),patch.object(ch,'run',side_effect=audit) as check:
   with self.assertRaisesRegex(ValueError,'native failure'):x.run(kit('qd'),root,'1')
  self.assertEqual(check.call_count,1);self.assertEqual(z.load(root/'build.json')['status'],'REFUSE');self.assertEqual(z.load(root/'chain.json')['status'],'FAIL')
 def test_mode_b_launch_commands_identical(self):
  root=F/'cmd';root.mkdir();z.write(root/'mode.json',dict(mode='b'));z.write(root/'env.json',dict(venv=str(root/'v'),paths=[]))
  Z=SimpleNamespace(load=lambda p:dict(bwrap=dict(file='/project/community/jjyeung/cp4tk_rt/kit/bwrap',sha256='a'*64)) if str(p).endswith('k/l.json') else z.load(p),checked=lambda p,*args:p)
  for action in ('plan','run','check'):
   values=[]
   for m in (old,x):
    with patch.object(m,'attach',return_value=Z),patch.object(m.subprocess,'run',side_effect=lambda cmd,**kw:values.append((cmd,kw)) or SimpleNamespace(returncode=0)):
     m.launch(kit('qd'),root,'123',action=action)
   # __file__ is the same delivered command location in a byte comparison.
   values[0][0]=[str(L/'out/rcj/x.py') if v==str(L/'attic/build24m4q/out/rcj/x.py') else v for v in values[0][0]]
   self.assertEqual(values[0],values[1])

r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
write(D/'PUBLICATION_TESTS.json',dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,failures=[str(v) for v in r.failures],errors=[str(v) for v in r.errors]))
raise SystemExit(not r.wasSuccessful())
