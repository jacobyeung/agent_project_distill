"""Replay three K1 rows using frozen selected-mask memberships and saved geometry."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run as B
import hashlib,json
import numpy as np
B.setup();R=B.R
root=B.HERE.parent/'r2'
box=json.loads((root/'out_box/BOX.json').read_text())
cap='arkitscenes/41098085'
receipt_path=root/'out4/factorial'/('arkitscenes__41098085.json')
receipt=json.loads(receipt_path.read_text())
key=hashlib.sha256(R.wire_json.wire_dumps(cap,sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]
folder=Path('/scratch/jjyeung/k1/run_convert_2')/key
with np.load(folder/'geometry.npz',allow_pickle=False) as z:
    g=R.geometry.from_arrays(**{n:z[n] for n in ['K','canvas_to_source','camera_to_world','depth_grid','grid_uv','anchor_frame_indices']},scale=receipt['geometry']['served_scale'])
cache=json.loads((folder/'candidates.json').read_text())
detect,=B.declarations(root/'vendor/ladder_predicted.py',['cache_detect'],dict(np=np))
detect=detect(cache)
checks=[];masks={}
for row in [r for r in box['rows'] if r['capture']==cap and r['box']['deployed/base']['prediction']!=r['box']['deployed/fused']['prediction'] and len(r['box']['deployed/fused']['printed'])==2][:3]:
    expected=row['box']['deployed/fused'];names=list(expected['printed'])
    if len(names)!=2:raise ValueError('test needs two answered operands')
    for n in names:
        if n not in masks:
            raw=detect(n);m=np.zeros((32,240,320),bool)
            for f,index in receipt['choices'][n]['members']:m[f-1]=raw[f-1][index]['mask'][::2,::2]
            masks[n]=m
    base=B.timed(names,masks,g,'base');got=B.timed(names,masks,g,'vote')
    assert got['gap_m']==expected['prediction'],(row['row_id'],got['gap_m'],expected['prediction'])
    assert base['gap_m']==row['box']['deployed/base']['prediction']
    for j,n in enumerate(names,1):
        obj=B.lift_frames(n,masks[n],g,R.grounding)
        text=R.boxes.serialize(n,'B'+str(j),obj['frames'],obj['best'],expected['printed'][n])
        assert text==got['responses'][n]
    checks.append(dict(row_id=row['row_id'],base_m=base['gap_m'],vote_m=got['gap_m'],prediction_and_printed_boxes_match=True,measurements=dict(base=base,vote=got)))
assert len(checks)==3
B.write(B.HERE/'K1_TEST.json',dict(passed=True,capture=cap,hardware=B.hardware(),checks=checks,method='Saved selector memberships, original candidate RLE masks, served geometry NPZ and recorded own-depth scale; compares against r2/out_box/BOX.json.',input_sha256={str(p):R.sha(p) for p in [receipt_path,folder/'geometry.npz',folder/'candidates.json',root/'out_box/BOX.json']}))
print('PASS: three K1 rows, base/vote predictions and vote printed boxes')
