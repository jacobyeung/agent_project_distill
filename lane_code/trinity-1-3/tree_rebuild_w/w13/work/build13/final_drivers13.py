"""Retain build-12 suite assertions and relocate only output and kit roots."""
from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build13';N=L/'work/n1fix2'
records=[]
for source,dest in [('packet_final.py','packet13.py'),('package.py','package13.py'),('compare.py','compare13.py')]:
    p=N/source;s=p.read_text()
    s=s.replace('work/build12/proofs/n1','work/build13/proofs/final').replace('work/build12/kits','work/build13/kits')
    if source=='compare.py':s=s.replace("L/'work/n1fix2/SUITE_COMPARISON.json'","L/'work/build13/SUITE_COMPARISON.json'")
    (B/dest).write_text(s)
    records.append(dict(source=str(p.relative_to(L)),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        output=dest,sha256=hashlib.sha256(s.encode()).hexdigest(),changes='Output and kit roots only; suite assertions unchanged.'))
s=(N/'make_delivery.py').read_text()
s=s.replace("f'tree_rebuild_b12_","f'tree_rebuild_b13_")
s=s.replace('work/build12/kits','work/build13/kits')
s=s.replace("size=sum(p.stat().st_size for p in members)+sum(row['bytes'] for row in packet_inputs);assert size<240_000_000", """extra=L/'work/build13'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    if set(rel.parts)&{'mutant','frozen','kits'}:continue
    if p.suffix in ('.py','.sh','.json','.md') and p.stat().st_size<30_000_000:members.append(p)
members.extend(p for p in (L/'out').glob('*.md'))
members.extend(L/'out'/n for n in ('TREE_SEAL.json','TREE_FILES.sha256','TREE.diff'))
members=list(dict.fromkeys(members))
size=sum(p.stat().st_size for p in members)+sum(row['bytes'] for row in packet_inputs)
assert size<600_000_000""")
s=s.replace("(B/'DELIVERY.json')", "(L/'work/build13/DELIVERY.json')")
(B/'delivery13.py').write_text(s)
(B/'RUNNER_EQUIVALENCE.json').write_text(json.dumps(records,indent=2))
