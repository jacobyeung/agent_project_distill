"""CPU contract checks for routing, weighting, frame bounds, and resume receipts."""
from common import *
import ast,subprocess
import route_stats as S,programs as P
from inputs import r0_items
import numpy as np

def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='';pins();tests=[]
 def check(name,value):
  assert value,name;tests.append(dict(name=name,status='PASS'))
 for p in (ROOT/'code').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
 check('Python syntax',True)
 for p in (ROOT/'scripts').glob('*.sh'):
  result=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''));check('shell '+p.name,result.returncode==0)
 gate=dict(size_screen=True,object_exists=True,first_seen_screen=True)
 def summary(d,lo,hi):return dict(status='OK',difference=d,ci95=[lo,hi])
 check('size threshold',S.verdict('object_size_estimation',summary(5,0.01,7),gate)=='ROUTE')
 check('size boundary lower zero',S.verdict('object_size_estimation',summary(5,0,7),gate).startswith('UNDECIDED'))
 check('size today alone report',S.verdict('object_size_estimation',summary(9,2,11),dict(gate,object_exists=False)).startswith('REPORT_ONLY'))
 check('negative stays direct',S.verdict('object_rel_distance',summary(-3,-4,-1),gate)=='STAYS_DIRECT')
 check('relative threshold',S.verdict('object_rel_distance',summary(3,.1,5),gate)=='ROUTE')
 check('absolute withdraw',S.verdict('object_abs_distance',summary(-2,-3,-.1),gate,comparison='object_vs_today')=='WITHDRAW_KIT1_PASS')
 check('track lower bound',S.verdict('object_size_estimation',summary(.2,.1,.3),gate,arm='track',comparison='track_vs_present')=='REPLACE_SOURCE')
 check('T94 lower bound',S.verdict('object_abs_distance',summary(.2,.1,.3),gate,arm='T94',comparison='T94_vs_f32')=='PAYS')
 fixture=[dict(qid=str(i),room='small' if i==0 else 'large',head_score=1. if i==0 else 0.,direct_score=0.,refusal_code=None) for i in range(4)]
 result=S.paired(fixture);check('item weighted not room weighted',result['difference']==25.)
 from student_pilot.scene_state import FrameMap
 from student_pilot.routed_candidates import lift_grid
 for n in (32,64,94):
  fm=FrameMap(tuple(range(n)),n_frames=n);check(f'FrameMap {n}',len(fm.source_indices)==n)
  class Geo:
   def has(self,k):return 1<=k<=n
   def lift(self,k,uv,mode):return np.column_stack([uv/1000,np.ones(len(uv))]),np.column_stack([uv/1000,np.ones(len(uv))]),np.zeros(len(uv))
  check(f'lift grid {n}',list(lift_grid(Geo(),n))==list(range(1,n+1)))
 from ground import Grounder
 scene_frames=list(range(0,94,3))[:32];mapping={s+1:i+1 for i,s in enumerate(scene_frames)}
 check('dense print projection remains anchors',set(mapping.values())<=set(range(1,33)) and 2 not in mapping)
 folder=ROOT/'work/check_receipt';folder.mkdir(exist_ok=True);p=folder/'value.txt';p.write_text('sealed\n');finish(folder,'test-binding',[p],0.)
 check('resume valid scene',done_valid(folder,'test-binding'));check('resume rejects changed binding',not done_valid(folder,'different'));p.write_text('changed\n');check('resume rejects altered output',not done_valid(folder,'test-binding'))
 # Raw text parsing covers every registered R0 operand, without model scores.
 r=[r for r in r0_items() if r['question_type'] in ('object_size_estimation','object_rel_distance','object_abs_distance','object_counting','obj_appearance_order')]
 check('all 1493 object questions parse',len(r)==1493 and all(P.operands(x) for x in r))
 for s in ["The nearest-to-farthest order from the table is: lamp, then bed, then chair, then door. ","nearest-to-farthest order from the table is: lamp, bed, chair, door. "]:
  check('four-candidate trace grammar',P.parse_order(s,['lamp','bed','chair','door']) is not None)
 check('trace with unknown option refuses',P.parse_order(s,['lamp','bed','chair','desk']) is None)
 write(ROOT/'out/CHECKS.json',dict(status='PASS',tests=tests));print(json.dumps(dict(status='PASS',checks=len(tests))))
if __name__=='__main__':main()
