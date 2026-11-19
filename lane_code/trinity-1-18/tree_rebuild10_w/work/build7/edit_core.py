"""Bounded source edits; retain each pre-edit file for parity checks."""
from pathlib import Path
import json

L = Path(__file__).resolve().parents[2]
T = L / 'work/tree_r1'
B = L / 'work/build7'
def edit(name, old, new, count=1):
    path = T / name
    text = path.read_text()
    assert text.count(old) == count, (name, old[:100], text.count(old))
    saved = B / 'before' / name
    saved.parent.mkdir(parents=True, exist_ok=True)
    if not saved.exists(): saved.write_text(text)
    path.write_text(text.replace(old, new))

edit('student_pilot/carrier_c1_run.py', "'tool_mode_flag', 'ground_target_filter', 's1_route_policy',", "'tool_mode_flag', 'ground_target_filter', 's1_route_policy', 'h1', 'b7_inputs', 'frame_count',")
edit('student_pilot/carrier_c1_run.py', '        self.processor = processor\n', "        self.processor = processor\n        self.h1 = receipt.get('h1', {})\n")
records = json.loads((B/'PATCH_HUNKS.json').read_text())
for row in records:
    if row['status'] == 'conflict':
        row.update(status='adapted', reason='Preserved build 6 receipt fields and connection exclusions; inserted the h1 field at its current site')
(B/'PATCH_HUNKS.json').write_text(json.dumps(records, indent=2)+'\n')

edit('launch_s1/b/r.sh', 'tk_env\n', 'tk_env\n# Use a path visible through the shared kit bind, not the host-only kit path.\nexport K3="$X/o/${SLURM_JOB_ID:-local}.stop"\nexport R1_STOP_FILE="$K3"\n')
edit('launch_s1/b/w.py', "    root=Path(root)\n", "    root=Path(root)\n    os.environ.setdefault('K3', str(root/'o'/(os.environ.get('SLURM_JOB_ID','local')+'.stop')))\n    os.environ.setdefault('R1_STOP_FILE', os.environ['K3'])\n")
edit('student_pilot/carrier_c1_run.py', "        if os.environ.get('K3'):\n            stop[0] = stop[0] or Path(os.environ['K3']).is_file()\n", "        from .stop_control import requested\n        stop[0] = requested(stop[0], cfg, step)\n")
edit('student_pilot/carrier_c1_run.py', "        if not smoke_steps and (step in recipe['milestones'] or (stopping and recipe.get('export_at_stop'))):", "        if not smoke_steps and (step in recipe['milestones'] or (stopping and (recipe.get('export_at_stop') or cfg.get('stop_after_step') is not None))):")
edit('student_pilot/carrier_c1_decode.py', 'def parse_head(text):', 'def parse_head(text, frame_count=32):')
edit('student_pilot/carrier_c1_decode.py', 'frame <= 32:', 'frame <= frame_count:')
edit('student_pilot/carrier_c1_decode.py', 'k <= 32 for k in frames', 'k <= frame_count for k in frames')
edit('student_pilot/carrier_c1_decode.py', 'Routed decoding requires all 32 frame carriers', 'Routed decoding requires every configured frame carrier')
edit('student_pilot/carrier_c1.py', 'Clip pose readout requires all 32 frames', 'Clip pose readout requires every configured frame')
edit('student_pilot/carrier_c1.py', '        even=points.shape[0]==16', "        frame_count=valid.shape[-1]\n        even=points.shape[0]==frame_count//2")
edit('student_pilot/carrier_c1.py', '        if points.shape[0]!=32 or not valid.all():\n            raise ValueError(\'Readout requires 32 visible frames and 16 or 32 depth slots\')', "        if points.shape[0]!=frame_count or not valid.all():\n            raise ValueError('Readout depth slots must match the configured visible frames')")
edit('student_pilot/carrier_c1_run.py', '            anchors=list(range(1,33)),', "            anchors=list(range(1,cfg.get('frame_count',32)+1)),\n            **({'b7_inputs':cfg['b7_inputs'], 'max_pixels':cfg['max_pixels'],\n                'min_pixels':cfg['min_pixels'], 'frame_count':cfg['frame_count'],\n                'frame_markers':cfg['frame_markers'],\n                'weight_scale':cfg['camera_overrides']['weight_scale']} if 'b7_inputs' in cfg else {}),")

edit('student_pilot/carrier_c1_routing.py', "EVENT_KINDS =", "BOTH_TYPES = ('object_counting', 'object_size_estimation', 'object_rel_dist',\n              'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',\n              'object_abs_dist')\nPOLICIES['both-path-20261116'] = dict(route=CAMERA_MOTION, both=BOTH_TYPES,\n    direct=tuple(t for t in ALL_TYPES if t not in CAMERA_MOTION + BOTH_TYPES))\nEVENT_KINDS =")
edit('student_pilot/carrier_c1_routing.py', "                kind = 'route' if qtype in policy['route'] else 'direct' if qtype in policy['direct'] else None\n                calls = bool(raw['tool_output_spans'])", "                calls = bool(raw['tool_output_spans'])\n                both = qtype in policy.get('both', ())\n                kind = ('route' if calls else 'direct') if both else ('route' if qtype in policy['route'] else 'direct' if qtype in policy['direct'] else None)\n                gate_reason = None\n                if 'both' in policy:\n                    from .routing_type_gate import refusal\n                    gate_reason = refusal(qtype, 'routed' if calls else 'direct', policy)\n                    row['answer_form'] = 'routed' if calls else 'direct'")
edit('student_pilot/carrier_c1_routing.py', "                          'type_without_policy' if kind is None else", "                          gate_reason if gate_reason else\n                          'type_without_policy' if kind is None else")
edit('student_pilot/carrier_c1_routing.py', "'direct_policy_reasoning_row' if kind == 'direct' else", "'direct_policy_reasoning_row' if kind == 'direct' and not both else")
edit('student_pilot/carrier_c1_routing.py', "'direct_row_for_route_type' if qtype not in policy['direct'] else None)", "'direct_row_for_route_type' if qtype not in policy['direct'] + policy.get('both', ()) else None)\n                    if 'both' in policy:\n                        row['answer_form'] = 'direct'")

with (B/'STATUS.md').open('a') as f:
    f.write('\nCore edits applied. Cache and faithful-row hunk dispositions: `work/build7/PATCH_HUNKS.json`. The S1 stop-file path now reaches ranks; CPU proof is pending. Both-path gating preserves legacy policies.\n')
