from pathlib import Path
import json
import sys
L=Path(__file__).resolve().parents[2];B=L/'work/build7';T=L/'work/tree_r1'
ns={};exec((B/'edit_core.py').read_text().split("edit('student_pilot")[0],{'__file__':str(B/'edit_core.py')},ns)
edit=ns['edit'];edit.__globals__.update(ns)
edit('launch_s1/b/r.sh', "    printf 'USR1\\n' >> \"$stop_file\"", "    printf 'USR1\\n' >> \"$stop_file\"\n    # The sandbox kit is a separate staging directory. Publish the same request there.\n    if [[ -n \"${NX:-}\" && -d \"$NX/o\" ]]; then\n        printf 'USR1\\n' >> \"$NX/o/${SLURM_JOB_ID:-local}.stop\"\n    fi")
edit('student_pilot/b7_inputs.py', "getattr(model, 'inherited_pose_names', ())", "getattr(model, 'inherited_head_params', ())")
edit('student_pilot/carrier_c1_run.py', "            heads={'path':str((directory/'heads.pt').resolve()),'sha256':pin['sha256']}))", "            heads={'path':str((directory/'heads.pt').resolve()),'sha256':pin['sha256']}))\n        if 'b7_inputs' in cfg:\n            from .b7_inputs import module_trainability\n            metadata = load(directory/'artifact.json')\n            metadata['trainable_modules'] = module_trainability(model,cfg)\n            write(directory/'artifact.json',metadata)\n            from .eat1_export import write_manifest\n            write_manifest(directory,model,cfg)")
edit('student_pilot/r2_contract.py', 'def preparation(cfg):\n', "def preparation(cfg):\n    if 'b7_inputs' in cfg:\n        from .b7_inputs import validate\n        validate(cfg['b7_inputs'], 'a2' if cfg.get('geometry_connector')=='gf1' else 'a0', verify=True)\n")
edit('student_pilot/carrier_c1_run.py', '    return bool(routing.excluded(benchmark, *keys)), int(routing.excluded(reported, *keys))', "    from .r0_exclusion import reserve\n    return bool(routing.excluded(benchmark, *keys) or reserve().matches(row)), int(routing.excluded(reported, *keys))")
edit('student_pilot/carrier_c1_run.py', '            from .r0_exclusion import Reserve\n            Reserve().check(value, stream)', '            from .r0_exclusion import reserve\n            reserve().check(value, stream)')
edit('student_pilot/carrier_c1_data.py', "    inputs = layout_inputs(row, layout, gap, frame_count=frame_count)", "    if hasattr(processor, '_b7_layout'):\n        from .r0_exclusion import reserve\n        reserve().check(row, 'dense_frames')\n        if len(row['student_input']['frames']) != frame_count:\n            raise ValueError('row_training_frame_count_mismatch')\n    inputs = layout_inputs(row, layout, gap, frame_count=frame_count)")
edit('student_pilot/r0_exclusion.py', 'import hashlib\n', 'import hashlib\nfrom functools import lru_cache\n')
p=T/'student_pilot/r0_exclusion.py';p.write_text(p.read_text()+"\n\n@lru_cache(maxsize=1)\ndef reserve():\n    return Reserve()\n")
sys.path.insert(0,str(T))
from student_pilot.response_spec import document
(T/'student_pilot/response_spec.json').write_bytes(document())
# Keep packet assertions and build-6 support adaptations, in a fixed owned directory.
for p in (L/'work/build6/packet').rglob('*'):
 if p.is_file():
  dest=B/'packet'/p.relative_to(L/'work/build6/packet');dest.parent.mkdir(parents=True,exist_ok=True)
  if p.suffix in ('.py','.json','.md','.txt'):
   dest.write_text(p.read_text().replace('work/build6','work/build7'))
  else:dest.write_bytes(p.read_bytes())
for name in ('classify_coverage.py','LEGACY_GUARDS.json'):
 p=L/'work/build6'/name
 (B/name).write_text(p.read_text().replace('work/build6','work/build7'))
# A complete new model inventory is written at export; semantic config flags are pinned now.
policy=dict(base_vit=dict(trainable=False,learning_rate=0.),merger=dict(trainable=False,learning_rate=0.),
 private_vit=dict(trainable=True,learning_rate=1e-5,frozen_submodules=['merger']),
 pose_head=dict(trainable=True,learning_rate=6e-5,inherited_learning_rate=1e-5),
 depth_head=dict(trainable=True,learning_rate=1e-4),lm=dict(trainable=True,learning_rate=6e-6))
(B/'TRAINABLE_POLICY.json').write_text(json.dumps(policy,indent=2)+'\n')
