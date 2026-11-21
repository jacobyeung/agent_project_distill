# Kit-only fix: b/a.py restores the soft address-space limit after the tree's admit() returns (mode q).
import sys,hashlib,json,base64
from pathlib import Path
K=Path(sys.argv[1])
a=K/'b/a.py'; s=a.read_text()
old="""   if mode=='q':
    from launch_r1.production_proof import run
"""
assert s.count(old)==1
new="""   if mode=='q':
    # admit() lowers the soft RLIMIT_AS for its CPU-only work and never restores it; the same
    # process later opens the device for the forward, so restore the earlier limit on return.
    import resource
    import student_pilot.s1_admission as admission_module
    native_admit=admission_module.admit
    def restoring_admit(*args,**kwargs):
     limit=resource.getrlimit(resource.RLIMIT_AS)
     try:return native_admit(*args,**kwargs)
     finally:resource.setrlimit(resource.RLIMIT_AS,limit)
    admission_module.admit=restoring_admit
    from launch_r1.production_proof import run
"""
s=s.replace(old,new); a.write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
L=(K/'SHA256SUMS.txt').read_text().splitlines()
L=[(sha(a)+'  b/a.py') if l.endswith('  b/a.py') else l for l in L]
(K/'SHA256SUMS.txt').write_text('\n'.join(L)+'\n')
seal=sha(K/'SHA256SUMS.txt')
b=json.loads((K/'BUILD.json').read_text()); d=json.loads(base64.b64decode(b['payload']))
old_seal=d.get('kit_sha256'); d['kit_sha256']=seal
raw=json.dumps(d,indent=2).encode()
b['payload']=base64.b64encode(raw).decode()
if 'sha256' in b:b['sha256']=hashlib.sha256(raw).hexdigest()
(K/'BUILD.json').write_text(json.dumps(b))
print('a.py',sha(a),'seal',old_seal,'->',seal,'BUILD keys',sorted(d))
