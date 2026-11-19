"""Derive the delivery membership from the retained build-14 packaging contract."""
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
s=(L/'work/build14/delivery14.py').read_text()
s=s.replace('tree_rebuild_b14_','tree_rebuild_b15_').replace('work/build14/kits','work/build15/kits')
s=s.replace("L/'work/build14/PACKET_INPUTS.json'","L/'work/build15/PACKET_INPUTS.json'")
s=s.replace("L/'work/build14/DELIVERY.json'","L/'work/build15/DELIVERY.json'")
point="members.extend(p for p in (L/'out').glob('*.md'))"
addition="""
extra=L/'work/build15'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    if str(rel) in ('DELIVERY.json','proofs/integrity/RESULT.json'):continue
    if set(rel.parts)&{'mutant','frozen','kits'}:continue
    if p.suffix in ('.py','.sh','.json','.md') and p.stat().st_size<30_000_000:members.append(p)
"""
assert point in s;s=s.replace(point,addition+'\n'+point)
(B/'delivery15.py').write_text(s)
