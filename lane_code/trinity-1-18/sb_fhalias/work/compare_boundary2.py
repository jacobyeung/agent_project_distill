from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1]
paths=[W/'out/boundary_before2_contract.json',W/'out/boundary_after2_contract.json']
b,a=[json.loads(p.read_text()) for p in paths]
def key(r):return (r['operation'],r.get('case',r.get('source')),r.get('family'))
def status(r):return r.get('accepted',r.get('host_boundary_passed'))
old={key(r):r for r in b['records']};changes=[]
lines=['operation\tcase\tfamily\tbefore\tafter']
for r in a['records']:
 previous=old[key(r)]
 lines.append('\t'.join([r['operation'],r.get('case',r.get('source','')).replace('\n','\\n'),r.get('family',''),str(status(previous)),str(status(r))]))
 if status(previous)!=status(r):changes.append(dict(operation=r['operation'],case=r.get('case'),family=r.get('family'),before=status(previous),after=status(r)))
assert len(changes)==12
inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[Path(__file__).resolve()]}
(W/'out/BOUNDARY_DIFF2.json').write_text(json.dumps(dict(input_sha256=inputs,changed_subcases=changes,changed_count=len(changes)),indent=2)+'\n')
(W/'out/BOUNDARY_MATRIX2.tsv').write_text('\n'.join(lines)+'\n')
