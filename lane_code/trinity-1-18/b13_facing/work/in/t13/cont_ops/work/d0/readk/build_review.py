"""Bounded local source comparison; no Git, network, or deletion."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parent
BASE=Path('/scratch/jjyeung/orch_n30/evalx27/work/kit/package.tar')
PIN='f42aa1a4aec049e03a321e88ccd8a5004a3e95963b08f18242db625bdec95684'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(BASE.read_bytes())==PIN
with tarfile.open(BASE) as archive:
    old={m.name:archive.extractfile(m).read() for m in archive if m.isfile()}
new={str(p.relative_to(ROOT/'kit')):p.read_bytes() for p in (ROOT/'kit').rglob('*') if p.is_file()}
records=[];hunks=[];patches=[]
path_only={'launcher/orchard_results.py'}
for name in sorted(old.keys()|new.keys()):
    a,b=old.get(name,b''),new.get(name,b'')
    if a==b:
        records.append(dict(file=name,status='IDENTICAL',sha256=sha(b)))
        continue
    try:
        aa=a.decode().splitlines();bb=b.decode().splitlines()
    except UnicodeDecodeError:
        records.append(dict(file=name,status='BINARY_OMITTED' if name not in new else 'BINARY_CHANGED',
                            old_sha256=sha(a),new_sha256=sha(b) if b else None))
        hunks.append(dict(file=name,operation='binary',old_lines=[],new_lines=[],
                          old_bytes=len(a),new_bytes=len(b),classification='BEYOND',review='R1'))
        patches.append('Binary inventory differs: '+name)
        continue
    status='OMITTED' if name not in new else ('ADDED' if name not in old else 'CHANGED')
    records.append(dict(file=name,status=status,old_sha256=sha(a) if a else None,new_sha256=sha(b) if b else None))
    for tag,i,j,k,l in difflib.SequenceMatcher(a=aa,b=bb,autojunk=False).get_opcodes():
        if tag=='equal':continue
        classification='PATH/ENV' if name in path_only else 'BEYOND'
        hunks.append(dict(file=name,operation=tag,old_lines=[i+1,j] if j>i else [],new_lines=[k+1,l] if l>k else [],classification=classification,review='R1'))
    patches.extend(difflib.unified_diff(aa,bb,fromfile='f42aa1a4/'+name,tofile='candidate/'+name,lineterm=''))
manifest=dict(baseline_archive=str(BASE),baseline_sha256=PIN,files=records,changed_ranges=hunks)
(ROOT/'evidence/SOURCE_DIFF.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'evidence/SOURCE.patch').write_text('\n'.join(patches)+'\n')
lines=['# Source classification', '',
'Baseline: the authenticated evalx27 package `f42aa1a4`. The production wrapper imports the accepted runtime direct reader, checks its SHA256, and requires the accepted `d27804f7…` evaluator source digest. It does not execute the package’s optional official-data filter.', '',
'`direct.py`, `common.py`, `export_check.py`, and the r3/r4/r5 adapters retain their package bytes. The bind fixtures also compare all four prompt inventories to the accepted packet. The full archive-admission function and room-bootstrap function have identical ASTs to their reviewed sources.', '',
'Every added, removed, or replaced line is covered below. BEYOND is conservative: it includes all control-flow, admission, selection, packaging, documentation, and omitted official-workflow lines. PATH/ENV covers only the return alias/schema substitutions. Omitted files are absent from this specialized package, not removed from any source directory.', '',
'R1 is the primary agent’s completed local code review in `REVIEW.md`; it is not an independent review. Exact hunks are in `evidence/SOURCE.patch`; hashes and ranges are in `evidence/SOURCE_DIFF.json`.', '',
'| File | Baseline lines | Candidate lines | Class | Review |','|---|---:|---:|---|---|']
fmt=lambda v: '—' if not v else (str(v[0]) if v[0]==v[1] else f'{v[0]}–{v[1]}')
for h in hunks:
    old_range = f"binary: {h['old_bytes']} bytes" if h['operation']=='binary' else fmt(h['old_lines'])
    new_range = f"binary: {h['new_bytes']} bytes" if h['operation']=='binary' else fmt(h['new_lines'])
    lines.append(f"| `{h['file']}` | {old_range} | {new_range} | {h['classification']} | R1 |")
lines+=['','The following Trinity-side additions are BEYOND in their entirety and are included in R1:']
for p in [ROOT/'f1f2.py',ROOT/'room_bootstrap.py',ROOT/'build_review.py',ROOT/'REPORT.md',ROOT/'REVIEW.md',ROOT/'FIX1.md',ROOT/'FIX2.md',*sorted((ROOT/'tests').glob('*.py'))]:
    lines.append(f"- `{p.relative_to(ROOT)}`: lines 1–{len(p.read_text().splitlines())}.")
(ROOT/'DIFF.md').write_text('\n'.join(lines)+'\n')
# Small manifests describe shipped code, without hashing generated test trees.
(ROOT/'evidence/FINAL_PINS.json').write_text(json.dumps({
    **{'kit/'+name:sha(raw) for name,raw in new.items()},
    **{name:sha((ROOT/name).read_bytes()) for name in ('f1f2.py','room_bootstrap.py','build_review.py',
        'REPORT.md','REVIEW.md','FIX1.md','FIX2.md','DIFF.md','evidence/DONE_SAMPLES.txt','evidence/UPLOADER_FORMAT.txt',
        'evidence/FINAL_EXPORT_SOURCE.txt','evidence/FIX1_RECONSTRUCTION.json','evidence/FIX2_READER_CHECK.json','DIFF_FIX1.patch')},
    **{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'tests').glob('*.py'))}
},indent=2,sort_keys=True)+'\n')
print(json.dumps(dict(kit_files=len(new),changed_ranges=len(hunks),identical=sum(r['status']=='IDENTICAL' for r in records))))
