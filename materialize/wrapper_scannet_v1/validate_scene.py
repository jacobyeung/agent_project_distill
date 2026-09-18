"""Verify ScanNet preparer evidence, asset hashes, and exact training membership."""
import argparse, time
from pathlib import Path
import common as b

def validate(scene,dry=False):
    b.require_env(); b.verify_scripts(); before=b.verify_sources()
    if not dry:b.lease(scene)
    started=time.monotonic(); plan=b.scene_plan(scene,dry); output=Path(plan['output'])
    from gt_scene_assets import validate_scene, verify, read_json, load_arrays, validate_dense
    from training_assets import bind_runtime_row
    from collect import registry_rows
    import numpy as np
    evidence=read_json(output/'VALIDATION_RECEIPT.json')
    b.require(evidence['status']=='validated_not_admitted' and evidence['scene']==scene,'preparer terminal mismatch')
    b.require(evidence['contract']==b.pin(b.CONTRACT) and evidence['frames_receipt']==plan['frames_receipt'],'preparer authentication drift')
    b.require(evidence['paid_api_calls']==evidence['gpu_runs']==0,'CPU-only requirement')
    receipt_pin=evidence['scene_receipt'];receipt=validate_scene(read_json(verify(receipt_pin)),load_dense=True)
    b.require((receipt['dataset'],receipt['scene_name'],receipt['runtime_scene_id'])==('scannet',scene,plan['runtime_scene_id']),'scene identity mismatch')
    frames=read_json(verify(plan['frames_receipt']))
    b.require(all(receipt[k]==frames[k] for k in ('frames','selected_frames','video')),'RGB membership drift')
    source=read_json(verify(receipt['source_provenance']))
    b.require(source['preparer_contract']==b.pin(b.CONTRACT) and source['collector_admission'] is False,'preparer provenance missing')
    b.require(source['dataset']=='scannet' and source['source_scene_id']==scene and source['raw_sources']==evidence['raw_sources'],'official source binding mismatch')
    # The pinned preparer hashes every raw input before and after materialization.
    for spec in evidence['raw_sources'].values():
        b.require(Path(spec['path']).stat().st_size==spec['size_bytes'],'raw source size changed after preparer')
    visibility=read_json(verify(evidence['all_frame_visibility']))
    alignment=read_json(verify(receipt['alignment']))
    b.require(visibility['validated_slots']==alignment['validated_slots']==32,'incomplete 32-slot validation')
    dense=validate_dense(load_arrays(receipt['dense']),receipt['frames'])
    calibration=load_arrays(receipt['calibration'])
    for key in ('camera_poses','intrinsics'):b.require(np.array_equal(dense[key],calibration[key]),'dense camera binding mismatch')
    b.require(len(alignment['frames'])==len(alignment['render_audits'])==32,'camera/reprojection census mismatch')
    b.require(min(r['raw_to_vsi_correlation'] for r in alignment['frames'])>=.99,'RGB correlation gate')
    b.require(max(r['max_reprojection_px'] for r in alignment['render_audits'])<=.05,'reprojection gate')
    selected=b.selected_rows(scene);membership=b.membership_summary(selected)
    for row in selected:
        bound=bind_runtime_row(row,receipt)
        b.require(bound['scene_name']==plan['runtime_scene_id'] and bound['id']==row['id'] and bound['source_scene_name']==scene,'membership binding mismatch')
        b.require(row['video']==f'scannet/{scene}.mp4','membership video mismatch')
    after=b.verify_sources();b.require(before['source_files']==after['source_files'],'preparer closure changed')
    # Only this separate registry namespace is written; parsing does not start a collector.
    registry=output/'registry.json';b.write(registry,b.registry([receipt_pin]))
    b.require(registry_rows({'assets_registry':str(registry)})=={('scannet',scene):receipt_pin},'registry parser mismatch')
    files={p.name:b.pin(p) for p in sorted(output.iterdir()) if p.is_file() and not p.name.startswith('.')}
    result=dict(schema='req232-scannet-gt-validation-v1',status='PASS',checked_at=b.utc(),scene=scene,
        runtime_scene_id=receipt['runtime_scene_id'],validated_slots=32,membership=membership,
        scene_receipt=receipt_pin,source_contract=b.pin(b.CONTRACT),script_manifest=b.pin(b.ROOT/'CONTRACT.json'),
        preparer=b.CONFIG['preparer'],preparer_validation=b.pin(output/'VALIDATION_RECEIPT.json'),
        output_files=files,output_size_bytes=sum(p['size_bytes'] for p in files.values()),
        elapsed_seconds=time.monotonic()-started,collector_admission=False,paid_api_calls=0,gpu_runs=0)
    b.write((b.ROOT/'dry_run' if dry else b.JOBS/scene)/'VALIDATION.json',result)
    print(b.canonical({'scene':scene,'status':'PASS','questions':len(selected)}).decode(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scene',required=True);p.add_argument('--dry',action='store_true');a=p.parse_args();validate(a.scene,a.dry)
