from pathlib import Path
O=Path('out');P=O/'src'
def edit(p,a,b):
 s=p.read_text();assert a in s,(p,a);p.write_text(s.replace(a,b))
p=P/'b/e2e_reader/perception_memo.py'
edit(p,'Only the frozen G3T output and SAM image pyramids enter this store. Keys bind','Only explicitly listed frozen modules enter this store. Keys bind')
edit(p,'    return dict(perception_memo=mode, perception_memo_verify_ids=tuple(ids))',"    modules = value['perception_memo_modules']\n    if not isinstance(modules, list) or any(type(m) is not str for m in modules):\n        raise ValueError('invalid_perception_memo_modules')\n    return dict(perception_memo=mode, perception_memo_verify_ids=tuple(ids),\n                perception_memo_modules=tuple(modules))")
edit(p,"def __init__(self, perception_memo='on', perception_memo_verify_ids=()):","def __init__(self, perception_memo='on', perception_memo_verify_ids=(), *, perception_memo_modules):")
edit(p,'        self.verify_ids = frozenset(perception_memo_verify_ids)','        self.verify_ids = frozenset(perception_memo_verify_ids)\n        self.modules = frozenset(perception_memo_modules)')
edit(p,'self.__init__(self.requested, tuple(self.verify_ids))','self.__init__(self.requested, tuple(self.verify_ids), perception_memo_modules=tuple(self.modules))')
edit(p,"if _disabled or self.mode == 'off':","if module not in self.modules or _disabled or self.mode == 'off':")
p=P/'b/e2e_reader/real.py'
edit(p,'def real_perception(artifact, *, device,','def real_perception(artifact, *, device, perception_memo_modules,')
edit(p,'memo = process_memo(dict(perception_memo=perception_memo,','memo = process_memo(dict(perception_memo=perception_memo, perception_memo_modules=perception_memo_modules,')
p=P/'b/e2e_reader/parity.py'
edit(p,"perception_memo=settings['perception_memo'],","perception_memo=settings['perception_memo'],\n                                             perception_memo_modules=settings['perception_memo_modules'],")
p=P/'orchard_h10/prepare.py'
edit(p,"perception_memo=config.get('perception_memo','off'),","perception_memo=config.get('perception_memo','off'),\n        perception_memo_modules=config['perception_memo_modules'],")
p=P/'orchard_h10/build.py'
edit(p,"payload_pins=pins,","payload_pins=pins,perception_memo_modules=['g3t'],")
p=P/'orchard_h10/runner.py'
edit(p,"identity.update(perception_memo=actual.get('perception_memo','off'),","identity.update(perception_memo=actual.get('perception_memo','off'),\n                    perception_memo_modules=actual['perception_memo_modules'],")
p=P/'h1eval/h10/launch.py'
edit(p,"'perception_memo_verify_ids'):","'perception_memo_verify_ids','perception_memo_modules'):")
edit(p,"perception_memo=(settings or {}).get('perception_memo','off'),","perception_memo=(settings or {}).get('perception_memo','off'),\n                 perception_memo_modules=settings['perception_memo_modules'] if reviewed else [],")
p=P/'h1eval/h10/parity_adapter.py'
edit(p,"('stage1_select_rule','perception_memo','perception_memo_verify_ids'):","('stage1_select_rule','perception_memo','perception_memo_verify_ids','perception_memo_modules'):")
p=O/'tower_sequence.py'
edit(p,'SCHEDULE=((0,3),(0,0),(0,1),(0,2),(0,4),(1,3))','SCHEDULE=((1,3),(0,3),(0,0),(0,1),(0,2),(0,4))')
edit(p,"perception_memo='verify' if i==0 else 'on',","perception_memo='verify' if i==1 else 'on',perception_memo_modules=['g3t'],")
edit(p,'perception_memo_verify_ids=verify_ids if i==0 else [],','perception_memo_verify_ids=verify_ids if i==1 else [],')
edit(p,"('perception_memo','perception_memo_verify_ids')","('perception_memo','perception_memo_verify_ids','perception_memo_modules')")
edit(p,"('verify' if i==0 else 'on')","('verify' if i==1 else 'on')")
edit(p,"value=real.real_perception(None,device='cpu',","value=real.real_perception(None,device='cpu',perception_memo_modules=['g3t'],")
edit(p,'for i in (0,1):','for i in (1,0):')
s=p.read_text();start=s.index('def memory_bound(');end=s.index('\ndef main():',start)
s=s[:start]+'''def memory_bound(*, captures=(84,60), allocation_bytes=200*1024**3):
 # Fixed G3T contract: at most 64 pose rows and 32 anchor grids. Eight bytes
 # per scalar covers both float64 poses and the fresh float32 grid outputs.
 g3t=(64*9+64+32+32*51*51*5+51+2)*8
 per_capture=g3t+1024**2
 runtime_allowance=64*1024**3
 reads=[dict(read=i,captures=n,memo_bytes=n*per_capture,
             memo_plus_transient_bytes=(n+3)*per_capture,
             host_budget_bytes=(n+3)*per_capture+runtime_allowance) for i,n in enumerate(captures)]
 return dict(basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],
             sam_memo_bytes=0,sam_measurement_required=False,g3t_capture_bytes_upper=g3t,
             python_overhead_bytes_per_capture=1024**2,transient_capture_copies=3,
             runtime_allowance_bytes=runtime_allowance,job_host_bytes=allocation_bytes,reads=reads,
             fits=all(r['host_budget_bytes']<=allocation_bytes for r in reads))


def memory_probe(config):
 """Check the retained G3T bound without loading or measuring SAM."""
 from orchard_h10.common import write
 settings=json.loads(Path(config['settings']).read_text())
 if settings['perception_memo_modules']!=['g3t']:raise ValueError('Unsupported operator memo modules')
 result=memory_bound()
 write(Path(config['output'])/'metadata/MEMORY.json',result)
 if not result['fits']:raise ValueError('Perception memo exceeds host memory plan')
 return result

''' + s[end:];p.write_text(s)
p=O/'tower_bootstrap.py'
edit(p,"and proof.get('memory',{}).get('measured') is True","and proof.get('memory',{}).get('basis') == 'fixed_g3t_shapes'\n        and proof['memory'].get('perception_memo_modules') == ['g3t']\n        and proof['memory'].get('sam_measurement_required') is False")
p=O/'node_check.py'
edit(p,"if settings['stage1_select_rule']!='null_argmax' or settings['perception_memo']!='off':","if (settings['stage1_select_rule']!='null_argmax' or settings['perception_memo']!='off'\n        or settings['perception_memo_modules']!=['g3t'] or settings['perception_memo_verify_ids']!=[]):")
# Required module setting in fixtures; these files are tests, not shipped reader logic.
for p in list(Path('work').glob('test_*.py'))+[Path('work/fixture_worker.py')]+list((O/'tests').glob('test_*.py')):
 if p.name=='test_baseline_ab.py':continue
 s=p.read_text()
 s=s.replace('perception_memo=',"perception_memo_modules=['g3t'],perception_memo=")
 s=s.replace("{'perception_memo':","{'perception_memo_modules':['g3t'],'perception_memo':")
 s=s.replace('M.Memo()',"M.Memo(perception_memo_modules=['g3t','g','s'])")
 s=s.replace("'perception_memo_verify_ids')","'perception_memo_verify_ids','perception_memo_modules')")
 s=s.replace("policy['perception_memo_verify_ids'][:-1] if i==0", "policy['perception_memo_verify_ids'][:-1] if i==1")
 p.write_text(s)
p=Path('work/test_memo.py')
edit(p,"{'perception_memo_modules':['g3t'],'perception_memo':", "{'perception_memo_modules':['g3t','g','s'],'perception_memo':")
edit(p,'self.assertEqual(sam.calls,expected)','self.assertEqual(sam.calls,30)')
edit(p,'self.assertEqual(len(events),50)','self.assertEqual(len(events),25)')
p=Path('work/test_multitype_ab.py')
edit(p,"self.assertEqual(sam.calls,{'off':10,'on':2,'verify':4}[mode])","self.assertEqual(sam.calls,10)")
p=Path('work/test_fixes.py')
edit(p,"('perception_memo','on'),('perception_memo_verify_ids',['x'])","('perception_memo','on'),('perception_memo_modules',['sam3']),('perception_memo_verify_ids',['x'])")
