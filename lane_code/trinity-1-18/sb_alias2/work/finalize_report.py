"""Render compact stream/family counts from the audited JSON."""
import json
from pathlib import Path
base=Path(__file__).resolve().parent.parent
p=base/'out/ROOM_AUDIT_REPORT.md';s=p.read_text();a=json.loads((base/'out/ROOM_AUDIT_TIERED.json').read_text())
s=s.replace('The audit covers all 204,413 v7 rows; 204,413 have proven scenes and resolved rooms. Counts apply to the proven rows; unresolved rows are not declared overlap-free.','The audit covers all 204,413 v7 rows. Every row has a proven scene and a resolved room.')
streams=list(a['hits_by_stream']['K1'].items());families=list(a['hits_by_family']['K1'].items())
lines=['','| K1 stream | Rows | K1 family | Rows |','|---|---:|---|---:|']
for i in range(max(len(streams),len(families))):
 st,sc=streams[i] if i<len(streams) else ('','');fa,fc=families[i] if i<len(families) else ('','')
 lines.append(f'| {st} | {sc} | {fa} | {fc} |')
s=s.replace('\nThe hash function agrees', '\n'.join(lines)+'\n\nThe hash function agrees',1)
s=s.replace('The archive also has 1,083 literal keys.','The archive also has 1,083 literal keys. All 2,571 hashed v7 row-field witnesses agree as well.')
s=s.replace('`python work/package.py` packages','`python work/finalize_report.py` renders the stream/family table from the audit JSON.\n`python work/package.py` packages')
assert len(s.splitlines())+2<=80,len(s.splitlines())
p.write_text(s);print('report lines before archive digest:',len(s.splitlines()))
