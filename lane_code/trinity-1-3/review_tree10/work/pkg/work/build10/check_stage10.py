from pathlib import Path
import difflib,hashlib,json
B=Path(__file__).resolve().parent
record=json.loads((B/'B04_STAGING.json').read_text());changes=[]
for row in record['code']:
    source=Path(row['source']);target=Path(row['target'])
    original=source.read_bytes();current=target.read_bytes()
    assert hashlib.sha256(original).hexdigest()==row['sha256']
    if original!=current:
        before=original.decode().splitlines();after=current.decode().splitlines()
        assert len(before)==len(after)
        changes += [dict(file=str(target.relative_to(B.parents[1])),line=i,before=a,after=b)
                    for i,(a,b) in enumerate(zip(before,after),1) if a!=b]
assert changes==record['changed_lines']
assert all(c['before'].startswith(('DATA = ','TREE = ','K1 = ')) for c in changes)
(B/'B04_SOURCE_AUDIT.json').write_text(json.dumps(dict(status='PASS',changes=changes,
    unchanged_files=len(record['code'])-len({c['file'] for c in changes})),indent=2)+'\n')
print('Staged b04 code differs only at its recorded path constants.')
