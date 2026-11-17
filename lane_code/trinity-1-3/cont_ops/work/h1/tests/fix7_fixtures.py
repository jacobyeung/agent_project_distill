"""Small synthetic rows; no production receipts or approvals are manufactured."""
import copy,gzip,json,sqlite3,sys
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parents[1];T=H/'build/tree'
sys.path[:0]=[str(T),str(T/'generator/derivgen_v7'),str(T/'generator/ground_rows_out')]
from student_pilot.p3_provenance import file_pin,load,write

def gzip_rows(path,rows):
 with gzip.open(path,'xt') as f:
  for row in rows:f.write(json.dumps(row)+'\n')

def pool_fixture(root):
 from student_pilot import s1_pool
 from generator.derivgen_v7.derivgen.ground_v313_tokens import tokenizer_for_rows
 from render_room_v314 import prepare
 from trace_format import room_v314 as R
 import numpy as np
 class Sensor:
  kind='gt'
  def __init__(self):
   self.depth=np.full((32,48,64),2.,dtype=np.float32)
   self.K=np.array([[40.,0.,32.],[0.,40.,24.],[0.,0.,1.]])
   self.valid=np.ones(32,dtype=bool)
  def cam(self,k):return np.diag([1.,-1.,-1.]),np.zeros(3)
  def has(self,k):return bool(self.valid[k-1])
  def frame_of(self,k):return k
 tok=tokenizer_for_rows(str(H/'build/fx/k/input_source_tokenizer.json'))
 frames=list(range(32));pin=dict(path=str(root/'synthetic.npz'),sha256='a'*64)
 canonical='scannet/scene9997_00';geo=Sensor()
 from generator.derivgen_v7.derivgen.room_rows_v314 import QUESTION
 item=dict(qid='room_test',type='room_size_estimation',roles={},question=QUESTION,options=[],
  gt_answer=R.measure(geo)['area_m2'],frame_indices=frames,
  gt_authority=dict(gt=pin,frame_indices=frames,canonical=canonical))
 raw,packed=prepare(item,SimpleNamespace(geo=geo,masks=None),None,tok,canonical=canonical,pin=pin,frames=frames,dev={'scannet/scene9998_00'})
 direct=dict(qid='direct_test',canonical=canonical,question_type='route_planning',head_program=None,score_nomination_allowed=False,
  answer='A',target='<think>\nThe turn is Turn Left.\n</think>\n\nA',question='Where?',options=['A. Turn Left'],
  student_input=dict(question='Where?',options=['A. Turn Left']),
  provenance=dict(canonical=canonical,frame_indices=frames))
 write(root/'dev.json',dict(schema='dev_s1_withhold_v1',canonical={},aliases={},natives=['d1/scene9998_00'],rooms=['d1/scene9998'],physical_groups=[]))
 write(root/'bench.json',dict(schema='benchmark_scene_exclusions_v1',scenes=['d1/scene9999_00'],physical_groups=[],rung1_tokens=[],other_corpora={}))
 exclusions={}
 for name in ('dev_s1','eval_rooms','room_release_gate'):
  path=root/(name+'.tsv');path.write_text('');p=file_pin(path)
  exclusions[name]=dict(list=p['path'],list_sha256=p['sha256'],rows=0)
 for name,key,f in [('dev_s1','withhold','dev.json'),('eval_rooms','v2','bench.json')]:
  p=file_pin(root/f);exclusions[name].update({key:p['path'],key+'_sha256':p['sha256']})
 (root/'remove.jsonl').write_text(json.dumps(dict(row_key='removed'))+'\n')
 sets=[]
 for name,kind,row in [('T0_room','packed',packed),('ROUTE_direct','rows',direct)]:
  path=root/(name+'.jsonl.gz');gzip_rows(path,[row]);sets.append(dict(name=name,status='final',rows_per_type={row['question_type']:1},files={kind:{**file_pin(path),'rows':1,'bytes':path.stat().st_size}}))
 write(root/'manifest.json',dict(schema='dose-pool-s1-manifest-v2',sets=sets,exclusions=exclusions))
 selection=s1_pool.prepare(file_pin(root/'manifest.json'),root/'selected',[file_pin(root/'remove.jsonl')],None)
 assert selection['selected_rows']==2,selection
 return selection,packed,direct

class CharacterTokenizer:
 eos_token='<eos>'
 eos_token_id=0
 pad_token_id=0
 def encode(self,s,**kw):return list(map(ord,s))
 def __call__(self,s,**kw):return dict(input_ids=self.encode(s),offset_mapping=[(i,i+1) for i in range(len(s))])

class Processor:
 tokenizer=CharacterTokenizer()
 _routing_tokens={'ids':{}}
 def apply_chat_template(self,messages,**kwargs):
  prompt='<|im_start|>assistant\n<think>\n'
  if kwargs.get('add_generation_prompt'):return prompt
  return '<|im_start|>assistant\n'+messages[-1]['content']+'<eos>\n'

def routing_fixture(root,selection):
 from student_pilot import carrier_c1_routing as routing
 from student_pilot.s1_routing import frame_request
 alias=routing.alias_of('scannet/scene9997_00');scene=alias.split('/',1)[1]
 write(root/'division.json',dict(schema='diagnostic-whole-scene-division-v1',training_only=True,train_scenes=[alias],heldout_scenes=[]))
 div=file_pin(root/'division.json')
 db=root/'legacy.sqlite'
 with sqlite3.connect(db) as c:c.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
 write(root/'legacy.json',dict(schema=routing.ROUTING_SCHEMA,stream='routing',database=file_pin(db),count=0,division=div,types={}))
 frames=[dict(d='d1',s=scene,i=i,sha256='a'*64,path='/data2/k6tk/aa/'+'a'*64+'.png') for i in range(32)]
 gzip_rows(root/'map.jsonl.gz',frames)
 with gzip.open(root/'plan.json.gz','xt') as f:json.dump(dict(v={scene:dict(g='d1',raw_n=32)}),f)
 write(root/'fps.json',dict(schema='s1-fps-authority-v1',by_scene={alias:30.}))
 (root/'model').mkdir();(root/'model/tokenizer.json').write_text('{}\n')
 write(root/'model.json',dict(kind='base',root=str(root/'model')))
 cfg=dict(streams=dict(routing=file_pin(root/'legacy.json')),training_mode='final',trace_program_version='3.14',
  s1_routing=dict(schema='s1-routing-inputs-v1',selection=file_pin(root/'selected/receipt.json'),catalog={},frame_map=file_pin(root/'map.jsonl.gz'),frame_plan=file_pin(root/'plan.json.gz'),fps_authority=file_pin(root/'fps.json')),
  dev_scene_exclusions=file_pin(root/'dev.json'),benchmark_scene_exclusions=file_pin(root/'bench.json'),remove_files=[file_pin(root/'remove.jsonl')],recipe={},route_table={'room_size_estimation':'route','route_planning':'direct'})
 return cfg,div,file_pin(root/'model.json')
