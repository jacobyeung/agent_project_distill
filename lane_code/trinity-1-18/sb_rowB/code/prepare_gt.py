import hashlib,io,json,tarfile
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from inventory import ROOT,sha

def main():
 loc=json.loads((ROOT/'inputs/GT_LOCATIONS.json').read_text()); rows=[json.loads(l) for l in (ROOT/'inputs/sources.jsonl').open()]
 wanted=defaultdict(set)
 for r in rows:wanted[Path(r['provenance']['raster']).name].add(r['provenance']['raster_sha256'])
 by=defaultdict(list)
 for x in loc['candidates']:by[x['archive']].append(x)
 pins={str(ROOT/'inputs/GT_LOCATIONS.json'):sha(ROOT/'inputs/GT_LOCATIONS.json'),str(ROOT/'inputs/sources.jsonl'):sha(ROOT/'inputs/sources.jsonl')}
 compact=[];issues=[];c=Counter()
 for path,candidates in by.items():
  pins[path]=sha(path)
  print('archive hashed',path,flush=True)
  with tarfile.open(path) as t:
   for x in candidates:
    raw=t.extractfile(x['member']).read();h=hashlib.sha256(raw).hexdigest();name=Path(x['member']).name
    if h not in wanted[name]:
     c['sha_mismatch']+=1;issues.append(dict(**x,sha256=h,expected_sha256=sorted(wanted[name]),status='MISSING: exact source raster'));continue
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
     keys=['c2w','frame_indices','ids','labels','obb_centroid','obb_axes','obb_lengths']
     missing=[k for k in keys if k not in z.files]
     if missing:issues.append(dict(**x,sha256=h,status='MISSING: '+','.join(missing)));c['missing_arrays']+=1;continue
     v={k:z[k].tolist() for k in keys}
     if 'valid' in z.files:v['valid']=z['valid'].tolist()
     compact.append(dict(input_sha256={path:pins[path],path+'::'+x['member']:h},raster_sha256=h,member=x['member'],archive=path,arrays=v))
     c['matched']+=1
 print(dict(c),flush=True)
 (ROOT/'inputs/GT_COMPACT.jsonl').write_text(''.join(json.dumps(v,allow_nan=False)+'\n' for v in compact))
 (ROOT/'out/GT_MATCH.json').write_text(json.dumps(dict(input_sha256=pins,counts=dict(c),issues=issues,matched_members=len(compact)),indent=2)+'\n')
 (ROOT/'STATUS.md').write_text('Stage 2: Census covers 7,932 rows; 7,898 cite an object outside the queried frame. GT_MATCH.json records source-SHA verification for archive candidates, and GT_COMPACT.jsonl preserves the original pose, frame indices, IDs, labels and box arrays for matched sources. Numeric trace reconstruction and native grammar checks follow; missing GT is refused explicitly.\n')
if __name__=='__main__':main()
