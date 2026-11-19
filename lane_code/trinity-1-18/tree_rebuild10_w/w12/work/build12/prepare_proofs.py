from pathlib import Path
import json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build12';N=L.parent
for name in ('mutation_confirm.py','portable_mutations.py'):
    s=(N/'wn3/work/n1fix3'/name).read_text().replace('work/n1fix3','work/build12')
    s=s.replace("str(T),str(B)","str(T),str(L/'work/n1fix2')")
    (B/name).write_text(s)
q=B/'proofs/review_inputs';q.mkdir(parents=True,exist_ok=True)
for name in ('MUTATION_SPEC.json','MUTANTS.json'):
    src=N/'wn3/work/n1fix3/proofs/review_inputs'/name
    if src.exists():(q/name).write_bytes(src.read_bytes())
# The current review carries the same sweep generator and byte-identical oracle.
p=B/'sweep.py';s=p.read_text().replace('review_tree10/work/parity','review_tree11/work/parity').replace('b9f_legacy.json','b11_legacy.json');p.write_text(s)
# Inspect the copied executable inputs, not inherited artifact prose.
issues=[]
for root in (B,L/'work/n1fix2',L/'work/build10'):
    for p in root.glob('*.py'):
        if p.name in ('bootstrap.py','prepare_proofs.py'):continue
        for line,text in enumerate(p.read_text().splitlines(),1):
            if re.search(r'/tree_rebuild_w/(?:wm|wn2|wn3|w10|w9f)/',text):
                issues.append(dict(file=str(p.relative_to(L)),line=line,text=text))
(B/'EXECUTABLE_PATH_SEARCH.json').write_text(json.dumps(dict(issues=issues),indent=2))
assert not issues,issues
(B/'STATUS.md').write_text('# Build 12 status\n\nGO=false. Merge targeted suite passed (proofs/merge_targeted/results.json). Default-deny handover, independent meta topology, producer receipt, legacy buffer binding and typed batch refusals are implemented; their proofs are in progress.\n')
