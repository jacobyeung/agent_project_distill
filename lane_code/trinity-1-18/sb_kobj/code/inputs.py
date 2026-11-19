"""Pinned dev data only; no aliases, inferred ID maps, or generated frame plans."""
from common import *
from collections import Counter,defaultdict
TYPES=('object_size_estimation','object_rel_distance','obj_appearance_order','object_abs_distance','object_counting')
EXPECTED=dict(zip(TYPES,(293,279,246,290,385)))

def paths():return js(ROOT/'config/PATHS.json')
def r0_items():
 rr=rows(paths()['r0_items'])
 assert all(r['r0_split']=='R0-dev' for r in rr)
 return rr

def direct(split,leg='R1'):
 cfg=paths();key=f'direct_{leg}_'+('R0' if split=='R0-dev' else 'S1')
 # The export must come from san_kit and its actual qid map, never a question-text join.
 receipt=js(cfg['direct_export_receipt']);entry=receipt['exports'][f'{leg}:200:{split}']
 assert sha(cfg[key])==entry['sha256']
 assert entry['source_call']==f"san_kit.direct('{leg}', 200, '{split}')"
 assert entry['idmap_sha256'] and entry['scorer_sha256']
 rr=rows(cfg[key]);assert all(r['qid'] and r['type'] and 'prediction' in r and 'score' in r and 'text' in r for r in rr)
 assert len({r['qid'] for r in rr})==len(rr),'Duplicate direct qid'
 assert all(r.get('split',split)==split for r in rr)
 return {r['qid']:r for r in rr}

def join_report(items,table):
 out={}
 for typ in TYPES:
  rr=[r for r in items if r['question_type']==typ]
  joined=[r for r in rr if r['qid'] in table and table[r['qid']]['type']==typ]
  out[typ]=dict(items=len(rr),joined=len(joined),missing=len(rr)-len(joined),status='PASS' if len(joined)==len(rr) else 'MISSING')
 return out

def r0_scenes(items,open_scene=False):
 from PIL import Image
 master=js(paths()['r0_manifest']);root=local(paths()['r0_root']);by=defaultdict(list)
 for r in items:by[r['scene']].append(r)
 scenes=[]
 for scene,rr in sorted(by.items()):
  entry=master['scenes']['scannetpp/'+scene];assert entry['r0_split']=='R0-dev'
  p=root/'out/frame_manifests'/f'{scene}.json';m=js(p);assert PINS[str(p)]==entry['manifest_sha256']
  f32=m['layout_f32'];f64=m['layout_f64'];union=sorted(set(f32)|set(f64));shared=sorted(set(f32)&set(f64))
  assert len(f32)==32 and len(f64)==64 and len(union)==94 and len(shared)==2
  assert not set(f32)<=set(f64) and m['count_match'] and not m['missing']
  assert all(r['frame_indices']==f32 for r in rr)
  assert set(map(int,m['frames']))==set(union)
  frames=[dict(index=i,path=str(root/'frames/scannetpp'/scene/f'{i:06d}.png'),sha256=m['frames'][str(i)]) for i in union]
  result=dict(scene=scene,dataset='scannetpp',room='scannetpp/'+scene,split='R0-dev',f32=f32,f64=f64,union=union,shared=shared,frames=frames,anchor_slots=[union.index(i) for i in f32])
  if open_scene and not scenes:
   for f in frames:
    assert sha(f['path'])==f['sha256']
    with Image.open(local(f['path'])) as im:im.load();assert list(im.size)==m['size']
   result['opened_verified']=len(frames)
  scenes.append(result)
 return scenes

def devs1():
 cfg=paths();table=direct('dev-S1');request=js(ROOT/'inputs/local/DEVS1_REQUEST.json');plan=js(cfg['devs1_plan'])
 assert PINS[str(local(cfg['devs1_plan']))]==request['plan_sha256'],'Staging plan pin mismatch'
 # The plan must explicitly bind source indices to pinned local files.
 bindings={(r['qid'],tuple(r['source_frame_indices'])):r for r in plan['items']}
 kept=[];skipped=[]
 for row in table.values():
  if row['type'] not in ('object_counting','object_size_estimation','object_rel_distance'):continue
  key=(row['qid'],tuple(row['source_frame_indices']));b=bindings.get(key)
  if b is None or len(b['frames'])!=32:skipped.append(dict(qid=row['qid'],reason='MISSING frame pin binding'));continue
  try:
   assert [f['index'] for f in b['frames']]==row['source_frame_indices']
   for f in b['frames']:assert local(f['path']).is_relative_to(local(request['frame_root'])) and sha(f['path'])==f['sha256']
  except (Missing,AssertionError):skipped.append(dict(qid=row['qid'],reason='MISSING or mismatched pinned frame'));continue
  assert row['dataset'] in ('scannet','scannetpp','arkitscenes')
  kept.append(dict(row,question_type=row['type'],frames=b['frames'],split='dev-S1'))
 return kept,skipped,table
