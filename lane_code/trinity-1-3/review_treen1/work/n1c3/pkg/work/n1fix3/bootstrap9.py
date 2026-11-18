from pathlib import Path
import hashlib, json, re
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/wn3')
B=L/'work/n1fix3'
N=L.parent
(L/'work/tmp').mkdir(parents=True,exist_ok=True)
B.mkdir(parents=True,exist_ok=True)
records=[]
for p in (L/'work/n1fix3').iterdir():
    if p.is_file() and p.suffix in ('.py','.sh','.json','.md'):
        target=B/p.name
        target.write_bytes(p.read_bytes())
        records.append(dict(source=str(p),destination=str(target),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
# Relocate every copied text reference, including scripts nested in kits.
# The base is evidence and remains byte-identical.
changed=[]
for root in (L/'work/n1fix3',B,L/'work/tree_r1',L/'work/contracts_r6',L/'out',L/'fixtures'):
    for p in root.rglob('*'):
        if not p.is_file() or p.is_symlink() or p.suffix not in ('.py','.sh','.json','.jsonl','.md','.txt','.yaml','.yml','.toml','.cfg','.ini'):continue
        try:text=p.read_text()
        except UnicodeError:continue
        new=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild_w/wn3/wn2(?:_w)?(?![\w/])',str(L),text)
        new=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild_w/wn3/wn2(?:_w)?/(?!w9f(?:/|\b))',str(L)+'/',new)
        if p.is_relative_to(B):new=new.replace('work/n1fix3','work/n1fix3')
        if new!=text:p.write_text(new);changed.append(str(p.relative_to(L)))
(B/'RELOCATION.json').write_text(json.dumps(dict(copied=records,rewritten=changed),indent=2)+'\n')
(B/'STATUS.md').write_text('# Build 9fix status\n\nHost verified: trinity-1-3. Workspace isolation prepared; source: RELOCATION.json. F1–F6 implementation and proofs are pending. GO=false.\n')
(B/'DECISIONS.md').write_text('# Build 9fix decisions\n\n- F1 baseline versus F5 extent refusal: measure the unchanged slices before enabling the extent receipt, then require the receipt for final intake and reader admission. This preserves separate evidence for each requirement.\n- Extent variants: default to repaired rows; retain filtered source pins as an explicit input parameter. Never infer a verdict from the dataset name.\n- Source isolation: rewrite executable path references in copied inputs; preserve the base tree as comparison evidence.\n- Final restaging: use a fresh fixed kit folder for this build; retain existing kits as evidence.\n')
print(json.dumps(dict(copied=len(records),rewritten=len(changed))))
