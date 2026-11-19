"""Build review receipts without model execution or fabricated result rows."""
import ast,difflib,hashlib,json,tarfile,time
from common import *
OUT=ROOT/'out/tower_frames';OUT.mkdir(exist_ok=True,parents=True)

def edited():
 sources=read_json(ROOT/'inputs/CODE_SOURCES.json')['input_sha256'];edits=[];diffs=[]
 for origin,expected in sources.items():
  if '/tree_b01ce449/' in origin:rel=origin.split('/tree_b01ce449/',1)[1]
  elif '/b04_e2ehook/' in origin:rel=origin.split('/b04_e2ehook/',1)[1]
  else:continue
  target=ROOT/'code/vendor'/rel
  if not target.exists():continue
  old=Path(origin).read_text();assert hashlib.sha256(old.encode()).hexdigest()==expected
  new=target.read_text()
  if old==new:continue
  diffs.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=origin,tofile=str(target)))
  for tag,a,b,c,d in difflib.SequenceMatcher(None,old.splitlines(),new.splitlines()).get_opcodes():
   if tag!='equal':edits.append(dict(file=str(target.relative_to(ROOT)),original_lines=list(range(a+1,b+1)),edited_lines=list(range(c+1,d+1)),old=old.splitlines()[a:b],new=new.splitlines()[c:d]))
 write_json(ROOT/'out/EDITED_LINES.json',dict(edits=edits));(ROOT/'out/EDITED_LINES.patch').write_text(''.join(diffs))
 return edits

def placeholders():
 spec=ROOT/'inputs/KIT_SPEC_tower_frames.md';sha(spec);dry=read_json(ROOT/'out/DRYRUN.json')
 for name,dependency in [('A_POSE.json','out/tower_frames/captures/A/<capture>/tower.npz'),('A_DEPTH.json','out/tower_frames/captures/A/<capture>/tower.npz'),('A_DISTANCE.txt','out/tower_frames/captures/A/<capture>/tower.npz'),('B_LADDER_TRAIN.txt','out/tower_frames/captures/B/<capture>/tower.npz'),('B_HELDOUT_once.txt','configs/CODE_REVIEW.json and completed B train pass'),('C_CAMERA.txt','inputs/CAMERA_ITEMS.json'),('C_PARITY.json','/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py')]:
  if not (OUT/name).exists():write_json(OUT/name,dict(status='MISSING',rows=[],expected_input=dependency,reason='CPU kit only; required real inputs or GPU captures are not available'))
 if not (OUT/'PER_ITEM.jsonl').exists():(OUT/'PER_ITEM.jsonl').write_text('')
 write_json(OUT/'DECISION.json',dict(status='MISSING',gpu_hours_used=0,bars={
  'A':{'pose_move':'MISSING','pose_short_displacement':'MISSING','lifting':'MISSING','run_64_arms':'MISSING'},
  'B':{'F64':'MISSING','F64_fused':'MISSING','F64_flagged':'MISSING'},
  'C':{'parity':'MISSING','G64':'MISSING','DA3_64':'MISSING','DA3_64_ownscale':'MISSING'}}))
 write_json(OUT/'PASS_TIMING.json',dict(gpu_passes=[],gpu_hours_used=0,CPU_dryrun_seconds=dry['seconds'],CPU_peak_kib=dry['peak_cpu_kib'],K1_G3T64_peak=dry['K1_peak_memory']))
 missing_gt=[c['gt']['path'] for c in manifest()['captures'] if not Path(c['gt']['path']).exists()]
 write_json(ROOT/'out/INPUT_AUDIT.json',dict(manifest_captures=300,present_GT_captures=300-len(missing_gt),missing_GT=missing_gt,missing_camera_module='/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py',named_tree_missing='/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449',used_tree='/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449',kbox_A0=dry['B']))

if __name__=='__main__':
 pins=code_pins();write_json(ROOT/'out/CODE_SHA256.json',dict(files=pins,code_sha256=digest(pins)));edited();placeholders();print('review artifacts written')
