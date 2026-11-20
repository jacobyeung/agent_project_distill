"""Exercise GT conversion and the join on the supplied round-1 synthetic capture."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gpkg.capture_io import Records
from gpkg.runtime.c import Writer,unrle
from gpkg.join_capture import score
from gt.v2 import convert_file


def main():
    out=ROOT/'out2/synthetic';out.mkdir(exist_ok=False)
    source=ROOT/'kit2/work/rerun2/dry544/synthetic.jsonl.gz'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    records=Records(source,dict(sha256=digest));row,=list(records)
    assert row['synthetic'] is True
    ref=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items'][0]
    names=[obj['name'] for obj in row['objects']]
    assert names==['object']
    ref=copy.deepcopy(ref);ref['calls']=[dict(call='<ground obj="object" mode="box">'),dict(call='<ground obj="unbound" mode="box">')]
    inst=np.full((32,240,320),-1,np.int32)
    for frame,mask in row['objects'][0]['selected_masks'].items():inst[int(frame)-1][unrle(mask)]=1
    path=out/'GT.npz'
    with path.open('xb') as f:
        np.savez_compressed(f,inst=inst,ids=[1],labels=['object'],frame_indices=row['source_indices'],valid=np.ones(32,bool),
                            c2w=row['geometry']['camera_to_world_metric'],K_frames=np.tile(np.eye(3),(32,1,1)),
                            obb_centroid=[[0,0,0]],obb_lengths=[[1,1,1]],obb_axes=[np.eye(3).ravel()])
    gt,audit=convert_file(path,[ref],[row])
    (out/'GT.json').write_text(json.dumps({row['capture']:gt},indent=2)+'\n')
    (out/'GT_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    row['pass_index']=0
    writer=Writer(out/'0.gz');writer.append(row);writer.close()
    receipt=dict(trusted=False,items=1,capture_records=1,capture_sha256=hashlib.sha256((out/'0.gz').read_bytes()).hexdigest(),per_item=[])
    (out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    result=score(out/'0.gz',out/'RECEIPT.json',out/'GT.json',out/'JOIN.jsonl')
    joined=json.loads((out/'JOIN.jsonl').read_text())
    assert joined['evidence']['selected_correct_frames']==3
    assert joined['stage']=='U' and joined['alignment']['center_rank']==0
    evidence=dict(source=str(source.relative_to(ROOT)),source_sha256=digest,source_read=records.report,
                  join_read=result,visible=True,proposed=True,selected_correct_frames=3,stage='U',
                  reason='supplied synthetic cameras are stationary; their centers cannot determine a rotation',
                  synthetic_annotations=True,real_GT_claim=False)
    (out/'RESULT.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence))


if __name__=='__main__':main()
