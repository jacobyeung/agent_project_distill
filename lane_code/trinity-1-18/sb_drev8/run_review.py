"""Run a review script with read provenance and workspace-only Python writes."""
import hashlib, json, os, runpy, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
script=ROOT/sys.argv[1]
reads={str(script),str(Path(__file__).resolve())}; cache={}; tracking=True
original_write=Path.write_text

def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0]); mode=args[1]; flags=args[2]
        write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)))
        ab=os.path.abspath(p)
        if write and not ab.startswith(str(ROOT)+'/'):
            raise RuntimeError('WRITE OUTSIDE WORKSPACE: '+ab)
        if not write and tracking and ab.startswith('/scratch/') and '/envs/' not in ab:
            reads.add(ab)
    if event=='sqlite3.connect':
        p=str(args[0]).removeprefix('file:').split('?')[0]
        if p.startswith('/'): reads.add(p)
sys.addaudithook(audit)

def provenance():
    global tracking
    tracking=False
    out={}
    try:
        for p in sorted(reads):
            path=Path(p)
            if not path.is_file(): continue
            st=path.stat(); key=(p,st.st_size,st.st_mtime_ns)
            if key not in cache:
                h=hashlib.sha256()
                with open(path,'rb') as f:
                    for b in iter(lambda:f.read(4<<20),b''): h.update(b)
                cache[key]=h.hexdigest()
            out[p]=cache[key]
    finally: tracking=True
    return out

def write(self,data,*args,**kw):
    if self.suffix=='.json':
        value=json.loads(data)
        if isinstance(value,dict):
            value['review_input_sha256']=provenance()
            value['review_command']='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python run_review.py '+script.name
            data=json.dumps(value,indent=1,sort_keys=True)+'\n'
    return original_write(self,data,*args,**kw)
Path.write_text=write
runpy.run_path(str(script),run_name='__main__')
(Path(ROOT/'work'/('PROVENANCE_'+script.stem+'.json'))).write_text(json.dumps({'script':script.name}))
