"""Demonstrate convert/serving acceptance differences on the missing train exports."""
import json
import re
import time
import torch
import numpy as np
from debug_geometry import ROOT, K1, SEL, OUT, read, write, npz, digest, sources, median_ratio
from adapters import reviewed_loader
from e2e_reader.geometry import from_tower, from_npz
from e2e_reader.stage1 import StageOne
from e2e_reader.grounding import StageOneSocket, ground_session
from selector_head import load_head
from predicted import cache_detect
from student_pilot.scene_state import FrameMap


def main():
    torch.set_num_threads(8)
    start=time.monotonic()
    audit=json.loads(read(OUT/'SERVING_SCALE_AUDIT.json'))
    names={r['capture'] for r in audit['rows'] if r['status']=='MISSING'}
    cs=[c for c in json.loads(read(ROOT/'train_manifest.json'))['captures'] if c['canonical'] in names]
    primary=set(read('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt').decode().splitlines())
    loader,guard,_=reviewed_loader()
    directory=SEL/'work/run_iso'
    for ext in ('json','safetensors'):read(directory/f'selector_head.{ext}')
    head,_=load_head(directory)
    evidence=[]
    for c in cs:
        assert c['k1_split']=='train'
        key=digest(c['canonical'])[:16];folder=K1/'run_convert_2'/key
        receipt=json.loads(read(folder/'CACHE_COMPLETE.json'))
        refused=folder/'REFUSED_GEOMETRY.npz';arrays=npz(refused)
        try:
            with guard.capture('guard_audit',c['canonical']):
                loader(refused,FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
            reviewed='ACCEPTED'
        except ValueError as exc:reviewed=type(exc).__name__+':'+str(exc)
        # The deployed reader accepts exactly these stored arrays.
        restored=from_npz(refused)
        tower=npz(K1/'run_tower_sam_2'/key/'tower.npz')
        hw=json.loads(read(K1/'run_tower_sam_2'/key/'PHASE_COMPLETE.json'))['source_hw']
        own=npz(K1/'own_170235/native/probe'/key/'own.npz')
        scale=median_ratio(tower['depth_grid'],tower['depth_conf_grid'],own['depth'])
        scale=float(torch.tensor(float(np.log(scale))).exp())
        live=from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],tower['depth_grid'],tower['grid_uv'],own['gravity'],scale,hw)
        cache=json.loads(read(folder/'candidates.json'))
        stage=StageOne(cache_detect(cache),head,live,rule='candidates_argmax')
        socket=StageOneSocket(stage.propose,stage.select,(240,320),32)
        session=ground_session(live,socket)
        rows=[r for r in c['rows'] if r['id'] in primary]
        outputs=[]
        for row in rows:
            for name in row['operands']:session.execute(f'<ground obj="{name}" mode="box">')
            a,b=row['operands']
            response=session.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
            outputs.append(dict(row_id=row['id'],operands=row['operands'],response=response,
                                answered=bool(re.fullmatch(r'distance [0-9]+\.[0-9]{2} m',response))))
        evidence.append(dict(capture=c['canonical'],missing_geometry=str(folder/'geometry.npz'),
            convert_receipt_refusal=receipt.get('geometry_refusal'),reviewed_loader=reviewed,
            reader_from_npz='ACCEPTED',reader_from_tower='ACCEPTED',
            stored_scale=float(arrays['scale']),reader_scale=scale,
            primary_train_rows=len(rows),reader_answered=sum(r['answered'] for r in outputs),rows=outputs))
    sources();read(ROOT/'audit_guard.py')
    write(OUT/'SERVING_GUARD_AUDIT.json',dict(captures=evidence,seconds=time.monotonic()-start,
        conclusion='BLOCKER: spec A0 GD_reviewed refuses registered train captures that the R1 serving reader accepts and answers'))
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
