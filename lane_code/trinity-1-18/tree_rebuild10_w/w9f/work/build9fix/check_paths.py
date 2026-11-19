from pathlib import Path
import json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
pattern=re.compile(r'/scratch/jjyeung/orch_n30/tree_rebuild(?:_w)?/(?!w9f(?:/|\b))')
matches=[]
for root in (L/'work/tree_r1',L/'work/build_n1',B,L/'work/contracts_r6',L/'fixtures'):
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in ('.py','.sh'):continue
        if 'proofs' in p.parts or 'kits' in p.parts:continue
        for i,line in enumerate(p.read_text().splitlines(),1):
            if pattern.search(line):matches.append(dict(file=str(p.relative_to(L)),line=i,text=line.strip()))
(B/'EXECUTABLE_PATH_SEARCH.json').write_text(json.dumps(matches,indent=2)+'\n')
print(json.dumps(matches,indent=2))
