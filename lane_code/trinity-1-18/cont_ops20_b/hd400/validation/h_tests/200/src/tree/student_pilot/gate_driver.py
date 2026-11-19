"""Run a checkpoint's heads on held-out scenes and score them with gate_eval.

Inputs:
- one row per held-out scene, in the training-row schema (opaque dataset and scene tokens,
  student_input with the 32 frames and their frame_indices);
- a v2 label bank built for those scenes (tools/label_bank_build.py);
- the held-out list and the training rows' scene census (both lists of [dataset, scene] tokens);
- a model with its trained heads attached (load_checkpoint on GPU, or any model in tests).

Every scene must be on the held-out list, absent from the training census, present in the bank with
the row's own frame set, and answered by every head; anything else raises.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from .camera_targets import GROUPS, insert_carriers
from .compact_label_bank import frame_set_sha256, read_bank
from .gate_eval import evaluate
from .head_api import FRAME_ANCHORS, HeadSession


def heads_of(supervision):
    heads = {'pose'}
    if supervision.has_gravity:
        heads.add('gravity')
    if supervision.has_scale:
        heads.add('scale')
    if supervision.point_depth is not None:
        heads.add('depth')
    return heads


def scene_records(model, tokenizer, rows, bank_path, encode_row, forward_context=None):
    """Predictions and labels per held-out row, in gate_eval's record layout."""
    bank = read_bank(bank_path)
    lookup = {key: i for i, key in enumerate(zip(bank['dataset_tokens'].tolist(), bank['scene_tokens'].tolist()))}
    records = []
    for row in rows:
        key = (row.get('dataset'), row.get('scene'))
        if key not in lookup:
            raise ValueError(f'Held-out scene {key} has no labels in the bank')
        index = lookup[key]
        if frame_set_sha256(row['student_input']['frame_indices']) != str(bank['frame_set_sha256'][index]):
            raise ValueError(f'Held-out row {key} uses other frames than its bank labels')
        batch = insert_carriers(encode_row(row), tokenizer)
        session = HeadSession.from_forward(model, batch, forward_context=forward_context)
        uv, depth_mask = bank['point_depth_uv'][index].astype(np.float64), bank['point_depth_mask'][index]
        pred_depth = None
        if session.feature_map is not None:
            pred_depth = np.zeros(depth_mask.shape)
            for g in range(GROUPS):
                if depth_mask[g].any():
                    pred_depth[g] = session.depth(FRAME_ANCHORS[g], uv[g])
        records.append({
            'dataset': key[0], 'scene': key[1],
            'gt': {'camera': bank['camera'][index].astype(np.float64), 'camera_mask': bank['camera_mask'][index],
                   'gravity': bank['gravity'][index].astype(np.float64), 'gravity_mask': bool(bank['gravity_mask'][index]),
                   'trajectory_scale': float(bank['trajectory_scale'][index]), 'point_depth_uv': uv,
                   'point_depth_gt': bank['point_depth_gt'][index].astype(np.float64), 'point_depth_mask': depth_mask},
            'pred': {'camera': session.raw_pose, 'gravity': session.gravity_up,
                     'trajectory_step_m': session.trajectory_step_m, 'point_depth': pred_depth},
        })
    return records


def run_gate(model, tokenizer, rows, bank_path, heldout, training_scenes, encode_row, forward_context=None):
    from .auxiliary_losses import unwrap

    supervision = unwrap(model).auxiliary_heads.camera
    records = scene_records(model, tokenizer, rows, bank_path, encode_row, forward_context)
    return evaluate(records, heads_of(supervision), heldout, training_scenes)


def load_checkpoint(student, adapter_dir, heads_json, heads_pt, device='cuda:0'):
    """Base model + adapter (+ vision blocks) + trained heads, in eval mode, and its processor."""
    import torch

    from .auxiliary_losses import attach
    from .batches import load_processor
    from .runner import load_adapter, load_base

    processor = load_processor(student)
    model, report = load_adapter(load_base(student, device=device), adapter_dir)
    manifest = json.loads(Path(heads_json).read_text())
    if 'camera' not in manifest:
        raise ValueError('The checkpoint has no camera heads')
    settings = manifest['settings'] if manifest['settings'].get('pose_weight') or manifest['settings'].get('depth_weight') else None
    heads = attach(model, settings, processor.tokenizer, manifest['camera']['settings'])
    state = torch.load(heads_pt, map_location='cpu', weights_only=True)
    missing, unexpected = heads.load_state_dict(state, strict=True)
    if missing or unexpected:
        raise ValueError('Head weights differ from the attached heads')
    model.eval()
    return model, processor, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--student', required=True)
    parser.add_argument('--adapter-dir', required=True)
    parser.add_argument('--heads-json', required=True)
    parser.add_argument('--heads-pt', required=True)
    parser.add_argument('--rows', required=True, help='JSONL, one held-out row per scene')
    parser.add_argument('--bank', required=True)
    parser.add_argument('--heldout', required=True, help='JSON {"scenes": [[dataset, scene], ...]}')
    parser.add_argument('--training-scenes', required=True, help='JSON {"scenes": [[dataset, scene], ...]} of the training rows')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    import torch

    from .diagnostic_data import encode_prompt

    output = Path(args.output)
    if output.exists():
        raise ValueError('The gate report already exists')
    model, processor, report = load_checkpoint(args.student, args.adapter_dir, args.heads_json, args.heads_pt)
    with Path(args.rows).open() as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    heldout = json.loads(Path(args.heldout).read_text())['scenes']
    training = json.loads(Path(args.training_scenes).read_text())['scenes']

    def encode_row(row):
        batch = encode_prompt(processor, row)[0]
        return {key: value.to('cuda:0') if hasattr(value, 'to') else value for key, value in batch.items()}

    result = run_gate(model, processor.tokenizer, rows, args.bank, heldout, training, encode_row,
                      forward_context=torch.autocast('cuda', dtype=torch.bfloat16))
    result['checkpoint'] = {'adapter_dir': str(args.adapter_dir), 'load_report': report}
    output.write_text(json.dumps(result, indent=1, default=lambda v: v.tolist() if hasattr(v, 'tolist') else str(v)) + '\n')
    print(json.dumps({'gate_passed': result['gate']['passed'], 'checks': result['gate']['checks']}))


if __name__ == '__main__':
    main()
