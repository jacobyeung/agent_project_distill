from pathlib import Path
import hashlib,json,subprocess,shutil,sys
W=Path(__file__).resolve().parent
FB=W.parents[1]
RO=FB/'ro/orch_n30'
TREE=RO/'tree_rebuild10_w/w24/work/tree_r1'
MAN=RO/'tree_rebuild10_w/w24/out/TREE_FILES.sha256'
SEAL=RO/'tree_rebuild10_w/w24/out/TREE_SEAL.json'
PA=FB/'patchA/out/PATCH_A.patch'
PC=FB/'camform/out/PATCH_CAMFORM.patch'
FT=json.loads((FB/'camform/out/FILES_TOUCHED.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
files={}
for line in MAN.read_text().splitlines():
    h,rel=line.split('  ',1);assert sha((TREE/rel).read_bytes())==h,rel;files[rel]=h
seal=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode())
print('seal',seal,seal==json.loads(SEAL.read_text())['tree_sha256'])
print('PA',sha(PA.read_bytes())); print('PC',sha(PC.read_bytes()), sha(PC.read_bytes())==FT['patch_sha256'])
for d in ('A','C'):
    t=W/('tree_'+d)
    if t.exists(): sys.exit('exists '+str(t))
    for rel in files:
        p=t/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(TREE/rel,p)
    r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(PA)],cwd=t,capture_output=True,text=True);print(d,'PA',r.returncode,r.stdout.strip()[-300:])
    if d=='C':
        r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(PC)],cwd=t,capture_output=True,text=True);print(d,'PC',r.returncode,r.stdout.strip())
def tree(t): return {str(p.relative_to(t)):sha(p.read_bytes()) for p in sorted(t.rglob('*')) if p.is_file()}
A=tree(W/'tree_A');C=tree(W/'tree_C')
print('A files',len(A),'C files',len(C))
pa_seal=sha(json.dumps(A,sort_keys=True,separators=(',',':')).encode());print('A seal',pa_seal,pa_seal==FT['base_plus_patchA_tree_sha256'])
diff={k:(A.get(k),C.get(k)) for k in set(A)|set(C) if A.get(k)!=C.get(k)}
ok=True
for f in FT['files']:
    got=diff.pop(f['path'],None);exp=(f['base_sha256'],f['new_sha256']);print(f['path'],got==exp,got)
    ok&=got==exp
print('extra diffs',diff); print('ALL_MATCH',ok and not diff)
# compare to their work/new
N=tree(FB/'camform/work/new'); print('their work/new == my C', {k for k in set(N)|set(C) if N.get(k)!=C.get(k) and '__pycache__' not in k})
