"""Price cached arms and emit the preregistered bars; no model forwards."""
import argparse, copy, json, re, time
from common import *
import numpy as np
from metrics import poses,c2w_pose,depth_metrics,K,paired,a_bars,b_bar,c_bar,mean
from replay import price,winning_box,flagged_row,selector_diagnostics
from camera import parity,response,ratio_scale,da3_pose
OUT=ROOT/'out/tower_frames'

def labels(split):
 path=Path('/scratch/jjyeung/orch_n30/sb_kbox')/(split+'_labels.json')
 data=read_json(path);return {r['id']:float(r['corrected']) for r in data['rows'] if r['split']==split}

def scored(rows,arm,lab):
 out=[]
 for r in rows:
  x=dict(r,arm=arm)
  if r['row_id'] not in lab:x.update(status='MISSING',missing='corrected label '+r['row_id'],score=None)
  else:x.update(label=lab[r['row_id']],score=100*K.mra(r['prediction'] if r['prediction'] is not None else float('nan'),lab[r['row_id']]))
  out.append(x)
 return out

def paired_scores(base,other):
 lookup={r['row_id']:r for r in base};out=[]
 for r in other:
  a=lookup.get(r['row_id'])
  if a is None or r.get('score') is None or a.get('score') is None:continue
  assert r['room']==a['room'] and r['split']==a['split']
  out.append(dict(r,delta=r['score']-a['score']))
 return out

def geometry(tw,own,depth_slots=None):
 from e2e_reader.geometry import from_tower
 from student_pilot.tower_scale import estimate_scale
 slots=tw.get('depth_slots',tw['anchor_slots']) if depth_slots is None else depth_slots
 anchors=tw['anchor_slots'];lookup={int(s):i for i,s in enumerate(tw.get('depth_slots',anchors))};where=[lookup[int(i)] for i in anchors]
 scale,_,_=estimate_scale(tw['depth_grid'][where],tw['depth_conf_grid'][where],own['depth'])
 hw=tw.get('source_hw')
 if hw is None:raise ValueError('MISSING source_hw from tower PHASE_COMPLETE.json')
 geo=from_tower(tw['raw_pose'],slots,tw['frame_indices'],tw['depth_grid'],tw['grid_uv'],own['gravity'],scale,hw)
 from reference.gravity_guard import validate_up_convention
 validate_up_convention(geo.C)
 return geo,scale

def stored_tower(c):
 folder=capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2');tw=npz(folder/'tower.npz');rec=read_json(folder/'PHASE_COMPLETE.json')
 assert rec['capture_sha256']==digest(c)
 assert INPUTS[str(local(folder/'tower.npz'))]==rec['files']['tower.npz']
 tw['source_hw']=np.array(rec['source_hw']);return tw

def emit(name,rows,status='OK',**extra):
 write_json(OUT/name,dict(status=status,rows=rows,**extra))

def items_file(rows,part,split):
 path=OUT/f'PER_ITEM_{part}_{split}.jsonl'
 with path.open('w') as f:
  for r in rows:f.write(json.dumps(clean(dict(r,input_sha256=dict(INPUTS))),sort_keys=True,allow_nan=False)+'\n')
 # Canonical combined output is rebuilt only from lane-owned, hashed part receipts.
 allrows=[]
 for p in sorted(OUT.glob('PER_ITEM_*_*.jsonl')):
  sha(p);allrows.extend(p.read_text().splitlines())
 (OUT/'PER_ITEM.jsonl').write_text('\n'.join(allrows)+'\n' if allrows else '')

def update_decision(part,value):
 path=OUT/'DECISION.json';d=read_json(path) if path.exists() else {'bars':{}}
 d['bars'][part]=value;write_json(path,d)

def part_a():
 pose_rows=[];dep=[];distance=[];miss=[];priced=[]
 lab={}
 for split in ('train','heldout'):
  try:lab[split]=labels(split)
  except FileNotFoundError:lab[split]={}
 for c in manifest()['captures']:
  if not Path(c['gt']['path']).is_file():miss.append(missing(c['gt']['path']));continue
  path=capdir(c,OUT/'captures/A')/'tower.npz'
  if not path.exists():miss.append(missing(path));continue
  try:
   g32=npz(path);g64=stored_tower(c);gt=npz(c['gt']['path']);own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz')
   assert np.array_equal(gt['frame_indices'],c['anchor_indices']);assert sha(c['gt']['path'])==c['gt']['sha256']
   row=dict(capture=c['canonical'],room=c['room'],split=c['k1_split']);dr=dict(row)
   geometries={}
   for arm,tw in [('G32',g32),('G64',g64)]:
    geo,scale=geometry(tw,own);geometries[arm]=geo
    row[arm]=poses(c2w_pose(tw['raw_pose'][tw['anchor_slots']]),gt['c2w'],scale,gt['valid']);dr[arm]=depth_metrics(tw['depth_grid'],gt['depth'],gt['valid'])
   pose_rows.append(row);dep.append(dr)
   cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
   for mask_arm in ('A0','A2'):
    sets={}
    for tower_arm,geo in geometries.items():
     sets[tower_arm]=scored(price(c,geo,cache=cache,gt=gt if mask_arm=='A2' else None),mask_arm+'_'+tower_arm,lab[c['k1_split']]);priced.extend(sets[tower_arm])
    distance.extend(dict(r,arm=mask_arm) for r in paired_scores(sets['G32'],sets['G64']))
  except (FileNotFoundError,ValueError) as e:miss.append(dict(capture=c['canonical'],status='MISSING',error=str(e)))
 emit('A_POSE.json',pose_rows,status='MISSING' if not pose_rows else 'OK',missing=miss)
 emit('A_DEPTH.json',dep,status='MISSING' if not dep else 'OK')
 bars=a_bars(pose_rows,distance);emit('A_DISTANCE.txt',distance,status='MISSING' if not distance else 'OK',bars=bars)
 update_decision('A',bars);items_file(priced,'A','all')
 return bars

def check_review(split):
 if split!='heldout':return
 review=read_json(ROOT/'configs/CODE_REVIEW.json')
 if review.get('status')!='APPROVED' or review.get('code_sha256')!=digest(code_pins()):raise ValueError('MISSING code-review approval for current code')
 if (OUT/'B_HELDOUT_once.txt').exists() and read_json(OUT/'B_HELDOUT_once.txt').get('status')!='MISSING':raise ValueError('Held-out look already consumed')

def diagnostics(rows):
 operands=[f for r in rows for f in r['printed_frames']];bands={}
 for low,high,name in [(0,1,'0'),(1,2,'1'),(2,3,'2'),(3,5,'3-4'),(5,10**9,'5+')]:
  rr=[r for r in rows if low<=r['min_member_frames']<high];bands[name]=dict(n=len(rr),score=mean([r['score'] for r in rr if r.get('score') is not None]))
 return dict(operands=len(operands),share_three_plus=sum(len(v)>=3 for v in operands)/len(operands) if operands else None,by_minimum_member_frames=bands)

def part_b(split):
 check_review(split);lab=labels(split);allrows=[];miss=[];selector=[]
 decision=read_json(OUT/'DECISION.json')['bars'].get('A',{})
 if decision.get('run_64_arms')!='PASS':raise ValueError('Part A has not passed a 64-frame bar')
 from e2e_reader.geometry import from_npz
 for c in manifest()['captures']:
  if c['k1_split']!=split:continue
  p=capdir(c,OUT/'captures/B')
  if not (p/'tower.npz').exists() or not (p/'candidates.json').exists():miss.append(missing(p));continue
  try:
   cache32=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json');gpath=capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz';sha(gpath);geo32=from_npz(gpath)
   tw=npz(p/'tower.npz');own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz');geo64,_=geometry(tw,own);cache64=read_json(p/'candidates.json')
   f32=scored(price(c,geo32,cache32,32),'F32',lab);f64=scored(price(c,geo64,cache64,64),'F64',lab)
   allrows.extend(f32+f64);byid={r['row_id']:r for r in f64}
   flags=[flagged_row(r,byid[r['row_id']]) for r in f32];allrows.extend(scored(flags,'F64_flagged',lab))
   rule=winning_box(dict(capture=c,cache=cache64,geometry=geo64,n_frames=64))
   if rule:allrows.extend(scored(price(c,geo64,cache64,64,box_rule=rule),'F64_fused',lab))
   gt=npz(c['gt']['path']);selector.append(dict(capture=c['canonical'],F32=selector_diagnostics(c,cache32,geo32,32,gt),F64=selector_diagnostics(c,cache64,geo64,64,gt)))
  except (FileNotFoundError,ValueError) as e:miss.append(dict(capture=c['canonical'],status='MISSING',error=str(e)))
 base=[r for r in allrows if r['arm']=='F32'];bars={};diag={}
 for arm in ('F32','F64','F64_flagged','F64_fused'):
  r=[r for r in allrows if r['arm']==arm];diag[arm]=diagnostics(r)
  if arm!='F32':bars[arm]=b_bar(paired_scores(base,r))
 filename='B_LADDER_TRAIN.txt' if split=='train' else 'B_HELDOUT_once.txt'
 emit(filename,allrows,status='MISSING' if not allrows else 'OK',bars=bars,diagnostics=diag,selector_top1=selector,missing=miss)
 if split=='heldout':
  tr=read_json(OUT/'B_LADDER_TRAIN.txt')['rows'];complete=tr+allrows;ref=[r for r in complete if r['arm']=='F32'];bars={arm:b_bar(paired_scores(ref,[r for r in complete if r['arm']==arm])) for arm in ('F64','F64_flagged','F64_fused')}
 update_decision('B',bars);items_file(allrows,'B',split);return bars

def camera_items():
 # This is an explicit interchange contract, not an inferred scene/frame join.
 path=ROOT/'inputs/CAMERA_ITEMS.json';d=read_json(path)
 if d.get('source')!='/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py' or d.get('step')!=544:raise ValueError('Unbound camera input producer')
 if len(d['items'])!=450:raise ValueError('Camera parity requires all 450 routed items')
 if len({x['id'] for x in d['items']})!=450:raise ValueError('Duplicate camera item IDs')
 for x in d['items']:
  if np.asarray(x['raw_pose32']).shape!=(32,9) or np.asarray(x['depth32']).shape!=(32,51,51):raise ValueError('Missing stored 32-frame pose/depth arrays')
  if len(x['anchor_slots'])!=32:raise ValueError('Camera LM frame map differs')
 for pin in d['sources']:
  assert sha(pin['path'])==pin['sha256']
 return d

def part_c():
 data=camera_items();items=data['items'];p=parity(items);write_json(OUT/'C_PARITY.json',p)
 if p['status']!='PASS':raise ValueError('BLOCKER: camera parity below 440/450')
 rows=[];skips=[];go64=read_json(OUT/'DECISION.json')['bars']['A'].get('run_64_arms')=='PASS'
 for item in items:
  capture=item['capture'];folder=OUT/'captures/C'/digest(capture)[:16];base=item['stored_response'];kind=item['type']
  for arm in ('G32','G64','DA3_64','DA3_64_ownscale'):
   if arm=='G64' and not go64:continue
   if arm=='G32':text=base
   else:
    path=folder/('g3t.npz' if arm=='G64' else 'da3.npz')
    if not path.exists():skips.append(dict(id=item['id'],arm=arm,**missing(path)));continue
    out=npz(path);anchors=np.array(item['anchor_slots']);depth32=np.asarray(item['depth32'])
    if arm=='G64':
     raw=out['raw_pose'][anchors]
     assert np.array_equal(out['anchor_slots'],anchors)
     scale=ratio_scale(item['scale'],depth32,out['depth_grid'])
    else:
     raw=da3_pose(out['c2w'],out['intrinsics'],out['source_hw'],anchors);scale=1.
     if arm.endswith('ownscale'):
      depths=out['depth'][anchors];h,w=depths.shape[1:];ys=np.rint(np.linspace(0,h-1,51)).astype(int);xs=np.rint(np.linspace(0,w-1,51)).astype(int)
      scale=ratio_scale(item['scale'],depth32,depths[:,ys[:,None],xs])
    text=response(raw,scale,item['gravity'],item['call'])
   if kind=='camera_displacement':
    match=re.search(r'distance = ([0-9.]+) m',text);prediction=float(match[1]);score=100*K.mra(prediction,float(item['truth']))
   elif kind=='camera_rotation':
    prediction=abs(float(re.fullmatch(r'turn = ([+-]?\d+) deg',text)[1]));score=100*K.mra(prediction,abs(float(item['truth'])))
   else:
    from student_pilot.head_programs import hp_answer
    prediction=hp_answer(kind,item['options'],text)
    score=100.*(prediction==item['truth'])
   rows.append(dict(id=item['id'],row_id=item['id'],room=item['room'],type=kind,arm=arm,prediction=prediction,score=score,response=text,truth=item['truth'],frame_gap=item['frame_gap']))
 base={r['id']:r for r in rows if r['arm']=='G32'};bars={}
 for arm in ('G64','DA3_64','DA3_64_ownscale'):
  rr=[dict(r,delta=r['score']-base[r['id']]['score']) for r in rows if r['arm']==arm];bars[arm]=c_bar(rr)
 bands={}
 for arm in ('G32','G64','DA3_64','DA3_64_ownscale'):
  rr=[r for r in rows if r['arm']==arm];bands[arm]={name:dict(n=len(v),score=mean([r['score'] for r in v])) for name,v in {
   'displacement_le_025':[r for r in rr if r['type']=='camera_displacement' and float(r['truth'])<=.25],
   'rotation_lt_5':[r for r in rr if r['type']=='camera_rotation' and abs(float(r['truth']))<5],
   **{'frame_gap_'+str(g):[r for r in rr if r['frame_gap']==g] for g in sorted({r['frame_gap'] for r in rr})}}.items()}
 emit('C_CAMERA.txt',rows,bars=bars,skipped=skips,diagnostics=bands,scale_rule='stored scale times median(G32 depth / challenger depth) on shared anchors; own depth unavailable')
 update_decision('C',bars);items_file(rows,'C','devs1');return bars

def main():
 p=argparse.ArgumentParser();p.add_argument('part',choices=['A','B','C']);p.add_argument('--split',choices=['train','heldout'],default='train');a=p.parse_args();code_pins();OUT.mkdir(parents=True,exist_ok=True)
 print({'A':part_a,'B':lambda:part_b(a.split),'C':part_c}[a.part]())
if __name__=='__main__':main()
