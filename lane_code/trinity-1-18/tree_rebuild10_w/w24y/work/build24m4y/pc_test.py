from pathlib import Path
import sys,json,hashlib,shutil,os,time,sqlite3,subprocess,copy,tarfile
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4y';T=L/'work/tree_r1c'
sys.path[:0]=[str(L/'out/rcj'),str(T),str(L/'out/kit_qd/b')]
import pc,rb,z
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,file_pin
from student_pilot import mdg_parent
F=D/('pc_'+str(time.time_ns()));F.mkdir();records=[]
real_run=subprocess.run;real_load=z.load
assets=D/'assets2';asset_files={p.name:z.sha(p) for p in assets.iterdir() if p.is_file()}
assert 'processor_config.json' in asset_files
for label,vqa,bad in [('both',True,False),('fallback',False,False),('mismatch',True,True)]:
 root=F/label;q=root/'dr/p/q';q.mkdir(parents=True);(q/'u').mkdir();(q/'selection').mkdir()
 shutil.copytree(T,root/'dr/p/s',copy_function=os.link)
 with tarfile.open(L/'work/build24m4h/p.tar') as archive:archive.extractall(q/'base_tree',filter='data')
 shutil.copytree(assets,root/'m',copy_function=os.link)
 with sqlite3.connect(q/'selection/rows.sqlite') as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  for i in range(100):
   r=dict(qid='q'+str(i),dataset='fixture',scene='room',target='<think>clear</think> A',student_input=dict(question='Q'+str(i),options=['A','B'],frames=[{}]*32,frame_indices=list(range(32)),timestamps=[i/30 for i in range(32)],fps=30,total_num_frames=32),routing=dict(category='route',events=[dict(kind='plan',text='Check')],answer='A'))
   c.execute('insert into rows values(?,?,?)',(10+3*i,json.dumps(r),'{}'))
 vpin=z.write(q/'v.json',dict(database=file_pin(q/'selection/rows.sqlite')))
 n=z.load(L/'work/build24/kits/n/k/n.json');p=z.load(L/'work/build24m4n/inputs/b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad')
 n['streams']['vqa']=vpin if vqa else dict(path=str(q/'absent'),sha256='0'*64)
 n['code']=z.write(q/'n_code.json',dict(tree_sha256=digest(inventory(T))))
 p['code']=z.write(q/'p_code.json',dict(tree_sha256=digest(inventory(q/'base_tree'))))
 assert digest(inventory(q/'base_tree')).startswith('b83a8a35')
 if bad:n['frame_count']=64
 nroot='/project/community/example/runs/aws128p_20261025/models/a32330d0/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
 proot='/scratch/fsw/example/models/a32330d0/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
 files=dict(asset_files);files.update({'model-00001.safetensors':'0'*64,'model.safetensors.index.json':'1'*64})
 npin=z.write(q/'m_n.json',dict(root=nroot,files=files));ppin=z.write(q/'m_p.json',dict(root=proot,files=files))
 z.write(q/'n.json',n);z.write(root/'pins.json',dict(paths={}))
 env=rb.environment()
 for field in ('paths','binds'):env[field]=[v for v in env[field] if Path(v) not in (T,D,L/'out/rcj')]
 z.write(q/'base_input.json',dict(config=p,recipe=dict(base_model=ppin),environment=env));z.write(q/'base_mounts.json',{})
 commands=[]
 def runner(cmd,**kw):
  commands.append(cmd.copy());at=cmd.index('--chdir');cmd[at:at]=['--ro-bind',str(D/'pc_boundary.py'),str(D/'pc_boundary.py')]
  cmd[-3]=str(D/'pc_boundary.py');return real_run(cmd,**kw)
 def load(path):return dict(namespace=str(root/'dr')) if str(path).endswith('k/p.json') else real_load(path)
 with patch.object(z,'load',side_effect=load),patch.object(mdg_parent,'model_pin',return_value=npin),patch.object(rb,'environment',return_value=env),patch.object(pc.subprocess,'run',side_effect=runner):rc=pc.run(L/'out/kit_qd',root)
 v=z.load(root/'proc_check.json')
 assert v['status']==('FAIL' if bad else 'PASS'),(label,v if 'rows' not in v else dict(reason=v.get('reason'),row=v['rows'][0]))
 assert v['count']==80 and len(commands)==2 and rc==int(bad)
 assert all(r['status']==('FAIL' if bad else 'PASS') for r in v['rows'])
 child_assets={side:z.load(q/('pc_'+side+'_out.json.assets')) for side in ('n','p')}
 assert all(a['readonly'] and a['no_loader_stub'] and a['constructed'] for a in child_assets.values())
 for a in child_assets.values():
  assert {'config.json','tokenizer.json','chat_template.jinja'} <= {Path(s).name for s in a['opened']},a
 records.append(dict(case=label,status=v['status'],scope=v['scope'],sample_sha256=v['sample_sha256'],children=child_assets,commands=commands))
z.write(D/'PC_INTEGRATION_TESTS.json',dict(status='PASS',records=records,scope='Real bwrap and AutoProcessor with synthetic processor metadata; native N/P constructors and per-row encoder comparison; no weights or RGB.'))
print('PC integration PASS: 40+40, fallback 80, deliberate mismatch; actual metadata loader in both sandboxes')
