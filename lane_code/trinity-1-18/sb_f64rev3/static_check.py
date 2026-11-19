import difflib, hashlib, json, tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'sb_f64fix'
NEW = ROOT.parent / 'sb_f64fix2'
inputs = {}
def sha(p):
    p = Path(p)
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    inputs[str(p)] = h
    return h
def files(root):
    return {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
changes, diffs = {}, []
for area in ('kit', 'work/scripts'):
    a, b = files(OLD / area), files(NEW / area)
    changes[area] = []
    for name in sorted(a.keys() | b.keys()):
        ah, bh = sha(a[name]) if name in a else None, sha(b[name]) if name in b else None
        if ah != bh:
            changes[area].append(dict(path=name, old=ah, new=bh))
            diffs.extend(difflib.unified_diff(a[name].read_text().splitlines(True) if name in a else [],
                         b[name].read_text().splitlines(True) if name in b else [],
                         fromfile=str(OLD / area / name), tofile=str(NEW / area / name)))
for name in ('work/regress/regression_check.py', 'work/regress/run_regress.sh'):
    a,b=OLD/name,NEW/name
    ah,bh=sha(a),sha(b)
    changes[name] = dict(old=ah,new=bh,changed=ah!=bh)
    if ah!=bh:
        diffs.extend(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile=str(a),tofile=str(b)))
(ROOT/'out/tree.diff').write_text(''.join(diffs))
archive=NEW/'out/sb_f64fix2.tar'
archive_sha=sha(archive)
assert archive_sha=='472d7775378a82ee365f11aa531f25b065129e339be1a3157abe1b85d24c6f89'
archive_checks={}
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        if member.isfile():
            name=member.name.removeprefix('./')
            p=NEW/name
            archive_checks[name]=p.is_file() and hashlib.sha256(tar.extractfile(member).read()).hexdigest()==sha(p)
assert all(v for k,v in archive_checks.items() if k.startswith('kit/'))
checksums={}
for line in (NEW/'kit/SHA256SUMS').read_text().splitlines():
    h,name=line.split(maxsplit=1)
    name=name.lstrip('*')
    p=NEW/'kit'/name
    if not p.is_file(): p=NEW/name
    checksums[name]=sha(p)==h
assert all(checksums.values())
static=ROOT.parent/'sb_f64rev2/out/static_review.json'
sha(static)
missing=json.loads(static.read_text())['missing_inputs']
for entry in missing.values():
    if 'path' in entry:
        entry['exists_now']=Path(entry['path']).exists()
    if 'location' in entry:
        entry['location']=entry['location'].replace('/sb_f64fix/','/sb_f64fix2/')
        file,key=entry['location'].split(':',1)
        value=json.loads(Path(file).read_text());sha(file)
        for part in key.split('.'): value=value.get(part) if isinstance(value,dict) else None
        entry['value_now']=value
for p in (Path(__file__),ROOT/'run_cpu.sh',NEW/'out/FIX2_REPORT.md',ROOT.parent/'sb_f64rev2/out/REVIEW_VERDICT.md',
          ROOT.parent/'sb_f64/pkg/work/tree_f64/student_pilot/carrier_c1_run.py'):
    sha(p)
result=dict(command='bash run_cpu.sh static_check.py',input_sha256=inputs,changes=changes,
            archive_sha256=archive_sha,archive_matches_disk=archive_checks,checksums=checksums,missing_inputs=missing)
(ROOT/'out/static_review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(changes=changes,archive_files=len(archive_checks),archive_mismatches=[k for k,v in archive_checks.items() if not v],missing_inputs=missing),indent=2))
