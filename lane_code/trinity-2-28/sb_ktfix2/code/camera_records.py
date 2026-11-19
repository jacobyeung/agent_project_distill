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
 """Verify explicit local metadata joins and bytes; real text parity remains a GPU check."""
 p=ROOT/'inputs/CAMERA_FRAME_JOINS.json'
 if not p.exists():return dict(status='MISSING',expected_path=str(p),reason='Run scripts/bind_camera.py to audit local metadata',skipped=450)
 from camera_binding import camera_items
 data=camera_items();joined=read_json(p)
 return dict(status='PASS' if data['items'] else 'MISSING',bound=len(data['items']),bound64=sum(r['has64'] for r in data['items']),skipped=len(data['skipped']),missing=data['skipped'],dense_missing=joined.get('dense_missing',[]),unique_frames_verified=joined['unique_frames_verified'],frame_bytes_verified=joined['frame_bytes_verified'],join_rule=joined['join_rule'],binding_path=str(p),binding_sha256=sha(p))
