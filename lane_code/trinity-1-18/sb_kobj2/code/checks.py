"""Regression checks for v2 leakage boundaries, fallbacks, and resume integrity."""
from common import *
import ast,subprocess,uuid
import route_stats as S,programs as P
from scoring import Scorer
from registration import guard_check

def main():
 pins();tests=[]
 def check(name,value):
  assert value,name;tests.append(dict(name=name,status='PASS'))
 for p in (ROOT/'code').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
 check('Python syntax',True)
 pack=Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack')
 manifest={n.removeprefix('./'):h for h,n in (line.split() for line in read(ROOT/'inputs/pack/MANIFEST.sha256').decode().splitlines())}
 checked=0
 for line in read(ROOT/'inputs/pack/R1_A4_SRC_SHA256.txt').decode().splitlines():
  h,n=line.split();rel='r1_src/'+n
  if rel in manifest:assert h==manifest[rel]==sha(pack/rel);checked+=1
 check('R1_A4 source hashes agree with pack',checked>0)
 for p in (ROOT/'scripts').glob('*.sh'):
  check('shell '+p.name,subprocess.run(['bash','-n',str(p)],capture_output=True).returncode==0)
 rr=[dict(qid='same',source_line=i+1,room='small' if i==0 else 'large',head_score=1. if i==0 else 0.,direct_score=0.,refusal_code=None,prediction=1,direct_prediction=0,subtype='') for i in range(4)]
 check('source_line identities and item weighting',S.paired(rr)['difference']==25.)
 check('absolute distance uses +3 bar',S.summary('object_abs_distance',rr,{'bar':{'type_points':3}})['verdict']=='MISS')
 check('bootstrap repeated room fixture CI includes zero',S.paired(rr)['ci95'][0]==0)
 check('scorer threshold inclusive',Scorer()({'type':'object_size_estimation','gt_released':'100'},50)==.1)
 check('missing prediction scores zero',Scorer()({'type':'object_size_estimation','gt_released':'100'},None)==0)
 item=dict(question_type='obj_appearance_order',question='What will be the first-time appearance order of the following categories in the video: chair, desk, lamp?',options=['A. chair, desk, lamp','B. desk, chair, lamp'])
 def ground(n):return dict(seen=True,frames=[1],first={'chair':1,'desk':1,'lamp':2}[n],tie_index=(1,0))
 check('equal first frames leave both options open',P.run(item,ground,'D')['prediction']=='D')
 item['options']=['A. chair, desk, lamp','B. lamp, chair, desk']
 check('unique partial order chooses A',P.run(item,ground,'D')['prediction']=='A')
 size=dict(question_type='object_size_estimation',question='What is the size of the chair, measured in centimeters?',unit='cm',options=[])
 check('refused size keeps direct',P.run(size,lambda n:dict(seen=False,box_available=False),17)['prediction']==17)
 check('refused size strict scores zero',P.run(size,lambda n:dict(seen=False,box_available=False),17,variant='strict')['prediction'] is None)
 check('one look guard',guard_check()['status']=='PASS')
 folder=ROOT/'work/check_receipt'/uuid.uuid4().hex;folder.mkdir(parents=True);p=folder/'value.txt';p.write_text('sealed\n');finish(folder,'test-binding',[p],0.)
 check('resume valid scene',done_valid(folder,'test-binding'));check('resume rejects changed binding',not done_valid(folder,'different'));p.write_text('changed\n');check('resume rejects altered output',not done_valid(folder,'test-binding'))
 import budget
 check('all v2 hard stops',budget.BUDGETS=={'K1_track':6300,'R0_f32':12600,'track':11700,'T94':10800,'dev-S1':7200,'S1_track':3600})
 check('no production look consumed',not list((ROOT/'out/object_route').glob('LOOK_*.json')))
 write(ROOT/'out/CHECKS.json',dict(status='PASS',tests=tests));print(json.dumps(dict(status='PASS',checks=len(tests))))
if __name__=='__main__':main()
