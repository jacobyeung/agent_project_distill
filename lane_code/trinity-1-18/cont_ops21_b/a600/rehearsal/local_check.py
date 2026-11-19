import builtins,sys,runpy
from pathlib import Path
original=builtins.compile
k=sys.argv[2]
def compile_local(source,filename,mode,*args,**kwargs):
    if isinstance(source,(str,bytes)):
        raw=source.decode() if isinstance(source,bytes) else source
        raw=raw.replace("'/project/community/jjyeung/okh7'",repr(k))
        raw=raw.replace("'/project/community/jjyeung/'",repr(k.rsplit('/',1)[0]+'/'))
        source=raw
    return original(source,filename,mode,*args,**kwargs)
builtins.compile=compile_local
p=sys.argv[1];sys.argv=[p,'check','--gpus','1','--time','03:00:00']
runpy.run_path(p,run_name='__main__')
