import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
import sqlite3,shutil,copy,subprocess
from unittest.mock import patch
import pc,rb
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
F=D/('pc_'+str(time.time_ns()));F.mkdir();records=[]
real_run=subprocess.run;real_load=z.load
ptree=L/'work/build24m4m/rcj_l/p_tree';assert digest(inventory(ptree)).startswith('b83a8a35')
for label,vqa_available,bad,absent in [('both',True,False,False),('fallback',False,False,False),('mismatch',True,True,False),('missing',True,False,True)]:
 root=F/label;q=root/'dr/p/q';q.mkdir(parents=True);(q/'u').mkdir()
 shutil.copytree(T,root/'dr/p/s',copy_function=os.link);shutil.copytree(ptree,q/'base_tree',copy_function=os.link)
 (q/'selection').mkdir();database=q/'selection/rows.sqlite'
 with sqlite3.connect(database) as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  for i in range(90):
   row=dict(qid='q'+str(i),dataset='fixture',scene='room',target='A',student_input=dict(question='Q'+str(i),options=['A','B'],frames=[{}]*32,frame_indices=list(range(32)),timestamps=[j/30 for j in range(32)],fps=30,total_num_frames=32))
   row['routing']=dict(category='route',events=[dict(kind='plan',text='Check')],answer='A')
   c.execute('insert into rows values(?,?,?)',(10+3*i,json.dumps(row),'{}'))
 vp=z.write(q/'v.json',dict(database=dict(path=str(database),sha256=z.sha(database))))
 files={}
 for p in (D/'assets3').iterdir():
  h=z.sha(p);files[p.name]=h
  if not (q/'u'/h).exists():os.link(p,q/'u'/h)
 # An unneeded shard in the receipt must never enter either asset mount list.
 files['model.safetensors-00001-of-00004.safetensors']='0'*64
 npin=z.write(q/'mn.json',dict(root='/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a',files=files))
 ppin=z.write(q/'mp.json',dict(root='/project/community/jjyeung/c7d31ddd/runs/q/models/a/snapshots/p',files=files))
 pose=z.write(q/'pose.json',dict(model=npin))
 n=copy.deepcopy(z.load(kit('n')/'k/n.json'));n['streams']['pose']=pose;n['streams']['vqa']=vp if vqa_available else dict(path=str(q/'missing'),sha256='0'*64)
 n['code']=z.write(q/'n_code.json',dict(tree_sha256=digest(inventory(T))))
 if bad:n['frame_count']=64
 p=z.load(input_file(n['r1_training']['p_run']['config']['sha256']))
 p['code']=z.write(q/'p_code.json',dict(tree_sha256=digest(inventory(q/'base_tree'))))
 z.write(q/'n.json',n);z.write(root/'pins.json',dict(paths={}))
 env=rb.environment()
 for field in ('paths','binds'):env[field]=[x for x in env[field] if Path(x)!=D and Path(x)!=T]
 z.write(q/'base_input.json',dict(config=p,recipe=dict(base_model=ppin),environment=env));z.write(q/'base_mounts.json',{})
 commands=[]
 def runner(cmd,**kw):
  commands.append(cmd.copy());assert cmd[-3]==str(L/'out/rcj/pc.py')
  at=cmd.index('--chdir');cmd[at:at]=['--ro-bind',str(D/'pc_boundary.py'),str(D/'pc_boundary.py')]
  cmd[-3]=str(D/'pc_boundary.py')
  # Fixture caches stay in the job's writable root, including in the P child.
  at=cmd.index('--chdir')
  for key in ('TMPDIR','HF_HOME','XDG_CACHE_HOME','TORCHINDUCTOR_CACHE_DIR'):
   cmd[at:at]=['--setenv',key,str(q/'cache')];at+=3
  if absent:
   for i in range(len(cmd)-3,-1,-1):
    if cmd[i]=='--ro-bind' and '/models/' in cmd[i+2]:del cmd[i:i+3]
  return real_run(cmd,**kw)
 def load(path):return dict(namespace=str(root/'dr')) if str(path).endswith('k/p.json') else real_load(path)
 with patch.object(z,'load',side_effect=load),patch.object(rb,'environment',return_value=env),patch.object(pc.subprocess,'run',side_effect=runner):rc=pc.run(kit('qd'),root)
 value=z.load(root/'proc_check.json');expected='FAIL' if bad or absent else 'PASS'
 assert value['status']==expected,{k:v for k,v in value.items() if k!='rows'}
 assert value['count']==80 and value['scope']['vqa_staged']==vqa_available
 assert rc==int(bad or absent)
 assert len(commands)==(1 if absent else 2)
 if absent:assert 'E95:n:1:OSError:' in value['reason'],value['reason']
 else:
  assert all(r['status']==expected for r in value['rows']),value['rows'][0]
  for side in ('n','p'):
   control=z.load(q/('pc_'+side+'.json'))
   assert len(control['assets'])==5 and not any(k.endswith('.safetensors') for k in control['assets'])
   assert all(Path(v['source']).parent==q/'u' for v in control['assets'].values())
 records.append(dict(case=label,status=value['status'],scope=value['scope'],sample_sha256=value['sample_sha256'],commands=commands,reason=value.get('reason')))
write(D/'PC_INTEGRATION_TESTS.json',dict(status='PASS',records=records,scope='Real AutoProcessor loads synthetic Llava processor metadata and Qwen tokenizer at receipt roots through native C and P constructors. Native text encoders compare 40+40 and 80 fallback; no tokenizer/constructor stub, weights or RGB.'))
print('PC integration PASS',len(records))
