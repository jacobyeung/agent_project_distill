from pathlib import Path
import hashlib, json, re
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/w10')
N=L.parent
F=N/'w9f'
B=L/'work/build10'
B.mkdir(parents=True,exist_ok=True)
(L/'work/tmp').mkdir(exist_ok=True)
copied=[]
def copy_text(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    raw=source.read_bytes()
    if len(raw)>10_000_000:raise ValueError(str(source))
    target.write_bytes(raw)
    copied.append(dict(source=str(source),target=str(target),sha256=hashlib.sha256(raw).hexdigest()))
for p in (F/'work/build9fix').iterdir():
    if p.is_file() and p.suffix in ('.py','.sh','.json','.md'):copy_text(p,B/p.name)
for p in (N/'work/design/eat1_v7/eat1').rglob('*'):
    if p.is_file() and p.suffix in ('.py','.json','.md','.sh'):copy_text(p,B/'eat1'/p.relative_to(N/'work/design/eat1_v7/eat1'))
rewritten=[]
# Relocate runnable harness copies only. Source/base and evidence retain their identities.
for p in B.rglob('*'):
    if not p.is_file() or 'eat1' in p.relative_to(B).parts:continue
    try:old=p.read_text()
    except UnicodeError:continue
    new=old.replace(str(F),str(L))
    new=re.sub(re.escape(str(N))+r'(?!/w10(?:/|\b))',str(L),new)
    new=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild(?![\w])',str(L),new)
    new=new.replace('work/build9fix','work/build10')
    if old!=new:p.write_text(new);rewritten.append(str(p.relative_to(L)))
(B/'RELOCATION.json').write_text(json.dumps(dict(copied=copied,rewritten=rewritten),indent=2)+'\n')
(B/'STATUS.md').write_text('# Build 10 status\n\nHost verified as trinity-1-3. Harness staging complete; G8 validation pending. G1–G7, byte parity, EAT-1 and final qualification remain pending. GO=false. Evidence: RELOCATION.json.\n')
(B/'DECISIONS.md').write_text('# Build 10 decisions\n\n- The v7 artifact already names fixed_math, with an unprojection-only description. Default: extend its validation to require zero parameters, declared inputs/outputs and artifact-bound buffer tensors; retain all existing clause checks.\n- Keep source paths unchanged until each runnable copy has an explicit path audit. Evidence-only receipts retain original identities.\n- Copy only bounded harness text and source. Read checkpoint and capture inputs in place; do not stage their tensors or frame sets.\n')
print(json.dumps(dict(copied=len(copied),rewritten=len(rewritten))))
