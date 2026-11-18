from pathlib import Path
import re,json
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';N=L.parent
for folder in ('n1fix2','build10'):
    root=L/'work'/folder
    for p in root.iterdir():
        if not p.is_file() or p.suffix not in ('.py','.sh'):continue
        s=p.read_text().replace(str(L)+'/wm',str(L)).replace('N=L.parent','N=L')
        proof='work/merge11/proofs'+('/n1' if folder=='n1fix2' else '')
        s=re.sub(r"B/'proofs([^']*)'",lambda m:"L/'"+proof+m[1]+"'",s)
        if folder=='n1fix2':s=s.replace("B/'kits'","L/'work/merge11/kits'")
        p.write_text(s)
    for sub in ('eat1','b04_stage'):
        for p in (root/sub).rglob('*.py'):
            p.write_text(p.read_text().replace(str(L)+'/wm',str(L)))
for folder in ('proofs','proofs/n1','proofs/parity','proofs/parity_build7','proofs/gf1','proofs/c8r'):
    (B/folder).mkdir(parents=True,exist_ok=True)
# Exact read-only input files stay on their original filesystem; no tensors or frames are copied.
links=[]
for kind in ('gf1','c8r'):
    src=N/'work/build7/proofs/eat1'/kind
    for rel in ['artifact/weights.pt','items.jsonl','run/ITEMS.jsonl']+[str(p.relative_to(src)) for p in (src/'frames').iterdir() if p.is_file()]:
        q=L/'work/build7/proofs/eat1'/kind/rel;q.parent.mkdir(parents=True,exist_ok=True)
        if not q.exists():q.symlink_to(src/rel)
        links.append(dict(local=str(q),source=str(src/rel)))
(B/'READONLY_INPUTS.json').write_text(json.dumps(links,indent=2)+'\n')
# Production test fixture paths point at the local copied fixtures.
for name in ('test_r2_data_path.py',):
    p=L/'work/tree_r1/tests'/name
    s=p.read_text()
    s=re.sub(re.escape(str(N))+r'/(?:wn2|w9f)(?:_w)?(?:/w9f)?',str(L),s)
    p.write_text(s)
