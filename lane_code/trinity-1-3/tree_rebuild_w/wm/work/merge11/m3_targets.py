from pathlib import Path
import json,difflib,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';T=L/'work/tree_r1';old=L.parent/'w10'
gaps=json.loads((old/'work/build10/GAPS.json').read_text());coverage=json.loads((B/'CHANGED_COVERAGE.json').read_text())
observed={(r['file'],r['line']):r['executed'] for r in coverage['statements']};records=[]
for name,lines in gaps.items():
    mapping={}
    before=(old/'work/tree_r1'/name).read_text().splitlines();after=(T/name).read_text().splitlines()
    for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag=='equal':mapping.update({i+1:c+i-a+1 for i in range(a,b)})
    for line in lines:
        mapped=mapping.get(line);records.append(dict(file=name,build10_line=line,current_line=mapped,observed=observed.get((name,mapped),False)))
(B/'M3_TARGETS.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records));assert all(r['observed'] for r in records)
