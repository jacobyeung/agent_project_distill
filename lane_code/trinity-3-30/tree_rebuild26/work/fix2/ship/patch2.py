# Kit-only change: b/a.py runs the tree's forward through b/fw.py in a fresh interpreter (mode q).
import sys,hashlib,os
from pathlib import Path
K=Path(sys.argv[1]);src=Path(sys.argv[2])
a=K/'b/a.py';s=a.read_text()
old="""    admission_module.admit=restoring_admit
    from launch_r1.production_proof import run
"""
assert s.count(old)==1
new="""    admission_module.admit=restoring_admit
    # A device query made while admit() hides the devices leaves this process unable to open one
    # later, so the forward runs in a fresh interpreter (b/fw.py) with the job's limit and scopes.
    import launch_r1.production_proof as proof_module
    from fw import call
    job_limit=resource.getrlimit(resource.RLIMIT_AS)
    def spawned_forward(*args,**kwargs):
     return call('launch_r1.production_proof','forward',args,kwargs,limit=job_limit)
    proof_module.forward=spawned_forward
    from launch_r1.production_proof import run
"""
a.write_text(s.replace(old,new))
f=K/'b/fw.py';assert not f.exists()
f.write_bytes(src.read_bytes());os.chmod(f,os.stat(K/'b/z.py').st_mode&0o7777)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
L=(K/'SHA256SUMS.txt').read_text().splitlines()
name=lambda l:l.split('  ',1)[1]
assert [name(l) for l in L]==sorted(name(l) for l in L)
L=[(sha(a)+'  b/a.py') if name(l)=='b/a.py' else l for l in L]+[sha(f)+'  b/fw.py']
L.sort(key=name)
(K/'SHA256SUMS.txt').write_text('\n'.join(L)+'\n')
print('a.py',sha(a),'fw.py',sha(f),'seal',sha(K/'SHA256SUMS.txt'))
