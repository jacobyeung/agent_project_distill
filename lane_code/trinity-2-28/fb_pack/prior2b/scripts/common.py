"""Authenticate local mirrored pins without editing or inventing source data."""
import sys,json,hashlib,base64
from pathlib import Path
W=Path(__file__).resolve().parents[1]
RO=Path('/scratch/jjyeung/orch_n30/fb_pack/ro'); OLD=Path('/scratch/jjyeung/orch_n30/fb_pack/prior2')
T=W/'work/sealed_new';sys.path.insert(0,str(T))
from student_pilot import p3_provenance as P
inputs={};locations={}
def track(path,expected=None):
 path=Path(path).resolve();key=str(path)
 if key in inputs:h=inputs[key]['sha256']
 else:
  h=P.sha256(path);inputs[key]=dict(path=key,sha256=h,bytes=path.stat().st_size)
 if expected and h!=expected:raise ValueError(f'HASH_MISMATCH:{path}:{h}!={expected}')
 return path
for name in ('INPUT_LOCATIONS.json','CAPSULE_RECOVERY.json'):
 value=json.loads(track(OLD/'out'/name).read_text());locations.update(value['found'])
if (W/'out/RECOVERED_METADATA.json').is_file():
 value=json.loads(track(W/'out/RECOVERED_METADATA.json').read_text());locations.update(value['found'])
kitroot=RO/'orch_n30/tree_rebuild10_w/w24/out/kit_n_go'
def mapped(path):
 for prefix,target in [('/scratch/jjyeung/orch_n30/',RO/'orch_n30'),('/scratch/jjyeung/n30_mirror/',RO/'n30_mirror')]:
  if str(path).startswith(prefix):return target/str(path)[len(prefix):]
 return Path(path)
def resolve(pin):
 candidates=[mapped(pin['path']),RO/'orch_n30/tree_rebuild10_w/ext/m400real/files'/str(pin['path']).lstrip('/')]
 if pin['sha256'] in locations:candidates.append(Path(locations[pin['sha256']]))
 candidates.extend([kitroot/'u'/pin['sha256'],OLD/'work/recovered'/pin['sha256']])
 for p in candidates:
  if not str(p).startswith('/scratch/'):continue
  if p.is_file():
   track(p)
   if inputs[str(p.resolve())]['sha256']==pin['sha256']:return p
   # Some kit files are authenticated base64 capsules, whose decoded bytes retain the pin.
   if p.stat().st_size<40_000_000:
    try:
     obj=json.loads(p.read_text());raw=base64.b64decode(obj['payload'],validate=True)
     if hashlib.sha256(raw).hexdigest()==pin['sha256']:
      dest=W/'work/recovered'/pin['sha256'];dest.parent.mkdir(exist_ok=True)
      if not dest.exists():dest.write_bytes(raw)
      return track(dest,pin['sha256'])
    except (ValueError,KeyError,TypeError,UnicodeError):pass
   raise ValueError(f'HASH_MISMATCH:{p}:{inputs[str(p.resolve())]["sha256"]}!={pin["sha256"]}')
 raise FileNotFoundError(f'MISSING:{pin["path"]}; expected_mirror_path={mapped(pin["path"])}; sha256={pin["sha256"]}')
P.pinned=resolve
CFG=RO/'orch_n30/tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json';KIT=kitroot/'k/n.json'
def config():return P.load(track(CFG,'0e78d7f86f85cf6090db94bb4916fbd1c57b9fa2aff04dd0a8428a414a4a5f5f'))
def code_inputs():
 for mod in list(sys.modules.values()):
  path=getattr(mod,'__file__',None)
  if path and Path(path).is_relative_to(T) and Path(path).is_file():track(path)
 track(__file__)
def write(name,value):
 code_inputs();value=dict(value,inputs=list(inputs.values()))
 p=W/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');return p
