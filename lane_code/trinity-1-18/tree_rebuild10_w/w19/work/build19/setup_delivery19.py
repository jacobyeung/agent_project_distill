from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build19'
p=B/'delivery19.py';s=p.read_text()
block="""
extra=L/'work/build18'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    if set(rel.parts)&{'mutant','frozen','base','kits'}:continue
    if p.suffix in ('.py','.sh','.json','.jsonl','.md','.log') and p.stat().st_size<30_000_000:members.append(p)
"""
s=s.replace("members.extend(p for p in (L/'out').glob('*.md'))",block+"\nmembers.extend(p for p in (L/'out').glob('*.md'))")
p.write_text(s)
p=B/'integrity19.py';s=p.read_text().replace("'work/build19/inputs/u.json'","'work/build19/inputs/component_rows.json'").replace("'work/build19/proofs/rooms/RESULT.json'","'work/build19/proofs/rows/RESULT.json'")
p.write_text(s)
