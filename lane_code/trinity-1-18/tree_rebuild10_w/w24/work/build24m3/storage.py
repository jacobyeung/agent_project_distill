from common import *
import gzip
def growth():
 known=json.loads(gzip.decompress((D/'DISK_BASELINE.json.gz').read_bytes()));seen=set();total=0
 for root,dirs,files in os.walk(L):
  dirs[:]=[n for n in dirs if not Path(root,n).is_symlink()]
  for name in dirs+files:
   s=Path(root,name).lstat();key=str(s.st_dev)+':'+str(s.st_ino)
   if key in seen:continue
   seen.add(key);total+=max(0,s.st_blocks-known.get(key,0))*512
 return total
if __name__=='__main__':print(growth())
