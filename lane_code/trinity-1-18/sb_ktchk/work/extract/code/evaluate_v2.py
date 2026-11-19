"""Train-only factor pricing; held-out values enter only a final report."""
from common import *
import numpy as np
import metrics
from process_guard import require_score
from exclusions import decision_rows,population
from policy import captures,row_ids,consume_heldout
from replay import price,winning_box,flagged_row,selector_diagnostics
from evaluate import geometry,stored_tower,scored,paired_scores,diagnostics,items_file,emit
OUT=ROOT/'out/tower_frames'
_HELDOUT_ACTIVE=False

def arm(C,V,rule):
 assert (C,V) in ((32,32),(64,32),(64,64))
 return f'C{C}_V{V}_{rule}'

def labels(split):
 if split=='heldout' and not _HELDOUT_ACTIVE:raise ValueError('Held-out is accessible only through heldout_once')
 p=Path('/scratch/jjyeung/orch_n30/sb_kbox2')/(split+'_labels.json')
 d=read_json(p);allowed=row_ids(split)
 result={r['id']:float(r['corrected']) for r in d['rows'] if r['id'] in allowed and r['split']==split}
 if set(result)!=allowed:raise ValueError('MISSING corrected labels: '+str(p)+' '+str(sorted(allowed-set(result))))
 return result

def update(part,bars,complete):
 path=OUT/'DECISION.json';d=read_json(path) if path.exists() else dict(bars={},complete={})
 if d.get('status')=='MISSING':d=dict(bars={},complete={})
 if d.get('train_complete'):raise ValueError('Train decisions already frozen')
 d.setdefault('bars',{})[part]=bars;d.setdefault('complete',{})[part]=complete
 d.update(selection_split='K1_train_outside_withheld',decision_rows=1012,full_report_rows=1037,heldout_role='report-only',devS1_role='diagnostic-only',part_B_independent=True)
 d['train_complete']=all(d['complete'].get(x,False) for x in ('A','B'))
 write_json(path,d)

def scale_record(c,tw,own):
 from e2e_reader.stage1 import median_ratio
 from student_pilot.tower_scale import estimate_scale
 slots={int(s):i for i,s in enumerate(tw.get('depth_slots',tw['anchor_slots']))};a=[slots[int(s)] for s in tw['anchor_slots']]
 d,conf=tw['depth_grid'][a],tw['depth_conf_grid'][a]
 scale=median_ratio(d,conf,own['depth'])
 gp=capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz'
 if not gp.is_file():return dict(capture=c['canonical'],scale=scale,stored_scale=None,status='NO_CONVERT_EXPORT',relative_error=None,legacy_relative_error=None)
 stored=float(npz(gp)['scale'])
 legacy=estimate_scale(d,conf,own['depth'])[0]
 return dict(capture=c['canonical'],scale=scale,stored_scale=stored,relative_error=abs(scale-stored)/abs(stored),legacy_range_gate_scale=legacy,legacy_relative_error=abs(legacy-stored)/abs(stored))

def run_a(split='train'):
 require_score(OUT,'A' if split=='train' else 'H')
 lab=labels(split);pose=[];depth=[];scales=[];prices=[];miss=[]
 for c in captures(split):
  p=capdir(c,OUT/'captures/A')/'tower.npz'
  if not p.exists():miss.append(missing(p));continue
  try:
   tws={32:npz(p),64:stored_tower(c)};gt=npz(c['gt']['path']);assert sha(c['gt']['path'])==c['gt']['sha256']
   own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz');cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
   pr=dict(capture=c['canonical'],room=c['room'],split=split);dr=dict(pr)
   for C,tw in tws.items():
    geo,scale=geometry(tw,own)
    pr['G'+str(C)]=metrics.poses(metrics.c2w_pose(tw['raw_pose'][tw['anchor_slots']]),gt['c2w'],scale,gt['valid'])
    dr['G'+str(C)]=metrics.depth_metrics(tw['depth_grid'],gt['depth'],gt['valid'])
    prices+=scored(price(c,geo,cache=cache),arm(C,32,'today'),lab)
    prices+=scored(price(c,geo,gt=gt),arm(C,32,'GTmask'),lab)
    rule=winning_box(dict(capture=c,cache=cache,geometry=geo,n_frames=32))
    if rule:prices+=scored(price(c,geo,cache,box_rule=rule),arm(C,32,'obj'),lab)
   pose.append(pr);depth.append(dr);scales.append(scale_record(c,tws[64],own))
  except (FileNotFoundError,ValueError) as e:miss.append(dict(capture=c['canonical'],status='MISSING',reason=str(e)))
 def rows(C,r):return [x for x in prices if x['arm']==arm(C,32,r)]
 differences=[dict(x,arm='A2') for x in paired_scores(rows(32,'GTmask'),rows(64,'GTmask'))]
 complete=len(pose)==len(captures(split)) and {r['row_id'] for r in rows(32,'today')}==row_ids(split) and not miss
 bars=metrics.a_bars(decision_rows(pose),decision_rows(differences)) if split=='train' and complete else dict(status='MISSING',reason='Complete pinned train population is required')
 checked_scales=[r for r in scales if r['relative_error'] is not None]
 for r in checked_scales:assert r['relative_error']<=1e-4, 'C64 scale disagrees with convert export: '+r['capture']
 if split=='train':
  bars['replace_box_reader_context']=metrics.b_bar(decision_rows(paired_scores(rows(32,'today'),rows(32,'obj')))) if rows(32,'obj') and complete else dict(status='NOT_APPLICABLE' if read_json(ROOT/'configs/KBOX_WINNING_BOX_RULE.json')['status']=='NO_OBJECT_VARIANT' else 'MISSING',reason='No object variant frozen' if read_json(ROOT/'configs/KBOX_WINNING_BOX_RULE.json')['status']=='NO_OBJECT_VARIANT' else 'Complete object-arm rows required')
  full_bars=metrics.a_bars(pose,differences) if complete else dict(status='MISSING')
  full_bars['replace_box_reader_context']=metrics.b_bar(paired_scores(rows(32,'today'),rows(32,'obj'))) if rows(32,'obj') and complete else dict(status='NOT_APPLICABLE')
  require_score(OUT,'A')
  emit('A_POSE.json',pose,status='OK' if complete else 'MISSING',missing=miss)
  emit('A_DEPTH.json',depth,status='OK' if complete else 'MISSING')
  write_json(OUT/'A_SCALE.json',dict(status='OK' if scales else 'MISSING',captures=scales,agreement_fraction=sum(r['relative_error']<=1e-4 for r in checked_scales)/len(checked_scales) if checked_scales else None,rule='e2e_reader.stage1.median_ratio',stored_rule='tower_scale_rule.estimate (0.1 < own_depth < 10)' if checked_scales and all(r['legacy_relative_error']<=1e-4 for r in checked_scales) else 'MISSING'))
  emit('A_DISTANCE.txt',prices,status='OK' if complete else 'MISSING',bars=bars,missing=miss,full_1037_report_only=full_bars,decision_population='K1 train outside withheld rooms (1012 distance rows)')
  update('A',bars,complete);items_file(prices,'A',split)
 return dict(rows=prices,pose=pose,depth=depth,scales=scales,missing=miss,complete=complete)

def gains_once(prices):
 has_obj=read_json(ROOT/'configs/KBOX_WINNING_BOX_RULE.json')['status']=='PASS'
 names=[arm(32,32,'today'),arm(32,32,'obj'),arm(64,64,'obj')] if has_obj else [arm(32,32,'today'),arm(64,64,'today')]
 indexed={name:{r['row_id']:r for r in prices if r['arm']==name} for name in names}
 allowed=row_ids('train')
 if any(set(v)!=allowed for v in indexed.values()):return dict(status='MISSING',reason='All required arms must cover exactly K1_TRAIN_1037',required_arms=names)
 comparisons={'box_gain':(names[0],names[1]),'added_frame_gain':(names[1],names[2]),'joint_gain':(names[0],names[2])} if has_obj else {'added_frame_gain':(names[0],names[1])}
 result={};full={}
 for key,(base,treatment) in comparisons.items():
  rr=paired_scores(list(indexed[base].values()),list(indexed[treatment].values()))
  assert len(rr)==1037
  full[key]=metrics.paired(rr,draws=10000)
  selected=decision_rows(rr);assert len(selected)==1012
  result[key]=metrics.paired(selected,draws=10000)
 return dict(status='OK',rows=1012,gains=result,full_1037_report_only=dict(rows=1037,gains=full),claim='Only joint_gain prices both changes; never add another kit result' if has_obj else 'No object variant frozen: one today frame-gain comparison')

def run_b(split='train'):
 require_score(OUT,'B' if split=='train' else 'H')
 lab=labels(split);prices=[];miss=[];selector=[];alignment=[]
 for c in captures(split):
  p=capdir(c,OUT/'captures/B')
  if not (p/'tower.npz').exists() or not (p/'candidates.json').exists():miss.append(missing(p));continue
  try:
   own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz');tw=stored_tower(c);dense=npz(p/'tower.npz')
   g32,_=geometry(tw,own);g64,_=geometry(dense,own)
   cache32=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json');cache64=read_json(p/'candidates.json')
   anchors=np.asarray(c['anchor_slots']);a=dense['depth_grid'][anchors];b=tw['depth_grid'];ok=np.isfinite(a)&np.isfinite(b)&(abs(b)>0)
   alignment.append(dict(capture=c['canonical'],anchor_proposals=cache64.get('anchor_proposal_check',{'status':'MISSING'}),max_anchor_depth_relative_error=float(np.max(abs(a[ok]-b[ok])/abs(b[ok]))) if ok.any() else None))
   sets={}
   for V,geo,cache in [(32,g32,cache32),(64,g64,cache64)]:
    sets[(V,'today')]=scored(price(c,geo,cache,V),arm(64,V,'today'),lab);prices+=sets[(V,'today')]
    rule=winning_box(dict(capture=c,cache=cache,geometry=geo,n_frames=V))
    if rule:sets[(V,'obj')]=scored(price(c,geo,cache,V,box_rule=rule),arm(64,V,'obj'),lab);prices+=sets[(V,'obj')]
   dense_rows={r['row_id']:r for r in sets[(64,'today')]}
   prices+=scored([flagged_row(r,dense_rows[r['row_id']]) for r in sets[(32,'today')]],'C64_V64_today_flagged',lab)
   gt=npz(c['gt']['path']);selector.append(dict(capture=c['canonical'],N32=selector_diagnostics(c,cache32,g32,32,gt),N64=selector_diagnostics(c,cache64,g64,64,gt)))
  except (FileNotFoundError,ValueError) as e:miss.append(dict(capture=c['canonical'],status='MISSING',reason=str(e)))
 primary='obj' if any(r['arm']==arm(64,32,'obj') for r in prices) else 'today'
 base=[r for r in prices if r['arm']==arm(64,32,primary)];treatment=[r for r in prices if r['arm']==arm(64,64,primary)]
 complete={r['row_id'] for r in base}=={r['row_id'] for r in treatment}==row_ids(split) and not miss
 bars=metrics.b_bar(decision_rows(paired_scores(base,treatment))) if split=='train' and complete else dict(status='MISSING',reason='Complete pinned train population is required')
 if split=='train':
  require_score(OUT,'B')
  emit('B_LADDER_TRAIN.txt',prices,status='OK' if complete else 'MISSING',bar=bars,full_1037_report_only=metrics.b_bar(paired_scores(base,treatment)) if complete else dict(status='MISSING'),decision_population='K1 train outside withheld rooms (1012 distance rows)',primary_rule=primary,missing=miss,selector_top1=selector,label_scope='Anchor members only; GT raster has 32 frames',alignment=alignment,diagnostics={name:diagnostics([r for r in prices if r['arm']==name]) for name in sorted({r['arm'] for r in prices})})
  a_path=OUT/'A_DISTANCE.txt';a=read_json(a_path).get('rows',[]) if a_path.exists() else []
  gains=gains_once(a+prices);write_json(OUT/'B_GAINS_ONCE.txt',gains)
  afg=gains.get('gains',{}).get('added_frame_gain',dict(status='MISSING'))
  afg=dict(afg,verdict='MISSING' if afg.get('status')!='OK' else 'PASS' if afg['low']>0 else 'FAIL')
  update('B',dict(views_pay=bars,added_frame_gain=afg,primary_rule=primary,flagged='REPORT_ONLY'),complete);items_file(prices,'B',split)
 return dict(rows=prices,missing=miss,complete=complete)

def heldout_once():
 global _HELDOUT_ACTIVE
 require_score(OUT,'H')
 p=Path('/scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json')
 if not p.is_file():raise FileNotFoundError('MISSING '+str(p)+'; held-out look not consumed')
 consume_heldout();_HELDOUT_ACTIVE=True
 results=dict(A=run_a('heldout'),B=run_b('heldout'))
 require_score(OUT,'H')
 write_json(OUT/'HELDOUT_once.txt',dict(status='OK' if all(v['complete'] for v in results.values()) else 'MISSING',role='REPORT_ONLY',results=results))
 items_file([dict(r,source_part=part) for part,v in results.items() for r in v['rows']],'H','heldout')
 _HELDOUT_ACTIVE=False
 return results

def run_c():
 from camera_pricing import run
 return run()

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('part',choices=['A','B','C','heldout']);a=p.parse_args()
 code_pins()
 {'A':run_a,'B':run_b,'C':run_c,'heldout':heldout_once}[a.part]()
