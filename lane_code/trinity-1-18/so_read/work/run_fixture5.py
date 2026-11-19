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
    return original_open(path,mode,*args,**kwargs)

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
