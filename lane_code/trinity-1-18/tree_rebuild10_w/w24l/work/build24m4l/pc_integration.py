from common import *
import shutil,importlib.util,subprocess,copy,sqlite3
from unittest.mock import patch
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from student_pilot import mdg_parent
spec=importlib.util.spec_from_file_location('pc_integrate',L/'out/rcj/pc.py');PC=importlib.util.module_from_spec(spec);spec.loader.exec_module(PC)
sys.path.insert(0,str(kit('qd')/'b'));import rb,z
F=D/'pc_integration';F.mkdir();records=[]
real_run=subprocess.run;real_load=z.load
for label,vqa_available,bad in [('both',True,False),('fallback',False,True)]:
 root=F/label;q=root/'dr/p/q';q.mkdir(parents=True);(q/'u').mkdir()
 shutil.copytree(T,root/'dr/p/s');shutil.copytree(D/'rcj_l/p_tree',q/'base_tree')
 (q/'selection').mkdir();shutil.copyfile(D/'rcj_l/n.sqlite',q/'selection/rows.sqlite')
 with sqlite3.connect(q/'selection/rows.sqlite') as c:
  for i,raw in c.execute('SELECT i,row FROM rows').fetchall():
   row=json.loads(raw);row['routing']=dict(category='route',events=[dict(kind='plan',text='Check')],answer='A');row['target']='stale fixture target'
   c.execute('UPDATE rows SET row=? WHERE i=?',(json.dumps(row),i))
 vqa_db=q/'v.sqlite';shutil.copyfile(D/'rcj_l/n.sqlite',vqa_db)
 vp=J.write(q/'v.json',dict(database=dict(path=str(vqa_db),sha256=J.sha(vqa_db))))
 modelpin=J.write(q/'model.json',dict(root='/fixture'))
 n=copy.deepcopy(J.load(kit('n')/'k/n.json'));n['streams']['vqa']=vp if vqa_available else dict(path=str(q/'missing'),sha256='0'*64)
 n['code']=J.write(q/'n_code.json',dict(tree_sha256=digest(inventory(T))))
 if bad:n['frame_count']=64
 p=J.load(input_file(n['r1_training']['p_run']['config']['sha256']))
 p['code']=J.write(q/'p_code.json',dict(tree_sha256=digest(inventory(q/'base_tree'))))
 J.write(q/'n.json',n);J.write(root/'pins.json',dict(paths={}))
 env=rb.environment()
 for field in ('paths','binds'):env[field]=[x for x in env[field] if Path(x)!=D and Path(x)!=T]
 J.write(q/'base_input.json',dict(config=p,recipe=dict(base_model=modelpin),environment=env))
 J.write(q/'base_mounts.json',{})
 commands=[]
 def runner(cmd,**kw):
  commands.append(cmd.copy())
  assert cmd[-3]==str(L/'out/rcj/pc.py') and all(x in cmd for x in ('-I','-s','-S','-B'))
  assert '--ro-bind' in cmd and str(q/'base_tree') in cmd if cmd[-1].endswith('base_tree') else True
  at=cmd.index('--chdir')
  for f in ('pc_worker_boundary.py','pc_fixture_worker.py'):cmd[at:at]=['--ro-bind',str(D/f),str(D/f)]
  # All producer and worker code is real; only loading absent tokenizer assets is stubbed.
  cmd[-3]=str(D/'pc_worker_boundary.py')
  return real_run(cmd,**kw)
 def load(path):return dict(namespace=str(root/'dr')) if str(path).endswith('k/p.json') else real_load(path)
 with patch.object(z,'load',side_effect=load),patch.object(mdg_parent,'model_pin',return_value=modelpin),patch.object(rb,'environment',return_value=env),patch.object(PC.subprocess,'run',side_effect=runner):
  rc=PC.run(kit('qd'),root)
 value=J.load(root/'proc_check.json');assert value['status']==('FAIL' if bad else 'PASS'),{k:v for k,v in value.items() if k!='rows'}
 assert value['rows'][0]['n']['values']['target_ids']!=[ord(c)+10 for c in 'stale fixture target']
 assert value['count']==80 and value['scope']['vqa_staged']==vqa_available
 assert len(commands)==2 and rc==int(bad)
 assert all(r['status']==('FAIL' if bad else 'PASS') for r in value['rows'])
 records.append(dict(case=label,status=value['status'],scope=value['scope'],sample_sha256=value['sample_sha256'],commands=commands))
J.write(D/'PC_INTEGRATION_TESTS.json',dict(status='PASS',records=records,scope='Real coordinator, source inventory gates, isolated worker mounts and native constructors/encoders; synthetic stores and stubbed tokenizer asset loading.'))
print('PC integration PASS: 40+40 and 80 fallback; native isolated workers; deliberate mismatch fails')
