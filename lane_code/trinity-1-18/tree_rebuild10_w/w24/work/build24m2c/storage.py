from common import *
def growth():
 baseline=J.load(D/'DISK_BASELINE.json');seen=set();total=0
 cutoff=(D/'DISK_BASELINE.json').stat().st_mtime-10
 for root,dirs,files in os.walk(L):
  dirs[:]=[n for n in dirs if n not in ('.git','.agents','.codex') and not os.path.islink(os.path.join(root,n))]
  # The initial baseline recorded files only. Count every directory changed
  # since this invocation in full, including existing parents, conservatively.
  directory=os.stat(root)
  if directory.st_ctime>=cutoff:total+=directory.st_blocks*512
  for name in files:
   p=Path(root)/name
   if p.is_symlink():continue
   s=p.stat()
   if s.st_ino in seen:continue
   seen.add(s.st_ino);total+=max(0,s.st_blocks*512-baseline.get(str(s.st_ino),[0,0])[1])
 return total
if __name__=='__main__':print(growth())
