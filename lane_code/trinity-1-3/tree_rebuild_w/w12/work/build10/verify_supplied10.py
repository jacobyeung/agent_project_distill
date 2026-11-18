"""Hash supplied input files in place; retain only bounded evidence."""
from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10'
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()
rows=[]
for p,want in [(N/'work/design/eat1_v7/b03_e2etest_eat1_v7.tar','9ac4c96cccd5b8701ac26b9631ac6815eaae4aa7e9b1f26b290360996ba3fd11'),
               (N/'w9f/out/tree_rebuild_b9f_64a2ea92.tar','a1cb13de7445ffc8e198548f8f1b49d31975b66d785c14f7b3f5ffdbe14351be')]:
    got=digest(p);rows.append(dict(path=str(p),expected=want,actual=got,match=want==got))
root=N/'work/design/b04_inputs';listed=[]
for line in (root/'SHA256SUMS.txt').read_text().splitlines():
    want,name=line.split(maxsplit=1);p=root/name
    got=digest(p)
    listed.append(dict(path=str(p),expected=want,actual=got,match=want==got,
        input_file=name not in ('./SHA256SUMS.txt','./fetch.err')))
result=dict(archives=rows,b04_files=listed,
    note='The supplied list contains its own empty-file digest; that self-entry is reported as a mismatch and is not a model input.')
(B/'SUPPLIED_HASHES.json').write_text(json.dumps(result,indent=2)+'\n')
assert all(r['match'] for r in rows)
assert all(r['match'] for r in listed if r['input_file'])
print(json.dumps(dict(archives=len(rows),b04_inputs=sum(r['input_file'] for r in listed),mismatches=[r['path'] for r in listed if not r['match']])))
