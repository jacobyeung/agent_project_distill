"""Freeze train-selected arms and reserve each R0 category before reading predictions."""
from common import *
CATEGORIES={'object_size_estimation':5.,'object_rel_distance':3.,'obj_appearance_order':5.}
PRIMARY=ROOT/'out/object_route/PRIMARY_ARMS.json'
SPEC=ROOT/'inputs/KIT_SPEC_object_route_r0dev_v2.md'

def select_construction(tower,track):
 # Three fully built constructions; no comparison can be inferred from a mean.
 if tower.get('P0_status')!='COMPLETE' or tower.get('P1_status')!='COMPLETE' or track.get('P2_status')!='COMPLETE':
  raise Missing('P0, P1 and P2 training evidence must be complete before selection')
 selected='P1' if tower['P1_minus_P0']['ci95'][0]>0 else 'P0'
 if track['P2_minus_'+selected]['ci95'][0]>0:selected='P2'
 return selected

def freeze(box_path,tower_path,track_path,output=PRIMARY):
 box,tower,track=(js(p) for p in (box_path,tower_path,track_path))
 for d in (box,tower,track):
  if d.get('status')!='COMPLETE' or d.get('selection_split')!='K1-train':raise Missing('Complete K1-train decisions required')
 replace=box['replace_box']=='PASS' and tower['replace_box_32']=='PASS'
 selected=select_construction(tower,track) if replace else None
 first=dict(box['first_seen_pair_rates']);first.update(track.get('first_seen_pair_rates',{}))
 priority=['linker','object','track']
 passing=[s for s in priority if first.get(s) is not None and first[s]>=.90]
 first_source=max(passing,key=lambda s:first[s]) if passing else None
 screen=None
 if selected:
  from ruling0749 import require_size_screen
  try:screen=require_size_screen(ROOT/'out/SELECTED_SIZE_SCREEN.json',selected)
  except Missing:screen=None
 enabled={'object_size_estimation':replace and screen is not None,'object_rel_distance':replace,'obj_appearance_order':bool(first_source)}
 arms={}
 for typ,bar in CATEGORIES.items():
  source=first_source if typ=='obj_appearance_order' else 'track' if selected=='P2' else 'object' if selected else None
  arms[typ]=dict(run=bool(enabled[typ]),source=source,construction=selected,box_rule='obj',frozen_rule=box.get('winning_fusion'),frames=94 if selected=='P1' and typ!='obj_appearance_order' else 32,geometry='g3t_s4',treatment='S4 treatment',program='first_frame_pairs' if typ=='obj_appearance_order' else 'two_candidate' if typ=='object_rel_distance' else typ,form='fallback',bar=dict(type_points=bar,ci95_lower_gt=0),reason='K1 gates passed' if enabled[typ] else 'K1 gate failed; read unspent')
 decisions=[box_path,tower_path,track_path]+([ROOT/'out/SELECTED_SIZE_SCREEN.json'] if screen else [])
 d=dict(status='FROZEN',selection_split='K1-train',arms=arms,decision_sha256={str(local(p)):sha(p) for p in decisions},spec_sha256=sha(SPEC),input_sha256=dict(PINS))
 output=local(output);assert output.is_relative_to(ROOT);output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('x') as f:json.dump(clean(d),f,indent=2)
 with output.with_suffix('.sha256').open('x') as f:f.write(sha(output)+'\n')
 return d

def primary(path=PRIMARY,verify_decisions=True):
 path=local(path);d=js(path)
 if sha(path)!=read(path.with_suffix('.sha256')).decode().strip():raise ValueError('PRIMARY_ARMS changed after freeze')
 assert d['status']=='FROZEN' and d['selection_split']=='K1-train' and set(d['arms'])==set(CATEGORIES)
 assert d['spec_sha256']==sha(SPEC)
 if verify_decisions:
  for p,h in d['decision_sha256'].items():assert sha(p)==h,'K1 decision changed'
 for typ,a in d['arms'].items():
  assert a['form']=='fallback' and a['geometry']=='g3t_s4' and a['box_rule']=='obj'
  assert a['source'] in ('linker','object','track',None)
  assert a['frames'] in ((32,) if typ=='obj_appearance_order' else (32,94))
  if a['run'] and typ=='object_size_estimation':
   from ruling0749 import require_size_screen
   require_size_screen(ROOT/'out/SELECTED_SIZE_SCREEN.json',a['construction'])
  assert a['bar']==dict(type_points=CATEGORIES[typ],ci95_lower_gt=0)
 return d

def reserve(category,path=PRIMARY,look_dir=None):
 d=primary(path);a=d['arms'][category]
 if not a['run']:raise Missing('Category did not pass K1 gates; read remains unspent')
 folder=local(look_dir or ROOT/'out/object_route');assert folder.is_relative_to(ROOT);folder.mkdir(parents=True,exist_ok=True)
 receipt=folder/f'LOOK_{category}.json'
 with receipt.open('x') as f:json.dump(dict(status='RESERVED',category=category,arm=a,primary_sha256=sha(path),input_sha256=dict(PINS)),f,indent=2)
 return receipt,a

def guard_check():
 try:primary(ROOT/'work/nonexistent_primary0749.json')
 except Missing:return dict(status='PASS',missing_primary_refused=True,production_looks=0)
 raise AssertionError('Missing primary was accepted')

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--box',required=True);p.add_argument('--tower',required=True);p.add_argument('--track',required=True);a=p.parse_args();freeze(a.box,a.tower,a.track)
