from common import *
import copy,tarfile,importlib.util
from unittest.mock import patch
sys.path.insert(0,str(kit('qd')/'b'));import pl,px,i,z
F=D/'plan_k';F.mkdir();(F/'remote/u').mkdir(parents=True)
spec=J.load(kit('qd')/'k/p.json');current=J.load(kit('qd')/'k/l.json')
old=J.load(L/'work/build24m4j/resolver/resolved_n.json')
resolved=copy.deepcopy(old)
def local(p):return str(p).replace(str(W/'w24j'),str(L))
for field in ('archive','receipt'):resolved[field]['path']=local(resolved[field]['path'])
for p in resolved['parts']:p['path']=local(p['path'])
for p in resolved['external_metadata']:p['path']=local(p['path'])
resolved['kit_sha256']=J.seal(kit('qd'))
resolved['config']=J.load(D/'candidate/qd/n.json')
resolved['config']['r1_training'].update({k:v for k,v in old['config']['r1_training'].items() if k in ('p_run','handover_receipt','persisted_files','donor_config_sha256')})
resolved['config']['streams']['routing']=old['config']['streams']['routing']
origins={}
def add(h,origin):
 if origin not in origins.setdefault(h,[]):origins[h].append(origin)
for v in spec['uploads']:add(v['sha256'],'uploads')
for h in spec['p_files'].values():add(h,'p_files')
for h in px.inventory(kit('qd')):add(h,'staging_inventory')
for h in old['small_files']:add(h,'resolved_small_members')
for v in old['external_metadata']:add(v['sha256'],'resolved_external_metadata')
for h in J.load(L/'work/build24m4j/RCJ_PLAN_AUDIT.json')['required_hashes']:add(h,'rebuild_inventory')
# Read only the named archived handover metadata, not any unavailable row payload.
manifest_path=W/'ext/m400real/MANIFEST.json'
if manifest_path.is_file():
 for item in J.load(manifest_path)['files']:add(item['sha256'],'handover_manifest')
missing={};requested={};actual={}
def source(h):
 try:p=input_file(h);actual[h]=str(p);return p
 except ValueError:
  assert h in origins,'UNMAPPED:'+h
  p=F/'standins'/h;p.parent.mkdir(exist_ok=True)
  if not p.exists():p.write_bytes(b'\x00offline payload boundary\n')
  missing[str(p)]=h;return p
for item in spec['uploads']:
 p=source(item['sha256']);out=F/'remote/u'/item['sha256'];os.link(p,out)
 if str(p) in missing:missing[str(out)]=item['sha256']
for p in resolved['external_metadata']:missing[p['path']]=p['sha256']
new_spec=dict(spec,n_root=str(F/'remote'))
load=pl.load;checked=pl.checked;sha=pl.sha
def read(p):return new_spec if Path(p)==kit('qd')/'k/p.json' else load(p)
def check(p,h,size=None):
 if str(p) in missing:
  assert missing[str(p)]==h;return Path(p)
 return checked(p,h,size)
def need(k,root,sources):
 def get(h,field):
  requested.setdefault(h,[]).append(field)
  p=source(h);sources[h]=str(p);return str(p)
 return get
def digest_file(p):return missing.get(str(p)) or sha(p)
root=F/'native';root.mkdir()
isdir=Path.is_dir;rglob=Path.rglob;frame_roots=set(resolved['request']['frame_roots'])
with patch.object(pl,'load',side_effect=read),patch.object(pl,'checked',side_effect=check),patch.object(pl,'sha',side_effect=digest_file),patch.object(px,'resolver',side_effect=need),patch.object(i,'refresh',side_effect=lambda req,root:req),patch.object(Path,'is_dir',lambda p:True if str(p) in frame_roots else isdir(p)),patch.object(Path,'rglob',lambda p,pattern:iter(()) if str(p) in frame_roots else rglob(p,pattern)):
 request,paths,hook=pl.plan_payload(kit('qd'),resolved,root,regeneration=True);hook.close()
plan=J.load(root/'plan.json')
pins={h:origins.get(h,[]) for h in requested}
assert all(pins.values())
all_pins={name[2:]:origins.get(name[2:],['planner_generated']) for name in plan['entries'] if name.startswith('u/')}
assert '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84' not in requested
frame_hashes={v['sha256'] for key,v in current.items() if key.startswith('f') and key[1:].isdigit() and isinstance(v,dict) and 'sha256' in v}
assert not frame_hashes&set(all_pins)
assert plan['config']['min_pixels']==16384 and plan['config']['max_pixels']==147456
J.write(D/'MODE_R_PLAN_TEST.json',dict(status='PASS',planner=str(kit('qd')/'b/pl.py'),requested=pins,all_pins=all_pins,fields=requested,entries=plan['entries'],parts=resolved['parts'],missing_payload_boundaries=missing,real_metadata=actual,frame_payloads_requested=False,export_weights_required=True,frame_roots='Empty directory mountpoints; no payload files',generated_database_requested=False,unmapped=[],scope='Actual pl.plan_payload on real N candidate and authenticated available metadata; unavailable row/processor payload checks and refresh stubbed; native payload staging not executed'))
print('MODE_R_PLAN PASS',len(requested),'requested pins mapped;',len(missing),'explicit unavailable payload boundaries')
