from pathlib import Path
p=Path('code/test_kit.py');s=p.read_text();i=s.index("if __name__=='__main__':")
addition=''' def test_pose_sign_lifting_arm_and_camera_license(self):
  pose=[dict(capture='p',split='train',G32=dict(move_mra=.2,short_displacement_mra=.3),G64=dict(move_mra=.4,short_displacement_mra=.5))]
  distance=[dict(room='r',split='train',arm='A2',delta=3.),dict(room='r',split='train',arm='today',delta=-7.)]
  bars=metrics.a_bars(pose,distance)
  self.assertEqual(bars['context_pays_pose'],'PASS');self.assertAlmostEqual(bars['move_mra']['train']['point'],20.)
  self.assertEqual(bars['lifting']['train']['point'],3.)
  pose[0]['G64']=dict(move_mra=.1,short_displacement_mra=.1)
  bars=metrics.a_bars(pose,distance)
  self.assertEqual(bars['context_pays_pose'],'FAIL');self.assertEqual(bars['reader_C64_licensed'],'FAIL')
 def test_update_discards_placeholder_and_retains_bars(self):
  import evaluate_v2 as E,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('decision_'+uuid.uuid4().hex);root.mkdir(parents=True)
  write_json(root/'DECISION.json',dict(status='MISSING',bars=dict(added_frame_gain='MISSING')))
  with patch.object(E,'OUT',root):
   E.update('A',dict(context_pays_pose='FAIL'),True)
   E.update('B',dict(added_frame_gain=dict(status='OK',verdict='PASS',low=1.)),True)
   d=read_json(root/'DECISION.json')
   self.assertNotIn('status',d);self.assertEqual(set(d['bars']),{'A','B'})
   self.assertEqual(d['bars']['A']['context_pays_pose'],'FAIL')
   self.assertEqual(d['bars']['B']['added_frame_gain']['verdict'],'PASS');self.assertTrue(d['train_complete'])
 def test_heldout_labels_guard(self):
  import evaluate_v2 as E
  from unittest.mock import patch
  with patch.object(E,'_HELDOUT_ACTIVE',False),patch.object(E,'read_json',return_value={'rows':[]}) as read,patch.object(E,'row_ids',return_value=set()):
   with self.assertRaisesRegex(ValueError,'heldout_once'):E.labels('heldout')
   read.assert_not_called()
 def run_a_fixture(self,stored=None):
  import evaluate_v2 as E,uuid
  from unittest.mock import patch
  from contextlib import ExitStack
  root=ROOT/'runtime'/('run_a_'+uuid.uuid4().hex);root.mkdir(parents=True)
  c=dict(canonical='fixture/no_convert',room='fixture',k1_split='train',gt={'path':str(root/'gt.npz')})
  tw=dict(raw_pose=np.zeros((1,9)),anchor_slots=np.array([0]),depth_grid=np.ones((1,2,2)),depth_conf_grid=np.arange(4).reshape(1,2,2))
  own=dict(depth=np.ones((1,2,2)),gravity=np.array([0.,1.,0.]))
  np.savez(root/'tower.npz',**tw);np.savez(root/'own.npz',**own)
  np.savez(root/'gt.npz',c2w=np.eye(4)[None],depth=np.ones((1,2,2)),valid=[True]);c['gt']['sha256']=sha(root/'gt.npz')
  write_json(root/'candidates.json',{})
  if stored is not None:np.savez(root/'geometry.npz',scale=stored)
  dense=dict(tw,context=64)
  def pricing(c,g,**kw):return [dict(row_id='row',room='fixture',split='train',prediction=2. if g==32 else 1.)]
  mocks=dict(OUT=root,labels=lambda split:{'row':1.},captures=lambda split:[c],row_ids=lambda split:{'row'},capdir=lambda *a:root,stored_tower=lambda c:dense,geometry=lambda tw,own:(tw.get('context',32),1.),price=pricing,winning_box=lambda context:None,emit=lambda *a,**k:None,items_file=lambda *a:None)
  with ExitStack() as stack:
   for name,value in mocks.items():stack.enter_context(patch.object(E,name,value))
   stack.enter_context(patch.object(E.metrics,'c2w_pose',lambda x:x))
   stack.enter_context(patch.object(E.metrics,'poses',lambda *a:dict(move_mra=.5,short_displacement_mra=.5)))
   stack.enter_context(patch.object(E.metrics,'depth_metrics',lambda *a:{}))
   result=E.run_a()
  return result,read_json(root/'DECISION.json'),read_json(root/'A_SCALE.json')
 def test_run_a_no_geometry_and_a2_direction(self):
  result,decision,scale=self.run_a_fixture()
  self.assertTrue(result['complete']);self.assertEqual(result['missing'],[])
  self.assertEqual(result['scales'][0]['status'],'NO_CONVERT_EXPORT')
  self.assertIsNone(scale['agreement_fraction']);self.assertEqual(scale['stored_rule'],'MISSING')
  self.assertEqual(decision['bars']['A']['lifting']['status'],'PASS')
  self.assertGreater(decision['bars']['A']['lifting']['train']['point'],0.)
 def test_run_a_asserts_convert_scale(self):
  with self.assertRaisesRegex(AssertionError,'scale disagrees'):self.run_a_fixture(stored=2.)
 def test_run_b_persists_added_frame_gain(self):
  import evaluate_v2 as E,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('gain_'+uuid.uuid4().hex);root.mkdir(parents=True)
  for status,low,want in [('OK',2.,'PASS'),('OK',0.,'FAIL'),('MISSING',None,'MISSING')]:
   gain=dict(status=status,low=low)
   with patch.object(E,'OUT',root),patch.object(E,'labels',return_value={}),patch.object(E,'captures',return_value=[]),patch.object(E,'row_ids',return_value={'absent'}),patch.object(E,'emit'),patch.object(E,'items_file'),patch.object(E,'gains_once',return_value=dict(gains={'added_frame_gain':gain})):
    E.run_b()
   d=read_json(root/'DECISION.json');self.assertEqual(d['bars']['B']['added_frame_gain']['verdict'],want)
 def test_dense_best_uses_remapped_anchor_areas(self):
  from e2e_reader.geometry import from_tower
  from replay import make_session
  pose=np.zeros((64,9));pose[:,6]=1;pose[:,7:]=1.;pose[:,0]=np.arange(64)*-.01
  grid=np.ones((64,51,51))*2+np.linspace(0,.3,51)[None,:,None]
  geo=from_tower(pose,np.arange(64),np.arange(64),grid,np.linspace(0,1000,51),[0,-1,0],1,(480,640))
  masks=np.zeros((64,20,20),bool);masks[0,5:10,5:10]=True;masks[63,5:15,5:15]=True
  session=make_session(geo,lambda name:[dict(instance_id='fixture',masks=masks)],[0,*range(3,64,2)])
  text=session.execute('<ground obj="fixture" mode="box">')
  self.assertIn('frames 1,32',text);self.assertIn('best 32',text)
 def test_part_c_requires_standalone_da3_go(self):
  import runner,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('preflight_'+uuid.uuid4().hex);(root/'inbox').mkdir(parents=True)
  code={'fixture':'code'}
  def read(path):
   if path.name=='GPU_GO.json':return dict(status='GO',parts=['C'],code_sha256=digest(code))
   if path.name=='DRYRUN.json':return dict(status='PASS',code_sha256=digest(code))
   return {}
  (root/'inbox/GPU_GO.json').write_text('fixture')
  with patch.object(runner,'ROOT',root),patch.object(runner,'read_json',side_effect=read),patch.object(runner,'code_pins',return_value=code),patch('camera_records.frame_binding',return_value={'status':'PASS'}):
   for contents in (None,'NOT GO','GO pending'):
    if contents is not None:(root/'inbox/DA3_GO.txt').write_text(contents)
    with self.assertRaisesRegex(PermissionError,'DA3_GO.txt'):runner.preflight('C')
   (root/'inbox/DA3_GO.txt').write_text('  GO  \\n');self.assertEqual(runner.preflight('C'),{})
 def test_halted_before_admission_and_not_admitted_receipt(self):
  import runner,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('admission_'+uuid.uuid4().hex);root.mkdir(parents=True)
  write_json(root/'HALTED_A.json',dict(reason='fixture'))
  with patch.object(runner,'OUT',root),patch('budget.admit') as admit:
   with self.assertRaisesRegex(RuntimeError,'HALTED'):runner.admit_ready('A',{})
   admit.assert_not_called()
   admit.side_effect=AssertionError('budget exhausted')
   self.assertIsNone(runner.admit_ready('B',{}))
   r=read_json(root/'NOT_ADMITTED_B.json');self.assertEqual(r['status'],'NOT_ADMITTED');self.assertTrue(r['skipped'])
 def test_compare_requires_complete_row_set(self):
  import kbox_hook
  from unittest.mock import patch
  with patch.object(kbox_hook,'evidence',return_value=([dict(capture='c',row_id='missing')],{})):
   with self.assertRaisesRegex(AssertionError,'row set'):kbox_hook.compare({'canonical':'c'},[])
'''
p.write_text(s[:i]+addition+s[i:])
