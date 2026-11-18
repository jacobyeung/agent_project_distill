from pathlib import Path
import json,hashlib,shutil,io
from PIL import Image
W=Path(__file__).resolve().parent.parent;R=W/'out2';G=R/'gates'
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def js(p,v):put(p,(json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Restore local lookup paths without altering delivered source.
(G/'base/work').mkdir(exist_ok=True)
p=G/'run_all.py';s=p.read_text().replace("env=dict(os.environ,OMP_NUM_THREADS", "env=dict(os.environ,PATH='/usr/bin:/bin',OMP_NUM_THREADS");p.write_text(s)
p=G/'base/b1/tests/test_constraints.py';s=p.read_text().replace("P = ROOT/'out/production'", "P = Path("+repr(str(R/'bases/b1/src'))+")");p.write_text(s)
p=G/'base/b1/tests/test_package.py';s=p.read_text().replace("str(Path("+repr(str(G/'lost/repin'))+")/'in/prod_pkg/a/1.json')", "str(OUT/'inputs_tower.json')");p.write_text(s)
p=G/'base/b2/tests/test_constraints.py';s=p.read_text().replace("B=O.parent.parent/'b1g/out'", "B=Path("+repr(str(R/'bases/b1'))+")");p.write_text(s)
# Structural wrong-config fixtures: real R1 config/receipt; synthetic data envelope.
root=G/'lost/repin/in/h1_1_run_inputs';cfgraw=(W/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json').read_bytes();cfg=json.loads(cfgraw)
p=root/'inputs/prepare_b000cf6bbd2346a59dc1d213e84ad066/config.json';put(p,cfgraw)
data=dict(schema='s1-in-job-data-v1',status='PREPARED',real_frames_verified=True,rehearsal=False,config=dict(path=str(p),sha256=sha(p)),preparation=cfg['preparation'])
js(root/'inputs/data_receipt.json',data);js(root/'binding.json',dict(preparation=cfg['preparation'],config_sha256=json.loads((W/'in/binding.json').read_text())['config_sha256']));js(root/'inputs/request.json',dict(config={'sha256':'0'*64}))
# Rebuild local room CPU fixture RGBs and capture manifests. Model stubs remain in
# the exact tower_sequence.py. These pixels are synthetic, never baseline reads.
for mode in ('base','release'):
 o=G/mode/'b2';source=o/'src';overlay=o/'fixture_src';overlay.mkdir(exist_ok=True)
 for p in source.iterdir():
  dest=overlay/p.name
  if p.name in ('h1eval','inputs'):
   shutil.copytree(p,dest,dirs_exist_ok=True)
  elif not dest.exists():dest.symlink_to(p.resolve(),target_is_directory=p.is_dir())
 stage=o/'cpu_fixture';frames=stage/'frames';frames.mkdir(parents=True,exist_ok=True);pins=[]
 for i in range(32):
  p=frames/('%02d.png'%i);Image.new('RGB',(64,48),(i*7%256,37,81)).save(p);pins.append(dict(path=p.name,sha256=sha(p)))
 def captures(v):
  cs=v['captures'];cs={c['native']:c for c in cs} if isinstance(cs,list) else cs
  for c in cs.values():
   c['frames']=[dict(p,index=n) for p,n in zip(pins,c['anchor_indices'])];c['anchor_slots']=list(range(32))
  return {'captures':cs}
 framefile=source/'b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
 cap=captures(json.loads(framefile.read_text()));js(stage/'captures.json',cap)
 js(overlay/'inputs/room_captures.json',captures(json.loads((source/'inputs/room_captures.json').read_text())))
 meta=source/'b/work/meta/x';tasks=[str(meta/'sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl'),str(meta/'sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl')]
 js(stage/'export/RESTORE.json',{'fixture':True});js(stage/'binding.json',dict(root=str(stage),name='fixture',sha256='a'*64))
 settings=dict(stage1_select_rule='null_argmax' if mode=='base' else 'candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,types=['room_size_estimation'],tree=str(overlay/'tree'),frames_root=str(frames),frames_json=str(stage/'captures.json'),dense_manifest=str(stage/'captures.json'),tasks=tasks,require_dense64=False,export_dir=str(stage/'export'),artifact_manifest=str(stage/'binding.json'),selector_head=str(stage/'selector'),sam3=dict(checkpoint_path=str(stage/'sam'),receipt_path=str(stage/'sam.json')))
 js(stage/'archive_layout_fixture/settings.json',settings);put(stage/'sj/b01ec87a6f29b/d/6.json',(o/'export_544.json').read_bytes())
 js(o/'LOCAL_CPU_CHECK.json',dict(root=str(stage),full_reader=json.loads((W/'out/b2/LOCAL_NATIVE_CPU_CHECK.json').read_text())['full_reader'],fixture='Rebuilt synthetic frames and capture manifests; full_reader field is retained historical fixture for guard-only test. CPU suite executes real reader on newly generated frames.'))
 p=o/'work/test_cpu_helper.py';s=p.read_text().replace("P=O/'src'","P=O/'fixture_src'");p.write_text(s)
print('Recovered CPU, metadata, and local lookup fixtures')
