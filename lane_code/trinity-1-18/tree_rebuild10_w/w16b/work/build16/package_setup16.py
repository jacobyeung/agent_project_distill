from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
s=(L/'work/build15/delivery15.py').read_text()
s=s.replace('tree_rebuild_b15_','tree_rebuild_b16_').replace('work/build15/kits','work/build16/kits')
s=s.replace("L/'work/build15/PACKET_INPUTS.json'","L/'work/build16/PACKET_INPUTS.json'")
s=s.replace("L/'work/build15/DELIVERY.json'","L/'work/build16/DELIVERY.json'")
point="members.extend(p for p in (L/'out').glob('*.md'))"
addition="""
extra=L/'work/build16'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    if str(rel) in ('DELIVERY.json','proofs/integrity/RESULT.json'):continue
    if set(rel.parts)&{'mutant','frozen','base','kits','retained_kits_attempt'}:continue
    if p.suffix in ('.py','.sh','.json','.jsonl','.md','.log') and p.stat().st_size<30_000_000:members.append(p)
"""
assert point in s;s=s.replace(point,addition+'\n'+point)
(B/'delivery16.py').write_text(s)
