"""Freeze PRIMARY_296 training membership, corrected labels, and raw-table coverage."""
import hashlib,json,re
from pathlib import Path
from adapters import ROOT,READER
REGISTRY=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/GT_SET_PRIMARY_296.json')
AUDIT=Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_BOX_AUDIT.json')
def main():
    pins={}
    def read(p):
        b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
    manifest=json.loads(read(ROOT/'train_manifest.json'));pins.update(manifest['input_sha256'])
    reg=json.loads(read(REGISTRY));assert len(reg)==296
    cs=[c for c in manifest['captures'] if c['canonical'] in reg]
    for c in cs:c['gt']=reg[c['canonical']]
    rows=[dict(row_id=r['id'],capture=c['canonical'],room=c['room']) for c in cs for r in c['rows'] if r['type']=='object_abs_distance']
    pred=[r for r in rows if (READER/'heads/selector/data/caps_raw'/(r['capture'].replace('/','__')+'.json.gz')).is_file()]
    assert len(rows)==1037 and len({r['room'] for r in rows})==192
    # Decode only audit entries belonging to train captures; never read held-out metrics.
    train={c['canonical'] for c in cs};boxes={}
    for block in re.findall(r'^  "[^"\n]+": \{\n.*?^  \}',read(AUDIT).decode(),re.M|re.S):
        canonical=re.search(r'"canonical": "([^"\n]+)"',block)
        if canonical and canonical[1] in train:
            entry=json.loads('{'+block+'}');boxes.update(entry)
    outputs={'pinned_train.json':dict(captures=cs,rows=rows,predicted_rows=pred,counts=dict(gt_rows=len(rows),gt_rooms=len({r['room'] for r in rows}),predicted_rows=len(pred),predicted_rooms=len({r['room'] for r in pred}))), 'train_boxes.json':dict(boxes=boxes)}
    for name,obj in outputs.items():(ROOT/name).write_text(json.dumps(dict(obj,input_sha256=pins))+'\n')
    (ROOT/'STATUS.md').write_text(f'Stage 2: Pinned {len(rows)} training distance rows in 192 physical rooms to PRIMARY_296, with {len(pred)} rows covered by raw-name selector tables. Corrected labels and training-only box audit entries are separate from stored-label parity. The CPU StageOne replay check is running; no held-out evaluation has run.\n')
    print(outputs['pinned_train.json']['counts'], 'train audit boxes',len(boxes))
if __name__=='__main__':main()
