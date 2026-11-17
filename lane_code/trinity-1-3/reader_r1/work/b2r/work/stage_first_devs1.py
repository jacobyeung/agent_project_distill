"""Extract only the first dev-S1 item's 64 authenticated PNGs from a supplied local tar."""
import argparse,hashlib,json,tarfile
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W/'out/src'
p=argparse.ArgumentParser();p.add_argument('--tar',required=True);a=p.parse_args()
m=json.loads((P/'items/room134.json').read_text());item=next(r for r in m['items'] if r['id'] in m['sets']['dev-S1'])
path=P/'b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
c=json.loads(path.read_text())['captures'];c={v['native']:v for v in c} if isinstance(c,list) else c
wanted={f['sha256']:f for f in c[item['native']]['frames']};seen=set()
with tarfile.open(a.tar,'r:*') as archive:
 for member in archive:
  if not member.isfile():continue
  candidates=[f for f in wanted.values() if Path(member.name).name==Path(f['path']).name]
  if not candidates:continue
  raw=archive.extractfile(member).read();digest=hashlib.sha256(raw).hexdigest()
  if digest not in wanted:raise ValueError('Pinned PNG differs: '+member.name)
  relative=Path(wanted[digest]['path']).relative_to('/scratch/jjyeung/devs1_frames')
  dest=W/'work/frames'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists() and dest.read_bytes()!=raw:raise ValueError('Existing PNG differs')
  dest.write_bytes(raw);seen.add(digest)
  if seen==set(wanted):break
if seen!=set(wanted):raise ValueError('Missing pinned PNGs: '+str(sorted(set(wanted)-seen)))
(W/'out/DEVS1_FRAME_CHECK.json').write_text(json.dumps(dict(passed=True,item=item['id'],frames=len(seen),source=str(Path(a.tar).resolve())),indent=2)+'\n')
print('Verified',len(seen),'frames for',item['id'])
