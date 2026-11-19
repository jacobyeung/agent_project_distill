"""Load staged calls without confusing the own pose head with the tower pose."""
import gzip,re
from common import *

PATH=ROOT/'inputs/ROUTED_FULL_544_devS1_camera.jsonl.gz'

def records():
 assert sha(PATH)=='8855c81ead7d82226fe194af5fc508de993efb2095b3521eced58366b198ce3a'
 rows=[json.loads(s) for s in gzip.decompress(PATH.read_bytes()).decode().splitlines()]
 assert len(rows)==450 and len({r['id'] for r in rows})==450
 out=[]
 for r in rows:
  assert r['step']==544 and len(r['source_frame_indices'])==32
  calls=[c for c in r['output']['calls']['records'] if c.get('name') in ('move','turn')]
  assert len(calls)==1,(r['id'],len(calls));c=calls[0]
  match=re.fullmatch(r'<(move|turn) from=(\d+) to=(\d+)>',c['call']);assert match
  i,j=int(match[2]),int(match[3]);assert 1<=i<=32 and 1<=j<=32 and (i,j)==(c['i'],c['j'])
  out.append(dict(id=r['id'],scene=r['scene'],room=r['room_key'],type=r['type'],truth=r['answer'],question=r['question'],source_frame_indices=r['source_frame_indices'],call=c['call'],stored_response=c['response'],scale=float(r['output']['scale']),gravity=r['output']['heads']['gravity'],frame_gap=abs(i-j)))
 return out

def frame_binding():
 """The named request supplies a root and bundle hash, but no per-item hashes."""
 p=Path('/scratch/jjyeung/devs1_r2/REQUEST.json')
 if not p.exists():return missing(p)
 req=read_json(p)
 # Refuse to infer a join from scene spelling, digest or source frame index.
 if 'items' not in req:
  return dict(status='MISSING',expected_path=str(p),missing_field='items[].frames[].{index,path,sha256}',reason='Request has bundle_sha256 and frame_root but no item-to-frame hash binding',skipped=450)
 from camera_binding import camera_items
 data=camera_items()
 return dict(status='PASS' if data['items'] else 'MISSING',bound=len(data['items']),skipped=len(data['skipped']))
