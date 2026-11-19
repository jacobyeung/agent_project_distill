"""Freeze train-selected arms and reserve each R0 category before reading predictions."""
from common import *
CATEGORIES={'object_abs_distance':3.,'object_size_estimation':5.,'object_rel_distance':3.,'obj_appearance_order':5.}
PRIMARY=ROOT/'out/object_route/PRIMARY_ARMS.json'
SPEC=ROOT/'inputs/KIT_SPEC_object_route_r0dev_v2.md'

def freeze(box_path,tower_path,track_path,output=PRIMARY):
 box,tower,track=(js(p) for p in (box_path,tower_path,track_path))
 for d in (box,tower,track):
  if d.get('status')!='COMPLETE' or d.get('selection_split')!='K1-train':raise Missing('Complete K1-train decision required')
 replace=box['replace_box']=='PASS' and tower['replace_box_32']=='PASS'
 first=dict(box['first_seen_pair_rates']);first.update(track.get('first_seen_pair_rates',{}))
 passing=[s for s,v in first.items() if v is not None and v>=.90]
 first_source=max(passing,key=lambda s:(first[s],s)) if passing else None
 source=track['box_source'];assert source in ('linker','track')
 enabled={'object_abs_distance':replace,'object_size_estimation':replace and box['size_screen']=='PASS' and tower['s4_size_treatment_ci95'][0]>-2.,'object_rel_distance':replace,'obj_appearance_order':bool(passing)}
 arms={}
 for typ,bar in CATEGORIES.items():
  arms[typ]=dict(run=bool(enabled[typ]),source=first_source if typ=='obj_appearance_order' else source,box_rule='obj',frozen_rule=box['winning_fusion'],frames=94 if typ=='object_abs_distance' and tower['views_pay']=='PASS' else 32,geometry='g3t_s4',treatment='S4 treatment',program='first_frame_pairs' if typ=='obj_appearance_order' else 'two_candidate' if typ=='object_rel_distance' else typ,form='fallback',bar=dict(type_points=bar,ci95_lower_gt=0),reason='K1 gates passed' if enabled[typ] else 'K1 gate failed; read unspent')
 sha(SPEC)
 d=dict(status='FROZEN',selection_split='K1-train',arms=arms,decision_sha256={str(local(p)):sha(p) for p in (box_path,tower_path,track_path)},spec_sha256=sha(SPEC),input_sha256=dict(PINS))
 output=local(output);assert output.is_relative_to(ROOT);output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('x') as f:json.dump(clean(d),f,indent=2)
 # A separate immutable digest rejects replacement of PRIMARY_ARMS.
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
  assert a['source'] in (('linker','object','track',None) if typ=='obj_appearance_order' else ('linker','track'))
  assert a['frames'] in ((32,94) if typ=='object_abs_distance' else (32,))
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
 # Synthetic arm decisions never reside at the production PRIMARY_ARMS path.
 import uuid
 folder=ROOT/'work/guard_tests'/uuid.uuid4().hex;folder.mkdir(parents=True)
 p=folder/'PRIMARY_ARMS.json';no_primary=False;twice=False
 try:reserve('object_size_estimation',p,folder)
 except Missing:no_primary=True
 box=dict(status='COMPLETE',selection_split='K1-train',replace_box='PASS',size_screen='PASS',winning_fusion='TEST_ONLY',first_seen_pair_rates={'linker':.95})
 tower=dict(status='COMPLETE',selection_split='K1-train',replace_box_32='PASS',views_pay='MISS',s4_size_treatment_ci95=[-1.,1.])
 track=dict(status='COMPLETE',selection_split='K1-train',box_source='linker',first_seen_pair_rates={})
 paths=[]
 for name,d in [('box',box),('tower',tower),('track',track)]:
  q=folder/(name+'.json');write(q,dict(d,synthetic=True));paths.append(q)
 freeze(*paths,output=p);reserve('object_size_estimation',p,folder)
 try:reserve('object_size_estimation',p,folder)
 except FileExistsError:twice=True
 assert no_primary and twice
 return dict(status='PASS',missing_primary_refused=no_primary,second_read_refused=twice,synthetic=True,production_looks=0)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--box',required=True);p.add_argument('--tower',required=True);p.add_argument('--track',required=True);a=p.parse_args();freeze(a.box,a.tower,a.track)
