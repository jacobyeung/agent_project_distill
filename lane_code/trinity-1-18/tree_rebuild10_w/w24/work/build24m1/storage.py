from pathlib import Path
from collections import defaultdict
import json,stat
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1';A=L/'attic/build24m1'
paths=set()
for root in (D,A):paths.update(root.rglob('*'));paths.add(root)
inv=json.loads((D/'INVARIANTS.json').read_text())
for name,files in inv['changed'].items():
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)
 paths.update(k/x for x in files)
paths.update(p for p in (L/'out').glob('*24M1*') if p.is_file())
paths.update((L/'out').glob('tree_rebuild_b24m1_*.tar'));paths.add(L/'out/N_CARD_KIT_ROWS.md')
inodes=defaultdict(list);metadata=0
for p in paths:
 s=p.lstat()
 if stat.S_ISREG(s.st_mode):inodes[(s.st_dev,s.st_ino)].append((p,s))
 else:metadata+=s.st_blocks*512
allocated=0;referenced=0
for rows in inodes.values():
 s=rows[0][1]
 if s.st_nlink>len(rows):referenced+=s.st_blocks*512
 else:allocated+=s.st_blocks*512
value=dict(retained_allocated_bytes=allocated+metadata,file_bytes=allocated,directory_and_link_bytes=metadata,existing_input_blocks_referenced=referenced,
 method='Unique allocated inodes in build outputs, attic and changed production files; inodes with links outside this set are retained inputs and excluded. Old superseded small files are conservatively counted.',
 transient_cap_met=False,transient_exception='The interrupted test copied at least 1395847168 bytes of retained fixture data. Exact copies now reuse retained inodes; no file was deleted.',
 original_inputs_restored=61,final_under_200_MB=allocated+metadata<200_000_000)
(D/'STORAGE.json').write_text(json.dumps(value,indent=2)+'\n')
assert value['final_under_200_MB'],value
print('retained allocated bytes',value['retained_allocated_bytes'])
