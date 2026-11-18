from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10'
old=json.loads((N/'w9f/out/TREE_SEAL.json').read_text());new=json.loads((L/'out/TREE_SEAL.json').read_text())
def hashes(value):
    for k in ('files','inventory'):
        if k in value:return value[k]
    raise ValueError(list(value))
a,b=hashes(old),hashes(new)
changed=[dict(file=f,before=a.get(f),after=b.get(f)) for f in sorted(set(a)|set(b)) if a.get(f)!=b.get(f)]
value=dict(before_source=str(N/'w9f/out/TREE_SEAL.json'),after_source='out/TREE_SEAL.json',changes=changed,
    identical_files=sum(a.get(f)==v for f,v in b.items()),absent_prior_files=sorted(set(a)-set(b)))
assert not value['absent_prior_files']
(B/'SOURCE_PRESERVATION.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'identical_files':value['identical_files'],'changed_files':[r['file'] for r in changed]}))
