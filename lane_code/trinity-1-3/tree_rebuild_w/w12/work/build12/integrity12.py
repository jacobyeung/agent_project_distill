"""Recompute final delivery identities without changing source or proof outputs."""
from pathlib import Path
import difflib, hashlib, json, os, shutil, sys, tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
def read(p):return json.loads((L/p).read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()
seal=read('out/TREE_SEAL.json');files=inventory(T)
assert seal['files']==files and seal['tree_sha256']==digest(files)
expected=''.join(h+'  '+name+'\n' for name,h in sorted(files.items()))
assert (L/'out/TREE_FILES.sha256').read_text()==expected
assert sha(L/'out/TREE_FILES.sha256')==seal['inventory_sha256']
base=L/'work/base/tree_b01ce449';prior=inventory(base);parts=[]
for name in sorted(set(files)|set(prior)):
    a=base/name;b=T/name
    try:
        old=a.read_text().splitlines(True) if a.exists() else []
        new=b.read_text().splitlines(True) if b.exists() else []
    except UnicodeDecodeError:
        if not a.exists() or not b.exists() or a.read_bytes()!=b.read_bytes():
            parts.append('Binary files a/'+name+' and b/'+name+' differ\n')
        continue
    if old!=new:parts.extend(difflib.unified_diff(old,new,fromfile='a/'+name,tofile='b/'+name))
assert (L/'out/TREE.diff').read_text()==''.join(parts)
assert sha(L/'out/TREE.diff')==seal['diff_sha256']
delivery=read('work/n1fix2/DELIVERY.json');archive=L/delivery['path']
assert sha(archive)==delivery['sha256'] and archive.stat().st_size==delivery['bytes']<150_000_000
frozen=read('work/build12/proofs/n1/package/ARCHIVE.json')
assert frozen['sha256']==delivery['sha256'] and frozen['source_sha256']==seal['tree_sha256']
with tarfile.open(archive) as f:
    package_source={m.name[len('work/tree_r1/'):]:hashlib.sha256(f.extractfile(m).read()).hexdigest()
                    for m in f.getmembers() if m.isfile() and m.name.startswith('work/tree_r1/')}
assert package_source==files
from launch_r1.build import verify as verify_r1
from launch_r2.build import verify as verify_r2
kits=read('work/n1fix2/KIT_RESULT.json');verified={}
for name,item in kits.items():
    assert item['GO'] is False
    assert item.get('source_sha256',item.get('source_seal'))==seal['tree_sha256']
    value=(verify_r1 if name=='r1' else verify_r2)(B/'kits'/name)
    assert value==item['kit_sha256'];verified[name]=value
patch=[];clean=B/'harness_base';live=L/'work/build10/eat1'
baseline=read('work/build12/HARNESS_BASE.json')
assert all(sha(clean/r['file'])==r['sha256'] for r in baseline['files'])
for p in sorted(live.rglob('*')):
    if not p.is_file() or p.suffix!='.py':continue
    rel=p.relative_to(live);q=clean/rel
    old=q.read_text().splitlines(True) if q.exists() else [];new=p.read_text().splitlines(True)
    if old!=new:patch.extend(difflib.unified_diff(old,new,fromfile='a/eat1/'+str(rel),tofile='b/eat1/'+str(rel)))
assert (L/'out/EAT1_FIXED_MATH.patch').read_text()==''.join(patch)
coverage=read('work/build12/CHANGED_COVERAGE.json');gaps=read('work/build12/GAPS.json')
assert not gaps
for row in coverage['statements']:assert row['sha256']==files[row['file']]
comparison=read('work/n1fix2/SUITE_COMPARISON.json')
regressions=[r for r in comparison['failures'] if not r['preexisting']]
assert not comparison['r2_failures'] and not comparison['fatal']
assert all('BF16 cached/online gradient' in r['cause'] for r in regressions)
suite=read('work/build12/proofs/n1/suite_tree/results.json');assert suite['complete']
source_hashes=read('work/build12/proofs/n1/suite_tree/source_hashes.json')
assert all(files[name]==value for name,value in source_hashes.items())
storage=0;tmp=0;file_count=0
for directory,dirs,names in os.walk(L,followlinks=False):
    dirs[:]=[n for n in dirs if not (Path(directory)/n).is_symlink()]
    for name in names:
        p=Path(directory)/name
        if p.is_symlink():continue
        amount=p.stat().st_size;storage+=amount;file_count+=1
        if p.is_relative_to(L/'work/tmp'):tmp+=amount
assert storage<8_000_000_000 and tmp<=200_000_000
result=dict(status='verified',source_seal=seal['tree_sha256'],source_files=len(files),
    source_inventory_sha256=seal['inventory_sha256'],base_diff_sha256=seal['diff_sha256'],
    archive=delivery,package_source_matches=True,frozen_archive_matches=True,kits=verified,
    harness_patch_sha256=sha(L/'out/EAT1_FIXED_MATH.patch'),harness_patch_exact_diff=True,
    cpu_gaps=0,coverage_classes=coverage['classes'],r2_failures=0,
    allowed_BF16_regressions=len(regressions),other_regressions=0,
    local_storage_bytes=storage,local_file_count=file_count,tmp_bytes=tmp,
    scratch_free_bytes=shutil.disk_usage('/scratch').free,
    storage_scope='L only; read-only sibling workspace occupancy was not surveyed',
    production_authorized=False)
(B/'FINAL_INTEGRITY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
