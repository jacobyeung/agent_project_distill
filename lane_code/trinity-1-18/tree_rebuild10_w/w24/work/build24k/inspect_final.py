from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';sys.path.insert(0,str(L/'work/build24'))
import joblib as J
uploads={v['sha256']:v['local_path'] for v in J.load(D/'UPLOADS_n.json')['files'] if v['opaque_name'].startswith('u/')}
p=J.load(Path(uploads['ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984']))
for key in ('database','materialization'):
 pin=p[key];print(key,pin,'in_upload',pin['sha256'] in uploads)
 if key=='materialization' and pin['sha256'] in uploads:
  mat=J.load(Path(uploads[pin['sha256']]));print('mat keys',list(mat));print('legacy',mat.get('legacy'));print('catalog',len(mat.get('inputs',{}).get('catalog',{})))
seen=set();total=0;big=[]
for p in D.rglob('*'):
 if p.is_symlink() or not p.is_file():continue
 s=p.stat();inode=(s.st_dev,s.st_ino)
 if inode in seen:continue
 seen.add(inode);total+=s.st_size
 if s.st_size>2000000:big.append((s.st_size,str(p.relative_to(D))))
print('D unique bytes',total,'largest',sorted(big,reverse=True)[:15])
