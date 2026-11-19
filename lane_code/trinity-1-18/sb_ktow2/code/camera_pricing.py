"""Diagnostic camera arms after real G32 text parity; no adoption decision."""
import re
import numpy as np
from common import *
from camera_records import records,frame_binding
from camera_binding import camera_items
from camera import response,ratio_scale,da3_pose
from metrics import K,paired,mean
OUT=ROOT/'out/tower_frames'

def score(item,text):
 kind=item['type']
 if kind=='camera_displacement':
  prediction=float(re.search(r'distance = ([0-9.]+) m',text)[1]);value=100*K.mra(prediction,float(item['truth']))
 elif kind=='camera_rotation':
  prediction=float(re.fullmatch(r'turn = ([+-]?\d+) deg',text)[1]);truth=float(item['truth'])
  value=100*K.mra(abs(prediction),abs(truth)) if prediction*truth>=0 else 0.
 else:
  match=re.search(r'The options are (.+)\.$',item['question'])
  if not match:raise ValueError('MISSING direction options in staged question '+item['id'])
  options=re.split(r', | and ',match[1]);assert len(options)==4
  from student_pilot.head_programs import hp_answer
  prediction=hp_answer(kind,[chr(65+i)+'. '+o for i,o in enumerate(options)],text);value=100.*(prediction==item['truth'])
 return dict(id=item['id'],row_id=item['id'],room=item['room'],type=kind,prediction=prediction,score=value,truth=item['truth'],frame_gap=item['frame_gap'],response=text)

def parity_check(data):
 checks=[];base={};items=data['items'];missing_ids={x['id'] for x in data['skipped']}
 for item in items:
  p=capdir(dict(canonical=item['capture']),OUT/'captures/C32')/'g32.npz'
  if not p.exists():missing_ids.add(item['id']);continue
  g=npz(p);base[item['id']]=g
  text=response(g['raw_pose'],item['scale'],item['gravity'],item['call'])
  checks.append(dict(id=item['id'],equal=text==item['stored_response'],stored=item['stored_response'],recomputed=text))
 matches=sum(r['equal'] for r in checks)
 parity=dict(status='PASS' if matches>=440 else 'BLOCKER',matched=matches,total=450,skipped=len(missing_ids),checks=checks)
 write_json(OUT/'C_PARITY.json',parity)
 return parity,base

def run():
 staged=records();binding=frame_binding()
 if binding['status']!='PASS':
  result=dict(status='MISSING',role='DIAGNOSTIC_ONLY',no_decision_bar=True,frame_binding=binding,records=450,reason='Authoritative frame hashes are required before G32 parity')
  write_json(OUT/'C_CAMERA.txt',result);return result
 data=camera_items();items=data['items'];parity,base=parity_check(data)
 if parity['status']!='PASS':
  result=dict(status='BLOCKER',role='DIAGNOSTIC_ONLY',reason='G32 matched fewer than 440/450 stored strings',parity=parity)
  write_json(OUT/'C_CAMERA.txt',result);return result
 rows=[];skips=[]
 for item in items:
  if item['id'] not in base:continue
  rows.append(dict(score(item,item['stored_response']),arm='G32'))
  if not item['has64']:skips.append(dict(id=item['id'],reason='Fewer than 64 explicitly bound decoded frames'));continue
  folder=capdir(dict(canonical=item['capture']),OUT/'captures/C64');anchors=np.asarray(item['anchor_slots']);d32=base[item['id']]['depth_grid']
  for model in ('G64','DA3_64'):
   p=folder/('g3t.npz' if model=='G64' else 'da3.npz')
   if not p.exists():skips.append(dict(id=item['id'],**missing(p)));continue
   prediction=npz(p)
   if model=='G64':
    raw=prediction['raw_pose'][anchors];d64=prediction['depth_grid'];scale=ratio_scale(item['scale'],d32,d64)
    arms={'camera_rotation':['G64_rot'],'camera_movement_direction':['G64_dir'],'camera_displacement':['G64_disp_proxy']}[item['type']]
   else:
    raw=da3_pose(prediction['c2w'],prediction['intrinsics'],prediction['source_hw'],anchors)
    depth=prediction['depth'][anchors];h,w=depth.shape[1:];ys=np.rint(np.linspace(0,h-1,51)).astype(int);xs=np.rint(np.linspace(0,w-1,51)).astype(int)
    scale=ratio_scale(item['scale'],d32,depth[:,ys[:,None],xs]);arms=['DA3_64','DA3_64_proxy']
   for arm in arms:
    # Rotation and direction have no metric scale treatment; proxy displacement does.
    scale_used=scale if arm.endswith('proxy') else 1.
    text=response(raw,scale_used,item['gravity'],item['call'])
    rows.append(dict(score(item,text),arm=arm,scale=scale_used,sensitivity_only=arm.endswith('proxy')))
 baseline={r['id']:r for r in rows if r['arm']=='G32'};summaries={}
 for arm in sorted({r['arm'] for r in rows if r['arm']!='G32'}):
  rr=[dict(r,delta=r['score']-baseline[r['id']]['score']) for r in rows if r['arm']==arm]
  groups={t:[r for r in rr if r['type']==t] for t in {r['type'] for r in rr}}
  groups.update(displacement_le_025=[r for r in rr if r['type']=='camera_displacement' and float(r['truth'])<=.25],rotation_lt_5=[r for r in rr if r['type']=='camera_rotation' and abs(float(r['truth']))<5])
  groups.update({'frame_gap_'+str(g):[r for r in rr if r['frame_gap']==g] for g in {r['frame_gap'] for r in rr}})
  summaries[arm]={key:dict(n=len(v),mean_score=mean([r['score'] for r in v]),paired_delta=paired(v)) for key,v in groups.items()}
 result=dict(status='OK',role='DIAGNOSTIC_ONLY',no_decision_bar=True,rows=rows,summaries=summaries,skipped=skips,scale_rule='proxy: stored scale times median(G32/G64 depth) over shared anchor grid; own depth unavailable',adoption='Nothing is adopted from Part C')
 write_json(OUT/'C_CAMERA.txt',result)
 from evaluate import items_file
 items_file(rows,'C','devs1')
 return result
