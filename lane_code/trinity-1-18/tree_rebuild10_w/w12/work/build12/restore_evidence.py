from pathlib import Path
import hashlib,json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build12';N=L.parent
records=[]
def copy(src,dst):
    if not src.is_file():return
    raw=src.read_bytes();assert len(raw)<50_000_000
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
    records.append(dict(source=str(src),target=str(dst.relative_to(L)),sha256=hashlib.sha256(raw).hexdigest()))
for name in ('CHANGED_COVERAGE.json','GAPS.json','PROOF_EQUALITY.json','FINAL_INTEGRITY.json'):
    copy(N/'wm/work/merge11'/name,B/'inherited11'/name)
for name in ('CHANGED_COVERAGE.json','GAPS.json','SUITE_COMPARISON.json'):
    copy(N/'wn3/work/n1fix3'/name,B/'inherited3'/name)
for name in ('KIT_RESULT.json','SUITE_COMPARISON.json','PACKET_INPUTS.json'):
    copy(N/'wm/work/n1fix2'/name,B/'inherited11'/name)
for group in ('suite_base','suite_tree'):
    for part in ('','generator','legacy','r2'):
        for name in ('results.json','source_hashes.json','hits.json','GROUP_RECEIPT.json','TEST_INVENTORY.json'):
            copy(N/'wm/work/merge11/proofs/n1'/group/part/name,B/'inherited11'/group/part/name)
for group in ('text','forward','checkpoint'):
    copy(N/'wn3/work/n1fix3/proofs'/group/'RESULT.json',B/'inherited3'/group/'RESULT.json')
for name in ('N1R.json','N1R2.json','N1C.json','N3_VARIANTS_C3.json','MUTANTS.json'):
    copy(Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c3')/name,B/'review_inputs'/name)
# The immutable proof-input records omitted by the archive are small JSON files.
src=N/'wm/work/merge11/proofs/n1/review_inputs'
for p in src.glob('*.json'):copy(p,B/'proofs/n1/review_inputs'/p.name)
for rel in ('input_samples/units/samples.json',):
    copy(N/'wm/work/merge11/proofs/n1'/rel,B/'proofs/n1'/rel)
# Localize copied metadata references; their hashes are refreshed bottom-up.
root=L/'work/n1fix2/inputs'
def rewrite(v):
    if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
    if isinstance(v,list):return [rewrite(x) for x in v]
    if isinstance(v,str):return re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild_w/(?:wm|wn2|wn3|w9f|w10)(?=/)',str(L),v)
    return v
def refresh(v):
    if isinstance(v,list):return [refresh(x) for x in v]
    if not isinstance(v,dict):return v
    v={k:refresh(x) for k,x in v.items()}
    if isinstance(v.get('path'),str) and v.get('sha256'):
        p=Path(v['path'])
        if p.is_relative_to(root) and p.is_file():v['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    return v
for _ in range(6):
    for p in root.glob('*.json'):
        try:old=json.loads(p.read_text())
        except json.JSONDecodeError:continue
        new=refresh(rewrite(old))
        if old!=new:p.write_text(json.dumps(new,indent=2)+'\n')
(L/'out/MIX_R1.json').write_bytes((root/'mix.json').read_bytes())
(B/'INHERITED_EVIDENCE.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(records=len(records))))
