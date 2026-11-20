"""Isolate P refresh ordering and selected-row equality without production stores."""
from pathlib import Path
import copy, importlib.util, json, sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m3';F=D/'p_refresh';F.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'work/build24/kits/n/b'),str(L/'work/tree_r1'),str(L/'work/build24')]
import rg,i,z
from student_pilot import p3_provenance as P,s1_routing,mdg_parent
spec=importlib.util.spec_from_file_location('old_rg',L/'attic/build24m1/work/build24/kits/n/b/rg.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
db=L/'work/build24m1/review_tests/no_pass/node/q_22c714e1_91/vqa.sqlite'
other=L/'work/build24m1/review_tests/no_pass/node/q_22c714e1_91/pose.sqlite'
records=[]
for kind,module,error in (('before',old,'P_REFRESH_NOT_APPLIED'),('after',rg,None),('p_pin',rg,'P_TRAINED_ROUTING_PIN_DIFFERS'),('db_pin',rg,'P_TRAINED_ROUTING_DATABASE_DIFFERS'),('rows',rg,'P_TRAINED_SELECTED_ROW_BYTES_OR_ORDER_DIFFER:0')):
 root=F/kind;root.mkdir();job=root/'q';job.mkdir()
 p_config={'streams':{'routing':{'path':'p_receipt','sha256':'0'*64 if kind=='p_pin' else 'ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984'}}}
 recipe={'inputs':{'selection':'old'},'legacy':{'path':'legacy','sha256':'1'*64},'division':{},'base_model':{}}
 documents={'point':{'division':{}},'n':{'database':{'path':str(db),'sha256':z.sha(db)}},'p_config':p_config,'p_receipt':{'database':{'path':str(db),'sha256':('0'*64 if kind=='db_pin' else '4e8e6c04'+'0'*56)},'materialization':{'path':'recipe','sha256':'2'*64}},'recipe':recipe}
 cfg={'streams':{'pointing':{'path':'point','sha256':'3'*64},'routing':{'path':'n','sha256':'4'*64}},'s1_routing':{},'r1_training':{'p_run':{'config':{'path':'p_config','sha256':'5'*64}}}}
 native_load=P.load;calls=[]
 def read(p):return copy.deepcopy(documents[str(p)]) if str(p) in documents else native_load(p)
 def pinned(pin):return Path(pin['path'])
 def refresh(request,directory):
  pcfg=native_load(request['config']['path']);assert pcfg['s1_routing']==recipe['inputs']
  pcfg['s1_routing']['selection']='current';calls.append('refresh')
  return dict(request,config=z.write(root/'refreshed.json',pcfg))
 def build(config,directory,division,model):
  directory=Path(directory);directory.mkdir()
  if directory.name=='pr':
   assert calls==['refresh'] and config['s1_routing']['selection']=='current','P_REFRESH_NOT_APPLIED'
  chosen=other if kind=='rows' and directory.name=='pr' else db
  value={'database':{'path':str(chosen),'sha256':z.sha(chosen)},'count':64}
  z.write(directory/'receipt.json',value);return value
 actual=None
 with patch.object(P,'pinned',pinned),patch.object(P,'load',read),patch.object(s1_routing,'build',build),patch.object(mdg_parent,'model_pin',return_value={}),patch.object(i,'refresh',refresh):
  try:value=module.regenerate(cfg,job)
  except (ValueError,AssertionError) as e:actual=str(e)
 assert actual==error,(kind,actual,error)
 if error is None:
  assert value['p_regeneration']['selected_rows_equal'] and value['p_regeneration']['rows']==64
  assert len(set(value['p_regeneration']['selected_row_hashes']))==1
 records.append(dict(case=kind,refusal=actual,refresh_calls=len(calls)))
z.write(D/'P_REFRESH_TESTS.json',dict(status='PASS',cases=records,boundaries='Pinned P documents and producer/refresh calls are controlled unit-test inputs; SQLite comparison uses retained native reader fixtures. Production P equality is not claimed.'))
print('P refresh ordering and exact selected-row comparison PASS')
