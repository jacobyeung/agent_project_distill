from pathlib import Path
import hashlib, json, re
L=Path(__file__).resolve().parent
B=L/'work/n1fix'
B.mkdir(parents=True,exist_ok=True)
(L/'work/tmp').mkdir(parents=True,exist_ok=True)
inventory={str(p.relative_to(L/'work/tree_r1')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (L/'work/tree_r1').rglob('*') if p.is_file()}
(B/'BUILD9FIX_FILES.json').write_text(json.dumps(inventory,indent=2)+'\n')
for p in (L/'work/build9fix').iterdir():
    if p.is_file() and p.suffix in ('.py','.sh'):
        text=p.read_text().replace('work/build9fix','work/n1fix')
        for old in ('/scratch/jjyeung/orch_n30/tree_rebuild_w/w9f','/scratch/jjyeung/orch_n30/tree_rebuild_w','/scratch/jjyeung/orch_n30/tree_rebuild'):
            text=re.sub(re.escape(old)+r'(?![\w])', '@@LOCAL@@',text)
        (B/p.name).write_text(text.replace('@@LOCAL@@',str(L)))
(B/'STATUS.md').write_text('# Build n1fix status\n\nHost verified. Review and sealed producer inspection are in progress. GO=false.\n')
(B/'DECISIONS.md').write_text('# Build n1fix decisions\n\n- Continuation: use P export-bound configuration and native preparation/run bindings; refuse unavailable evidence by name. An operator continuation receipt cannot establish progress.\n- Storage: reuse bounded local fixtures and authenticated receipts. Do not reread full stores or copy model assets.\n- Frame-host proof: require a job-private temporary namespace and validate the staged path closure before native preparation. Local tests simulate that namespace under work/tmp.\n')
print('Harness copies prepared inside '+str(B))
