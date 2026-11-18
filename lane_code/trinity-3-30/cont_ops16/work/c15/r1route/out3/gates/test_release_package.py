import ast,copy,hashlib,importlib.util,io,json,os,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
O=Path(sys.argv.pop(1)).resolve();W=Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3');sys.path[:0]=[str(O),str(O/'src')]
from orchard_h10.common import read_config,sha,canonical,opaque,submit_argv
from orchard_h10.job import check_inputs,verify_config
from orchard_h10.export_pins import admit,validate

def read(p):return json.loads(p.read_text())
class Package(unittest.TestCase):
 def setUp(self):self.cfg=read_config(O/'package');self.inputs=read(O/'inputs_tower.json');self.export=read(O/'package/a/export.json')
 def test_final_plan_and_fixture_metadata_admission(self):
  verify_config(self.cfg);check_inputs(self.inputs,self.cfg,package=O/'package')
  self.assertEqual(self.cfg['export_binding']['run'],'673bc60f');self.assertEqual(self.cfg['export_binding']['step'],200)
 def test_wrong_run_step_lineage_member_config_archive_refused(self):
  for key,value in [('run','17c4ffa4'),('step',100),('lineage','RL'),('member_directory','m100'),('config_sha256','0'*64),('archive_sha256','0'*64),('object','q8/8865619b/17c4ffa4_m200.tar')]:
   bad=copy.deepcopy(self.export);bad[key]=value
   with self.assertRaises(ValueError):admit(self.inputs,self.cfg,bad)
 def test_all_prep_hashes_refused(self):
  for key in ('config','receipt','data_receipt'):
   bad=copy.deepcopy(self.export);bad['preparation'][key]['sha256']='0'*64
   with self.assertRaises(ValueError):admit(self.inputs,self.cfg,bad)
 def test_export_member_hashes_sizes_paths_refused(self):
  for key in ('artifact','heads','full_weights'):
   for field,value in [('sha256','0'*64),('bytes',1),('path','/tmp/0')]:
    bad=copy.deepcopy(self.inputs);bad['files'][key][field]=value
    with self.assertRaises(ValueError):check_inputs(bad,self.cfg,package=O/'package')
 def test_serving_and_item_bytes_identical(self):
  with tarfile.open(O/'original/0.tgz') as t:a={m.name:t.extractfile(m).read() for m in t}
  with tarfile.open(O/'0.tgz') as t:b={m.name:t.extractfile(m).read() for m in t}
  self.assertEqual(set(a),set(b))
  for n in a:
   if n.startswith(('b/','tree/','h1eval/','items/','rows/','auth/')):self.assertEqual(a[n],b[n],n)
  self.assertEqual(sorted(n for n in a if a[n]!=b[n]),read(O/'PAYLOAD_CHANGES.json'))
 def test_all_payload_and_delivery_hashes(self):
  with tarfile.open(O/'0.tgz') as t:files={m.name:t.extractfile(m).read() for m in t}
  for n,pin in self.cfg['payload_pins'].items():self.assertEqual(pin,dict(bytes=len(files[n]),sha256=hashlib.sha256(files[n]).hexdigest()))
  for n,h in read(O/'package/PACKAGE.json')['files'].items():self.assertEqual(sha(O/'package'/n),h)
 def test_old_base_export_refused(self):
  base=Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/bases')/O.name
  with self.assertRaises(ValueError):admit(read(base/'inputs_tower.json'),self.cfg,read(base/'export_544.json'))
 def test_unfilled_release_refuses(self):
  with self.assertRaises((KeyError,ValueError)):check_inputs(read(W/('A' if O.name=='b1' else 'B')/'package/a/1.json'),self.cfg,package=W/('A' if O.name=='b1' else 'B')/'package')
 def test_opaque_walltime_caps_margins(self):
  opaque(submit_argv(self.cfg['token'],1,'05:00:00'));opaque([(O/'package/BATCH.sh').read_text()])
  self.assertEqual(self.cfg['stop_margin'],1800);self.assertEqual(self.cfg['return_margin'],1200)
  with self.assertRaises(ValueError):submit_argv(self.cfg['token'],2,'05:00:00')
 def test_fixed_tower_and_scale_dependencies(self):
  old=read(Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/bases')/O.name/'inputs_tower.json')
  for key,value in old['files'].items():
   if key not in ('artifact','heads','full_weights'):self.assertEqual(self.inputs['files'][key],value)
  for key in ('policy','python','env_roots','frames_root','sam_source'):self.assertEqual(self.inputs[key],old[key])
 def test_py36_helpers_and_metadata_check(self):
  # Execute the actual 3.py/8.py metadata checker under Python 3.6. Only remote
  # path placement and dependency file sizes are explicit filesystem fixtures.
  base=O/'checks'/('a'+os.urandom(8).hex());base.mkdir();p=base/('a15_cot_ap'+self.cfg['token'])
  import shutil
  shutil.copytree(O/'package',p);os.chmod(p/'a',0o700)
  script=base/'0.py';script.write_text('''import sys,json,tarfile,types,os\nfrom pathlib import Path\np=Path(sys.argv[1])\nwith tarfile.open(p/'0.tgz') as t:source=t.extractfile('8.py').read()\nm=types.ModuleType('fixture');m.__file__=str(p/'3.py');exec(compile(source,m.__file__,'exec'),m.__dict__)\nreal=Path;inputs=json.loads((p/'a/1.json').read_text());sizes={v['path']:v['bytes'] for a in inputs['archives'] for v in a['parts']}\ndef path(v):\n if str(v)=='/project/community/jjyeung/okh7':return p.parent\n if str(v) in sizes:return types.SimpleNamespace(stat=lambda:types.SimpleNamespace(st_size=sizes[str(v)]))\n return real(v)\nm.Path=path\nv=m.check(p,1,'05:00:00');assert v['passed'] is True\nprint(json.dumps(v))\n''')
  r=subprocess.run(['/usr/bin/python3','-I','-s','-B',str(script),str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  self.assertEqual(r.returncode,0,r.stderr.decode());(O/'PY36_CHECK.json').write_bytes(r.stdout)
  for helper in (p/'3.py',p/'a/4.py',p/'a/5.py'):
   r=subprocess.run(['/usr/bin/python3','-I','-s','-B',str(helper),'--help'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertEqual(r.returncode,0,r.stderr.decode())
 def test_settings_manifest_count_and_order(self):
  import tower_sequence as t
  spec=t.descriptors(O/'src');self.assertEqual(len(spec),1)
  self.assertEqual(spec[0]['expected'],636 if O.name=='b1' else 134)
  self.assertEqual(spec[0]['stage1_select_rule'],'candidates_argmax');self.assertEqual(spec[0]['perception_memo'],'on');self.assertEqual(spec[0]['perception_memo_verify_ids'],[])
  self.assertEqual(spec[0]['perception_memo_modules'],['g3t']);self.assertFalse(spec[0]['save_own_depth'])
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Package))
 (O/'tests_package_result.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped)))+'\n');sys.exit(not r.wasSuccessful())
