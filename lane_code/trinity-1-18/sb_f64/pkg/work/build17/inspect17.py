from pathlib import Path
import json, hashlib, sqlite3
L=Path(__file__).resolve().parents[2]
E=L.parent
for p in [E/'ext/b12/work/auth/K1SPLIT_R0.json',E/'ext/b12/work/auth/arkit_3dod_metadata.csv',E/'ext/b12/work/d3_token_map.json',E/'inputs/rooms/R0_ROOMS.txt',E/'inputs/rooms/EXCLUSIONS.json']:
    b=p.read_bytes(); print(p,len(b),hashlib.sha256(b).hexdigest())
    if p.suffix=='.json':
        x=json.loads(b);print(str(x)[:2400])
print('workspace bytes',sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()))
print('temporary bytes',sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()))
p=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
print(c.execute('SELECT sql FROM sqlite_master WHERE type="table"').fetchall())
for r in c.execute('SELECT * FROM rows LIMIT 1'):print(str(r)[:4000])
c.close()
