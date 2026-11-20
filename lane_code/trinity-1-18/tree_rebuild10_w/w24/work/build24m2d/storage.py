from common import *
import gzip

def growth():
 rows=json.loads(gzip.decompress((L/'attic/build24m2d/retained/DISK_BASELINE.json.gz').read_bytes()))
 known={(v[0],v[1]):v[2] for v in rows.values()};seen=set();total=0
 for root,dirs,files in os.walk(L):
  dirs[:]=[n for n in dirs if not Path(root,n).is_symlink()]
  for name in dirs+files:
   p=Path(root,name);s=p.lstat();key=(s.st_dev,s.st_ino)
   if key in seen:continue
   seen.add(key);total+=max(0,s.st_blocks-known.get(key,0))*512
 return total
if __name__=='__main__':print(growth())
