import gzip,io,json,tarfile,sys
from pathlib import Path
O=Path('/scratch/jjyeung/orch_n30/b07_offread')
rev={v:k for k,v in json.loads((O/'builds/R/out/NAME_MAP.json').read_text()).items()}
logical=lambda n:'/'.join(rev.get(p,p) for p in n.split('/'))
res={}
for key,acc in (('vsi',O/'builds/R/work/accepted_vsi'),('revsi',O/'in/kit_revsi')):
    with tarfile.open(O/f'builds/R/out/package_{key}.tar') as tf:
        files={logical(m.name):tf.extractfile(m).read() for m in tf if m.isfile()}
    pre='kit/'+key+'/'
    ship={n[len(pre):]:v for n,v in files.items() if n.startswith(pre)}
    accd={str(p.relative_to(acc)):p.read_bytes() for p in acc.rglob('*') if p.is_file()}
    trees=('reader/','parity/','inputs/','cohort/')
    diff=[];missing=[];extra=[]
    for n,v in accd.items():
        if not n.startswith(trees):continue
        if n not in ship:missing.append(n);continue
        if ship[n]!=v:
            if n=='cohort/MEDIA_MANIFEST.json':
                s=lambda b:[{k:x for k,x in r.items() if k not in ('bytes','status')} for r in json.loads(b)]
                if s(ship[n])==s(v):continue
            diff.append(n)
    extra=[n for n in ship if n.startswith(trees) and n not in accd]
    res[key]=dict(accepted_files=sum(n.startswith(trees) for n in accd),diff=diff,missing=missing,extra=extra)
print(json.dumps(res,indent=1))
