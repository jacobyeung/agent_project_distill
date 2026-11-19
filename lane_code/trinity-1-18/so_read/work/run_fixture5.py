"""CPU fixture storage: hardlink immutable reviewed inputs and repeated tar bytes.
Writes to shared fixtures detach through an atomic replacement before editing.
No file is deleted; existing round-1..4 artifacts remain untouched.
"""
import atexit,hashlib,json,os,runpy,sys,uuid
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
manifest=json.loads((L/'out_round5/patches/MANIFEST.json').read_text())
base=Path(manifest['verification_root'])/'src'
registry=L/'work/fixture_pins5.json'
assets=json.loads(registry.read_text()) if registry.exists() else {}
for rel,pin in manifest['base_pin']['inventory'].items():
    p=base/rel
    if p.stat().st_size>=1024:assets[pin]=str(p)
original_write=Path.write_bytes
original_open=Path.open

def detach(path):
    if path.exists() and not path.is_symlink() and path.stat().st_nlink>1:
        tmp=path.with_name(path.name+'.cow'+uuid.uuid4().hex)
        original_write(tmp,path.read_bytes())
        os.replace(tmp,path)

def open_path(path,mode='r',*args,**kwargs):
    if any(v in mode for v in ('w','a','+')):detach(path)
    stream=original_open(path,mode,*args,**kwargs)
    if mode=='xb' and L/'work' in path.absolute().parents:
        return ShareOnClose(path,stream)
    return stream

class ShareOnClose:
    """Share known immutable archive members after the real write has closed."""
    def __init__(self,path,stream):self.path=path;self.stream=stream
    def __getattr__(self,name):return getattr(self.stream,name)
    def __enter__(self):return self
    def __exit__(self,*args):
        self.stream.close()
        if args[0] is not None:return
        path=self.path
        if path.is_symlink() or path.stat().st_nlink>1 or path.stat().st_size<1024:return
        with original_open(path,'rb') as f:raw=f.read()
        pin=hashlib.sha256(raw).hexdigest();name=assets.get(pin)
        if not name:return
        source=Path(name)
        if source==path or not source.is_file():return
        with original_open(source,'rb') as f:other=f.read()
        if raw!=other:return
        tmp=path.with_name(path.name+'.share10'+uuid.uuid4().hex)
        os.link(source,tmp);os.replace(tmp,path)

def write_bytes(path,raw):
    pin=hashlib.sha256(raw).hexdigest()
    if not path.exists() and L in path.resolve().parents and pin in assets:
        source=Path(assets[pin])
        if source!=path and source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==pin:
            os.link(source,path);return len(raw)
    count=original_write(path,raw)
    if len(raw)>131072 and path.suffix=='.tgz':assets[pin]=str(path.resolve())
    return count

Path.open=open_path;Path.write_bytes=write_bytes
atexit.register(lambda:registry.write_text(json.dumps(assets,sort_keys=True)+'\n'))
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
