from pathlib import Path
import json,re,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';M=L/'work/merge11'
old=B/'proofs/review_inputs';target=M/'proofs/n1/review_inputs'
if not target.exists():target.symlink_to(old,target_is_directory=True)
# Keep the published report pin equal to the local, semantically unchanged mix.
(L/'out/MIX_R1.json').write_bytes((B/'inputs/mix.json').read_bytes())
# Preserve kit roots from earlier builds; this build stages into an empty root.
p=B/'stage9.py';s=p.read_text().replace("root=B/'kits'","root=L/'work/merge11/kits'");p.write_text(s)
# Package the current kits, proofs' immutable inputs, review tests and their producer source.
p=B/'make_delivery.py';s=p.read_text().replace('tree_rebuild_bn1f2_', 'tree_rebuild_b11_')
s=s.replace("'work/n1fix2/kits'","'work/merge11/kits'")
s=s.replace("for folder in ('original','proofs/review_inputs'):","for folder in ('original','proofs/review_inputs'):")
s=s.replace("members=list(dict.fromkeys(members))", "members.append(L/'work/merge11/legacy9fix_source.py')\nmembers=list(dict.fromkeys(members))")
p.write_text(s)
# Run both exact frozen source variants; base reuse needs unchanged runner bytes.
p=B/'package.py';s=p.read_text().replace('work/n1fix2/kits','work/merge11/kits')
a=s.index("    if variant=='base':")
b=s.index("    env['R2_TREE']=str(path)",a)
s=s[:a]+s[b:]
p.write_text(s)
# These copies retain all assertions; only root paths and output destinations differ.
names=['test_runner.py','compact_tmp.py','monitor9.py','stage9.py','seal.py','make_delivery.py','package.py','packet_final.py','compare.py']
issues=[]
for name in names:
    for line,text in enumerate((B/name).read_text().splitlines(),1):
        if 'L.parent' in text or re.search(r'/tree_rebuild_w/(?:w9f|wn2|w10)(?:/|[\x27\x22])',text):issues.append(dict(file=name,line=line,text=text))
(M/'EXECUTABLE_PATH_SEARCH.json').write_text(json.dumps(dict(files=names,issues=issues),indent=2)+'\n')
assert not issues,issues
print('Final package harness uses local roots and fresh kits.')
