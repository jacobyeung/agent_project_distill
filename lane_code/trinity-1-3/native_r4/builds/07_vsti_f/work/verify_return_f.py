"""Recheck the measured fixture with final source and real digit-token admission."""
from pathlib import Path
from unittest.mock import patch
import sys,tarfile
B=Path(__file__).resolve().parents[1];sys.path.append(str(B/'code'))
from adapter import *
import o,engine
v=load(B/'out/RETURN_SIZE.json');root=Path(v['root']);run=root/'run'
module=o.imports()[2];config=dict(token='5d648e9274d54fba92aef108',binding='f'*64)
source=o.build_return(root,run,root/'return_verified_frames',config,0,None)
# Simulate the excluded production frame-store inventory without copying its pixels.
frame_root=B.parent/'03_vsti_c/work/input_full/store'
inv=load(source/'INVENTORY.json');frames=[]
for p in sorted(frame_root.rglob('*.png')):
 assert len(p.stem)==64 and all(c in '0123456789abcdef' for c in p.stem)
 frames.append(dict(path='i/store/'+str(p.relative_to(frame_root)),bytes=p.stat().st_size,suffix='.png',excluded=True,sha256=p.stem))
inv['files']=sorted(inv['files']+frames,key=lambda r:r['path']);inv['excluded']=sorted(r['path'] for r in inv['files'] if r['excluded'])
dump(source/'INVENTORY.json',inv)
v['simulated_frame_inventory']=dict(files=len(frames),bytes=sum(r['bytes'] for r in frames),
 source=str(frame_root),hashes='Content-addressed filenames from V1c; pixels not rehashed or copied in this CPU rehearsal',
 note='Conservative full V1c 9952-file store, larger than the supplied 4864-file Orchard staging count; entries synthesized in returned inventory only.')
with patch.object(module,'pool_operation',return_value=dict(verified=True)),patch.object(module,'upload',return_value=dict(verified=True)):
 result=o.publish_read(module,source,config['token'],config['binding'],0)
archive=Path(result['local_return'])/'result.tar.gz'
with tarfile.open(archive) as stream:
 members=[m for m in stream.getmembers() if m.isfile()]
 expanded=sum(m.size for m in members)
v.update(full_return_expanded_bytes=expanded,full_return_archive_bytes=archive.stat().st_size,full_return_members=len(members),
         expanded_headroom_bytes=v['expanded_cap_bytes']-expanded,
         archive_headroom_bytes=v['archive_cap_bytes']-archive.stat().st_size,
         archive=pin(archive),inventory=pin(source/'INVENTORY.json'),source_pins=engine.source_pins(),
         token_admission='actual final publisher, digit-leading token; only remote channel functions mocked',
         measurement='Actual archive regular-member sizes and archive stat, excluding sidecar publication receipts')
assert result['returned'] and result['token']==config['token']
assert expanded<v['expanded_cap_bytes'] and archive.stat().st_size<v['archive_cap_bytes']
dump(B/'out/RETURN_SIZE.json',v)
print({k:v[k] for k in ('full_return_expanded_bytes','full_return_archive_bytes','full_return_members')})
