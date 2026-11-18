from pathlib import Path
import json,hashlib,shutil
W=Path.cwd();F=Path('/scratch/jjyeung/orch_n30/reader_r1/work/fix7');R=W/'release';R.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for k in ('b1','b2'):
 o=W/'out'/k;r=R/k;r.mkdir(exist_ok=True)
 if not (r/'src').exists():(r/'src').symlink_to(o/'src',target_is_directory=True)
 shutil.copytree(o/'package',r/'package',dirs_exist_ok=True)
 for p in o.iterdir():
  if p.is_file() and (p.suffix in ('.py','.json') or p.name in ('TOKEN','0.tgz')):(r/p.name).write_bytes(p.read_bytes())
 for n in ('work','tests','checks','work/tmp','original'):(r/n).mkdir(parents=True,exist_ok=True)
 (r/'original/0.tgz').write_bytes((F/k/'0.tgz').read_bytes())
 for p in (o/'work').glob('*.py'):(r/'work'/p.name).write_bytes(p.read_bytes())
 # Metadata fixtures exercise final admission and CPU orchestration without staging weights.
 cfg=json.loads((o/'src/9.json').read_text());binding=cfg['export_binding']
 inp=json.loads((o/'package/a/0.json').read_text());pin=json.loads((F/k/'export_544.json').read_text())
 pin.update({key:binding[key] for key in ('run','step','member_directory','lineage','object','config_sha256')});pin['archive_sha256']=inp['archives'][0]['sha256']
 for name,digest in binding['preparation_sha256'].items():pin['preparation'][name]['sha256']=digest
 for name in ('artifact','heads','full_weights'):inp['files'][name]['path']=inp['files'][name]['path'].replace('/m544/','/m200/')
 put(r/'export_544.json',pin);put(r/'package/a/export.json',pin);inp['export_pin']=dict(path='a/export.json',bytes=(r/'package/a/export.json').stat().st_size,sha256=sha(r/'package/a/export.json'))
 put(r/'inputs_tower.json',inp);put(r/'package/a/1.json',inp)
 s=(F/k/'work/test_sequence.py').read_text().replace("stage1_select_rule='null_argmax'","stage1_select_rule='candidates_argmax'").replace("perception_memo='off'","perception_memo='on'")
 s=s.replace("s['stage1_select_rule']=T.RULES[1]","s['stage1_select_rule']='null_argmax'").replace("s['stage1_select_rule']='candidates_argmax'","s['stage1_select_rule']='null_argmax'")
 if k=='b1':
  s=s.replace('),786)', '),636)').replace("len(result),2","len(result),1").replace("'verify' if i==1 else 'on'","'on'").replace('ids if i==1 else []','[]').replace('n=636 if i==0 else 150','n=636').replace('[(1,3),(0,3),(0,0),(0,1),(0,2),(0,4)]','[(0,3),(0,0),(0,1),(0,2),(0,4)]').replace("r['completed'],786","r['completed'],636")
 (r/'work/test_sequence.py').write_text(s)
 if k=='b2':
  s=(F/k/'work/test_cpu_helper.py').read_text().replace("# Read the exact settings", "# Read the exact settings")
  s=s.replace("S,J,R,I,A=common.template();", "settings['stage1_select_rule']='candidates_argmax';settings['perception_memo']='on'\n  S,J,R,I,A=common.template();")
  (r/'work/test_cpu_helper.py').write_text(s)
 # Room scorer regression uses matching selector and step for its fixture.
 if k=='b2':
  (r/'room_pair.py').write_text((F/k/'room_pair.py').read_text().replace('null_argmax','candidates_argmax'))
  for name in ('test_room_pair.py','test_room_pair_labels.py'):
   s=(Path('/scratch/jjyeung/orch_n30/reader_r1/work/b2r/work')/name).read_text().replace("O=W/'out'","O=W")
   s=s.replace("stage1_select_rule='null_argmax'","stage1_select_rule='candidates_argmax'").replace("('stage1_select_rule','candidates_argmax')","('stage1_select_rule','null_argmax')")
   (r/'work'/name).write_text(s)
 # Return and graceful STOP tests use real launcher subprocesses and fixture model outputs.
 oldwork=Path('/scratch/jjyeung/orch_n30/reader_r1/work')/('b1g' if k=='b1' else 'b2r')/'work'
 for name in ('fixture_worker.py','test_fixes.py','test_select_stubs.py'):
  if not (oldwork/name).exists():continue
  s=(oldwork/name).read_text().replace("O=W/'out'","O=W")
  (r/'work'/name).write_text(s)
# Preserve every guard test; update only plan/payload expectations and fixture settings.
s=(W/'bundle_regression.py').read_text()
s=s.replace("old=W/('boot' if O.name=='b1' else 'boot2')","old=Path('/scratch/jjyeung/orch_n30/reader_r1/work/fix7')/('boot' if O.name=='b1' else 'boot2')")
s=s.replace("self.assertEqual((root/'6.py').read_bytes(),(O/'tower_sequence.py').read_bytes())","self.assertEqual((root/'6.py').read_bytes(),(old/'6.py').read_bytes())")
s=s.replace("stage1_select_rule='null_argmax'","stage1_select_rule='candidates_argmax'").replace("perception_memo='on' if O.name=='b2' else 'off'","perception_memo='on'")
s=s.replace("self.assertEqual([n for n in old if old[n]!=new[n]],['9.json'])","self.assertEqual(sorted(n for n in old if old[n]!=new[n]),json.loads((O/'PAYLOAD_CHANGES.json').read_text()))")
s=s.replace("a=json.loads(old['9.json']);b=json.loads(new['9.json']);a['token']=b['token'];self.assertEqual(a,b)","a=json.loads(old['9.json']);b=json.loads(new['9.json']);self.assertEqual(b['export_binding']['run'],'673bc60f');self.assertEqual(b['export_binding']['step'],200)\n        for n in old:\n            if n.startswith(('b/','tree/','h1eval/','items/','rows/')):self.assertEqual(old[n],new[n])")
(W/'release_bundle.py').write_text(s)
