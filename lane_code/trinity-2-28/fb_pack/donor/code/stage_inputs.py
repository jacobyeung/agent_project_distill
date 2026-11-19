from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];R=Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30')
O=W/'out/inputs';O.mkdir(exist_ok=True)
files={
 'fov_variants.py':R/'sb_own400/kit/fov_variants.py',
 'core.py':R/'sb_own400/kit/core.py',
 'runtime.py':R/'sb_own400/kit/runtime.py',
 'TRAIN_CAPTURES.json':R/'sb_own400/kit/inputs/TRAIN_CAPTURES.json',
 'G3T_FOV.json':R/'sb_own400/kit/inputs/G3T_FOV.json',
 'READER_STAGE_PLAN.json':R/'sb_own400/kit/inputs/READER_STAGE_PLAN.json',
 'EXPORT_PINS.json':R/'sb_own400/kit/inputs/EXPORT_PINS.json',
 'GO_TRAIN.json':R/'tree_rebuild10_w/w24/work/build24d/GO_TRAIN.json',
 'GO_RESULT.json':R/'tree_rebuild10_w/w24/work/build24d/GO_RESULT.json',
 'fixture_receipt.json':R/'tree_rebuild10_w/w24/work/build24d/go/p2/q/p/prepare_7eda36539cb74403ac605704a3b81bbd/prepared/s1_receipt.json',
}
pins={}
for n,p in files.items():
 b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();(O/n).write_bytes(b)
cs=json.loads((O/'TRAIN_CAPTURES.json').read_text())['captures'][:2]
fovs=json.loads((O/'G3T_FOV.json').read_text())['captures']
frames={}
for c in cs:
 assert c['k1_split']=='train' and c['split']=='train'
 assert len(c['anchor_indices'])==len(c['anchor_slots'])==32
 v=fovs[c['canonical']]
 assert v['capture_sha256']==hashlib.sha256(json.dumps(c,sort_keys=True,allow_nan=False).encode()).hexdigest()
 assert v['anchor_indices']==c['anchor_indices']
 for index,slot in zip(c['anchor_indices'],c['anchor_slots']):
  f=c['dense_frames'][slot];assert f['index']==index
  p=Path(f['path']);assert p.is_relative_to('/scratch/jjyeung/k1_frames')
  h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==f['sha256'];frames[str(p)]=h
selected={'input_sha256':{**pins,**frames},'captures':cs,'fovs':{c['canonical']:fovs[c['canonical']] for c in cs}}
(W/'out/K1_SELECTION.json').write_text(json.dumps(selected,indent=2)+'\n')
missing=[]
for p in [Path(x['path']) for x in json.loads((O/'READER_STAGE_PLAN.json').read_text())['expanded_files'] if x['role'] in ('artifact','heads')] + [R/'tree_rebuild10_w/w24/work/build24/proofs/capacity/model.json']:
 if not p.exists():missing.append({'status':'MISSING','expected_location':str(p)})
pins['/data2/jjyeung/agent_project_data/distill_design/TOWER_ARM_SCALE_DRIFT_20261119.md']=hashlib.sha256((W/'out/BUILD_RECORD.md').read_bytes()).hexdigest()
pins[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
missing.append({'status':'MISSING','name':'step-544 heads.pt','expected_location':None,'reason':'No checkpoint location supplied; the selected export must be bound through scale_donor.checkpoint.'})
missing.append({'status':'MISSING','name':'production FoV/source pricing decision','expected_location':'N kit scale_donor.fov_source and scale_donor.checkpoint','reason':'The task leaves the frozen K1 decision open; no production variant is inferred.'})
(W/'out/INPUTS.json').write_text(json.dumps({'input_sha256':pins,'frame_sha256':frames,'missing':missing,
 'real_weights_status':'MISSING: step400 heads e72208ac; fixture weights used. Step544 export not supplied.'},indent=2)+'\n')
print('Selected', [c['canonical'] for c in cs],len(frames),'authenticated RGB frames')
