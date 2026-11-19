import csv, hashlib, json, os
from pathlib import Path
X=Path('extract').resolve(); K='/scratch/jjyeung/orch_n30/sb_ktfix2'
rows=list(csv.DictReader(open(X/'out/STAGE_LIST.tsv'),delimiter='\t'))
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def parts(r): return set(r['parts'].split(',')) if r['parts'] else set()
tot={p:sum(int(r['bytes']) for r in rows if r['bytes'] and p in parts(r)) for p in 'ABCH'}
tot['union']=sum(int(r['bytes']) for r in rows if r['bytes'])
inc=dict(A=tot['A'],
 B_after_A=sum(int(r['bytes']) for r in rows if r['bytes'] and 'B' in parts(r) and 'A' not in parts(r)),
 C_after_AB=sum(int(r['bytes']) for r in rows if r['bytes'] and 'C' in parts(r) and not parts(r)&{'A','B'}),
 H_after_ABC=sum(int(r['bytes']) for r in rows if r['bytes'] and 'H' in parts(r) and not parts(r)&{'A','B','C'}),
 C_alone=tot['C'])
missing=[];size_bad=[];kit_bad=[];dir_missing=[];man_bad=[]
for r in rows:
    p=r['path']
    if r['kind']=='create': continue
    local=X/p[len(K)+1:] if p.startswith(K+'/') else Path(p)
    if r['kind']=='dir':
        m=X/'out/manifests'/(p.strip('/').replace('/','__')+'.sha256')
        if not m.exists() or sha(m)!=r['sha256']: man_bad.append(p); continue
        for line in m.read_text().splitlines():
            h,rel=line.split('  ',1); q=local/rel
            if not q.exists(): dir_missing.append(str(q))
            elif p.startswith(K+'/') and sha(q)!=h: kit_bad.append(str(q))
    else:
        if not local.exists(): missing.append(p)
        elif r['bytes'] and local.stat().st_size!=int(r['bytes']): size_bad.append(p)
        elif p.startswith(K+'/') and r['sha256'] and sha(local)!=r['sha256']: kit_bad.append(p)
# kit files in the extracted tree that GPU parts import but no row covers
kitdirs=[r['path'] for r in rows if r['path'].startswith(K+'/')]
uncovered=sorted(str(q.relative_to(X)) for q in (X/'code').rglob('*') if q.is_file() and not any(str(K/Path(str(q.relative_to(X))))==d or str(K/Path(str(q.relative_to(X)))).startswith(d+'/') for d in kitdirs))
res=dict(rows=len(rows),totals=tot,sequential_increments=inc,missing_files=missing[:20],n_missing=len(missing),size_mismatch=size_bad[:20],
 manifest_mismatch=man_bad,dir_members_missing=dir_missing[:20],n_dir_members_missing=len(dir_missing),kit_hash_mismatch=kit_bad[:20],code_files_uncovered=uncovered[:20])
json.dump(res,open('stage_check.json','w'),indent=1); print(json.dumps(res,indent=1))
