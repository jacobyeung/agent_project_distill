"""Pinned dev data only; no aliases, inferred ID maps, or generated frame plans."""
from common import *
from collections import Counter,defaultdict
TYPES=('object_size_estimation','object_rel_distance','obj_appearance_order','object_abs_distance','object_counting')
EXPECTED=dict(zip(TYPES,(293,279,246,290,385)))

def paths():return js(ROOT/'config/PATHS.json')
def r0_items():
 rr=rows(paths()['r0_items'])
 assert all(r['r0_split']=='R0-dev' for r in rr)
 return [dict(r,source_line=i) for i,r in enumerate(rr,1)]

def direct(split,leg='R1'):
 import gzip
 if leg!='R1':raise ValueError('Only registered R1 direct tables are allowed')
 cfg=paths();path=cfg['direct_R1_R0' if split=='R0-dev' else 'direct_R1_S1']
 manifest={n.removeprefix('./'):h for h,n in (line.split() for line in read(ROOT/'inputs/pack/MANIFEST.sha256').decode().splitlines())}
 blob=read(path);assert PINS[str(local(path))]==manifest[Path(path).name]
 rr=[json.loads(x) for x in gzip.decompress(blob).splitlines() if x.strip()]
 assert all(r['set']==split and r['step']==200 and r['run']=='R1' for r in rr)
 key='source_line' if split=='R0-dev' else 'id'
 assert len({r[key] for r in rr})==len(rr)
 return {r[key]:dict(r,prediction=r['pred'],qid=r.get('qid',r['id'])) for r in rr}

def join_report(items,table):
 for line,d in table.items():
  assert isinstance(line,int) and 1<=line<=len(items)
  r=items[line-1]
  assert (d['qid'],d['question'],d['type'],d['scene'])==(r['qid'],r['question'],r['question_type'],r['scene'])
 return {t:dict(items=sum(r['question_type']==t for r in items),joined=sum(r['type']==t for r in table.values())) for t in sorted({r['type'] for r in table.values()})}

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
 cfg=paths();table=direct('dev-S1');request=js(ROOT/'inputs/local/DEVS1_REQUEST.json')
 relevant=[r for r in table.values() if r['type'] in ('object_counting','object_size_estimation','object_rel_distance')]
 if not local(cfg['devs1_plan']).is_file():
  return [],[dict(id=r['id'],type=r['type'],reason='MISSING sha-bound staging plan',expected_path=str(local(cfg['devs1_plan']))) for r in relevant],table
 plan=js(cfg['devs1_plan']);assert sha(cfg['devs1_plan'])==request['plan_sha256']
 bindings={r['id']:r for r in plan['items']};kept=[];skipped=[]
 for row in relevant:
  b=bindings.get(row['id'])
  if b is None or len(b['frames'])!=32:
   skipped.append(dict(id=row['id'],reason='MISSING exact item binding'));continue
  assert b['question']==row['question'] and b['room']==row['room']
  try:
   assert [f['index'] for f in b['frames']]==b['source_frame_indices']
   for f in b['frames']:assert local(f['path']).is_relative_to(local(request['frame_root'])) and sha(f['path'])==f['sha256']
  except (Missing,AssertionError):
   skipped.append(dict(id=row['id'],reason='MISSING/mismatched frame pin'));continue
  assert b['dataset'] in ('scannet','scannetpp','arkitscenes')
  kept.append(dict(row,question_type=row['type'],answer=row['gt_released'],dataset=b['dataset'],scene=b['scene'],source_frame_indices=b['source_frame_indices'],frames=b['frames'],split='dev-S1'))
 return kept,skipped,table
