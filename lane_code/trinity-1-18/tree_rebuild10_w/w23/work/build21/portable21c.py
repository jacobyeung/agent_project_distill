"""Record test inputs and redirect authenticated bytes in an extracted delivery."""
from pathlib import Path
import builtins,io,json,os,sys
L=Path(__file__).resolve().parents[2]
reads=set();writes=set()
def audit(event,args):
    if event!='open' or not isinstance(args[0],(str,bytes)):return
    p=os.fsdecode(args[0])
    if not p.startswith(('/scratch/jjyeung/orch_n30/tree_rebuild10_w/','/scratch/jjyeung/n30_mirror/')):return
    mode=args[1];flags=args[2]
    writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)
    if writing:writes.add(p)
    elif p not in writes:reads.add(p)

def install():
    manifest=L/'work/build21c/DEPENDENCIES.json'
    if os.environ.get('B21C_PORTABLE')=='1':
        value=json.loads(manifest.read_text());aliases=value['aliases'];old_root=value['workspace']
        origin_file=L/'work/build23/PACKAGE_ORIGIN.json'
        origin=json.loads(origin_file.read_text())['workspace'] if origin_file.is_file() else old_root
        def mapped(path):
            if not isinstance(path,(str,bytes,os.PathLike)):return path
            s=os.fsdecode(path)
            local=str(L)
            if s.startswith(local+'/fixtures/'):
                original=old_root+s[len(local):]
                if original in aliases:return str(L/aliases[original])
            if s.startswith(old_root+'/work/build21/proofs/'):
                return local+s[len(old_root):]
            if origin!=local and (s==origin or s.startswith(origin+'/')):
                return local+s[len(origin):]
            if s in aliases:return str(L/aliases[s])
            if s==old_root or s.startswith(old_root+'/'):return str(L)+s[len(old_root):]
            return path
        original_open=builtins.open;original_io=io.open;original_os=os.open;original_stat=os.stat
        def opened(path,*args,**kwargs):return original_open(mapped(path),*args,**kwargs)
        def io_opened(path,*args,**kwargs):return original_io(mapped(path),*args,**kwargs)
        def os_opened(path,*args,**kwargs):return original_os(mapped(path),*args,**kwargs)
        def stat(path,*args,**kwargs):return original_stat(mapped(path),*args,**kwargs)
        builtins.open=opened;io.open=io_opened;os.open=os_opened;os.stat=stat
    sys.addaudithook(audit)

def save(root):
    (Path(root)/'READ_INPUTS.json').write_text(json.dumps(sorted(reads),indent=2)+'\n')
