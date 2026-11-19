"""Verify final source, archive, kits, writable scope and storage without remote access."""
from pathlib import Path
import hashlib,json,os,sys,subprocess,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import digest
from student_pilot.source_seal import inventory
from launch_r1.build import verify as verify_r1
from launch_r2.build import verify as verify_r2
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
seal=read(L/'out/TREE_SEAL.json');files=inventory(T)
assert files==seal['files'] and digest(files)==seal['tree_sha256']
assert sha(L/'out/TREE_FILES.sha256')==seal['inventory_sha256']
assert sha(L/'out/TREE.diff')==seal['diff_sha256']
delivery=read(B/'DELIVERY.json');assert sha(L/delivery['path'])==delivery['sha256']
assert (L/delivery['path']).stat().st_size==delivery['bytes']<150_000_000
kits=read(B/'KIT_RESULT.json')
for name,kit in kits.items():
    actual=(verify_r1 if name=='r1' else verify_r2)(L/'work/build12/kits'/name)
    assert actual==kit['kit_sha256'] and kit['GO'] is False
old={name:h for h,name in (line.split('  ',1) for line in (L/'work/build12/proofs/n1/review_inputs/TREE_FILES.sha256').read_text().splitlines())}
assert digest(old).startswith('64a2ea92')
changes=[dict(file=n,build9fix_sha256=old.get(n),current_sha256=files.get(n)) for n in sorted(set(old)|set(files)) if old.get(n)!=files.get(n)]
(B/'DIFF_VS_BUILD9FIX.json').write_text(json.dumps(dict(source='work/build12/proofs/n1/review_inputs/TREE_FILES.sha256',build9fix_seal=digest(old),files=changes),indent=2))
sizes={}
for name,root in [('workspace',L),('tmp',L/'work/tmp')]:
    total=0;pending=[root]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for e in entries:
                if e.is_symlink():continue
                if e.is_dir(follow_symlinks=False):pending.append(e.path)
                elif e.is_file(follow_symlinks=False):total+=e.stat(follow_symlinks=False).st_size
    sizes[name]=total
assert sizes['workspace']<8_000_000_000 and sizes['tmp']<=200_000_000
df=subprocess.run(['df','-BG','--output=avail','/scratch'],check=True,capture_output=True,text=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
record=dict(source_seal=seal['tree_sha256'],package=delivery,storage=sizes,scratch=df.stdout,GO=False)
(B/'FINAL_INTEGRITY.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
