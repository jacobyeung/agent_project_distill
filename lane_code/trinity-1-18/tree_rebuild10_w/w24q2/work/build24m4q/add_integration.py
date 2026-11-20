from pathlib import Path
import time
L=Path.cwd();p=L/'out/rcj/x.py';s=p.read_text().replace("        import ep\n        entries += [('k_'+name, p) for name, p in ep.artifact_entries(root)]", "        try:\n            import ep\n            entries += [('k_'+name, p) for name, p in ep.artifact_entries(root)]\n        except Exception as error:\n            errors.append(dict(file='k', error=type(error).__name__+': '+str(error)))")
a=L/'attic/build24m4q/x_ep1.py';p.rename(a);p.write_text(s)
p=L/'work/build24m4q/tests.py';s=p.read_text();at=s.index("if __name__=='__main__':")
s=s[:at]+'''
 def test_chain_runs_after_regeneration_failure_without_changing_exception(self):
  import rg,px
  from types import SimpleNamespace
  root=F/'run_hook';root.mkdir();native=root/'dr/p/q';native.mkdir(parents=True)
  z.write(root/'pins.json',dict(paths={}))
  c=cfg();c['streams']={}
  database=db(native/'selection/rows.sqlite',[row()])
  oldload=z.load
  def loadp(p):return dict(namespace=str(root/'dr')) if str(p).endswith('k/p.json') else oldload(p)
  Z=SimpleNamespace(load=loadp,write=z.write,checked=z.checked)
  reached=[]
  def regen(config,directory,compare=True):
   reached.append('build');raise ValueError('native after DB')
  def chain(config,directory,output):
   self.assertEqual(config,c);self.assertEqual(Path(directory),native)
   reached.append('chain');v=ch.scan(config,'routing',[dict(database=database)])
   z.write(Path(output)/'chain.json',dict(status=v['status'],streams=dict(routing=v)));return v
  def program(*a,**k):return rg.regenerate(c,native)
  with patch.object(x,'attach',return_value=Z),patch.object(rg,'regenerate',side_effect=regen),patch.object(x.runpy,'run_path',side_effect=program),patch.object(ch,'run',side_effect=chain):
   with self.assertRaisesRegex(ValueError,'native after DB'):x.run_r(L/'out/kit_qd',root,'123')
  self.assertEqual(reached,['build','chain']);self.assertEqual(z.load(root/'ch_cfg.json'),c)
  self.assertEqual(z.load(root/'chain.json')['status'],'PASS')
 def test_diagnostic_failure_does_not_change_success_or_native_refusal(self):
  import rg
  from types import SimpleNamespace
  for failed in (False,True):
   root=F/('diag_failure_'+str(failed));native=root/'dr/p/q';native.mkdir(parents=True)
   db(native/'selection/rows.sqlite',[row()]);z.write(root/'pins.json',dict(paths={}))
   oldload=z.load
   def loadp(p):return dict(namespace=str(root/'dr')) if str(p).endswith('k/p.json') else oldload(p)
   Z=SimpleNamespace(load=loadp,write=z.write,checked=z.checked)
   def regen(*a,**k):
    if failed:raise ValueError('native refusal')
    return {'status':'PASS'}
   def program(*a,**k):return rg.regenerate(cfg(),native)
   with patch.object(x,'attach',return_value=Z),patch.object(rg,'regenerate',side_effect=regen),patch.object(x.runpy,'run_path',side_effect=program),patch.object(ch,'run',side_effect=RuntimeError('diagnostic failure')):
    if failed:
     with self.assertRaisesRegex(ValueError,'native refusal'):x.run_r(L/'out/kit_qd',root,'123')
    else:x.run_r(L/'out/kit_qd',root,'123')
   self.assertEqual(z.load(root/'chain.json')['status'],'UNAVAILABLE')
 def test_later_publication_failure_still_publishes_chain_and_timing(self):
  import ep
  from types import SimpleNamespace
  root=F/'later';root.mkdir();remote=root/'remote';target=remote/'o/123'
  z.write(root/'mode.json',dict(mode='r'));z.write(root/'chain.json',dict(status='FAIL',streams=dict(routing=dict(rows_checked=2,database_rows=2,refused_rows=1))))
  oldload=z.load
  def loadp(p):return dict(n_root=str(remote)) if str(p).endswith('k/p.json') else oldload(p)
  Z=SimpleNamespace(load=loadp,write=z.write,sha=z.sha)
  with patch.object(x,'attach',return_value=Z),patch.object(ep,'artifact_entries',side_effect=ValueError('later publication')):
   with self.assertRaisesRegex(ValueError,'R1_PUBLICATION_INCOMPLETE'):x.publish(L/'out/kit_qd',root,'123',7)
  self.assertEqual((target/'chain.json').read_bytes(),(root/'chain.json').read_bytes())
  timing=z.load(target/'timings.json');self.assertEqual(timing['chain']['status'],'FAIL');self.assertEqual(timing['returncode'],7)
  self.assertEqual(timing['chain']['routing']['rows_checked'],2)
 def test_full_run_uses_current_pin_and_never_candidate(self):
  root=F/'full';root.mkdir();native=root/'q';native.mkdir()
  a=row();a['s1_source']=dict(name='pool');a['routing'].update(question_type='object_abs_distance',ground_record=dict(program_audit=dict(independent_ordered_boxes=[{}])))
  b=copy.deepcopy(a);b['question']='changed copy'
  db(native/'base/rows.sqlite',[a]);db(native/'selection/rows.sqlite',[b])
  c=cfg();c['streams']={};c['extent_receipt']=pin(root/'e.json',dict(schema='full-extent-receipt-v1',rows={'ok':dict(content_sha256=digest(content(a)),box_statuses=['full'],repair_sha256=None)}))
  for stream in ('vqa','pointing','pose'):
   p=db(root/(stream+'.sqlite'),[row()]);c['streams'][stream]=pin(root/(stream+'.json'),dict(database=p))
  before=copy.deepcopy(c)
  with patch.object(ch,'DB',file_pin(native/'base/rows.sqlite')['sha256']):v=ch.run(c,native,root)
  self.assertEqual(c,before);self.assertEqual(v['status'],'FAIL');self.assertEqual(v['candidate']['status'],'PASS')
  self.assertEqual(v['streams']['routing']['counts']['extents'],dict(FAIL=1))
  self.assertTrue(all(v['streams'][s]['rows_checked']==20000 for s in ('vqa','pointing','pose')))
  self.assertEqual(v['population']['status'],'NOT_REACHED');self.assertEqual(v['population']['database_rows'],1)
  self.assertFalse(v['candidate_used']);self.assertFalse(v['candidate']['candidate_pinned'])
'''+s[at:]
a=L/'attic/build24m4q/tests_before_integration.py';p.rename(a);p.write_text(s)
